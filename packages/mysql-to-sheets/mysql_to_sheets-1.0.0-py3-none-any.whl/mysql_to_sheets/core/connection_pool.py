"""MySQL connection pooling for improved performance.

This module provides connection pooling for MySQL connections,
reducing connection overhead for frequent sync operations.
"""

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock

import mysql.connector
from mysql.connector import Error as MySQLError
from mysql.connector.pooling import MySQLConnectionPool

from mysql_to_sheets.core.config import Config
from mysql_to_sheets.core.exceptions import DatabaseError
from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)

# Global connection pool with thread-safe access
_pool: MySQLConnectionPool | None = None
_pool_lock = Lock()


@dataclass
class PoolConfig:
    """Configuration for connection pool.

    Attributes:
        pool_size: Number of connections in the pool.
        pool_name: Name identifier for the pool.
        pool_reset_session: Whether to reset session state on return.
    """

    pool_size: int = 5
    pool_name: str = "mysql_to_sheets_pool"
    pool_reset_session: bool = True


def get_connection_pool(
    config: Config,
    pool_config: PoolConfig | None = None,
) -> MySQLConnectionPool:
    """Get or create the global connection pool.

    Creates a new pool if one doesn't exist, or returns the existing pool.
    The pool is configured based on the provided Config object.

    This function is thread-safe and uses double-checked locking to avoid
    race conditions when multiple threads call simultaneously.

    Args:
        config: Application config with database credentials.
        pool_config: Optional pool-specific configuration.

    Returns:
        MySQLConnectionPool instance.

    Raises:
        DatabaseError: If pool creation fails.
    """
    global _pool

    # Fast path: pool already exists
    if _pool is not None:
        return _pool

    # Slow path: acquire lock and create pool
    with _pool_lock:
        # Double-check after acquiring lock (another thread may have created it)
        if _pool is not None:
            return _pool

        if pool_config is None:
            pool_config = PoolConfig()

        try:
            logger.info(
                f"Creating MySQL connection pool: {pool_config.pool_name} "
                f"(size={pool_config.pool_size})"
            )

            _pool = MySQLConnectionPool(
                pool_name=pool_config.pool_name,
                pool_size=pool_config.pool_size,
                pool_reset_session=pool_config.pool_reset_session,
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database=config.db_name,
                connection_timeout=config.db_connect_timeout,
            )

            logger.info("Connection pool created successfully")

        except MySQLError as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise DatabaseError(
                message=f"Failed to create connection pool: {e}",
                host=config.db_host,
                database=config.db_name,
                original_error=e,
            ) from e

    return _pool


def reset_pool() -> None:
    """Reset the global connection pool.

    Useful for testing or when configuration changes.
    This function is thread-safe.
    """
    global _pool
    with _pool_lock:
        _pool = None
    logger.info("Connection pool reset")


def _validate_connection(
    connection: mysql.connector.MySQLConnection,
    config: Config,
) -> mysql.connector.MySQLConnection:
    """Validate a pooled connection is still alive.

    MySQL closes idle connections after wait_timeout (default 8 hours).
    This check pings the connection to detect stale connections early.

    Args:
        connection: The pooled connection to validate.
        config: Application config for reconnection.

    Returns:
        A valid connection (either the original or a new one).

    Raises:
        DatabaseError: If reconnection fails.
    """
    try:
        # Ping the connection to check if it's still alive
        connection.ping(reconnect=True, attempts=1, delay=0)
        return connection
    except MySQLError as e:
        logger.warning(
            "Stale connection detected in pool (likely exceeded MySQL wait_timeout). "
            "Reconnecting: %s",
            e,
        )
        # Connection is stale, close it and get a new one
        try:
            connection.close()
        except (OSError, RuntimeError):
            pass

        # Create a fresh connection
        try:
            new_connection = mysql.connector.connect(
                host=config.db_host,
                port=config.db_port,
                user=config.db_user,
                password=config.db_password,
                database=config.db_name,
                connection_timeout=config.db_connect_timeout,
            )
            logger.info("Reconnected after stale connection detected")
            return new_connection
        except MySQLError as reconnect_error:
            raise DatabaseError(
                message=f"Failed to reconnect after stale connection: {reconnect_error}",
                host=config.db_host,
                database=config.db_name,
                original_error=reconnect_error,
            ) from reconnect_error


@contextmanager
def pooled_connection(
    config: Config,
    pool_config: PoolConfig | None = None,
) -> Generator[mysql.connector.MySQLConnection, None, None]:
    """Context manager for getting a pooled connection.

    Acquires a connection from the pool, validates it's still alive,
    yields it, and returns it to the pool on exit. Handles cleanup on
    exceptions.

    IMPORTANT: Connections may become stale if idle longer than MySQL's
    wait_timeout (default 8 hours). This function validates connections
    before returning them to avoid "MySQL server has gone away" errors.

    Args:
        config: Application config with database credentials.
        pool_config: Optional pool-specific configuration.

    Yields:
        MySQL connection from the pool (validated as alive).

    Raises:
        DatabaseError: If connection acquisition fails.

    Example:
        with pooled_connection(config) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    """
    pool = get_connection_pool(config, pool_config)
    connection = None

    try:
        connection = pool.get_connection()
        logger.debug("Acquired connection from pool")

        # Validate the connection is still alive (handles stale connections)
        connection = _validate_connection(connection, config)

        yield connection  # type: ignore[misc]

    except MySQLError as e:
        logger.error(f"Pool connection error: {e}")
        raise DatabaseError(
            message=f"Failed to get pooled connection: {e}",
            host=config.db_host,
            database=config.db_name,
            original_error=e,
        ) from e

    finally:
        if connection is not None:
            try:
                connection.close()  # Returns connection to pool
                logger.debug("Returned connection to pool")
            except (OSError, RuntimeError) as e:
                logger.warning(f"Error returning connection to pool: {e}")


class PooledConnection:
    """Class-based context manager for pooled connections.

    Provides the same functionality as pooled_connection() but
    as a class for cases where a callable is needed.

    Attributes:
        config: Application configuration.
        pool_config: Pool-specific configuration.
        connection: The acquired connection (set on enter).
    """

    def __init__(
        self,
        config: Config,
        pool_config: PoolConfig | None = None,
    ) -> None:
        """Initialize pooled connection manager.

        Args:
            config: Application config with database credentials.
            pool_config: Optional pool-specific configuration.
        """
        self.config = config
        self.pool_config = pool_config
        self.connection: mysql.connector.MySQLConnection | None = None

    def __enter__(self) -> mysql.connector.MySQLConnection:
        """Acquire connection from pool and validate it's alive.

        Returns:
            MySQL connection (validated as alive).

        Raises:
            DatabaseError: If connection acquisition fails.
        """
        pool = get_connection_pool(self.config, self.pool_config)
        try:
            self.connection = pool.get_connection()  # type: ignore[assignment]
            logger.debug("Acquired connection from pool (class)")

            # Validate the connection is still alive (handles stale connections)
            self.connection = _validate_connection(self.connection, self.config)  # type: ignore[assignment]

            return self.connection  # type: ignore[return-value]
        except MySQLError as e:
            raise DatabaseError(
                message=f"Failed to get pooled connection: {e}",
                host=self.config.db_host,
                database=self.config.db_name,
                original_error=e,
            ) from e

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: Exception | None,
        exc_tb: object,
    ) -> None:
        """Return connection to pool.

        Args:
            exc_type: Exception type if raised.
            exc_val: Exception value if raised.
            exc_tb: Exception traceback if raised.
        """
        if self.connection is not None:
            try:
                self.connection.close()
                logger.debug("Returned connection to pool (class)")
            except (OSError, RuntimeError) as e:
                logger.warning(f"Error returning connection to pool: {e}")


def get_pool_stats() -> dict[str, str | int] | None:
    """Get statistics about the connection pool.

    Returns:
        Dictionary with pool statistics, or None if pool not initialized.
        Keys: pool_size (int), pool_name (str)
    """
    global _pool

    if _pool is None:
        return None

    return {
        "pool_name": str(_pool.pool_name),
        "pool_size": int(_pool.pool_size) if isinstance(_pool.pool_size, (int, str)) else _pool.pool_size,
    }
