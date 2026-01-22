"""
Telegram bot interface for copy trading bot
"""
import asyncio
from typing import TYPE_CHECKING
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from .handlers import TelegramHandlers
from ..utils.logger import get_logger
from ..config import settings

if TYPE_CHECKING:
    from ..main import CopyTradingBot

logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot interface for controlling the copy trading bot"""

    def __init__(self, trading_bot: 'CopyTradingBot', bot_token: str = None):
        """
        Initialize Telegram bot

        Args:
            trading_bot: Main copy trading bot instance
            bot_token: Telegram bot token
        """
        self.trading_bot = trading_bot
        self.bot_token = bot_token or settings.telegram_bot_token

        if not self.bot_token:
            raise ValueError("Telegram bot token not provided")

        self.application: Application = None
        self.handlers = TelegramHandlers(trading_bot)
        self.is_running = False

        logger.info("Telegram bot initialized")

    async def start(self):
        """Start the Telegram bot"""
        if self.is_running:
            logger.warning("Telegram bot already running")
            return

        logger.info("Starting Telegram bot...")

        # Create application
        self.application = (
            Application.builder()
            .token(self.bot_token)
            .build()
        )

        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("status", self.handlers.status_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("wallets", self.handlers.wallets_command))
        self.application.add_handler(CommandHandler("positions", self.handlers.positions_command))
        self.application.add_handler(CommandHandler("settings", self.handlers.settings_command))

        # Register callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.handlers.button_callback))

        # Register error handler
        self.application.add_error_handler(self.handlers.error_handler)

        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

        self.is_running = True
        logger.info("Telegram bot started successfully")

    async def stop(self):
        """Stop the Telegram bot"""
        if not self.is_running:
            return

        logger.info("Stopping Telegram bot...")

        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

        self.is_running = False
        logger.info("Telegram bot stopped")

    async def send_notification(self, message: str, chat_id: str = None):
        """
        Send a notification message

        Args:
            message: Message to send
            chat_id: Chat ID to send to (uses default if not provided)
        """
        if not self.is_running or not self.application:
            logger.warning("Cannot send notification - Telegram bot not running")
            return

        target_chat_id = chat_id or settings.telegram_chat_id

        if not target_chat_id:
            logger.warning("No chat ID configured for notifications")
            return

        try:
            await self.application.bot.send_message(
                chat_id=target_chat_id,
                text=message
            )
            logger.debug(f"Notification sent: {message[:50]}...")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    async def send_trade_notification(
        self,
        trade_type: str,
        token: str,
        amount: float,
        price: float,
        wallet: str
    ):
        """
        Send a trade notification

        Args:
            trade_type: 'buy' or 'sell'
            token: Token address
            amount: Trade amount in SOL
            price: Token price
            wallet: Source wallet address
        """
        emoji = "🟢" if trade_type.lower() == "buy" else "🔴"
        action = "BUY" if trade_type.lower() == "buy" else "SELL"

        message = (
            f"{emoji} {action} Trade Executed\n\n"
            f"Token: {token[:8]}...{token[-8:]}\n"
            f"Amount: {amount:.4f} SOL\n"
            f"Price: ${price:.8f}\n"
            f"Source: {wallet[:8]}...{wallet[-8:]}\n"
        )

        await self.send_notification(message)

    async def send_position_update(
        self,
        action: str,
        token: str,
        pnl: float,
        pnl_percentage: float
    ):
        """
        Send a position update notification

        Args:
            action: Action taken (e.g., 'Closed', 'Take Profit', 'Stop Loss')
            token: Token address
            pnl: Profit/Loss in SOL
            pnl_percentage: Profit/Loss percentage
        """
        emoji = "💰" if pnl > 0 else "📉"
        sign = "+" if pnl > 0 else ""

        message = (
            f"{emoji} Position {action}\n\n"
            f"Token: {token[:8]}...{token[-8:]}\n"
            f"PnL: {sign}{pnl:.4f} SOL ({sign}{pnl_percentage:.2f}%)\n"
        )

        await self.send_notification(message)

    async def send_error_notification(self, error_message: str):
        """
        Send an error notification

        Args:
            error_message: Error message
        """
        message = f"❌ Error\n\n{error_message}"
        await self.send_notification(message)
