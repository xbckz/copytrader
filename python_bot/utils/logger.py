"""
Logging configuration for the copy trading bot
"""
import logging
import sys
from typing import Optional
from pathlib import Path
import colorlog
from datetime import datetime


def setup_logger(
    name: str = "copytrader",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup a logger with color formatting and optional file output

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler with colors
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Color formatter
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file

        # File formatter (no colors)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the given name"""
    return logging.getLogger(name)


# Create default logger instance
default_logger = setup_logger(
    name="copytrader",
    level="INFO",
    log_file=f"logs/copytrader_{datetime.now().strftime('%Y%m%d')}.log"
)
