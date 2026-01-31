"""Timeout configuration and handling utilities.

This module provides configurable timeout settings for database
connections and API calls.
"""

import signal
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from types import FrameType
from typing import Any

from mysql_to_sheets.core.exceptions import TimeoutError


@dataclass
class TimeoutConfig:
    """Configuration for operation timeouts.

    Attributes:
        db_connect_timeout: MySQL connection timeout in seconds.
        db_read_timeout: MySQL read timeout in seconds.
        db_write_timeout: MySQL write timeout in seconds.
        sheets_timeout: Google Sheets API timeout in seconds.
        http_timeout: General HTTP request timeout in seconds.
    """

    db_connect_timeout: int = 10
    db_read_timeout: int = 300  # 5 minutes for large queries
    db_write_timeout: int = 60
    sheets_timeout: int = 60
    http_timeout: int = 30

    def get_mysql_connect_args(self) -> dict[str, int]:
        """Get MySQL connector connection timeout arguments.

        Returns:
            Dict with timeout parameters for mysql.connector.connect()
        """
        return {
            "connection_timeout": self.db_connect_timeout,
        }

    def get_mysql_socket_args(self) -> dict[str, int]:
        """Get MySQL connector socket timeout arguments.

        These are set after connection for read/write operations.

        Returns:
            Dict with read_timeout and write_timeout.
        """
        return {
            "read_timeout": self.db_read_timeout,
            "write_timeout": self.db_write_timeout,
        }


class TimeoutHandler:
    """Context manager for enforcing operation timeouts.

    Uses SIGALRM on Unix systems for timeout enforcement.
    On Windows, this is a no-op (timeout not enforced).

    Example:
        with TimeoutHandler(30, "Database query"):
            cursor.execute(query)
    """

    def __init__(
        self,
        timeout_seconds: int,
        operation_name: str = "Operation",
    ) -> None:
        """Initialize timeout handler.

        Args:
            timeout_seconds: Timeout duration in seconds.
            operation_name: Name of operation for error messages.
        """
        self.timeout_seconds = timeout_seconds
        self.operation_name = operation_name
        self._old_handler: Callable[[int, FrameType | None], Any] | int | None = None

    def _timeout_handler(self, signum: int, frame: object) -> None:
        """Signal handler for SIGALRM."""
        raise TimeoutError(
            message=f"{self.operation_name} timed out after {self.timeout_seconds} seconds",
            timeout_seconds=self.timeout_seconds,
            operation=self.operation_name,
        )

    def __enter__(self) -> "TimeoutHandler":
        """Set up timeout alarm."""
        # Only works on Unix-like systems
        if hasattr(signal, "SIGALRM"):
            self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.timeout_seconds)
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: object) -> None:
        """Cancel timeout alarm."""
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            if self._old_handler is not None:
                signal.signal(signal.SIGALRM, self._old_handler)


@contextmanager
def timeout(
    seconds: int,
    operation: str = "Operation",
) -> Generator[None, None, None]:
    """Context manager for enforcing timeouts.

    Args:
        seconds: Timeout duration in seconds.
        operation: Name of operation for error messages.

    Yields:
        None

    Raises:
        TimeoutError: If operation exceeds timeout.

    Example:
        with timeout(30, "Database query"):
            cursor.execute(query)
    """
    handler = TimeoutHandler(seconds, operation)
    with handler:
        yield


def get_default_timeout_config() -> TimeoutConfig:
    """Get default timeout configuration.

    Returns:
        TimeoutConfig with default values.
    """
    return TimeoutConfig()


def create_timeout_config(
    db_connect_timeout: int | None = None,
    db_read_timeout: int | None = None,
    db_write_timeout: int | None = None,
    sheets_timeout: int | None = None,
    http_timeout: int | None = None,
) -> TimeoutConfig:
    """Create a timeout configuration with custom values.

    Args:
        db_connect_timeout: MySQL connection timeout.
        db_read_timeout: MySQL read timeout.
        db_write_timeout: MySQL write timeout.
        sheets_timeout: Sheets API timeout.
        http_timeout: HTTP request timeout.

    Returns:
        TimeoutConfig with specified values or defaults.
    """
    defaults = get_default_timeout_config()
    return TimeoutConfig(
        db_connect_timeout=db_connect_timeout or defaults.db_connect_timeout,
        db_read_timeout=db_read_timeout or defaults.db_read_timeout,
        db_write_timeout=db_write_timeout or defaults.db_write_timeout,
        sheets_timeout=sheets_timeout or defaults.sheets_timeout,
        http_timeout=http_timeout or defaults.http_timeout,
    )
