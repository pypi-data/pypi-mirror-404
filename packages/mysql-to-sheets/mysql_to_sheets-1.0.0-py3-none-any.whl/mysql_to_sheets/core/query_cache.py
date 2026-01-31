"""Optional query result caching for sync operations.

Provides in-memory and Redis-backed caching of database query results
to reduce database load for repeated identical syncs.

Extraction target: This module is a candidate for the ``tla-query-cache``
standalone package. It depends only on the standard library and optionally
``redis``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


def make_cache_key(
    sql_query: str,
    db_type: str,
    db_host: str,
    db_name: str,
    column_order: list[str] | None = None,
    rename_map: dict[str, str] | None = None,
) -> str:
    """Build a deterministic cache key from query parameters.

    The cache key includes column mapping configuration to prevent returning
    cached results with wrong columns when the mapping changes.

    Args:
        sql_query: The SQL query string.
        db_type: Database type (mysql, postgres, etc.).
        db_host: Database hostname.
        db_name: Database name.
        column_order: Optional list of columns to include (affects result shape).
        rename_map: Optional column rename mapping (affects column names).

    Returns:
        Hex digest string suitable as a cache key.
    """
    raw = f"{db_type}:{db_host}:{db_name}:{sql_query}"

    # Include column mapping in cache key to prevent returning wrong columns
    # when mapping configuration changes (Edge Case 24)
    if column_order:
        raw += f":cols={','.join(column_order)}"
    if rename_map:
        # Sort keys for deterministic ordering
        sorted_map = sorted(rename_map.items())
        raw += f":rename={sorted_map}"

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class MemoryCache:
    """Simple in-memory cache with TTL expiration and size limits.

    Limits both the number of entries and total memory usage to prevent
    unbounded memory growth from large query results.
    """

    # Maximum number of cached entries
    MAX_ENTRIES = 50
    # Maximum total size of cached payloads in bytes (~256MB)
    MAX_TOTAL_BYTES = 256 * 1024 * 1024

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}
        self._total_bytes: int = 0

    def get(self, key: str) -> tuple[list[str], list[list[Any]]] | None:
        """Return cached value or None if missing/expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, payload = entry
        if time.monotonic() > expires_at:
            self._total_bytes -= len(payload)
            del self._store[key]
            return None
        data = json.loads(payload)
        return data["headers"], data["rows"]

    def set(
        self,
        key: str,
        headers: list[str],
        rows: list[list[Any]],
        ttl_seconds: int,
    ) -> None:
        """Store a value with TTL, evicting expired/oldest entries if needed."""
        payload = json.dumps({"headers": headers, "rows": rows})
        payload_size = len(payload)

        # Evict expired entries first
        self._evict_expired()

        # Evict oldest entries if at capacity
        while (
            len(self._store) >= self.MAX_ENTRIES
            or self._total_bytes + payload_size > self.MAX_TOTAL_BYTES
        ) and self._store:
            oldest_key = min(self._store, key=lambda k: self._store[k][0])
            self._total_bytes -= len(self._store[oldest_key][1])
            del self._store[oldest_key]

        # Remove old entry for this key if replacing
        if key in self._store:
            self._total_bytes -= len(self._store[key][1])

        self._store[key] = (time.monotonic() + ttl_seconds, payload)
        self._total_bytes += payload_size

    def _evict_expired(self) -> None:
        """Remove all expired entries."""
        now = time.monotonic()
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            self._total_bytes -= len(self._store[k][1])
            del self._store[k]

    def invalidate(self, key: str) -> None:
        """Remove a key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()
        self._total_bytes = 0


class RedisCache:
    """Redis-backed query cache.

    Requires the ``redis`` package. Falls back gracefully on errors.
    """

    def __init__(self, redis_url: str) -> None:
        import redis as redis_lib

        self._client: redis_lib.Redis[bytes] = redis_lib.from_url(
            redis_url, decode_responses=False
        )
        self._prefix = "query_cache:"

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> tuple[list[str], list[list[Any]]] | None:
        """Return cached value or None if missing."""
        try:
            raw = self._client.get(self._key(key))
        except Exception:
            logger.warning("Redis cache get failed", exc_info=True)
            return None
        if raw is None:
            return None
        data = json.loads(raw)
        return data["headers"], data["rows"]

    def set(
        self,
        key: str,
        headers: list[str],
        rows: list[list[Any]],
        ttl_seconds: int,
    ) -> None:
        """Store a value with TTL."""
        payload = json.dumps({"headers": headers, "rows": rows})
        try:
            self._client.setex(self._key(key), ttl_seconds, payload)
        except Exception:
            logger.warning("Redis cache set failed", exc_info=True)

    def invalidate(self, key: str) -> None:
        """Remove a key from the cache."""
        try:
            self._client.delete(self._key(key))
        except Exception:
            logger.warning("Redis cache invalidate failed", exc_info=True)

    def clear(self) -> None:
        """Remove all cache entries (with prefix)."""
        try:
            keys = self._client.keys(f"{self._prefix}*")
            if keys:
                self._client.delete(*keys)
        except Exception:
            logger.warning("Redis cache clear failed", exc_info=True)


# Module-level singleton
_cache: MemoryCache | RedisCache | None = None


def get_query_cache(
    backend: str = "memory",
    redis_url: str = "",
) -> MemoryCache | RedisCache:
    """Get or create the query cache singleton.

    Args:
        backend: ``"memory"`` or ``"redis"``.
        redis_url: Redis connection URL (required when backend is ``"redis"``).

    Returns:
        Cache instance.
    """
    global _cache
    if _cache is not None:
        return _cache

    if backend == "redis":
        _cache = RedisCache(redis_url)
        logger.info("Query cache: Redis backend")
    else:
        _cache = MemoryCache()
        logger.info("Query cache: in-memory backend")

    return _cache


def reset_query_cache() -> None:
    """Reset the cache singleton (for testing)."""
    global _cache
    _cache = None
