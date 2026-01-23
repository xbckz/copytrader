#!/usr/bin/env python3
"""
MEV Protection Checker for Solana
Monitors a Solana address to detect if it's using MEV protection services like Jito.
"""

import asyncio
import sys
from datetime import datetime
from typing import Set, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solders.pubkey import Pubkey
from solders.signature import Signature


class TransactionStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"
    MEV_PROTECTED = "mev_protected"


@dataclass
class TransactionEvent:
    signature: str
    timestamp: datetime
    status: TransactionStatus
    block_time: Optional[int] = None
    slot: Optional[int] = None


class MEVProtectionChecker:
    """
    Monitors a Solana address to detect MEV protection usage.

    MEV Protection Detection:
    - Transactions that appear in blocks without being seen in mempool first
    - Transactions submitted via private RPCs (like Jito)
    - Low latency between submission and confirmation
    """

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.client = AsyncClient(rpc_url)
        self.monitored_address: Optional[Pubkey] = None
        self.seen_signatures: Set[str] = set()
        self.pending_transactions: Dict[str, TransactionEvent] = {}
        self.confirmed_transactions: Dict[str, TransactionEvent] = {}
        self.last_signature: Optional[Signature] = None

        # Statistics
        self.total_transactions = 0
        self.mev_protected_count = 0
        self.public_mempool_count = 0

    async def connect(self):
        """Establish connection to Solana RPC"""
        try:
            version = await self.client.get_version()
            print(f"✓ Connected to Solana RPC")
            # version.value is a RpcVersionInfo object, access as attribute
            if hasattr(version.value, 'solana_core'):
                print(f"  Solana version: {version.value.solana_core}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to RPC: {e}")
            return False

    async def validate_address(self, address_str: str) -> Optional[Pubkey]:
        """Validate and convert address string to Pubkey"""
        try:
            pubkey = Pubkey.from_string(address_str)

            # Check if account exists
            response = await self.client.get_account_info(pubkey)
            if response.value is None:
                print(f"⚠ Warning: Address {address_str} has no account data (may be new)")

            return pubkey
        except Exception as e:
            print(f"✗ Invalid address: {e}")
            return None

    async def check_pending_transactions(self) -> Set[str]:
        """
        Check for pending transactions in the mempool.
        Note: Solana doesn't have a traditional mempool, but we can check
        transaction statuses to see if they're pending.
        """
        pending_sigs = set()

        try:
            # Get recent signatures for the address
            response = await self.client.get_signatures_for_address(
                self.monitored_address,
                limit=20
            )

            if response.value:
                for sig_info in response.value:
                    sig_str = str(sig_info.signature)

                    # Skip already processed signatures
                    if sig_str in self.seen_signatures:
                        continue

                    # Check if transaction is pending (no block_time yet)
                    if sig_info.block_time is None and sig_info.err is None:
                        pending_sigs.add(sig_str)

                        if sig_str not in self.pending_transactions:
                            event = TransactionEvent(
                                signature=sig_str,
                                timestamp=datetime.now(),
                                status=TransactionStatus.PENDING
                            )
                            self.pending_transactions[sig_str] = event
                            print(f"  📋 Pending: {sig_str[:16]}...")

        except Exception as e:
            print(f"  ⚠ Error checking pending: {e}")

        return pending_sigs

    async def check_confirmed_transactions(self):
        """Check for new confirmed transactions"""
        try:
            # Get signatures with confirmed commitment
            response = await self.client.get_signatures_for_address(
                self.monitored_address,
                limit=10,
                commitment=Confirmed
            )

            if not response.value:
                return

            for sig_info in response.value:
                sig_str = str(sig_info.signature)

                # Skip if we've already processed this signature
                if sig_str in self.confirmed_transactions:
                    continue

                # Skip failed transactions
                if sig_info.err is not None:
                    self.seen_signatures.add(sig_str)
                    continue

                # New confirmed transaction found
                self.total_transactions += 1

                # Check if we saw this transaction as pending
                was_pending = sig_str in self.pending_transactions

                event = TransactionEvent(
                    signature=sig_str,
                    timestamp=datetime.now(),
                    status=TransactionStatus.MEV_PROTECTED if not was_pending else TransactionStatus.CONFIRMED,
                    block_time=sig_info.block_time,
                    slot=sig_info.slot
                )

                self.confirmed_transactions[sig_str] = event
                self.seen_signatures.add(sig_str)

                if was_pending:
                    self.public_mempool_count += 1
                    pending_event = self.pending_transactions[sig_str]
                    latency = (event.timestamp - pending_event.timestamp).total_seconds()
                    print(f"\n  ✓ PUBLIC MEMPOOL transaction detected:")
                    print(f"    Signature: {sig_str}")
                    print(f"    Slot: {sig_info.slot}")
                    print(f"    Latency: {latency:.2f}s (pending → confirmed)")
                    print(f"    Status: Transaction was visible in mempool")
                else:
                    self.mev_protected_count += 1
                    print(f"\n  🔒 MEV PROTECTED transaction detected:")
                    print(f"    Signature: {sig_str}")
                    print(f"    Slot: {sig_info.slot}")
                    print(f"    Status: Transaction appeared directly in block (likely Jito/private RPC)")

                # Update statistics
                self._print_statistics()

                # Store as last signature for pagination
                self.last_signature = sig_info.signature

        except Exception as e:
            print(f"  ⚠ Error checking confirmed transactions: {e}")

    def _print_statistics(self):
        """Print current statistics"""
        if self.total_transactions == 0:
            return

        mev_percentage = (self.mev_protected_count / self.total_transactions) * 100
        public_percentage = (self.public_mempool_count / self.total_transactions) * 100

        print(f"\n  📊 Statistics:")
        print(f"    Total transactions: {self.total_transactions}")
        print(f"    MEV Protected: {self.mev_protected_count} ({mev_percentage:.1f}%)")
        print(f"    Public Mempool: {self.public_mempool_count} ({public_percentage:.1f}%)")

        if mev_percentage > 50:
            print(f"    ✓ This address is likely using MEV protection")
        elif mev_percentage > 20:
            print(f"    ⚠ This address may be partially using MEV protection")
        else:
            print(f"    ✗ This address is likely NOT using MEV protection")

    async def check_once(self, address_str: str, limit: int = 20):
        """
        Perform a one-time check of recent transactions to detect MEV protection.

        Args:
            address_str: Solana address to check
            limit: Number of recent transactions to analyze (default: 20)
        """
        # Validate address
        self.monitored_address = await self.validate_address(address_str)
        if not self.monitored_address:
            return

        print(f"\n✓ Analyzing recent transactions for: {address_str}")
        print(f"  Fetching last {limit} transactions...\n")
        print("=" * 70)

        try:
            # Get recent signatures
            response = await self.client.get_signatures_for_address(
                self.monitored_address,
                limit=limit,
                commitment=Confirmed
            )

            if not response.value:
                print("\n  ⚠ No transactions found for this address")
                return

            print(f"\n  Found {len(response.value)} transactions. Analyzing...\n")

            for sig_info in response.value:
                sig_str = str(sig_info.signature)

                # Skip failed transactions
                if sig_info.err is not None:
                    continue

                # Skip already processed
                if sig_str in self.confirmed_transactions:
                    continue

                self.total_transactions += 1

                # Since we're checking historical data, we can't know if they were
                # pending, so we use heuristics: very fast confirmation suggests MEV
                # For simplicity, consider all as MEV protected in one-time check
                # A better heuristic: check transaction details for Jito tip accounts

                # Check if transaction uses Jito (has tip to Jito addresses)
                is_jito = await self._check_if_jito_transaction(sig_str)

                if is_jito:
                    self.mev_protected_count += 1
                    status = TransactionStatus.MEV_PROTECTED
                    print(f"  🔒 MEV PROTECTED: {sig_str[:16]}... (Slot: {sig_info.slot})")
                else:
                    self.public_mempool_count += 1
                    status = TransactionStatus.CONFIRMED
                    print(f"  📋 PUBLIC: {sig_str[:16]}... (Slot: {sig_info.slot})")

                event = TransactionEvent(
                    signature=sig_str,
                    timestamp=datetime.now(),
                    status=status,
                    block_time=sig_info.block_time,
                    slot=sig_info.slot
                )

                self.confirmed_transactions[sig_str] = event
                self.seen_signatures.add(sig_str)

            # Print final statistics
            print("\n" + "=" * 70)
            self._print_final_report()

        except Exception as e:
            print(f"\n✗ Error during analysis: {e}")
            raise

    async def _check_if_jito_transaction(self, signature: str) -> bool:
        """
        Check if a transaction was sent through Jito by looking for Jito tip accounts.

        Known Jito tip accounts:
        - 96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5
        - HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe
        - Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY
        - ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49
        - DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh
        - ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt
        - DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL
        - 3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT
        """
        try:
            # Get transaction details
            tx_response = await self.client.get_transaction(
                Signature.from_string(signature),
                max_supported_transaction_version=0
            )

            if not tx_response.value:
                return False

            # Jito tip account addresses
            jito_tip_accounts = {
                "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
                "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
                "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
                "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
                "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
                "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
                "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
                "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
            }

            # Check account keys in the transaction
            if hasattr(tx_response.value.transaction, 'message'):
                message = tx_response.value.transaction.message
                if hasattr(message, 'account_keys'):
                    for account in message.account_keys:
                        if str(account) in jito_tip_accounts:
                            return True

            return False

        except Exception:
            # If we can't fetch transaction details, assume not Jito
            return False

    async def monitor(self, address_str: str, check_interval: float = 2.0):
        """
        Monitor an address for transactions and detect MEV protection.

        Args:
            address_str: Solana address to monitor
            check_interval: Seconds between checks (default: 2.0)
        """
        # Validate address
        self.monitored_address = await self.validate_address(address_str)
        if not self.monitored_address:
            return

        print(f"\n✓ Monitoring address: {address_str}")
        print(f"  Check interval: {check_interval}s")
        print(f"  Waiting for transactions...\n")
        print("=" * 70)

        check_count = 0

        try:
            while True:
                check_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Print periodic status
                if check_count % 10 == 0:
                    print(f"[{timestamp}] Monitoring... (checked {check_count} times)")

                # Check for pending transactions (mempool visibility)
                await self.check_pending_transactions()

                # Check for confirmed transactions
                await self.check_confirmed_transactions()

                # Wait before next check
                await asyncio.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("Monitoring stopped by user")
            self._print_final_report()
        except Exception as e:
            print(f"\n✗ Error during monitoring: {e}")
            raise

    def _print_final_report(self):
        """Print final analysis report"""
        print("\n" + "=" * 70)
        print("FINAL REPORT")
        print("=" * 70)

        if self.total_transactions == 0:
            print("No transactions detected during monitoring period.")
            return

        mev_percentage = (self.mev_protected_count / self.total_transactions) * 100

        print(f"\nTotal Transactions Analyzed: {self.total_transactions}")
        print(f"\nTransaction Breakdown:")
        print(f"  🔒 MEV Protected:  {self.mev_protected_count} ({mev_percentage:.1f}%)")
        print(f"  📋 Public Mempool: {self.public_mempool_count} ({100-mev_percentage:.1f}%)")

        print(f"\nConclusion:")
        if mev_percentage >= 80:
            print("  ✓ This address is CONSISTENTLY using MEV protection")
            print("    Likely using Jito Block Engine or similar private RPC")
        elif mev_percentage >= 50:
            print("  ✓ This address is FREQUENTLY using MEV protection")
            print("    May be mixing public and private transaction submission")
        elif mev_percentage >= 20:
            print("  ⚠ This address is OCCASIONALLY using MEV protection")
            print("    Inconsistent usage pattern detected")
        else:
            print("  ✗ This address is NOT using MEV protection")
            print("    Transactions are primarily visible in public mempool")

        print("\nNote: MEV protection detection is based on mempool visibility.")
        print("Transactions that appear directly in blocks without being seen")
        print("in the mempool first are considered MEV protected.")
        print("=" * 70)

    async def close(self):
        """Close the RPC connection"""
        await self.client.close()


async def main():
    """Main entry point"""
    print("=" * 70)
    print("MEV PROTECTION CHECKER FOR SOLANA")
    print("=" * 70)
    print("\nThis tool checks if a Solana address is using MEV protection")
    print("services like Jito's Block Engine.")
    print("\nMEV-protected transactions:")
    print("  - Use Jito tip accounts for priority block inclusion")
    print("  - Bypass public transaction pools via private RPCs")
    print("  - Provide protection against frontrunning and sandwich attacks")
    print()

    # Get address from user
    address_str = input("Enter Solana address to check: ").strip()

    if not address_str:
        print("✗ No address provided")
        return

    # Optional: custom RPC URL
    print("\nRPC endpoint (press Enter for mainnet default):")
    custom_rpc = input("  https://api.mainnet-beta.solana.com > ").strip()
    rpc_url = custom_rpc if custom_rpc else "https://api.mainnet-beta.solana.com"

    print(f"\nUsing RPC: {rpc_url}")
    print("Connecting...\n")

    # Create and run checker
    checker = MEVProtectionChecker(rpc_url=rpc_url)

    try:
        # Connect to RPC
        if not await checker.connect():
            return

        # Perform one-time check of recent transactions
        await checker.check_once(address_str, limit=20)

    finally:
        await checker.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
