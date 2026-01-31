"""PostgreSQL database connection implementation.

This module provides the PostgreSQL-specific implementation of the DatabaseConnection
protocol, wrapping psycopg2 functionality. Includes optional connection pooling via
psycopg2.pool.ThreadedConnectionPool.
"""

import atexit
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from mysql_to_sheets.core.database.base import (
    BaseDatabaseConnection,
    FetchResult,
    WriteResult,
)
from mysql_to_sheets.core.exceptions import DatabaseError, UnsupportedDatabaseError
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)

# Global PostgreSQL connection pool
_pg_pool: Any = None
_atexit_registered: bool = False


def _get_psycopg2() -> Any:
    """Lazy import psycopg2 to make it optional.

    Returns:
        The psycopg2 module.

    Raises:
        UnsupportedDatabaseError: If psycopg2 is not installed.
    """
    try:
        import psycopg2

        return psycopg2
    except ImportError as e:
        raise UnsupportedDatabaseError(
            message="PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary",
            db_type="postgres",
        ) from e


def get_pg_pool(
    config: Any,
    pool_size: int | None = None,
) -> Any:
    """Get or create the global PostgreSQL connection pool.

    Uses psycopg2.pool.ThreadedConnectionPool for thread-safe pooling.
    Automatically registers cleanup on interpreter shutdown.

    Args:
        config: Application config with database credentials.
        pool_size: Maximum pool size. Defaults to config.db_pool_size.

    Returns:
        ThreadedConnectionPool instance.

    Raises:
        DatabaseError: If pool creation fails.
    """
    global _pg_pool, _atexit_registered

    if _pg_pool is not None and not _pg_pool.closed:
        return _pg_pool

    psycopg2 = _get_psycopg2()
    from psycopg2.pool import ThreadedConnectionPool as _ThreadedConnectionPool

    size = pool_size or getattr(config, "db_pool_size", 5)

    try:
        logger.info(f"Creating PostgreSQL connection pool (size={size})")

        dsn_params: dict[str, Any] = {
            "host": config.db_host,
            "port": config.db_port,
            "user": config.db_user,
            "password": config.db_password,
            "dbname": config.db_name,
            "connect_timeout": config.db_connect_timeout,
        }

        if getattr(config, "db_ssl_mode", None):
            dsn_params["sslmode"] = config.db_ssl_mode
        if getattr(config, "db_ssl_ca", None):
            dsn_params["sslrootcert"] = config.db_ssl_ca

        _pg_pool = _ThreadedConnectionPool(
            minconn=1,
            maxconn=size,
            **dsn_params,
        )

        # Register cleanup handler on first pool creation
        if not _atexit_registered:
            atexit.register(reset_pg_pool)
            _atexit_registered = True
            logger.debug("Registered PostgreSQL pool cleanup on interpreter shutdown")

        logger.info("PostgreSQL connection pool created successfully")
        return _pg_pool

    except psycopg2.Error as e:
        logger.error(f"Failed to create PostgreSQL connection pool: {e}")
        raise DatabaseError(
            message=f"Failed to create PostgreSQL connection pool: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e


def reset_pg_pool() -> None:
    """Reset the global PostgreSQL connection pool.

    Closes all connections and clears the cached pool.
    """
    global _pg_pool
    if _pg_pool is not None:
        try:
            _pg_pool.closeall()
        except OSError:
            pass
    _pg_pool = None
    logger.info("PostgreSQL connection pool reset")


@contextmanager
def pg_pooled_connection(
    config: Any,
    pool_size: int | None = None,
) -> Generator[Any, None, None]:
    """Context manager for getting a pooled PostgreSQL connection.

    Acquires a connection from the pool and returns it on exit.

    Args:
        config: Application config with database credentials.
        pool_size: Optional max pool size override.

    Yields:
        psycopg2 connection from the pool.

    Raises:
        DatabaseError: If connection acquisition fails.
    """
    psycopg2 = _get_psycopg2()
    pool = get_pg_pool(config, pool_size)
    connection = None

    try:
        connection = pool.getconn()
        logger.debug("Acquired PostgreSQL connection from pool")
        yield connection
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL pool connection error: {e}")
        raise DatabaseError(
            message=f"Failed to get pooled PostgreSQL connection: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e
    finally:
        if connection is not None:
            try:
                pool.putconn(connection)
                logger.debug("Returned PostgreSQL connection to pool")
            except OSError as e:
                logger.warning(f"Error returning PostgreSQL connection to pool: {e}")


def get_pg_pool_stats() -> dict[str, Any] | None:
    """Get statistics about the PostgreSQL connection pool.

    Returns:
        Dictionary with pool info, or None if pool not initialized.
    """
    if _pg_pool is None or _pg_pool.closed:
        return None

    return {
        "pool_minconn": _pg_pool.minconn,
        "pool_maxconn": _pg_pool.maxconn,
        "closed": _pg_pool.closed,
    }


class PostgresConnection(BaseDatabaseConnection):
    """PostgreSQL database connection implementation.

    Provides PostgreSQL-specific connection handling using psycopg2.

    Example:
        >>> config = DatabaseConfig(
        ...     db_type="postgres",
        ...     host="localhost",
        ...     port=5432,
        ...     user="user",
        ...     password="pass",
        ...     database="mydb",
        ... )
        >>> with PostgresConnection(config) as conn:
        ...     result = conn.execute("SELECT * FROM users")
    """

    @property
    def db_type(self) -> str:
        """Return 'postgres' as the database type."""
        return "postgres"

    def _build_connection_params(self) -> dict[str, Any]:
        """Build connection parameters for psycopg2.

        Returns:
            Dictionary of connection parameters.
        """
        params: dict[str, Any] = {
            "host": self.config.host,
            "port": self.config.port,
            "user": self.config.user,
            "password": self.config.password,
            "dbname": self.config.database,
            "connect_timeout": self.config.connect_timeout,
        }

        # Add SSL options if configured
        if self.config.ssl_mode:
            params["sslmode"] = self.config.ssl_mode

        if self.config.ssl_ca:
            params["sslrootcert"] = self.config.ssl_ca

        return params

    def connect(self) -> None:
        """Establish a connection to the PostgreSQL database.

        Raises:
            DatabaseError: If connection fails.
            UnsupportedDatabaseError: If psycopg2 is not installed.
        """
        psycopg2 = _get_psycopg2()

        try:
            params = self._build_connection_params()
            self._connection = psycopg2.connect(**params)
        except psycopg2.Error as e:
            # EC-38: Check for port mismatch on connection failure
            from mysql_to_sheets.core.database.factory import enhance_connection_error

            enhanced_message = enhance_connection_error(
                e, "postgres", self.config.host, self.config.port
            )
            raise DatabaseError(
                message=f"Failed to connect to PostgreSQL: {enhanced_message}",
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
        psycopg2 = _get_psycopg2()

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

        except psycopg2.Error as e:
            raise DatabaseError(
                message=f"Failed to execute PostgreSQL query: {e}",
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

        Uses a named cursor for server-side cursor support, which is
        more memory-efficient for large result sets.

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

        psycopg2 = _get_psycopg2()

        if self._connection is None:
            self.connect()

        cursor = None
        chunks_yielded = 0
        try:
            # Use a named cursor for server-side cursor (streaming)
            # Include thread ID and timestamp to avoid cursor name collisions
            # This is Edge Case 27: Concurrent streaming could collide with just id(self)
            cursor_name = (
                f"streaming_cursor_{id(self)}_{threading.get_ident()}_{int(time.time() * 1000)}"
            )
            cursor = self._connection.cursor(name=cursor_name)
            cursor.itersize = chunk_size
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
                "Cursor will be closed. If you see connection pool exhaustion, "
                "ensure generators are explicitly closed after early termination.",
                chunks_yielded,
            )
            raise  # Re-raise to allow normal generator cleanup
        except psycopg2.Error as e:
            raise DatabaseError(
                message=f"Failed to execute PostgreSQL streaming query: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def test_connection(self) -> bool:
        """Test if the PostgreSQL connection is valid.

        Returns:
            True if connection successful.

        Raises:
            DatabaseError: If connection test fails.
            UnsupportedDatabaseError: If psycopg2 is not installed.
        """
        psycopg2 = _get_psycopg2()

        try:
            params = self._build_connection_params()
            connection = psycopg2.connect(**params)
            connection.close()
            return True
        except psycopg2.Error as e:
            raise DatabaseError(
                message=f"PostgreSQL connection test failed: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e

    def close(self) -> None:
        """Close the PostgreSQL connection."""
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
        """Insert rows into a PostgreSQL table.

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
        psycopg2 = _get_psycopg2()

        if self._connection is None:
            self.connect()

        if not rows:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Build parameterized INSERT query
            columns_str = ", ".join(f'"{col}"' for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            query = f'INSERT INTO "{table}" ({columns_str}) VALUES ({placeholders})'

            # Execute batch insert
            cursor.executemany(query, rows)
            self._connection.commit()

            return WriteResult(
                rows_affected=cursor.rowcount,
                rows_inserted=cursor.rowcount,
            )

        except psycopg2.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to insert rows into PostgreSQL: {e}",
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

        Uses PostgreSQL's INSERT ... ON CONFLICT DO UPDATE syntax.

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
        psycopg2 = _get_psycopg2()

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

            # Build parameterized INSERT ... ON CONFLICT DO UPDATE query
            columns_str = ", ".join(f'"{col}"' for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))
            conflict_cols = ", ".join(f'"{col}"' for col in key_columns)
            update_clause = ", ".join(f'"{col}" = EXCLUDED."{col}"' for col in update_columns)

            query = (
                f'INSERT INTO "{table}" ({columns_str}) VALUES ({placeholders}) '
                f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_clause}"
            )

            # Execute batch upsert
            cursor.executemany(query, rows)
            self._connection.commit()

            # PostgreSQL doesn't easily distinguish between inserts and updates
            # rowcount gives total affected rows
            return WriteResult(
                rows_affected=cursor.rowcount,
                rows_inserted=0,  # Unknown
                rows_updated=0,  # Unknown
            )

        except psycopg2.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to upsert rows into PostgreSQL: {e}",
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
        psycopg2 = _get_psycopg2()

        if self._connection is None:
            self.connect()

        if not key_values:
            return WriteResult(rows_affected=0)

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Build parameterized DELETE query
            conditions = " AND ".join(f'"{col}" = %s' for col in key_columns)
            query = f'DELETE FROM "{table}" WHERE {conditions}'

            # Execute batch delete
            cursor.executemany(query, key_values)
            self._connection.commit()

            return WriteResult(rows_affected=cursor.rowcount)

        except psycopg2.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to delete rows from PostgreSQL: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def truncate_table(self, table: str) -> WriteResult:
        """Remove all rows from a PostgreSQL table.

        Args:
            table: Target table name.

        Returns:
            WriteResult (row count is 0 for TRUNCATE).

        Raises:
            DatabaseError: If truncation fails.
        """
        psycopg2 = _get_psycopg2()

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(f'TRUNCATE TABLE "{table}"')
            self._connection.commit()

            return WriteResult(rows_affected=0)

        except psycopg2.Error as e:
            self._connection.rollback()
            raise DatabaseError(
                message=f"Failed to truncate PostgreSQL table: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def list_tables(self) -> list[str]:
        """List all tables in the PostgreSQL database.

        Returns:
            List of table names.

        Raises:
            DatabaseError: If query fails.
        """
        psycopg2 = _get_psycopg2()

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY tablename
            """)
            tables = [row[0] for row in cursor.fetchall()]
            return tables

        except psycopg2.Error as e:
            raise DatabaseError(
                message=f"Failed to list PostgreSQL tables: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()

    def get_table_columns(self, table: str) -> list[dict[str, Any]]:
        """Get column information for a PostgreSQL table.

        Args:
            table: Table name to inspect.

        Returns:
            List of column info dicts with keys: name, type, nullable, default, primary_key.

        Raises:
            DatabaseError: If query fails.
        """

        psycopg2 = _get_psycopg2()

        if self._connection is None:
            self.connect()

        cursor = None
        try:
            cursor = self._connection.cursor()

            # Get column info
            cursor.execute(
                """
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT ku.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage ku
                        ON tc.constraint_name = ku.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_name = %s
                ) pk ON c.column_name = pk.column_name
                WHERE c.table_name = %s
                ORDER BY c.ordinal_position
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
                        "primary_key": row[4],
                    }
                )
            return columns

        except psycopg2.Error as e:
            raise DatabaseError(
                message=f"Failed to get columns for PostgreSQL table {table}: {e}",
                host=self.config.host,
                database=self.config.database,
                original_error=e,
            ) from e
        finally:
            if cursor:
                cursor.close()
