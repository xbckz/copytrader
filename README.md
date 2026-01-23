# MEV Alert Bot for Solana

A simple Telegram bot that monitors Solana wallets and sends alerts when they make **non-MEV-protected** transactions.

## What Does It Do?

This bot:
1. 📍 Tracks Solana wallet addresses you specify
2. 🔍 Monitors every transaction they make in real-time
3. 🚨 Sends you a Telegram alert when they make a transaction **WITHOUT** MEV protection (no Jito)
4. ✅ Silent when they use MEV protection (Jito)

## Why Is This Useful?

- **Copy Trading**: Know when traders you follow stop using MEV protection
- **Security**: Get alerted if your own wallet makes unprotected transactions
- **Research**: Study MEV protection adoption patterns

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Bot

Create a `.env` file:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_@BotFather

# Optional (defaults to mainnet)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### 3. Run

```bash
python mev_alert_bot.py
```

## Usage

### Start the bot in Telegram

Send `/start` to your bot and you'll see a menu with options:

### Add a wallet to track

```
/add <wallet_address> <wallet_name>
```

Example:
```
/add DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK TopTrader
```

### List all tracked wallets

```
/list
```

### Remove a wallet

```
/remove <wallet_address>
```

## How It Works

The bot uses **MEV protection detection** to identify transactions:

### MEV Protected (No Alert)
- Transactions sent through Jito Block Engine
- Uses Jito tip accounts
- Bypasses public mempool
- ✅ **No notification sent**

### Non-MEV Protected (Alert Sent)
- Regular public transactions
- Visible in mempool
- No Jito protection
- 🚨 **Alert sent to Telegram**

## Example Alert

When a tracked wallet makes a non-protected transaction, you'll receive:

```
🚨 NON-MEV-PROTECTED TRANSACTION DETECTED!

📛 Wallet: TopTrader
📍 Address: DYw8jCTfwHNRJh...
📝 Signature: 5J7zN...
🔢 Slot: 245123456
⚠ Status: Public mempool transaction

🔗 View on Solscan
🔗 View on SolanaFM
```

## Commands

- `/start` - Show main menu
- `/add <address> <name>` - Add wallet to track
- `/remove <address>` - Stop tracking wallet
- `/list` - Show all tracked wallets
- `/help` - Show help message

## Requirements

- Python 3.11+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- Solana RPC endpoint (optional, uses public mainnet by default)

## Advanced Configuration

### Use Custom RPC

For better performance, use a premium RPC provider:

```bash
SOLANA_RPC_URL=https://your-premium-rpc.com
```

Recommended providers:
- Helius
- QuickNode
- Alchemy

### Use Devnet for Testing

```bash
SOLANA_RPC_URL=https://api.devnet.solana.com
```

## Files

- `mev_alert_bot.py` - Main Telegram bot
- `mev_protection_checker.py` - MEV detection module
- `.env` - Configuration (create this)
- `requirements.txt` - Python dependencies

## License

MIT

## Disclaimer

This bot is for informational purposes. MEV detection accuracy depends on RPC provider capabilities and network conditions.
