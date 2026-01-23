"""
Simple test script for the refactored bot
Run this to test the basic functionality without Telegram
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python_bot.services.bot_backend import CopyTradingBackend
from python_bot.utils.logger import get_logger

logger = get_logger(__name__)


async def test_backend():
    """Test backend functionality"""
    logger.info("=== Testing Bot Backend ===\n")

    # Initialize backend
    backend = CopyTradingBackend()
    await backend.initialize()

    # Get bot status
    logger.info("1. Testing bot status...")
    status = await backend.get_bot_status()
    print(f"   Bot running: {status['is_running']}")
    print(f"   Network: {status['network']}")
    print(f"   SOL price: €{status['sol_price_eur']:.2f}\n")

    # Test session management
    logger.info("2. Testing session management...")
    session = backend.create_session(
        name="Test Session",
        strategy_id=2,  # Balanced
        initial_balance_eur=20.0
    )
    print(f"   Created session: {session.name}")
    print(f"   Balance: €{session.balance_manager.get_balance_eur():.2f}\n")

    # Test balance management
    logger.info("3. Testing balance management...")
    backend.add_balance(50.0, note="Test deposit")
    balance = backend.get_balance()
    print(f"   After deposit: €{balance['current_balance_eur']:.2f}")
    print(f"   In SOL: {balance['current_balance_sol']:.4f} SOL\n")

    # Test wallet tracking
    logger.info("4. Testing wallet tracking...")
    try:
        wallet = backend.add_wallet(
            address="7ABz8qEFZTHPkovMDsmQkm64DZWN5wRtU7LEtD2ShkQ6",
            name="Test Wallet",
            notes="Sample wallet for testing"
        )
        print(f"   Added wallet: {wallet.name}")
        print(f"   Address: {wallet.address[:8]}...{wallet.address[-6:]}\n")
    except Exception as e:
        print(f"   Error adding wallet: {e}\n")

    # Test fee calculation
    logger.info("5. Testing fee calculation...")
    fees = backend.calculate_swap_fees(0.5)
    print(f"   Trade amount: 0.5 SOL")
    print(f"   Network fee: {fees['network_fee']:.6f} SOL")
    print(f"   Priority fee: {fees['priority_fee']:.6f} SOL")
    print(f"   Platform fee: {fees['platform_fee']:.6f} SOL")
    print(f"   Total fees: {fees['total_fee']:.6f} SOL ({fees['total_fee_percentage']:.2f}%)\n")

    # Test session statistics
    logger.info("6. Testing statistics...")
    stats = backend.get_overall_statistics()
    print(f"   Total sessions: {stats['total_sessions']}")
    print(f"   Total balance: €{stats['total_balance_eur']:.2f}")
    print(f"   Active wallets: {stats['wallets']['total_wallets']}\n")

    # Cleanup
    await backend.shutdown()
    logger.info("=== Test Complete ===")


async def main():
    """Main test function"""
    try:
        await test_backend()
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
