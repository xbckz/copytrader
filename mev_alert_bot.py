#!/usr/bin/env python3
"""
MEV Alert Telegram Bot
Monitors Solana wallets and sends alerts when non-MEV-protected transactions are detected
"""

import asyncio
import os
import traceback
from datetime import datetime
from typing import Dict, Set
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from mev_protection_checker import MEVProtectionChecker, TransactionStatus

# Load environment variables
load_dotenv()

# Bot state
tracked_wallets: Dict[str, str] = {}  # {address: name}
monitoring_tasks: Dict[str, asyncio.Task] = {}  # {address: task}
bot_application = None


class WalletMonitor:
    """Monitors a single wallet and sends alerts"""

    def __init__(self, address: str, name: str, checker: MEVProtectionChecker, chat_id: int):
        self.address = address
        self.name = name
        self.checker = checker
        self.chat_id = chat_id
        self.seen_signatures: Set[str] = set()
        self.is_running = True

    async def start_monitoring(self):
        """Start monitoring the wallet"""
        print(f"🔍 Started monitoring {self.name} ({self.address[:8]}...)")

        try:
            # Validate address
            pubkey = await self.checker.validate_address(self.address)
            if not pubkey:
                await self.send_alert(f"❌ Invalid address for wallet: {self.name}")
                return

            self.checker.monitored_address = pubkey

            # Send start notification
            await self.send_alert(
                f"✅ Started monitoring wallet:\n"
                f"📛 Name: {self.name}\n"
                f"📍 Address: `{self.address}`\n\n"
                f"You'll receive alerts when non-MEV-protected transactions are detected.",
                parse_mode='Markdown'
            )

            # Start monitoring loop
            while self.is_running:
                await self.check_transactions()
                await asyncio.sleep(3.0)  # Check every 3 seconds

        except asyncio.CancelledError:
            print(f"🛑 Stopped monitoring {self.name}")
        except Exception as e:
            print(f"❌ Error monitoring {self.name}: {e}")
            await self.send_alert(f"❌ Error monitoring {self.name}: {e}")

    async def check_transactions(self):
        """Check for new transactions"""
        try:
            # Get recent signatures
            response = await self.checker.client.get_signatures_for_address(
                self.checker.monitored_address,
                limit=5
            )

            if not response.value:
                return

            for sig_info in response.value:
                sig_str = str(sig_info.signature)

                # Skip already processed or failed transactions
                if sig_str in self.seen_signatures or sig_info.err is not None:
                    continue

                # Skip if not yet confirmed
                if sig_info.block_time is None:
                    continue

                self.seen_signatures.add(sig_str)

                # Check if it's a Jito transaction
                is_mev_protected = await self.checker._check_if_jito_transaction(sig_str)

                # Send alert if NOT MEV protected
                if not is_mev_protected:
                    await self.send_non_mev_alert(sig_str, sig_info.slot)

        except Exception as e:
            print(f"⚠ Error checking transactions for {self.name}: {type(e).__name__}: {e}")
            traceback.print_exc()

    async def send_non_mev_alert(self, signature: str, slot: int):
        """Send alert for non-MEV-protected transaction"""
        message = (
            f"🚨 NON-MEV-PROTECTED TRANSACTION DETECTED!\n\n"
            f"📛 Wallet: {self.name}\n"
            f"📍 Address: `{self.address[:16]}...`\n"
            f"📝 Signature: `{signature[:16]}...`\n"
            f"🔢 Slot: {slot}\n"
            f"⚠ Status: Public mempool transaction\n\n"
            f"🔗 [View on Solscan](https://solscan.io/tx/{signature})\n"
            f"🔗 [View on SolanaFM](https://solana.fm/tx/{signature})"
        )

        await self.send_alert(message, parse_mode='Markdown')

    async def send_alert(self, message: str, parse_mode: str = None):
        """Send alert to Telegram"""
        try:
            await bot_application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")

    def stop(self):
        """Stop monitoring"""
        self.is_running = False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Wallet", callback_data="add_wallet")],
        [InlineKeyboardButton("📋 List Wallets", callback_data="list_wallets")],
        [InlineKeyboardButton("🗑️ Remove Wallet", callback_data="remove_wallet")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🤖 *MEV Alert Bot*\n\n"
        "I monitor Solana wallets and alert you when they make "
        "*non-MEV-protected* transactions.\n\n"
        "What would you like to do?"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()

    if query.data == "add_wallet":
        await query.edit_message_text(
            "📝 To add a wallet, use this command:\n\n"
            "`/add <address> <name>`\n\n"
            "Example:\n"
            "`/add DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK MyTrader`",
            parse_mode='Markdown'
        )

    elif query.data == "list_wallets":
        await list_wallets_command(update, context, is_callback=True)

    elif query.data == "remove_wallet":
        await query.edit_message_text(
            "🗑️ To remove a wallet, use this command:\n\n"
            "`/remove <address>`\n\n"
            "Example:\n"
            "`/remove DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK`\n\n"
            "Or use `/list` to see all addresses.",
            parse_mode='Markdown'
        )

    elif query.data == "help":
        await help_command(update, context, is_callback=True)

    elif query.data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("➕ Add Wallet", callback_data="add_wallet")],
            [InlineKeyboardButton("📋 List Wallets", callback_data="list_wallets")],
            [InlineKeyboardButton("🗑️ Remove Wallet", callback_data="remove_wallet")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🤖 *MEV Alert Bot*\n\nWhat would you like to do?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def add_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid format. Use:\n"
            "`/add <address> <name>`",
            parse_mode='Markdown'
        )
        return

    address = context.args[0]
    name = " ".join(context.args[1:])

    # Check if already tracking
    if address in tracked_wallets:
        await update.message.reply_text(f"⚠ Already tracking wallet: {tracked_wallets[address]}")
        return

    # Add wallet
    tracked_wallets[address] = name

    # Start monitoring
    chat_id = update.effective_chat.id
    checker = MEVProtectionChecker(
        rpc_url=os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    )
    await checker.connect()

    monitor = WalletMonitor(address, name, checker, chat_id)
    task = asyncio.create_task(monitor.start_monitoring())
    monitoring_tasks[address] = task

    await update.message.reply_text(
        f"✅ Added wallet!\n"
        f"📛 Name: {name}\n"
        f"📍 Address: `{address}`\n\n"
        f"Monitoring started...",
        parse_mode='Markdown'
    )


async def remove_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove command"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Invalid format. Use:\n"
            "`/remove <address>`",
            parse_mode='Markdown'
        )
        return

    address = context.args[0]

    if address not in tracked_wallets:
        await update.message.reply_text("⚠ Wallet not found in tracking list.")
        return

    name = tracked_wallets[address]

    # Stop monitoring task
    if address in monitoring_tasks:
        monitoring_tasks[address].cancel()
        del monitoring_tasks[address]

    # Remove from tracking
    del tracked_wallets[address]

    await update.message.reply_text(
        f"✅ Removed wallet:\n"
        f"📛 {name}\n"
        f"📍 `{address}`",
        parse_mode='Markdown'
    )


async def list_wallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Handle /list command"""
    if not tracked_wallets:
        message = "📋 No wallets being tracked.\n\nUse `/add` to add a wallet."
    else:
        message = f"📋 *Tracked Wallets* ({len(tracked_wallets)}):\n\n"
        for i, (address, name) in enumerate(tracked_wallets.items(), 1):
            status = "🟢 Active" if address in monitoring_tasks else "🔴 Stopped"
            message += f"{i}. *{name}*\n"
            message += f"   {status}\n"
            message += f"   `{address[:16]}...`\n\n"

    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_callback:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Handle /help command"""
    help_text = (
        "*MEV Alert Bot - Help*\n\n"
        "*Commands:*\n"
        "/start - Show main menu\n"
        "/add <address> <name> - Add wallet to track\n"
        "/remove <address> - Remove wallet\n"
        "/list - List all tracked wallets\n"
        "/help - Show this help\n\n"
        "*What does this bot do?*\n"
        "Monitors Solana wallets and sends you alerts when they make "
        "transactions WITHOUT MEV protection (Jito).\n\n"
        "*Why is this useful?*\n"
        "MEV-protected transactions are more secure and prevent frontrunning. "
        "If a wallet you're tracking stops using MEV protection, you'll know immediately.\n\n"
        "*Example:*\n"
        "`/add DYw8...NSKK TopTrader`"
    )

    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_callback:
        await update.callback_query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')


def main():
    """Start the bot"""
    global bot_application

    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file!")
        return

    print("🤖 MEV Alert Bot Starting...")
    print(f"📡 Solana RPC: {os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')}")

    # Create application
    bot_application = Application.builder().token(token).build()

    # Add handlers
    bot_application.add_handler(CommandHandler("start", start_command))
    bot_application.add_handler(CommandHandler("add", add_wallet_command))
    bot_application.add_handler(CommandHandler("remove", remove_wallet_command))
    bot_application.add_handler(CommandHandler("list", list_wallets_command))
    bot_application.add_handler(CommandHandler("help", help_command))
    bot_application.add_handler(CallbackQueryHandler(button_callback))

    # Start bot
    print("✅ Bot started! Send /start to your bot in Telegram.")
    print("Press Ctrl+C to stop\n")

    # run_polling() is synchronous and manages its own event loop
    bot_application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
