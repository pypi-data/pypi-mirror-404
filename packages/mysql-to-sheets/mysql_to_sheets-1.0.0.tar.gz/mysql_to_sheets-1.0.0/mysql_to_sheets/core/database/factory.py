"""Factory function for creating database connections.

This module provides the get_connection() factory function that creates
the appropriate database connection based on configuration.

Database driver imports are deferred so that optional dependencies
(psycopg2, pymssql) are only required when actually used.
"""

from __future__ import annotations

from mysql_to_sheets.core.database.base import DatabaseConfig, DatabaseConnection
from mysql_to_sheets.core.exceptions import (
    ConfigError,
    ErrorCode,
    UnsupportedDatabaseError,
)

_SUPPORTED_TYPES = ["mysql", "postgres", "postgresql", "sqlite", "mssql", "sqlserver"]

# Default ports for each database type
_DEFAULT_PORTS = {
    "mysql": 3306,
    "postgres": 5432,
    "postgresql": 5432,
    "mssql": 1433,
    "sqlserver": 1433,
}


def detect_port_mismatch(db_type: str, port: int) -> str | None:
    """Detect if the configured port doesn't match the expected default for db_type.

    This helps catch a common onboarding mistake where users switch database types
    but forget to update the port (EC-38).

    Args:
        db_type: Database type (mysql, postgres, mssql, etc.)
        port: Configured port number.

    Returns:
        Warning message if port mismatch detected, None otherwise.

    Example:
        >>> detect_port_mismatch("postgres", 3306)
        'You are connecting to PostgreSQL on port 3306, but PostgreSQL typically uses port 5432...'
    """
    db_type_lower = db_type.lower()
    expected_port = _DEFAULT_PORTS.get(db_type_lower)

    if expected_port is None or port == expected_port:
        return None

    # Check if the port is a default port for a DIFFERENT database type
    for other_type, other_port in _DEFAULT_PORTS.items():
        if port == other_port and other_type != db_type_lower:
            # Normalize display names
            db_display = {
                "mysql": "MySQL",
                "postgres": "PostgreSQL",
                "postgresql": "PostgreSQL",
                "mssql": "SQL Server",
                "sqlserver": "SQL Server",
            }
            current_name = db_display.get(db_type_lower, db_type)
            other_name = db_display.get(other_type, other_type)

            return (
                f"You are connecting to {current_name} on port {port}, "
                f"but {current_name} typically uses port {expected_port}. "
                f"Port {port} is the default for {other_name}.\n"
                f"Did you mean to use port {expected_port}? Check DB_PORT in your .env file.\n\n"
                f"Default ports: MySQL=3306, PostgreSQL=5432, SQL Server=1433"
            )

    return None


def enhance_connection_error(
    error: Exception,
    db_type: str,
    host: str,
    port: int,
) -> str:
    """Enhance a database connection error with port mismatch detection.

    Call this when a connection error occurs to potentially add helpful
    context about port misconfiguration.

    Args:
        error: The original connection error.
        db_type: Database type being connected to.
        host: Database host.
        port: Database port.

    Returns:
        Enhanced error message with port mismatch hint if applicable,
        or original error message if no mismatch detected.
    """
    error_str = str(error)

    # Check for port mismatch on connection refused/timeout errors
    error_lower = error_str.lower()
    if any(
        keyword in error_lower
        for keyword in ["refused", "timeout", "timed out", "connection", "cannot connect"]
    ):
        mismatch_warning = detect_port_mismatch(db_type, port)
        if mismatch_warning:
            return f"{error_str}\n\nPossible cause:\n{mismatch_warning}"

    return error_str


def get_connection(config: DatabaseConfig) -> DatabaseConnection:
    """Create a database connection based on configuration.

    Factory function that returns the appropriate database connection
    implementation based on the db_type in the configuration. Imports
    are deferred so optional drivers are only loaded when needed.

    Args:
        config: Database configuration with db_type specified.

    Returns:
        DatabaseConnection instance for the specified database type.

    Raises:
        UnsupportedDatabaseError: If the database type is not supported.
    """
    db_type = config.db_type.lower()

    if db_type == "mysql":
        from mysql_to_sheets.core.database.mysql import MySQLConnection

        return MySQLConnection(config)  # type: ignore[call-arg]
    elif db_type in ("postgres", "postgresql"):
        try:
            from mysql_to_sheets.core.database.postgres import PostgresConnection
        except ImportError as e:
            raise ConfigError(
                message=(
                    "PostgreSQL driver not installed. "
                    "Install it with: pip install mysql-to-sheets[postgres]"
                ),
                code=ErrorCode.CONFIG_DRIVER_MISSING,
                missing_fields=["psycopg2-binary"],
            ) from e

        return PostgresConnection(config)  # type: ignore[call-arg]
    elif db_type == "sqlite":
        from mysql_to_sheets.core.database.sqlite import SQLiteConnection

        return SQLiteConnection(config)  # type: ignore[call-arg]
    elif db_type in ("mssql", "sqlserver"):
        try:
            from mysql_to_sheets.core.database.mssql import MSSQLConnection
        except ImportError as e:
            raise ConfigError(
                message=(
                    "SQL Server driver not installed. "
                    "Install it with: pip install mysql-to-sheets[mssql]"
                ),
                code=ErrorCode.CONFIG_DRIVER_MISSING,
                missing_fields=["pymssql"],
            ) from e

        return MSSQLConnection(config)  # type: ignore[call-arg]
    else:
        supported = ", ".join(sorted(set(_SUPPORTED_TYPES)))
        raise UnsupportedDatabaseError(
            message=f"Unsupported database type: '{db_type}'. Supported types: {supported}",
            db_type=db_type,
        )


def get_supported_databases() -> list[str]:
    """Get list of supported database types.

    Returns:
        List of supported database type identifiers.
    """
    # Return unique values (exclude aliases)
    return ["mysql", "postgres", "sqlite", "mssql"]
