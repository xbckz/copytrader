"""
Main entry point for Solana Copy Trading Bot
"""
import asyncio
from typing import List, Dict
from datetime import datetime

from .config import settings
from .config.strategies import STRATEGIES, get_all_strategies, print_strategy_comparison
from .utils.logger import setup_logger, get_logger
from .blockchain.solana_client import SolanaClient
from .blockchain.transaction_monitor import TransactionMonitor
from .monitoring.kolscan import KOLscanClient
from .monitoring.wallet_tracker import WalletTracker
from .trading.dex_client import JupiterClient
from .trading.price_tracker import PriceTracker
from .trading.executor import TradeExecutor
from .strategy.engine import StrategyEngine
from .database.models import init_database

# Setup logger
logger = setup_logger(
    name="copytrader",
    level=settings.log_level,
    log_file=f"logs/copytrader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)


class CopyTradingBot:
    """Main copy trading bot application"""

    def __init__(self):
        """Initialize the bot"""
        self.solana_client: SolanaClient = None
        self.jupiter_client: JupiterClient = None
        self.kolscan_client: KOLscanClient = None
        self.transaction_monitor: TransactionMonitor = None
        self.wallet_tracker: WalletTracker = None
        self.price_tracker: PriceTracker = None
        self.trade_executor: TradeExecutor = None

        self.strategy_engines: List[StrategyEngine] = []
        self.is_running = False

        logger.info("=" * 80)
        logger.info("SOLANA COPY TRADING BOT")
        logger.info("=" * 80)
        logger.info(f"Mode: {'TEST' if settings.test_mode else 'PRODUCTION'}")
        logger.info(f"Network: {settings.solana_network}")
        logger.info(f"Simulate Trades: {settings.simulate_trades}")
        logger.info("=" * 80)

    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing bot components...")

        try:
            # Initialize database
            await init_database()

            # Initialize Solana client
            self.solana_client = SolanaClient(
                rpc_url=settings.solana_rpc_url,
                commitment="confirmed"
            )
            await self.solana_client.connect()

            # Initialize Jupiter client
            self.jupiter_client = JupiterClient()
            await self.jupiter_client.connect()

            # Initialize KOLscan client
            self.kolscan_client = KOLscanClient(
                api_url=settings.kolscan_api_url,
                api_key=settings.kolscan_api_key
            )
            await self.kolscan_client.connect()

            # Initialize transaction monitor
            self.transaction_monitor = TransactionMonitor(
                solana_client=self.solana_client,
                check_interval=2.0
            )

            # Initialize wallet tracker
            self.wallet_tracker = WalletTracker(
                kolscan_client=self.kolscan_client,
                transaction_monitor=self.transaction_monitor,
                top_count=settings.top_wallets_count,
                refresh_interval=settings.wallet_refresh_interval
            )

            # Initialize wallet list
            await self.wallet_tracker.initialize()

            # Initialize price tracker
            self.price_tracker = PriceTracker(
                jupiter_client=self.jupiter_client,
                update_interval=settings.price_update_interval
            )

            # Initialize trade executor
            self.trade_executor = TradeExecutor(
                solana_client=self.solana_client,
                jupiter_client=self.jupiter_client,
                wallet_keypair=None  # Set this with actual keypair
            )

            # Initialize strategy engines
            await self._initialize_strategies()

            logger.info("All components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}", exc_info=True)
            raise

    async def _initialize_strategies(self):
        """Initialize strategy engines based on configuration"""
        active_strategy = settings.active_strategy

        if active_strategy.lower() == 'all':
            # Run all strategies
            logger.info("Initializing ALL strategies for comparison")
            strategies = get_all_strategies()

            for strategy_id, strategy_config in strategies.items():
                engine = StrategyEngine(
                    solana_client=self.solana_client,
                    jupiter_client=self.jupiter_client,
                    wallet_tracker=self.wallet_tracker,
                    transaction_monitor=self.transaction_monitor,
                    price_tracker=self.price_tracker,
                    trade_executor=self.trade_executor,
                    strategy=strategy_config
                )
                self.strategy_engines.append(engine)

            logger.info(f"Initialized {len(self.strategy_engines)} strategy engines")

        else:
            # Run single strategy
            try:
                strategy_id = int(active_strategy)
                strategy_config = STRATEGIES[strategy_id]

                logger.info(f"Initializing strategy: {strategy_config.name}")

                engine = StrategyEngine(
                    solana_client=self.solana_client,
                    jupiter_client=self.jupiter_client,
                    wallet_tracker=self.wallet_tracker,
                    transaction_monitor=self.transaction_monitor,
                    price_tracker=self.price_tracker,
                    trade_executor=self.trade_executor,
                    strategy=strategy_config
                )
                self.strategy_engines.append(engine)

                logger.info(f"Initialized strategy engine: {strategy_config.name}")

            except (ValueError, KeyError) as e:
                logger.error(f"Invalid strategy ID: {active_strategy}")
                raise

    async def start(self):
        """Start the bot"""
        if self.is_running:
            logger.warning("Bot already running")
            return

        self.is_running = True
        logger.info("Starting copy trading bot...")

        try:
            # Start transaction monitor
            await self.transaction_monitor.start()

            # Start wallet tracker auto-refresh
            await self.wallet_tracker.start_auto_refresh()

            # Start price tracker
            await self.price_tracker.start()

            # Start all strategy engines
            for engine in self.strategy_engines:
                await engine.start()

            logger.info("=" * 80)
            logger.info("BOT STARTED - Monitoring for trades")
            logger.info("=" * 80)

            # Print strategy comparison if running multiple
            if len(self.strategy_engines) > 1:
                print_strategy_comparison()

        except Exception as e:
            logger.error(f"Error starting bot: {e}", exc_info=True)
            self.is_running = False
            raise

    async def stop(self):
        """Stop the bot"""
        if not self.is_running:
            return

        logger.info("Stopping copy trading bot...")

        # Stop all strategy engines
        for engine in self.strategy_engines:
            await engine.stop()

        # Stop price tracker
        await self.price_tracker.stop()

        # Stop wallet tracker
        await self.wallet_tracker.stop_auto_refresh()

        # Stop transaction monitor
        await self.transaction_monitor.stop()

        # Disconnect clients
        await self.jupiter_client.disconnect()
        await self.kolscan_client.disconnect()
        await self.solana_client.disconnect()

        self.is_running = False
        logger.info("Bot stopped")

    async def print_status(self):
        """Print current bot status"""
        logger.info("=" * 80)
        logger.info("BOT STATUS")
        logger.info("=" * 80)

        # Wallet tracker status
        tracker_stats = self.wallet_tracker.get_statistics()
        logger.info(f"Tracked Wallets: {tracker_stats['total_wallets']}")
        logger.info(f"Avg Win Rate: {tracker_stats['average_win_rate']:.2f}%")

        # Strategy performance
        for i, engine in enumerate(self.strategy_engines):
            stats = engine.get_performance_stats()
            logger.info(f"\n--- Strategy {i+1}: {stats['strategy_name']} ---")
            logger.info(f"Balance: {stats['current_balance']:.4f} SOL")
            logger.info(f"Portfolio Value: {stats['portfolio_value']:.4f} SOL")
            logger.info(f"Total PnL: {stats['total_pnl_sol']:.4f} SOL ({stats['total_pnl_percentage']:.2f}%)")
            logger.info(f"Open Positions: {stats['open_positions']}")
            logger.info(f"Total Trades: {stats['total_trades']}")
            logger.info(f"Win Rate: {stats['win_rate']:.2f}%")

        logger.info("=" * 80)

    async def run(self):
        """Main run loop"""
        try:
            await self.initialize()
            await self.start()

            # Run indefinitely
            while self.is_running:
                await asyncio.sleep(60)  # Print status every minute
                await self.print_status()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down gracefully...")
        await self.stop()
        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    bot = CopyTradingBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
