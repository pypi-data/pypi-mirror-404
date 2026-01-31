"""Job queue backend factory.

Provides a factory function to get the appropriate job queue backend
based on configuration. Supports SQLite (default) and Redis backends.
"""

import logging
from typing import TYPE_CHECKING

from mysql_to_sheets.core.job_backend import JobQueueBackend

if TYPE_CHECKING:
    from mysql_to_sheets.core.config import Config

logger = logging.getLogger(__name__)

# Cached backend instance
_backend: JobQueueBackend | None = None
_backend_type: str | None = None


def get_job_backend(
    config: "Config | None" = None,
    backend_type: str | None = None,
    db_path: str | None = None,
    redis_url: str | None = None,
) -> JobQueueBackend:
    """Get or create a job queue backend.

    Factory function that returns the appropriate backend based on
    configuration. Caches the backend instance for reuse.

    Args:
        config: Configuration object. If provided, uses job_queue_backend
            to determine which backend to use.
        backend_type: Explicit backend type ('sqlite' or 'redis').
            Takes precedence over config.
        db_path: SQLite database path (for sqlite backend).
        redis_url: Redis connection URL (for redis backend).

    Returns:
        JobQueueBackend instance.

    Raises:
        ValueError: If configuration is invalid or backend type unknown.

    Examples:
        # Using config
        backend = get_job_backend(config)

        # Explicit SQLite
        backend = get_job_backend(backend_type="sqlite", db_path="/path/to/jobs.db")

        # Explicit Redis
        backend = get_job_backend(backend_type="redis", redis_url="redis://localhost:6379/0")
    """
    global _backend, _backend_type

    # Determine backend type
    resolved_type = _resolve_backend_type(config, backend_type)

    # Return cached backend if type matches
    if _backend is not None and _backend_type == resolved_type:
        return _backend

    # Create new backend
    if resolved_type == "redis":
        _backend = _create_redis_backend(config, redis_url)
    else:
        _backend = _create_sqlite_backend(config, db_path)

    _backend_type = resolved_type
    logger.info(f"Created job queue backend: {resolved_type}")

    return _backend


def _resolve_backend_type(
    config: "Config | None",
    backend_type: str | None,
) -> str:
    """Resolve the backend type from config or explicit parameter.

    Args:
        config: Configuration object.
        backend_type: Explicit backend type.

    Returns:
        Backend type string ('sqlite' or 'redis').
    """
    # Explicit type takes precedence
    if backend_type:
        return backend_type.lower()

    # Use config if provided
    if config:
        return config.job_queue_backend.lower()

    # Check environment variable
    import os

    return os.getenv("JOB_QUEUE_BACKEND", "sqlite").lower()


def _create_sqlite_backend(
    config: "Config | None",
    db_path: str | None,
) -> JobQueueBackend:
    """Create a SQLite-based job queue backend.

    Args:
        config: Configuration object.
        db_path: Explicit database path.

    Returns:
        SQLiteJobQueue instance.
    """
    from mysql_to_sheets.core.sqlite_job_queue import SQLiteJobQueue

    # Determine database path
    if db_path:
        path = db_path
    elif config:
        path = config.tenant_db_path
    else:
        import os

        path = os.getenv("TENANT_DB_PATH", "./data/tenant.db")

    return SQLiteJobQueue(db_path=path)


def _create_redis_backend(
    config: "Config | None",
    redis_url: str | None,
) -> JobQueueBackend:
    """Create a Redis-based job queue backend.

    Args:
        config: Configuration object.
        redis_url: Explicit Redis URL.

    Returns:
        RedisJobQueue instance.
    """
    from mysql_to_sheets.core.redis_job_queue import RedisJobQueue

    # Determine Redis URL
    if redis_url:
        url = redis_url
    elif config:
        url = config.redis_url
    else:
        import os

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Get TTL from config
    ttl = 86400  # Default 24 hours
    if config:
        ttl = config.redis_job_ttl_seconds

    return RedisJobQueue(redis_url=url, ttl_seconds=ttl)


def reset_job_backend() -> None:
    """Reset the cached backend instance.

    Useful for testing and cleanup.
    """
    global _backend, _backend_type
    _backend = None
    _backend_type = None


def get_backend_type() -> str | None:
    """Get the current backend type.

    Returns:
        Backend type string or None if no backend initialized.
    """
    return _backend_type
