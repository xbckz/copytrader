# MEV Protection Checker for Solana

A tool to detect if a Solana address is using MEV (Maximal Extractable Value) protection services like Jito's Block Engine or other private RPC endpoints.

## What is MEV Protection?

MEV protection on Solana refers to services that help users avoid frontrunning, sandwich attacks, and other forms of MEV extraction by:

- Submitting transactions through private RPCs (e.g., Jito Block Engine)
- Bypassing the public mempool/transaction pool
- Sending transactions directly to validators
- Preventing transaction visibility before execution

## How It Works

This tool monitors a Solana address and analyzes transaction patterns to detect MEV protection:

1. **Mempool Monitoring**: Checks if transactions appear as pending before confirmation
2. **Block Analysis**: Detects transactions that appear directly in blocks
3. **Pattern Recognition**: Calculates the percentage of MEV-protected vs public transactions

### Detection Logic

- **MEV Protected**: Transactions that appear directly in confirmed blocks without being seen in the mempool first
- **Public Mempool**: Transactions that were visible as pending before confirmation

## Installation

Ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

Required packages:
- `solana>=0.30.0`
- `solders>=0.18.0`

## Usage

### Basic Usage

Run the script:

```bash
python mev_protection_checker.py
```

The tool will prompt you for:
1. **Solana address** to monitor
2. **RPC endpoint** (optional, defaults to mainnet)

### Example Session

```
Enter Solana address to monitor: DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK

RPC endpoint (press Enter for mainnet default):
  https://api.mainnet-beta.solana.com >

✓ Connected to Solana RPC
  Solana version: 1.18.x

✓ Monitoring address: DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK
  Check interval: 2.0s
  Waiting for transactions...

[12:34:56] Monitoring... (checked 10 times)

  🔒 MEV PROTECTED transaction detected:
    Signature: 5J7zN...
    Slot: 245123456
    Status: Transaction appeared directly in block (likely Jito/private RPC)

  📊 Statistics:
    Total transactions: 1
    MEV Protected: 1 (100.0%)
    Public Mempool: 0 (0.0%)
    ✓ This address is likely using MEV protection
```

### Custom RPC Endpoint

You can use a custom RPC endpoint (useful for devnet/testnet or premium RPC providers):

```bash
python mev_protection_checker.py
```

When prompted, enter your custom RPC:
```
RPC endpoint (press Enter for mainnet default):
  https://api.mainnet-beta.solana.com > https://your-custom-rpc.com
```

## Understanding Results

### Statistics Breakdown

The tool provides real-time statistics:

- **Total transactions**: Number of transactions analyzed
- **MEV Protected**: Transactions that bypassed public mempool
- **Public Mempool**: Transactions visible before confirmation

### Conclusion Categories

Based on the MEV protection percentage:

| Percentage | Category | Meaning |
|------------|----------|---------|
| ≥80% | CONSISTENTLY using | Address primarily uses MEV protection |
| 50-79% | FREQUENTLY using | Mixed usage pattern, mostly protected |
| 20-49% | OCCASIONALLY using | Inconsistent MEV protection usage |
| <20% | NOT using | Primarily public mempool transactions |

## Examples

### Example 1: MEV Protected Address (Jito User)

```
FINAL REPORT
======================================================================

Total Transactions Analyzed: 10

Transaction Breakdown:
  🔒 MEV Protected:  9 (90.0%)
  📋 Public Mempool: 1 (10.0%)

Conclusion:
  ✓ This address is CONSISTENTLY using MEV protection
    Likely using Jito Block Engine or similar private RPC
```

### Example 2: Public Mempool Address

```
FINAL REPORT
======================================================================

Total Transactions Analyzed: 15

Transaction Breakdown:
  🔒 MEV Protected:  2 (13.3%)
  📋 Public Mempool: 13 (86.7%)

Conclusion:
  ✗ This address is NOT using MEV protection
    Transactions are primarily visible in public mempool
```

## Technical Details

### Monitoring Process

1. **Connection**: Establishes connection to Solana RPC
2. **Validation**: Validates the provided address
3. **Polling Loop**: Every 2 seconds:
   - Checks for pending transactions (mempool)
   - Checks for confirmed transactions (blocks)
   - Compares patterns to detect MEV protection

### Limitations

- **Solana Mempool**: Solana doesn't have a traditional mempool like Ethereum. Detection is based on transaction visibility timing.
- **RPC Limitations**: Some RPC providers may not expose pending transactions, which could affect detection accuracy.
- **Sample Size**: More transactions = more accurate detection. Monitor for longer periods for better results.
- **Network Conditions**: High network load may affect pending transaction visibility.

### Best Practices

1. **Monitor for Extended Periods**: Let it run for multiple transactions (ideally 10+)
2. **Use Mainnet**: MEV protection is primarily used on mainnet
3. **Active Addresses**: Monitor addresses that are actively trading
4. **Premium RPC**: Use a quality RPC endpoint for better pending transaction visibility

## Use Cases

### Trading Analysis
Analyze if successful traders are using MEV protection to gain advantages.

### Bot Detection
Identify if competing bots are using private transaction submission.

### Security Research
Study MEV protection adoption patterns on Solana.

### Wallet Monitoring
Track if your own wallet's MEV protection setup is working correctly.

## Troubleshooting

### No Transactions Detected

- Ensure the address is active and making transactions
- Try a different RPC endpoint
- Verify the address is correct

### Connection Errors

- Check your internet connection
- Verify RPC endpoint is accessible
- Try using the default mainnet RPC

### High False Positives

- Use a premium RPC with better mempool visibility
- Monitor for longer periods
- Consider network congestion factors

## Stop Monitoring

Press `Ctrl+C` to stop monitoring and see the final report.

## Advanced Configuration

You can modify the script to adjust:

- `check_interval`: Polling frequency (default: 2.0 seconds)
- `limit`: Number of recent signatures to fetch (default: 10-20)
- RPC endpoints for different networks

## Contributing

Feel free to enhance the tool with:
- WebSocket support for real-time monitoring
- Multiple address monitoring
- Historical analysis mode
- Export to CSV/JSON

## License

Part of the Solana Copy Trading Bot project.

## Disclaimer

This tool is for informational and research purposes. Detection accuracy depends on RPC provider capabilities and network conditions. Results should be interpreted as probabilistic rather than definitive.
