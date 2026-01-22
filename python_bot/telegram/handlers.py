"""
Telegram bot command handlers
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from typing import TYPE_CHECKING

from .keyboards import (
    get_main_menu_keyboard,
    get_back_button,
    get_settings_keyboard,
    get_wallets_keyboard,
    get_positions_keyboard,
    get_confirmation_keyboard
)
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..main import CopyTradingBot

logger = get_logger(__name__)


class TelegramHandlers:
    """Handlers for Telegram bot commands and callbacks"""

    def __init__(self, trading_bot: 'CopyTradingBot'):
        """
        Initialize handlers

        Args:
            trading_bot: Main copy trading bot instance
        """
        self.bot = trading_bot

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")

        welcome_text = (
            f"👋 Welcome to Solana Copy Trading Bot, {user.first_name}!\n\n"
            "🤖 This bot helps you automatically copy trades from top Solana wallets.\n\n"
            "📊 Features:\n"
            "• Real-time wallet monitoring\n"
            "• Automated trade copying\n"
            "• Multiple trading strategies\n"
            "• Performance tracking\n"
            "• Risk management\n\n"
            "Use the menu below to control the bot:"
        )

        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard()
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📚 Bot Commands:\n\n"
            "/start - Show main menu\n"
            "/status - View bot status\n"
            "/stats - View performance statistics\n"
            "/wallets - View tracked wallets\n"
            "/positions - View open positions\n"
            "/settings - Configure bot settings\n"
            "/help - Show this help message\n\n"
            "Use the inline buttons for easy navigation!"
        )

        await update.message.reply_text(help_text, reply_markup=get_back_button())

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        await self._show_status(update.message)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        await self._show_stats(update.message)

    async def wallets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /wallets command"""
        await self._show_wallets(update.message)

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command"""
        await self._show_positions(update.message)

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        await self._show_settings(update.message)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        logger.debug(f"Callback received: {callback_data}")

        # Main menu
        if callback_data == "main_menu":
            await self._show_main_menu(query)

        # Status
        elif callback_data == "status":
            await self._show_status(query.message)

        # Statistics
        elif callback_data == "stats":
            await self._show_stats(query.message)

        # Wallets
        elif callback_data == "wallets":
            await self._show_wallets(query.message)
        elif callback_data.startswith("wallets_"):
            await self._handle_wallets_action(query, callback_data)

        # Positions
        elif callback_data == "positions":
            await self._show_positions(query.message)
        elif callback_data.startswith("positions_"):
            await self._handle_positions_action(query, callback_data)

        # Settings
        elif callback_data == "settings":
            await self._show_settings(query.message)
        elif callback_data.startswith("settings_"):
            await self._handle_settings_action(query, callback_data)

        # Bot control
        elif callback_data == "start_bot":
            await self._start_bot(query)
        elif callback_data == "stop_bot":
            await self._stop_bot(query)

        # Refresh
        elif callback_data == "refresh":
            await self._show_main_menu(query)

    async def _show_main_menu(self, query_or_message):
        """Show main menu"""
        is_running = "🟢 Running" if self.bot.is_running else "🔴 Stopped"

        menu_text = (
            "🤖 Solana Copy Trading Bot\n\n"
            f"Status: {is_running}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Select an option from the menu below:"
        )

        if hasattr(query_or_message, 'edit_text'):
            await query_or_message.edit_text(menu_text, reply_markup=get_main_menu_keyboard())
        else:
            await query_or_message.reply_text(menu_text, reply_markup=get_main_menu_keyboard())

    async def _show_status(self, message):
        """Show bot status"""
        is_running = "🟢 Running" if self.bot.is_running else "🔴 Stopped"

        # Get wallet tracker stats
        tracker_stats = self.bot.wallet_tracker.get_statistics() if hasattr(self.bot, 'wallet_tracker') else {}

        status_text = (
            "📊 Bot Status\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Status: {is_running}\n"
            f"Network: {self.bot.solana_client.rpc_url if hasattr(self.bot, 'solana_client') else 'N/A'}\n"
            f"Tracked Wallets: {tracker_stats.get('total_wallets', 0)}\n"
            f"Avg Win Rate: {tracker_stats.get('average_win_rate', 0):.2f}%\n"
            f"Active Strategies: {len(self.bot.strategy_engines) if hasattr(self.bot, 'strategy_engines') else 0}\n\n"
            f"Last Updated: {datetime.now().strftime('%H:%M:%S')}"
        )

        if hasattr(message, 'edit_text'):
            await message.edit_text(status_text, reply_markup=get_back_button())
        else:
            await message.reply_text(status_text, reply_markup=get_back_button())

    async def _show_stats(self, message):
        """Show performance statistics"""
        if not hasattr(self.bot, 'strategy_engines') or not self.bot.strategy_engines:
            stats_text = "📈 No statistics available yet.\nStart the bot to begin trading."
        else:
            stats_text = "📈 Performance Statistics\n━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, engine in enumerate(self.bot.strategy_engines):
                stats = engine.get_performance_stats()
                stats_text += (
                    f"Strategy: {stats['strategy_name']}\n"
                    f"Balance: {stats['current_balance']:.4f} SOL\n"
                    f"Portfolio: {stats['portfolio_value']:.4f} SOL\n"
                    f"Total PnL: {stats['total_pnl_sol']:.4f} SOL ({stats['total_pnl_percentage']:.2f}%)\n"
                    f"Open Positions: {stats['open_positions']}\n"
                    f"Total Trades: {stats['total_trades']}\n"
                    f"Win Rate: {stats['win_rate']:.2f}%\n\n"
                )

        if hasattr(message, 'edit_text'):
            await message.edit_text(stats_text, reply_markup=get_back_button())
        else:
            await message.reply_text(stats_text, reply_markup=get_back_button())

    async def _show_wallets(self, message, page=0):
        """Show tracked wallets"""
        if not hasattr(self.bot, 'wallet_tracker'):
            wallets_text = "👛 No wallets being tracked."
        else:
            top_wallets = self.bot.wallet_tracker.get_top_wallets(limit=10)

            wallets_text = "👛 Top Tracked Wallets\n━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, wallet in enumerate(top_wallets, 1):
                addr = wallet['address']
                wallets_text += (
                    f"{i}. {addr[:8]}...{addr[-8:]}\n"
                    f"   PnL: {wallet.get('pnl', 0):.2f} SOL\n"
                    f"   Win Rate: {wallet.get('win_rate', 0):.1f}%\n"
                    f"   Trades: {wallet.get('total_trades', 0)}\n\n"
                )

        if hasattr(message, 'edit_text'):
            await message.edit_text(wallets_text, reply_markup=get_wallets_keyboard(page))
        else:
            await message.reply_text(wallets_text, reply_markup=get_wallets_keyboard(page))

    async def _show_positions(self, message):
        """Show open positions"""
        if not hasattr(self.bot, 'strategy_engines') or not self.bot.strategy_engines:
            positions_text = "💼 No positions open."
        else:
            positions_text = "💼 Open Positions\n━━━━━━━━━━━━━━━━━━━━\n\n"

            total_positions = 0
            for engine in self.bot.strategy_engines:
                stats = engine.get_performance_stats()
                total_positions += stats.get('open_positions', 0)

            positions_text += f"Total Open Positions: {total_positions}\n\n"
            positions_text += "Use the buttons below for more details."

        if hasattr(message, 'edit_text'):
            await message.edit_text(positions_text, reply_markup=get_positions_keyboard())
        else:
            await message.reply_text(positions_text, reply_markup=get_positions_keyboard())

    async def _show_settings(self, message):
        """Show settings menu"""
        from ..config import settings

        settings_text = (
            "⚙️ Bot Settings\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Network: {settings.solana_network}\n"
            f"Test Mode: {'✅' if settings.test_mode else '❌'}\n"
            f"Simulate Trades: {'✅' if settings.simulate_trades else '❌'}\n"
            f"Active Strategy: {settings.active_strategy}\n"
            f"Min Trade Size: {settings.min_trade_size} SOL\n"
            f"Max Trade Size: {settings.max_trade_size} SOL\n"
            f"Slippage: {settings.slippage_percentage:.2f}%\n\n"
            "Select a setting to modify:"
        )

        if hasattr(message, 'edit_text'):
            await message.edit_text(settings_text, reply_markup=get_settings_keyboard())
        else:
            await message.reply_text(settings_text, reply_markup=get_settings_keyboard())

    async def _start_bot(self, query):
        """Start the trading bot"""
        if self.bot.is_running:
            await query.message.edit_text(
                "⚠️ Bot is already running!",
                reply_markup=get_back_button()
            )
            return

        try:
            await self.bot.start()
            await query.message.edit_text(
                "✅ Bot started successfully!\n\n"
                "The bot is now monitoring wallets and copying trades.",
                reply_markup=get_back_button()
            )
            logger.info("Bot started via Telegram command")
        except Exception as e:
            await query.message.edit_text(
                f"❌ Error starting bot:\n{str(e)}",
                reply_markup=get_back_button()
            )
            logger.error(f"Error starting bot via Telegram: {e}")

    async def _stop_bot(self, query):
        """Stop the trading bot"""
        if not self.bot.is_running:
            await query.message.edit_text(
                "⚠️ Bot is not running!",
                reply_markup=get_back_button()
            )
            return

        try:
            await self.bot.stop()
            await query.message.edit_text(
                "⏸️ Bot stopped successfully!\n\n"
                "All monitoring and trading has been paused.",
                reply_markup=get_back_button()
            )
            logger.info("Bot stopped via Telegram command")
        except Exception as e:
            await query.message.edit_text(
                f"❌ Error stopping bot:\n{str(e)}",
                reply_markup=get_back_button()
            )
            logger.error(f"Error stopping bot via Telegram: {e}")

    async def _handle_wallets_action(self, query, callback_data):
        """Handle wallet-related actions"""
        if callback_data == "wallets_refresh":
            if hasattr(self.bot, 'wallet_tracker'):
                await self.bot.wallet_tracker.refresh_wallet_list()
                await self._show_wallets(query.message)
        # Add pagination handling here if needed

    async def _handle_positions_action(self, query, callback_data):
        """Handle position-related actions"""
        # Implement position details viewing here
        pass

    async def _handle_settings_action(self, query, callback_data):
        """Handle settings-related actions"""
        await query.message.edit_text(
            "⚠️ Settings modification coming soon!\n\n"
            "For now, edit the .env file to change settings.",
            reply_markup=get_back_button()
        )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Telegram bot error: {context.error}", exc_info=context.error)

        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
