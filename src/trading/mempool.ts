import { MempoolTransaction } from '../types';
import { DEMO_TOKENS } from '../config';

class MempoolMonitor {
  private listeners: Map<number, (tx: MempoolTransaction) => void> = new Map();
  private isMonitoring: boolean = false;
  private monitoringInterval?: NodeJS.Timeout;

  startMonitoring(userId: number, callback: (tx: MempoolTransaction) => void): void {
    this.listeners.set(userId, callback);

    if (!this.isMonitoring) {
      this.isMonitoring = true;
      this.simulateMempoolActivity();
    }
  }

  stopMonitoring(userId: number): void {
    this.listeners.delete(userId);

    if (this.listeners.size === 0) {
      this.isMonitoring = false;
      if (this.monitoringInterval) {
        clearInterval(this.monitoringInterval);
      }
    }
  }

  private simulateMempoolActivity(): void {
    // Simulate mempool transactions every 5-15 seconds
    const scheduleNext = () => {
      const delay = 5000 + Math.random() * 10000; // 5-15 seconds
      this.monitoringInterval = setTimeout(() => {
        if (this.isMonitoring) {
          this.generateSimulatedTransaction();
          scheduleNext();
        }
      }, delay);
    };

    scheduleNext();
  }

  private generateSimulatedTransaction(): void {
    // Randomly select a token from the demo tokens
    const token = DEMO_TOKENS[Math.floor(Math.random() * DEMO_TOKENS.length)];

    // Simulate different types of transactions
    const isBuy = Math.random() > 0.5;
    const amountEth = 0.1 + Math.random() * 2; // 0.1 to 2.1 ETH

    const tx: MempoolTransaction = {
      hash: '0x' + Math.random().toString(16).substring(2, 66),
      from: '0x' + Math.random().toString(16).substring(2, 42),
      to: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', // Uniswap V2 Router
      value: isBuy ? amountEth.toFixed(18) : '0',
      gasPrice: (10 + Math.random() * 40).toFixed(0), // 10-50 gwei
      timestamp: Date.now(),
      type: 'swap',
      tokenIn: isBuy ? 'ETH' : token.symbol,
      tokenOut: isBuy ? token.symbol : 'ETH',
      amountIn: amountEth.toFixed(18),
      amountOut: (amountEth * (isBuy ? 1 / token.price : token.price)).toFixed(0),
    };

    // Notify all listeners
    this.listeners.forEach((callback) => {
      callback(tx);
    });
  }

  isUserMonitoring(userId: number): boolean {
    return this.listeners.has(userId);
  }
}

export const mempoolMonitor = new MempoolMonitor();
