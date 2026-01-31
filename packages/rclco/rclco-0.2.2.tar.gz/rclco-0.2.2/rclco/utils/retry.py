"""Retry utilities for handling transient failures."""

import time
from dataclasses import dataclass
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

from rclco.core.logging import get_logger

logger = get_logger("utils.retry")

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including the first)
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff (delay *= base after each retry)
        exceptions: Tuple of exception types to retry on
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    exceptions: tuple[type[Exception], ...] = (Exception,)


def retry(
    config: RetryConfig | None = None,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that retries a function on failure with exponential backoff.

    Can be used with a RetryConfig object or with individual parameters.

    Args:
        config: RetryConfig object with all retry settings
        max_attempts: Maximum number of attempts (overrides config)
        base_delay: Initial delay in seconds (overrides config)
        exceptions: Exception types to retry on (overrides config)

    Returns:
        Decorated function that will retry on failure

    Example:
        @retry(max_attempts=3, base_delay=1.0)
        def fetch_data():
            return api.get("data")

        @retry(config=RetryConfig(max_attempts=5, exceptions=(ConnectionError,)))
        def connect_to_db():
            return db.connect()
    """
    # Build effective config
    effective_config = config or RetryConfig()

    if max_attempts is not None:
        effective_config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=effective_config.base_delay,
            max_delay=effective_config.max_delay,
            exponential_base=effective_config.exponential_base,
            exceptions=effective_config.exceptions,
        )

    if base_delay is not None:
        effective_config = RetryConfig(
            max_attempts=effective_config.max_attempts,
            base_delay=base_delay,
            max_delay=effective_config.max_delay,
            exponential_base=effective_config.exponential_base,
            exceptions=effective_config.exceptions,
        )

    if exceptions is not None:
        effective_config = RetryConfig(
            max_attempts=effective_config.max_attempts,
            base_delay=effective_config.base_delay,
            max_delay=effective_config.max_delay,
            exponential_base=effective_config.exponential_base,
            exceptions=exceptions,
        )

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            delay = effective_config.base_delay

            for attempt in range(1, effective_config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except effective_config.exceptions as e:
                    last_exception = e

                    if attempt == effective_config.max_attempts:
                        logger.warning(
                            f"{func.__name__} failed after {attempt} attempts: {e}"
                        )
                        raise

                    logger.debug(
                        f"{func.__name__} attempt {attempt} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)
                    delay = min(
                        delay * effective_config.exponential_base,
                        effective_config.max_delay,
                    )

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error")

        return wrapper

    return decorator
