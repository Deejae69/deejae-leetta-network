"""
Error handling utilities for DeeJae LeEtta Network
Provides consistent error handling and recovery strategies
"""

from functools import wraps
from typing import Callable, Any, Optional
import traceback
from config.logging_config import setup_logger

logger = setup_logger(__name__)


class NetworkError(Exception):
    """Base exception for network-related errors"""
    pass


class AgentError(Exception):
    """Base exception for AI agent errors"""
    pass


class BlockchainError(Exception):
    """Base exception for blockchain interaction errors"""
    pass


class WebhookError(Exception):
    """Base exception for webhook handling errors"""
    pass


class TradingError(Exception):
    """Base exception for trading strategy errors"""
    pass


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff

            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        return wrapper
    return decorator


def handle_errors(error_type: type = Exception, default_return: Any = None):
    """
    Decorator to handle errors gracefully and return a default value

    Args:
        error_type: Type of exception to catch
        default_return: Value to return on error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except error_type as e:
                logger.error(
                    f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                )
                return default_return

        return wrapper
    return decorator


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with arguments and return values
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {str(e)}")
            raise

    return wrapper


class ErrorContext:
    """
    Context manager for error handling with automatic logging

    Usage:
        with ErrorContext("Processing transaction"):
            # Your code here
            pass
    """

    def __init__(self, context: str, raise_exception: bool = True):
        self.context = context
        self.raise_exception = raise_exception

    def __enter__(self):
        logger.debug(f"Starting: {self.context}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Error during {self.context}: {exc_type.__name__}: {str(exc_val)}\n"
                f"{traceback.format_tb(exc_tb)}"
            )
            return not self.raise_exception  # Suppress exception if raise_exception is False

        logger.debug(f"Completed: {self.context}")
        return False
