# Local Setup Guide

This repository contains **two different trading bots**. Choose the one you want to run:

## 🐍 Option 1: Python Solana Copy Trading Bot (Recommended)

A production-ready bot that monitors top Solana wallets and copies their trades with 5 different strategies.

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Quick Start (5 minutes)

1. **Clone the repository** (if you haven't already):
```bash
git clone <your-repo-url>
cd copytrader
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
# Copy the example config
cp .env.example .env

# Edit .env with your preferred editor
nano .env
```

**Minimal config for testing** (paste this into `.env`):
```bash
# Solana Network (use devnet for safe testing)
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WS_URL=wss://api.devnet.solana.com
SOLANA_NETWORK=devnet

# Testing mode (SAFE - no real money)
TEST_MODE=true
USE_DEVNET=true
SIMULATE_TRADES=true

# Choose a strategy (1-5) or 'all' to test all strategies
ACTIVE_STRATEGY=1

# Optional: Leave wallet keys empty for simulation mode
WALLET_PRIVATE_KEY=
WALLET_PUBLIC_KEY=
```

4. **Run the bot**:
```bash
# Option A: Use the automated script
./run_bot.sh

# Option B: Run directly
python -m python_bot.main
```

5. **Success!** You should see:
```
================================================================================
SOLANA COPY TRADING BOT
================================================================================
Mode: TEST
Network: devnet
Simulate Trades: True
================================================================================
INFO - Initializing bot components...
INFO - Connected to Solana RPC
INFO - BOT STARTED - Monitoring for trades
```

### What it does:
- Monitors top 100 KOL wallets on Solana
- Detects their trades in real-time
- Copies trades automatically (simulation mode = no real execution)
- Manages positions with Take Profit (TP) and Stop Loss (SL)
- Tracks performance across 5 different strategies

### Available Strategies:
| ID | Name | Take Profit | Stop Loss | Best For |
|----|------|-------------|-----------|----------|
| 1 | Conservative | 10% | 5% | Safe, steady gains |
| 2 | Balanced | 20% | 10% | Medium risk/reward |
| 3 | Aggressive | 50% | 15% | High risk traders |
| 4 | Scalper | 5% | 3% | Quick small profits |
| 5 | HODL | 100% | 25% | Long-term holds |

### Test all strategies:
```bash
# In .env, set:
ACTIVE_STRATEGY=all
```

### Monitoring:
```bash
# View logs
tail -f logs/copytrader_*.log

# Check database
sqlite3 copytrader.db "SELECT * FROM positions;"
```

### Next Steps:
1. ✅ Run in simulation mode (no risk)
2. Test on devnet with free SOL (get from Solana faucet)
3. Compare all strategies to find best performer
4. Read full docs in `README_PYTHON_BOT.md`

---

## 📱 Option 2: TypeScript Telegram MEV Bot

A demo Telegram bot that simulates MEV sniping on Ethereum.

### Prerequisites
- Node.js (v16 or higher)
- npm package manager
- Telegram Bot Token (from @BotFather)

### Quick Start

1. **Install Node.js dependencies**:
```bash
npm install
```

2. **Configure Telegram bot**:
```bash
# Create .env file
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
```

Get your bot token from [@BotFather](https://t.me/BotFather) on Telegram.

3. **Build the bot**:
```bash
npm run build
```

4. **Run the bot**:
```bash
# Production mode
npm start

# Development mode (with auto-reload)
npm run dev
```

5. **Use the bot**:
- Open Telegram
- Search for your bot
- Send `/start` to begin
- Use menu buttons to interact

### Features:
- MEV mempool sniping simulation
- Demo trading with €20 starting balance
- Real-time statistics tracking
- Position management
- Trade history

**Note**: This is a DEMO bot - all trades are simulated!

---

## 🎯 Which Bot Should I Use?

### Use Python Bot if you want:
- Real copy trading functionality
- Solana blockchain integration
- Multiple strategy testing
- Production-ready features
- Position management with TP/SL
- Performance tracking and optimization

### Use TypeScript Bot if you want:
- Simple Telegram interface
- MEV sniping simulation
- Demo/educational purposes
- Ethereum-focused (simulated)
- No setup complexity

---

## 🗂️ Project Structure

```
copytrader/
├── python_bot/              # Python Solana copy trading bot
│   ├── main.py             # Main entry point
│   ├── config/             # Configuration and strategies
│   ├── blockchain/         # Solana client and monitoring
│   ├── trading/            # DEX integration and execution
│   ├── strategy/           # Strategy engine and position management
│   └── monitoring/         # Wallet tracking (KOLscan)
│
├── src/                    # TypeScript Telegram bot
│   ├── index.ts           # Entry point
│   ├── bot.ts             # Bot logic
│   ├── menu.ts            # Telegram UI
│   └── trading/           # Trading simulation
│
├── .env.example           # Example environment configuration
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
├── run_bot.sh            # Automated Python bot runner
├── LOCAL_SETUP.md        # This file
├── README.md             # Telegram bot README
├── README_PYTHON_BOT.md  # Python bot full documentation
└── QUICKSTART.md         # Python bot quick start
```

---

## 🔧 Troubleshooting

### Python Bot Issues

**Can't install dependencies:**
```bash
# Upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt
```

**Connection errors:**
```bash
# Try alternative RPC endpoint
# In .env:
SOLANA_RPC_URL=https://api.devnet.solana.com
```

**No trades detected:**
- This is normal in simulation mode
- The bot simulates based on wallet monitoring
- For real trades, you need devnet or mainnet with actual wallet activity

### TypeScript Bot Issues

**npm install fails:**
```bash
# Clear npm cache
npm cache clean --force
npm install
```

**Bot doesn't respond on Telegram:**
- Check your bot token is correct
- Make sure the bot is started (`npm start`)
- Check console for error messages

---

## 📚 Documentation

- **Python Bot**: See `README_PYTHON_BOT.md` for full documentation
- **Python Quick Start**: See `QUICKSTART.md` for 5-minute setup
- **TypeScript Bot**: See `README.md` for Telegram bot details

---

## ⚠️ Important Safety Notes

### For Testing (Recommended Start):
1. **Always start in simulation mode** (`SIMULATE_TRADES=true`)
2. **Use devnet first** before touching mainnet
3. **Test with small amounts** when you go live
4. **Monitor constantly** - check logs frequently

### Before Going Live:
- [ ] Thoroughly tested in simulation
- [ ] Tested on devnet successfully
- [ ] Reviewed all strategy performance
- [ ] Understand all risks
- [ ] Start with minimal funds
- [ ] Have emergency stop plan

### Risk Warning:
**Cryptocurrency trading involves significant risk of loss. This software is for educational purposes. You are responsible for all trading decisions and outcomes.**

- No guarantees of profit
- Can lose your entire investment
- Test extensively before using real money
- Never invest more than you can afford to lose

---

## 🚀 Getting Started Right Now

**For Python Solana Bot (Recommended):**
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set TEST_MODE=true, SIMULATE_TRADES=true
./run_bot.sh
```

**For TypeScript Telegram Bot:**
```bash
npm install
echo "TELEGRAM_BOT_TOKEN=your_token" > .env
npm run build
npm start
```

---

## 💡 Pro Tips

1. **Start simple** - Use Conservative strategy (1) first
2. **Learn gradually** - Understand one feature at a time
3. **Read the logs** - They tell you everything that's happening
4. **Test strategies** - Compare all 5 to find your best
5. **Stay safe** - Simulation → Devnet → Small mainnet → Scale up

---

## 🆘 Need Help?

1. Check the logs in `logs/` directory
2. Review your `.env` configuration
3. Read the full documentation (README_PYTHON_BOT.md)
4. Verify your RPC connection
5. Start fresh with simulation mode

---

**Happy Trading! 📈**

Remember: Start safe, test thoroughly, and never risk more than you can afford to lose.
