"""Centralized tenant database path management.

This module provides a single source of truth for tenant database path
resolution, used across CLI, API, and Web interfaces.
"""

import os
from pathlib import Path

# Default tenant database path (relative to working directory)
DEFAULT_TENANT_DB_PATH = "./data/tenant.db"


def get_tenant_db_path() -> str:
    """Get tenant database path from environment.

    The path is resolved from the TENANT_DB_PATH environment variable,
    falling back to the default path if not set.

    Returns:
        Absolute or relative path to the tenant database file.
    """
    return os.getenv("TENANT_DB_PATH", DEFAULT_TENANT_DB_PATH)


def ensure_tenant_db_dir(db_path: str | None = None) -> str:
    """Ensure tenant database directory exists.

    Creates the parent directory if it doesn't exist.

    Args:
        db_path: Optional database path. Uses get_tenant_db_path() if not provided.

    Returns:
        The database path (unchanged).
    """
    path = db_path or get_tenant_db_path()
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    return path


def get_tenant_db_url(db_path: str | None = None) -> str:
    """Get SQLAlchemy database URL for tenant database.

    Args:
        db_path: Optional database path. Uses get_tenant_db_path() if not provided.

    Returns:
        SQLAlchemy SQLite database URL.
    """
    path = db_path or get_tenant_db_path()
    return f"sqlite:///{path}"


def resolve_tenant_db_path(db_path: str | None = None) -> Path:
    """Resolve tenant database path to absolute Path.

    Args:
        db_path: Optional database path. Uses get_tenant_db_path() if not provided.

    Returns:
        Absolute Path object for the tenant database.
    """
    path = db_path or get_tenant_db_path()
    return Path(path).resolve()
