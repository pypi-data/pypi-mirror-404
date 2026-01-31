"""Base classes and protocols for database connections.

This module defines the protocol that all database connections must implement,
along with common data structures used across database implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class DatabaseConfig:
    """Configuration for database connections.

    Attributes:
        db_type: Database type ('mysql' or 'postgres').
        host: Database server hostname.
        port: Database server port.
        user: Database username.
        password: Database password.
        database: Database name.
        connect_timeout: Connection timeout in seconds.
        read_timeout: Query read timeout in seconds.
        ssl_mode: SSL mode for connection (postgres: disable, require, verify-ca, verify-full).
        ssl_ca: Path to SSL CA certificate file.
    """

    db_type: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""
    connect_timeout: int = 10
    read_timeout: int = 300
    ssl_mode: str = ""
    ssl_ca: str = ""

    def __post_init__(self) -> None:
        """Set default port based on database type."""
        # Only adjust port if using MySQL default (3306), indicating it wasn't explicitly set
        if self.port == 3306:
            if self.db_type in ("postgres", "postgresql"):
                object.__setattr__(self, "port", 5432)
            elif self.db_type in ("mssql", "sqlserver"):
                object.__setattr__(self, "port", 1433)
            elif self.db_type == "sqlite":
                object.__setattr__(self, "port", 0)  # N/A for SQLite


@dataclass
class FetchResult:
    """Result of a database query execution.

    Attributes:
        headers: List of column names.
        rows: List of data rows (each row is a list of values).
        row_count: Number of rows returned.
    """

    headers: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0

    def __post_init__(self) -> None:
        """Calculate row count if not set."""
        if self.row_count == 0 and self.rows:
            self.row_count = len(self.rows)


@dataclass
class WriteResult:
    """Result of a database write operation.

    Attributes:
        rows_affected: Number of rows inserted, updated, or deleted.
        rows_inserted: Number of rows inserted (for upsert operations).
        rows_updated: Number of rows updated (for upsert operations).
        rows_skipped: Number of rows skipped (for skip conflict mode).
    """

    rows_affected: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0


@runtime_checkable
class DatabaseConnection(Protocol):
    """Protocol defining the interface for database connections.

    All database implementations (MySQL, PostgreSQL) must implement
    this protocol to be usable with the sync tool.
    """

    @property
    def db_type(self) -> str:
        """Return the database type identifier.

        Returns:
            Database type string ('mysql' or 'postgres').
        """
        ...

    def connect(self) -> None:
        """Establish a connection to the database.

        Raises:
            DatabaseError: If connection fails.
        """
        ...

    def execute(self, query: str) -> FetchResult:
        """Execute a query and return all results.

        Args:
            query: SQL query to execute.

        Returns:
            FetchResult with headers and all rows.

        Raises:
            DatabaseError: If query execution fails.
        """
        ...

    def execute_streaming(
        self,
        query: str,
        chunk_size: int = 1000,
    ) -> Generator[FetchResult, None, None]:
        """Execute a query and yield results in chunks.

        Args:
            query: SQL query to execute.
            chunk_size: Number of rows per chunk.

        Yields:
            FetchResult with headers and chunk of rows.

        Raises:
            DatabaseError: If query execution fails.
        """
        ...

    def test_connection(self) -> bool:
        """Test if the database connection is valid.

        Returns:
            True if connection successful.

        Raises:
            DatabaseError: If connection test fails.
        """
        ...

    def close(self) -> None:
        """Close the database connection."""
        ...

    def __enter__(self) -> "DatabaseConnection":
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

    def insert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> WriteResult:
        """Insert rows into a table.

        Args:
            table: Target table name.
            columns: List of column names.
            rows: List of data rows (each row is a list of values).

        Returns:
            WriteResult with affected row count.

        Raises:
            DatabaseError: If insertion fails.
        """
        ...

    def upsert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
        key_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> WriteResult:
        """Insert rows with update on conflict (upsert).

        Args:
            table: Target table name.
            columns: List of column names.
            rows: List of data rows.
            key_columns: Columns that form the unique key for conflict detection.
            update_columns: Columns to update on conflict. If None, updates all non-key columns.

        Returns:
            WriteResult with insert/update counts.

        Raises:
            DatabaseError: If upsert fails.
        """
        ...

    def delete_rows(
        self,
        table: str,
        key_columns: list[str],
        key_values: list[list[Any]],
    ) -> WriteResult:
        """Delete rows matching the given key values.

        Args:
            table: Target table name.
            key_columns: Columns that identify rows to delete.
            key_values: List of key value tuples to delete.

        Returns:
            WriteResult with deleted row count.

        Raises:
            DatabaseError: If deletion fails.
        """
        ...

    def truncate_table(self, table: str) -> WriteResult:
        """Remove all rows from a table.

        Args:
            table: Target table name.

        Returns:
            WriteResult (row count may be 0 for TRUNCATE).

        Raises:
            DatabaseError: If truncation fails.
        """
        ...


class BaseDatabaseConnection(ABC):
    """Abstract base class for database connections.

    Provides common functionality and enforces the DatabaseConnection protocol.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize the database connection.

        Args:
            config: Database configuration.
        """
        self.config = config
        self._connection: Any = None

    @property
    @abstractmethod
    def db_type(self) -> str:
        """Return the database type identifier."""
        ...

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the database."""
        ...

    @abstractmethod
    def execute(self, query: str) -> FetchResult:
        """Execute a query and return all results."""
        ...

    @abstractmethod
    def execute_streaming(
        self,
        query: str,
        chunk_size: int = 1000,
    ) -> Generator[FetchResult, None, None]:
        """Execute a query and yield results in chunks."""
        ...

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the database connection is valid."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        ...

    def insert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> WriteResult:
        """Insert rows into a table.

        Default implementation raises NotImplementedError.
        Subclasses should override this method.

        Args:
            table: Target table name.
            columns: List of column names.
            rows: List of data rows.

        Returns:
            WriteResult with affected row count.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(f"insert_rows not implemented for {self.db_type}")

    def upsert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
        key_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> WriteResult:
        """Insert rows with update on conflict (upsert).

        Default implementation raises NotImplementedError.
        Subclasses should override this method.

        Args:
            table: Target table name.
            columns: List of column names.
            rows: List of data rows.
            key_columns: Columns that form the unique key.
            update_columns: Columns to update on conflict.

        Returns:
            WriteResult with insert/update counts.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(f"upsert_rows not implemented for {self.db_type}")

    def delete_rows(
        self,
        table: str,
        key_columns: list[str],
        key_values: list[list[Any]],
    ) -> WriteResult:
        """Delete rows matching the given key values.

        Default implementation raises NotImplementedError.
        Subclasses should override this method.

        Args:
            table: Target table name.
            key_columns: Columns that identify rows to delete.
            key_values: List of key value tuples to delete.

        Returns:
            WriteResult with deleted row count.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(f"delete_rows not implemented for {self.db_type}")

    def truncate_table(self, table: str) -> WriteResult:
        """Remove all rows from a table.

        Default implementation raises NotImplementedError.
        Subclasses should override this method.

        Args:
            table: Target table name.

        Returns:
            WriteResult (row count may be 0 for TRUNCATE).

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(f"truncate_table not implemented for {self.db_type}")

    def list_tables(self) -> list[str]:
        """List all tables in the database.

        Default implementation raises NotImplementedError.
        Subclasses should override this method.

        Returns:
            List of table names.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(f"list_tables not implemented for {self.db_type}")

    def get_table_columns(self, table: str) -> list[dict[str, Any]]:
        """Get column information for a table.

        Default implementation raises NotImplementedError.
        Subclasses should override this method.

        Args:
            table: Table name to inspect.

        Returns:
            List of column info dicts with keys: name, type, nullable, default, primary_key.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError(f"get_table_columns not implemented for {self.db_type}")

    def __enter__(self) -> "BaseDatabaseConnection":
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
