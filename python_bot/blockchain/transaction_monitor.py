"""
Real-time transaction monitoring for Solana wallets
"""
import asyncio
from typing import List, Dict, Any, Callable, Optional, Set
from datetime import datetime
import json

from solders.pubkey import Pubkey

from ..config import settings
from ..utils.logger import get_logger
from .solana_client import SolanaClient

logger = get_logger(__name__)


class TransactionMonitor:
    """Monitor Solana wallets for new transactions in real-time"""

    def __init__(
        self,
        solana_client: SolanaClient,
        check_interval: float = 2.0
    ):
        """
        Initialize transaction monitor

        Args:
            solana_client: Connected Solana client
            check_interval: Interval between checks in seconds
        """
        self.client = solana_client
        self.check_interval = check_interval

        self.monitored_wallets: Set[str] = set()
        self.last_signatures: Dict[str, str] = {}  # wallet -> last signature
        self.is_running = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Callbacks for new transactions
        self.transaction_callbacks: List[Callable] = []

        logger.info("Transaction monitor initialized")

    def add_wallet(self, wallet_address: str):
        """
        Add a wallet to monitor

        Args:
            wallet_address: Wallet public key to monitor
        """
        self.monitored_wallets.add(wallet_address)
        logger.info(f"Added wallet to monitor: {wallet_address[:8]}...")

    def add_wallets(self, wallet_addresses: List[str]):
        """
        Add multiple wallets to monitor

        Args:
            wallet_addresses: List of wallet public keys
        """
        for address in wallet_addresses:
            self.add_wallet(address)

        logger.info(f"Added {len(wallet_addresses)} wallets to monitor")

    def remove_wallet(self, wallet_address: str):
        """
        Remove a wallet from monitoring

        Args:
            wallet_address: Wallet public key to remove
        """
        self.monitored_wallets.discard(wallet_address)
        self.last_signatures.pop(wallet_address, None)
        logger.info(f"Removed wallet from monitoring: {wallet_address[:8]}...")

    def register_callback(self, callback: Callable):
        """
        Register a callback function for new transactions

        Args:
            callback: Async function to call with transaction data
                     Signature: async def callback(wallet: str, transactions: List[Dict])
        """
        self.transaction_callbacks.append(callback)
        logger.info(f"Registered transaction callback: {callback.__name__}")

    async def start(self):
        """Start monitoring wallets"""
        if self.is_running:
            logger.warning("Transaction monitor already running")
            return

        if not self.monitored_wallets:
            logger.warning("No wallets to monitor")
            return

        self.is_running = True
        logger.info(f"Starting transaction monitor for {len(self.monitored_wallets)} wallets")

        # Initialize last signatures for all wallets
        await self._initialize_last_signatures()

        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop monitoring wallets"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("Stopping transaction monitor")

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _initialize_last_signatures(self):
        """Initialize last known signatures for all monitored wallets"""
        logger.info("Initializing last signatures for monitored wallets...")

        tasks = []
        for wallet in self.monitored_wallets:
            tasks.append(self._get_latest_signature(wallet))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for wallet, result in zip(self.monitored_wallets, results):
            if isinstance(result, Exception):
                logger.error(f"Error initializing signature for {wallet[:8]}...: {result}")
            elif result:
                self.last_signatures[wallet] = result
                logger.debug(f"Initialized signature for {wallet[:8]}...: {result[:8]}...")

    async def _get_latest_signature(self, wallet: str) -> Optional[str]:
        """
        Get the latest transaction signature for a wallet

        Args:
            wallet: Wallet address

        Returns:
            Latest signature or None
        """
        try:
            signatures = await self.client.get_signatures_for_address(wallet, limit=1)

            if signatures:
                return signatures[0]['signature']

            return None

        except Exception as e:
            logger.error(f"Error getting latest signature for {wallet[:8]}...: {e}")
            return None

    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Transaction monitoring loop started")

        while self.is_running:
            try:
                await self._check_all_wallets()
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

    async def _check_all_wallets(self):
        """Check all monitored wallets for new transactions"""
        tasks = []
        for wallet in self.monitored_wallets:
            tasks.append(self._check_wallet_transactions(wallet))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_wallet_transactions(self, wallet: str):
        """
        Check a specific wallet for new transactions

        Args:
            wallet: Wallet address to check
        """
        try:
            # Get recent signatures
            last_sig = self.last_signatures.get(wallet)

            # Fetch signatures (before the last known one)
            signatures = await self.client.get_signatures_for_address(
                wallet,
                limit=10,
                before=None  # Get latest
            )

            if not signatures:
                return

            # Find new transactions
            new_transactions = []
            new_last_sig = None

            for sig_info in signatures:
                sig = sig_info['signature']

                # Update the most recent signature
                if not new_last_sig:
                    new_last_sig = sig

                # Stop if we've reached the last known signature
                if sig == last_sig:
                    break

                # Skip failed transactions
                if sig_info.get('err'):
                    continue

                new_transactions.append(sig_info)

            # Update last signature
            if new_last_sig:
                self.last_signatures[wallet] = new_last_sig

            # Process new transactions
            if new_transactions:
                logger.info(
                    f"Found {len(new_transactions)} new transaction(s) "
                    f"for {wallet[:8]}..."
                )

                # Fetch full transaction details
                detailed_txs = await self._fetch_transaction_details(new_transactions)

                # Call registered callbacks
                await self._notify_callbacks(wallet, detailed_txs)

        except Exception as e:
            logger.error(f"Error checking wallet {wallet[:8]}...: {e}")

    async def _fetch_transaction_details(
        self,
        signatures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fetch detailed transaction information

        Args:
            signatures: List of signature info dictionaries

        Returns:
            List of detailed transaction data
        """
        detailed_txs = []

        for sig_info in signatures:
            try:
                tx_response = await self.client.get_transaction(
                    sig_info['signature'],
                    max_supported_transaction_version=0
                )

                if tx_response and tx_response.value:
                    tx_data = {
                        'signature': sig_info['signature'],
                        'slot': sig_info['slot'],
                        'block_time': sig_info['block_time'],
                        'transaction': tx_response.value
                    }
                    detailed_txs.append(tx_data)

            except Exception as e:
                logger.error(
                    f"Error fetching transaction details for "
                    f"{sig_info['signature'][:8]}...: {e}"
                )

        return detailed_txs

    async def _notify_callbacks(self, wallet: str, transactions: List[Dict[str, Any]]):
        """
        Notify all registered callbacks about new transactions

        Args:
            wallet: Wallet address
            transactions: List of transaction data
        """
        for callback in self.transaction_callbacks:
            try:
                await callback(wallet, transactions)
            except Exception as e:
                logger.error(
                    f"Error in transaction callback {callback.__name__}: {e}",
                    exc_info=True
                )

    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitor status

        Returns:
            Status dictionary
        """
        return {
            'is_running': self.is_running,
            'monitored_wallets': len(self.monitored_wallets),
            'check_interval': self.check_interval,
            'wallets': list(self.monitored_wallets)
        }
