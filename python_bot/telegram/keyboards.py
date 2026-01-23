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
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("🎯 Sessions", callback_data="sessions")
        ],
        [
            InlineKeyboardButton("👛 Tracked Wallets", callback_data="wallets"),
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


def get_balance_keyboard():
    """Get balance management keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Balance", callback_data="balance_add"),
            InlineKeyboardButton("📜 Transactions", callback_data="balance_transactions")
        ],
        [
            InlineKeyboardButton("💱 Update SOL Price", callback_data="balance_update_price"),
            InlineKeyboardButton("🔄 Refresh", callback_data="balance")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_balance_keyboard():
    """Get quick add balance amounts keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("€10", callback_data="balance_add_10"),
            InlineKeyboardButton("€20", callback_data="balance_add_20"),
            InlineKeyboardButton("€50", callback_data="balance_add_50")
        ],
        [
            InlineKeyboardButton("€100", callback_data="balance_add_100"),
            InlineKeyboardButton("€200", callback_data="balance_add_200"),
            InlineKeyboardButton("💶 Custom", callback_data="balance_add_custom")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="balance")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_sessions_keyboard():
    """Get sessions management keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("➕ New Session", callback_data="session_create"),
            InlineKeyboardButton("📋 View All", callback_data="sessions_list")
        ],
        [
            InlineKeyboardButton("🎯 Switch Active", callback_data="session_switch"),
            InlineKeyboardButton("⚙️ Configure", callback_data="session_configure")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="sessions"),
            InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_session_strategy_keyboard():
    """Get strategy selection keyboard for new session"""
    keyboard = [
        [InlineKeyboardButton("🛡️ Strategy 1: Conservative", callback_data="session_strategy_1")],
        [InlineKeyboardButton("⚖️ Strategy 2: Balanced", callback_data="session_strategy_2")],
        [InlineKeyboardButton("🚀 Strategy 3: Aggressive", callback_data="session_strategy_3")],
        [InlineKeyboardButton("⚡ Strategy 4: Scalper", callback_data="session_strategy_4")],
        [InlineKeyboardButton("💎 Strategy 5: HODL", callback_data="session_strategy_5")],
        [InlineKeyboardButton("⬅️ Back", callback_data="sessions")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_wallets_management_keyboard():
    """Get wallet management keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Wallet", callback_data="wallet_add"),
            InlineKeyboardButton("📋 View All", callback_data="wallets_list")
        ],
        [
            InlineKeyboardButton("🔍 Search", callback_data="wallet_search"),
            InlineKeyboardButton("❌ Remove", callback_data="wallet_remove")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="wallets"),
            InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_wallet_actions_keyboard(wallet_address):
    """Get actions keyboard for a specific wallet"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit Name", callback_data=f"wallet_edit_{wallet_address[:8]}"),
            InlineKeyboardButton("📊 View Stats", callback_data=f"wallet_stats_{wallet_address[:8]}")
        ],
        [
            InlineKeyboardButton("⏸️ Deactivate", callback_data=f"wallet_deactivate_{wallet_address[:8]}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"wallet_delete_{wallet_address[:8]}")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="wallets_list")]
    ]
    return InlineKeyboardMarkup(keyboard)
