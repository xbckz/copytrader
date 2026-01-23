"""
Helius API Client - Enhanced Solana RPC with additional features
"""
from typing import Optional, List, Dict
import aiohttp
import asyncio

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HeliusClient:
    """Client for Helius enhanced RPC API"""

    def __init__(self, api_key: str = None):
        """
        Initialize Helius client

        Args:
            api_key: Helius API key
        """
        self.api_key = api_key or settings.helius_api_key
        self.use_helius = settings.use_helius and self.api_key is not None

        if self.use_helius:
            # Helius enhanced RPC endpoints
            if settings.solana_network == "mainnet-beta":
                self.rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"
            else:
                self.rpc_url = f"https://devnet.helius-rpc.com/?api-key={self.api_key}"

            self.api_url = f"https://api.helius.xyz/v0"
        else:
            self.rpc_url = settings.solana_rpc_url
            self.api_url = None

        self.session: Optional[aiohttp.ClientSession] = None
        self._initialized = False

        logger.info(f"Helius client initialized: {'Enabled' if self.use_helius else 'Disabled'}")

    async def initialize(self):
        """Initialize HTTP session"""
        if self._initialized:
            return

        self.session = aiohttp.ClientSession()
        self._initialized = True

        logger.info("Helius client session initialized")

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self._initialized = False
            logger.info("Helius client session closed")

    async def get_parsed_transactions(
        self,
        address: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get parsed transaction history for an address (Helius enhanced)

        Args:
            address: Wallet address
            limit: Maximum number of transactions

        Returns:
            List of parsed transactions
        """
        if not self.use_helius or not self.api_url:
            logger.warning("Helius API not available, cannot fetch parsed transactions")
            return []

        try:
            url = f"{self.api_url}/addresses/{address}/transactions"
            params = {
                'api-key': self.api_key,
                'limit': limit
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Fetched {len(data)} parsed transactions for {address[:8]}...")
                    return data
                else:
                    logger.error(f"Failed to fetch parsed transactions: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching parsed transactions: {e}")
            return []

    async def get_token_balances(self, address: str) -> List[Dict]:
        """
        Get token balances for an address (Helius enhanced)

        Args:
            address: Wallet address

        Returns:
            List of token balances
        """
        if not self.use_helius or not self.api_url:
            logger.warning("Helius API not available, cannot fetch token balances")
            return []

        try:
            url = f"{self.api_url}/addresses/{address}/balances"
            params = {'api-key': self.api_key}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tokens = data.get('tokens', [])
                    logger.debug(f"Fetched {len(tokens)} token balances for {address[:8]}...")
                    return tokens
                else:
                    logger.error(f"Failed to fetch token balances: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching token balances: {e}")
            return []

    async def get_wallet_performance(self, address: str, days: int = 30) -> Dict:
        """
        Get wallet performance metrics (simulated for now)

        Args:
            address: Wallet address
            days: Number of days to analyze

        Returns:
            Performance metrics
        """
        # Get recent transactions
        transactions = await self.get_parsed_transactions(address, limit=100)

        # Analyze transactions to extract performance metrics
        total_trades = 0
        successful_trades = 0
        total_volume = 0.0

        for tx in transactions:
            # Check if it's a swap/trade transaction
            tx_type = tx.get('type', '')
            if 'SWAP' in tx_type or 'swap' in tx_type.lower():
                total_trades += 1
                # Simple heuristic: if fee is paid, assume successful
                if tx.get('fee', 0) > 0:
                    successful_trades += 1

                # Sum up native transfers as volume
                for transfer in tx.get('nativeTransfers', []):
                    total_volume += transfer.get('amount', 0) / 1e9  # Convert lamports to SOL

        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0.0

        metrics = {
            'address': address,
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'win_rate': win_rate,
            'total_volume_sol': total_volume,
            'analysis_period_days': days
        }

        logger.debug(f"Wallet performance for {address[:8]}...: {total_trades} trades, {win_rate:.1f}% win rate")

        return metrics

    async def get_token_metadata(self, token_address: str) -> Optional[Dict]:
        """
        Get token metadata (name, symbol, decimals, etc.)

        Args:
            token_address: Token mint address

        Returns:
            Token metadata or None
        """
        if not self.use_helius or not self.api_url:
            return None

        try:
            url = f"{self.api_url}/token-metadata"
            params = {
                'api-key': self.api_key
            }
            data = {
                'mintAccounts': [token_address]
            }

            async with self.session.post(url, params=params, json=data) as response:
                if response.status == 200:
                    results = await response.json()
                    if results and len(results) > 0:
                        metadata = results[0]
                        logger.debug(f"Fetched metadata for token {token_address[:8]}...")
                        return metadata
                    return None
                else:
                    logger.error(f"Failed to fetch token metadata: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching token metadata: {e}")
            return None

    async def get_transaction_details(self, signature: str) -> Optional[Dict]:
        """
        Get detailed parsed transaction information

        Args:
            signature: Transaction signature

        Returns:
            Transaction details or None
        """
        if not self.use_helius or not self.api_url:
            return None

        try:
            url = f"{self.api_url}/transactions"
            params = {
                'api-key': self.api_key
            }
            data = {
                'transactions': [signature]
            }

            async with self.session.post(url, params=params, json=data) as response:
                if response.status == 200:
                    results = await response.json()
                    if results and len(results) > 0:
                        return results[0]
                    return None
                else:
                    logger.error(f"Failed to fetch transaction details: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching transaction details: {e}")
            return None

    async def webhooks_subscribe(
        self,
        webhook_url: str,
        addresses: List[str],
        transaction_types: List[str] = None
    ) -> Optional[str]:
        """
        Subscribe to webhook notifications for addresses (Helius feature)

        Args:
            webhook_url: Webhook URL to receive notifications
            addresses: List of addresses to monitor
            transaction_types: List of transaction types to filter

        Returns:
            Webhook ID or None
        """
        if not self.use_helius or not self.api_url:
            logger.warning("Helius API not available, cannot create webhook")
            return None

        try:
            url = f"{self.api_url}/webhooks"
            params = {'api-key': self.api_key}
            data = {
                'webhookURL': webhook_url,
                'transactionTypes': transaction_types or ['ANY'],
                'accountAddresses': addresses,
                'webhookType': 'enhanced'
            }

            async with self.session.post(url, params=params, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    webhook_id = result.get('webhookID')
                    logger.info(f"Webhook created: {webhook_id}")
                    return webhook_id
                else:
                    logger.error(f"Failed to create webhook: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return None

    def get_rpc_url(self) -> str:
        """Get RPC URL (Helius or default)"""
        return self.rpc_url

    def is_available(self) -> bool:
        """Check if Helius is available and enabled"""
        return self.use_helius and self._initialized
