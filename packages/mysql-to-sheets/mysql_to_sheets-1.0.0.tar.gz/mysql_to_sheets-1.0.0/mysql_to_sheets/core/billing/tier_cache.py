"""In-memory TTL cache for organization tier lookups.

This module provides caching for tier lookups to reduce database queries.
The cache is invalidated on billing webhook updates.

Example:
    >>> from mysql_to_sheets.core.tier_cache import get_tier_cache
    >>> from mysql_to_sheets.core.tier import Tier
    >>>
    >>> cache = get_tier_cache()
    >>> cache.set(org_id=123, tier=Tier.PRO)
    >>> tier = cache.get(org_id=123)  # Returns Tier.PRO
    >>> cache.invalidate(org_id=123)  # Remove from cache
"""

from __future__ import annotations

import os
import time
from threading import Lock
from typing import TYPE_CHECKING

from mysql_to_sheets.core.logging_utils import get_module_logger

if TYPE_CHECKING:
    from mysql_to_sheets.core.billing.tier import Tier

logger = get_module_logger(__name__)

# Default TTL: 5 minutes
DEFAULT_TTL_SECONDS = 300


class TierCache:
    """Thread-safe in-memory TTL cache for organization tiers.

    This cache stores tier lookups with a configurable TTL to reduce
    database queries. The cache is thread-safe and supports:
    - get: Retrieve cached tier (returns None if expired or missing)
    - set: Store tier with TTL
    - invalidate: Remove specific org from cache
    - clear: Remove all entries

    Attributes:
        ttl_seconds: Time-to-live for cache entries in seconds.
    """

    def __init__(self, ttl_seconds: int | None = None) -> None:
        """Initialize the tier cache.

        Args:
            ttl_seconds: Time-to-live for cache entries. Defaults to
                TIER_CACHE_TTL_SECONDS env var or 300 seconds.
        """
        if ttl_seconds is None:
            ttl_seconds = int(os.environ.get("TIER_CACHE_TTL_SECONDS", DEFAULT_TTL_SECONDS))
        self._ttl = ttl_seconds
        self._cache: dict[int, tuple[float, Tier]] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    @property
    def ttl_seconds(self) -> int:
        """Get the cache TTL in seconds."""
        return self._ttl

    def get(self, org_id: int) -> Tier | None:
        """Get cached tier for an organization.

        Args:
            org_id: Organization ID to look up.

        Returns:
            Cached Tier if valid and not expired, None otherwise.
        """
        with self._lock:
            entry = self._cache.get(org_id)
            if entry is None:
                self._misses += 1
                return None

            expiry_time, tier = entry
            if time.time() >= expiry_time:
                # Entry expired, remove it
                del self._cache[org_id]
                self._misses += 1
                logger.debug("Tier cache expired for org_id=%s", org_id)
                return None

            self._hits += 1
            logger.debug("Tier cache hit for org_id=%s, tier=%s", org_id, tier.value)
            return tier

    def set(self, org_id: int, tier: Tier) -> None:
        """Store tier in cache with TTL.

        Args:
            org_id: Organization ID.
            tier: Tier to cache.
        """
        with self._lock:
            expiry_time = time.time() + self._ttl
            self._cache[org_id] = (expiry_time, tier)
            logger.debug("Tier cache set for org_id=%s, tier=%s, ttl=%s", org_id, tier.value, self._ttl)

    def invalidate(self, org_id: int) -> bool:
        """Remove organization from cache.

        Args:
            org_id: Organization ID to invalidate.

        Returns:
            True if entry was removed, False if not found.
        """
        with self._lock:
            if org_id in self._cache:
                del self._cache[org_id]
                logger.debug("Tier cache invalidated for org_id=%s", org_id)
                return True
            return False

    def clear(self) -> int:
        """Remove all entries from cache.

        Returns:
            Number of entries cleared.
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.debug("Tier cache cleared, removed %s entries", count)
            return count

    def stats(self) -> dict[str, int | float]:
        """Get cache statistics.

        Returns:
            Dictionary with cache metrics.
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self._ttl,
            }


# Global cache instance
_tier_cache: TierCache | None = None
_tier_cache_lock = Lock()


def get_tier_cache() -> TierCache:
    """Get the global tier cache instance.

    Creates the cache on first access with TTL from environment.

    Returns:
        Global TierCache instance.
    """
    global _tier_cache
    if _tier_cache is None:
        with _tier_cache_lock:
            if _tier_cache is None:
                _tier_cache = TierCache()
    return _tier_cache


def reset_tier_cache() -> None:
    """Reset the global tier cache instance.

    Primarily for testing purposes.
    """
    global _tier_cache
    with _tier_cache_lock:
        if _tier_cache is not None:
            _tier_cache.clear()
        _tier_cache = None


def is_tier_cache_enabled() -> bool:
    """Check if tier caching is enabled.

    Returns:
        True if caching is enabled (default), False if disabled.
    """
    return os.environ.get("TIER_CACHE_ENABLED", "true").lower() in ("true", "1", "yes", "on")
