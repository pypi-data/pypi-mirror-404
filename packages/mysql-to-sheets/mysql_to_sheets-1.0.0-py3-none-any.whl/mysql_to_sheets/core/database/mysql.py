"""MySQL database connection implementation.

This module provides the MySQL-specific implementation of the DatabaseConnection
protocol, wrapping mysql-connector-python functionality.
"""

from collections.abc import Generator
from typing import Any

import mysql.connector
from mysql.connector import Error as MySQLError

from mysql_to_sheets.core.database.base import (
    BaseDatabaseConnection,
    FetchResult,
    WriteResult,
)
from mysql_to_sheets.core.exceptions import DatabaseError
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)


class MySQLConnection(BaseDatabaseConnection):
    """MySQL database connection implementation.

    Provides MySQL-specific connection handling using mysql-connector-python.

    Example:
        >>> config = DatabaseConfig(
        ...     db_type="mysql",
        ...     host="localhost",
        ...     user="user",
        ...     password="pass",
        ...     database="mydb",
        ... )
        >>> with MySQLConnection(config) as conn:
        ...     result = conn.execute("SELECT * FROM users")
    """

    @property
    def db_type(self) -> str:
        """Return 'mysql' as the database type."""
        return "mysql"

    def connect(self) -> None:
        """Establish a connection to the MySQL database.

        Raises:
            DatabaseError: If connection fails.
        """
        try:
            self._connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                connection_timeout=self.config.connect_timeout,
            )
        except MySQLError as e:
            # EC-38: Check for port mismatch on connection failure
            from mysql_to_sheets.core.database.factory import enhance_connection_error

            enhanced_message = enhance_connection_error(
                e, "mysql", self.config.host, self.config.port
            )
            raise DatabaseError(
                message=f"Failed to connect to MySQL: {enhanced_message}",
                host=self.config.host,
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

            return FetchResult(
                headers=headers,
                rows=rows,
                row_count=len(rows),
            )

        except MySQLError as e:
            raise DatabaseError(
                message=f"Failed to execute MySQL query: {e}",
                host=self.config.host,
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
            # Use unbuffered cursor for streaming
            cursor = self._connection.cursor(buffered=False)
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
            # This is expected behavior but log for debugging connection issues
            logger.debug(
                "Streaming query terminated early after %d chunks. "
                "Cursor will be closed. If you see connection pool exhaustion, "
                "ensure generators are explicitly closed after early termination.",
                chunks_yielded,
            )
            raise  # Re-raise to allow normal generator cleanup
        except MySQLError as e:
            raise DatabaseError(
                message=f"Failed to execute MySQL streaming query: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def test_connection(self) -> bool:
        """Test if the MySQL connection is valid.

        Returns:
            True if connection successful.

        Raises:
            DatabaseError: If connection test fails.
        """
        try:
            connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                connection_timeout=self.config.connect_timeout,
            )
            connection.close()
            return True
        except MySQLError as e:
            raise DatabaseError(
                message=f"MySQL connection test failed: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e

    def close(self) -> None:
        """Close the MySQL connection."""
        if self._connection is not None:
            try:
                if self._connection.is_connected():
                    self._connection.close()
            except MySQLError:
                pass  # Ignore errors during close
            finally:
                self._connection = None

    def insert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> WriteResult:
        """Insert rows into a MySQL table.

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
            columns_str = ", ".join(f"`{col}`" for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            query = f"INSERT INTO `{table}` ({columns_str}) VALUES ({placeholders})"

            # Execute batch insert
            cursor.executemany(query, rows)
            self._connection.commit()

            return WriteResult(
                rows_affected=cursor.rowcount,
                rows_inserted=cursor.rowcount,
            )

        except MySQLError as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to insert rows into MySQL: {e}",
                host=self.config.host,
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
        """Insert rows with update on duplicate key (upsert).

        Uses MySQL's INSERT ... ON DUPLICATE KEY UPDATE syntax.

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

            # Build parameterized INSERT ... ON DUPLICATE KEY UPDATE query
            columns_str = ", ".join(f"`{col}`" for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            update_clause = ", ".join(f"`{col}` = VALUES(`{col}`)" for col in update_columns)

            query = (
                f"INSERT INTO `{table}` ({columns_str}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {update_clause}"
            )

            # Execute batch upsert
            cursor.executemany(query, rows)
            self._connection.commit()

            # MySQL's rowcount for ON DUPLICATE KEY UPDATE:
            # - 1 for each new row inserted
            # - 2 for each existing row updated
            # - 0 for rows that matched but weren't changed
            affected = cursor.rowcount
            # Approximate insert/update split (not perfectly accurate)
            # A row count of 2 indicates an update
            rows_updated = affected // 2
            rows_inserted = affected - (rows_updated * 2)
            if rows_inserted < 0:
                rows_inserted = 0

            return WriteResult(
                rows_affected=affected,
                rows_inserted=rows_inserted,
                rows_updated=rows_updated,
            )

        except MySQLError as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to upsert rows into MySQL: {e}",
                host=self.config.host,
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
            conditions = " AND ".join(f"`{col}` = %s" for col in key_columns)
            query = f"DELETE FROM `{table}` WHERE {conditions}"

            # Execute batch delete
            cursor.executemany(query, key_values)
            self._connection.commit()

            return WriteResult(rows_affected=cursor.rowcount)

        except MySQLError as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to delete rows from MySQL: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def truncate_table(self, table: str) -> WriteResult:
        """Remove all rows from a MySQL table.

        Args:
            table: Target table name.

        Returns:
            WriteResult (row count is 0 for TRUNCATE).

        Raises:
            DatabaseError: If truncation fails.
        """
        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"TRUNCATE TABLE `{table}`")
            self._connection.commit()

            return WriteResult(rows_affected=0)

        except MySQLError as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to truncate MySQL table: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def list_tables(self) -> list[str]:
        """List all tables in the MySQL database.

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
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            return tables

        except MySQLError as e:
            raise DatabaseError(
                message=f"Failed to list MySQL tables: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def get_table_columns(self, table: str) -> list[dict[str, Any]]:
        """Get column information for a MySQL table.

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
            cursor.execute(f"DESCRIBE `{table}`")
            rows = cursor.fetchall()

            columns = []
            for row in rows:
                # DESCRIBE returns: Field, Type, Null, Key, Default, Extra
                columns.append(
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[4],
                        "primary_key": row[3] == "PRI",
                    }
                )
            return columns

        except MySQLError as e:
            raise DatabaseError(
                message=f"Failed to get columns for MySQL table {table}: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()
