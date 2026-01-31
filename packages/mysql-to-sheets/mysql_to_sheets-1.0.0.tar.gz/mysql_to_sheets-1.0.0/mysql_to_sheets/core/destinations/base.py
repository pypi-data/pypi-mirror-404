"""Base classes and protocols for destination connections.

This module defines the protocol that all destination connections must implement,
along with common data structures used across destination implementations.

Follows the same pattern as core/database/base.py for consistency.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class DestinationConfig:
    """Configuration for destination connections.

    Attributes:
        destination_type: Destination type ('google_sheets', 'excel_online', etc.).
        target_id: Target identifier (Sheet ID, Workbook ID, etc.).
        target_name: Target name (worksheet/table name).
        credentials_file: Path to credentials file (e.g., service_account.json).
        timeout: Operation timeout in seconds.
        options: Additional destination-specific options.
    """

    destination_type: str = "google_sheets"
    target_id: str = ""
    target_name: str = "Sheet1"
    credentials_file: str | None = None
    timeout: int = 60
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class WriteResult:
    """Result of a destination write operation.

    Attributes:
        success: Whether the operation succeeded.
        rows_written: Number of rows written.
        message: Optional status message.
        metadata: Additional metadata about the operation.
    """

    success: bool
    rows_written: int = 0
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class DestinationConnection(Protocol):
    """Protocol defining the interface for destination connections.

    All destination implementations (Google Sheets, Excel Online, etc.) must
    implement this protocol to be usable with the sync tool.
    """

    @property
    def destination_type(self) -> str:
        """Return the destination type identifier.

        Returns:
            Destination type string ('google_sheets', 'excel_online', etc.).
        """
        ...

    def connect(self) -> None:
        """Establish a connection to the destination.

        Raises:
            DestinationError: If connection fails.
        """
        ...

    def write(
        self,
        headers: list[str],
        rows: list[list[Any]],
        mode: str = "replace",
    ) -> WriteResult:
        """Write data to the destination.

        Args:
            headers: Column headers.
            rows: Data rows to write.
            mode: Write mode ('replace', 'append').

        Returns:
            WriteResult with operation details.

        Raises:
            DestinationError: If write fails.
        """
        ...

    def read(self) -> tuple[list[str], list[list[Any]]]:
        """Read all data from the destination.

        Returns:
            Tuple of (headers, rows).

        Raises:
            DestinationError: If read fails.
        """
        ...

    def clear(self) -> None:
        """Clear all data from the destination.

        Raises:
            DestinationError: If clear fails.
        """
        ...

    def close(self) -> None:
        """Close the destination connection."""
        ...

    def test_connection(self) -> bool:
        """Test if the destination connection is valid.

        Returns:
            True if connection successful.

        Raises:
            DestinationError: If connection test fails.
        """
        ...

    def __enter__(self) -> "DestinationConnection":
        """Enter context manager, establishing connection."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager, closing connection."""
        ...


class BaseDestinationConnection(ABC):
    """Abstract base class for destination connections.

    Provides common functionality and enforces the DestinationConnection protocol.
    """

    def __init__(self, config: DestinationConfig) -> None:
        """Initialize the destination connection.

        Args:
            config: Destination configuration.
        """
        self.config = config
        self._connected: bool = False

    @property
    @abstractmethod
    def destination_type(self) -> str:
        """Return the destination type identifier."""
        ...

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the destination."""
        ...

    @abstractmethod
    def write(
        self,
        headers: list[str],
        rows: list[list[Any]],
        mode: str = "replace",
    ) -> WriteResult:
        """Write data to the destination."""
        ...

    @abstractmethod
    def read(self) -> tuple[list[str], list[list[Any]]]:
        """Read all data from the destination."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the destination."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the destination connection."""
        ...

    def test_connection(self) -> bool:
        """Test if the destination connection is valid.

        Default implementation attempts to connect and returns True if successful.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self.connect()
            return True
        except Exception:
            return False
        finally:
            self.close()

    def __enter__(self) -> "BaseDestinationConnection":
        """Enter context manager, establishing connection.

        Returns:
            Self after establishing connection.
        """
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager, closing connection.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        self.close()
