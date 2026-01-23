"""
KOLscan API client for fetching top performing wallets
"""
import aiohttp
from typing import List, Dict, Any, Optional
import asyncio

from ..config import settings
from ..utils.logger import get_logger
from ..utils.helpers import retry_async

logger = get_logger(__name__)


class KOLscanClient:
    """Client for interacting with KOLscan API"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize KOLscan client

        Args:
            api_url: KOLscan API base URL
            api_key: KOLscan API key
        """
        self.api_url = api_url or settings.kolscan_api_url
        self.api_key = api_key or settings.kolscan_api_key

        self.session: Optional[aiohttp.ClientSession] = None

        logger.info("KOLscan client initialized")

    async def connect(self):
        """Initialize HTTP session"""
        if not self.session:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            self.session = aiohttp.ClientSession(headers=headers)
            logger.info("KOLscan HTTP session created")

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("KOLscan HTTP session closed")

    @retry_async(max_retries=3, delay=2.0)
    async def get_top_wallets(
        self,
        limit: int = 100,
        timeframe: str = "7d",
        min_pnl: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch top performing wallets from KOLscan

        Args:
            limit: Number of wallets to fetch
            timeframe: Timeframe for performance (1d, 7d, 30d)
            min_pnl: Minimum PnL filter

        Returns:
            List of wallet data dictionaries
        """
        if not self.session:
            await self.connect()

        # Note: This is a placeholder for the actual KOLscan API
        # Replace with real API endpoint when available
        endpoint = f"{self.api_url}/wallets/top"

        params = {
            'limit': limit,
            'timeframe': timeframe,
            'sort': 'pnl_desc'
        }

        if min_pnl:
            params['min_pnl'] = min_pnl

        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    wallets = data.get('wallets', [])

                    logger.info(f"Fetched {len(wallets)} top wallets from KOLscan")
                    return wallets
                elif response.status == 401:
                    logger.error("KOLscan API authentication failed - check API key")
                    return []
                else:
                    logger.error(f"KOLscan API error: {response.status}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching top wallets: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching top wallets: {e}")
            return []

    async def get_wallet_details(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific wallet

        Args:
            wallet_address: Wallet public key

        Returns:
            Wallet details or None
        """
        if not self.session:
            await self.connect()

        endpoint = f"{self.api_url}/wallets/{wallet_address}"

        try:
            async with self.session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Fetched details for wallet {wallet_address[:8]}...")
                    return data
                else:
                    logger.warning(f"Wallet details not found: {wallet_address}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching wallet details for {wallet_address}: {e}")
            return None

    async def get_fallback_wallets(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Fallback method when KOLscan API is not available
        Returns empty list - use manual wallet tracking instead

        Args:
            count: Number of wallets to return

        Returns:
            Empty list (no placeholder data)
        """
        logger.warning(
            "KOLscan API not available. "
            "Please use manual wallet tracking to add wallets to monitor."
        )
        return []

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
