import { MempoolTransaction, Trade } from '../types';
import { config, ETH_PRICE_USD, EUR_USD_RATE, DEMO_TOKENS } from '../config';
import { calculateGasFee, ethToEur } from '../utils/formatting';
import { statsTracker } from '../stats/tracker';

export class MEVSniper {
  private userId: number;

  constructor(userId: number) {
    this.userId = userId;
  }

  async analyzeAndSnipe(tx: MempoolTransaction): Promise<{ shouldSnipe: boolean; reason: string }> {
    // MEV Sniping Strategy:
    // 1. Check if transaction is a buy (we want to copy buys)
    // 2. Ensure it's a significant amount (filter out small trades)
    // 3. Calculate if we can profit after fees

    if (tx.type !== 'swap') {
      return { shouldSnipe: false, reason: 'Not a swap transaction' };
    }

    const stats = statsTracker.getUserStats(this.userId);

    // Check if we have enough balance
    if (stats.balance < 1) {
      return { shouldSnipe: false, reason: 'Insufficient balance' };
    }

    // Only snipe buys (ETH -> Token)
    const isBuy = tx.tokenIn === 'ETH';
    if (!isBuy) {
      return { shouldSnipe: false, reason: 'Not a buy transaction' };
    }

    // Check transaction size - only copy significant trades
    const txValueEth = parseFloat(tx.amountIn || '0');
    if (txValueEth < 0.5) {
      return { shouldSnipe: false, reason: 'Transaction too small' };
    }

    // Random chance to simulate successful sniping (70% success rate)
    const willSucceed = Math.random() > 0.3;

    return {
      shouldSnipe: true,
      reason: willSucceed ? 'Good opportunity detected' : 'Competition too high'
    };
  }

  async executeTrade(tx: MempoolTransaction): Promise<Trade> {
    const stats = statsTracker.getUserStats(this.userId);
    const token = DEMO_TOKENS.find(t => t.symbol === tx.tokenOut) || DEMO_TOKENS[0];

    // Calculate trade size (proportional to balance, 10-30% of balance)
    const tradePercentage = 0.1 + Math.random() * 0.2;
    const tradeAmountEur = Math.min(stats.balance * tradePercentage, stats.balance - 1);

    // Calculate gas fee
    // Sniping after the target transaction = lower priority gas
    const baseGas = parseFloat(tx.gasPrice);
    const ourGasPrice = baseGas + 1; // Just 1 gwei above to save on fees
    const gasUsed = config.gasLimit * (0.6 + Math.random() * 0.2); // 60-80% of limit
    const gasFeeEth = calculateGasFee(gasUsed, ourGasPrice);
    const gasFeeEur = ethToEur(gasFeeEth, ETH_PRICE_USD, EUR_USD_RATE);

    // Calculate slippage (0.1-0.5%)
    const slippage = 0.001 + Math.random() * 0.004;
    const effectiveTradeAmount = tradeAmountEur - gasFeeEur;
    const tokensReceived = (effectiveTradeAmount * (1 - slippage)) / token.price;

    // Determine if trade succeeds or fails
    const analysis = await this.analyzeAndSnipe(tx);
    const status = analysis.reason === 'Good opportunity detected' ? 'completed' : 'failed';

    const trade: Trade = {
      id: Math.random().toString(36).substring(7),
      timestamp: Date.now(),
      type: 'buy',
      tokenAddress: token.address,
      tokenSymbol: token.symbol,
      amount: status === 'completed' ? tokensReceived : 0,
      price: token.price,
      gasUsed: gasUsed,
      gasFee: gasFeeEur,
      totalCost: status === 'completed' ? tradeAmountEur : gasFeeEur,
      status: status,
    };

    statsTracker.addTrade(this.userId, trade);

    return trade;
  }

  async sellPosition(tokenAddress: string, percentage: number = 100): Promise<Trade | null> {
    const stats = statsTracker.getUserStats(this.userId);
    const position = stats.activePositions.find(p => p.tokenAddress === tokenAddress);

    if (!position) {
      return null;
    }

    const sellAmount = position.amount * (percentage / 100);

    // Simulate price movement (-5% to +15%)
    const priceChange = -0.05 + Math.random() * 0.2;
    const currentPrice = position.entryPrice * (1 + priceChange);

    // Calculate gas fee for sell
    const gasPrice = config.minGasPrice + Math.random() * (config.maxGasPrice - config.minGasPrice);
    const gasUsed = config.gasLimit * 0.7;
    const gasFeeEth = calculateGasFee(gasUsed, gasPrice);
    const gasFeeEur = ethToEur(gasFeeEth, ETH_PRICE_USD, EUR_USD_RATE);

    const sellValueEur = sellAmount * currentPrice;
    const netValue = sellValueEur - gasFeeEur;

    const trade: Trade = {
      id: Math.random().toString(36).substring(7),
      timestamp: Date.now(),
      type: 'sell',
      tokenAddress: position.tokenAddress,
      tokenSymbol: position.tokenSymbol,
      amount: sellAmount,
      price: currentPrice,
      gasUsed: gasUsed,
      gasFee: gasFeeEur,
      totalCost: netValue,
      profit: (currentPrice - position.entryPrice) * sellAmount,
      status: 'completed',
    };

    statsTracker.addTrade(this.userId, trade);

    return trade;
  }
}
