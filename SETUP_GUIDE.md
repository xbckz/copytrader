# Solana Copy Trading Bot - Setup Guide

## Overview

This is a realistic simulation of a Solana copy trading bot with:
- **Real blockchain data** from Helius API
- **Accurate fee simulation** (network fees, slippage, price impact)
- **EUR-based balance** starting at €20
- **Manual wallet tracking** to monitor specific traders
- **Multiple trading sessions** with different strategies
- **Telegram frontend** for easy control

## Quick Start

### 1. Get Required API Keys

#### Helius API (Required - FREE)
Helius provides enhanced Solana RPC access with transaction parsing and better rate limits.

1. Visit https://www.helius.dev/
2. Click "Sign Up" (it's FREE)
3. Create an account
4. Go to Dashboard
5. Create a new API key
6. Copy your API key

**Free tier includes:**
- 100,000 credits/month
- Enhanced RPC endpoints
- Transaction parsing
- Webhook support

#### Telegram Bot Token (Required for UI)
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Start a chat with your new bot
6. Get your chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the JSON response

#### KOLscan API (Optional)
Only needed if you want automatic discovery of top traders.

1. Visit https://kolscan.io/
2. Sign up for an account
3. Get your API key from dashboard

**Note:** Without KOLscan, you can manually add wallets to track.

### 2. Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # Required
   HELIUS_API_KEY=your_helius_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id

   # Optional
   KOLSCAN_API_KEY=your_kolscan_api_key_here
   ```

3. Configure initial settings:
   ```bash
   # Starting balance (EUR)
   INITIAL_BALANCE_EUR=20.0

   # Current SOL price (will be updated dynamically)
   SOL_PRICE_EUR=200.0

   # Simulation mode (recommended for testing)
   SIMULATE_TRADES=true

   # Use mainnet for realistic data
   SOLANA_NETWORK=mainnet-beta
   USE_DEVNET=false
   ```

### 3. Install Dependencies

```bash
cd python_bot
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python -m python_bot.database.init_db
```

### 5. Run the Bot

```bash
python -m python_bot.main
```

## Features Explained

### 1. Balance Management

- **Starting Balance:** €20 (converted to SOL at current rate)
- **Add Balance:** Use the "💰 Balance" menu to add more funds
- **Quick Add:** €10, €20, €50, €100, €200 buttons
- **Custom Amount:** Add any amount you want
- **Transaction History:** View all deposits and trading activity

### 2. Manual Wallet Tracking

Since we removed placeholder data, you need to manually add wallets to track:

1. Click "👛 Tracked Wallets"
2. Click "➕ Add Wallet"
3. Send the Solana wallet address
4. Optionally add a name and notes
5. The bot will start monitoring this wallet's trades

**Finding Good Wallets to Track:**
- https://kolscan.io/leaderboard (if you have API key)
- https://www.topwallets.ai/top-kols
- https://gmgn.ai/
- Twitter/Discord trader shares
- On-chain analytics tools

### 3. Trading Sessions

Create multiple sessions to test different strategies:

1. Click "🎯 Sessions"
2. Click "➕ New Session"
3. Choose a strategy:
   - **Conservative:** 10% TP, 5% SL, low risk
   - **Balanced:** 20% TP, 10% SL, medium risk
   - **Aggressive:** 50% TP, 15% SL, high risk
   - **Scalper:** 5% TP, 3% SL, quick trades
   - **HODL:** 100% TP, 25% SL, long-term

4. Each session has its own:
   - Balance
   - Strategy configuration
   - Performance metrics
   - Trade history

### 4. Realistic Fee Simulation

All simulated trades include accurate fees:

- **Network Fee:** ~0.000005 SOL (base Solana fee)
- **Priority Fee:** 0.00005 SOL (configurable)
- **Platform Fee:** 0.25% (Jupiter DEX fee)
- **Slippage:** 0-1% (random, realistic)
- **Price Impact:** 0.01%-1% (based on trade size)

This means the simulation logic can be used directly for real trading!

### 5. Telegram Menu Structure

```
Main Menu
├── 📊 Status - Bot status and active session
├── 📈 Statistics - Performance across all sessions
├── 💰 Balance - Manage funds
│   ├── ➕ Add Balance
│   ├── 📜 Transactions
│   └── 💱 Update SOL Price
├── 🎯 Sessions - Manage trading sessions
│   ├── ➕ New Session
│   ├── 📋 View All
│   ├── 🎯 Switch Active
│   └── ⚙️ Configure
├── 👛 Tracked Wallets - Manual wallet management
│   ├── ➕ Add Wallet
│   ├── 📋 View All
│   ├── 🔍 Search
│   └── ❌ Remove
├── 💼 Positions - View open trades
├── ▶️ Start Bot - Begin trading
├── ⏸️ Stop Bot - Pause trading
├── ⚙️ Settings - Configure bot
└── 🔄 Refresh - Update data
```

## Architecture

The bot is now structured with clean separation:

```
┌─────────────────────┐
│  Telegram Frontend  │  (User Interface)
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│   Bot Backend API   │  (Business Logic)
├─────────────────────┤
│ • SessionManager    │  (Multiple trading sessions)
│ • BalanceManager    │  (EUR/SOL balance tracking)
│ • WalletTracker     │  (Manual wallet management)
│ • FeeCalculator     │  (Realistic fee simulation)
│ • HeliusClient      │  (Real blockchain data)
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│   Blockchain Layer  │
├─────────────────────┤
│ • Solana RPC        │
│ • Helius Enhanced   │
│ • Jupiter DEX       │
│ • Transaction Mon.  │
└─────────────────────┘
```

## Configuration Options

### Strategy Parameters

Edit strategies in `python_bot/config/strategies.py`:

- `take_profit_pct`: % profit target
- `stop_loss_pct`: % loss limit
- `copy_percentage`: % of tracked wallet's trade size
- `max_positions`: Maximum concurrent positions
- `max_hold_time`: Maximum time to hold (minutes)

### Risk Management

Adjust in `.env`:

```bash
SLIPPAGE_BPS=100              # 1% slippage tolerance
PRIORITY_FEE_LAMPORTS=50000   # Higher = faster execution
MAX_POSITION_SIZE=0.3         # Max 30% balance per trade
```

### Fee Configuration

```bash
BASE_NETWORK_FEE=0.000005     # Solana base fee
JUPITER_PLATFORM_FEE_BPS=25   # Jupiter fee (0.25%)
```

## Testing the Simulation

1. **Add a wallet to track:**
   - Find a high-volume Solana trader
   - Add their address via Telegram menu
   - Monitor their recent trades

2. **Create multiple sessions:**
   - Session 1: Conservative strategy
   - Session 2: Aggressive strategy
   - Compare performance

3. **Add balance incrementally:**
   - Start with €20
   - Add €50 when profitable
   - Test different capital levels

4. **Monitor realistic fees:**
   - Check trade details
   - Verify fee calculations
   - Ensure fees match real Jupiter costs

## Next Steps: Going Live

When you're ready for real trading:

1. Set up a Solana wallet:
   ```bash
   solana-keygen new --outfile ~/.config/solana/id.json
   ```

2. Fund the wallet with SOL

3. Update `.env`:
   ```bash
   WALLET_PRIVATE_KEY=<your_private_key>
   WALLET_PUBLIC_KEY=<your_public_key>
   SIMULATE_TRADES=false
   TEST_MODE=false
   ```

4. Test with small amounts first!

## Troubleshooting

### "KOLscan API not available"
- This is normal if you don't have a KOLscan API key
- Use manual wallet tracking instead

### "Helius client not available"
- Check your `HELIUS_API_KEY` in `.env`
- Verify you have internet connection
- Check Helius dashboard for API usage

### "No wallets being monitored"
- Manually add wallets via Telegram menu
- Check wallet addresses are valid Solana addresses

### Telegram bot not responding
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check `TELEGRAM_CHAT_ID` matches your chat
- Ensure bot is running (`python -m python_bot.main`)

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration in `.env`
3. Verify API keys are valid
4. Check Solana network status

## License

MIT License - Use at your own risk. This is simulation software for educational purposes.
