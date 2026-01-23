"""
Database models for storing trade data
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class Session(Base):
    """Trading session model - allows multiple sessions with different configs"""
    __tablename__ = 'sessions'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    strategy_id = Column(Integer, nullable=False)

    # Balance tracking
    starting_balance_sol = Column(Float, nullable=False)
    current_balance_sol = Column(Float, nullable=False)

    # Session configuration (stored as JSON)
    config = Column(JSON, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)

    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl_sol = Column(Float, default=0.0)
    total_pnl_percentage = Column(Float, default=0.0)


class BalanceTransaction(Base):
    """Balance transaction model for deposits/withdrawals"""
    __tablename__ = 'balance_transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)  # 'deposit', 'withdrawal'
    amount_sol = Column(Float, nullable=False)
    amount_eur = Column(Float, nullable=True)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    note = Column(String, nullable=True)


class TrackedWallet(Base):
    """Manually tracked wallet model"""
    __tablename__ = 'tracked_wallets'

    address = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    source = Column(String, nullable=False)  # 'manual', 'kolscan'

    # Tracking info
    added_at = Column(DateTime, default=datetime.now)
    added_by = Column(String, default='user')
    is_active = Column(Boolean, default=True)

    # Performance metrics (updated periodically)
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    last_trade_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.now)

    # Additional metadata
    notes = Column(Text, nullable=True)


class Position(Base):
    """Position database model"""
    __tablename__ = 'positions'

    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    token_address = Column(String, nullable=False)
    token_symbol = Column(String, nullable=True)
    entry_price = Column(Float, nullable=False)
    entry_amount_sol = Column(Float, nullable=False)
    token_amount = Column(Float, nullable=False)
    strategy_id = Column(Integer, nullable=False)
    wallet_source = Column(String, nullable=False)

    # TP/SL
    take_profit_price = Column(Float)
    stop_loss_price = Column(Float)

    # Status
    is_open = Column(Boolean, default=True)
    opened_at = Column(DateTime, default=datetime.now)

    # Exit data
    exit_price = Column(Float, nullable=True)
    exit_amount_sol = Column(Float, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    pnl_sol = Column(Float, nullable=True)
    pnl_percentage = Column(Float, nullable=True)
    close_reason = Column(String, nullable=True)


class Trade(Base):
    """Trade history database model with detailed fee tracking"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    signature = Column(String, unique=True, nullable=False)
    session_id = Column(String, nullable=False)
    position_id = Column(String, nullable=False)
    trade_type = Column(String, nullable=False)  # 'buy' or 'sell'
    token_address = Column(String, nullable=False)
    token_symbol = Column(String, nullable=True)

    # Pricing
    price = Column(Float, nullable=False)
    amount_sol = Column(Float, nullable=False)
    token_amount = Column(Float, nullable=False)

    # Fees (all in SOL)
    network_fee = Column(Float, default=0.0)  # Base network fee (~0.000005 SOL)
    priority_fee = Column(Float, default=0.0)  # Priority fee for faster execution
    platform_fee = Column(Float, default=0.0)  # Jupiter/DEX platform fee
    slippage_cost = Column(Float, default=0.0)  # Actual slippage cost
    total_fee = Column(Float, default=0.0)  # Sum of all fees

    # Execution details
    expected_price = Column(Float, nullable=True)
    actual_price = Column(Float, nullable=True)
    slippage_percentage = Column(Float, default=0.0)
    price_impact_percentage = Column(Float, default=0.0)

    strategy_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    simulated = Column(Boolean, default=False)


async def init_database(database_url: str = None):
    """
    Initialize database

    Args:
        database_url: Database connection URL
    """
    db_url = database_url or settings.database_url

    try:
        # Create engine
        # Convert async SQLAlchemy URL to sync for migrations/initialization
        if 'sqlite+aiosqlite://' in db_url:
            db_url = db_url.replace('sqlite+aiosqlite://', 'sqlite:///')
        elif 'aiosqlite://' in db_url:
            db_url = db_url.replace('aiosqlite://', 'sqlite:///')

        engine = create_engine(
            db_url,
            echo=False
        )

        # Create tables
        Base.metadata.create_all(engine)

        logger.info(f"Database initialized: {db_url}")

        return engine

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
