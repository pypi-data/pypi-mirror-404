"""Tests for API key scope functionality.

Verifies scope validation, hierarchy, and middleware enforcement.
"""

from __future__ import annotations

import tempfile

import pytest

from mysql_to_sheets.core.security import generate_api_key, generate_api_key_salt, hash_api_key


def _create_key_components() -> tuple[str, str, str, str]:
    """Create all components needed for a key."""
    raw_key = generate_api_key()
    key_salt = generate_api_key_salt()
    key_hash = hash_api_key(raw_key, key_salt)
    key_prefix = raw_key[:8]  # First 8 chars for prefix
    return raw_key, key_hash, key_salt, key_prefix


class TestAPIKeyScopes:
    """Tests for APIKeyModel scope functionality."""

    @pytest.fixture
    def db_path(self) -> str:
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    def test_has_scope_with_wildcard(self, db_path: str) -> None:
        """Verify wildcard scope grants all permissions."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["*"],
        )

        assert key.has_scope("read") is True
        assert key.has_scope("sync") is True
        assert key.has_scope("config") is True
        assert key.has_scope("admin") is True

    def test_has_scope_direct_match(self, db_path: str) -> None:
        """Verify direct scope match works."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["read", "sync"],
        )

        assert key.has_scope("read") is True
        assert key.has_scope("sync") is True
        assert key.has_scope("config") is False
        assert key.has_scope("admin") is False

    def test_has_scope_hierarchy_admin(self, db_path: str) -> None:
        """Verify admin scope includes all lower scopes."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["admin"],
        )

        assert key.has_scope("read") is True
        assert key.has_scope("sync") is True
        assert key.has_scope("config") is True
        assert key.has_scope("admin") is True

    def test_has_scope_hierarchy_config(self, db_path: str) -> None:
        """Verify config scope includes sync and read."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["config"],
        )

        assert key.has_scope("read") is True
        assert key.has_scope("sync") is True
        assert key.has_scope("config") is True
        assert key.has_scope("admin") is False

    def test_has_scope_hierarchy_sync(self, db_path: str) -> None:
        """Verify sync scope includes read."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["sync"],
        )

        assert key.has_scope("read") is True
        assert key.has_scope("sync") is True
        assert key.has_scope("config") is False
        assert key.has_scope("admin") is False

    def test_has_scope_read_only(self, db_path: str) -> None:
        """Verify read scope is the lowest level."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["read"],
        )

        assert key.has_scope("read") is True
        assert key.has_scope("sync") is False
        assert key.has_scope("config") is False
        assert key.has_scope("admin") is False

    def test_has_scope_empty_defaults_to_wildcard(self, db_path: str) -> None:
        """Verify empty scopes defaults to wildcard (backwards compat).

        Empty scopes list is treated as ["*"] for backwards compatibility
        with existing keys that might not have scopes set.
        """
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
        )
        # Empty list treated as wildcard for safety
        key.scopes = []

        # Empty list falls back to ["*"] behavior
        assert key.has_scope("read") is True
        assert key.has_scope("admin") is True

    def test_has_scope_none_defaults_to_wildcard(self, db_path: str) -> None:
        """Verify None scopes defaults to wildcard (legacy compat)."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=None,
        )

        # None is treated as ["*"] for backwards compatibility
        assert key.has_scope("read") is True
        assert key.has_scope("admin") is True

    def test_create_key_with_scopes(self, db_path: str) -> None:
        """Verify creating a key with specific scopes."""
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        repo = get_api_key_repository(db_path)

        key = repo.create(
            name="read-only-key",
            key_hash="hash123",
            key_salt="salt123",
            key_prefix="mts_read",
            scopes=["read"],
        )

        assert key.scopes == ["read"]
        assert key.has_scope("read") is True
        assert key.has_scope("sync") is False

    def test_create_key_defaults_to_wildcard(self, db_path: str) -> None:
        """Verify creating a key without scopes defaults to wildcard."""
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        repo = get_api_key_repository(db_path)

        key = repo.create(
            name="default-key",
            key_hash="hash456",
            key_salt="salt456",
            key_prefix="mts_dflt",
        )

        assert key.scopes == ["*"]
        assert key.has_scope("admin") is True

    def test_to_dict_includes_scopes(self, db_path: str) -> None:
        """Verify to_dict includes scopes."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        key = APIKeyModel(
            name="test",
            key_hash="hash",
            scopes=["read", "sync"],
        )

        data = key.to_dict()
        assert "scopes" in data
        assert data["scopes"] == ["read", "sync"]

    def test_from_dict_includes_scopes(self, db_path: str) -> None:
        """Verify from_dict parses scopes."""
        from mysql_to_sheets.models.api_keys import APIKeyModel

        data = {
            "name": "test",
            "key_hash": "hash",
            "scopes": ["config"],
        }

        key = APIKeyModel.from_dict(data)
        assert key.scopes == ["config"]


class TestScopeMiddleware:
    """Tests for scope enforcement middleware."""

    def test_get_required_scope_read_endpoints(self) -> None:
        """Verify GET endpoints require read scope."""
        from mysql_to_sheets.api.middleware.scope import get_required_scope

        assert get_required_scope("GET", "/api/v1/history") == "read"
        assert get_required_scope("GET", "/api/v1/configs") == "read"
        assert get_required_scope("GET", "/api/v1/configs/123") == "read"

    def test_get_required_scope_sync_endpoints(self) -> None:
        """Verify sync endpoints require sync scope."""
        from mysql_to_sheets.api.middleware.scope import get_required_scope

        assert get_required_scope("POST", "/api/v1/sync") == "sync"
        assert get_required_scope("POST", "/api/v1/validate") == "sync"

    def test_get_required_scope_config_endpoints(self) -> None:
        """Verify config management requires config scope."""
        from mysql_to_sheets.api.middleware.scope import get_required_scope

        assert get_required_scope("POST", "/api/v1/configs") == "config"
        assert get_required_scope("PUT", "/api/v1/configs") == "config"
        assert get_required_scope("DELETE", "/api/v1/configs") == "config"

    def test_get_required_scope_admin_endpoints(self) -> None:
        """Verify admin endpoints require admin scope."""
        from mysql_to_sheets.api.middleware.scope import get_required_scope

        assert get_required_scope("POST", "/api/v1/users") == "admin"
        assert get_required_scope("DELETE", "/api/v1/organizations") == "admin"

    def test_get_required_scope_exempt_endpoints(self) -> None:
        """Verify exempt endpoints return None."""
        from mysql_to_sheets.api.middleware.scope import get_required_scope

        assert get_required_scope("GET", "/api/v1/health") is None
        assert get_required_scope("GET", "/docs") is None

    def test_get_required_scope_unknown_defaults(self) -> None:
        """Verify unknown endpoints default to read/sync."""
        from mysql_to_sheets.api.middleware.scope import get_required_scope

        # Unknown GET defaults to read
        assert get_required_scope("GET", "/api/v1/unknown") == "read"
        # Unknown POST defaults to sync
        assert get_required_scope("POST", "/api/v1/unknown") == "sync"


class TestAuthMiddlewareScopeIntegration:
    """Tests for scope integration in auth middleware."""

    @pytest.fixture
    def db_path(self) -> str:
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            return f.name

    def test_auth_returns_scopes_in_key_info(self, db_path: str) -> None:
        """Verify auth middleware includes scopes in key_info."""
        from mysql_to_sheets.api.middleware.auth import AuthMiddleware
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        # Create a key with specific scopes
        repo = get_api_key_repository(db_path)
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()
        repo.create(
            name="test-key",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
            scopes=["read", "sync"],
        )

        # Create middleware and validate key
        middleware = AuthMiddleware(
            app=None,
            enabled=True,
            db_path=db_path,
        )

        result = middleware._validate_api_key(raw_key)
        assert result is not None
        assert "scopes" in result
        assert result["scopes"] == ["read", "sync"]
        assert "has_scope" in result
        assert callable(result["has_scope"])

    def test_auth_has_scope_function_works(self, db_path: str) -> None:
        """Verify has_scope function in key_info works correctly."""
        from mysql_to_sheets.api.middleware.auth import AuthMiddleware
        from mysql_to_sheets.models.api_keys import get_api_key_repository

        # Create a read-only key
        repo = get_api_key_repository(db_path)
        raw_key, key_hash, key_salt, key_prefix = _create_key_components()
        repo.create(
            name="read-only",
            key_hash=key_hash,
            key_salt=key_salt,
            key_prefix=key_prefix,
            scopes=["read"],
        )

        middleware = AuthMiddleware(
            app=None,
            enabled=True,
            db_path=db_path,
        )

        result = middleware._validate_api_key(raw_key)
        assert result is not None

        has_scope = result["has_scope"]
        assert has_scope("read") is True
        assert has_scope("sync") is False
        assert has_scope("admin") is False
