"""
Simple test for Telegram handlers without full bot
"""
import asyncio
from python_bot.services.bot_backend import CopyTradingBackend
from python_bot.telegram.handlers import TelegramHandlers


async def test_handlers():
    """Test handler initialization"""
    print("Initializing backend...")
    backend = CopyTradingBackend()
    await backend.initialize()

    print("Initializing handlers...")
    handlers = TelegramHandlers(backend)

    print("Getting bot status...")
    status = backend.get_bot_status()
    print(f"Status: {status}")

    print("\nTest passed!")
    await backend.shutdown()


if __name__ == "__main__":
    asyncio.run(test_handlers())
