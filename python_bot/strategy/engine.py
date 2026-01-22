"""
Strategy execution engine for copy trading
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..config import settings
from ..config.strategies import StrategyConfig, get_strategy
from ..utils.logger import get_logger
from ..utils.helpers import sol_to_lamports
from ..blockchain.solana_client import SolanaClient
from ..blockchain.transaction_monitor import TransactionMonitor
from ..monitoring.wallet_tracker import WalletTracker
from ..trading.price_tracker import PriceTracker
from ..trading.executor import TradeExecutor
from ..trading.dex_client import JupiterClient
from .position_manager import PositionManager

logger = get_logger(__name__)


class StrategyEngine:
    """Execute trading strategy based on KOL wallet activities"""

    def __init__(
        self,
        solana_client: SolanaClient,
        jupiter_client: JupiterClient,
        wallet_tracker: WalletTracker,
        transaction_monitor: TransactionMonitor,
        price_tracker: PriceTracker,
        trade_executor: TradeExecutor,
        strategy: StrategyConfig
    ):
        """
        Initialize strategy engine

        Args:
            solana_client: Solana blockchain client
            jupiter_client: Jupiter DEX client
            wallet_tracker: Wallet tracker for monitoring KOLs
            transaction_monitor: Transaction monitor
            price_tracker: Price tracker
            trade_executor: Trade executor
            strategy: Strategy configuration to use
        """
        self.solana = solana_client
        self.jupiter = jupiter_client
        self.wallet_tracker = wallet_tracker
        self.tx_monitor = transaction_monitor
        self.price_tracker = price_tracker
        self.executor = trade_executor
        self.strategy = strategy

        # Position manager for this strategy
        self.position_manager = PositionManager(
            price_tracker=price_tracker,
            trade_executor=trade_executor,
            strategy=strategy
        )

        # Performance tracking
        self.balance_sol = settings.initial_balance
        self.starting_balance = settings.initial_balance
        self.daily_loss = 0.0
        self.last_reset = datetime.now()

        # Running state
        self.is_running = False

        logger.info(
            f"Strategy engine initialized: {strategy.name} "
            f"(ID: {strategy.id})"
        )

    async def start(self):
        """Start the strategy engine"""
        if self.is_running:
            logger.warning("Strategy engine already running")
            return

        self.is_running = True
        logger.info(f"Starting strategy engine: {self.strategy.name}")

        # Register transaction callback
        self.tx_monitor.register_callback(self._on_new_transaction)

        # Start position monitoring
        await self.position_manager.start_monitoring()

        logger.info(
            f"Strategy engine started (balance: {self.balance_sol} SOL)"
        )

    async def stop(self):
        """Stop the strategy engine"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info(f"Stopping strategy engine: {self.strategy.name}")

        # Stop position monitoring
        await self.position_manager.stop_monitoring()

        logger.info("Strategy engine stopped")

    async def _on_new_transaction(
        self,
        wallet_address: str,
        transactions: List[Dict[str, Any]]
    ):
        """
        Callback for new transactions from monitored wallets

        Args:
            wallet_address: Wallet that made the transaction
            transactions: List of transaction data
        """
        if not self.is_running:
            return

        for tx_data in transactions:
            try:
                await self._process_transaction(wallet_address, tx_data)
            except Exception as e:
                logger.error(
                    f"Error processing transaction from {wallet_address[:8]}...: {e}",
                    exc_info=True
                )

    async def _process_transaction(
        self,
        wallet_address: str,
        tx_data: Dict[str, Any]
    ):
        """
        Process a transaction and potentially copy the trade

        Args:
            wallet_address: Source wallet address
            tx_data: Transaction data
        """
        # Parse transaction to extract trade details
        trade_info = await self._parse_trade_from_transaction(tx_data)

        if not trade_info:
            return

        # Only process buy transactions
        if trade_info['type'] != 'buy':
            logger.debug(f"Skipping non-buy transaction from {wallet_address[:8]}...")
            return

        token_address = trade_info['token_address']
        sol_amount = trade_info['sol_amount']

        logger.info(
            f"Detected buy from {wallet_address[:8]}...: "
            f"{sol_amount} SOL -> {token_address[:8]}..."
        )

        # Check if trade size meets minimum
        if sol_amount < self.strategy.min_wallet_trade_size:
            logger.debug(
                f"Trade size {sol_amount} SOL below minimum "
                f"{self.strategy.min_wallet_trade_size} SOL, skipping"
            )
            return

        # Check daily loss limit
        if await self._check_daily_loss_limit():
            logger.warning("Daily loss limit reached, not copying trade")
            return

        # Copy the trade
        await self._copy_trade(wallet_address, token_address, sol_amount)

    async def _parse_trade_from_transaction(
        self,
        tx_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse transaction data to extract trade information

        Args:
            tx_data: Transaction data

        Returns:
            Trade info dict or None if not a relevant trade
        """
        # This is a simplified parser - in production you would need
        # comprehensive transaction parsing for Solana DEX transactions
        # This would involve parsing program instructions, token transfers, etc.

        try:
            # Placeholder for actual transaction parsing
            # In reality, you'd parse the transaction instructions
            # to identify DEX swaps, extract token addresses, amounts, etc.

            # For now, return None to indicate we need to implement
            # proper transaction parsing
            return None

        except Exception as e:
            logger.error(f"Error parsing transaction: {e}")
            return None

    async def _copy_trade(
        self,
        source_wallet: str,
        token_address: str,
        original_sol_amount: float
    ):
        """
        Copy a trade from a KOL wallet

        Args:
            source_wallet: Source wallet that made the trade
            token_address: Token being traded
            original_sol_amount: Original trade size in SOL
        """
        # Calculate our trade size based on strategy
        our_trade_size = self.balance_sol * self.strategy.copy_percentage

        # Check against min/max trade sizes
        our_trade_size = max(
            settings.min_trade_size,
            min(our_trade_size, settings.max_trade_size)
        )

        # Check if we have enough balance
        if our_trade_size > self.balance_sol:
            logger.warning(
                f"Insufficient balance ({self.balance_sol} SOL) "
                f"for trade ({our_trade_size} SOL)"
            )
            return

        # Check position size limit
        max_position_size = self.balance_sol * self.strategy.position_size_pct
        if our_trade_size > max_position_size:
            our_trade_size = max_position_size
            logger.info(
                f"Trade size limited to {our_trade_size} SOL "
                f"by position size limit"
            )

        logger.info(
            f"Copying trade: {our_trade_size} SOL -> {token_address[:8]}..."
        )

        # Get current token price
        token_price = await self.jupiter.get_token_price(token_address)

        if not token_price:
            logger.error("Failed to get token price, skipping trade")
            return

        # Execute buy
        result = await self.executor.execute_buy(
            token_address=token_address,
            sol_amount=our_trade_size
        )

        if not result or not result.get('success'):
            logger.error("Trade execution failed")
            return

        # Update balance
        self.balance_sol -= our_trade_size

        # Open position
        position = await self.position_manager.open_position(
            token_address=token_address,
            entry_price=token_price,
            sol_amount=our_trade_size,
            token_amount=result.get('output_amount', 0),
            wallet_source=source_wallet
        )

        if position:
            logger.info(
                f"Position opened: {position.id[:16]}... "
                f"Entry: ${token_price:.8f}, "
                f"Amount: {our_trade_size} SOL"
            )
        else:
            logger.error("Failed to create position")

    async def _check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been reached

        Returns:
            True if limit reached, False otherwise
        """
        # Reset daily loss if it's a new day
        now = datetime.now()
        if (now - self.last_reset).days >= 1:
            self.daily_loss = 0.0
            self.last_reset = now

        # Calculate current daily loss
        current_balance = self.balance_sol
        for position in self.position_manager.get_all_positions():
            current_balance += position.entry_amount_sol

        daily_loss_pct = ((self.starting_balance - current_balance) / self.starting_balance) * 100

        if daily_loss_pct >= self.strategy.daily_loss_limit:
            logger.warning(
                f"Daily loss limit reached: {daily_loss_pct:.2f}% >= "
                f"{self.strategy.daily_loss_limit}%"
            )
            return True

        return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics

        Returns:
            Performance stats dictionary
        """
        position_stats = self.position_manager.get_statistics()

        # Calculate total portfolio value
        portfolio_value = self.balance_sol
        for position in self.position_manager.get_all_positions():
            portfolio_value += position.entry_amount_sol + position.unrealized_pnl_sol

        total_pnl = portfolio_value - self.starting_balance
        total_pnl_pct = (total_pnl / self.starting_balance) * 100

        return {
            'strategy_id': self.strategy.id,
            'strategy_name': self.strategy.name,
            'starting_balance': self.starting_balance,
            'current_balance': self.balance_sol,
            'portfolio_value': portfolio_value,
            'total_pnl_sol': total_pnl,
            'total_pnl_percentage': total_pnl_pct,
            'open_positions': len(self.position_manager.positions),
            'total_trades': position_stats['total_trades'],
            'winning_trades': position_stats['winning_trades'],
            'losing_trades': position_stats['losing_trades'],
            'win_rate': position_stats['win_rate'],
            'is_running': self.is_running
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'is_running': self.is_running,
            'strategy': {
                'id': self.strategy.id,
                'name': self.strategy.name,
                'description': self.strategy.description
            },
            'performance': self.get_performance_stats(),
            'positions': [p.to_dict() for p in self.position_manager.get_all_positions()]
        }
