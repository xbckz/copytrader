"""
Wallet tracker for managing and monitoring top KOL wallets
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from ..config import settings
from ..utils.logger import get_logger
from .kolscan import KOLscanClient
from ..blockchain.transaction_monitor import TransactionMonitor

logger = get_logger(__name__)


class WalletTracker:
    """Manages tracking of top performing wallets"""

    def __init__(
        self,
        kolscan_client: KOLscanClient,
        transaction_monitor: TransactionMonitor,
        top_count: int = 100,
        refresh_interval: int = 3600
    ):
        """
        Initialize wallet tracker

        Args:
            kolscan_client: KOLscan API client
            transaction_monitor: Transaction monitor instance
            top_count: Number of top wallets to track
            refresh_interval: Interval to refresh wallet list (seconds)
        """
        self.kolscan = kolscan_client
        self.tx_monitor = transaction_monitor
        self.top_count = top_count
        self.refresh_interval = refresh_interval

        self.tracked_wallets: Dict[str, Dict[str, Any]] = {}
        self.last_refresh: Optional[datetime] = None
        self.is_running = False
        self._refresh_task: Optional[asyncio.Task] = None

        logger.info(f"Wallet tracker initialized (tracking top {top_count} wallets)")

    async def initialize(self):
        """Initialize wallet tracker and fetch initial wallet list"""
        logger.info("Initializing wallet tracker...")

        # Fetch initial top wallets
        await self.refresh_wallet_list()

        # Add wallets to transaction monitor
        wallet_addresses = list(self.tracked_wallets.keys())
        self.tx_monitor.add_wallets(wallet_addresses)

        logger.info(f"Wallet tracker initialized with {len(wallet_addresses)} wallets")

    async def refresh_wallet_list(self):
        """Refresh the list of top wallets from KOLscan"""
        logger.info("Refreshing top wallet list from KOLscan...")

        try:
            # Fetch top wallets
            wallets = await self.kolscan.get_top_wallets(
                limit=self.top_count,
                timeframe="7d"
            )

            if not wallets:
                # Use fallback if API fails
                logger.warning("No wallets from KOLscan, using fallback")
                wallets = await self.kolscan.get_fallback_wallets(self.top_count)

            # Update tracked wallets
            old_wallet_count = len(self.tracked_wallets)
            new_tracked = {}

            for wallet_data in wallets:
                address = wallet_data.get('address')
                if not address:
                    continue

                new_tracked[address] = {
                    'address': address,
                    'pnl': wallet_data.get('pnl', 0),
                    'win_rate': wallet_data.get('win_rate', 0),
                    'total_trades': wallet_data.get('total_trades', 0),
                    'rank': wallet_data.get('rank', 999),
                    'added_at': datetime.now(),
                    'last_seen': datetime.now()
                }

            # Find wallets to add/remove
            old_addresses = set(self.tracked_wallets.keys())
            new_addresses = set(new_tracked.keys())

            to_add = new_addresses - old_addresses
            to_remove = old_addresses - new_addresses

            # Update tracking
            self.tracked_wallets = new_tracked
            self.last_refresh = datetime.now()

            # Update transaction monitor
            for address in to_add:
                self.tx_monitor.add_wallet(address)

            for address in to_remove:
                self.tx_monitor.remove_wallet(address)

            logger.info(
                f"Wallet list refreshed: {len(new_tracked)} total, "
                f"+{len(to_add)} added, -{len(to_remove)} removed"
            )

            return len(new_tracked)

        except Exception as e:
            logger.error(f"Error refreshing wallet list: {e}", exc_info=True)
            return 0

    async def start_auto_refresh(self):
        """Start automatic wallet list refresh"""
        if self.is_running:
            logger.warning("Auto-refresh already running")
            return

        self.is_running = True
        logger.info(f"Starting auto-refresh (interval: {self.refresh_interval}s)")

        self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

    async def stop_auto_refresh(self):
        """Stop automatic wallet list refresh"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("Stopping auto-refresh")

        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

    async def _auto_refresh_loop(self):
        """Auto-refresh loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.refresh_interval)
                await self.refresh_wallet_list()

            except asyncio.CancelledError:
                logger.info("Auto-refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-refresh loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait a minute before retrying

    def get_wallet_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tracked wallet

        Args:
            address: Wallet address

        Returns:
            Wallet info dict or None
        """
        return self.tracked_wallets.get(address)

    def get_top_wallets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N tracked wallets by rank

        Args:
            limit: Number of wallets to return

        Returns:
            List of wallet info dicts
        """
        sorted_wallets = sorted(
            self.tracked_wallets.values(),
            key=lambda x: x.get('rank', 999)
        )
        return sorted_wallets[:limit]

    def is_tracked(self, address: str) -> bool:
        """
        Check if a wallet is being tracked

        Args:
            address: Wallet address

        Returns:
            True if tracked, False otherwise
        """
        return address in self.tracked_wallets

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tracker statistics

        Returns:
            Statistics dictionary
        """
        if not self.tracked_wallets:
            return {
                'total_wallets': 0,
                'average_win_rate': 0,
                'average_pnl': 0,
                'last_refresh': None
            }

        wallets = list(self.tracked_wallets.values())

        return {
            'total_wallets': len(wallets),
            'average_win_rate': sum(w.get('win_rate', 0) for w in wallets) / len(wallets),
            'average_pnl': sum(w.get('pnl', 0) for w in wallets) / len(wallets),
            'last_refresh': self.last_refresh,
            'is_running': self.is_running
        }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current tracker status

        Returns:
            Status dictionary
        """
        return {
            'is_running': self.is_running,
            'tracked_wallets': len(self.tracked_wallets),
            'top_count': self.top_count,
            'refresh_interval': self.refresh_interval,
            'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None,
            'statistics': self.get_statistics()
        }
