# Quick Start Guide - Solana Copy Trading Bot

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (1 min)

```bash
cd /home/user/copytrader
pip install -r requirements.txt
```

Or use the automated runner:
```bash
./run_bot.sh  # Will auto-install dependencies
```

### Step 2: Configure Environment (2 min)

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

**Minimal configuration for testing:**
```bash
# Use devnet for safe testing
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_NETWORK=devnet

# Testing mode
TEST_MODE=true
USE_DEVNET=true
SIMULATE_TRADES=true  # No real trades, just simulation

# Strategy to use (1-5, or 'all' for comparison)
ACTIVE_STRATEGY=1

# Optional: Leave wallet keys empty for simulation mode
WALLET_PRIVATE_KEY=
WALLET_PUBLIC_KEY=
```

### Step 3: Run the Bot (1 min)

```bash
# Option 1: Use the runner script (recommended)
./run_bot.sh

# Option 2: Run directly
python -m python_bot.main
```

### Step 4: Monitor Output (1 min)

You should see:
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
INFO - Wallet tracker initialized with 100 wallets
INFO - Starting copy trading bot...
INFO - BOT STARTED - Monitoring for trades
================================================================================
```

**Success!** The bot is now:
- ✅ Connected to Solana devnet
- ✅ Monitoring top 100 wallets
- ✅ Ready to simulate copy trading
- ✅ Using Strategy 1 (Conservative: TP 10%, SL 5%)

---

## 📊 Understanding the 5 Strategies

When you see the bot running, it uses one of these strategies:

| Strategy | TP% | SL% | Best For |
|----------|-----|-----|----------|
| 1. Conservative | 10% | 5% | Safe, steady gains |
| 2. Balanced | 20% | 10% | Medium risk/reward |
| 3. Aggressive | 50% | 15% | High risk/reward |
| 4. Scalper | 5% | 3% | Quick small profits |
| 5. HODL | 100% | 25% | Long-term holds |

**To test all strategies at once:**
```bash
# In .env, set:
ACTIVE_STRATEGY=all
```

This runs all 5 strategies in parallel so you can compare performance!

---

## 🎯 What Happens Next?

### In Simulation Mode (Default)

The bot will:
1. Monitor top 100 KOL wallets
2. Detect when they make trades
3. **Simulate** copying their trades (no real execution)
4. Track positions with TP/SL
5. Show you PnL as if you had traded

**Safe for testing!** No real funds at risk.

### What You'll See

```
INFO - Found 1 new transaction(s) for WALLET001...
INFO - Detected buy from WALLET001: 0.5 SOL -> TOKEN123...
INFO - Copying trade: 0.15 SOL -> TOKEN123...
INFO - SIMULATION MODE - Trade not executed
INFO - Position opened: abc123... Entry: $0.00012345, TP: $0.00013579, SL: $0.00011728
```

Every minute, you'll see status updates:
```
==================================================================================================
BOT STATUS
==================================================================================================
Tracked Wallets: 100
Avg Win Rate: 72.50%

--- Strategy 1: Conservative ---
Balance: 99.8500 SOL
Portfolio Value: 100.1234 SOL
Total PnL: 0.1234 SOL (0.12%)
Open Positions: 2
Total Trades: 5
Win Rate: 60.00%
==================================================================================================
```

---

## 🧪 Testing Progression

### Phase 1: Simulation (START HERE)
```bash
# .env settings:
TEST_MODE=true
SIMULATE_TRADES=true
```
- ✅ Safe - no real trades
- ✅ Learn how the bot works
- ✅ See position management
- ✅ Understand TP/SL logic

### Phase 2: Devnet Testing
```bash
# Get free devnet SOL first:
solana airdrop 2 YOUR_ADDRESS --url devnet

# .env settings:
TEST_MODE=true
SIMULATE_TRADES=false  # Real execution on devnet
USE_DEVNET=true
```
- ✅ Real transactions on test network
- ✅ No real money at risk
- ✅ Test full execution flow
- ✅ Verify everything works

### Phase 3: Strategy Comparison
```bash
# .env settings:
ACTIVE_STRATEGY=all  # Run all 5 strategies
SIMULATE_TRADES=true  # Keep it safe
```
- ✅ Compare all strategies
- ✅ Find best performer
- ✅ Optimize settings
- ✅ Make data-driven decisions

### Phase 4: Mainnet (ADVANCED - BE CAREFUL!)
```bash
# .env settings:
SOLANA_NETWORK=mainnet-beta
TEST_MODE=false
SIMULATE_TRADES=false
INITIAL_BALANCE=0.1  # START SMALL!
```
- ⚠️ ONLY after extensive testing
- ⚠️ Start with tiny amounts
- ⚠️ Monitor constantly
- ⚠️ Understand the risks

---

## 📝 Logs and Monitoring

### Check Logs
```bash
# View latest log
tail -f logs/copytrader_*.log

# Search for errors
grep ERROR logs/copytrader_*.log

# View all trades
grep "Position opened" logs/copytrader_*.log
```

### Check Database
```bash
# View all positions
sqlite3 copytrader.db "SELECT * FROM positions;"

# View recent trades
sqlite3 copytrader.db "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;"
```

---

## 🛑 Stopping the Bot

Press `Ctrl+C` to gracefully stop the bot. It will:
1. Close all monitoring connections
2. Save final state to database
3. Print final statistics
4. Exit cleanly

---

## ❓ Troubleshooting

### Bot won't start
```bash
# Check Python version (need 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### No trades detected
- This is normal in simulation mode
- KOLscan API may not be available (uses fallback)
- Transaction parsing is a placeholder (needs implementation for production)

### Connection errors
```bash
# Try different RPC endpoint
# In .env:
SOLANA_RPC_URL=https://api.devnet.solana.com
```

---

## 🎓 Next Steps

1. **Learn the basics** - Run in simulation mode
2. **Test on devnet** - Use free test SOL
3. **Compare strategies** - Find what works best
4. **Read full docs** - Check README_PYTHON_BOT.md
5. **Customize** - Adjust strategies in `python_bot/config/strategies.py`
6. **Scale carefully** - Only go to mainnet after thorough testing

---

## 💡 Pro Tips

1. **Start with simulation** - Always test first
2. **Monitor closely** - Watch logs and status
3. **Small positions** - Limit risk per trade
4. **Test all strategies** - Find your best performer
5. **Read the code** - Understand what it's doing
6. **Keep learning** - Crypto is complex and risky

---

## 📚 More Information

- **Full Documentation**: `README_PYTHON_BOT.md`
- **Strategy Details**: `python_bot/config/strategies.py`
- **Settings Reference**: `.env.example`
- **Code Structure**: `README_PYTHON_BOT.md` (Architecture section)

---

## ⚠️ Important Reminder

**This is educational software for learning about copy trading and automated strategies.**

- Start with simulation mode
- Test extensively on devnet
- Understand all risks
- Never invest more than you can afford to lose
- Crypto trading is highly risky
- No guarantees of profit

---

**Ready to get started?** Run `./run_bot.sh` and watch the magic happen! 🚀

Questions? Check the logs, review the code, or read the full documentation.

Happy (safe) trading! 📈
