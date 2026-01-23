"""
Bot Backend - Core business logic layer separated from Telegram frontend
"""
from typing import Optional, Dict, List
import asyncio
from datetime import datetime

from .session_manager import SessionManager, TradingSession
from .balance_manager import BalanceManager
from .manual_wallet_tracker import ManualWalletTracker, ManualWallet
from .fee_calculator import FeeCalculator
from ..blockchain.helius_client import HeliusClient
from ..blockchain.solana_client import SolanaClient
from ..trading.dex_client import JupiterClient
from ..monitoring.kolscan import KOLscanClient
from ..utils.logger import get_logger
from ..config import settings

logger = get_logger(__name__)


class CopyTradingBackend:
    """
    Main backend service that coordinates all bot functionality
    Separates business logic from Telegram frontend
    """

    def __init__(self):
        """Initialize backend services"""
        self.session_manager = SessionManager()
        self.wallet_tracker = ManualWalletTracker()
        self.fee_calculator = FeeCalculator()

        # Blockchain clients
        self.helius_client: Optional[HeliusClient] = None
        self.solana_client: Optional[SolanaClient] = None
        self.jupiter_client: Optional[JupiterClient] = None
        self.kolscan_client: Optional[KOLscanClient] = None

        # Bot state
        self.is_running = False
        self.is_initialized = False

        # SOL/EUR price tracking
        self.sol_price_eur = settings.sol_price_eur
        self.last_price_update = datetime.now()

        logger.info("Copy trading backend initialized")

    async def initialize(self):
        """Initialize all backend services"""
        if self.is_initialized:
            logger.warning("Backend already initialized")
            return

        try:
            logger.info("Initializing backend services...")

            # Initialize Helius client
            if settings.helius_api_key:
                self.helius_client = HeliusClient(settings.helius_api_key)
                await self.helius_client.initialize()
                logger.info("Helius client initialized")

            # Initialize Solana client
            self.solana_client = SolanaClient()
            connected = await self.solana_client.connect()
            if connected:
                logger.info("Solana client initialized")
            else:
                logger.warning("Solana client not available - running in demo mode")

            # Initialize Jupiter client (optional)
            try:
                self.jupiter_client = JupiterClient()
                await self.jupiter_client.connect()
                logger.info("Jupiter client initialized")
            except Exception as e:
                logger.warning(f"Jupiter client not available: {e}")

            # Initialize KOLscan client (optional)
            if settings.kolscan_api_key:
                try:
                    self.kolscan_client = KOLscanClient()
                    await self.kolscan_client.connect()
                    logger.info("KOLscan client initialized")
                except Exception as e:
                    logger.warning(f"KOLscan client not available: {e}")

            # Create default session if none exists
            if not self.session_manager.list_sessions():
                self._create_default_session()

            # Update SOL price
            await self.update_sol_price()

            self.is_initialized = True
            logger.info("Backend services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize backend: {e}")
            raise

    async def shutdown(self):
        """Shutdown all backend services"""
        logger.info("Shutting down backend services...")

        try:
            if self.helius_client:
                await self.helius_client.close()

            if self.solana_client:
                await self.solana_client.disconnect()

            if self.jupiter_client:
                await self.jupiter_client.disconnect()

            if self.kolscan_client:
                await self.kolscan_client.disconnect()

            self.is_initialized = False
            logger.info("Backend services shut down successfully")

        except Exception as e:
            logger.error(f"Error during backend shutdown: {e}")

    def _create_default_session(self):
        """Create default trading session"""
        session = self.session_manager.create_session(
            name="Default Session",
            strategy_id=2,  # Balanced strategy
            initial_balance_eur=settings.initial_balance_eur,
            config={}
        )
        logger.info(f"Default session created: {session.name}")

    # ==================== Session Management ====================

    def create_session(
        self,
        name: str,
        strategy_id: int,
        initial_balance_eur: float = 20.0
    ) -> TradingSession:
        """Create new trading session"""
        session = self.session_manager.create_session(
            name=name,
            strategy_id=strategy_id,
            initial_balance_eur=initial_balance_eur
        )
        return session

    def get_session(self, session_id: str) -> Optional[TradingSession]:
        """Get session by ID"""
        return self.session_manager.get_session(session_id)

    def get_active_session(self) -> Optional[TradingSession]:
        """Get currently active session"""
        return self.session_manager.get_active_session()

    def list_sessions(self, active_only: bool = False) -> List[TradingSession]:
        """List all sessions"""
        return self.session_manager.list_sessions(active_only)

    def switch_session(self, session_id: str) -> bool:
        """Switch active session"""
        return self.session_manager.set_active_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        return self.session_manager.delete_session(session_id)

    def get_session_statistics(self) -> dict:
        """Get statistics for all sessions"""
        return self.session_manager.get_statistics()

    # ==================== Balance Management ====================

    def get_balance(self, session_id: str = None) -> dict:
        """Get balance for a session"""
        session = self._get_session_or_active(session_id)
        if not session:
            return {}

        return session.balance_manager.get_statistics()

    def add_balance(
        self,
        amount_eur: float,
        session_id: str = None,
        note: str = None
    ) -> dict:
        """Add balance to a session"""
        session = self._get_session_or_active(session_id)
        if not session:
            raise ValueError("No active session")

        return session.balance_manager.add_balance(amount_eur, note)

    def get_balance_transactions(
        self,
        session_id: str = None,
        limit: int = 10
    ) -> list:
        """Get balance transaction history"""
        session = self._get_session_or_active(session_id)
        if not session:
            return []

        return session.balance_manager.get_transaction_history(limit)

    # ==================== Wallet Management ====================

    def add_wallet(
        self,
        address: str,
        name: str = None,
        notes: str = None
    ) -> ManualWallet:
        """Add wallet to track"""
        return self.wallet_tracker.add_wallet(address, name, notes)

    def remove_wallet(self, address: str) -> bool:
        """Remove wallet from tracking"""
        return self.wallet_tracker.remove_wallet(address)

    def get_wallet(self, address: str) -> Optional[ManualWallet]:
        """Get wallet by address"""
        return self.wallet_tracker.get_wallet(address)

    def list_wallets(
        self,
        active_only: bool = False,
        sort_by: str = 'added_at'
    ) -> List[ManualWallet]:
        """List tracked wallets"""
        return self.wallet_tracker.list_wallets(active_only, sort_by)

    def get_wallet_statistics(self) -> dict:
        """Get wallet tracking statistics"""
        return self.wallet_tracker.get_statistics()

    async def update_wallet_metrics(self, address: str):
        """Update wallet performance metrics from blockchain"""
        if not self.helius_client or not self.helius_client.is_available():
            logger.warning("Helius client not available for wallet metrics")
            return

        wallet = self.wallet_tracker.get_wallet(address)
        if not wallet:
            return

        # Fetch performance data from Helius
        performance = await self.helius_client.get_wallet_performance(address)

        # Update wallet metrics
        wallet.update_metrics(
            total_trades=performance.get('total_trades', 0),
            successful_trades=performance.get('successful_trades', 0),
            total_pnl=0.0,  # Would need more complex calculation
            last_trade_at=datetime.now() if performance.get('total_trades', 0) > 0 else None
        )

        logger.info(f"Updated metrics for wallet {wallet.name}")

    # ==================== Fee Calculation ====================

    def calculate_swap_fees(
        self,
        amount_sol: float,
        slippage_bps: int = None
    ) -> dict:
        """Calculate fees for a swap"""
        return self.fee_calculator.calculate_swap_fees(amount_sol, slippage_bps)

    def estimate_trade_cost(
        self,
        amount_sol: float,
        slippage_bps: int = None
    ) -> float:
        """Estimate total cost for a trade"""
        return self.fee_calculator.estimate_total_cost(amount_sol, slippage_bps)

    # ==================== Price Management ====================

    async def update_sol_price(self):
        """Update SOL/EUR price from market data"""
        try:
            # Get SOL/USD price from Jupiter
            if self.jupiter_client:
                # Jupiter returns prices, we'd need to implement SOL/USDC quote
                # For now, use a fixed price or external API
                # In production, you'd call CoinGecko or similar
                pass

            # For demo, use configured price
            self.sol_price_eur = settings.sol_price_eur
            self.last_price_update = datetime.now()

            # Update all session balance managers
            for session in self.session_manager.list_sessions():
                session.balance_manager.update_sol_price(self.sol_price_eur)

            logger.debug(f"SOL price updated: {self.sol_price_eur:.2f} EUR")

        except Exception as e:
            logger.error(f"Error updating SOL price: {e}")

    def get_sol_price_eur(self) -> float:
        """Get current SOL/EUR price"""
        return self.sol_price_eur

    # ==================== Bot Control ====================

    async def start_bot(self):
        """Start the trading bot"""
        if self.is_running:
            logger.warning("Bot already running")
            return

        if not self.is_initialized:
            await self.initialize()

        self.is_running = True
        logger.info("Trading bot started")

        # In a real implementation, this would start:
        # - Transaction monitoring
        # - Strategy engines
        # - Position management
        # etc.

    async def stop_bot(self):
        """Stop the trading bot"""
        if not self.is_running:
            logger.warning("Bot not running")
            return

        self.is_running = False
        logger.info("Trading bot stopped")

    def is_bot_running(self) -> bool:
        """Check if bot is running"""
        return self.is_running

    # ==================== Status & Statistics ====================

    def get_bot_status(self) -> dict:
        """Get overall bot status"""
        active_session = self.get_active_session()

        return {
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'active_session': active_session.name if active_session else None,
            'total_sessions': len(self.session_manager.sessions),
            'tracked_wallets': len(self.wallet_tracker.wallets),
            'sol_price_eur': self.sol_price_eur,
            'last_price_update': self.last_price_update,
            'network': settings.solana_network,
            'using_helius': self.helius_client.is_available() if self.helius_client else False
        }

    def get_overall_statistics(self) -> dict:
        """Get comprehensive statistics"""
        session_stats = self.session_manager.get_statistics()
        wallet_stats = self.wallet_tracker.get_statistics()

        return {
            **session_stats,
            'wallets': wallet_stats,
            'sol_price_eur': self.sol_price_eur,
            'network': settings.solana_network
        }

    # ==================== Helper Methods ====================

    def _get_session_or_active(self, session_id: str = None) -> Optional[TradingSession]:
        """Get session by ID or return active session"""
        if session_id:
            return self.session_manager.get_session(session_id)
        return self.session_manager.get_active_session()
