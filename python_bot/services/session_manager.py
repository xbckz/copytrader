"""
Session Manager - Handles multiple trading sessions with different configurations
"""
from typing import Dict, Optional, List
from datetime import datetime
import uuid

from .balance_manager import BalanceManager
from ..config.strategies import get_strategy
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TradingSession:
    """Represents a single trading session"""

    def __init__(
        self,
        session_id: str,
        name: str,
        strategy_id: int,
        initial_balance_eur: float,
        config: dict = None
    ):
        """
        Initialize trading session

        Args:
            session_id: Unique session ID
            name: Human-readable session name
            strategy_id: Strategy ID (1-5)
            initial_balance_eur: Initial balance in EUR
            config: Additional configuration
        """
        self.session_id = session_id
        self.name = name
        self.strategy_id = strategy_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.is_active = True

        # Initialize balance manager
        self.balance_manager = BalanceManager(session_id, initial_balance_eur)

        # Load strategy configuration
        self.strategy = get_strategy(strategy_id)

        # Custom configuration
        self.config = config or {}

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl_sol = 0.0

        # Active positions
        self.active_positions = {}
        self.closed_positions = {}

        logger.info(
            f"Trading session created: {name} (ID: {session_id[:8]}...) "
            f"Strategy: {self.strategy.name}, Balance: {initial_balance_eur:.2f} EUR"
        )

    def get_win_rate(self) -> float:
        """Calculate win rate"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = datetime.now()

    def record_trade(self, pnl_sol: float):
        """
        Record a completed trade

        Args:
            pnl_sol: Profit/loss in SOL
        """
        self.total_trades += 1
        self.total_pnl_sol += pnl_sol

        if pnl_sol > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        self.update_last_active()

    def get_statistics(self) -> dict:
        """Get session statistics"""
        balance_stats = self.balance_manager.get_statistics()

        return {
            'session_id': self.session_id,
            'name': self.name,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy.name,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'balance_sol': balance_stats['current_balance_sol'],
            'balance_eur': balance_stats['current_balance_eur'],
            'initial_balance_eur': balance_stats['initial_balance_eur'],
            'total_pnl_sol': self.total_pnl_sol,
            'total_pnl_eur': balance_stats['total_pnl_eur'],
            'total_pnl_percentage': balance_stats['total_pnl_percentage'],
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.get_win_rate(),
            'active_positions': len(self.active_positions),
            'closed_positions': len(self.closed_positions)
        }

    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'name': self.name,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'config': self.config
        }


class SessionManager:
    """Manages multiple trading sessions"""

    def __init__(self):
        """Initialize session manager"""
        self.sessions: Dict[str, TradingSession] = {}
        self.active_session_id: Optional[str] = None

        logger.info("Session manager initialized")

    def create_session(
        self,
        name: str,
        strategy_id: int,
        initial_balance_eur: float = 20.0,
        config: dict = None
    ) -> TradingSession:
        """
        Create a new trading session

        Args:
            name: Session name
            strategy_id: Strategy ID (1-5)
            initial_balance_eur: Initial balance in EUR
            config: Additional configuration

        Returns:
            Created TradingSession
        """
        session_id = str(uuid.uuid4())

        session = TradingSession(
            session_id=session_id,
            name=name,
            strategy_id=strategy_id,
            initial_balance_eur=initial_balance_eur,
            config=config
        )

        self.sessions[session_id] = session

        # Set as active if it's the first session
        if self.active_session_id is None:
            self.active_session_id = session_id

        logger.info(f"Session created: {name} (ID: {session_id[:8]}...)")

        return session

    def get_session(self, session_id: str) -> Optional[TradingSession]:
        """
        Get session by ID

        Args:
            session_id: Session ID

        Returns:
            TradingSession or None
        """
        return self.sessions.get(session_id)

    def get_active_session(self) -> Optional[TradingSession]:
        """Get currently active session"""
        if self.active_session_id:
            return self.sessions.get(self.active_session_id)
        return None

    def set_active_session(self, session_id: str) -> bool:
        """
        Set active session

        Args:
            session_id: Session ID to activate

        Returns:
            True if successful
        """
        if session_id not in self.sessions:
            logger.warning(f"Cannot activate non-existent session: {session_id}")
            return False

        self.active_session_id = session_id
        logger.info(f"Active session changed to: {self.sessions[session_id].name}")
        return True

    def deactivate_session(self, session_id: str) -> bool:
        """
        Deactivate a session

        Args:
            session_id: Session ID to deactivate

        Returns:
            True if successful
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.is_active = False

        # If this was the active session, clear it
        if self.active_session_id == session_id:
            self.active_session_id = None

        logger.info(f"Session deactivated: {session.name}")
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session ID to delete

        Returns:
            True if successful
        """
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        del self.sessions[session_id]

        # If this was the active session, clear it
        if self.active_session_id == session_id:
            self.active_session_id = None

        logger.info(f"Session deleted: {session.name}")
        return True

    def list_sessions(self, active_only: bool = False) -> List[TradingSession]:
        """
        List all sessions

        Args:
            active_only: Only return active sessions

        Returns:
            List of TradingSession objects
        """
        sessions = list(self.sessions.values())

        if active_only:
            sessions = [s for s in sessions if s.is_active]

        # Sort by last active (most recent first)
        sessions.sort(key=lambda x: x.last_active, reverse=True)

        return sessions

    def get_statistics(self) -> dict:
        """Get overall statistics across all sessions"""
        total_sessions = len(self.sessions)
        active_sessions = len([s for s in self.sessions.values() if s.is_active])

        total_balance_eur = sum(s.balance_manager.get_balance_eur() for s in self.sessions.values())
        total_pnl_eur = sum(s.balance_manager.get_total_pnl_eur() for s in self.sessions.values())
        total_trades = sum(s.total_trades for s in self.sessions.values())
        total_winning = sum(s.winning_trades for s in self.sessions.values())

        overall_win_rate = (total_winning / total_trades * 100) if total_trades > 0 else 0.0

        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_balance_eur': total_balance_eur,
            'total_pnl_eur': total_pnl_eur,
            'total_trades': total_trades,
            'total_winning_trades': total_winning,
            'overall_win_rate': overall_win_rate,
            'active_session_id': self.active_session_id
        }
