# Telegram Crypto Copy Trader Bot

A demo MEV sniping bot for Telegram that simulates copy trading with realistic fees and market conditions.

## Features

- 🎯 **MEV Mempool Sniping**: Monitors mempool for large buy transactions
- 💰 **Low Fee Strategy**: Uses Target + 1 gwei to minimize costs
- 📊 **Real-time Statistics**: Track balance, positions, P&L, and win rate
- 💼 **Position Management**: View and sell positions with profit tracking
- 📈 **Trade History**: Complete history of all executed trades
- ⚡ **Realistic Simulation**: Includes gas fees, slippage, and market dynamics

## Demo Mode

This is a **demonstration version** that simulates trading:
- Starting balance: €20
- All trades are simulated (no real funds)
- Realistic gas fees for small amounts
- Market slippage (0.1-0.5%)
- Success rate simulation (70%)

## Quick Start

### Installation

```bash
npm install
```

### Build

```bash
npm run build
```

### Run

```bash
npm start
```

Or for development with auto-reload:

```bash
npm run dev
```

## Bot Commands

- `/start` - Initialize the bot and show main menu
- `/reset` - Reset statistics and balance to €20
- `/help` - Show help and documentation

## Menu Options

### 📊 Dashboard
View comprehensive statistics:
- Current balance and portfolio value
- Total trades and win rate
- Realized and unrealized P&L
- Total fees paid

### 🎯 Start/Stop Sniping
- **Start**: Begin monitoring mempool for opportunities
- **Stop**: Pause trading activity

### 💼 Positions
- View all active positions
- See entry price, current price, and P&L
- Sell 50% or 100% of any position

### 📈 Trade History
View the last 10 trades with:
- Buy/Sell type
- Token and amount
- Gas fees paid
- Profit/loss (for sells)

### ⚙️ Settings
- View bot configuration
- Reset statistics
- Check demo mode status

## How It Works

### MEV Sniping Strategy

1. **Mempool Monitoring**: Bot watches for large buy transactions (>0.5 ETH)
2. **Analysis**: Evaluates if the opportunity is profitable after fees
3. **Execution**: Places order after target transaction (saves gas)
4. **Tracking**: Records position with entry price and fees

### Fee Calculation

- **Gas Fee**: Realistic calculation based on gas price and usage
- **Slippage**: Random 0.1-0.5% to simulate market impact
- **Network Conditions**: Variable gas prices (10-50 gwei)

### Trade Execution

The bot automatically:
- Calculates optimal trade size (10-30% of balance)
- Uses low gas strategy (Target + 1 gwei)
- Simulates success/failure based on market conditions
- Updates positions and statistics in real-time

## Demo Tokens

The simulation includes popular tokens:
- PEPE
- SHIB
- DOGE
- FLOKI

## Technical Details

### Technology Stack
- **Language**: TypeScript
- **Bot Framework**: node-telegram-bot-api
- **Blockchain**: ethers.js (for types and utilities)

### Project Structure
```
src/
├── index.ts              # Entry point
├── bot.ts                # Main bot logic
├── menu.ts               # Menu system and UI
├── config.ts             # Configuration
├── types.ts              # TypeScript types
├── stats/
│   └── tracker.ts        # Statistics tracking
├── trading/
│   ├── mempool.ts        # Mempool simulation
│   └── mev.ts            # MEV sniping logic
└── utils/
    └── formatting.ts     # Formatting utilities
```

## Safety Features

- Demo mode only (no real trading)
- Balance checks before trades
- Automatic stop when balance < €1
- Failed trade handling (only gas fee deducted)

## Future Enhancements

For a production version, consider adding:
- Real blockchain integration
- Multiple DEX support
- Custom gas strategies
- Advanced analytics
- Trade alerts and notifications
- Position take-profit/stop-loss
- Multiple wallet support

## License

MIT

## Disclaimer

This is a demonstration bot for educational purposes only. No real trading or cryptocurrency transactions occur. Always conduct thorough research and use caution when dealing with real cryptocurrency trading.
