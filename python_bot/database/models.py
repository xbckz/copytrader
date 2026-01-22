"""
Database models for storing trade data
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class Position(Base):
    """Position database model"""
    __tablename__ = 'positions'

    id = Column(String, primary_key=True)
    token_address = Column(String, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_amount_sol = Column(Float, nullable=False)
    token_amount = Column(Integer, nullable=False)
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
    """Trade history database model"""
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    signature = Column(String, unique=True, nullable=False)
    position_id = Column(String, nullable=False)
    trade_type = Column(String, nullable=False)  # 'buy' or 'sell'
    token_address = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    amount_sol = Column(Float, nullable=False)
    token_amount = Column(Integer, nullable=False)
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
