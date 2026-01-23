"""
Fee Calculator - Calculates realistic transaction fees for Solana swaps
"""
from typing import Dict
import random

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FeeCalculator:
    """Calculates realistic fees for Solana transactions"""

    def __init__(self):
        """Initialize fee calculator"""
        # Base Solana network fee (typically ~0.000005 SOL)
        self.base_network_fee = settings.base_network_fee

        # Priority fee (configurable, typically 0.00001 - 0.0001 SOL)
        self.priority_fee_lamports = settings.priority_fee_lamports
        self.priority_fee_sol = self.priority_fee_lamports / 1_000_000_000

        # Jupiter platform fee (typically 0.25% = 25 bps)
        self.jupiter_fee_bps = settings.jupiter_platform_fee_bps

        logger.info(
            f"Fee calculator initialized: "
            f"Network={self.base_network_fee:.6f} SOL, "
            f"Priority={self.priority_fee_sol:.6f} SOL, "
            f"Jupiter={self.jupiter_fee_bps} bps"
        )

    def calculate_swap_fees(
        self,
        amount_sol: float,
        slippage_bps: int = None,
        use_priority: bool = True
    ) -> Dict[str, float]:
        """
        Calculate all fees for a swap transaction

        Args:
            amount_sol: Swap amount in SOL
            slippage_bps: Slippage tolerance in basis points
            use_priority: Use priority fee for faster execution

        Returns:
            Dictionary with fee breakdown
        """
        slippage_bps = slippage_bps or settings.slippage_bps

        # Network fee (base transaction fee)
        network_fee = self.base_network_fee

        # Priority fee (optional, for faster execution)
        priority_fee = self.priority_fee_sol if use_priority else 0.0

        # Platform fee (Jupiter charges ~0.25% of swap amount)
        platform_fee = (amount_sol * self.jupiter_fee_bps) / 10000

        # Simulate actual slippage (usually less than max tolerance)
        # Actual slippage is typically 0-50% of max slippage tolerance
        actual_slippage_bps = random.uniform(0, slippage_bps * 0.5)
        slippage_cost = (amount_sol * actual_slippage_bps) / 10000

        # Price impact (varies based on liquidity and trade size)
        # Smaller trades have less impact, larger trades more
        # Simulate realistic price impact: 0.01% - 1%
        price_impact_bps = self._calculate_price_impact(amount_sol)
        price_impact_cost = (amount_sol * price_impact_bps) / 10000

        # Total fees
        total_fee = (
            network_fee +
            priority_fee +
            platform_fee +
            slippage_cost +
            price_impact_cost
        )

        fees = {
            'network_fee': network_fee,
            'priority_fee': priority_fee,
            'platform_fee': platform_fee,
            'slippage_cost': slippage_cost,
            'slippage_percentage': actual_slippage_bps / 100,
            'price_impact_cost': price_impact_cost,
            'price_impact_percentage': price_impact_bps / 100,
            'total_fee': total_fee,
            'total_fee_percentage': (total_fee / amount_sol * 100) if amount_sol > 0 else 0
        }

        logger.debug(
            f"Fees calculated for {amount_sol:.6f} SOL swap: "
            f"Total={total_fee:.6f} SOL ({fees['total_fee_percentage']:.2f}%)"
        )

        return fees

    def _calculate_price_impact(self, amount_sol: float) -> float:
        """
        Calculate realistic price impact based on trade size

        Args:
            amount_sol: Trade amount in SOL

        Returns:
            Price impact in basis points
        """
        # Simulate realistic price impact based on trade size
        # Small trades: 1-10 bps (0.01%-0.1%)
        # Medium trades: 10-50 bps (0.1%-0.5%)
        # Large trades: 50-100 bps (0.5%-1%)

        if amount_sol < 0.1:
            # Very small trades: 1-5 bps
            return random.uniform(1, 5)
        elif amount_sol < 0.5:
            # Small trades: 5-15 bps
            return random.uniform(5, 15)
        elif amount_sol < 1.0:
            # Medium trades: 15-30 bps
            return random.uniform(15, 30)
        elif amount_sol < 5.0:
            # Large trades: 30-60 bps
            return random.uniform(30, 60)
        else:
            # Very large trades: 60-100 bps
            return random.uniform(60, 100)

    def estimate_total_cost(
        self,
        amount_sol: float,
        slippage_bps: int = None
    ) -> float:
        """
        Estimate total cost including all fees

        Args:
            amount_sol: Swap amount
            slippage_bps: Slippage tolerance

        Returns:
            Total cost in SOL
        """
        fees = self.calculate_swap_fees(amount_sol, slippage_bps)
        return amount_sol + fees['total_fee']

    def estimate_net_proceeds(
        self,
        amount_sol: float,
        slippage_bps: int = None
    ) -> float:
        """
        Estimate net proceeds after fees

        Args:
            amount_sol: Swap amount
            slippage_bps: Slippage tolerance

        Returns:
            Net proceeds in SOL
        """
        fees = self.calculate_swap_fees(amount_sol, slippage_bps)
        return amount_sol - fees['total_fee']

    def get_fee_breakdown_text(self, fees: dict) -> str:
        """
        Generate human-readable fee breakdown

        Args:
            fees: Fee dictionary from calculate_swap_fees

        Returns:
            Formatted string
        """
        lines = [
            "Fee Breakdown:",
            f"  Network Fee: {fees['network_fee']:.6f} SOL",
            f"  Priority Fee: {fees['priority_fee']:.6f} SOL",
            f"  Platform Fee: {fees['platform_fee']:.6f} SOL ({self.jupiter_fee_bps} bps)",
            f"  Slippage Cost: {fees['slippage_cost']:.6f} SOL ({fees['slippage_percentage']:.2f}%)",
            f"  Price Impact: {fees['price_impact_cost']:.6f} SOL ({fees['price_impact_percentage']:.2f}%)",
            f"  ─────────────────────",
            f"  Total Fees: {fees['total_fee']:.6f} SOL ({fees['total_fee_percentage']:.2f}%)"
        ]
        return "\n".join(lines)

    def simulate_execution_price(
        self,
        expected_price: float,
        slippage_bps: int = None,
        is_buy: bool = True
    ) -> Dict[str, float]:
        """
        Simulate actual execution price with slippage

        Args:
            expected_price: Expected price
            slippage_bps: Slippage tolerance
            is_buy: True for buy, False for sell

        Returns:
            Dictionary with price simulation
        """
        slippage_bps = slippage_bps or settings.slippage_bps

        # Actual slippage is typically 0-50% of max tolerance
        actual_slippage_bps = random.uniform(0, slippage_bps * 0.5)
        actual_slippage_decimal = actual_slippage_bps / 10000

        # For buys: price goes up (worse for buyer)
        # For sells: price goes down (worse for seller)
        if is_buy:
            actual_price = expected_price * (1 + actual_slippage_decimal)
        else:
            actual_price = expected_price * (1 - actual_slippage_decimal)

        return {
            'expected_price': expected_price,
            'actual_price': actual_price,
            'slippage_bps': actual_slippage_bps,
            'slippage_percentage': actual_slippage_bps / 100,
            'price_difference': actual_price - expected_price,
            'price_difference_percentage': ((actual_price - expected_price) / expected_price * 100)
        }

    def update_priority_fee(self, lamports: int):
        """
        Update priority fee

        Args:
            lamports: Priority fee in lamports
        """
        self.priority_fee_lamports = lamports
        self.priority_fee_sol = lamports / 1_000_000_000
        logger.info(f"Priority fee updated: {lamports} lamports ({self.priority_fee_sol:.6f} SOL)")

    def update_platform_fee(self, bps: int):
        """
        Update platform fee

        Args:
            bps: Platform fee in basis points
        """
        self.jupiter_fee_bps = bps
        logger.info(f"Platform fee updated: {bps} bps ({bps/100:.2f}%)")
