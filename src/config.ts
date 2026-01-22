import dotenv from 'dotenv';
import { BotConfig } from './types';

dotenv.config();

export const config: BotConfig = {
  demoMode: process.env.DEMO_MODE === 'true',
  initialBalance: parseFloat(process.env.INITIAL_BALANCE || '20'),
  maxSlippage: 0.5, // 0.5%
  gasLimit: 200000,
  minGasPrice: 5, // gwei
  maxGasPrice: 50, // gwei
};

export const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';

// Demo mode constants
export const DEMO_TOKENS = [
  { symbol: 'PEPE', address: '0x6982508145454Ce325dDbE47a25d4ec3d2311933', price: 0.00001 },
  { symbol: 'SHIB', address: '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE', price: 0.00002 },
  { symbol: 'DOGE', address: '0xba2ae424d960c26247dd6c32edc70b295c744c43', price: 0.08 },
  { symbol: 'FLOKI', address: '0xcf0C122c6b73ff809C693DB761e7BaeBe62b6a2E', price: 0.00015 },
];

export const ETH_PRICE_USD = 2300; // Simulated ETH price in USD
export const EUR_USD_RATE = 1.1; // EUR to USD conversion
