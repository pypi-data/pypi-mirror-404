"""Tests for retry module.

Uses freezegun for time-sensitive circuit breaker tests to avoid real delays.
"""

from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from mysql_to_sheets.core.exceptions import (
    CircuitOpenError,
    DatabaseError,
    RetryExhaustedError,
)
from mysql_to_sheets.core.retry import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RetryConfig,
    get_circuit_breaker,
    is_retryable_mysql_error,
    is_retryable_sheets_error,
    reset_circuit_breakers,
    retry,
)


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)

        assert config.calculate_delay(0) == 1.0  # 1 * 2^0 = 1
        assert config.calculate_delay(1) == 2.0  # 1 * 2^1 = 2
        assert config.calculate_delay(2) == 4.0  # 1 * 2^2 = 4
        assert config.calculate_delay(3) == 8.0  # 1 * 2^3 = 8

    def test_calculate_delay_max_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(base_delay=10.0, max_delay=30.0, jitter=False)

        assert config.calculate_delay(5) == 30.0  # Would be 320, capped at 30

    def test_calculate_delay_jitter(self):
        """Test jitter adds randomness to delay."""
        config = RetryConfig(base_delay=1.0, jitter=True)

        delays = [config.calculate_delay(0) for _ in range(10)]

        # With jitter, delays should vary
        assert len(set(delays)) > 1


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def setup_method(self):
        """Reset circuit breakers before each test."""
        reset_circuit_breakers()

    def test_initial_state_closed(self):
        """Test circuit starts in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed() is True
        assert cb.is_open() is False

    def test_allow_request_when_closed(self):
        """Test requests are allowed when circuit is closed."""
        cb = CircuitBreaker()
        assert cb.allow_request() is True

    def test_opens_after_failure_threshold(self):
        """Test circuit opens after reaching failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        cb.record_failure()
        cb.record_failure()
        assert cb.is_closed() is True

        cb.record_failure()  # Third failure triggers open
        assert cb.is_open() is True
        assert cb.allow_request() is False

    def test_success_resets_failure_count(self):
        """Test successful call resets failure counter."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Reset counter

        cb.record_failure()
        cb.record_failure()
        assert cb.is_closed() is True  # Still closed, counter was reset

    def test_half_open_after_timeout(self):
        """Test circuit transitions to half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=60,  # 60 seconds
        )
        cb = CircuitBreaker(config)

        with freeze_time("2024-01-15 10:00:00") as frozen_time:
            cb.record_failure()  # Open circuit
            assert cb.is_open() is True

            # Move time forward past recovery timeout
            frozen_time.move_to("2024-01-15 10:01:01")  # 61 seconds later

            assert cb.state == CircuitState.HALF_OPEN
            assert cb.allow_request() is True

    def test_half_open_closes_on_success(self):
        """Test circuit closes after successes in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=60,  # 60 seconds
            success_threshold=2,
        )
        cb = CircuitBreaker(config)

        with freeze_time("2024-01-15 10:00:00") as frozen_time:
            cb.record_failure()  # Open circuit

            # Move time forward past recovery timeout
            frozen_time.move_to("2024-01-15 10:01:01")

            _ = cb.state  # Trigger state transition check

            cb.record_success()
            assert cb.state == CircuitState.HALF_OPEN

            cb.record_success()  # Second success closes circuit
            assert cb.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        """Test circuit reopens on failure in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=60,  # 60 seconds
        )
        cb = CircuitBreaker(config)

        with freeze_time("2024-01-15 10:00:00") as frozen_time:
            cb.record_failure()  # Open circuit

            # Move time forward past recovery timeout
            frozen_time.move_to("2024-01-15 10:01:01")

            _ = cb.state  # Trigger state transition
            cb.record_failure()  # Fail in half-open

            assert cb.is_open() is True

    def test_reset(self):
        """Test reset restores initial state."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config)

        cb.record_failure()  # Open circuit
        assert cb.is_open() is True

        cb.reset()
        assert cb.is_closed() is True

    def test_get_circuit_breaker_singleton(self):
        """Test get_circuit_breaker returns same instance for same name."""
        cb1 = get_circuit_breaker("test")
        cb2 = get_circuit_breaker("test")

        assert cb1 is cb2

    def test_get_circuit_breaker_different_names(self):
        """Test different names return different instances."""
        cb1 = get_circuit_breaker("mysql")
        cb2 = get_circuit_breaker("sheets")

        assert cb1 is not cb2


class TestRetryDecorator:
    """Tests for retry decorator."""

    def setup_method(self):
        """Reset circuit breakers before each test."""
        reset_circuit_breakers()

    def test_success_no_retry(self):
        """Test successful function doesn't retry."""
        call_count = 0

        @retry(RetryConfig(max_attempts=3))
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test function is retried on retryable exception."""
        call_count = 0

        @retry(RetryConfig(max_attempts=3, base_delay=0.01))
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseError("Transient error")
            return "success"

        result = fail_twice()

        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """Test RetryExhaustedError raised when all attempts fail."""

        @retry(RetryConfig(max_attempts=3, base_delay=0.01))
        def always_fail():
            raise DatabaseError("Always fails")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_fail()

        assert exc_info.value.attempts == 3
        assert "Always fails" in str(exc_info.value.last_error)

    def test_non_retryable_exception(self):
        """Test non-retryable exceptions are not retried."""
        call_count = 0

        @retry(RetryConfig(max_attempts=3))
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            raise_value_error()

        assert call_count == 1  # No retries

    def test_circuit_breaker_integration(self):
        """Test retry with circuit breaker."""
        cb = get_circuit_breaker("test_integration")

        @retry(RetryConfig(max_attempts=2, base_delay=0.01), circuit_breaker=cb)
        def sometimes_fail():
            raise DatabaseError("Failed")

        # Exhaust retries
        with pytest.raises(RetryExhaustedError):
            sometimes_fail()

    def test_circuit_open_fails_fast(self):
        """Test requests fail fast when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config, name="fast_fail")
        cb.record_failure()  # Open circuit

        @retry(circuit_breaker=cb)
        def some_func():
            return "success"

        with pytest.raises(CircuitOpenError):
            some_func()

    def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        callbacks = []

        def on_retry(exc, attempt):
            callbacks.append((str(exc), attempt))

        call_count = 0

        @retry(
            RetryConfig(max_attempts=3, base_delay=0.01),
            on_retry=on_retry,
        )
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseError(f"Attempt {call_count}")
            return "success"

        result = fail_twice()

        assert result == "success"
        assert len(callbacks) == 2
        assert callbacks[0][1] == 0  # First retry
        assert callbacks[1][1] == 1  # Second retry


class TestRetryableErrorChecks:
    """Tests for error retryability checks."""

    def test_retryable_mysql_connection_refused(self):
        """Test connection refused is retryable."""
        error = Exception("Connection refused")
        assert is_retryable_mysql_error(error) is True

    def test_retryable_mysql_timeout(self):
        """Test timeout is retryable."""
        error = Exception("Operation timed out")
        assert is_retryable_mysql_error(error) is True

    def test_retryable_mysql_deadlock(self):
        """Test deadlock is retryable."""
        error = Exception("Deadlock found")
        assert is_retryable_mysql_error(error) is True

    def test_non_retryable_mysql_syntax(self):
        """Test syntax error is not retryable."""
        error = Exception("Syntax error in SQL")
        assert is_retryable_mysql_error(error) is False

    def test_retryable_sheets_rate_limit(self):
        """Test rate limit error is retryable."""
        error = Exception("Rate limit exceeded")
        assert is_retryable_sheets_error(error) is True

    def test_retryable_sheets_429(self):
        """Test 429 error is retryable."""
        error = Exception("Error 429: Too many requests")
        assert is_retryable_sheets_error(error) is True

    def test_retryable_sheets_500(self):
        """Test 500 error is retryable."""
        error = Exception("500 Internal Server Error")
        assert is_retryable_sheets_error(error) is True

    def test_non_retryable_sheets_not_found(self):
        """Test not found error is not retryable."""
        error = Exception("Spreadsheet not found")
        assert is_retryable_sheets_error(error) is False
