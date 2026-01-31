"""Tests for query result caching."""

from __future__ import annotations

import time

import pytest

from mysql_to_sheets.core.query_cache import (
    MemoryCache,
    get_query_cache,
    make_cache_key,
    reset_query_cache,
)


class TestMakeCacheKey:
    """Tests for cache key generation."""

    def test_deterministic(self) -> None:
        key1 = make_cache_key("SELECT 1", "mysql", "localhost", "mydb")
        key2 = make_cache_key("SELECT 1", "mysql", "localhost", "mydb")
        assert key1 == key2

    def test_different_queries_produce_different_keys(self) -> None:
        key1 = make_cache_key("SELECT 1", "mysql", "localhost", "mydb")
        key2 = make_cache_key("SELECT 2", "mysql", "localhost", "mydb")
        assert key1 != key2

    def test_different_hosts_produce_different_keys(self) -> None:
        key1 = make_cache_key("SELECT 1", "mysql", "host1", "mydb")
        key2 = make_cache_key("SELECT 1", "mysql", "host2", "mydb")
        assert key1 != key2

    def test_returns_hex_string(self) -> None:
        key = make_cache_key("SELECT 1", "mysql", "localhost", "mydb")
        assert len(key) == 64  # SHA-256 hex digest


class TestMemoryCache:
    """Tests for in-memory cache backend."""

    def test_set_and_get(self) -> None:
        cache = MemoryCache()
        cache.set("k", ["col1"], [["val1"]], ttl_seconds=60)
        result = cache.get("k")
        assert result is not None
        headers, rows = result
        assert headers == ["col1"]
        assert rows == [["val1"]]

    def test_get_missing_returns_none(self) -> None:
        cache = MemoryCache()
        assert cache.get("missing") is None

    def test_ttl_expiration(self) -> None:
        cache = MemoryCache()
        cache.set("k", ["col1"], [["val1"]], ttl_seconds=0)
        # TTL of 0 means it expires immediately
        time.sleep(0.01)
        assert cache.get("k") is None

    def test_invalidate(self) -> None:
        cache = MemoryCache()
        cache.set("k", ["col1"], [["val1"]], ttl_seconds=60)
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_invalidate_missing_key_no_error(self) -> None:
        cache = MemoryCache()
        cache.invalidate("nonexistent")  # Should not raise

    def test_clear(self) -> None:
        cache = MemoryCache()
        cache.set("a", ["c1"], [[1]], ttl_seconds=60)
        cache.set("b", ["c2"], [[2]], ttl_seconds=60)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_stores_complex_data(self) -> None:
        cache = MemoryCache()
        headers = ["id", "name", "active"]
        rows = [[1, "Alice", True], [2, "Bob", False], [3, None, None]]
        cache.set("k", headers, rows, ttl_seconds=60)
        result = cache.get("k")
        assert result is not None
        assert result[0] == headers
        assert result[1] == rows


class TestRedisCache:
    """Tests for Redis cache backend using fakeredis."""

    @pytest.fixture(autouse=True)
    def _check_fakeredis(self) -> None:
        pytest.importorskip("fakeredis")

    def _make_cache(self):  # type: ignore[return]  # noqa: PLC0415
        import fakeredis  # noqa: PLC0415

        from mysql_to_sheets.core.query_cache import RedisCache  # noqa: PLC0415

        cache = RedisCache.__new__(RedisCache)
        cache._client = fakeredis.FakeRedis()
        cache._prefix = "query_cache:"
        return cache

    def test_set_and_get(self) -> None:
        cache = self._make_cache()
        cache.set("k", ["col1"], [["val1"]], ttl_seconds=60)
        result = cache.get("k")
        assert result is not None
        assert result[0] == ["col1"]
        assert result[1] == [["val1"]]

    def test_get_missing_returns_none(self) -> None:
        cache = self._make_cache()
        assert cache.get("missing") is None

    def test_invalidate(self) -> None:
        cache = self._make_cache()
        cache.set("k", ["col1"], [["val1"]], ttl_seconds=60)
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_clear(self) -> None:
        cache = self._make_cache()
        cache.set("a", ["c1"], [[1]], ttl_seconds=60)
        cache.set("b", ["c2"], [[2]], ttl_seconds=60)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


class TestGetQueryCache:
    """Tests for the cache singleton factory."""

    def setup_method(self) -> None:
        reset_query_cache()

    def teardown_method(self) -> None:
        reset_query_cache()

    def test_returns_memory_cache_by_default(self) -> None:
        cache = get_query_cache()
        assert isinstance(cache, MemoryCache)

    def test_singleton(self) -> None:
        cache1 = get_query_cache()
        cache2 = get_query_cache()
        assert cache1 is cache2

    def test_reset_clears_singleton(self) -> None:
        cache1 = get_query_cache()
        reset_query_cache()
        cache2 = get_query_cache()
        assert cache1 is not cache2


class TestProtocols:
    """Tests for SyncConfigProtocol."""

    def test_config_satisfies_protocol(self) -> None:
        from mysql_to_sheets.core.config import Config
        from mysql_to_sheets.core.protocols import SyncConfigProtocol

        assert isinstance(Config(), SyncConfigProtocol)
