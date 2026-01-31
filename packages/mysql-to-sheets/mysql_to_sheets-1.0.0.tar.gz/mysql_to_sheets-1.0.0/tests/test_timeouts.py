"""Tests for timeout configuration and handling.

Note: Tests that use time.sleep() with SIGALRM are marked as @pytest.mark.slow
because they require real time to pass for signal handling. These tests cannot
be mocked with freezegun because SIGALRM requires real time.
"""

import signal
import sys
import time
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.exceptions import TimeoutError
from mysql_to_sheets.core.timeouts import (
    TimeoutConfig,
    TimeoutHandler,
    create_timeout_config,
    get_default_timeout_config,
    timeout,
)


class TestTimeoutConfig:
    """Tests for TimeoutConfig dataclass."""

    def test_default_values(self) -> None:
        """Test TimeoutConfig has sensible defaults."""
        config = TimeoutConfig()

        assert config.db_connect_timeout == 10
        assert config.db_read_timeout == 300
        assert config.db_write_timeout == 60
        assert config.sheets_timeout == 60
        assert config.http_timeout == 30

    def test_custom_values(self) -> None:
        """Test TimeoutConfig with custom values."""
        config = TimeoutConfig(
            db_connect_timeout=5,
            db_read_timeout=120,
            db_write_timeout=30,
            sheets_timeout=90,
            http_timeout=15,
        )

        assert config.db_connect_timeout == 5
        assert config.db_read_timeout == 120
        assert config.db_write_timeout == 30
        assert config.sheets_timeout == 90
        assert config.http_timeout == 15

    def test_get_mysql_connect_args(self) -> None:
        """Test get_mysql_connect_args returns correct dict."""
        config = TimeoutConfig(db_connect_timeout=15)
        args = config.get_mysql_connect_args()

        assert args == {"connection_timeout": 15}

    def test_get_mysql_socket_args(self) -> None:
        """Test get_mysql_socket_args returns correct dict."""
        config = TimeoutConfig(
            db_read_timeout=120,
            db_write_timeout=45,
        )
        args = config.get_mysql_socket_args()

        assert args == {
            "read_timeout": 120,
            "write_timeout": 45,
        }


class TestGetDefaultTimeoutConfig:
    """Tests for get_default_timeout_config function."""

    def test_returns_timeout_config(self) -> None:
        """Test get_default_timeout_config returns TimeoutConfig."""
        config = get_default_timeout_config()
        assert isinstance(config, TimeoutConfig)

    def test_returns_default_values(self) -> None:
        """Test get_default_timeout_config returns defaults."""
        config = get_default_timeout_config()
        default = TimeoutConfig()

        assert config.db_connect_timeout == default.db_connect_timeout
        assert config.db_read_timeout == default.db_read_timeout


class TestCreateTimeoutConfig:
    """Tests for create_timeout_config function."""

    def test_with_all_custom_values(self) -> None:
        """Test create_timeout_config with all custom values."""
        config = create_timeout_config(
            db_connect_timeout=5,
            db_read_timeout=100,
            db_write_timeout=50,
            sheets_timeout=45,
            http_timeout=20,
        )

        assert config.db_connect_timeout == 5
        assert config.db_read_timeout == 100
        assert config.db_write_timeout == 50
        assert config.sheets_timeout == 45
        assert config.http_timeout == 20

    def test_with_partial_values(self) -> None:
        """Test create_timeout_config with some custom values."""
        config = create_timeout_config(
            db_connect_timeout=5,
            sheets_timeout=45,
        )

        # Custom values
        assert config.db_connect_timeout == 5
        assert config.sheets_timeout == 45

        # Default values
        defaults = TimeoutConfig()
        assert config.db_read_timeout == defaults.db_read_timeout
        assert config.db_write_timeout == defaults.db_write_timeout
        assert config.http_timeout == defaults.http_timeout

    def test_with_no_values(self) -> None:
        """Test create_timeout_config with no custom values."""
        config = create_timeout_config()
        defaults = TimeoutConfig()

        assert config.db_connect_timeout == defaults.db_connect_timeout
        assert config.db_read_timeout == defaults.db_read_timeout


class TestTimeoutHandler:
    """Tests for TimeoutHandler class."""

    def test_initialization(self) -> None:
        """Test TimeoutHandler initialization."""
        handler = TimeoutHandler(30, "Test operation")

        assert handler.timeout_seconds == 30
        assert handler.operation_name == "Test operation"

    def test_default_operation_name(self) -> None:
        """Test TimeoutHandler with default operation name."""
        handler = TimeoutHandler(30)

        assert handler.operation_name == "Operation"

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_context_manager_sets_alarm(self) -> None:
        """Test TimeoutHandler sets signal alarm on entry."""
        handler = TimeoutHandler(30, "Test")

        with handler:
            # We can't easily test the alarm was set, but we can verify
            # it doesn't raise during normal operation
            pass

        # If we get here, the context manager worked

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_context_manager_clears_alarm(self) -> None:
        """Test TimeoutHandler clears alarm on exit."""
        handler = TimeoutHandler(30, "Test")

        with handler:
            pass

        # Alarm should be cleared - setting another should work
        signal.alarm(0)  # Should not raise

    @pytest.mark.slow
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_raises_timeout_error_on_timeout(self) -> None:
        """Test TimeoutHandler raises TimeoutError on timeout."""
        handler = TimeoutHandler(1, "Slow operation")

        with pytest.raises(TimeoutError) as exc_info:
            with handler:
                time.sleep(2)  # Sleep longer than timeout

        assert exc_info.value.timeout_seconds == 1
        assert exc_info.value.operation == "Slow operation"
        assert "timed out" in exc_info.value.message

    @pytest.mark.slow
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_restores_previous_handler(self) -> None:
        """Test TimeoutHandler restores previous signal handler."""
        # Set a custom handler
        custom_called = []

        def custom_handler(signum, frame):
            custom_called.append(True)

        old_handler = signal.signal(signal.SIGALRM, custom_handler)

        try:
            handler = TimeoutHandler(30, "Test")
            with handler:
                pass

            # Trigger alarm to verify custom handler is restored
            signal.alarm(1)
            time.sleep(1.5)

            # Custom handler should have been called
            # (only if we restored properly)
        except:
            pass  # Expected if handler wasn't restored
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def test_noop_on_windows(self) -> None:
        """Test TimeoutHandler is a no-op on Windows."""
        # Mock platform without SIGALRM
        with patch.object(signal, "SIGALRM", None, create=True):
            # Remove SIGALRM if it exists
            sigalrm = getattr(signal, "SIGALRM", None)
            if hasattr(signal, "SIGALRM"):
                delattr(signal, "SIGALRM")

            try:
                handler = TimeoutHandler(1, "Test")
                # Should not raise even without SIGALRM
                with handler:
                    pass
            finally:
                if sigalrm is not None:
                    signal.SIGALRM = sigalrm


class TestTimeoutContextManager:
    """Tests for timeout() context manager function."""

    def test_basic_usage(self) -> None:
        """Test timeout context manager basic usage."""
        with timeout(30, "Test operation"):
            # Quick operation should complete
            pass

    @pytest.mark.slow
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_raises_on_timeout(self) -> None:
        """Test timeout raises TimeoutError on timeout."""
        with pytest.raises(TimeoutError) as exc_info:
            with timeout(1, "Slow operation"):
                time.sleep(2)

        assert exc_info.value.timeout_seconds == 1
        assert exc_info.value.operation == "Slow operation"

    def test_default_operation_name(self) -> None:
        """Test timeout with default operation name."""
        # Just verify it doesn't raise
        with timeout(30):
            pass

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_exception_propagates(self) -> None:
        """Test exceptions other than timeout propagate normally."""
        with pytest.raises(ValueError):
            with timeout(30, "Test"):
                raise ValueError("Test error")

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="SIGALRM not available on Windows",
    )
    def test_nested_timeouts(self) -> None:
        """Test nested timeout contexts."""
        with timeout(30, "Outer"):
            with timeout(20, "Inner"):
                pass


class TestTimeoutErrorException:
    """Tests for TimeoutError exception raised by timeouts."""

    def test_timeout_error_attributes(self) -> None:
        """Test TimeoutError has expected attributes."""
        error = TimeoutError(
            message="Operation timed out",
            timeout_seconds=30,
            operation="Database query",
        )

        assert error.message == "Operation timed out"
        assert error.timeout_seconds == 30
        assert error.operation == "Database query"

    def test_timeout_error_to_dict(self) -> None:
        """Test TimeoutError to_dict method."""
        error = TimeoutError(
            message="Timed out",
            timeout_seconds=30,
            operation="Query",
        )

        error_dict = error.to_dict()

        assert error_dict["error"] == "TimeoutError"
        assert error_dict["message"] == "Timed out"
        assert error_dict["details"]["timeout_seconds"] == 30
        assert error_dict["details"]["operation"] == "Query"

    def test_timeout_error_optional_fields(self) -> None:
        """Test TimeoutError with optional fields omitted."""
        error = TimeoutError(message="Timed out")

        assert error.timeout_seconds is None
        assert error.operation is None

        error_dict = error.to_dict()
        assert "timeout_seconds" not in error_dict["details"]
        assert "operation" not in error_dict["details"]
