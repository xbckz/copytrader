"""
Telegram bot command handlers - Complete implementation
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
from datetime import datetime
from typing import TYPE_CHECKING

from .keyboards import (
    get_main_menu_keyboard,
    get_back_button,
    get_settings_keyboard,
    get_wallets_keyboard,
    get_positions_keyboard,
    get_balance_keyboard,
    get_add_balance_keyboard,
    get_sessions_keyboard,
    get_session_strategy_keyboard,
    get_wallets_management_keyboard,
    get_wallet_actions_keyboard
)
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..services.bot_backend import CopyTradingBackend

logger = get_logger(__name__)

# Conversation states
WAITING_WALLET_ADDRESS, WAITING_WALLET_NAME, WAITING_BALANCE_AMOUNT, WAITING_SESSION_NAME = range(4)


class TelegramHandlers:
    """Handlers for Telegram bot commands and callbacks"""

    def __init__(self, backend: 'CopyTradingBackend'):
        """
        Initialize handlers

        Args:
            backend: Bot backend instance
        """
        self.backend = backend

    # ==================== Helper Methods ====================

    async def _safe_edit_message(self, query, text: str, reply_markup=None):
        """Safely edit message, avoiding 'message not modified' errors"""
        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                # Message content is the same, ignore
                pass
            else:
                logger.error(f"Error editing message: {e}")
                # Try sending new message instead
                await query.message.reply_text(text=text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Unexpected error editing message: {e}")

    async def _send_or_edit(self, update_or_query, text: str, reply_markup=None):
        """Send new message or edit existing based on update type"""
        if hasattr(update_or_query, 'callback_query'):
            # It's an update with callback_query
            await self._safe_edit_message(update_or_query.callback_query, text, reply_markup)
        elif hasattr(update_or_query, 'edit_message_text'):
            # It's a callback_query
            await self._safe_edit_message(update_or_query, text, reply_markup)
        elif hasattr(update_or_query, 'reply_text'):
            # It's a message
            await update_or_query.reply_text(text=text, reply_markup=reply_markup)
        elif hasattr(update_or_query, 'message'):
            # It's an update with message
            await update_or_query.message.reply_text(text=text, reply_markup=reply_markup)

    # ==================== Commands ====================

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")

        welcome_text = (
            f"👋 Welcome to Solana Copy Trading Bot, {user.first_name}!\n\n"
            "🤖 Realistic simulation with real blockchain data.\n\n"
            "📊 Features:\n"
            "• Manual wallet tracking\n"
            "• Multiple trading sessions\n"
            "• EUR-based balance (start with €20)\n"
            "• Accurate fee simulation\n"
            "• Real-time monitoring\n\n"
            "Use the menu below to get started:"
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
            "/help - Show this help message\n\n"
            "💰 Balance Management:\n"
            "• Add funds (€10-€200 or custom)\n"
            "• View transaction history\n\n"
            "🎯 Session Management:\n"
            "• Create multiple trading sessions\n"
            "• Test different strategies\n"
            "• Compare performance\n\n"
            "👛 Wallet Tracking:\n"
            "• Add wallets manually\n"
            "• Monitor real trades\n"
            "• Track performance\n\n"
            "Use the inline buttons for easy navigation!"
        )

        await update.message.reply_text(help_text, reply_markup=get_back_button())

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        await self._show_status(update.message)

    # ==================== Callback Handler ====================

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
            await self._show_status(query)

        # Statistics
        elif callback_data == "stats":
            await self._show_stats(query)

        # Balance
        elif callback_data == "balance":
            await self._show_balance(query)
        elif callback_data == "balance_add":
            await self._show_add_balance(query)
        elif callback_data.startswith("balance_add_"):
            await self._handle_quick_add_balance(query, callback_data)
        elif callback_data == "balance_transactions":
            await self._show_balance_transactions(query)
        elif callback_data == "balance_update_price":
            await self._update_sol_price(query)

        # Sessions
        elif callback_data == "sessions":
            await self._show_sessions(query)
        elif callback_data == "session_create":
            await self._show_create_session(query)
        elif callback_data.startswith("session_strategy_"):
            await self._handle_strategy_selection(query, callback_data, context)
        elif callback_data == "sessions_list":
            await self._show_sessions_list(query)
        elif callback_data == "session_switch":
            await self._show_switch_session(query)
        elif callback_data.startswith("session_select_"):
            await self._handle_session_selection(query, callback_data)

        # Wallets
        elif callback_data == "wallets":
            await self._show_wallets(query)
        elif callback_data == "wallet_add":
            await self._start_add_wallet(query, context)
        elif callback_data == "wallets_list":
            await self._show_wallets_list(query)
        elif callback_data == "wallet_remove":
            await self._show_remove_wallet(query)
        elif callback_data.startswith("wallet_delete_"):
            await self._handle_wallet_delete(query, callback_data)
        elif callback_data.startswith("wallet_stats_"):
            await self._show_wallet_stats(query, callback_data)

        # Positions
        elif callback_data == "positions":
            await self._show_positions(query)
        elif callback_data == "positions_open":
            await self._show_open_positions(query)
        elif callback_data == "positions_history":
            await self._show_trade_history(query)

        # Settings
        elif callback_data == "settings":
            await self._show_settings(query)

        # Bot control
        elif callback_data == "start_bot":
            await self._start_bot(query)
        elif callback_data == "stop_bot":
            await self._stop_bot(query)

        # Refresh
        elif callback_data == "refresh":
            await self._show_main_menu(query)

    # ==================== Main Menu ====================

    async def _show_main_menu(self, query):
        """Show main menu"""
        status = await self.backend.get_bot_status()
        active_session = self.backend.get_active_session()

        is_running = "🟢 Running" if status['is_running'] else "🔴 Stopped"

        menu_text = (
            "🤖 Solana Copy Trading Bot\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Status: {is_running}\n"
            f"Network: {status['network']}\n"
            f"Active Session: {active_session.name if active_session else 'None'}\n"
            f"Tracked Wallets: {status['tracked_wallets']}\n"
            f"SOL Price: €{status['sol_price_eur']:.2f}\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "Select an option from the menu below:"
        )

        await self._safe_edit_message(query, menu_text, get_main_menu_keyboard())

    # ==================== Status ====================

    async def _show_status(self, query):
        """Show bot status"""
        status = await self.backend.get_bot_status()
        active_session = self.backend.get_active_session()

        is_running = "🟢 Running" if status['is_running'] else "🔴 Stopped"

        status_text = (
            "📊 Bot Status\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Status: {is_running}\n"
            f"Network: {status['network']}\n"
            f"Using Helius: {'✅ Yes' if status['using_helius'] else '❌ No'}\n\n"
            "🎯 Active Session:\n"
        )

        if active_session:
            session_stats = active_session.get_statistics()
            status_text += (
                f"  Name: {session_stats['name']}\n"
                f"  Strategy: {session_stats['strategy_name']}\n"
                f"  Balance: €{session_stats['balance_eur']:.2f}\n"
                f"  PnL: €{session_stats['total_pnl_eur']:.2f} ({session_stats['total_pnl_percentage']:.1f}%)\n"
                f"  Win Rate: {session_stats['win_rate']:.1f}%\n"
            )
        else:
            status_text += "  No active session\n"

        status_text += (
            f"\n👛 Tracked Wallets: {status['tracked_wallets']}\n"
            f"💰 SOL Price: €{status['sol_price_eur']:.2f}\n"
            f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        )

        await self._safe_edit_message(query, status_text, get_back_button())

    # ==================== Statistics ====================

    async def _show_stats(self, query):
        """Show performance statistics"""
        overall_stats = self.backend.get_overall_statistics()
        sessions = self.backend.list_sessions()

        if not sessions:
            stats_text = (
                "📈 No statistics available yet.\n\n"
                "Create a session to start trading!"
            )
        else:
            stats_text = (
                "📈 Performance Statistics\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 Total Balance: €{overall_stats['total_balance_eur']:.2f}\n"
                f"📊 Total PnL: €{overall_stats['total_pnl_eur']:.2f}\n"
                f"🎯 Active Sessions: {overall_stats['active_sessions']}\n"
                f"📈 Total Trades: {overall_stats['total_trades']}\n"
                f"✅ Win Rate: {overall_stats['overall_win_rate']:.1f}%\n\n"
                "Sessions:\n"
            )

            for session in sessions[:5]:  # Show up to 5 sessions
                session_stats = session.get_statistics()
                stats_text += (
                    f"\n🎯 {session_stats['name']}\n"
                    f"  Balance: €{session_stats['balance_eur']:.2f}\n"
                    f"  PnL: €{session_stats['total_pnl_eur']:.2f} ({session_stats['total_pnl_percentage']:.1f}%)\n"
                    f"  Trades: {session_stats['total_trades']} | Win: {session_stats['win_rate']:.1f}%\n"
                )

        await self._safe_edit_message(query, stats_text, get_back_button())

    # ==================== Balance ====================

    async def _show_balance(self, query):
        """Show balance information"""
        active_session = self.backend.get_active_session()

        if not active_session:
            balance_text = (
                "💰 Balance\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ No active session\n\n"
                "Create a session first!"
            )
        else:
            balance_stats = active_session.balance_manager.get_statistics()

            balance_text = (
                "💰 Balance\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Session: {active_session.name}\n\n"
                f"💶 Current Balance: €{balance_stats['current_balance_eur']:.2f}\n"
                f"💎 In SOL: {balance_stats['current_balance_sol']:.4f} SOL\n\n"
                f"📊 Initial: €{balance_stats['initial_balance_eur']:.2f}\n"
                f"📈 Total PnL: €{balance_stats['total_pnl_eur']:.2f} ({balance_stats['total_pnl_percentage']:.1f}%)\n\n"
                f"💱 SOL Price: €{balance_stats['sol_price_eur']:.2f}\n"
                f"💳 Deposits: {balance_stats['total_deposits']}\n"
            )

        await self._safe_edit_message(query, balance_text, get_balance_keyboard())

    async def _show_add_balance(self, query):
        """Show add balance options"""
        add_balance_text = (
            "➕ Add Balance\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Select an amount to add:"
        )

        await self._safe_edit_message(query, add_balance_text, get_add_balance_keyboard())

    async def _handle_quick_add_balance(self, query, callback_data):
        """Handle quick add balance button"""
        # Extract amount from callback_data (e.g., "balance_add_10" -> 10)
        amount_str = callback_data.replace("balance_add_", "")

        if amount_str == "custom":
            # TODO: Implement custom amount input
            await query.answer("Custom amount not implemented yet", show_alert=True)
            return

        try:
            amount_eur = float(amount_str)

            # Add balance to active session
            active_session = self.backend.get_active_session()
            if not active_session:
                await query.answer("No active session!", show_alert=True)
                return

            transaction = self.backend.add_balance(amount_eur)

            success_text = (
                "✅ Balance Added!\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Amount: €{amount_eur:.2f}\n"
                f"New Balance: €{transaction['balance_after'] * transaction['sol_price_eur']:.2f}\n"
                f"SOL: {transaction['balance_after']:.4f} SOL\n\n"
                "Balance updated successfully!"
            )

            await self._safe_edit_message(query, success_text, get_back_button())

        except Exception as e:
            logger.error(f"Error adding balance: {e}")
            await query.answer(f"Error adding balance: {str(e)}", show_alert=True)

    async def _show_balance_transactions(self, query):
        """Show balance transaction history"""
        active_session = self.backend.get_active_session()

        if not active_session:
            await query.answer("No active session!", show_alert=True)
            return

        transactions = self.backend.get_balance_transactions(limit=10)

        if not transactions:
            tx_text = (
                "📜 Transaction History\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "No transactions yet."
            )
        else:
            tx_text = (
                "📜 Transaction History\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

            for tx in transactions[:10]:
                tx_type = tx['type'].upper()
                amount_eur = tx['amount_eur']
                timestamp = tx['timestamp']

                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except:
                        timestamp = datetime.now()

                tx_text += (
                    f"{'➕' if tx_type == 'DEPOSIT' else '➖'} {tx_type}\n"
                    f"  €{amount_eur:.2f} | {timestamp.strftime('%Y-%m-%d %H:%M')}\n\n"
                )

        await self._safe_edit_message(query, tx_text, get_back_button())

    async def _update_sol_price(self, query):
        """Update SOL price"""
        await self.backend.update_sol_price()
        sol_price = self.backend.get_sol_price_eur()

        await query.answer(f"SOL price updated: €{sol_price:.2f}", show_alert=True)
        await self._show_balance(query)

    # ==================== Sessions ====================

    async def _show_sessions(self, query):
        """Show sessions overview"""
        sessions = self.backend.list_sessions()
        active_session = self.backend.get_active_session()

        sessions_text = (
            "🎯 Trading Sessions\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Total Sessions: {len(sessions)}\n"
            f"Active: {active_session.name if active_session else 'None'}\n\n"
        )

        if sessions:
            for session in sessions[:3]:
                stats = session.get_statistics()
                is_active = "🟢" if session.session_id == (active_session.session_id if active_session else None) else "⚪"
                sessions_text += (
                    f"{is_active} {stats['name']}\n"
                    f"  Strategy: {stats['strategy_name']}\n"
                    f"  Balance: €{stats['balance_eur']:.2f}\n"
                    f"  PnL: €{stats['total_pnl_eur']:.2f} ({stats['total_pnl_percentage']:.1f}%)\n\n"
                )
        else:
            sessions_text += "No sessions yet. Create one to get started!"

        await self._safe_edit_message(query, sessions_text, get_sessions_keyboard())

    async def _show_create_session(self, query):
        """Show create session menu"""
        create_text = (
            "➕ Create New Session\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Select a trading strategy:\n\n"
            "🛡️ Conservative: Low risk, 10% TP / 5% SL\n"
            "⚖️ Balanced: Medium risk, 20% TP / 10% SL\n"
            "🚀 Aggressive: High risk, 50% TP / 15% SL\n"
            "⚡ Scalper: Quick trades, 5% TP / 3% SL\n"
            "💎 HODL: Long-term, 100% TP / 25% SL\n"
        )

        await self._safe_edit_message(query, create_text, get_session_strategy_keyboard())

    async def _handle_strategy_selection(self, query, callback_data, context):
        """Handle strategy selection for new session"""
        # Extract strategy ID (e.g., "session_strategy_1" -> 1)
        strategy_id = int(callback_data.replace("session_strategy_", ""))

        # Store in context for next step
        context.user_data['pending_session_strategy'] = strategy_id

        # For now, create session with default name
        from ..config.strategies import get_strategy
        strategy = get_strategy(strategy_id)

        session_name = f"{strategy.name} Session"

        try:
            session = self.backend.create_session(
                name=session_name,
                strategy_id=strategy_id,
                initial_balance_eur=20.0
            )

            success_text = (
                "✅ Session Created!\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Name: {session.name}\n"
                f"Strategy: {strategy.name}\n"
                f"Balance: €20.00\n\n"
                "Session is now active!"
            )

            await self._safe_edit_message(query, success_text, get_back_button())

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            await query.answer(f"Error: {str(e)}", show_alert=True)

    async def _show_sessions_list(self, query):
        """Show list of all sessions"""
        sessions = self.backend.list_sessions()

        if not sessions:
            list_text = (
                "📋 Sessions List\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "No sessions yet."
            )
        else:
            list_text = (
                "📋 Sessions List\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

            for session in sessions:
                stats = session.get_statistics()
                list_text += (
                    f"{'🟢' if stats['is_active'] else '⚪'} {stats['name']}\n"
                    f"  Strategy: {stats['strategy_name']}\n"
                    f"  Balance: €{stats['balance_eur']:.2f}\n"
                    f"  PnL: {stats['total_pnl_percentage']:.1f}%\n"
                    f"  Trades: {stats['total_trades']} ({stats['win_rate']:.0f}% win)\n\n"
                )

        await self._safe_edit_message(query, list_text, get_back_button())

    async def _show_switch_session(self, query):
        """Show session switch menu"""
        # TODO: Implement session switching UI
        await query.answer("Session switching not fully implemented yet", show_alert=True)

    async def _handle_session_selection(self, query, callback_data):
        """Handle session selection"""
        # TODO: Implement session selection
        await query.answer("Session selection not fully implemented yet", show_alert=True)

    # ==================== Wallets ====================

    async def _show_wallets(self, query):
        """Show wallets overview"""
        wallet_stats = self.backend.get_wallet_statistics()
        wallets = self.backend.list_wallets()

        wallets_text = (
            "👛 Tracked Wallets\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Total Wallets: {wallet_stats['total_wallets']}\n"
            f"Active: {wallet_stats['active_wallets']}\n"
            f"Total Trades: {wallet_stats['total_trades']}\n"
            f"Win Rate: {wallet_stats['overall_win_rate']:.1f}%\n\n"
        )

        if wallets:
            wallets_text += "Recent wallets:\n\n"
            for wallet in wallets[:3]:
                stats = wallet.get_statistics()
                wallets_text += (
                    f"{'🟢' if stats['is_active'] else '⚪'} {stats['name']}\n"
                    f"  {stats['address'][:8]}...{stats['address'][-6:]}\n"
                    f"  Trades: {stats['total_trades']} | Win: {stats['win_rate']:.0f}%\n\n"
                )
        else:
            wallets_text += "No wallets tracked yet.\nAdd a wallet to get started!"

        await self._safe_edit_message(query, wallets_text, get_wallets_management_keyboard())

    async def _start_add_wallet(self, query, context):
        """Start wallet addition process"""
        add_text = (
            "➕ Add Wallet\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Please send the Solana wallet address you want to track.\n\n"
            "Example:\n"
            "7ABz8qEFZTHPkovMDsmQkm64DZWN5wRtU7LEtD2ShkQ6\n\n"
            "Send /cancel to abort."
        )

        await query.message.reply_text(add_text)
        return WAITING_WALLET_ADDRESS

    async def _show_wallets_list(self, query):
        """Show full list of wallets"""
        wallets = self.backend.list_wallets()

        if not wallets:
            list_text = (
                "📋 Wallets List\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "No wallets tracked yet."
            )
        else:
            list_text = (
                "📋 Tracked Wallets\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

            for wallet in wallets:
                stats = wallet.get_statistics()
                list_text += (
                    f"{'🟢' if stats['is_active'] else '⚪'} {stats['name']}\n"
                    f"  {stats['address']}\n"
                    f"  Trades: {stats['total_trades']} | Win: {stats['win_rate']:.1f}%\n"
                    f"  Added: {stats['added_at'].strftime('%Y-%m-%d')}\n\n"
                )

        await self._safe_edit_message(query, list_text, get_back_button())

    async def _show_remove_wallet(self, query):
        """Show wallet removal menu"""
        # TODO: Implement wallet removal UI
        await query.answer("Wallet removal not fully implemented yet", show_alert=True)

    async def _handle_wallet_delete(self, query, callback_data):
        """Handle wallet deletion"""
        # TODO: Implement wallet deletion
        await query.answer("Wallet deletion not fully implemented yet", show_alert=True)

    async def _show_wallet_stats(self, query, callback_data):
        """Show detailed wallet statistics"""
        # TODO: Implement wallet stats display
        await query.answer("Wallet stats not fully implemented yet", show_alert=True)

    # ==================== Positions ====================

    async def _show_positions(self, query):
        """Show positions overview"""
        active_session = self.backend.get_active_session()

        if not active_session:
            pos_text = (
                "💼 Positions\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "No active session."
            )
        else:
            open_positions = len(active_session.active_positions)
            closed_positions = len(active_session.closed_positions)

            pos_text = (
                "💼 Positions\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Session: {active_session.name}\n\n"
                f"📊 Open: {open_positions}\n"
                f"📜 Closed: {closed_positions}\n"
                f"📈 Total Trades: {active_session.total_trades}\n"
                f"✅ Win Rate: {active_session.get_win_rate():.1f}%\n"
            )

        await self._safe_edit_message(query, pos_text, get_positions_keyboard())

    async def _show_open_positions(self, query):
        """Show open positions"""
        active_session = self.backend.get_active_session()

        if not active_session:
            await query.answer("No active session!", show_alert=True)
            return

        if not active_session.active_positions:
            pos_text = (
                "📊 Open Positions\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "No open positions."
            )
        else:
            pos_text = (
                "📊 Open Positions\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )

            for pos_id, position in list(active_session.active_positions.items())[:5]:
                # TODO: Format position details
                pos_text += f"Position {pos_id[:8]}...\n\n"

        await self._safe_edit_message(query, pos_text, get_back_button())

    async def _show_trade_history(self, query):
        """Show trade history"""
        active_session = self.backend.get_active_session()

        if not active_session:
            await query.answer("No active session!", show_alert=True)
            return

        history_text = (
            "📜 Trade History\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Total Trades: {active_session.total_trades}\n"
            f"Winning: {active_session.winning_trades}\n"
            f"Losing: {active_session.losing_trades}\n"
            f"Win Rate: {active_session.get_win_rate():.1f}%\n\n"
            "No detailed history yet."
        )

        await self._safe_edit_message(query, history_text, get_back_button())

    # ==================== Settings ====================

    async def _show_settings(self, query):
        """Show settings menu"""
        settings_text = (
            "⚙️ Settings\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Settings configuration coming soon!\n\n"
            "Current configuration:\n"
            "• Simulation mode: ON\n"
            "• Network: Mainnet\n"
            "• Helius API: Enabled\n"
        )

        await self._safe_edit_message(query, settings_text, get_back_button())

    # ==================== Bot Control ====================

    async def _start_bot(self, query):
        """Start the trading bot"""
        await self.backend.start_bot()
        await query.answer("✅ Bot started!", show_alert=True)
        await self._show_main_menu(query)

    async def _stop_bot(self, query):
        """Stop the trading bot"""
        await self.backend.stop_bot()
        await query.answer("⏸️ Bot stopped!", show_alert=True)
        await self._show_main_menu(query)
