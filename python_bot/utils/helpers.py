"""
Helper utility functions
"""
import asyncio
from typing import Callable, Any, TypeVar, Optional
from functools import wraps
import time
from decimal import Decimal

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def format_sol(amount: float, decimals: int = 4) -> str:
    """Format SOL amount with specified decimals"""
    return f"{amount:.{decimals}f} SOL"


def format_percentage(percentage: float, decimals: int = 2) -> str:
    """Format percentage value"""
    sign = "+" if percentage >= 0 else ""
    return f"{sign}{percentage:.{decimals}f}%"


def format_price(price: float, decimals: int = 8) -> str:
    """Format token price"""
    if price >= 1:
        return f"${price:.4f}"
    else:
        # For small prices, use more decimals
        return f"${price:.{decimals}f}"


def lamports_to_sol(lamports: int) -> float:
    """Convert lamports to SOL"""
    return lamports / 1_000_000_000


def sol_to_lamports(sol: float) -> int:
    """Convert SOL to lamports"""
    return int(sol * 1_000_000_000)


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def retry_async(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper
    return decorator


def retry_sync(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying sync functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper
    return decorator


def truncate_address(address: str, start: int = 4, end: int = 4) -> str:
    """Truncate a Solana address for display"""
    if len(address) <= start + end:
        return address
    return f"{address[:start]}...{address[-end:]}"


async def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 60.0,
    check_interval: float = 0.5,
    error_message: str = "Condition timeout"
) -> bool:
    """
    Wait for a condition to become true

    Args:
        condition: Callable that returns bool
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        error_message: Error message if timeout occurs

    Returns:
        True if condition met, False if timeout

    Raises:
        TimeoutError: If condition not met within timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return True
        await asyncio.sleep(check_interval)

    raise TimeoutError(error_message)
