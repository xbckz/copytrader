"""
Position management with take profit and stop loss monitoring
"""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import settings
from ..config.strategies import StrategyConfig
from ..utils.logger import get_logger
from ..utils.helpers import calculate_percentage_change
from ..trading.price_tracker import PriceTracker
from ..trading.executor import TradeExecutor

logger = get_logger(__name__)


class PositionStatus(Enum):
    """Position status enum"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING_CLOSE = "pending_close"


@dataclass
class Position:
    """Represents a trading position"""
    id: str
    token_address: str
    entry_price: float
    entry_amount_sol: float
    token_amount: int
    strategy_id: int
    opened_at: datetime
    wallet_source: str  # Which KOL wallet triggered this trade

    # Current state
    current_price: float = 0.0
    status: PositionStatus = PositionStatus.OPEN

    # Exit parameters
    take_profit_price: float = 0.0
    stop_loss_price: float = 0.0
    trailing_stop_price: Optional[float] = None
    highest_price: float = 0.0

    # Results (when closed)
    exit_price: Optional[float] = None
    exit_amount_sol: Optional[float] = None
    closed_at: Optional[datetime] = None
    pnl_sol: Optional[float] = None
    pnl_percentage: Optional[float] = None
    close_reason: Optional[str] = None

    def __post_init__(self):
        """Initialize calculated fields"""
        self.highest_price = self.entry_price
        if self.entry_price > 0:
            self.current_price = self.entry_price

    @property
    def unrealized_pnl_percentage(self) -> float:
        """Calculate unrealized PnL percentage"""
        if self.entry_price == 0 or self.status != PositionStatus.OPEN:
            return 0.0
        return calculate_percentage_change(self.entry_price, self.current_price)

    @property
    def unrealized_pnl_sol(self) -> float:
        """Calculate unrealized PnL in SOL"""
        if self.entry_price == 0 or self.status != PositionStatus.OPEN:
            return 0.0

        # Estimate current SOL value
        price_ratio = self.current_price / self.entry_price
        current_sol_value = self.entry_amount_sol * price_ratio

        return current_sol_value - self.entry_amount_sol

    @property
    def hold_time_seconds(self) -> int:
        """Calculate how long position has been held"""
        if self.closed_at:
            return int((self.closed_at - self.opened_at).total_seconds())
        else:
            return int((datetime.now() - self.opened_at).total_seconds())

    def update_price(self, new_price: float):
        """
        Update current price and trailing stop

        Args:
            new_price: New token price
        """
        self.current_price = new_price

        # Update highest price
        if new_price > self.highest_price:
            self.highest_price = new_price

    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            'id': self.id,
            'token_address': self.token_address,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'entry_amount_sol': self.entry_amount_sol,
            'token_amount': self.token_amount,
            'strategy_id': self.strategy_id,
            'status': self.status.value,
            'opened_at': self.opened_at.isoformat(),
            'wallet_source': self.wallet_source,
            'take_profit_price': self.take_profit_price,
            'stop_loss_price': self.stop_loss_price,
            'unrealized_pnl_percentage': self.unrealized_pnl_percentage,
            'unrealized_pnl_sol': self.unrealized_pnl_sol,
            'hold_time_seconds': self.hold_time_seconds,
            'exit_price': self.exit_price,
            'exit_amount_sol': self.exit_amount_sol,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'pnl_sol': self.pnl_sol,
            'pnl_percentage': self.pnl_percentage,
            'close_reason': self.close_reason
        }


class PositionManager:
    """Manage trading positions with TP/SL monitoring"""

    def __init__(
        self,
        price_tracker: PriceTracker,
        trade_executor: TradeExecutor,
        strategy: StrategyConfig
    ):
        """
        Initialize position manager

        Args:
            price_tracker: Price tracker instance
            trade_executor: Trade executor instance
            strategy: Strategy configuration
        """
        self.price_tracker = price_tracker
        self.executor = trade_executor
        self.strategy = strategy

        # Active positions: position_id -> Position
        self.positions: Dict[str, Position] = {}

        # Closed positions history
        self.closed_positions: List[Position] = []

        # Monitoring state
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info(
            f"Position manager initialized for strategy: {strategy.name}"
        )

    async def open_position(
        self,
        token_address: str,
        entry_price: float,
        sol_amount: float,
        token_amount: int,
        wallet_source: str
    ) -> Optional[Position]:
        """
        Open a new position

        Args:
            token_address: Token mint address
            entry_price: Entry price
            sol_amount: Amount of SOL invested
            token_amount: Amount of tokens received
            wallet_source: Source wallet that triggered the trade

        Returns:
            Created position or None if max positions reached
        """
        # Check max positions limit
        if len(self.positions) >= self.strategy.max_positions:
            logger.warning(
                f"Max positions ({self.strategy.max_positions}) reached, "
                f"cannot open new position"
            )
            return None

        # Create position ID
        position_id = f"{token_address}_{int(datetime.now().timestamp())}"

        # Calculate TP/SL prices
        tp_multiplier = 1 + (self.strategy.take_profit_percentage / 100)
        sl_multiplier = 1 - (self.strategy.stop_loss_percentage / 100)

        take_profit_price = entry_price * tp_multiplier
        stop_loss_price = entry_price * sl_multiplier

        # Create position
        position = Position(
            id=position_id,
            token_address=token_address,
            entry_price=entry_price,
            entry_amount_sol=sol_amount,
            token_amount=token_amount,
            strategy_id=self.strategy.id,
            opened_at=datetime.now(),
            wallet_source=wallet_source,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price
        )

        # Add to active positions
        self.positions[position_id] = position

        # Start tracking price for this token
        self.price_tracker.add_token(token_address)

        logger.info(
            f"Opened position {position_id[:16]}... "
            f"Entry: ${entry_price:.8f}, TP: ${take_profit_price:.8f}, "
            f"SL: ${stop_loss_price:.8f}"
        )

        return position

    async def close_position(
        self,
        position_id: str,
        reason: str,
        current_price: Optional[float] = None
    ) -> bool:
        """
        Close a position

        Args:
            position_id: Position ID to close
            reason: Reason for closing
            current_price: Current price (if known)

        Returns:
            True if closed successfully, False otherwise
        """
        position = self.positions.get(position_id)
        if not position:
            logger.error(f"Position not found: {position_id}")
            return False

        if position.status != PositionStatus.OPEN:
            logger.warning(f"Position {position_id} not open")
            return False

        try:
            # Mark as pending close
            position.status = PositionStatus.PENDING_CLOSE

            # Get current price
            if current_price is None:
                current_price = self.price_tracker.get_price(position.token_address)

            if current_price is None:
                logger.error("Cannot get current price for position close")
                position.status = PositionStatus.OPEN
                return False

            # Execute sell
            result = await self.executor.execute_sell(
                token_address=position.token_address,
                token_amount=position.token_amount
            )

            if not result or not result.get('success'):
                logger.error(f"Failed to close position {position_id}")
                position.status = PositionStatus.OPEN
                return False

            # Update position with exit data
            position.exit_price = current_price
            position.exit_amount_sol = result.get('output_amount', 0.0)
            position.closed_at = datetime.now()
            position.status = PositionStatus.CLOSED
            position.close_reason = reason

            # Calculate PnL
            position.pnl_sol = position.exit_amount_sol - position.entry_amount_sol
            position.pnl_percentage = calculate_percentage_change(
                position.entry_price,
                position.exit_price
            )

            # Move to closed positions
            self.closed_positions.append(position)
            del self.positions[position_id]

            logger.info(
                f"Closed position {position_id[:16]}... "
                f"Reason: {reason}, PnL: {position.pnl_percentage:.2f}% "
                f"({position.pnl_sol:.4f} SOL)"
            )

            return True

        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}", exc_info=True)
            position.status = PositionStatus.OPEN
            return False

    async def start_monitoring(self):
        """Start monitoring positions for TP/SL"""
        if self.is_monitoring:
            logger.warning("Position monitoring already running")
            return

        self.is_monitoring = True
        logger.info("Starting position monitoring for TP/SL")

        self._monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop monitoring positions"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        logger.info("Stopping position monitoring")

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Main monitoring loop for TP/SL"""
        logger.info("Position monitoring loop started")

        while self.is_monitoring:
            try:
                await self._check_all_positions()
                await asyncio.sleep(1.0)  # Check every second

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _check_all_positions(self):
        """Check all positions for TP/SL conditions"""
        for position_id, position in list(self.positions.items()):
            await self._check_position(position)

    async def _check_position(self, position: Position):
        """
        Check a single position for TP/SL conditions

        Args:
            position: Position to check
        """
        # Get current price
        current_price = self.price_tracker.get_price(position.token_address)

        if current_price is None:
            return

        # Update position price
        position.update_price(current_price)

        # Check max hold time
        if self.strategy.max_hold_time > 0:
            if position.hold_time_seconds >= self.strategy.max_hold_time:
                logger.info(
                    f"Position {position.id[:16]}... exceeded max hold time, closing"
                )
                await self.close_position(position.id, "Max hold time", current_price)
                return

        # Check stop loss
        if current_price <= position.stop_loss_price:
            logger.info(
                f"Position {position.id[:16]}... hit stop loss "
                f"(${current_price:.8f} <= ${position.stop_loss_price:.8f})"
            )
            await self.close_position(position.id, "Stop loss", current_price)
            return

        # Check take profit
        if current_price >= position.take_profit_price:
            logger.info(
                f"Position {position.id[:16]}... hit take profit "
                f"(${current_price:.8f} >= ${position.take_profit_price:.8f})"
            )
            await self.close_position(position.id, "Take profit", current_price)
            return

        # Check trailing stop (if enabled)
        if self.strategy.use_trailing_stop:
            await self._check_trailing_stop(position, current_price)

    async def _check_trailing_stop(self, position: Position, current_price: float):
        """
        Check and update trailing stop

        Args:
            position: Position to check
            current_price: Current token price
        """
        # Calculate profit percentage
        profit_pct = position.unrealized_pnl_percentage

        # Activate trailing stop if profit threshold reached
        if profit_pct >= self.strategy.trailing_stop_activation:
            # Calculate trailing stop price
            trail_distance = self.strategy.trailing_stop_distance / 100
            trailing_price = position.highest_price * (1 - trail_distance)

            # Update trailing stop price
            if position.trailing_stop_price is None or trailing_price > position.trailing_stop_price:
                position.trailing_stop_price = trailing_price

            # Check if trailing stop triggered
            if current_price <= position.trailing_stop_price:
                logger.info(
                    f"Position {position.id[:16]}... hit trailing stop "
                    f"(${current_price:.8f} <= ${position.trailing_stop_price:.8f})"
                )
                await self.close_position(position.id, "Trailing stop", current_price)

    def get_all_positions(self) -> List[Position]:
        """Get all active positions"""
        return list(self.positions.values())

    def get_position(self, position_id: str) -> Optional[Position]:
        """Get a specific position"""
        return self.positions.get(position_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get position statistics"""
        all_closed = self.closed_positions

        if not all_closed:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'average_pnl': 0.0,
                'total_pnl': 0.0
            }

        winning = [p for p in all_closed if p.pnl_sol and p.pnl_sol > 0]
        losing = [p for p in all_closed if p.pnl_sol and p.pnl_sol <= 0]

        total_pnl = sum(p.pnl_sol for p in all_closed if p.pnl_sol)

        return {
            'total_trades': len(all_closed),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(all_closed)) * 100 if all_closed else 0,
            'average_pnl': total_pnl / len(all_closed) if all_closed else 0,
            'total_pnl': total_pnl
        }
