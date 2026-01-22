"""
Jupiter DEX aggregator client for Solana trading
"""
import aiohttp
from typing import Optional, Dict, Any, List
import asyncio
import base64

from ..config import settings
from ..utils.logger import get_logger
from ..utils.helpers import retry_async

logger = get_logger(__name__)


class JupiterClient:
    """Client for Jupiter DEX aggregator API"""

    # Jupiter API endpoints
    JUPITER_V6_API = "https://quote-api.jup.ag/v6"
    PRICE_API = "https://price.jup.ag/v4"

    # Common token addresses on Solana
    WSOL = "So11111111111111111111111111111111111111112"  # Wrapped SOL
    USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    def __init__(self):
        """Initialize Jupiter client"""
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("Jupiter DEX client initialized")

    async def connect(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("Jupiter HTTP session created")

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Jupiter HTTP session closed")

    @retry_async(max_retries=3, delay=1.0)
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a swap quote from Jupiter

        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount: Amount in smallest unit (lamports for SOL)
            slippage_bps: Slippage in basis points (default from settings)

        Returns:
            Quote data or None if error
        """
        if not self.session:
            await self.connect()

        slippage = slippage_bps or settings.slippage_bps

        url = f"{self.JUPITER_V6_API}/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': str(amount),
            'slippageBps': str(slippage),
            'onlyDirectRoutes': 'false'  # Allow multi-hop routes
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Got quote: {amount} {input_mint[:8]}... -> {output_mint[:8]}...")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Quote error ({response.status}): {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None

    @retry_async(max_retries=3, delay=1.0)
    async def get_swap_transaction(
        self,
        quote: Dict[str, Any],
        user_public_key: str,
        wrap_unwrap_sol: bool = True
    ) -> Optional[str]:
        """
        Get swap transaction from Jupiter quote

        Args:
            quote: Quote data from get_quote()
            user_public_key: User's wallet public key
            wrap_unwrap_sol: Automatically wrap/unwrap SOL

        Returns:
            Base64 encoded transaction or None
        """
        if not self.session:
            await self.connect()

        url = f"{self.JUPITER_V6_API}/swap"
        payload = {
            'quoteResponse': quote,
            'userPublicKey': user_public_key,
            'wrapAndUnwrapSol': wrap_unwrap_sol,
            'computeUnitPriceMicroLamports': settings.priority_fee_lamports
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    swap_transaction = data.get('swapTransaction')
                    logger.debug("Got swap transaction from Jupiter")
                    return swap_transaction
                else:
                    error_text = await response.text()
                    logger.error(f"Swap transaction error ({response.status}): {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Error getting swap transaction: {e}")
            return None

    @retry_async(max_retries=3, delay=1.0)
    async def get_token_price(
        self,
        token_address: str,
        vs_token: Optional[str] = None
    ) -> Optional[float]:
        """
        Get token price from Jupiter Price API

        Args:
            token_address: Token mint address
            vs_token: Price denominated in this token (default: USDC)

        Returns:
            Token price or None
        """
        if not self.session:
            await self.connect()

        vs = vs_token or self.USDC
        url = f"{self.PRICE_API}/price"
        params = {
            'ids': token_address,
            'vsToken': vs
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    price_data = data.get('data', {}).get(token_address, {})
                    price = price_data.get('price')

                    if price:
                        logger.debug(f"Price for {token_address[:8]}...: ${price}")
                        return float(price)
                    else:
                        logger.warning(f"No price data for {token_address}")
                        return None
                else:
                    logger.error(f"Price API error: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error getting token price: {e}")
            return None

    @retry_async(max_retries=3, delay=1.0)
    async def get_multiple_prices(
        self,
        token_addresses: List[str],
        vs_token: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get prices for multiple tokens

        Args:
            token_addresses: List of token mint addresses
            vs_token: Price denominated in this token (default: USDC)

        Returns:
            Dictionary mapping token address to price
        """
        if not self.session:
            await self.connect()

        vs = vs_token or self.USDC
        url = f"{self.PRICE_API}/price"

        # Jupiter API accepts comma-separated IDs
        ids = ','.join(token_addresses)
        params = {
            'ids': ids,
            'vsToken': vs
        }

        prices = {}

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    price_data = data.get('data', {})

                    for token_address in token_addresses:
                        token_price = price_data.get(token_address, {}).get('price')
                        if token_price:
                            prices[token_address] = float(token_price)

                    logger.debug(f"Got prices for {len(prices)} tokens")
                    return prices
                else:
                    logger.error(f"Price API error: {response.status}")
                    return prices

        except Exception as e:
            logger.error(f"Error getting multiple prices: {e}")
            return prices

    async def calculate_output_amount(
        self,
        input_mint: str,
        output_mint: str,
        input_amount: int
    ) -> Optional[int]:
        """
        Calculate expected output amount for a swap

        Args:
            input_mint: Input token mint
            output_mint: Output token mint
            input_amount: Input amount in smallest unit

        Returns:
            Expected output amount or None
        """
        quote = await self.get_quote(input_mint, output_mint, input_amount)

        if quote:
            out_amount = quote.get('outAmount')
            if out_amount:
                return int(out_amount)

        return None

    async def get_sol_price_usd(self) -> Optional[float]:
        """
        Get current SOL price in USD

        Returns:
            SOL price in USD or None
        """
        return await self.get_token_price(self.WSOL, self.USDC)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
