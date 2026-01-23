"""
Balance Manager - Handles balance tracking, deposits, and withdrawals
"""
from typing import Optional
from datetime import datetime
import uuid

from ..utils.logger import get_logger
from ..config import settings

logger = get_logger(__name__)


class BalanceManager:
    """Manages trading balance for sessions"""

    def __init__(self, session_id: str, initial_balance_eur: float = None):
        """
        Initialize balance manager

        Args:
            session_id: Trading session ID
            initial_balance_eur: Initial balance in EUR
        """
        self.session_id = session_id
        self.initial_balance_eur = initial_balance_eur or settings.initial_balance_eur

        # Convert EUR to SOL using current price
        self.sol_price_eur = settings.sol_price_eur
        self.balance_sol = self.initial_balance_eur / self.sol_price_eur

        # Track balance history
        self.balance_history = []
        self.transactions = []

        # Record initial deposit
        self._record_transaction(
            transaction_type="deposit",
            amount_sol=self.balance_sol,
            amount_eur=self.initial_balance_eur,
            note="Initial balance"
        )

        logger.info(
            f"Balance manager initialized for session {session_id}: "
            f"{self.initial_balance_eur:.2f} EUR = {self.balance_sol:.4f} SOL "
            f"(SOL price: {self.sol_price_eur:.2f} EUR)"
        )

    def get_balance_sol(self) -> float:
        """Get current balance in SOL"""
        return self.balance_sol

    def get_balance_eur(self) -> float:
        """Get current balance in EUR"""
        return self.balance_sol * self.sol_price_eur

    def get_total_pnl_sol(self) -> float:
        """Get total PnL in SOL"""
        return self.balance_sol - (self.initial_balance_eur / self.sol_price_eur)

    def get_total_pnl_eur(self) -> float:
        """Get total PnL in EUR"""
        return self.get_balance_eur() - self.initial_balance_eur

    def get_total_pnl_percentage(self) -> float:
        """Get total PnL as percentage"""
        initial_sol = self.initial_balance_eur / self.sol_price_eur
        if initial_sol == 0:
            return 0.0
        return ((self.balance_sol - initial_sol) / initial_sol) * 100

    def add_balance(self, amount_eur: float, note: str = None) -> dict:
        """
        Add balance (deposit)

        Args:
            amount_eur: Amount to add in EUR
            note: Optional note

        Returns:
            Transaction details
        """
        amount_sol = amount_eur / self.sol_price_eur
        balance_before = self.balance_sol

        self.balance_sol += amount_sol

        transaction = self._record_transaction(
            transaction_type="deposit",
            amount_sol=amount_sol,
            amount_eur=amount_eur,
            balance_before=balance_before,
            note=note or f"Deposit of {amount_eur:.2f} EUR"
        )

        logger.info(
            f"Balance added: {amount_eur:.2f} EUR ({amount_sol:.4f} SOL). "
            f"New balance: {self.get_balance_eur():.2f} EUR ({self.balance_sol:.4f} SOL)"
        )

        return transaction

    def withdraw_balance(self, amount_eur: float, note: str = None) -> dict:
        """
        Withdraw balance

        Args:
            amount_eur: Amount to withdraw in EUR
            note: Optional note

        Returns:
            Transaction details
        """
        amount_sol = amount_eur / self.sol_price_eur

        if amount_sol > self.balance_sol:
            raise ValueError(
                f"Insufficient balance: {self.get_balance_eur():.2f} EUR "
                f"({self.balance_sol:.4f} SOL) < {amount_eur:.2f} EUR ({amount_sol:.4f} SOL)"
            )

        balance_before = self.balance_sol
        self.balance_sol -= amount_sol

        transaction = self._record_transaction(
            transaction_type="withdrawal",
            amount_sol=amount_sol,
            amount_eur=amount_eur,
            balance_before=balance_before,
            note=note or f"Withdrawal of {amount_eur:.2f} EUR"
        )

        logger.info(
            f"Balance withdrawn: {amount_eur:.2f} EUR ({amount_sol:.4f} SOL). "
            f"New balance: {self.get_balance_eur():.2f} EUR ({self.balance_sol:.4f} SOL)"
        )

        return transaction

    def deduct_for_trade(self, amount_sol: float, fees_sol: float) -> bool:
        """
        Deduct balance for a trade including fees

        Args:
            amount_sol: Trade amount in SOL
            fees_sol: Total fees in SOL

        Returns:
            True if successful, False if insufficient balance
        """
        total_required = amount_sol + fees_sol

        if total_required > self.balance_sol:
            logger.warning(
                f"Insufficient balance for trade: "
                f"Required {total_required:.6f} SOL (trade: {amount_sol:.6f}, fees: {fees_sol:.6f}), "
                f"Available: {self.balance_sol:.6f} SOL"
            )
            return False

        self.balance_sol -= total_required

        logger.debug(
            f"Deducted {amount_sol:.6f} SOL + {fees_sol:.6f} SOL fees = {total_required:.6f} SOL. "
            f"New balance: {self.balance_sol:.6f} SOL"
        )

        return True

    def credit_from_trade(self, amount_sol: float, fees_sol: float):
        """
        Credit balance from a trade sale (minus fees)

        Args:
            amount_sol: Trade proceeds in SOL
            fees_sol: Total fees in SOL
        """
        net_amount = amount_sol - fees_sol
        self.balance_sol += net_amount

        logger.debug(
            f"Credited {amount_sol:.6f} SOL - {fees_sol:.6f} SOL fees = {net_amount:.6f} SOL. "
            f"New balance: {self.balance_sol:.6f} SOL"
        )

    def update_sol_price(self, new_price_eur: float):
        """
        Update SOL/EUR price for accurate balance display

        Args:
            new_price_eur: New SOL price in EUR
        """
        old_price = self.sol_price_eur
        self.sol_price_eur = new_price_eur

        logger.debug(f"SOL price updated: {old_price:.2f} EUR -> {new_price_eur:.2f} EUR")

    def _record_transaction(
        self,
        transaction_type: str,
        amount_sol: float,
        amount_eur: float = None,
        balance_before: float = None,
        note: str = None
    ) -> dict:
        """Record a balance transaction"""
        if balance_before is None:
            balance_before = self.balance_sol

        transaction = {
            'id': str(uuid.uuid4()),
            'session_id': self.session_id,
            'type': transaction_type,
            'amount_sol': amount_sol,
            'amount_eur': amount_eur or (amount_sol * self.sol_price_eur),
            'balance_before': balance_before,
            'balance_after': self.balance_sol,
            'sol_price_eur': self.sol_price_eur,
            'timestamp': datetime.now(),
            'note': note
        }

        self.transactions.append(transaction)
        return transaction

    def get_transaction_history(self, limit: int = None) -> list:
        """
        Get transaction history

        Args:
            limit: Maximum number of transactions to return

        Returns:
            List of transactions
        """
        transactions = sorted(self.transactions, key=lambda x: x['timestamp'], reverse=True)

        if limit:
            transactions = transactions[:limit]

        return transactions

    def get_statistics(self) -> dict:
        """Get balance statistics"""
        return {
            'session_id': self.session_id,
            'current_balance_sol': self.balance_sol,
            'current_balance_eur': self.get_balance_eur(),
            'initial_balance_eur': self.initial_balance_eur,
            'total_pnl_sol': self.get_total_pnl_sol(),
            'total_pnl_eur': self.get_total_pnl_eur(),
            'total_pnl_percentage': self.get_total_pnl_percentage(),
            'sol_price_eur': self.sol_price_eur,
            'total_deposits': len([t for t in self.transactions if t['type'] == 'deposit']),
            'total_withdrawals': len([t for t in self.transactions if t['type'] == 'withdrawal'])
        }
