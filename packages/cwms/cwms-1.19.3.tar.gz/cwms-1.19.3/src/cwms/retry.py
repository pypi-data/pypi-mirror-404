"""Retry utilities with exponential backoff for transient failures."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])


class TransientError(Exception):
    """Exception indicating a transient failure that should trigger retry.

    Use this to wrap errors that are likely to succeed on retry,
    such as network timeouts, rate limits, or temporary service unavailability.
    """

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
        retry_after: float | None = None,
    ) -> None:
        """Initialize TransientError.

        Args:
            message: Error description
            original_error: The underlying exception that caused this error
            retry_after: Optional suggested delay before retry (seconds)
        """
        super().__init__(message)
        self.original_error = original_error
        self.retry_after = retry_after


class PermanentError(Exception):
    """Exception indicating a permanent failure that should NOT retry.

    Use this for errors that will not succeed on retry, such as
    invalid API keys, malformed requests, or resource not found.
    """

    def __init__(
        self,
        message: str,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize PermanentError.

        Args:
            message: Error description
            original_error: The underlying exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including initial)
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        retryable_exceptions: Tuple of exception types that should trigger retry
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (TransientError, TimeoutError, ConnectionError, OSError)
    )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: initial_delay * (base ^ attempt)
        delay = self.initial_delay * (self.exponential_base**attempt)

        # Cap at maximum delay
        delay = min(delay, self.max_delay)

        # Add jitter (±25%) to prevent thundering herd
        if self.jitter:
            jitter_range = delay * 0.25
            delay = delay + random.uniform(-jitter_range, jitter_range)  # noqa: S311

        return max(0.0, delay)


# Default configurations for different use cases
DEFAULT_RETRY_CONFIG = RetryConfig()

API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

AGGRESSIVE_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=0.5,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)


def with_retry(
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> Callable[[F], F]:
    """Decorator that adds retry with exponential backoff to a function.

    Args:
        config: Retry configuration (uses DEFAULT_RETRY_CONFIG if not provided)
        on_retry: Optional callback called before each retry with
                  (attempt_number, exception, delay)

    Returns:
        Decorator function

    Example:
        @with_retry(API_RETRY_CONFIG)
        def call_api():
            # This will retry up to 3 times with exponential backoff
            return requests.get("https://api.example.com")
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except PermanentError:
                    # Don't retry permanent errors
                    raise

                except config.retryable_exceptions as e:
                    last_exception = e

                    # Check if we have more attempts
                    if attempt >= config.max_attempts - 1:
                        logger.warning(
                            "All %d retry attempts exhausted for %s",
                            config.max_attempts,
                            func.__name__,
                        )
                        raise

                    # Calculate delay
                    if isinstance(e, TransientError) and e.retry_after is not None:
                        delay = e.retry_after
                    else:
                        delay = config.calculate_delay(attempt)

                    # Log retry attempt
                    logger.info(
                        "Attempt %d/%d for %s failed: %s. Retrying in %.1fs...",
                        attempt + 1,
                        config.max_attempts,
                        func.__name__,
                        str(e),
                        delay,
                    )

                    # Call retry callback if provided
                    if on_retry is not None:
                        on_retry(attempt + 1, e, delay)

                    # Wait before retry
                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception is not None:
                raise last_exception
            raise RuntimeError(f"Unexpected retry failure in {func.__name__}")

        return wrapper  # type: ignore[return-value]

    return decorator


def is_transient_http_error(status_code: int) -> bool:
    """Check if an HTTP status code indicates a transient error.

    Args:
        status_code: HTTP status code

    Returns:
        True if the error is likely transient and should be retried
    """
    # Rate limiting
    if status_code == 429:
        return True

    # Server errors (5xx) are often transient
    if 500 <= status_code < 600:
        return True

    # Request timeout
    return status_code == 408


def classify_api_error(error: Exception) -> Exception:
    """Classify an API error as transient or permanent.

    This helper function examines common API error types and wraps them
    appropriately for the retry system.

    Args:
        error: The original exception

    Returns:
        Either a TransientError or PermanentError wrapping the original
    """
    error_str = str(error).lower()

    # Check for rate limiting indicators
    rate_limit_indicators = ["rate limit", "rate_limit", "too many requests", "429"]
    if any(indicator in error_str for indicator in rate_limit_indicators):
        return TransientError(
            f"Rate limited: {error}",
            original_error=error,
            retry_after=60.0,  # Default 60s for rate limits
        )

    # Check for timeout indicators
    timeout_indicators = ["timeout", "timed out", "deadline exceeded"]
    if any(indicator in error_str for indicator in timeout_indicators):
        return TransientError(
            f"Request timed out: {error}",
            original_error=error,
        )

    # Check for connection issues
    connection_indicators = ["connection", "network", "unreachable", "unavailable"]
    if any(indicator in error_str for indicator in connection_indicators):
        return TransientError(
            f"Connection error: {error}",
            original_error=error,
        )

    # Check for server errors
    server_error_indicators = ["500", "502", "503", "504", "internal server error"]
    if any(indicator in error_str for indicator in server_error_indicators):
        return TransientError(
            f"Server error: {error}",
            original_error=error,
        )

    # Check for permanent error indicators
    permanent_indicators = [
        "invalid api key",
        "invalid_api_key",
        "authentication",
        "unauthorized",
        "forbidden",
        "not found",
        "invalid request",
        "bad request",
        "model not found",
    ]
    if any(indicator in error_str for indicator in permanent_indicators):
        return PermanentError(
            f"Permanent error: {error}",
            original_error=error,
        )

    # Default to transient for unknown errors (safer to retry)
    return TransientError(
        f"Unknown error (treating as transient): {error}",
        original_error=error,
    )


def retry_with_fallback(
    primary_func: Callable[[], Any],
    fallback_func: Callable[[], Any],
    config: RetryConfig | None = None,
    fallback_on_exhaustion: bool = True,
) -> Any:
    """Execute a function with retry, falling back to alternative on failure.

    This is useful when you have a primary method (e.g., API call) and a
    fallback (e.g., cached value or simpler computation).

    Args:
        primary_func: Primary function to execute
        fallback_func: Fallback function if primary fails
        config: Retry configuration for primary function
        fallback_on_exhaustion: If True, use fallback after all retries fail.
                                If False, raise the last exception.

    Returns:
        Result from either primary or fallback function

    Example:
        result = retry_with_fallback(
            primary_func=lambda: api.get_embeddings(text),
            fallback_func=lambda: [],  # Return empty embeddings
        )
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    @with_retry(config)
    def wrapped_primary() -> Any:
        return primary_func()

    try:
        return wrapped_primary()
    except Exception as e:
        if fallback_on_exhaustion:
            logger.warning(
                "Primary function failed after retries, using fallback: %s",
                str(e),
            )
            return fallback_func()
        raise
