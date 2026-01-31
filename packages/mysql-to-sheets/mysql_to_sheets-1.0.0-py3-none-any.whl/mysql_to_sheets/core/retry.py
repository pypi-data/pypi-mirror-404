"""Retry decorator and circuit breaker for resilient operations.

This module provides retry logic with exponential backoff and a circuit breaker
pattern to prevent cascading failures when external services are down.

Extraction target: ``tla-retry`` standalone package.
Depends on ``tla-errors`` (mysql_to_sheets.core.exceptions).
See STANDALONE_PROJECTS.md for extraction details.
"""

import functools
import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import NamedTuple, ParamSpec, TypeVar

from mysql_to_sheets.core.exceptions import (
    CircuitOpenError,
    DatabaseError,
    RetryExhaustedError,
    SheetsError,
)
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (including initial).
        base_delay: Base delay in seconds between retries.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delays.
        retryable_exceptions: Exception types that should trigger retry.
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (DatabaseError, SheetsError, ConnectionError, TimeoutError)
    )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Uses exponential backoff with optional jitter.

        Args:
            attempt: The attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        delay = self.base_delay * (self.exponential_base**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add jitter of ±25% to prevent thundering herd
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.0, delay)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Number of failures before opening circuit.
        recovery_timeout: Time to wait before trying half-open state.
        half_open_max_calls: Max calls to allow in half-open state.
        success_threshold: Successes needed in half-open to close circuit.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """Circuit breaker implementation for external service calls.

    The circuit breaker prevents cascading failures by failing fast
    when a service is detected as unhealthy.

    States:
    - CLOSED: Normal operation, all calls go through
    - OPEN: Service is down, calls fail immediately
    - HALF_OPEN: Testing recovery, limited calls allowed

    Attributes:
        config: Circuit breaker configuration.
        name: Identifier for this circuit breaker.
    """

    def __init__(
        self,
        config: CircuitBreakerConfig | None = None,
        name: str = "default",
    ) -> None:
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration.
            name: Identifier for logging and metrics.
        """
        self.config = config or CircuitBreakerConfig()
        self.name = name
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery timeout."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
                if elapsed >= self.config.recovery_timeout:
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
        return self._state

    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing all calls)."""
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        """Check if circuit is open (rejecting all calls)."""
        return self.state == CircuitState.OPEN

    def allow_request(self) -> bool:
        """Check if a request should be allowed through.

        Returns:
            True if request is allowed, False if should be rejected.
        """
        state = self.state  # This checks for timeout transition

        if state == CircuitState.CLOSED:
            return True

        if state == CircuitState.OPEN:
            return False

        # HALF_OPEN: Allow limited calls
        if self._half_open_calls < self.config.half_open_max_calls:
            self._half_open_calls += 1
            return True
        return False

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                logger.info(f"Circuit '{self.name}' recovered, closing circuit")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now(timezone.utc)

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            logger.warning(f"Circuit '{self.name}' failure in HALF_OPEN, reopening")
            self._state = CircuitState.OPEN
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.config.failure_threshold:
                logger.warning(f"Circuit '{self.name}' opened after {self._failure_count} failures")
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


# Global circuit breakers for different services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig | None = None,
) -> CircuitBreaker:
    """Get or create a named circuit breaker.

    Args:
        name: Unique identifier for the circuit breaker.
        config: Optional configuration (only used on creation).

    Returns:
        Circuit breaker instance.
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(config, name)
    return _circuit_breakers[name]


def reset_circuit_breakers() -> None:
    """Reset all circuit breakers (useful for testing)."""
    for cb in _circuit_breakers.values():
        cb.reset()
    _circuit_breakers.clear()


def retry(
    config: RetryConfig | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for retrying operations with exponential backoff.

    Retries the decorated function when retryable exceptions occur,
    using exponential backoff between attempts.

    Args:
        config: Retry configuration. Uses defaults if not provided.
        circuit_breaker: Optional circuit breaker for fail-fast behavior.
        on_retry: Optional callback called before each retry with (exception, attempt).

    Returns:
        Decorated function.

    Example:
        @retry(RetryConfig(max_attempts=3, base_delay=1.0))
        def fetch_data():
            ...

        @retry(circuit_breaker=get_circuit_breaker("mysql"))
        def connect_to_database():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Check circuit breaker first
            if circuit_breaker is not None and not circuit_breaker.allow_request():
                raise CircuitOpenError(
                    message=f"Circuit breaker '{circuit_breaker.name}' is open",
                    circuit_name=circuit_breaker.name,
                )

            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)

                    # Record success for circuit breaker
                    if circuit_breaker is not None:
                        circuit_breaker.record_success()

                    return result

                except config.retryable_exceptions as e:
                    last_exception = e

                    # Record failure for circuit breaker
                    if circuit_breaker is not None:
                        circuit_breaker.record_failure()

                    # Check if we have more attempts
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)

                        # Honor retry_after from rate-limited SheetsError
                        retry_after = getattr(e, "retry_after", None)
                        if retry_after is not None and retry_after > delay:
                            delay = min(retry_after, config.max_delay * 10)

                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        if on_retry is not None:
                            on_retry(e, attempt)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}"
                        )

                except Exception:
                    # Non-retryable exception, fail immediately
                    if circuit_breaker is not None:
                        circuit_breaker.record_failure()
                    raise

            # All retries exhausted
            raise RetryExhaustedError(
                message=f"Operation failed after {config.max_attempts} attempts",
                attempts=config.max_attempts,
                last_error=last_exception,
            )

        return wrapper

    return decorator


def retry_async(
    config: RetryConfig | None = None,
    circuit_breaker: CircuitBreaker | None = None,
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Async version of retry decorator.

    Same behavior as retry() but for async functions.

    Args:
        config: Retry configuration. Uses defaults if not provided.
        circuit_breaker: Optional circuit breaker for fail-fast behavior.
        on_retry: Optional callback called before each retry.

    Returns:
        Decorated async function.
    """
    import asyncio

    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Check circuit breaker first
            if circuit_breaker is not None and not circuit_breaker.allow_request():
                raise CircuitOpenError(
                    message=f"Circuit breaker '{circuit_breaker.name}' is open",
                    circuit_name=circuit_breaker.name,
                )

            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    result = await func(*args, **kwargs)  # type: ignore[misc]

                    if circuit_breaker is not None:
                        circuit_breaker.record_success()

                    return result  # type: ignore[no-any-return]

                except config.retryable_exceptions as e:
                    last_exception = e

                    if circuit_breaker is not None:
                        circuit_breaker.record_failure()

                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Async attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        if on_retry is not None:
                            on_retry(e, attempt)

                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} async attempts failed for {func.__name__}"
                        )

                except Exception:
                    if circuit_breaker is not None:
                        circuit_breaker.record_failure()
                    raise

            raise RetryExhaustedError(
                message=f"Async operation failed after {config.max_attempts} attempts",
                attempts=config.max_attempts,
                last_error=last_exception,
            )

        return wrapper  # type: ignore[return-value]

    return decorator


def is_retryable_mysql_error(error: Exception) -> bool:
    """Check if a MySQL error is retryable (transient).

    Retryable errors are typically connection issues or timeouts
    that may succeed on retry.

    Args:
        error: The exception to check.

    Returns:
        True if the error is retryable.
    """
    # mysql.connector error codes for transient errors
    RETRYABLE_ERROR_CODES = {
        1040,  # Too many connections
        1205,  # Lock wait timeout
        1213,  # Deadlock
        2003,  # Can't connect to server
        2006,  # MySQL server has gone away
        2013,  # Lost connection during query
        2055,  # Lost connection to MySQL server
    }

    error_msg = str(error).lower()

    # Check for specific patterns
    if "connection refused" in error_msg:
        return True
    if "timed out" in error_msg:
        return True
    if "too many connections" in error_msg:
        return True
    if "deadlock" in error_msg:
        return True
    if "lost connection" in error_msg:
        return True

    # Check error code if available
    if hasattr(error, "errno") and error.errno in RETRYABLE_ERROR_CODES:
        return True

    return False


def is_retryable_sheets_error(error: Exception) -> bool:
    """Check if a Google Sheets API error is retryable.

    Retryable errors are typically rate limits or temporary failures.

    Args:
        error: The exception to check.

    Returns:
        True if the error is retryable.
    """
    error_msg = str(error).lower()

    # Rate limit errors (429)
    if "rate limit" in error_msg:
        return True
    if "quota exceeded" in error_msg:
        return True
    if "429" in error_msg:
        return True

    # Temporary server errors (5xx)
    if "500" in error_msg or "502" in error_msg or "503" in error_msg:
        return True
    if "internal server error" in error_msg:
        return True
    if "service unavailable" in error_msg:
        return True

    return False


class RateLimitInfo(NamedTuple):
    """Information about a rate limit error.

    Attributes:
        is_rate_limited: Whether the error is a rate limit.
        retry_after: Seconds to wait before retrying (if available).
        quota_type: Type of quota exceeded (if available).
    """

    is_rate_limited: bool
    retry_after: float | None
    quota_type: str | None


def parse_sheets_rate_limit(error: Exception) -> RateLimitInfo:
    """Parse rate limit information from a Google Sheets API error.

    Extracts retry timing and quota type from error messages.

    Args:
        error: The exception to parse.

    Returns:
        RateLimitInfo with parsed rate limit details.

    Example:
        >>> error = gspread.exceptions.APIError({"error": {"code": 429}})
        >>> info = parse_sheets_rate_limit(error)
        >>> if info.is_rate_limited:
        ...     time.sleep(info.retry_after or 60)
    """
    error_str = str(error)
    error_lower = error_str.lower()

    # Check if this is a rate limit error
    is_rate_limited = any(
        [
            "429" in error_str,
            "rate limit" in error_lower,
            "quota exceeded" in error_lower,
            "too many requests" in error_lower,
            "resource exhausted" in error_lower,
        ]
    )

    if not is_rate_limited:
        return RateLimitInfo(
            is_rate_limited=False,
            retry_after=None,
            quota_type=None,
        )

    # Try to extract retry-after from error message
    retry_after: float | None = None

    # Look for "Retry-After: X" header or similar patterns
    retry_patterns = [
        r"retry[- ]after[:\s]+(\d+)",
        r"wait[:\s]+(\d+)\s*(?:second|sec|s)",
        r"(\d+)\s*(?:second|sec|s)\s*(?:before|until)",
    ]

    for pattern in retry_patterns:
        match = re.search(pattern, error_lower)
        if match:
            try:
                retry_after = float(match.group(1))
                break
            except ValueError:
                pass

    # If no retry-after found, use default based on quota type
    quota_type: str | None = None

    if "per minute" in error_lower or "per-minute" in error_lower:
        quota_type = "per_minute"
        if retry_after is None:
            retry_after = 60.0
    elif "per user" in error_lower or "per-user" in error_lower:
        quota_type = "per_user"
        if retry_after is None:
            retry_after = 60.0
    elif "daily" in error_lower or "per day" in error_lower:
        quota_type = "daily"
        if retry_after is None:
            retry_after = 3600.0  # 1 hour default for daily quota
    elif "read" in error_lower:
        quota_type = "read"
        if retry_after is None:
            retry_after = 100.0
    elif "write" in error_lower:
        quota_type = "write"
        if retry_after is None:
            retry_after = 100.0
    else:
        quota_type = "unknown"
        if retry_after is None:
            retry_after = 60.0  # Default fallback

    return RateLimitInfo(
        is_rate_limited=True,
        retry_after=retry_after,
        quota_type=quota_type,
    )
