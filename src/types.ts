export interface Trade {
  id: string;
  timestamp: number;
  type: 'buy' | 'sell';
  tokenAddress: string;
  tokenSymbol: string;
  amount: number;
  price: number;
  gasUsed: number;
  gasFee: number;
  totalCost: number;
  profit?: number;
  status: 'pending' | 'completed' | 'failed';
}

export interface UserStats {
  userId: number;
  balance: number;
  totalTrades: number;
  successfulTrades: number;
  failedTrades: number;
  totalProfit: number;
  totalFees: number;
  winRate: number;
  activePositions: Position[];
  tradeHistory: Trade[];
}

export interface Position {
  tokenAddress: string;
  tokenSymbol: string;
  amount: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  entryTime: number;
}

export interface MempoolTransaction {
  hash: string;
  from: string;
  to: string;
  value: string;
  gasPrice: string;
  timestamp: number;
  type: 'swap' | 'transfer' | 'unknown';
  tokenIn?: string;
  tokenOut?: string;
  amountIn?: string;
  amountOut?: string;
}

export interface BotConfig {
  demoMode: boolean;
  initialBalance: number;
  maxSlippage: number;
  gasLimit: number;
  minGasPrice: number;
  maxGasPrice: number;
}
