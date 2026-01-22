"""
Telegram bot keyboard layouts
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    """Get main menu inline keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("📈 Statistics", callback_data="stats")
        ],
        [
            InlineKeyboardButton("👛 Wallets", callback_data="wallets"),
            InlineKeyboardButton("💼 Positions", callback_data="positions")
        ],
        [
            InlineKeyboardButton("▶️ Start Bot", callback_data="start_bot"),
            InlineKeyboardButton("⏸️ Stop Bot", callback_data="stop_bot")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_button():
    """Get back to main menu button"""
    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard():
    """Get settings menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Strategy", callback_data="settings_strategy"),
            InlineKeyboardButton("💰 Trade Size", callback_data="settings_trade_size")
        ],
        [
            InlineKeyboardButton("🛡️ Risk Settings", callback_data="settings_risk"),
            InlineKeyboardButton("🌐 Network", callback_data="settings_network")
        ],
        [
            InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
            InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_wallets_keyboard(page=0):
    """Get wallets list keyboard with pagination"""
    keyboard = [
        [
            InlineKeyboardButton("◀️ Prev", callback_data=f"wallets_prev_{page}"),
            InlineKeyboardButton(f"Page {page + 1}", callback_data="wallets_page"),
            InlineKeyboardButton("▶️ Next", callback_data=f"wallets_next_{page}")
        ],
        [InlineKeyboardButton("🔄 Refresh Wallets", callback_data="wallets_refresh")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_positions_keyboard():
    """Get positions keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Open Positions", callback_data="positions_open"),
            InlineKeyboardButton("📜 Trade History", callback_data="positions_history")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="positions"),
            InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action):
    """Get confirmation keyboard for actions"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
