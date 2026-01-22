import { UserStats, Trade, Position } from '../types';
import { config } from '../config';

class StatsTracker {
  private stats: Map<number, UserStats> = new Map();

  getUserStats(userId: number): UserStats {
    if (!this.stats.has(userId)) {
      this.stats.set(userId, {
        userId,
        balance: config.initialBalance,
        totalTrades: 0,
        successfulTrades: 0,
        failedTrades: 0,
        totalProfit: 0,
        totalFees: 0,
        winRate: 0,
        activePositions: [],
        tradeHistory: [],
      });
    }
    return this.stats.get(userId)!;
  }

  addTrade(userId: number, trade: Trade): void {
    const stats = this.getUserStats(userId);

    stats.tradeHistory.unshift(trade);
    if (stats.tradeHistory.length > 50) {
      stats.tradeHistory = stats.tradeHistory.slice(0, 50);
    }

    stats.totalTrades++;
    stats.totalFees += trade.gasFee;

    if (trade.status === 'completed') {
      stats.successfulTrades++;

      if (trade.type === 'buy') {
        // Add new position
        const existingPos = stats.activePositions.find(p => p.tokenAddress === trade.tokenAddress);
        if (existingPos) {
          // Average down
          const totalAmount = existingPos.amount + trade.amount;
          existingPos.entryPrice = (existingPos.entryPrice * existingPos.amount + trade.price * trade.amount) / totalAmount;
          existingPos.amount = totalAmount;
        } else {
          stats.activePositions.push({
            tokenAddress: trade.tokenAddress,
            tokenSymbol: trade.tokenSymbol,
            amount: trade.amount,
            entryPrice: trade.price,
            currentPrice: trade.price,
            unrealizedPnL: 0,
            entryTime: trade.timestamp,
          });
        }
        stats.balance -= trade.totalCost;
      } else if (trade.type === 'sell') {
        // Remove or reduce position
        const posIndex = stats.activePositions.findIndex(p => p.tokenAddress === trade.tokenAddress);
        if (posIndex !== -1) {
          const position = stats.activePositions[posIndex];
          const profit = (trade.price - position.entryPrice) * trade.amount;
          stats.totalProfit += profit;

          if (trade.amount >= position.amount) {
            stats.activePositions.splice(posIndex, 1);
          } else {
            position.amount -= trade.amount;
          }
        }
        stats.balance += trade.totalCost;
      }
    } else if (trade.status === 'failed') {
      stats.failedTrades++;
      // Still deduct gas fee for failed transactions
      stats.balance -= trade.gasFee;
    }

    stats.winRate = stats.totalTrades > 0 ? (stats.successfulTrades / stats.totalTrades) * 100 : 0;
  }

  updatePositionPrices(userId: number, tokenAddress: string, newPrice: number): void {
    const stats = this.getUserStats(userId);
    const position = stats.activePositions.find(p => p.tokenAddress === tokenAddress);

    if (position) {
      position.currentPrice = newPrice;
      position.unrealizedPnL = (newPrice - position.entryPrice) * position.amount;
    }
  }

  resetStats(userId: number): void {
    this.stats.set(userId, {
      userId,
      balance: config.initialBalance,
      totalTrades: 0,
      successfulTrades: 0,
      failedTrades: 0,
      totalProfit: 0,
      totalFees: 0,
      winRate: 0,
      activePositions: [],
      tradeHistory: [],
    });
  }
}

export const statsTracker = new StatsTracker();
