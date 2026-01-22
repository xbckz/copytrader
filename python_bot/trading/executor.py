"""
Trade execution module for Solana DEX trading
"""
import base64
from typing import Optional, Dict, Any
from decimal import Decimal

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from ..config import settings
from ..utils.logger import get_logger
from ..utils.helpers import retry_async, sol_to_lamports, lamports_to_sol
from ..blockchain.solana_client import SolanaClient
from .dex_client import JupiterClient

logger = get_logger(__name__)


class TradeExecutor:
    """Execute trades on Solana DEXs via Jupiter aggregator"""

    def __init__(
        self,
        solana_client: SolanaClient,
        jupiter_client: JupiterClient,
        wallet_keypair: Optional[Keypair] = None
    ):
        """
        Initialize trade executor

        Args:
            solana_client: Solana blockchain client
            jupiter_client: Jupiter DEX client
            wallet_keypair: Wallet keypair for signing transactions
        """
        self.solana = solana_client
        self.jupiter = jupiter_client
        self.wallet = wallet_keypair

        self.simulate_only = settings.simulate_trades

        logger.info(
            f"Trade executor initialized "
            f"(simulate_only: {self.simulate_only})"
        )

    def set_wallet(self, keypair: Keypair):
        """
        Set wallet keypair for signing transactions

        Args:
            keypair: Wallet keypair
        """
        self.wallet = keypair
        logger.info(f"Wallet set: {str(keypair.pubkey())[:8]}...")

    async def execute_buy(
        self,
        token_address: str,
        sol_amount: float,
        min_tokens_out: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a buy order (SOL -> Token)

        Args:
            token_address: Token mint address to buy
            sol_amount: Amount of SOL to spend
            min_tokens_out: Minimum tokens expected (slippage protection)

        Returns:
            Trade result dictionary or None if failed
        """
        if not self.wallet:
            logger.error("No wallet keypair set")
            return None

        try:
            logger.info(f"Executing BUY: {sol_amount} SOL -> {token_address[:8]}...")

            # Convert SOL to lamports
            lamports = sol_to_lamports(sol_amount)

            # Get quote from Jupiter
            quote = await self.jupiter.get_quote(
                input_mint=JupiterClient.WSOL,
                output_mint=token_address,
                amount=lamports,
                slippage_bps=settings.slippage_bps
            )

            if not quote:
                logger.error("Failed to get quote for buy")
                return None

            # Extract quote details
            out_amount = int(quote.get('outAmount', 0))
            price_impact = float(quote.get('priceImpactPct', 0))

            logger.info(
                f"Quote received: {out_amount} tokens, "
                f"price impact: {price_impact:.4f}%"
            )

            # Check minimum output
            if min_tokens_out and out_amount < min_tokens_out:
                logger.warning(
                    f"Output {out_amount} below minimum {min_tokens_out}, "
                    f"trade cancelled"
                )
                return None

            # If simulating, return mock result
            if self.simulate_only:
                logger.info("SIMULATION MODE - Trade not executed")
                return {
                    'success': True,
                    'simulated': True,
                    'signature': 'SIM_' + 'x' * 60,
                    'input_amount': sol_amount,
                    'output_amount': out_amount,
                    'token_address': token_address,
                    'price_impact': price_impact
                }

            # Get swap transaction
            swap_tx = await self.jupiter.get_swap_transaction(
                quote=quote,
                user_public_key=str(self.wallet.pubkey())
            )

            if not swap_tx:
                logger.error("Failed to get swap transaction")
                return None

            # Decode and sign transaction
            tx_bytes = base64.b64decode(swap_tx)
            transaction = VersionedTransaction.from_bytes(tx_bytes)

            # Sign transaction
            transaction.sign([self.wallet])

            # Send transaction
            signature = await self.solana.send_transaction(
                transaction,
                signers=[self.wallet],
                skip_preflight=False
            )

            logger.info(f"Buy transaction sent: {signature}")

            # Wait for confirmation
            confirmed = await self.solana.confirm_transaction(
                signature,
                timeout=settings.tx_confirmation_timeout
            )

            if confirmed:
                logger.info(f"Buy confirmed: {signature}")
                return {
                    'success': True,
                    'simulated': False,
                    'signature': signature,
                    'input_amount': sol_amount,
                    'output_amount': out_amount,
                    'token_address': token_address,
                    'price_impact': price_impact
                }
            else:
                logger.error(f"Buy confirmation timeout: {signature}")
                return None

        except Exception as e:
            logger.error(f"Error executing buy: {e}", exc_info=True)
            return None

    async def execute_sell(
        self,
        token_address: str,
        token_amount: int,
        min_sol_out: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a sell order (Token -> SOL)

        Args:
            token_address: Token mint address to sell
            token_amount: Amount of tokens to sell (in smallest unit)
            min_sol_out: Minimum SOL expected (slippage protection)

        Returns:
            Trade result dictionary or None if failed
        """
        if not self.wallet:
            logger.error("No wallet keypair set")
            return None

        try:
            logger.info(f"Executing SELL: {token_amount} of {token_address[:8]}...")

            # Get quote from Jupiter
            quote = await self.jupiter.get_quote(
                input_mint=token_address,
                output_mint=JupiterClient.WSOL,
                amount=token_amount,
                slippage_bps=settings.slippage_bps
            )

            if not quote:
                logger.error("Failed to get quote for sell")
                return None

            # Extract quote details
            out_lamports = int(quote.get('outAmount', 0))
            out_sol = lamports_to_sol(out_lamports)
            price_impact = float(quote.get('priceImpactPct', 0))

            logger.info(
                f"Quote received: {out_sol} SOL, "
                f"price impact: {price_impact:.4f}%"
            )

            # Check minimum output
            if min_sol_out and out_sol < min_sol_out:
                logger.warning(
                    f"Output {out_sol} SOL below minimum {min_sol_out} SOL, "
                    f"trade cancelled"
                )
                return None

            # If simulating, return mock result
            if self.simulate_only:
                logger.info("SIMULATION MODE - Trade not executed")
                return {
                    'success': True,
                    'simulated': True,
                    'signature': 'SIM_' + 'x' * 60,
                    'input_amount': token_amount,
                    'output_amount': out_sol,
                    'token_address': token_address,
                    'price_impact': price_impact
                }

            # Get swap transaction
            swap_tx = await self.jupiter.get_swap_transaction(
                quote=quote,
                user_public_key=str(self.wallet.pubkey())
            )

            if not swap_tx:
                logger.error("Failed to get swap transaction")
                return None

            # Decode and sign transaction
            tx_bytes = base64.b64decode(swap_tx)
            transaction = VersionedTransaction.from_bytes(tx_bytes)

            # Sign transaction
            transaction.sign([self.wallet])

            # Send transaction
            signature = await self.solana.send_transaction(
                transaction,
                signers=[self.wallet],
                skip_preflight=False
            )

            logger.info(f"Sell transaction sent: {signature}")

            # Wait for confirmation
            confirmed = await self.solana.confirm_transaction(
                signature,
                timeout=settings.tx_confirmation_timeout
            )

            if confirmed:
                logger.info(f"Sell confirmed: {signature}")
                return {
                    'success': True,
                    'simulated': False,
                    'signature': signature,
                    'input_amount': token_amount,
                    'output_amount': out_sol,
                    'token_address': token_address,
                    'price_impact': price_impact
                }
            else:
                logger.error(f"Sell confirmation timeout: {signature}")
                return None

        except Exception as e:
            logger.error(f"Error executing sell: {e}", exc_info=True)
            return None

    async def get_trade_quote(
        self,
        input_token: str,
        output_token: str,
        amount: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a trade quote without executing

        Args:
            input_token: Input token mint address
            output_token: Output token mint address
            amount: Input amount in smallest unit

        Returns:
            Quote details or None
        """
        try:
            quote = await self.jupiter.get_quote(
                input_mint=input_token,
                output_mint=output_token,
                amount=amount
            )

            if quote:
                return {
                    'input_amount': amount,
                    'output_amount': int(quote.get('outAmount', 0)),
                    'price_impact': float(quote.get('priceImpactPct', 0)),
                    'route': quote.get('routePlan', [])
                }

            return None

        except Exception as e:
            logger.error(f"Error getting trade quote: {e}")
            return None
