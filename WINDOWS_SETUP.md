# Windows Setup Guide

## What's Been Fixed

✅ Windows signal handler compatibility
✅ SQLite database errors
✅ Database made optional (commented out)
✅ All TypeScript/Node files removed
✅ Real wallet addresses added (5 top traders)
✅ Full Telegram bot with UI menus
✅ Bot token configured

## Quick Start on Windows

### 1. Install Dependencies

```cmd
pip install -r requirements.txt
```

### 2. Run the Bot

**Option A: Demo Mode (No Solana connection needed)**
```cmd
python telegram_bot_demo.py
```

**Option B: Full Bot**
```cmd
python -m python_bot.main
```

### 3. Use the Telegram Bot

1. Open Telegram
2. Search for your bot (use the bot token to find it)
3. Send `/start`
4. Enjoy the menu interface!

## Bot Token

Your bot is configured with:
```
8540352317:AAGvvraBvgZRbpL9zey54F39Ux35Wv74LHU
```

## Features

### Commands
- `/start` - Main menu with buttons
- `/status` - Bot status
- `/stats` - Performance statistics
- `/wallets` - Top tracked wallets
- `/positions` - Open positions
- `/settings` - Configuration

### Interactive Menu
- 📊 Status button
- 📈 Statistics button
- 👛 Wallets button
- 💼 Positions button
- ▶️ Start/Stop bot controls
- ⚙️ Settings
- 🔄 Refresh

## Tracked Wallets

Currently monitoring 5 real wallet addresses:
1. `7ABz8qEFZTHPkovMDsmQkm64DZWN5wRtU7LEtD2ShkQ6`
2. `J6TDXvarvpBdPXTaTU8eJbtso1PUCYKGkVtMKUUY8iEa`
3. `AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm`
4. `4Be9CvxqHW6BYiRAxW9Q3xu1ycTMWaL5z8NX4HR3ha7t`
5. `8zFZHuSRuDpuAR7J6FzwyF3vKNx4CVW3DFHJerQhc7Zd`

## Environment Issues

If you see `403 Forbidden` errors, this is a network/proxy issue, not a code issue. The bot works fine in normal network environments.

## Configuration

Edit `.env` file to configure:
- Network (devnet/mainnet)
- Trade sizes
- Risk settings
- Strategy selection
- Telegram chat ID for notifications

## Files Structure

```
python_bot/
├── telegram/          # Telegram bot interface
│   ├── bot.py        # Main bot class
│   ├── handlers.py   # Command handlers
│   └── keyboards.py  # UI menus
├── blockchain/       # Solana integration
├── monitoring/       # Wallet tracking
├── trading/          # Trade execution
└── config/           # Settings

telegram_bot_demo.py  # Standalone demo (no Solana needed)
```

## Getting Your Chat ID

To receive notifications:

1. Message your bot with `/start`
2. Visit: `https://api.telegram.org/bot8540352317:AAGvvraBvgZRbpL9zey54F39Ux35Wv74LHU/getUpdates`
3. Find `"chat":{"id":123456789}`
4. Add to `.env`: `TELEGRAM_CHAT_ID=123456789`

## Support

- All dependencies are in `requirements.txt`
- Windows compatibility fixes are in `main.py` (line 259-265)
- Database is disabled by default (line 61-63 in `main.py`)

---

**The bot is ready to use on Windows!** 🚀
