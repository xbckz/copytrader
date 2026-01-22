"""
Trading strategy configurations for testing and comparison
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""
    id: int
    name: str
    description: str

    # Entry parameters
    copy_percentage: float  # Percentage of wallet balance to use per trade
    min_wallet_trade_size: float  # Minimum SOL size of wallet trade to copy

    # Exit parameters
    take_profit_percentage: float  # TP as percentage
    stop_loss_percentage: float    # SL as percentage

    # Position management
    max_positions: int  # Maximum concurrent positions
    position_size_pct: float  # Max position size as % of balance

    # Trailing stop
    use_trailing_stop: bool
    trailing_stop_activation: float  # Activate trailing after this % profit
    trailing_stop_distance: float    # Distance from peak in %

    # Time-based exit
    max_hold_time: int  # Maximum hold time in seconds (0 = unlimited)

    # Risk management
    daily_loss_limit: float  # Max daily loss as % of starting balance
    max_slippage: float  # Maximum acceptable slippage %


# Strategy 1: Conservative - Small gains, tight stop
STRATEGY_1 = StrategyConfig(
    id=1,
    name="Conservative",
    description="Low risk with quick exits - TP 10%, SL 5%",
    copy_percentage=0.15,  # 15% of balance per trade
    min_wallet_trade_size=0.5,  # Only copy trades >= 0.5 SOL
    take_profit_percentage=10.0,
    stop_loss_percentage=5.0,
    max_positions=3,
    position_size_pct=0.15,
    use_trailing_stop=False,
    trailing_stop_activation=8.0,
    trailing_stop_distance=3.0,
    max_hold_time=3600,  # 1 hour max hold
    daily_loss_limit=10.0,
    max_slippage=1.0
)

# Strategy 2: Balanced - Medium risk/reward
STRATEGY_2 = StrategyConfig(
    id=2,
    name="Balanced",
    description="Balanced approach - TP 20%, SL 10%",
    copy_percentage=0.20,  # 20% of balance per trade
    min_wallet_trade_size=0.3,
    take_profit_percentage=20.0,
    stop_loss_percentage=10.0,
    max_positions=5,
    position_size_pct=0.20,
    use_trailing_stop=True,
    trailing_stop_activation=15.0,
    trailing_stop_distance=5.0,
    max_hold_time=7200,  # 2 hours max hold
    daily_loss_limit=15.0,
    max_slippage=1.5
)

# Strategy 3: Aggressive - Higher risk/reward
STRATEGY_3 = StrategyConfig(
    id=3,
    name="Aggressive",
    description="High risk/reward - TP 50%, SL 15%",
    copy_percentage=0.25,  # 25% of balance per trade
    min_wallet_trade_size=0.2,
    take_profit_percentage=50.0,
    stop_loss_percentage=15.0,
    max_positions=5,
    position_size_pct=0.25,
    use_trailing_stop=True,
    trailing_stop_activation=30.0,
    trailing_stop_distance=10.0,
    max_hold_time=14400,  # 4 hours max hold
    daily_loss_limit=20.0,
    max_slippage=2.0
)

# Strategy 4: Scalper - Very quick trades
STRATEGY_4 = StrategyConfig(
    id=4,
    name="Scalper",
    description="Quick profits - TP 5%, SL 3%",
    copy_percentage=0.30,  # 30% of balance per trade
    min_wallet_trade_size=0.1,
    take_profit_percentage=5.0,
    stop_loss_percentage=3.0,
    max_positions=8,
    position_size_pct=0.12,
    use_trailing_stop=False,
    trailing_stop_activation=4.0,
    trailing_stop_distance=1.5,
    max_hold_time=1800,  # 30 minutes max hold
    daily_loss_limit=12.0,
    max_slippage=0.8
)

# Strategy 5: HODL - Long-term holds with wide stops
STRATEGY_5 = StrategyConfig(
    id=5,
    name="HODL",
    description="Long-term holds - TP 100%, SL 25%",
    copy_percentage=0.20,  # 20% of balance per trade
    min_wallet_trade_size=1.0,  # Only copy significant trades
    take_profit_percentage=100.0,
    stop_loss_percentage=25.0,
    max_positions=3,
    position_size_pct=0.30,
    use_trailing_stop=True,
    trailing_stop_activation=50.0,
    trailing_stop_distance=20.0,
    max_hold_time=0,  # No time limit
    daily_loss_limit=25.0,
    max_slippage=2.5
)


# All strategies mapped by ID
STRATEGIES: Dict[int, StrategyConfig] = {
    1: STRATEGY_1,
    2: STRATEGY_2,
    3: STRATEGY_3,
    4: STRATEGY_4,
    5: STRATEGY_5
}


def get_strategy(strategy_id: int) -> StrategyConfig:
    """Get strategy configuration by ID"""
    if strategy_id not in STRATEGIES:
        raise ValueError(f"Invalid strategy ID: {strategy_id}. Must be 1-5.")
    return STRATEGIES[strategy_id]


def get_all_strategies() -> Dict[int, StrategyConfig]:
    """Get all strategy configurations"""
    return STRATEGIES


def print_strategy_comparison():
    """Print comparison table of all strategies"""
    print("\n" + "="*100)
    print("STRATEGY COMPARISON TABLE")
    print("="*100)
    print(f"{'ID':<5} {'Name':<15} {'TP%':<8} {'SL%':<8} {'Max Pos':<10} {'Hold Time':<12} {'Description'}")
    print("-"*100)

    for strategy in STRATEGIES.values():
        hold_time = f"{strategy.max_hold_time}s" if strategy.max_hold_time > 0 else "Unlimited"
        print(f"{strategy.id:<5} {strategy.name:<15} {strategy.take_profit_percentage:<8.1f} "
              f"{strategy.stop_loss_percentage:<8.1f} {strategy.max_positions:<10} "
              f"{hold_time:<12} {strategy.description}")

    print("="*100 + "\n")
