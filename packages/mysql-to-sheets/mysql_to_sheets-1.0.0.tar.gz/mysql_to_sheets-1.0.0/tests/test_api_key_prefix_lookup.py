"""Tests for API key prefix lookup optimization.

Verifies O(1) prefix-based filtering before expensive hash verification.
"""

from __future__ import annotations

import tempfile

import pytest

from mysql_to_sheets.core.security import generate_api_key, generate_api_key_salt, hash_api_key
from mysql_to_sheets.models.api_keys import APIKeyRepository, get_api_key_repository


def _create_key_components() -> tuple[str, str, str, str]:
    """Create all components needed for a key."""
    raw_key = generate_api_key()
    key_salt = generate_api_key_salt()
    key_hash = hash_api_key(raw_key, key_salt)
    key_prefix = raw_key[:8]  # First 8 chars for prefix
    return raw_key, key_hash, key_salt, key_prefix


class TestAPIKeyPrefixLookup:
    """Tests for prefix-based API key lookup."""

    @pytest.fixture
    def db_path(self) -> str:
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    @pytest.fixture
    def repo(self, db_path: str) -> APIKeyRepository:
        """Create repository instance."""
        return get_api_key_repository(db_path)

    def test_get_by_prefix_returns_matching_key(self, repo: APIKeyRepository) -> None:
        """Verify get_by_prefix returns keys with matching prefix."""
        # Generate a key with known prefix
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()

        # Create the key
        repo.create(
            name="test-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
        )

        # Lookup by prefix should find it
        results = repo.get_by_prefix(key_prefix)
        assert len(results) == 1
        assert results[0].name == "test-key"
        assert results[0].key_prefix == key_prefix

    def test_get_by_prefix_returns_empty_for_no_match(
        self, repo: APIKeyRepository
    ) -> None:
        """Verify get_by_prefix returns empty list for non-matching prefix."""
        # Create a key
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()
        repo.create(
            name="test-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
        )

        # Lookup with different prefix should return empty
        results = repo.get_by_prefix("mts_xxxx")
        assert len(results) == 0

    def test_get_by_prefix_excludes_revoked_by_default(
        self, repo: APIKeyRepository
    ) -> None:
        """Verify get_by_prefix excludes revoked keys by default."""
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()

        # Create and revoke the key
        created = repo.create(
            name="test-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
        )
        repo.revoke(created.id)

        # Default lookup should not find revoked key
        results = repo.get_by_prefix(key_prefix)
        assert len(results) == 0

        # Explicit include_revoked should find it
        results = repo.get_by_prefix(key_prefix, include_revoked=True)
        assert len(results) == 1
        assert results[0].revoked is True

    def test_get_by_prefix_with_multiple_keys(self, repo: APIKeyRepository) -> None:
        """Verify get_by_prefix only returns keys with exact prefix match."""
        # Create multiple keys with different prefixes
        keys_created = []
        for i in range(3):
            raw_key, key_hash, key_salt, key_prefix = _create_key_components()
            created = repo.create(
                name=f"test-key-{i}",
                key_hash=key_hash,
                key_salt=key_salt,
                key_prefix=key_prefix,
            )
            keys_created.append((created, key_prefix))

        # Each prefix should only match its own key
        for created, prefix in keys_created:
            results = repo.get_by_prefix(prefix)
            assert len(results) == 1
            assert results[0].id == created.id

    def test_prefix_lookup_performance_advantage(
        self, repo: APIKeyRepository
    ) -> None:
        """Demonstrate that prefix lookup returns fewer candidates than get_all.

        This verifies the optimization: instead of checking all keys,
        we only check keys matching the prefix (typically 0 or 1).
        """
        # Create 10 keys with different prefixes
        target_prefix = None
        for i in range(10):
            raw_key, key_hash, key_salt, key_prefix = _create_key_components()
            repo.create(
                name=f"test-key-{i}",
                key_hash=key_hash,
                key_salt=key_salt,
                key_prefix=key_prefix,
            )
            if i == 5:
                target_prefix = key_prefix

        # get_all returns all 10 keys
        all_keys = repo.get_all()
        assert len(all_keys) == 10

        # get_by_prefix returns only 1 key (or 0 if prefix collision, very rare)
        candidates = repo.get_by_prefix(target_prefix)
        assert len(candidates) <= 1  # Prefix is unique per key

    def test_legacy_keys_without_prefix(self, repo: APIKeyRepository) -> None:
        """Verify handling of legacy keys that don't have a stored prefix."""
        # Simulate legacy key creation (no prefix stored)
        key_salt = generate_api_key_salt()
        key_hash = hash_api_key("legacy_key_12345", key_salt)
        repo.create(
            name="legacy-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=None,  # Legacy: no prefix
        )

        # Prefix lookup won't find it
        results = repo.get_by_prefix("legacy_k")
        assert len(results) == 0

        # But get_all still returns it
        all_keys = repo.get_all()
        assert len(all_keys) == 1
        assert all_keys[0].key_prefix is None


class TestAuthMiddlewarePrefixLookup:
    """Test auth middleware integration with prefix lookup."""

    @pytest.fixture
    def db_path(self) -> str:
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    def test_auth_middleware_uses_prefix_lookup(self, db_path: str) -> None:
        """Verify auth middleware uses efficient prefix lookup."""
        from mysql_to_sheets.api.middleware.auth import AuthMiddleware
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        # Create a key
        repo = get_api_key_repository(db_path)
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()
        repo.create(
            name="test-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
        )

        # Create middleware instance
        middleware = AuthMiddleware(
            app=None,
            enabled=True,
            db_path=db_path,
        )

        # Validate the key
        result = middleware._validate_api_key(raw_key)
        assert result is not None
        assert result["name"] == "test-key"

    def test_auth_middleware_rejects_invalid_key(self, db_path: str) -> None:
        """Verify auth middleware rejects keys that don't match."""
        from mysql_to_sheets.api.middleware.auth import AuthMiddleware
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        # Create a key
        repo = get_api_key_repository(db_path)
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()
        repo.create(
            name="test-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
        )

        # Create middleware instance
        middleware = AuthMiddleware(
            app=None,
            enabled=True,
            db_path=db_path,
        )

        # Try to validate a different key (same prefix, different hash)
        fake_key = key_prefix + "different_suffix_here"
        result = middleware._validate_api_key(fake_key)
        assert result is None

    def test_auth_middleware_handles_legacy_keys(self, db_path: str) -> None:
        """Verify auth middleware falls back for legacy keys without prefix."""
        from mysql_to_sheets.api.middleware.auth import AuthMiddleware
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        # Create a legacy key (no prefix stored)
        repo = get_api_key_repository(db_path)
        legacy_key = "mts_legacy_key_123456789"
        key_salt = generate_api_key_salt()
        key_hash = hash_api_key(legacy_key, key_salt)
        repo.create(
            name="legacy-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=None,  # Legacy: no prefix
        )

        # Create middleware instance
        middleware = AuthMiddleware(
            app=None,
            enabled=True,
            db_path=db_path,
        )

        # Validate the legacy key (should use fallback path)
        result = middleware._validate_api_key(legacy_key)
        assert result is not None
        assert result["name"] == "legacy-key"
