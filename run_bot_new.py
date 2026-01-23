"""
New bot runner using the refactored backend
Run this instead of python_bot/main.py
"""
import asyncio
import signal
from python_bot.services.bot_backend import CopyTradingBackend
from python_bot.telegram.bot import TelegramBot
from python_bot.telegram.handlers import TelegramHandlers
from python_bot.utils.logger import setup_logger, get_logger
from python_bot.config import settings
from datetime import datetime

# Setup logger
logger = setup_logger(
    name="copytrader",
    level=settings.log_level,
    log_file=f"logs/copytrader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)


class SimpleBot:
    """Simple bot wrapper using new backend"""

    def __init__(self):
        self.backend = None
        self.telegram_bot = None
        self.running = False

    async def start(self):
        """Start the bot"""
        logger.info("=" * 80)
        logger.info("SOLANA COPY TRADING BOT - NEW ARCHITECTURE")
        logger.info("=" * 80)
        logger.info(f"Mode: {'TEST' if settings.test_mode else 'PRODUCTION'}")
        logger.info(f"Network: {settings.solana_network}")
        logger.info(f"Simulate Trades: {settings.simulate_trades}")
        logger.info("=" * 80)

        # Initialize backend
        logger.info("Initializing backend...")
        self.backend = CopyTradingBackend()
        await self.backend.initialize()
        logger.info("✅ Backend initialized")

        # Initialize Telegram bot if configured
        if settings.telegram_bot_token:
            logger.info("Starting Telegram bot...")
            try:
                # Create custom TelegramBot that works with backend
                from telegram import Update
                from telegram.ext import Application, CommandHandler, CallbackQueryHandler

                # Create handlers with backend
                handlers = TelegramHandlers(self.backend)

                # Create application
                application = Application.builder().token(settings.telegram_bot_token).build()

                # Register handlers
                application.add_handler(CommandHandler("start", handlers.start_command))
                application.add_handler(CommandHandler("help", handlers.help_command))
                application.add_handler(CommandHandler("status", handlers.status_command))
                application.add_handler(CommandHandler("stats", handlers.stats_command))
                application.add_handler(CommandHandler("wallets", handlers.wallets_command))
                application.add_handler(CommandHandler("positions", handlers.positions_command))
                application.add_handler(CommandHandler("settings", handlers.settings_command))
                application.add_handler(CallbackQueryHandler(handlers.button_callback))
                application.add_error_handler(handlers.error_handler)

                # Start polling
                await application.initialize()
                await application.start()
                await application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )

                self.telegram_bot = application
                logger.info("✅ Telegram bot started")

            except Exception as e:
                logger.error(f"Failed to start Telegram bot: {e}")
                logger.info("Bot will continue without Telegram interface")
        else:
            logger.info("No Telegram bot token configured")

        logger.info("=" * 80)
        logger.info("BOT STARTED - Ready to use!")
        logger.info("=" * 80)
        logger.info("Send /start to your Telegram bot to begin")
        logger.info("Press Ctrl+C to stop")

        self.running = True

        # Keep running
        try:
            while self.running:
                await asyncio.sleep(60)

                # Print status every minute
                status = self.backend.get_bot_status()
                logger.info("=" * 80)
                logger.info("BOT STATUS")
                logger.info("=" * 80)
                logger.info(f"Running: {'Yes' if status['is_running'] else 'No'}")
                logger.info(f"Tracked Wallets: {status['tracked_wallets']}")
                logger.info(f"Active Session: {status['active_session'] or 'None'}")

                active_session = self.backend.get_active_session()
                if active_session:
                    stats = active_session.get_statistics()
                    logger.info(f"Balance: €{stats['balance_eur']:.2f}")
                    logger.info(f"Total Trades: {stats['total_trades']}")
                    logger.info(f"Win Rate: {stats['win_rate']:.1f}%")
                logger.info("=" * 80)

        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            await self.stop()

    async def stop(self):
        """Stop the bot"""
        self.running = False

        if self.telegram_bot:
            logger.info("Stopping Telegram bot...")
            await self.telegram_bot.updater.stop()
            await self.telegram_bot.stop()
            await self.telegram_bot.shutdown()

        if self.backend:
            logger.info("Shutting down backend...")
            await self.backend.shutdown()

        logger.info("Bot stopped")


async def main():
    """Main entry point"""
    bot = SimpleBot()

    # Handle signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.stop()))

    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
