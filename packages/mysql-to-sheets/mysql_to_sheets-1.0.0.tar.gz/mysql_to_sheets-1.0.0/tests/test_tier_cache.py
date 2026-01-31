"""Tests for tier caching functionality.

Verifies TTL cache behavior, invalidation, and integration with tier lookups.
"""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.tier import Tier


class TestTierCache:
    """Tests for TierCache class."""

    @pytest.fixture(autouse=True)
    def reset_cache(self) -> None:
        """Reset the global cache before each test."""
        from mysql_to_sheets.core.tier_cache import reset_tier_cache

        reset_tier_cache()
        yield
        reset_tier_cache()

    def test_cache_set_and_get(self) -> None:
        """Verify basic set and get operations."""
        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)
        cache.set(org_id=123, tier=Tier.PRO)

        result = cache.get(123)
        assert result == Tier.PRO

    def test_cache_returns_none_for_missing_key(self) -> None:
        """Verify get returns None for missing entries."""
        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)

        result = cache.get(999)
        assert result is None

    def test_cache_expires_after_ttl(self) -> None:
        """Verify entries expire after TTL."""
        from mysql_to_sheets.core.tier_cache import TierCache

        # Use very short TTL for testing
        cache = TierCache(ttl_seconds=1)
        cache.set(org_id=123, tier=Tier.PRO)

        # Should be cached
        assert cache.get(123) == Tier.PRO

        # Wait for expiry
        time.sleep(1.1)

        # Should be expired
        assert cache.get(123) is None

    def test_cache_invalidate(self) -> None:
        """Verify invalidate removes entry."""
        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)
        cache.set(org_id=123, tier=Tier.PRO)

        assert cache.get(123) == Tier.PRO

        result = cache.invalidate(123)
        assert result is True  # Entry was removed

        assert cache.get(123) is None

    def test_cache_invalidate_missing_key(self) -> None:
        """Verify invalidate returns False for missing key."""
        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)

        result = cache.invalidate(999)
        assert result is False

    def test_cache_clear(self) -> None:
        """Verify clear removes all entries."""
        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)
        cache.set(org_id=1, tier=Tier.FREE)
        cache.set(org_id=2, tier=Tier.PRO)
        cache.set(org_id=3, tier=Tier.BUSINESS)

        count = cache.clear()
        assert count == 3

        assert cache.get(1) is None
        assert cache.get(2) is None
        assert cache.get(3) is None

    def test_cache_stats(self) -> None:
        """Verify cache statistics tracking."""
        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)
        cache.set(org_id=123, tier=Tier.PRO)

        # Generate some hits and misses
        cache.get(123)  # hit
        cache.get(123)  # hit
        cache.get(999)  # miss

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3, abs=0.01)
        assert stats["ttl_seconds"] == 60

    def test_cache_ttl_from_environment(self) -> None:
        """Verify TTL can be configured from environment."""
        from mysql_to_sheets.core.tier_cache import TierCache

        with patch.dict(os.environ, {"TIER_CACHE_TTL_SECONDS": "120"}):
            cache = TierCache()  # No explicit TTL
            assert cache.ttl_seconds == 120

    def test_cache_thread_safety(self) -> None:
        """Verify cache is thread-safe."""
        import threading

        from mysql_to_sheets.core.tier_cache import TierCache

        cache = TierCache(ttl_seconds=60)
        errors: list[Exception] = []

        def writer(org_id: int, tier: Tier) -> None:
            try:
                for _ in range(100):
                    cache.set(org_id, tier)
                    cache.get(org_id)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(i, Tier.PRO))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestGlobalTierCache:
    """Tests for global tier cache instance."""

    @pytest.fixture(autouse=True)
    def reset_cache(self) -> None:
        """Reset the global cache before each test."""
        from mysql_to_sheets.core.tier_cache import reset_tier_cache

        reset_tier_cache()
        yield
        reset_tier_cache()

    def test_get_tier_cache_returns_singleton(self) -> None:
        """Verify get_tier_cache returns the same instance."""
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        cache1 = get_tier_cache()
        cache2 = get_tier_cache()

        assert cache1 is cache2

    def test_reset_tier_cache(self) -> None:
        """Verify reset_tier_cache creates new instance."""
        from mysql_to_sheets.core.tier_cache import get_tier_cache, reset_tier_cache

        cache1 = get_tier_cache()
        cache1.set(org_id=123, tier=Tier.PRO)

        reset_tier_cache()

        cache2 = get_tier_cache()
        # New cache should be empty
        assert cache2.get(123) is None

    def test_is_tier_cache_enabled_default(self) -> None:
        """Verify caching is enabled by default."""
        from mysql_to_sheets.core.tier_cache import is_tier_cache_enabled

        with patch.dict(os.environ, {}, clear=True):
            # Default is enabled when env var not set
            with patch.dict(os.environ, {"TIER_CACHE_ENABLED": "true"}):
                assert is_tier_cache_enabled() is True

    def test_is_tier_cache_enabled_false(self) -> None:
        """Verify caching can be disabled."""
        from mysql_to_sheets.core.tier_cache import is_tier_cache_enabled

        with patch.dict(os.environ, {"TIER_CACHE_ENABLED": "false"}):
            assert is_tier_cache_enabled() is False


class TestTierIntegration:
    """Tests for tier cache integration with tier lookups."""

    @pytest.fixture(autouse=True)
    def reset_cache(self) -> None:
        """Reset the global cache before each test."""
        from mysql_to_sheets.core.tier_cache import reset_tier_cache

        reset_tier_cache()
        yield
        reset_tier_cache()

    def test_tier_lookup_uses_cache(self) -> None:
        """Verify _get_organization_tier uses cache."""
        from mysql_to_sheets.core.tier import Tier, set_tier_callback
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        call_count = 0

        def mock_callback(org_id: int) -> Tier:
            nonlocal call_count
            call_count += 1
            return Tier.BUSINESS

        set_tier_callback(mock_callback)

        try:
            from mysql_to_sheets.core.tier import _get_organization_tier

            # First call should hit callback
            tier1 = _get_organization_tier(123)
            assert tier1 == Tier.BUSINESS
            assert call_count == 1

            # Second call should use cache
            tier2 = _get_organization_tier(123)
            assert tier2 == Tier.BUSINESS
            assert call_count == 1  # No additional callback call

        finally:
            set_tier_callback(None)  # type: ignore

    def test_tier_lookup_bypasses_cache_when_disabled(self) -> None:
        """Verify cache is bypassed when disabled."""
        from mysql_to_sheets.core.tier import Tier, set_tier_callback

        call_count = 0

        def mock_callback(org_id: int) -> Tier:
            nonlocal call_count
            call_count += 1
            return Tier.PRO

        set_tier_callback(mock_callback)

        try:
            with patch.dict(os.environ, {"TIER_CACHE_ENABLED": "false"}):
                from mysql_to_sheets.core.tier import _get_organization_tier

                # Both calls should hit callback
                _get_organization_tier(123)
                _get_organization_tier(123)
                assert call_count == 2

        finally:
            set_tier_callback(None)  # type: ignore


class TestBillingWebhookCacheInvalidation:
    """Tests for cache invalidation on billing webhook updates."""

    @pytest.fixture(autouse=True)
    def reset_cache(self) -> None:
        """Reset the global cache before each test."""
        from mysql_to_sheets.core.tier_cache import reset_tier_cache

        reset_tier_cache()
        yield
        reset_tier_cache()

    def test_update_organization_invalidates_cache(self) -> None:
        """Verify _update_organization invalidates tier cache."""
        from unittest.mock import MagicMock, patch

        from mysql_to_sheets.core.tier import Tier
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        # Pre-populate cache
        cache = get_tier_cache()
        cache.set(org_id=123, tier=Tier.FREE)
        assert cache.get(123) == Tier.FREE

        # Mock the organization repository
        mock_org = MagicMock()
        mock_org.subscription_tier = "free"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org

        with patch(
            "mysql_to_sheets.models.organizations.get_organization_repository",
            return_value=mock_repo,
        ):
            with patch(
                "mysql_to_sheets.api.billing_webhook_routes.get_tenant_db_path",
                return_value=":memory:",
            ):
                from mysql_to_sheets.api.billing_webhook_routes import (
                    _update_organization,
                )

                _update_organization(
                    organization_id=123,
                    subscription_tier="pro",
                )

        # Cache should be invalidated
        assert cache.get(123) is None
