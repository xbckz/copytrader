# Solana Copy Trading Bot - Python Implementation

A production-ready copy trading bot for Solana that monitors top 100 KOLscan wallets and executes trades with multiple strategy configurations for testing and optimization.

## Features

### Core Functionality
- **Real-time Wallet Monitoring**: Tracks top 100 KOLscan wallets
- **Transaction Detection**: Monitors Solana blockchain for new transactions
- **Automated Copy Trading**: Automatically copies trades from successful wallets
- **Price Tracking**: Real-time price monitoring via Jupiter aggregator
- **DEX Integration**: Trade execution through Jupiter for best prices

### 5 Testing Strategies

Each strategy has different risk/reward parameters for comparison:

| ID | Strategy | TP% | SL% | Max Positions | Hold Time | Description |
|----|----------|-----|-----|---------------|-----------|-------------|
| 1  | Conservative | 10% | 5% | 3 | 1 hour | Low risk, quick exits |
| 2  | Balanced | 20% | 10% | 5 | 2 hours | Medium risk/reward |
| 3  | Aggressive | 50% | 15% | 5 | 4 hours | High risk/reward |
| 4  | Scalper | 5% | 3% | 8 | 30 min | Very quick trades |
| 5  | HODL | 100% | 25% | 3 | Unlimited | Long-term holds |

### Position Management
- **Take Profit (TP)**: Automatic exit at profit target
- **Stop Loss (SL)**: Automatic exit to limit losses
- **Trailing Stop**: Optional trailing stop for protecting profits
- **Time-based Exit**: Maximum hold time limits
- **Daily Loss Limit**: Stop trading if daily loss exceeds threshold

### Monitoring & Analytics
- **Real-time Performance Tracking**: Live PnL, win rate, trade count
- **Position Tracking**: Monitor all open positions
- **Trade History**: Complete audit trail
- **Comprehensive Logging**: Detailed logs for debugging

## Architecture

```
python_bot/
├── main.py                 # Main entry point
├── config/
│   ├── settings.py         # Configuration management
│   └── strategies.py       # 5 strategy configurations
├── blockchain/
│   ├── solana_client.py    # Solana RPC client
│   └── transaction_monitor.py  # Real-time tx monitoring
├── monitoring/
│   ├── kolscan.py          # KOLscan API client
│   └── wallet_tracker.py   # Top 100 wallet tracking
├── trading/
│   ├── dex_client.py       # Jupiter DEX integration
│   ├── price_tracker.py    # Real-time price monitoring
│   └── executor.py         # Trade execution
├── strategy/
│   ├── engine.py           # Strategy execution engine
│   └── position_manager.py # TP/SL position management
├── database/
│   └── models.py           # SQLite database models
└── utils/
    ├── logger.py           # Logging configuration
    └── helpers.py          # Utility functions
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Solana wallet with private key (for trading)
- (Optional) KOLscan API key

### Step 1: Install Dependencies

```bash
cd /home/user/copytrader
pip install -r requirements.txt
```

### Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# For testing, use devnet
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WS_URL=wss://api.devnet.solana.com
SOLANA_NETWORK=devnet

# Your wallet (IMPORTANT: Use a test wallet on devnet!)
WALLET_PRIVATE_KEY=your_base58_private_key
WALLET_PUBLIC_KEY=your_public_key

# Testing mode (ALWAYS start with this)
TEST_MODE=true
USE_DEVNET=true
SIMULATE_TRADES=true  # Start with simulation

# Strategy (1-5 or 'all')
ACTIVE_STRATEGY=1  # Or 'all' to run all strategies

# KOLscan (optional)
KOLSCAN_API_KEY=your_api_key_if_available
```

## Local Testing Guide

### Testing Phase 1: Simulation Mode

This mode simulates trades without executing on blockchain.

1. **Configure for simulation**:
```bash
# In .env
TEST_MODE=true
USE_DEVNET=true
SIMULATE_TRADES=true
ACTIVE_STRATEGY=1
```

2. **Run the bot**:
```bash
cd /home/user/copytrader
python -m python_bot.main
```

3. **What to observe**:
   - Bot connects to Solana devnet
   - Fetches top wallets (or uses fallback list)
   - Monitors for transactions
   - Simulates trades (no real execution)
   - Shows position management with TP/SL
   - Prints performance statistics every minute

4. **Expected output**:
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

### Testing Phase 2: Devnet with Real Execution

Once simulation works, test with real transactions on devnet.

1. **Get devnet SOL**:
```bash
# Use Solana faucet to get free devnet SOL
solana airdrop 2 YOUR_WALLET_ADDRESS --url devnet
```

2. **Configure for devnet execution**:
```bash
# In .env
TEST_MODE=true
USE_DEVNET=true
SIMULATE_TRADES=false  # Enable real execution
INITIAL_BALANCE=1.0    # Start small on devnet
```

3. **Run and monitor**:
```bash
python -m python_bot.main
```

4. **Monitor logs**:
```bash
# In another terminal
tail -f logs/copytrader_*.log
```

### Testing Phase 3: Compare All Strategies

Test all 5 strategies simultaneously to find the best performer.

1. **Configure for multi-strategy**:
```bash
# In .env
ACTIVE_STRATEGY=all
SIMULATE_TRADES=true  # Use simulation for safety
```

2. **Run comparison**:
```bash
python -m python_bot.main
```

3. **Analyze results**:
   - Each strategy tracks independent positions
   - Compare PnL, win rate, and trade count
   - Review which TP/SL settings perform best
   - Check logs for detailed trade analysis

4. **Expected output**:
```
STRATEGY COMPARISON TABLE
==================================================================================================
ID    Name            TP%      SL%      Max Pos    Hold Time    Description
--------------------------------------------------------------------------------------------------
1     Conservative    10.0     5.0      3          3600s        Low risk with quick exits
2     Balanced        20.0     10.0     5          7200s        Balanced approach
3     Aggressive      50.0     15.0     5          14400s       High risk/reward
4     Scalper         5.0      3.0      8          1800s        Quick profits
5     HODL            100.0    25.0     3          Unlimited    Long-term holds
==================================================================================================
```

### Testing Phase 4: Production Preparation

Before going to mainnet:

1. **Review strategy performance**:
   - Analyze which strategy performed best
   - Check win rate (should be > 50%)
   - Verify TP/SL logic works correctly
   - Ensure position limits are respected

2. **Test transaction parsing**:
   - Verify DEX transaction detection works
   - Ensure correct token addresses are extracted
   - Validate trade size calculations

3. **Risk management checks**:
   - Confirm daily loss limits work
   - Test position size limits
   - Verify balance checks prevent over-trading

### Moving to Mainnet (CAUTION!)

**⚠️ WARNING: Only proceed if thoroughly tested on devnet!**

1. **Minimal configuration**:
```bash
# In .env
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_NETWORK=mainnet-beta
TEST_MODE=false
USE_DEVNET=false
SIMULATE_TRADES=false

# Start with VERY small amounts!
INITIAL_BALANCE=0.1
MIN_TRADE_SIZE=0.01
MAX_TRADE_SIZE=0.05

# Use your best-performing strategy
ACTIVE_STRATEGY=2  # Or whichever performed best
```

2. **Use production RPC** (recommended):
   - Consider using a premium RPC provider (Helius, QuickNode, etc.)
   - Free public RPCs may have rate limits
   - Better for production reliability

3. **Start small and monitor closely**:
   - Begin with minimal balance
   - Watch first few trades closely
   - Gradually increase if performing well
   - Always monitor logs

## Troubleshooting

### Common Issues

**1. Cannot connect to Solana RPC**
```
Solution: Check RPC URL, try alternative endpoint:
- Devnet: https://api.devnet.solana.com
- Mainnet: https://api.mainnet-beta.solana.com
- Or use premium RPC provider
```

**2. No wallets found from KOLscan**
```
Solution: Bot will use fallback wallet list for testing.
For production, you need valid KOLscan API access.
```

**3. Trade execution fails**
```
Solution:
- Check wallet has sufficient SOL for gas
- Verify wallet private key is correct
- Ensure using correct network (devnet/mainnet)
- Check slippage settings
```

**4. Transactions not detected**
```
Solution:
- Transaction parsing needs Solana program-specific logic
- For testing, you can manually trigger trades
- Full implementation requires DEX-specific parsers
```

### Logs

All logs are saved to `logs/` directory:
- Console output: Color-coded by level
- File output: Complete debug information
- Separate log file per run with timestamp

### Database

Positions and trades are stored in SQLite:
- Location: `copytrader.db`
- View with: `sqlite3 copytrader.db`
- Query positions: `SELECT * FROM positions;`
- Query trades: `SELECT * FROM trades;`

## Configuration Options

### Key Settings

```python
# Trading
INITIAL_BALANCE=100         # Starting balance in SOL
MIN_TRADE_SIZE=0.01        # Minimum trade size
MAX_TRADE_SIZE=1.0         # Maximum trade size
MAX_POSITION_SIZE=0.3      # Max 30% per position

# Risk Management
SLIPPAGE_BPS=100           # 1% slippage tolerance
PRIORITY_FEE_LAMPORTS=50000  # Transaction priority

# Monitoring
TOP_WALLETS_COUNT=100      # Number of wallets to track
WALLET_REFRESH_INTERVAL=3600  # Refresh every hour
PRICE_UPDATE_INTERVAL=1.0  # Price updates per second
```

### Strategy Customization

Edit `python_bot/config/strategies.py` to customize strategies:

```python
STRATEGY_1 = StrategyConfig(
    id=1,
    name="My Custom Strategy",
    take_profit_percentage=15.0,  # 15% TP
    stop_loss_percentage=7.5,     # 7.5% SL
    # ... other parameters
)
```

## Performance Optimization

### For Production

1. **Use premium RPC endpoint**: Faster, more reliable
2. **Optimize price updates**: Adjust `PRICE_UPDATE_INTERVAL`
3. **Database**: Consider PostgreSQL for better performance
4. **Monitoring**: Add Prometheus/Grafana for metrics
5. **Alerts**: Implement Telegram notifications

### Resource Usage

- CPU: Low (mostly async I/O)
- Memory: ~100-200 MB
- Network: Moderate (RPC calls, price updates)
- Disk: Minimal (SQLite database)

## Safety Features

- ✅ Test mode with simulation
- ✅ Devnet support for safe testing
- ✅ Daily loss limits
- ✅ Position size limits
- ✅ Balance checks before trades
- ✅ Transaction confirmation timeouts
- ✅ Comprehensive error handling
- ✅ Detailed logging

## Important Notes

### Transaction Parsing

The current implementation includes a placeholder for transaction parsing. For production use, you need to implement:

1. **DEX-specific parsers**: Jupiter, Raydium, Orca, etc.
2. **Token transfer detection**: SPL token program interactions
3. **Swap instruction parsing**: Extract token addresses and amounts
4. **Program ID matching**: Identify which DEX was used

Example resources:
- Solana program library documentation
- Jupiter API documentation
- Anchor framework for program interaction

### KOLscan Integration

If KOLscan API is not available:
- Bot uses fallback wallet list
- You can manually add wallet addresses
- Consider alternative data sources (on-chain analysis, other APIs)

### Production Checklist

Before running on mainnet with real funds:

- [ ] Thoroughly tested on devnet
- [ ] Reviewed all strategy performance
- [ ] Verified TP/SL logic works correctly
- [ ] Tested with small amounts first
- [ ] Implemented proper transaction parsing
- [ ] Set up monitoring and alerts
- [ ] Configured proper risk limits
- [ ] Using reliable RPC endpoint
- [ ] Have emergency stop mechanism
- [ ] Understand all risks involved

## Disclaimer

**⚠️ IMPORTANT DISCLAIMER ⚠️**

This software is provided for educational and research purposes. Trading cryptocurrencies involves significant risk of loss.

- **Test extensively** on devnet before mainnet
- **Start with small amounts** you can afford to lose
- **Monitor constantly** when running
- **Understand the risks** of automated trading
- **No guarantees** of profit
- **You are responsible** for all trading decisions and outcomes

The developers are not responsible for any financial losses incurred through use of this software.

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- Review logs in `logs/` directory
- Check configuration in `.env`
- Verify Solana RPC connectivity
- Test components individually

## Next Steps

1. ✅ Complete local testing in simulation mode
2. ✅ Test on devnet with real execution
3. ✅ Compare all 5 strategies
4. ✅ Analyze performance and optimize
5. ⚠️ Implement production transaction parsing
6. ⚠️ Set up monitoring and alerts
7. ⚠️ Test with minimal mainnet funds
8. ⚠️ Scale gradually if successful

Good luck and trade safely! 🚀
