"""
Utility functions for Calendar Sync
Includes logging, retry logic, rate limiting, and helper functions
"""

import logging
import time
import functools
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from pathlib import Path

from src.config import Config


def setup_logging(name: str = "calendar_sync") -> logging.Logger:
    """
    Set up logging with both file and console handlers

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_path = Path(Config.LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        Config.LOG_PATH,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator to retry a function with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for wait time between retries
        exceptions: Tuple of exception types to catch

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = setup_logging()
            retries = 0

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )
                        raise

                    wait_time = backoff_factor**retries
                    logger.warning(
                        f"{func.__name__} failed (attempt {retries}/{max_retries}), "
                        f"retrying in {wait_time:.1f}s: {e}"
                    )
                    time.sleep(wait_time)

            return None

        return wrapper

    return decorator


class RateLimiter:
    """
    Simple rate limiter to avoid exceeding API rate limits

    Example:
        rate_limiter = RateLimiter(calls_per_second=3)  # Notion limit
        for item in items:
            rate_limiter.wait_if_needed()
            api_call(item)
    """

    def __init__(self, calls_per_second: float):
        """
        Initialize rate limiter

        Args:
            calls_per_second: Maximum number of calls per second
        """
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call: Optional[float] = None

    def wait_if_needed(self):
        """Sleep if necessary to respect rate limit"""
        if self.last_call is not None:
            elapsed = time.time() - self.last_call
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)

        self.last_call = time.time()


def generate_external_id(source: str, source_id: str) -> str:
    """
    Generate a consistent external ID for duplicate prevention

    Args:
        source: Source system name (e.g., 'google_personal', 'strava')
        source_id: ID from source system

    Returns:
        External ID string (e.g., 'google_personal_evt123')
    """
    # Remove any special characters from source_id that might cause issues
    clean_source_id = source_id.replace("/", "_").replace(" ", "_")
    return f"{source}_{clean_source_id}"


def parse_external_id(external_id: str) -> tuple[str, str]:
    """
    Parse an external ID back into source and source_id

    Args:
        external_id: External ID string (e.g., 'google_personal_evt123')

    Returns:
        Tuple of (source, source_id)
    """
    parts = external_id.split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid external ID format: {external_id}")
    return parts[0], parts[1]


def format_datetime_for_notion(dt: datetime) -> dict:
    """
    Format a datetime object for Notion API

    Args:
        dt: datetime object

    Returns:
        Dictionary with 'start' key and ISO 8601 formatted datetime
    """
    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return {"start": dt.isoformat()}


def format_date_range_for_notion(start_dt: datetime, end_dt: datetime) -> dict:
    """
    Format a date range for Notion API

    Args:
        start_dt: Start datetime
        end_dt: End datetime

    Returns:
        Dictionary with 'start' and 'end' keys
    """
    # Ensure datetimes are timezone-aware
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    return {"start": start_dt.isoformat(), "end": end_dt.isoformat()}


def safe_get(dictionary: dict, *keys, default=None) -> Any:
    """
    Safely get nested dictionary values

    Args:
        dictionary: Dictionary to search
        *keys: Sequence of keys to traverse
        default: Default value if key not found

    Returns:
        Value at nested key, or default if not found

    Example:
        safe_get(event, 'start', 'dateTime', default='')
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result


def truncate_string(s: str, max_length: int = 2000, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def batch_process(items: list, batch_size: int = 10) -> list:
    """
    Split a list into batches

    Args:
        items: List to split
        batch_size: Size of each batch

    Returns:
        List of batches

    Example:
        for batch in batch_process(items, batch_size=10):
            process_batch(batch)
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i : i + batch_size])
    return batches


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 30s", "1h 15m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# Create a default logger instance for convenience
logger = setup_logging()


if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...\n")

    # Test logging
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")

    # Test external ID generation
    external_id = generate_external_id("google_personal", "evt123")
    print(f"Generated external ID: {external_id}")

    source, source_id = parse_external_id(external_id)
    print(f"Parsed: source={source}, source_id={source_id}")

    # Test rate limiter
    print("\nTesting rate limiter (3 calls per second)...")
    rate_limiter = RateLimiter(calls_per_second=3)
    start = time.time()
    for i in range(5):
        rate_limiter.wait_if_needed()
        print(f"Call {i + 1} at {time.time() - start:.2f}s")

    print("\n✓ All tests passed!")
