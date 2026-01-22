# Telegram Bot Guide

## Overview

The Solana Copy Trading Bot now includes a full-featured Telegram interface with a beautiful menu UI for easy bot control and monitoring.

## Bot Token

Your bot token is already configured:
```
8540352317:AAGvvraBvgZRbpL9zey54F39Ux35Wv74LHU
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your bot:**
   - The bot token is already set in `.env`
   - You can optionally set `TELEGRAM_CHAT_ID` to receive notifications

3. **Start the bot:**
   ```bash
   python -m python_bot.main
   ```

4. **Open Telegram:**
   - Search for your bot using the bot token
   - Send `/start` to begin

## Features

### 📱 Main Menu
Beautiful inline keyboard with quick access to all features:
- 📊 Status - View bot status
- 📈 Statistics - Performance stats
- 👛 Wallets - Tracked wallets
- 💼 Positions - Open positions
- ▶️ Start Bot - Start trading
- ⏸️ Stop Bot - Pause trading
- ⚙️ Settings - Bot configuration
- 🔄 Refresh - Update display

### 🤖 Available Commands

#### `/start`
- Welcome message
- Main menu display
- Quick overview of features

#### `/status`
- Bot running status
- Network information
- Tracked wallets count
- Average win rate
- Active strategies

#### `/stats`
- Detailed performance statistics
- Current balance
- Portfolio value
- Total PnL (SOL and %)
- Open positions count
- Total trades
- Win rate

#### `/wallets`
- Top 10 tracked wallets
- PnL for each wallet
- Win rate
- Total trades
- Pagination support

#### `/positions`
- Current open positions
- Position details
- Trade history access

#### `/settings`
- View current configuration
- Network settings
- Test mode status
- Trade simulation status
- Active strategy
- Trade size limits
- Slippage tolerance

#### `/help`
- List of all commands
- Quick help guide

### 🔔 Notifications

The bot automatically sends notifications for:

**Trade Notifications:**
- 🟢 BUY trades executed
- 🔴 SELL trades executed
- Token address
- Amount in SOL
- Price
- Source wallet

**Position Updates:**
- 💰 Profitable position closures
- 📉 Loss position closures
- PnL in SOL and percentage

**Error Notifications:**
- ❌ Critical errors
- System alerts

### 🎮 Interactive Controls

**Start/Stop Bot:**
- Click "▶️ Start Bot" to begin trading
- Click "⏸️ Stop Bot" to pause
- Confirmation messages for each action

**Navigation:**
- ⬅️ Back buttons on all screens
- 🔄 Refresh to update data
- Smooth menu transitions

## How to Get Your Chat ID

To receive notifications, you need to set your Telegram chat ID:

1. Message your bot with `/start`
2. Visit: `https://api.telegram.org/bot8540352317:AAGvvraBvgZRbpL9zey54F39Ux35Wv74LHU/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. Copy your chat ID
5. Add to `.env`:
   ```
   TELEGRAM_CHAT_ID=123456789
   ```

## Screenshots

### Main Menu
```
🤖 Solana Copy Trading Bot

Status: 🟢 Running
Time: 2026-01-22 22:45:30

Select an option from the menu below:

[📊 Status] [📈 Statistics]
[👛 Wallets] [💼 Positions]
[▶️ Start Bot] [⏸️ Stop Bot]
[⚙️ Settings] [🔄 Refresh]
```

### Status View
```
📊 Bot Status
━━━━━━━━━━━━━━━━━━━━

Status: 🟢 Running
Network: https://api.devnet.solana.com
Tracked Wallets: 5
Avg Win Rate: 72.50%
Active Strategies: 1

Last Updated: 22:45:30

[⬅️ Back to Menu]
```

### Statistics View
```
📈 Performance Statistics
━━━━━━━━━━━━━━━━━━━━

Strategy: Conservative
Balance: 100.0000 SOL
Portfolio: 102.5000 SOL
Total PnL: 2.5000 SOL (2.50%)
Open Positions: 3
Total Trades: 15
Win Rate: 73.33%

[⬅️ Back to Menu]
```

## Security Notes

⚠️ **Important:**
- Your bot token is sensitive - keep `.env` file secure
- Never commit `.env` to version control (already in `.gitignore`)
- Only share your bot link with trusted users
- Monitor bot activity regularly

## Troubleshooting

### Bot not responding
1. Check if bot is running: `python -m python_bot.main`
2. Verify bot token in `.env`
3. Check internet connection
4. Look for errors in logs

### No notifications
1. Set `TELEGRAM_CHAT_ID` in `.env`
2. Enable notifications: `ENABLE_TELEGRAM_NOTIFICATIONS=true`
3. Send `/start` to your bot first

### Commands not working
1. Make sure you're chatting with the correct bot
2. Try `/start` to reset the bot
3. Check bot logs for errors

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review error messages in Telegram
- Verify all settings in `.env`

---

**Enjoy your Telegram-powered trading bot! 🚀**
