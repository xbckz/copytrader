# Solana Copy Trading Bot

A Telegram bot for copy trading on Solana blockchain with wallet tracking and automated trading strategies.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
HELIUS_API_KEY=your_helius_api_key (optional)
SOLANA_RPC_URL=https://api.devnet.solana.com (optional)
```

### Run

```bash
python run_bot_new.py
```

## Features

- 🎯 **Wallet Tracking**: Monitor profitable traders and copy their moves
- 💰 **Multiple Strategies**: Conservative, Balanced, and Aggressive trading strategies
- 📊 **Session Management**: Track multiple trading sessions with independent statistics
- 💼 **Position Management**: Automatic position tracking with P&L calculations
- 📈 **Trade History**: Complete history of all executed trades
- ⚡ **Real-time Updates**: Live balance and statistics updates

## Architecture

The bot uses a clean architecture with separated concerns:

- `python_bot/services/` - Core business logic (backend, sessions, balances)
- `python_bot/blockchain/` - Blockchain interactions (Solana RPC, Helius API)
- `python_bot/trading/` - DEX integrations (Jupiter aggregator)
- `python_bot/telegram/` - Telegram bot interface
- `python_bot/monitoring/` - Wallet tracking and analysis

## Demo Mode

If Solana SDK is not installed, the bot runs in demo mode with simulated trading for testing purposes.

## License

MIT
