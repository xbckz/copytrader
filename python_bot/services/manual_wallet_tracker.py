"""
Manual Wallet Tracker - Allows users to manually add and track Solana wallets
"""
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ManualWallet:
    """Represents a manually tracked wallet"""

    def __init__(
        self,
        address: str,
        name: str = None,
        notes: str = None
    ):
        """
        Initialize manual wallet

        Args:
            address: Wallet address
            name: Optional friendly name
            notes: Optional notes
        """
        self.address = address
        self.name = name or f"Wallet {address[:8]}..."
        self.notes = notes
        self.added_at = datetime.now()
        self.is_active = True

        # Performance metrics (updated from blockchain data)
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_pnl = 0.0
        self.last_trade_at = None
        self.last_updated = datetime.now()

        # Transaction history
        self.transaction_history = []

        logger.info(f"Manual wallet added: {self.name} ({address})")

    def get_win_rate(self) -> float:
        """Calculate win rate"""
        if self.total_trades == 0:
            return 0.0
        return (self.successful_trades / self.total_trades) * 100

    def update_metrics(
        self,
        total_trades: int = None,
        successful_trades: int = None,
        total_pnl: float = None,
        last_trade_at: datetime = None
    ):
        """
        Update wallet performance metrics

        Args:
            total_trades: Total number of trades
            successful_trades: Number of successful trades
            total_pnl: Total profit/loss
            last_trade_at: Last trade timestamp
        """
        if total_trades is not None:
            self.total_trades = total_trades
        if successful_trades is not None:
            self.successful_trades = successful_trades
        if total_pnl is not None:
            self.total_pnl = total_pnl
        if last_trade_at is not None:
            self.last_trade_at = last_trade_at

        self.failed_trades = self.total_trades - self.successful_trades
        self.last_updated = datetime.now()

        logger.debug(f"Metrics updated for wallet {self.name}: {self.total_trades} trades, {self.get_win_rate():.1f}% win rate")

    def add_transaction(self, transaction_data: dict):
        """
        Add transaction to history

        Args:
            transaction_data: Transaction details
        """
        self.transaction_history.append({
            **transaction_data,
            'recorded_at': datetime.now()
        })

        # Update metrics based on transaction
        self.total_trades += 1
        if transaction_data.get('success', False):
            self.successful_trades += 1
        else:
            self.failed_trades += 1

        pnl = transaction_data.get('pnl', 0.0)
        self.total_pnl += pnl

        self.last_trade_at = datetime.now()
        self.last_updated = datetime.now()

    def get_statistics(self) -> dict:
        """Get wallet statistics"""
        return {
            'address': self.address,
            'name': self.name,
            'is_active': self.is_active,
            'added_at': self.added_at,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'win_rate': self.get_win_rate(),
            'total_pnl': self.total_pnl,
            'last_trade_at': self.last_trade_at,
            'last_updated': self.last_updated,
            'notes': self.notes
        }

    def to_dict(self) -> dict:
        """Convert wallet to dictionary"""
        return {
            'address': self.address,
            'name': self.name,
            'notes': self.notes,
            'is_active': self.is_active,
            'added_at': self.added_at.isoformat(),
            'total_trades': self.total_trades,
            'win_rate': self.get_win_rate(),
            'total_pnl': self.total_pnl,
            'last_trade_at': self.last_trade_at.isoformat() if self.last_trade_at else None
        }


class ManualWalletTracker:
    """Manages manually tracked wallets"""

    def __init__(self):
        """Initialize manual wallet tracker"""
        self.wallets: Dict[str, ManualWallet] = {}
        logger.info("Manual wallet tracker initialized")

    def add_wallet(
        self,
        address: str,
        name: str = None,
        notes: str = None
    ) -> ManualWallet:
        """
        Add a wallet to track

        Args:
            address: Wallet address
            name: Optional friendly name
            notes: Optional notes

        Returns:
            ManualWallet object

        Raises:
            ValueError: If wallet already exists
        """
        if not self._validate_address(address):
            raise ValueError(f"Invalid Solana address: {address}")

        if address in self.wallets:
            raise ValueError(f"Wallet already tracked: {address}")

        wallet = ManualWallet(address=address, name=name, notes=notes)
        self.wallets[address] = wallet

        logger.info(f"Wallet added to tracker: {wallet.name} ({address})")

        return wallet

    def remove_wallet(self, address: str) -> bool:
        """
        Remove a wallet from tracking

        Args:
            address: Wallet address

        Returns:
            True if removed, False if not found
        """
        if address not in self.wallets:
            logger.warning(f"Wallet not found for removal: {address}")
            return False

        wallet = self.wallets[address]
        del self.wallets[address]

        logger.info(f"Wallet removed from tracker: {wallet.name} ({address})")

        return True

    def get_wallet(self, address: str) -> Optional[ManualWallet]:
        """
        Get wallet by address

        Args:
            address: Wallet address

        Returns:
            ManualWallet or None
        """
        return self.wallets.get(address)

    def activate_wallet(self, address: str) -> bool:
        """
        Activate wallet monitoring

        Args:
            address: Wallet address

        Returns:
            True if successful
        """
        wallet = self.wallets.get(address)
        if not wallet:
            return False

        wallet.is_active = True
        logger.info(f"Wallet activated: {wallet.name}")
        return True

    def deactivate_wallet(self, address: str) -> bool:
        """
        Deactivate wallet monitoring

        Args:
            address: Wallet address

        Returns:
            True if successful
        """
        wallet = self.wallets.get(address)
        if not wallet:
            return False

        wallet.is_active = False
        logger.info(f"Wallet deactivated: {wallet.name}")
        return True

    def update_wallet(
        self,
        address: str,
        name: str = None,
        notes: str = None
    ) -> bool:
        """
        Update wallet details

        Args:
            address: Wallet address
            name: New name
            notes: New notes

        Returns:
            True if successful
        """
        wallet = self.wallets.get(address)
        if not wallet:
            return False

        if name:
            wallet.name = name
        if notes:
            wallet.notes = notes

        logger.info(f"Wallet updated: {wallet.name}")
        return True

    def list_wallets(
        self,
        active_only: bool = False,
        sort_by: str = 'added_at'
    ) -> List[ManualWallet]:
        """
        List all tracked wallets

        Args:
            active_only: Only return active wallets
            sort_by: Sort field ('added_at', 'win_rate', 'total_pnl', 'total_trades')

        Returns:
            List of ManualWallet objects
        """
        wallets = list(self.wallets.values())

        if active_only:
            wallets = [w for w in wallets if w.is_active]

        # Sort wallets
        if sort_by == 'win_rate':
            wallets.sort(key=lambda x: x.get_win_rate(), reverse=True)
        elif sort_by == 'total_pnl':
            wallets.sort(key=lambda x: x.total_pnl, reverse=True)
        elif sort_by == 'total_trades':
            wallets.sort(key=lambda x: x.total_trades, reverse=True)
        else:  # added_at
            wallets.sort(key=lambda x: x.added_at, reverse=True)

        return wallets

    def get_active_addresses(self) -> List[str]:
        """
        Get list of active wallet addresses for monitoring

        Returns:
            List of wallet addresses
        """
        return [
            address for address, wallet in self.wallets.items()
            if wallet.is_active
        ]

    def get_statistics(self) -> dict:
        """Get overall statistics"""
        total_wallets = len(self.wallets)
        active_wallets = len([w for w in self.wallets.values() if w.is_active])

        total_trades = sum(w.total_trades for w in self.wallets.values())
        total_successful = sum(w.successful_trades for w in self.wallets.values())

        overall_win_rate = (total_successful / total_trades * 100) if total_trades > 0 else 0.0

        return {
            'total_wallets': total_wallets,
            'active_wallets': active_wallets,
            'inactive_wallets': total_wallets - active_wallets,
            'total_trades': total_trades,
            'overall_win_rate': overall_win_rate
        }

    @staticmethod
    def _validate_address(address: str) -> bool:
        """
        Validate Solana address format

        Args:
            address: Address to validate

        Returns:
            True if valid
        """
        # Basic validation: should be 32-44 characters, base58 encoded
        if not address or len(address) < 32 or len(address) > 44:
            return False

        # Check if it's base58 (no 0, O, I, l)
        valid_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
        return all(c in valid_chars for c in address)
