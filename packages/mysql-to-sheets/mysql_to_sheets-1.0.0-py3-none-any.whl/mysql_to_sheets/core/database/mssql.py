"""SQL Server database connection implementation.

This module provides the SQL Server-specific implementation of the DatabaseConnection
protocol, wrapping pymssql functionality.
"""

from collections.abc import Generator
from typing import Any

from mysql_to_sheets.core.database.base import (
    BaseDatabaseConnection,
    FetchResult,
    WriteResult,
)
from mysql_to_sheets.core.exceptions import DatabaseError, UnsupportedDatabaseError
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)


def _get_pymssql() -> Any:
    """Lazy import pymssql to make it optional.

    Returns:
        The pymssql module.

    Raises:
        UnsupportedDatabaseError: If pymssql is not installed.
    """
    try:
        import pymssql

        return pymssql
    except ImportError as e:
        raise UnsupportedDatabaseError(
            message="SQL Server support requires pymssql. Install with: pip install pymssql",
            db_type="mssql",
        ) from e


class MSSQLConnection(BaseDatabaseConnection):
    """SQL Server database connection implementation.

    Provides SQL Server-specific connection handling using pymssql.

    Example:
        >>> config = DatabaseConfig(
        ...     db_type="mssql",
        ...     host="sql.example.com",
        ...     port=1433,
        ...     user="user",
        ...     password="pass",
        ...     database="mydb",
        ... )
        >>> with MSSQLConnection(config) as conn:
        ...     result = conn.execute("SELECT * FROM users")
    """

    @property
    def db_type(self) -> str:
        """Return 'mssql' as the database type."""
        return "mssql"

    def connect(self) -> None:
        """Establish a connection to the SQL Server database.

        Raises:
            DatabaseError: If connection fails.
            UnsupportedDatabaseError: If pymssql is not installed.
        """
        pymssql = _get_pymssql()

        try:
            self._connection = pymssql.connect(
                server=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                timeout=self.config.connect_timeout,
                login_timeout=self.config.connect_timeout,
            )
        except pymssql.Error as e:
            # EC-38: Check for port mismatch on connection failure
            from mysql_to_sheets.core.database.factory import enhance_connection_error

            enhanced_message = enhance_connection_error(
                e, "mssql", self.config.host, self.config.port
            )
            raise DatabaseError(
                message=f"Failed to connect to SQL Server: {enhanced_message}",
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
        pymssql = _get_pymssql()

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

        except pymssql.Error as e:
            raise DatabaseError(
                message=f"Failed to execute SQL Server query: {e}",
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

        pymssql = _get_pymssql()

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
        except pymssql.Error as e:
            raise DatabaseError(
                message=f"Failed to execute SQL Server streaming query: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def test_connection(self) -> bool:
        """Test if the SQL Server connection is valid.

        Returns:
            True if connection successful.

        Raises:
            DatabaseError: If connection test fails.
            UnsupportedDatabaseError: If pymssql is not installed.
        """
        pymssql = _get_pymssql()

        try:
            connection = pymssql.connect(
                server=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                timeout=self.config.connect_timeout,
                login_timeout=self.config.connect_timeout,
            )
            connection.close()
            return True
        except pymssql.Error as e:
            raise DatabaseError(
                message=f"SQL Server connection test failed: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e

    def close(self) -> None:
        """Close the SQL Server connection."""
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass  # Ignore errors during close
            finally:
                self._connection = None

    def insert_rows(
        self,
        table: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> WriteResult:
        """Insert rows into a SQL Server table.

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
        pymssql = _get_pymssql()

        if self._connection is None:
            self.connect()

        if not rows:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Build parameterized INSERT query
            columns_str = ", ".join(f"[{col}]" for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            query = f"INSERT INTO [{table}] ({columns_str}) VALUES ({placeholders})"

            # Execute batch insert
            cursor.executemany(query, rows)
            self._connection.commit()

            return WriteResult(
                rows_affected=cursor.rowcount,
                rows_inserted=cursor.rowcount,
            )

        except pymssql.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to insert rows into SQL Server: {e}",
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
        """Insert rows with update on conflict (upsert).

        Uses SQL Server's MERGE statement.

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
        pymssql = _get_pymssql()

        if self._connection is None:
            self.connect()

        if not rows:
            return WriteResult(rows_affected=0)

        cursor = None
        total_affected = 0
        try:
            cursor = self._connection.cursor()

            # Determine which columns to update
            if update_columns is None:
                update_columns = [col for col in columns if col not in key_columns]

            # SQL Server MERGE syntax - process one row at a time for simplicity
            # (batch MERGE is complex and requires temp tables)
            for row in rows:
                # Build value placeholders
                values = dict(zip(columns, row))

                # Build MERGE statement
                merge_conditions = " AND ".join(f"target.[{col}] = %s" for col in key_columns)
                update_set = ", ".join(f"target.[{col}] = %s" for col in update_columns)
                insert_cols = ", ".join(f"[{col}]" for col in columns)
                insert_vals = ", ".join(["%s"] * len(columns))

                query = f"""
                    MERGE INTO [{table}] AS target
                    USING (SELECT 1 AS dummy) AS source
                    ON ({merge_conditions})
                    WHEN MATCHED THEN
                        UPDATE SET {update_set}
                    WHEN NOT MATCHED THEN
                        INSERT ({insert_cols}) VALUES ({insert_vals});
                """

                # Build parameter list: key values for ON, update values, then all values for INSERT
                params = (
                    [values[col] for col in key_columns]
                    + [values[col] for col in update_columns]
                    + [values[col] for col in columns]
                )

                cursor.execute(query, params)
                total_affected += cursor.rowcount

            self._connection.commit()

            return WriteResult(
                rows_affected=total_affected,
                rows_inserted=0,  # Unknown without additional queries
                rows_updated=0,  # Unknown without additional queries
            )

        except pymssql.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to upsert rows into SQL Server: {e}",
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
        pymssql = _get_pymssql()

        if self._connection is None:
            self.connect()

        if not key_values:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Build parameterized DELETE query
            conditions = " AND ".join(f"[{col}] = %s" for col in key_columns)
            query = f"DELETE FROM [{table}] WHERE {conditions}"

            # Execute batch delete
            cursor.executemany(query, key_values)
            self._connection.commit()

            return WriteResult(rows_affected=cursor.rowcount)

        except pymssql.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to delete rows from SQL Server: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def truncate_table(self, table: str) -> WriteResult:
        """Remove all rows from a SQL Server table.

        Args:
            table: Target table name.

        Returns:
            WriteResult (row count is 0 for TRUNCATE).

        Raises:
            DatabaseError: If truncation fails.
        """
        pymssql = _get_pymssql()

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(f"TRUNCATE TABLE [{table}]")
            self._connection.commit()

            return WriteResult(rows_affected=0)

        except pymssql.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to truncate SQL Server table: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def list_tables(self) -> list[str]:
        """List all tables in the SQL Server database.

        Returns:
            List of table names.

        Raises:
            DatabaseError: If query fails.
        """
        pymssql = _get_pymssql()

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tables = [row[0] for row in cursor.fetchall()]
            return tables

        except pymssql.Error as e:
            raise DatabaseError(
                message=f"Failed to list SQL Server tables: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def get_table_columns(self, table: str) -> list[dict[str, Any]]:
        """Get column information for a SQL Server table.

        Args:
            table: Table name to inspect.

        Returns:
            List of column info dicts with keys: name, type, nullable, default, primary_key.

        Raises:
            DatabaseError: If query fails.
        """

        pymssql = _get_pymssql()

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Get column info with primary key detection
            cursor.execute(
                """
                SELECT
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.IS_NULLABLE,
                    c.COLUMN_DEFAULT,
                    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS is_primary
                FROM INFORMATION_SCHEMA.COLUMNS c
                LEFT JOIN (
                    SELECT ku.COLUMN_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                    JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                        ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                    WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                        AND tc.TABLE_NAME = %s
                ) pk ON c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE c.TABLE_NAME = %s
                ORDER BY c.ORDINAL_POSITION
            """,
                (table, table),
            )
            rows = cursor.fetchall()

            columns = []
            for row in rows:
                columns.append(
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3],
                        "primary_key": row[4] == 1,
                    }
                )
            return columns

        except pymssql.Error as e:
            raise DatabaseError(
                message=f"Failed to get columns for SQL Server table {table}: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()
