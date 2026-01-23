"""
Configuration settings for the Solana Copy Trading Bot
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # Solana Configuration
    solana_rpc_url: str = Field(
        default="https://api.devnet.solana.com",
        description="Solana RPC endpoint"
    )
    solana_ws_url: str = Field(
        default="wss://api.devnet.solana.com",
        description="Solana WebSocket endpoint"
    )
    solana_network: str = Field(
        default="devnet",
        description="Solana network (mainnet-beta, devnet, testnet)"
    )

    # Wallet Configuration
    wallet_private_key: str = Field(
        default="",
        description="Base58 encoded private key"
    )
    wallet_public_key: str = Field(
        default="",
        description="Wallet public key"
    )

    # KOLscan API
    kolscan_api_key: Optional[str] = Field(
        default=None,
        description="KOLscan API key"
    )
    kolscan_api_url: str = Field(
        default="https://api.kolscan.com/v1",
        description="KOLscan API endpoint"
    )

    # Helius API
    helius_api_key: Optional[str] = Field(
        default=None,
        description="Helius API key for enhanced RPC"
    )
    use_helius: bool = Field(
        default=False,
        description="Use Helius enhanced RPC"
    )

    # Trading Configuration
    initial_balance_eur: float = Field(
        default=20.0,
        description="Initial balance in EUR (will be converted to SOL)"
    )
    sol_price_eur: float = Field(
        default=200.0,
        description="SOL price in EUR (updated dynamically)"
    )
    initial_balance: float = Field(
        default=100.0,
        description="Initial balance in SOL (calculated from EUR)"
    )
    min_trade_size: float = Field(
        default=0.01,
        description="Minimum trade size in SOL"
    )
    max_trade_size: float = Field(
        default=1.0,
        description="Maximum trade size in SOL"
    )
    max_position_size: float = Field(
        default=0.3,
        description="Maximum position size as fraction of balance"
    )

    # Risk Management
    slippage_bps: int = Field(
        default=100,
        description="Slippage tolerance in basis points (100 = 1%)"
    )
    priority_fee_lamports: int = Field(
        default=50000,
        description="Priority fee for transaction execution"
    )

    # Fee Configuration (for realistic simulation)
    base_network_fee: float = Field(
        default=0.000005,
        description="Base Solana network fee in SOL"
    )
    jupiter_platform_fee_bps: int = Field(
        default=25,
        description="Jupiter platform fee in basis points (0.25%)"
    )

    # Strategy Selection
    active_strategy: str = Field(
        default="1",
        description="Active strategy ID (1-5) or 'all'"
    )

    # Testing Mode
    test_mode: bool = Field(
        default=True,
        description="Enable test mode"
    )
    use_devnet: bool = Field(
        default=True,
        description="Use Solana devnet"
    )
    simulate_trades: bool = Field(
        default=False,
        description="Simulate trades without execution"
    )

    # Monitoring
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    enable_telegram_notifications: bool = Field(
        default=False,
        description="Enable Telegram notifications"
    )
    telegram_bot_token: Optional[str] = Field(
        default=None,
        description="Telegram bot token"
    )
    telegram_chat_id: Optional[str] = Field(
        default=None,
        description="Telegram chat ID"
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./copytrader.db",
        description="Database connection URL"
    )

    # Top Wallets Monitoring
    top_wallets_count: int = Field(
        default=100,
        description="Number of top KOLscan wallets to monitor"
    )
    wallet_refresh_interval: int = Field(
        default=3600,
        description="Interval to refresh wallet list (seconds)"
    )

    # Transaction Monitoring
    tx_confirmation_timeout: int = Field(
        default=60,
        description="Transaction confirmation timeout (seconds)"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed operations"
    )

    # Price Tracking
    price_update_interval: float = Field(
        default=1.0,
        description="Price update interval (seconds)"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.test_mode and self.solana_network == "mainnet-beta"

    @property
    def slippage_percentage(self) -> float:
        """Get slippage as percentage"""
        return self.slippage_bps / 100.0


# Global settings instance
settings = Settings()
