"""
Solana blockchain client for RPC interactions
"""
import asyncio
from typing import Optional, List, Dict, Any
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.signature import Signature
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from solders.rpc.responses import GetTransactionResp

from ..config import settings
from ..utils.logger import get_logger
from ..utils.helpers import retry_async, lamports_to_sol

logger = get_logger(__name__)


class SolanaClient:
    """Client for interacting with Solana blockchain"""

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        commitment: str = "confirmed"
    ):
        """
        Initialize Solana client

        Args:
            rpc_url: Solana RPC endpoint URL
            commitment: Transaction commitment level
        """
        self.rpc_url = rpc_url or settings.solana_rpc_url
        self.commitment = Confirmed if commitment == "confirmed" else Finalized
        self.client: Optional[AsyncClient] = None
        self._is_connected = False

        logger.info(f"Initializing Solana client for {self.rpc_url}")

    async def connect(self):
        """Establish connection to Solana RPC"""
        try:
            self.client = AsyncClient(self.rpc_url, commitment=self.commitment)

            # Test connection
            version = await self.client.get_version()
            logger.info(f"Connected to Solana RPC: {version}")

            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Solana RPC: {e}")
            self._is_connected = False
            raise

    async def disconnect(self):
        """Close connection to Solana RPC"""
        if self.client:
            await self.client.close()
            self._is_connected = False
            logger.info("Disconnected from Solana RPC")

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._is_connected

    @retry_async(max_retries=3, delay=1.0)
    async def get_balance(self, pubkey: str) -> float:
        """
        Get SOL balance for a wallet

        Args:
            pubkey: Wallet public key

        Returns:
            Balance in SOL
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            pk = Pubkey.from_string(pubkey)
            response = await self.client.get_balance(pk)
            lamports = response.value
            sol_balance = lamports_to_sol(lamports)

            logger.debug(f"Balance for {pubkey[:8]}...: {sol_balance} SOL")
            return sol_balance

        except Exception as e:
            logger.error(f"Error getting balance for {pubkey}: {e}")
            raise

    @retry_async(max_retries=3, delay=1.0)
    async def get_transaction(
        self,
        signature: str,
        max_supported_transaction_version: int = 0
    ) -> Optional[GetTransactionResp]:
        """
        Get transaction details by signature

        Args:
            signature: Transaction signature
            max_supported_transaction_version: Max transaction version

        Returns:
            Transaction details or None if not found
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            sig = Signature.from_string(signature)
            response = await self.client.get_transaction(
                sig,
                max_supported_transaction_version=max_supported_transaction_version
            )

            if response.value:
                logger.debug(f"Retrieved transaction {signature[:8]}...")
                return response
            else:
                logger.warning(f"Transaction not found: {signature}")
                return None

        except Exception as e:
            logger.error(f"Error getting transaction {signature}: {e}")
            raise

    @retry_async(max_retries=3, delay=1.0)
    async def get_signatures_for_address(
        self,
        address: str,
        limit: int = 10,
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transaction signatures for an address

        Args:
            address: Wallet address
            limit: Maximum number of signatures to return
            before: Get signatures before this signature

        Returns:
            List of signature info dictionaries
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            pk = Pubkey.from_string(address)
            before_sig = Signature.from_string(before) if before else None

            response = await self.client.get_signatures_for_address(
                pk,
                limit=limit,
                before=before_sig
            )

            signatures = []
            if response.value:
                for sig_info in response.value:
                    signatures.append({
                        'signature': str(sig_info.signature),
                        'slot': sig_info.slot,
                        'block_time': sig_info.block_time,
                        'err': sig_info.err
                    })

            logger.debug(f"Found {len(signatures)} signatures for {address[:8]}...")
            return signatures

        except Exception as e:
            logger.error(f"Error getting signatures for {address}: {e}")
            raise

    @retry_async(max_retries=3, delay=2.0, backoff=2.0)
    async def get_recent_blockhash(self) -> str:
        """
        Get recent blockhash for transactions

        Returns:
            Recent blockhash as string
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            response = await self.client.get_latest_blockhash()
            blockhash = str(response.value.blockhash)
            logger.debug(f"Recent blockhash: {blockhash[:8]}...")
            return blockhash

        except Exception as e:
            logger.error(f"Error getting recent blockhash: {e}")
            raise

    @retry_async(max_retries=3, delay=1.0)
    async def get_token_accounts_by_owner(
        self,
        owner: str,
        program_id: str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    ) -> List[Dict[str, Any]]:
        """
        Get token accounts owned by an address

        Args:
            owner: Owner's public key
            program_id: Token program ID (default: SPL Token)

        Returns:
            List of token account info
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            owner_pk = Pubkey.from_string(owner)
            program_pk = Pubkey.from_string(program_id)

            response = await self.client.get_token_accounts_by_owner(
                owner_pk,
                {"programId": program_pk}
            )

            accounts = []
            if response.value:
                for account in response.value:
                    accounts.append({
                        'pubkey': str(account.pubkey),
                        'account': account.account
                    })

            logger.debug(f"Found {len(accounts)} token accounts for {owner[:8]}...")
            return accounts

        except Exception as e:
            logger.error(f"Error getting token accounts for {owner}: {e}")
            raise

    async def send_transaction(
        self,
        transaction: Transaction,
        signers: List[Keypair],
        skip_preflight: bool = False
    ) -> str:
        """
        Send a transaction to the network

        Args:
            transaction: Transaction to send
            signers: List of keypairs to sign with
            skip_preflight: Skip preflight transaction checks

        Returns:
            Transaction signature
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            # Sign transaction
            for signer in signers:
                transaction.sign([signer])

            # Send transaction
            response = await self.client.send_transaction(
                transaction,
                skip_preflight=skip_preflight
            )

            signature = str(response.value)
            logger.info(f"Transaction sent: {signature}")
            return signature

        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            raise

    async def confirm_transaction(
        self,
        signature: str,
        timeout: int = 60
    ) -> bool:
        """
        Wait for transaction confirmation

        Args:
            signature: Transaction signature to confirm
            timeout: Maximum time to wait in seconds

        Returns:
            True if confirmed, False if timeout
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        try:
            sig = Signature.from_string(signature)

            # Wait for confirmation with timeout
            start_time = asyncio.get_event_loop().time()

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                response = await self.client.get_signature_statuses([sig])

                if response.value and response.value[0]:
                    status = response.value[0]
                    if status.confirmation_status in ["confirmed", "finalized"]:
                        logger.info(f"Transaction confirmed: {signature}")
                        return True
                    elif status.err:
                        logger.error(f"Transaction failed: {status.err}")
                        return False

                await asyncio.sleep(2)

            logger.warning(f"Transaction confirmation timeout: {signature}")
            return False

        except Exception as e:
            logger.error(f"Error confirming transaction {signature}: {e}")
            return False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
