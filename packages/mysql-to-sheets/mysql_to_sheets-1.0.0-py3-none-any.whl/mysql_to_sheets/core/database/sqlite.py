"""SQLite database connection implementation.

This module provides the SQLite-specific implementation of the DatabaseConnection
protocol, wrapping sqlite3 functionality. SQLite is built-in to Python and
does not require additional dependencies.
"""

import sqlite3
from collections.abc import Generator
from typing import Any

from mysql_to_sheets.core.database.base import (
    BaseDatabaseConnection,
    FetchResult,
    WriteResult,
)
from mysql_to_sheets.core.exceptions import DatabaseError
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)


class SQLiteConnection(BaseDatabaseConnection):
    """SQLite database connection implementation.

    Provides SQLite-specific connection handling using the built-in sqlite3 module.
    Uses the `database` config field as the file path (e.g., "./data.db" or ":memory:").

    Example:
        >>> config = DatabaseConfig(
        ...     db_type="sqlite",
        ...     database=":memory:",  # or "./data.db" for file-based
        ... )
        >>> with SQLiteConnection(config) as conn:
        ...     result = conn.execute("SELECT * FROM users")
    """

    @property
    def db_type(self) -> str:
        """Return 'sqlite' as the database type."""
        return "sqlite"

    def connect(self) -> None:
        """Establish a connection to the SQLite database.

        Uses the `database` config field as the file path.
        Supports ":memory:" for in-memory databases.

        Raises:
            DatabaseError: If connection fails.
        """
        try:
            db_path = self.config.database or ":memory:"
            self._connection = sqlite3.connect(
                db_path,
                timeout=self.config.connect_timeout,
            )
            # Enable foreign keys (disabled by default in SQLite)
            self._connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            raise DatabaseError(
                message=f"Failed to connect to SQLite database: {e}",
                database=self.config.database,
                original_error=e,
            ) from e

    def execute(self, query: str) -> FetchResult:
        """Execute a query and return all results.

        Args:
            query: SQL query to execute.

        Returns:
            FetchResult with headers and all rows.

        Raises:
            DatabaseError: If query execution fails.
        """
        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(query)

            # Get column headers from cursor description
            headers = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = [list(row) for row in cursor.fetchall()]

            # Commit if this was a write operation (no results to return)
            if cursor.description is None:
                self._connection.commit()

            return FetchResult(
                headers=headers,
                rows=rows,
                row_count=len(rows),
            )

        except sqlite3.Error as e:
            raise DatabaseError(
                message=f"Failed to execute SQLite query: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def execute_streaming(
        self,
        query: str,
        chunk_size: int = 1000,
    ) -> Generator[FetchResult, None, None]:
        """Execute a query and yield results in chunks.

        SQLite doesn't have true server-side cursors, but we simulate
        streaming by fetching in chunks for memory efficiency.

        IMPORTANT: Streaming generators should be fully consumed or explicitly
        closed to ensure proper cursor cleanup. Early termination (break) will
        delay cleanup until garbage collection.

        Example of proper cleanup:
            gen = connection.execute_streaming(query)
            try:
                for chunk in gen:
                    if should_stop:
                        break
            finally:
                gen.close()  # Ensures immediate cursor cleanup

        Args:
            query: SQL query to execute.
            chunk_size: Number of rows per chunk. Must be > 0.

        Yields:
            FetchResult with headers and chunk of rows.

        Raises:
            DatabaseError: If query execution fails.
            ValueError: If chunk_size is <= 0.
        """
        # Validate chunk_size to prevent infinite loops or errors
        if chunk_size <= 0:
            raise ValueError(
                f"chunk_size must be positive, got {chunk_size}. "
                "Use a value between 100 and 10000 for optimal performance."
            )

        if self._connection is None:
            self.connect()

        cursor = None
        chunks_yielded = 0
        try:
            cursor = self._connection.cursor()
            cursor.execute(query)

            # Get column headers from cursor description
            headers = [desc[0] for desc in cursor.description] if cursor.description else []

            # Yield chunks
            while True:
                chunk = cursor.fetchmany(chunk_size)
                if not chunk:
                    break

                rows = [list(row) for row in chunk]
                chunks_yielded += 1
                yield FetchResult(
                    headers=headers,
                    rows=rows,
                    row_count=len(rows),
                )

        except GeneratorExit:
            # Generator was closed early (break, gen.close(), or GC)
            logger.debug(
                "Streaming query terminated early after %d chunks. "
                "Cursor will be closed.",
                chunks_yielded,
            )
            raise  # Re-raise to allow normal generator cleanup
        except sqlite3.Error as e:
            raise DatabaseError(
                message=f"Failed to execute SQLite streaming query: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def test_connection(self) -> bool:
        """Test if the SQLite connection is valid.

        Returns:
            True if connection successful.

        Raises:
            DatabaseError: If connection test fails.
        """
        try:
            db_path = self.config.database or ":memory:"
            connection = sqlite3.connect(
                db_path,
                timeout=self.config.connect_timeout,
            )
            # Execute a simple query to verify the database is accessible
            connection.execute("SELECT 1")
            connection.close()
            return True
        except sqlite3.Error as e:
            raise DatabaseError(
                message=f"SQLite connection test failed: {e}",
                database=self.config.database,
                original_error=e,
            ) from e

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._connection is not None:
            try:
                self._connection.close()
            except OSError:
                pass  # Ignore errors during close
            finally:
                self._connection = None

    def insert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> WriteResult:
        """Insert rows into a SQLite table.

        Uses batch INSERT for efficiency.

        Args:
            table: Target table name.
            columns: List of column names.
            rows: List of data rows.

        Returns:
            WriteResult with affected row count.

        Raises:
            DatabaseError: If insertion fails.
        """
        if self._connection is None:
            self.connect()

        if not rows:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Build parameterized INSERT query
            columns_str = ", ".join(f'"{col}"' for col in columns)
            placeholders = ", ".join(["?"] * len(columns))
            query = f'INSERT INTO "{table}" ({columns_str}) VALUES ({placeholders})'

            # Execute batch insert
            cursor.executemany(query, rows)
            self._connection.commit()

            return WriteResult(
                rows_affected=cursor.rowcount,
                rows_inserted=cursor.rowcount,
            )

        except sqlite3.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to insert rows into SQLite: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def upsert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
        key_columns: list[str],
        update_columns: list[str] | None = None,
    ) -> WriteResult:
        """Insert rows with update on conflict (upsert).

        Uses SQLite's INSERT OR REPLACE syntax.

        Args:
            table: Target table name.
            columns: List of column names.
            rows: List of data rows.
            key_columns: Columns that form the unique key.
            update_columns: Columns to update on conflict. If None, updates all non-key columns.

        Returns:
            WriteResult with insert/update counts.

        Raises:
            DatabaseError: If upsert fails.
        """
        if self._connection is None:
            self.connect()

        if not rows:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Determine which columns to update
            if update_columns is None:
                update_columns = [col for col in columns if col not in key_columns]

            # Build parameterized INSERT ... ON CONFLICT DO UPDATE query (SQLite 3.24+)
            columns_str = ", ".join(f'"{col}"' for col in columns)
            placeholders = ", ".join(["?"] * len(columns))
            conflict_cols = ", ".join(f'"{col}"' for col in key_columns)
            update_clause = ", ".join(f'"{col}" = excluded."{col}"' for col in update_columns)

            query = (
                f'INSERT INTO "{table}" ({columns_str}) VALUES ({placeholders}) '
                f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_clause}"
            )

            # Execute batch upsert
            cursor.executemany(query, rows)
            self._connection.commit()

            return WriteResult(
                rows_affected=cursor.rowcount,
                rows_inserted=0,  # Unknown
                rows_updated=0,  # Unknown
            )

        except sqlite3.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to upsert rows into SQLite: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

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
        if self._connection is None:
            self.connect()

        if not key_values:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Build parameterized DELETE query
            conditions = " AND ".join(f'"{col}" = ?' for col in key_columns)
            query = f'DELETE FROM "{table}" WHERE {conditions}'

            # Execute batch delete
            cursor.executemany(query, key_values)
            self._connection.commit()

            return WriteResult(rows_affected=cursor.rowcount)

        except sqlite3.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to delete rows from SQLite: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def truncate_table(self, table: str) -> WriteResult:
        """Remove all rows from a SQLite table.

        SQLite doesn't have TRUNCATE, so we use DELETE FROM.

        Args:
            table: Target table name.

        Returns:
            WriteResult with deleted row count.

        Raises:
            DatabaseError: If deletion fails.
        """
        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(f'DELETE FROM "{table}"')
            self._connection.commit()

            return WriteResult(rows_affected=cursor.rowcount)

        except sqlite3.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to truncate SQLite table: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def list_tables(self) -> list[str]:
        """List all tables in the SQLite database.

        Returns:
            List of table names.

        Raises:
            DatabaseError: If query fails.
        """
        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            return tables

        except sqlite3.Error as e:
            raise DatabaseError(
                message=f"Failed to list SQLite tables: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def get_table_columns(self, table: str) -> list[dict[str, Any]]:
        """Get column information for a SQLite table.

        Args:
            table: Table name to inspect.

        Returns:
            List of column info dicts with keys: name, type, nullable, default, primary_key.

        Raises:
            DatabaseError: If query fails.
        """

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(f'PRAGMA table_info("{table}")')
            rows = cursor.fetchall()

            columns = []
            for row in rows:
                # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
                columns.append(
                    {
                        "name": row[1],
                        "type": row[2],
                        "nullable": row[3] == 0,
                        "default": row[4],
                        "primary_key": row[5] == 1,
                    }
                )
            return columns

        except sqlite3.Error as e:
            raise DatabaseError(
                message=f"Failed to get columns for SQLite table {table}: {e}",
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()
