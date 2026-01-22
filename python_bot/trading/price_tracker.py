"""
Real-time price tracker for tokens
"""
import asyncio
from typing import Dict, Optional, Callable, List
from datetime import datetime
from collections import defaultdict

from ..config import settings
from ..utils.logger import get_logger
from .dex_client import JupiterClient

logger = get_logger(__name__)


class PriceTracker:
    """Track real-time prices for multiple tokens"""

    def __init__(
        self,
        jupiter_client: JupiterClient,
        update_interval: float = 1.0
    ):
        """
        Initialize price tracker

        Args:
            jupiter_client: Jupiter DEX client
            update_interval: Price update interval in seconds
        """
        self.jupiter = jupiter_client
        self.update_interval = update_interval

        # Token prices: token_address -> price
        self.prices: Dict[str, float] = {}

        # Price history: token_address -> list of (timestamp, price)
        self.price_history: Dict[str, List[tuple]] = defaultdict(list)
        self.max_history_length = 1000  # Keep last 1000 price points

        # Tracked tokens
        self.tracked_tokens: set = set()

        # Price update callbacks: token_address -> list of callbacks
        self.price_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Tracking state
        self.is_running = False
        self._track_task: Optional[asyncio.Task] = None

        logger.info(f"Price tracker initialized (update interval: {update_interval}s)")

    def add_token(self, token_address: str):
        """
        Add a token to track

        Args:
            token_address: Token mint address
        """
        self.tracked_tokens.add(token_address)
        logger.info(f"Added token to price tracking: {token_address[:8]}...")

    def add_tokens(self, token_addresses: List[str]):
        """
        Add multiple tokens to track

        Args:
            token_addresses: List of token mint addresses
        """
        for address in token_addresses:
            self.add_token(address)

    def remove_token(self, token_address: str):
        """
        Remove a token from tracking

        Args:
            token_address: Token mint address
        """
        self.tracked_tokens.discard(token_address)
        self.prices.pop(token_address, None)
        self.price_history.pop(token_address, None)
        self.price_callbacks.pop(token_address, None)

        logger.info(f"Removed token from price tracking: {token_address[:8]}...")

    def register_price_callback(
        self,
        token_address: str,
        callback: Callable[[str, float, float], None]
    ):
        """
        Register a callback for price updates

        Args:
            token_address: Token mint address
            callback: Async function called on price update
                     Signature: async def callback(token: str, old_price: float, new_price: float)
        """
        self.price_callbacks[token_address].append(callback)
        logger.debug(f"Registered price callback for {token_address[:8]}...")

    async def start(self):
        """Start price tracking"""
        if self.is_running:
            logger.warning("Price tracker already running")
            return

        if not self.tracked_tokens:
            logger.warning("No tokens to track")
            return

        self.is_running = True
        logger.info(f"Starting price tracker for {len(self.tracked_tokens)} tokens")

        # Start tracking task
        self._track_task = asyncio.create_task(self._tracking_loop())

    async def stop(self):
        """Stop price tracking"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("Stopping price tracker")

        if self._track_task:
            self._track_task.cancel()
            try:
                await self._track_task
            except asyncio.CancelledError:
                pass

    async def _tracking_loop(self):
        """Main price tracking loop"""
        logger.info("Price tracking loop started")

        while self.is_running:
            try:
                await self._update_all_prices()
                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                logger.info("Price tracking loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in price tracking loop: {e}", exc_info=True)
                await asyncio.sleep(self.update_interval)

    async def _update_all_prices(self):
        """Update prices for all tracked tokens"""
        if not self.tracked_tokens:
            return

        try:
            # Fetch prices for all tokens at once
            token_list = list(self.tracked_tokens)
            new_prices = await self.jupiter.get_multiple_prices(token_list)

            # Update prices and trigger callbacks
            for token_address, new_price in new_prices.items():
                old_price = self.prices.get(token_address, 0)

                # Update price
                self.prices[token_address] = new_price

                # Add to history
                timestamp = datetime.now()
                self.price_history[token_address].append((timestamp, new_price))

                # Trim history if too long
                if len(self.price_history[token_address]) > self.max_history_length:
                    self.price_history[token_address] = \
                        self.price_history[token_address][-self.max_history_length:]

                # Trigger callbacks if price changed significantly
                if old_price > 0:
                    price_change_pct = abs((new_price - old_price) / old_price) * 100

                    if price_change_pct > 0.1:  # 0.1% change threshold
                        await self._notify_price_callbacks(token_address, old_price, new_price)

        except Exception as e:
            logger.error(f"Error updating prices: {e}")

    async def _notify_price_callbacks(
        self,
        token_address: str,
        old_price: float,
        new_price: float
    ):
        """
        Notify registered callbacks about price change

        Args:
            token_address: Token mint address
            old_price: Previous price
            new_price: New price
        """
        callbacks = self.price_callbacks.get(token_address, [])

        for callback in callbacks:
            try:
                await callback(token_address, old_price, new_price)
            except Exception as e:
                logger.error(f"Error in price callback: {e}", exc_info=True)

    def get_price(self, token_address: str) -> Optional[float]:
        """
        Get current price for a token

        Args:
            token_address: Token mint address

        Returns:
            Current price or None
        """
        return self.prices.get(token_address)

    def get_price_change(
        self,
        token_address: str,
        timeframe_seconds: Optional[int] = None
    ) -> Optional[float]:
        """
        Get price change percentage over a timeframe

        Args:
            token_address: Token mint address
            timeframe_seconds: Timeframe in seconds (None = since tracking started)

        Returns:
            Price change percentage or None
        """
        history = self.price_history.get(token_address, [])

        if len(history) < 2:
            return None

        current_price = history[-1][1]

        if timeframe_seconds:
            # Find price from timeframe ago
            cutoff_time = datetime.now().timestamp() - timeframe_seconds
            for timestamp, price in reversed(history[:-1]):
                if timestamp.timestamp() <= cutoff_time:
                    old_price = price
                    break
            else:
                old_price = history[0][1]  # Use first available price
        else:
            old_price = history[0][1]  # First price

        if old_price == 0:
            return None

        return ((current_price - old_price) / old_price) * 100

    def get_status(self) -> Dict[str, any]:
        """
        Get tracker status

        Returns:
            Status dictionary
        """
        return {
            'is_running': self.is_running,
            'tracked_tokens': len(self.tracked_tokens),
            'update_interval': self.update_interval,
            'prices_cached': len(self.prices),
            'tokens': list(self.tracked_tokens)
        }
