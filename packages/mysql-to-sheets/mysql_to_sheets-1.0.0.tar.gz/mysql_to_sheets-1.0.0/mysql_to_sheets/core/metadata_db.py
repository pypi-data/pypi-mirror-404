"""Metadata database engine factory.

Provides a factory function to get SQLAlchemy engines for internal metadata
storage (users, orgs, jobs, configs, etc.). Supports SQLite for local
development and PostgreSQL for production multi-worker deployments.
"""

import logging
import os
from threading import Lock
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, QueuePool

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config

logger = logging.getLogger(__name__)

# Cached engine instances by URL with thread-safe access
_engines: dict[str, Engine] = {}
_engines_lock = Lock()


def get_metadata_engine(
    config: "Config | None" = None,
    db_url: str | None = None,
) -> Engine:
    """Get or create a SQLAlchemy engine for metadata storage.

    Creates and caches engines based on database URL. Supports both SQLite
    (default for local development) and PostgreSQL (for production).

    Args:
        config: Configuration object. If provided, uses metadata_db_type and
            metadata_db_url to determine the connection.
        db_url: Explicit database URL. Takes precedence over config.

    Returns:
        SQLAlchemy Engine instance.

    Raises:
        ValueError: If configuration is invalid.

    Examples:
        # Using config
        engine = get_metadata_engine(config)

        # Using explicit URL
        engine = get_metadata_engine(db_url="postgresql://user:pass@host/db")
    """
    # Determine the database URL
    url = _resolve_database_url(config, db_url)

    # Fast path: return cached engine if available
    if url in _engines:
        return _engines[url]

    # Slow path: acquire lock and create engine
    with _engines_lock:
        # Double-check after acquiring lock (another thread may have created it)
        if url in _engines:
            return _engines[url]

        # Create new engine
        engine = _create_engine(url)
        _engines[url] = engine

        logger.info(f"Created metadata engine for {_mask_url(url)}")

    return engine


def _resolve_database_url(
    config: "Config | None",
    db_url: str | None,
) -> str:
    """Resolve the database URL from config or explicit parameter.

    Args:
        config: Configuration object.
        db_url: Explicit database URL.

    Returns:
        Database URL string.

    Raises:
        ValueError: If no valid URL can be determined.
    """
    # Explicit URL takes precedence
    if db_url:
        return db_url

    # Use config if provided
    if config:
        if config.metadata_db_type == "postgres" and config.metadata_db_url:
            return config.metadata_db_url
        elif config.metadata_db_type == "sqlite":
            # Use tenant_db_path for SQLite
            return f"sqlite:///{config.tenant_db_path}"
        elif config.metadata_db_url:
            # If URL is provided but type doesn't match, use URL anyway
            return config.metadata_db_url
        else:
            # Default to tenant_db_path as SQLite
            return f"sqlite:///{config.tenant_db_path}"

    # Check environment variables as fallback
    env_url = os.getenv("METADATA_DB_URL")
    if env_url:
        return env_url

    env_type = os.getenv("METADATA_DB_TYPE", "sqlite")
    if env_type == "sqlite":
        tenant_path = os.getenv("TENANT_DB_PATH", "./data/tenant.db")
        return f"sqlite:///{tenant_path}"

    raise ValueError("No database URL configured. Set METADATA_DB_URL or provide config.")


def _create_engine(url: str) -> Engine:
    """Create a SQLAlchemy engine with appropriate settings.

    Args:
        url: Database URL.

    Returns:
        Configured Engine instance.
    """
    parsed = urlparse(url)
    is_sqlite = parsed.scheme == "sqlite"
    is_postgres = parsed.scheme in ("postgresql", "postgres")

    # Engine arguments
    engine_args: dict[str, Any] = {
        "echo": False,
    }

    if is_sqlite:
        # SQLite-specific settings
        # Use NullPool for thread safety in multi-threaded apps
        engine_args["poolclass"] = NullPool
        engine_args["connect_args"] = {"check_same_thread": False}

        engine = create_engine(url, **engine_args)

        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    elif is_postgres:
        # PostgreSQL-specific settings
        # Use connection pooling for better performance
        # Read pool configuration from environment with sensible defaults
        pool_size = int(os.getenv("METADATA_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("METADATA_MAX_OVERFLOW", "10"))
        pool_recycle = int(os.getenv("METADATA_POOL_RECYCLE_SECONDS", "1800"))

        engine_args["poolclass"] = QueuePool
        engine_args["pool_size"] = pool_size
        engine_args["max_overflow"] = max_overflow
        engine_args["pool_pre_ping"] = True
        engine_args["pool_recycle"] = pool_recycle

        engine = create_engine(url, **engine_args)

    else:
        # Generic settings for other databases
        engine_args["pool_pre_ping"] = True
        engine = create_engine(url, **engine_args)

    return engine


def _mask_url(url: str) -> str:
    """Mask sensitive parts of a database URL for logging.

    Args:
        url: Database URL.

    Returns:
        URL with password masked.
    """
    parsed = urlparse(url)
    if parsed.password:
        masked = url.replace(f":{parsed.password}@", ":***@")
        return masked
    return url


def get_metadata_db_type(url: str) -> str:
    """Get the database type from a URL.

    Args:
        url: Database URL.

    Returns:
        Database type string ('sqlite', 'postgres', or 'unknown').
    """
    parsed = urlparse(url)
    if parsed.scheme == "sqlite":
        return "sqlite"
    elif parsed.scheme in ("postgresql", "postgres"):
        return "postgres"
    else:
        return "unknown"


def reset_engines() -> None:
    """Dispose all cached engines and clear the cache.

    Useful for testing and cleanup.
    This function is thread-safe.
    """
    global _engines
    with _engines_lock:
        for url, engine in _engines.items():
            try:
                engine.dispose()
                logger.debug(f"Disposed engine for {_mask_url(url)}")
            except (OSError, RuntimeError) as e:
                logger.warning(f"Error disposing engine: {e}")
        _engines.clear()


def get_engine_for_jobs(
    db_path: str | None = None,
    config: "Config | None" = None,
) -> Engine:
    """Get engine for job queue database.

    This is a convenience function for the job queue system. It uses the
    metadata engine factory but can fall back to a specific db_path for
    backward compatibility with SQLite-only deployments.

    Args:
        db_path: Legacy SQLite path (for backward compatibility).
        config: Configuration object.

    Returns:
        SQLAlchemy Engine instance.
    """
    # If explicit db_path provided and it looks like a file path (not URL),
    # convert to SQLite URL for backward compatibility
    if db_path and not db_path.startswith(("sqlite://", "postgresql://", "postgres://")):
        return get_metadata_engine(db_url=f"sqlite:///{db_path}")

    # If db_path is already a URL, use it directly
    if db_path:
        return get_metadata_engine(db_url=db_path)

    # Otherwise use config
    return get_metadata_engine(config=config)
