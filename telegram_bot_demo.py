"""
Standalone Telegram bot demo - works without Solana RPC connection
Run this to test the Telegram bot interface
"""
import asyncio
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

sys.path.insert(0, '/home/user/copytrader')

from python_bot.telegram.keyboards import (
    get_main_menu_keyboard,
    get_back_button,
    get_settings_keyboard,
    get_wallets_keyboard,
    get_positions_keyboard
)
from python_bot.config import settings


# Mock bot state
class MockBot:
    def __init__(self):
        self.is_running = False
        self.tracked_wallets = 5
        self.avg_win_rate = 72.5
        self.strategy_name = "Conservative"
        self.balance = 100.0
        self.portfolio_value = 102.5
        self.pnl = 2.5
        self.pnl_pct = 2.5
        self.open_positions = 3
        self.total_trades = 15
        self.win_rate = 73.33

mock_bot = MockBot()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

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


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    is_running = "🟢 Running" if mock_bot.is_running else "🔴 Stopped"

    status_text = (
        "📊 Bot Status\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Status: {is_running}\n"
        f"Network: {settings.solana_network}\n"
        f"Tracked Wallets: {mock_bot.tracked_wallets}\n"
        f"Avg Win Rate: {mock_bot.avg_win_rate:.2f}%\n"
        f"Active Strategies: 1\n\n"
        f"Last Updated: {datetime.now().strftime('%H:%M:%S')}"
    )

    await update.message.reply_text(status_text, reply_markup=get_back_button())


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    stats_text = (
        "📈 Performance Statistics\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Strategy: {mock_bot.strategy_name}\n"
        f"Balance: {mock_bot.balance:.4f} SOL\n"
        f"Portfolio: {mock_bot.portfolio_value:.4f} SOL\n"
        f"Total PnL: {mock_bot.pnl:.4f} SOL ({mock_bot.pnl_pct:.2f}%)\n"
        f"Open Positions: {mock_bot.open_positions}\n"
        f"Total Trades: {mock_bot.total_trades}\n"
        f"Win Rate: {mock_bot.win_rate:.2f}%\n"
    )

    await update.message.reply_text(stats_text, reply_markup=get_back_button())


async def wallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wallets command"""
    wallets_text = (
        "👛 Top Tracked Wallets\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1. 7ABz8qEF...ShkQ6\n"
        "   PnL: 1000.00 SOL\n"
        "   Win Rate: 75.0%\n"
        "   Trades: 100\n\n"
        "2. J6TDXvar...Y8iEa\n"
        "   PnL: 990.00 SOL\n"
        "   Win Rate: 74.5%\n"
        "   Trades: 101\n\n"
        "3. AVAZvHLR...NXYm\n"
        "   PnL: 980.00 SOL\n"
        "   Win Rate: 74.0%\n"
        "   Trades: 102\n"
    )

    await update.message.reply_text(wallets_text, reply_markup=get_wallets_keyboard())


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /positions command"""
    positions_text = (
        "💼 Open Positions\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Total Open Positions: {mock_bot.open_positions}\n\n"
        "Use the buttons below for more details."
    )

    await update.message.reply_text(positions_text, reply_markup=get_positions_keyboard())


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
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

    await update.message.reply_text(settings_text, reply_markup=get_settings_keyboard())


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "main_menu":
        is_running = "🟢 Running" if mock_bot.is_running else "🔴 Stopped"
        menu_text = (
            "🤖 Solana Copy Trading Bot\n\n"
            f"Status: {is_running}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Select an option from the menu below:"
        )
        await query.message.edit_text(menu_text, reply_markup=get_main_menu_keyboard())

    elif callback_data == "status":
        is_running = "🟢 Running" if mock_bot.is_running else "🔴 Stopped"
        status_text = (
            "📊 Bot Status\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Status: {is_running}\n"
            f"Network: {settings.solana_network}\n"
            f"Tracked Wallets: {mock_bot.tracked_wallets}\n"
            f"Avg Win Rate: {mock_bot.avg_win_rate:.2f}%\n"
            f"Active Strategies: 1\n\n"
            f"Last Updated: {datetime.now().strftime('%H:%M:%S')}"
        )
        await query.message.edit_text(status_text, reply_markup=get_back_button())

    elif callback_data == "stats":
        stats_text = (
            "📈 Performance Statistics\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Strategy: {mock_bot.strategy_name}\n"
            f"Balance: {mock_bot.balance:.4f} SOL\n"
            f"Portfolio: {mock_bot.portfolio_value:.4f} SOL\n"
            f"Total PnL: {mock_bot.pnl:.4f} SOL ({mock_bot.pnl_pct:.2f}%)\n"
            f"Open Positions: {mock_bot.open_positions}\n"
            f"Total Trades: {mock_bot.total_trades}\n"
            f"Win Rate: {mock_bot.win_rate:.2f}%\n"
        )
        await query.message.edit_text(stats_text, reply_markup=get_back_button())

    elif callback_data == "wallets":
        wallets_text = (
            "👛 Top Tracked Wallets\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. 7ABz8qEF...ShkQ6\n"
            "   PnL: 1000.00 SOL\n"
            "   Win Rate: 75.0%\n"
            "   Trades: 100\n\n"
            "2. J6TDXvar...Y8iEa\n"
            "   PnL: 990.00 SOL\n"
            "   Win Rate: 74.5%\n"
            "   Trades: 101\n\n"
            "3. AVAZvHLR...NXYm\n"
            "   PnL: 980.00 SOL\n"
            "   Win Rate: 74.0%\n"
            "   Trades: 102\n"
        )
        await query.message.edit_text(wallets_text, reply_markup=get_wallets_keyboard())

    elif callback_data == "positions":
        positions_text = (
            "💼 Open Positions\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Total Open Positions: {mock_bot.open_positions}\n\n"
            "Use the buttons below for more details."
        )
        await query.message.edit_text(positions_text, reply_markup=get_positions_keyboard())

    elif callback_data == "settings":
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
        await query.message.edit_text(settings_text, reply_markup=get_settings_keyboard())

    elif callback_data == "start_bot":
        if not mock_bot.is_running:
            mock_bot.is_running = True
            await query.message.edit_text(
                "✅ Bot started successfully!\n\n"
                "The bot is now monitoring wallets and copying trades.",
                reply_markup=get_back_button()
            )
        else:
            await query.message.edit_text(
                "⚠️ Bot is already running!",
                reply_markup=get_back_button()
            )

    elif callback_data == "stop_bot":
        if mock_bot.is_running:
            mock_bot.is_running = False
            await query.message.edit_text(
                "⏸️ Bot stopped successfully!\n\n"
                "All monitoring and trading has been paused.",
                reply_markup=get_back_button()
            )
        else:
            await query.message.edit_text(
                "⚠️ Bot is not running!",
                reply_markup=get_back_button()
            )

    elif callback_data == "refresh":
        is_running = "🟢 Running" if mock_bot.is_running else "🔴 Stopped"
        menu_text = (
            "🤖 Solana Copy Trading Bot\n\n"
            f"Status: {is_running}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Select an option from the menu below:"
        )
        await query.message.edit_text(menu_text, reply_markup=get_main_menu_keyboard())


async def main():
    """Main entry point"""
    bot_token = "8540352317:AAGvvraBvgZRbpL9zey54F39Ux35Wv74LHU"

    if not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env file")
        return

    print("=" * 80)
    print("TELEGRAM BOT DEMO (Standalone Mode)")
    print("=" * 80)
    print(f"Bot Token: {bot_token[:20]}...")
    print("Starting Telegram bot...")
    print("\nOpen Telegram and send /start to your bot")
    print("Press Ctrl+C to stop")
    print("=" * 80)

    # Create application
    application = Application.builder().token(bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("wallets", wallets_command))
    application.add_handler(CommandHandler("positions", positions_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

    print("✅ Telegram bot is running!")

    # Run until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        print("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
