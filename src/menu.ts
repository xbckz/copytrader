import TelegramBot from 'node-telegram-bot-api';
import { statsTracker } from './stats/tracker';
import { formatCurrency, formatPercentage, formatAddress, formatTimestamp } from './utils/formatting';

export function getMainMenuKeyboard(): TelegramBot.InlineKeyboardMarkup {
  return {
    inline_keyboard: [
      [{ text: '📊 Dashboard', callback_data: 'dashboard' }],
      [
        { text: '🎯 Start Sniping', callback_data: 'start_sniping' },
        { text: '⏸️ Stop Sniping', callback_data: 'stop_sniping' }
      ],
      [{ text: '💼 Positions', callback_data: 'positions' }],
      [{ text: '📈 Trade History', callback_data: 'history' }],
      [{ text: '⚙️ Settings', callback_data: 'settings' }],
    ],
  };
}

export function getDashboardMessage(userId: number): string {
  const stats = statsTracker.getUserStats(userId);

  const totalValue = stats.balance + stats.activePositions.reduce((sum, pos) => {
    return sum + (pos.currentPrice * pos.amount);
  }, 0);

  const unrealizedPnL = stats.activePositions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);

  return `
📊 *DASHBOARD*

💰 *Balance:* ${formatCurrency(stats.balance)}
💎 *Portfolio Value:* ${formatCurrency(totalValue)}
${unrealizedPnL !== 0 ? `📈 *Unrealized P&L:* ${formatCurrency(unrealizedPnL)} (${formatPercentage((unrealizedPnL / 20) * 100)})` : ''}

📊 *Trading Stats:*
• Total Trades: ${stats.totalTrades}
• Successful: ${stats.successfulTrades} ✅
• Failed: ${stats.failedTrades} ❌
• Win Rate: ${stats.winRate.toFixed(1)}%

💸 *Financial:*
• Total Profit: ${formatCurrency(stats.totalProfit)}
• Total Fees: ${formatCurrency(stats.totalFees)}
• Net P&L: ${formatCurrency(stats.totalProfit - stats.totalFees)}

🎯 *Active Positions:* ${stats.activePositions.length}
  `.trim();
}

export function getPositionsMessage(userId: number): string {
  const stats = statsTracker.getUserStats(userId);

  if (stats.activePositions.length === 0) {
    return '💼 *POSITIONS*\n\nNo active positions. Start sniping to open positions!';
  }

  let message = '💼 *ACTIVE POSITIONS*\n\n';

  stats.activePositions.forEach((pos, index) => {
    const pnlPercent = ((pos.currentPrice - pos.entryPrice) / pos.entryPrice) * 100;
    const pnlEmoji = pos.unrealizedPnL >= 0 ? '📈' : '📉';

    message += `${index + 1}. *${pos.tokenSymbol}*\n`;
    message += `   Amount: ${pos.amount.toFixed(0)} tokens\n`;
    message += `   Entry: ${formatCurrency(pos.entryPrice)}\n`;
    message += `   Current: ${formatCurrency(pos.currentPrice)}\n`;
    message += `   ${pnlEmoji} P&L: ${formatCurrency(pos.unrealizedPnL)} (${formatPercentage(pnlPercent)})\n`;
    message += `   Address: \`${formatAddress(pos.tokenAddress)}\`\n\n`;
  });

  return message.trim();
}

export function getPositionsKeyboard(userId: number): TelegramBot.InlineKeyboardMarkup {
  const stats = statsTracker.getUserStats(userId);
  const keyboard: TelegramBot.InlineKeyboardButton[][] = [];

  stats.activePositions.forEach((pos) => {
    keyboard.push([
      { text: `Sell 50% ${pos.tokenSymbol}`, callback_data: `sell_${pos.tokenAddress}_50` },
      { text: `Sell 100% ${pos.tokenSymbol}`, callback_data: `sell_${pos.tokenAddress}_100` },
    ]);
  });

  keyboard.push([{ text: '🔙 Back to Menu', callback_data: 'main_menu' }]);

  return { inline_keyboard: keyboard };
}

export function getTradeHistoryMessage(userId: number): string {
  const stats = statsTracker.getUserStats(userId);

  if (stats.tradeHistory.length === 0) {
    return '📈 *TRADE HISTORY*\n\nNo trades yet. Start sniping to see your history!';
  }

  let message = '📈 *TRADE HISTORY* (Last 10)\n\n';

  stats.tradeHistory.slice(0, 10).forEach((trade, index) => {
    const emoji = trade.type === 'buy' ? '🟢' : '🔴';
    const statusEmoji = trade.status === 'completed' ? '✅' : '❌';

    message += `${index + 1}. ${emoji} *${trade.type.toUpperCase()}* ${trade.tokenSymbol} ${statusEmoji}\n`;
    message += `   Time: ${formatTimestamp(trade.timestamp)}\n`;
    message += `   Amount: ${trade.amount.toFixed(0)} @ ${formatCurrency(trade.price)}\n`;
    message += `   Gas Fee: ${formatCurrency(trade.gasFee)}\n`;

    if (trade.profit !== undefined) {
      const profitEmoji = trade.profit >= 0 ? '💰' : '💸';
      message += `   ${profitEmoji} Profit: ${formatCurrency(trade.profit)}\n`;
    }

    message += `\n`;
  });

  return message.trim();
}

export function getSettingsMessage(): string {
  return `
⚙️ *SETTINGS*

🎮 *Mode:* Demo (Simulated Trading)
💵 *Initial Balance:* €20
📊 *Max Slippage:* 0.5%
⛽ *Gas Strategy:* Low (Target + 1 gwei)

ℹ️ This is a demo version. All trades are simulated with realistic fees and market conditions.

🔄 Use /reset to reset your statistics and start over.
  `.trim();
}

export function getSettingsKeyboard(): TelegramBot.InlineKeyboardMarkup {
  return {
    inline_keyboard: [
      [{ text: '🔄 Reset Statistics', callback_data: 'reset_stats' }],
      [{ text: '🔙 Back to Menu', callback_data: 'main_menu' }],
    ],
  };
}
