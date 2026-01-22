import TelegramBot from 'node-telegram-bot-api';
import { TELEGRAM_BOT_TOKEN } from './config';
import { mempoolMonitor } from './trading/mempool';
import { MEVSniper } from './trading/mev';
import { statsTracker } from './stats/tracker';
import {
  getMainMenuKeyboard,
  getDashboardMessage,
  getPositionsMessage,
  getPositionsKeyboard,
  getTradeHistoryMessage,
  getSettingsMessage,
  getSettingsKeyboard,
} from './menu';
import { MempoolTransaction } from './types';
import { formatCurrency, formatAddress } from './utils/formatting';

export class CopyTraderBot {
  private bot: TelegramBot;
  private snipers: Map<number, MEVSniper> = new Map();
  private notificationQueue: Map<number, NodeJS.Timeout> = new Map();

  constructor() {
    this.bot = new TelegramBot(TELEGRAM_BOT_TOKEN, { polling: true });
    this.setupHandlers();
  }

  private setupHandlers(): void {
    // Command handlers
    this.bot.onText(/\/start/, (msg) => this.handleStart(msg));
    this.bot.onText(/\/reset/, (msg) => this.handleReset(msg));
    this.bot.onText(/\/help/, (msg) => this.handleHelp(msg));

    // Callback query handler
    this.bot.on('callback_query', (query) => this.handleCallbackQuery(query));

    console.log('✅ Bot is running...');
  }

  private async handleStart(msg: TelegramBot.Message): Promise<void> {
    const chatId = msg.chat.id;

    const welcomeMessage = `
🤖 *Welcome to Crypto Copy Trader Bot!*

This is a demo MEV sniping bot that simulates copy trading with realistic fees and market conditions.

💰 *Starting Balance:* €20
🎯 *Strategy:* MEV Mempool Sniping
⚡ *Fee Optimization:* Low gas (Target + 1 gwei)

*How it works:*
1. Monitor mempool for large buy transactions
2. Analyze profitability after fees
3. Execute snipe orders automatically
4. Track positions and P&L in real-time

Use the menu below to get started!
    `.trim();

    await this.bot.sendMessage(chatId, welcomeMessage, {
      parse_mode: 'Markdown',
      reply_markup: getMainMenuKeyboard(),
    });
  }

  private async handleReset(msg: TelegramBot.Message): Promise<void> {
    const chatId = msg.chat.id;
    const userId = msg.from?.id || chatId;

    // Stop sniping if active
    if (mempoolMonitor.isUserMonitoring(userId)) {
      mempoolMonitor.stopMonitoring(userId);
    }

    statsTracker.resetStats(userId);

    await this.bot.sendMessage(
      chatId,
      '🔄 Statistics reset! Your balance is back to €20.',
      { reply_markup: getMainMenuKeyboard() }
    );
  }

  private async handleHelp(msg: TelegramBot.Message): Promise<void> {
    const chatId = msg.chat.id;

    const helpMessage = `
📖 *HELP & COMMANDS*

*/start* - Start the bot and show main menu
*/reset* - Reset statistics and balance
*/help* - Show this help message

*Menu Options:*
• 📊 Dashboard - View your stats and balance
• 🎯 Start Sniping - Begin monitoring mempool
• ⏸️ Stop Sniping - Pause trading
• 💼 Positions - View and manage positions
• 📈 Trade History - See past trades
• ⚙️ Settings - Bot configuration

*About MEV Sniping:*
The bot monitors the mempool for large buy transactions and attempts to copy them. By placing our order after the target transaction, we save on gas fees (only +1 gwei above the target).

*Fees Included:*
• Gas fees (realistic for €20 trades)
• Slippage (0.1-0.5%)
• Network congestion simulation

*Demo Mode:*
All trades are simulated. No real funds are used.
    `.trim();

    await this.bot.sendMessage(chatId, helpMessage, {
      parse_mode: 'Markdown',
      reply_markup: getMainMenuKeyboard(),
    });
  }

  private async handleCallbackQuery(query: TelegramBot.CallbackQuery): Promise<void> {
    const chatId = query.message?.chat.id;
    const messageId = query.message?.message_id;
    const userId = query.from.id;
    const data = query.data;

    if (!chatId || !data) return;

    try {
      await this.bot.answerCallbackQuery(query.id);

      switch (data) {
        case 'main_menu':
          await this.bot.editMessageText('🏠 *Main Menu*\n\nSelect an option:', {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'Markdown',
            reply_markup: getMainMenuKeyboard(),
          });
          break;

        case 'dashboard':
          await this.bot.editMessageText(getDashboardMessage(userId), {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'Markdown',
            reply_markup: {
              inline_keyboard: [[{ text: '🔙 Back to Menu', callback_data: 'main_menu' }]],
            },
          });
          break;

        case 'start_sniping':
          await this.startSniping(chatId, userId, messageId);
          break;

        case 'stop_sniping':
          await this.stopSniping(chatId, userId, messageId);
          break;

        case 'positions':
          await this.bot.editMessageText(getPositionsMessage(userId), {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'Markdown',
            reply_markup: getPositionsKeyboard(userId),
          });
          break;

        case 'history':
          await this.bot.editMessageText(getTradeHistoryMessage(userId), {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'Markdown',
            reply_markup: {
              inline_keyboard: [[{ text: '🔙 Back to Menu', callback_data: 'main_menu' }]],
            },
          });
          break;

        case 'settings':
          await this.bot.editMessageText(getSettingsMessage(), {
            chat_id: chatId,
            message_id: messageId,
            parse_mode: 'Markdown',
            reply_markup: getSettingsKeyboard(),
          });
          break;

        case 'reset_stats':
          statsTracker.resetStats(userId);
          if (mempoolMonitor.isUserMonitoring(userId)) {
            mempoolMonitor.stopMonitoring(userId);
          }
          await this.bot.editMessageText(
            '🔄 Statistics reset! Balance restored to €20.',
            {
              chat_id: chatId,
              message_id: messageId,
              reply_markup: getMainMenuKeyboard(),
            }
          );
          break;

        default:
          // Handle sell commands
          if (data.startsWith('sell_') && messageId) {
            await this.handleSell(chatId, userId, messageId, data);
          }
          break;
      }
    } catch (error) {
      console.error('Error handling callback query:', error);
    }
  }

  private async startSniping(chatId: number, userId: number, messageId?: number): Promise<void> {
    if (mempoolMonitor.isUserMonitoring(userId)) {
      await this.bot.sendMessage(chatId, '⚠️ Sniping is already active!');
      return;
    }

    const stats = statsTracker.getUserStats(userId);
    if (stats.balance < 1) {
      await this.bot.sendMessage(chatId, '⚠️ Insufficient balance to start sniping. Minimum €1 required.');
      return;
    }

    if (!this.snipers.has(userId)) {
      this.snipers.set(userId, new MEVSniper(userId));
    }

    const sniper = this.snipers.get(userId)!;

    mempoolMonitor.startMonitoring(userId, async (tx: MempoolTransaction) => {
      await this.handleMempoolTransaction(chatId, userId, tx, sniper);
    });

    const message = `
🎯 *Sniping Started!*

Monitoring mempool for opportunities...
You'll be notified when trades are executed.

📊 Current Balance: ${formatCurrency(stats.balance)}
⚡ Gas Strategy: Target + 1 gwei (low fees)
    `.trim();

    if (messageId) {
      await this.bot.editMessageText(message, {
        chat_id: chatId,
        message_id: messageId,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [[{ text: '🔙 Back to Menu', callback_data: 'main_menu' }]],
        },
      });
    } else {
      await this.bot.sendMessage(chatId, message, {
        parse_mode: 'Markdown',
        reply_markup: getMainMenuKeyboard(),
      });
    }
  }

  private async stopSniping(chatId: number, userId: number, messageId?: number): Promise<void> {
    if (!mempoolMonitor.isUserMonitoring(userId)) {
      await this.bot.sendMessage(chatId, '⚠️ Sniping is not active!');
      return;
    }

    mempoolMonitor.stopMonitoring(userId);

    const message = '⏸️ *Sniping Stopped*\n\nMempool monitoring has been paused.';

    if (messageId) {
      await this.bot.editMessageText(message, {
        chat_id: chatId,
        message_id: messageId,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [[{ text: '🔙 Back to Menu', callback_data: 'main_menu' }]],
        },
      });
    } else {
      await this.bot.sendMessage(chatId, message, {
        parse_mode: 'Markdown',
        reply_markup: getMainMenuKeyboard(),
      });
    }
  }

  private async handleMempoolTransaction(
    chatId: number,
    userId: number,
    tx: MempoolTransaction,
    sniper: MEVSniper
  ): Promise<void> {
    // Analyze the transaction
    const analysis = await sniper.analyzeAndSnipe(tx);

    // Only notify about interesting opportunities
    if (analysis.shouldSnipe) {
      // Send notification about detected opportunity
      await this.bot.sendMessage(
        chatId,
        `🔍 *Opportunity Detected!*\n\n` +
        `Token: ${tx.tokenOut}\n` +
        `Target Buy: ${parseFloat(tx.amountIn!).toFixed(4)} ETH\n` +
        `Gas: ${tx.gasPrice} gwei\n\n` +
        `Analyzing...`,
        { parse_mode: 'Markdown' }
      );

      // Execute the trade
      const trade = await sniper.executeTrade(tx);

      // Send trade result
      const resultEmoji = trade.status === 'completed' ? '✅' : '❌';
      const resultMessage = `
${resultEmoji} *Trade ${trade.status === 'completed' ? 'Executed' : 'Failed'}!*

Token: ${trade.tokenSymbol}
Amount: ${trade.amount.toFixed(0)} tokens
Price: ${formatCurrency(trade.price)}
Gas Fee: ${formatCurrency(trade.gasFee)}
Total Cost: ${formatCurrency(trade.totalCost)}

${trade.status === 'completed' ? '💎 Position opened!' : '⚠️ ' + analysis.reason}
      `.trim();

      await this.bot.sendMessage(chatId, resultMessage, {
        parse_mode: 'Markdown',
      });

      // Update dashboard
      const stats = statsTracker.getUserStats(userId);
      if (stats.balance < 1) {
        await this.stopSniping(chatId, userId);
        await this.bot.sendMessage(
          chatId,
          '⚠️ Insufficient balance. Sniping stopped.\n\nSell your positions or reset to continue.',
          { reply_markup: getMainMenuKeyboard() }
        );
      }
    }
  }

  private async handleSell(chatId: number, userId: number, messageId: number, data: string): Promise<void> {
    const parts = data.split('_');
    const tokenAddress = parts[1];
    const percentage = parseInt(parts[2]);

    const sniper = this.snipers.get(userId) || new MEVSniper(userId);
    const trade = await sniper.sellPosition(tokenAddress, percentage);

    if (!trade) {
      await this.bot.answerCallbackQuery({ callback_query_id: '', text: 'Position not found!' });
      return;
    }

    const profitEmoji = trade.profit && trade.profit >= 0 ? '💰' : '💸';
    const message = `
✅ *Sell Order Executed!*

Token: ${trade.tokenSymbol}
Amount: ${trade.amount.toFixed(0)} tokens (${percentage}%)
Price: ${formatCurrency(trade.price)}
${profitEmoji} Profit: ${formatCurrency(trade.profit || 0)}
Gas Fee: ${formatCurrency(trade.gasFee)}
Net Value: ${formatCurrency(trade.totalCost)}
    `.trim();

    await this.bot.sendMessage(chatId, message, { parse_mode: 'Markdown' });

    // Update the positions view
    await this.bot.editMessageText(getPositionsMessage(userId), {
      chat_id: chatId,
      message_id: messageId,
      parse_mode: 'Markdown',
      reply_markup: getPositionsKeyboard(userId),
    });
  }

  public start(): void {
    console.log('🤖 Crypto Copy Trader Bot started!');
    console.log('📡 Listening for commands...');
  }
}
