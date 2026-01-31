"""Database abstraction layer for MySQL and PostgreSQL.

This module provides a unified interface for database connections,
allowing the sync tool to work with both MySQL and PostgreSQL databases.

Example:
    >>> from mysql_to_sheets.core.database import get_connection, DatabaseConfig
    >>>
    >>> config = DatabaseConfig(
    ...     db_type="postgres",
    ...     host="localhost",
    ...     port=5432,
    ...     user="user",
    ...     password="pass",
    ...     database="mydb",
    ... )
    >>> with get_connection(config) as conn:
    ...     result = conn.execute("SELECT * FROM users")
    ...     print(result.headers, result.rows)
"""

from mysql_to_sheets.core.database.base import (
    DatabaseConfig,
    DatabaseConnection,
    FetchResult,
    WriteResult,
)
from mysql_to_sheets.core.database.factory import get_connection
from mysql_to_sheets.core.database.type_converters import (
    clean_value,
    get_converter,
    register_converter,
)

__all__ = [
    "DatabaseConfig",
    "DatabaseConnection",
    "FetchResult",
    "WriteResult",
    "get_connection",
    "clean_value",
    "register_converter",
    "get_converter",
]
