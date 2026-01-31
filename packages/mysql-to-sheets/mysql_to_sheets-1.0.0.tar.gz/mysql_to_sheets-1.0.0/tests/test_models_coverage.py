"""Tests for model repositories to increase coverage.

Tests for sync_configs, favorites, and webhooks repositories.
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mysql_to_sheets.models.favorites import (
    FavoriteQuery,
    FavoriteQueryRepository,
    FavoriteSheet,
    FavoriteSheetRepository,
    reset_favorite_query_repository,
    reset_favorite_sheet_repository,
)
from mysql_to_sheets.models.repository import clear_tenant, set_tenant
from mysql_to_sheets.models.sync_configs import (
    SyncConfigDefinition,
    SyncConfigRepository,
    reset_sync_config_repository,
)
from mysql_to_sheets.models.webhooks import (
    WebhookDelivery,
    WebhookRepository,
    WebhookSubscription,
    reset_webhook_repository,
)


class TestSyncConfigRepository:
    """Tests for SyncConfigRepository."""

    def setup_method(self):
        """Create temp database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_configs.db")
        self.repo = SyncConfigRepository(self.db_path)
        reset_sync_config_repository()
        set_tenant(1)

    def teardown_method(self):
        """Clean up temp files."""
        clear_tenant()
        reset_sync_config_repository()
        Path(self.db_path).unlink(missing_ok=True)
        Path(self.temp_dir).rmdir()

    def test_create_config(self):
        """Test creating a sync config."""
        config = SyncConfigDefinition(
            name="test-config",
            sql_query="SELECT * FROM users",
            sheet_id="ABC123",
            organization_id=1,
            description="Test config",
            sync_mode="replace",
            column_case="title",
        )

        created = self.repo.create(config)

        assert created.id is not None
        assert created.name == "test-config"
        assert created.sql_query == "SELECT * FROM users"
        assert created.created_at is not None

    def test_create_config_with_column_mapping(self):
        """Test creating config with column mapping."""
        config = SyncConfigDefinition(
            name="mapped-config",
            sql_query="SELECT id, name FROM users",
            sheet_id="XYZ789",
            organization_id=1,
            column_mapping={"id": "User ID", "name": "Full Name"},
            column_order=["Full Name", "User ID"],
        )

        created = self.repo.create(config)

        assert created.column_mapping == {"id": "User ID", "name": "Full Name"}
        assert created.column_order == ["Full Name", "User ID"]

    def test_create_duplicate_name_fails(self):
        """Test that duplicate names fail."""
        config1 = SyncConfigDefinition(
            name="duplicate",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        self.repo.create(config1)

        config2 = SyncConfigDefinition(
            name="duplicate",
            sql_query="SELECT 2",
            sheet_id="DEF",
            organization_id=1,
        )

        with pytest.raises(ValueError, match="already exists"):
            self.repo.create(config2)

    def test_create_invalid_sync_mode_fails(self):
        """Test that invalid sync mode fails validation."""
        config = SyncConfigDefinition(
            name="invalid",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
            sync_mode="invalid_mode",
        )

        with pytest.raises(ValueError, match="Invalid sync_mode"):
            self.repo.create(config)

    def test_create_invalid_column_case_fails(self):
        """Test that invalid column case fails validation."""
        config = SyncConfigDefinition(
            name="invalid",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
            column_case="invalid_case",
        )

        with pytest.raises(ValueError, match="Invalid column_case"):
            self.repo.create(config)

    def test_get_by_id(self):
        """Test retrieving config by ID."""
        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        found = self.repo.get_by_id(created.id, organization_id=1)

        assert found is not None
        assert found.id == created.id
        assert found.name == "test"

    def test_get_by_id_wrong_org_returns_none(self):
        """Test that wrong organization returns None."""
        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        # Set tenant to different org before querying
        set_tenant(999)
        found = self.repo.get_by_id(created.id, organization_id=999)

        assert found is None

    def test_get_by_name(self):
        """Test retrieving config by name."""
        config = SyncConfigDefinition(
            name="named-config",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        self.repo.create(config)

        found = self.repo.get_by_name("named-config", organization_id=1)

        assert found is not None
        assert found.name == "named-config"

    def test_get_all_configs(self):
        """Test retrieving all configs."""
        for i in range(3):
            config = SyncConfigDefinition(
                name=f"config-{i}",
                sql_query=f"SELECT {i}",
                sheet_id="ABC",
                organization_id=1,
            )
            self.repo.create(config)

        all_configs = self.repo.get_all(organization_id=1)

        assert len(all_configs) == 3
        assert sorted([c.name for c in all_configs]) == ["config-0", "config-1", "config-2"]

    def test_get_all_enabled_only(self):
        """Test retrieving only enabled configs."""
        config1 = SyncConfigDefinition(
            name="enabled",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
            enabled=True,
        )
        config2 = SyncConfigDefinition(
            name="disabled",
            sql_query="SELECT 2",
            sheet_id="DEF",
            organization_id=1,
            enabled=False,
        )
        self.repo.create(config1)
        self.repo.create(config2)

        enabled = self.repo.get_all(organization_id=1, enabled_only=True)

        assert len(enabled) == 1
        assert enabled[0].name == "enabled"

    def test_get_all_with_pagination(self):
        """Test pagination."""
        for i in range(5):
            config = SyncConfigDefinition(
                name=f"config-{i}",
                sql_query=f"SELECT {i}",
                sheet_id="ABC",
                organization_id=1,
            )
            self.repo.create(config)

        page1 = self.repo.get_all(organization_id=1, limit=2, offset=0)
        page2 = self.repo.get_all(organization_id=1, limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].name != page2[0].name

    def test_update_config(self):
        """Test updating a config."""
        config = SyncConfigDefinition(
            name="original",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        created.name = "updated"
        created.sql_query = "SELECT 2"
        created.description = "Updated description"

        updated = self.repo.update(created)

        assert updated.name == "updated"
        assert updated.sql_query == "SELECT 2"
        assert updated.description == "Updated description"
        assert updated.updated_at is not None

    def test_update_without_id_fails(self):
        """Test that update without ID fails."""
        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )

        with pytest.raises(ValueError, match="ID is required"):
            self.repo.update(config)

    def test_update_nonexistent_fails(self):
        """Test updating nonexistent config fails."""
        config = SyncConfigDefinition(
            id=999,
            name="test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )

        with pytest.raises(ValueError, match="not found"):
            self.repo.update(config)

    def test_update_to_duplicate_name_fails(self):
        """Test renaming to duplicate name fails."""
        config1 = SyncConfigDefinition(
            name="first",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        config2 = SyncConfigDefinition(
            name="second",
            sql_query="SELECT 2",
            sheet_id="DEF",
            organization_id=1,
        )
        self.repo.create(config1)
        created2 = self.repo.create(config2)

        created2.name = "first"

        with pytest.raises(ValueError, match="already exists"):
            self.repo.update(created2)

    def test_delete_config(self):
        """Test deleting a config."""
        config = SyncConfigDefinition(
            name="to-delete",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        result = self.repo.delete(created.id, organization_id=1)

        assert result is True
        assert self.repo.get_by_id(created.id, organization_id=1) is None

    def test_delete_nonexistent_returns_false(self):
        """Test deleting nonexistent config returns False."""
        result = self.repo.delete(999, organization_id=1)
        assert result is False

    def test_enable_disable_config(self):
        """Test enabling and disabling configs."""
        config = SyncConfigDefinition(
            name="toggle",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
            enabled=True,
        )
        created = self.repo.create(config)

        # Disable
        result = self.repo.disable(created.id, organization_id=1)
        assert result is True

        disabled = self.repo.get_by_id(created.id, organization_id=1)
        assert disabled.enabled is False

        # Enable
        result = self.repo.enable(created.id, organization_id=1)
        assert result is True

        enabled = self.repo.get_by_id(created.id, organization_id=1)
        assert enabled.enabled is True

    def test_count_configs(self):
        """Test counting configs."""
        for i in range(3):
            config = SyncConfigDefinition(
                name=f"config-{i}",
                sql_query=f"SELECT {i}",
                sheet_id="ABC",
                organization_id=1,
                enabled=(i < 2),
            )
            self.repo.create(config)

        total = self.repo.count(organization_id=1)
        enabled_only = self.repo.count(organization_id=1, enabled_only=True)

        assert total == 3
        assert enabled_only == 2

    def test_update_freshness(self):
        """Test updating freshness tracking."""
        config = SyncConfigDefinition(
            name="fresh",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        # Update with success
        result = self.repo.update_freshness(
            created.id,
            organization_id=1,
            success=True,
            row_count=100,
        )

        assert result is True

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.last_sync_at is not None
        assert updated.last_success_at is not None
        assert updated.last_row_count == 100

    def test_update_freshness_failure(self):
        """Test updating freshness after failure."""
        config = SyncConfigDefinition(
            name="stale",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        result = self.repo.update_freshness(
            created.id,
            organization_id=1,
            success=False,
        )

        assert result is True

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.last_sync_at is not None
        assert updated.last_success_at is None

    def test_update_sla(self):
        """Test updating SLA threshold."""
        config = SyncConfigDefinition(
            name="sla-test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        result = self.repo.update_sla(
            created.id,
            organization_id=1,
            sla_minutes=120,
        )

        assert result is True

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.sla_minutes == 120

    def test_update_sla_invalid_value_fails(self):
        """Test that invalid SLA value fails."""
        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        with pytest.raises(ValueError, match="at least 1"):
            self.repo.update_sla(created.id, organization_id=1, sla_minutes=0)

    def test_update_last_alert(self):
        """Test updating last alert timestamp."""
        config = SyncConfigDefinition(
            name="alert-test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
        )
        created = self.repo.create(config)

        result = self.repo.update_last_alert(created.id, organization_id=1)

        assert result is True

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.last_alert_at is not None

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        config = SyncConfigDefinition(
            name="serialize-test",
            sql_query="SELECT 1",
            sheet_id="ABC",
            organization_id=1,
            column_mapping={"a": "A"},
            column_order=["A"],
            created_at=datetime(2024, 1, 15, 10, 30, 0),
        )

        # Test to_dict
        data = config.to_dict()
        assert data["name"] == "serialize-test"
        assert data["column_mapping"] == {"a": "A"}
        assert "2024-01-15" in data["created_at"]

        # Test from_dict
        restored = SyncConfigDefinition.from_dict(data)
        assert restored.name == config.name
        assert restored.column_mapping == config.column_mapping


class TestFavoriteQueryRepository:
    """Tests for FavoriteQueryRepository."""

    def setup_method(self):
        """Create temp database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_favorites.db")
        self.repo = FavoriteQueryRepository(self.db_path)
        reset_favorite_query_repository()
        set_tenant(1)

    def teardown_method(self):
        """Clean up temp files."""
        clear_tenant()
        reset_favorite_query_repository()
        Path(self.db_path).unlink(missing_ok=True)
        Path(self.temp_dir).rmdir()

    def test_create_favorite_query(self):
        """Test creating a favorite query."""
        fav = FavoriteQuery(
            name="daily-users",
            sql_query="SELECT * FROM users WHERE created_at >= CURDATE()",
            organization_id=1,
            description="Daily active users",
            tags=["users", "daily"],
        )

        created = self.repo.create(fav)

        assert created.id is not None
        assert created.name == "daily-users"
        assert created.tags == ["users", "daily"]

    def test_create_shared_favorite(self):
        """Test creating a shared (non-private) favorite."""
        fav = FavoriteQuery(
            name="shared-query",
            sql_query="SELECT 1",
            organization_id=1,
            is_private=False,
        )

        created = self.repo.create(fav)
        assert created.is_private is False

    def test_create_private_favorite(self):
        """Test creating a private favorite."""
        fav = FavoriteQuery(
            name="private-query",
            sql_query="SELECT 1",
            organization_id=1,
            created_by_user_id=42,
            is_private=True,
        )

        created = self.repo.create(fav)
        assert created.is_private is True

    def test_create_duplicate_shared_name_fails(self):
        """Test that duplicate shared names fail."""
        fav1 = FavoriteQuery(
            name="duplicate",
            sql_query="SELECT 1",
            organization_id=1,
            is_private=False,
        )
        self.repo.create(fav1)

        fav2 = FavoriteQuery(
            name="duplicate",
            sql_query="SELECT 2",
            organization_id=1,
            is_private=False,
        )

        with pytest.raises(ValueError, match="already exists"):
            self.repo.create(fav2)

    def test_get_by_id(self):
        """Test retrieving favorite by ID."""
        fav = FavoriteQuery(
            name="test-query",
            sql_query="SELECT 1",
            organization_id=1,
        )
        created = self.repo.create(fav)

        found = self.repo.get_by_id(created.id, organization_id=1)

        assert found is not None
        assert found.id == created.id

    def test_get_by_name(self):
        """Test retrieving favorite by name."""
        fav = FavoriteQuery(
            name="named-query",
            sql_query="SELECT 1",
            organization_id=1,
        )
        self.repo.create(fav)

        found = self.repo.get_by_name("named-query", organization_id=1)

        assert found is not None
        assert found.name == "named-query"

    def test_visibility_filter_shows_shared(self):
        """Test that shared favorites are visible to all."""
        fav = FavoriteQuery(
            name="shared",
            sql_query="SELECT 1",
            organization_id=1,
            is_private=False,
        )
        self.repo.create(fav)

        # User 1 should see it
        found = self.repo.get_by_name("shared", organization_id=1, user_id=1)
        assert found is not None

        # User 2 should also see it
        found = self.repo.get_by_name("shared", organization_id=1, user_id=2)
        assert found is not None

    def test_visibility_filter_hides_others_private(self):
        """Test that private favorites are only visible to creator."""
        fav = FavoriteQuery(
            name="private",
            sql_query="SELECT 1",
            organization_id=1,
            created_by_user_id=1,
            is_private=True,
        )
        self.repo.create(fav)

        # Creator should see it
        found = self.repo.get_by_name("private", organization_id=1, user_id=1)
        assert found is not None

        # Other user should not see it
        found = self.repo.get_by_name("private", organization_id=1, user_id=2)
        assert found is None

    def test_get_all_queries(self):
        """Test retrieving all queries."""
        for i in range(3):
            fav = FavoriteQuery(
                name=f"query-{i}",
                sql_query=f"SELECT {i}",
                organization_id=1,
            )
            self.repo.create(fav)

        all_favs = self.repo.get_all(organization_id=1)

        assert len(all_favs) == 3

    def test_update_favorite(self):
        """Test updating a favorite."""
        fav = FavoriteQuery(
            name="original",
            sql_query="SELECT 1",
            organization_id=1,
        )
        created = self.repo.create(fav)

        created.name = "updated"
        created.description = "Updated description"
        created.tags = ["new", "tags"]

        updated = self.repo.update(created)

        assert updated.name == "updated"
        assert updated.description == "Updated description"
        assert updated.tags == ["new", "tags"]

    def test_delete_favorite(self):
        """Test hard deleting a favorite."""
        fav = FavoriteQuery(
            name="to-delete",
            sql_query="SELECT 1",
            organization_id=1,
        )
        created = self.repo.create(fav)

        result = self.repo.delete(created.id, organization_id=1)

        assert result is True
        assert self.repo.get_by_id(created.id, organization_id=1) is None

    def test_deactivate_favorite(self):
        """Test soft deleting (deactivating) a favorite."""
        fav = FavoriteQuery(
            name="to-deactivate",
            sql_query="SELECT 1",
            organization_id=1,
        )
        created = self.repo.create(fav)

        result = self.repo.deactivate(created.id, organization_id=1)

        assert result is True

        # Should not appear in default queries
        found = self.repo.get_by_id(created.id, organization_id=1)
        assert found is None

        # Should appear when including inactive
        all_favs = self.repo.get_all(organization_id=1, include_inactive=True)
        assert any(f.id == created.id for f in all_favs)

    def test_increment_use_count(self):
        """Test incrementing use count."""
        fav = FavoriteQuery(
            name="popular",
            sql_query="SELECT 1",
            organization_id=1,
        )
        created = self.repo.create(fav)

        self.repo.increment_use_count(created.id, organization_id=1)
        self.repo.increment_use_count(created.id, organization_id=1)

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.use_count == 2
        assert updated.last_used_at is not None

    def test_search_by_text(self):
        """Test searching favorites by text."""
        fav1 = FavoriteQuery(
            name="user analytics",
            sql_query="SELECT * FROM users",
            organization_id=1,
            description="Analytics for users",
        )
        fav2 = FavoriteQuery(
            name="sales report",
            sql_query="SELECT * FROM sales",
            organization_id=1,
        )
        self.repo.create(fav1)
        self.repo.create(fav2)

        results = self.repo.search(organization_id=1, query_text="user")

        assert len(results) >= 1
        assert any("user" in r.name.lower() or "user" in r.description.lower() for r in results)

    def test_search_by_tags(self):
        """Test searching favorites by tags."""
        fav1 = FavoriteQuery(
            name="query1",
            sql_query="SELECT 1",
            organization_id=1,
            tags=["analytics", "users"],
        )
        fav2 = FavoriteQuery(
            name="query2",
            sql_query="SELECT 2",
            organization_id=1,
            tags=["reporting", "sales"],
        )
        self.repo.create(fav1)
        self.repo.create(fav2)

        results = self.repo.search(organization_id=1, tags=["analytics"])

        assert len(results) >= 1
        assert any("analytics" in r.tags for r in results)

    def test_count_favorites(self):
        """Test counting favorites."""
        for i in range(3):
            fav = FavoriteQuery(
                name=f"query-{i}",
                sql_query=f"SELECT {i}",
                organization_id=1,
                is_active=(i < 2),
            )
            self.repo.create(fav)

        total = self.repo.count(organization_id=1, include_inactive=True)
        active_only = self.repo.count(organization_id=1, include_inactive=False)

        assert total == 3
        assert active_only == 2


class TestFavoriteSheetRepository:
    """Tests for FavoriteSheetRepository."""

    def setup_method(self):
        """Create temp database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_sheets.db")
        self.repo = FavoriteSheetRepository(self.db_path)
        reset_favorite_sheet_repository()
        set_tenant(1)

    def teardown_method(self):
        """Clean up temp files."""
        clear_tenant()
        reset_favorite_sheet_repository()
        Path(self.db_path).unlink(missing_ok=True)
        Path(self.temp_dir).rmdir()

    def test_create_favorite_sheet(self):
        """Test creating a favorite sheet."""
        fav = FavoriteSheet(
            name="sales-dashboard",
            sheet_id="ABC123XYZ",
            organization_id=1,
            description="Sales dashboard sheet",
            default_worksheet="Sales",
            tags=["dashboard", "sales"],
        )

        created = self.repo.create(fav)

        assert created.id is not None
        assert created.name == "sales-dashboard"
        assert created.sheet_id == "ABC123XYZ"
        assert created.default_worksheet == "Sales"

    def test_get_by_sheet_id(self):
        """Test retrieving by sheet ID."""
        fav = FavoriteSheet(
            name="unique-sheet",
            sheet_id="UNIQUE123",
            organization_id=1,
        )
        self.repo.create(fav)

        found = self.repo.get_by_sheet_id("UNIQUE123", organization_id=1)

        assert found is not None
        assert found.sheet_id == "UNIQUE123"

    def test_update_verified_timestamp(self):
        """Test updating verified timestamp."""
        fav = FavoriteSheet(
            name="verify-test",
            sheet_id="VERIFY123",
            organization_id=1,
        )
        created = self.repo.create(fav)

        result = self.repo.update_verified(created.id, organization_id=1)

        assert result is True

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.last_verified_at is not None

    def test_increment_use_count_sheet(self):
        """Test incrementing sheet use count."""
        fav = FavoriteSheet(
            name="popular-sheet",
            sheet_id="POPULAR123",
            organization_id=1,
        )
        created = self.repo.create(fav)

        self.repo.increment_use_count(created.id, organization_id=1)

        updated = self.repo.get_by_id(created.id, organization_id=1)
        assert updated.use_count == 1
        assert updated.last_used_at is not None


class TestWebhookRepository:
    """Tests for WebhookRepository."""

    def setup_method(self):
        """Create temp database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_webhooks.db")

        # Create users and organizations tables first (webhooks has foreign keys)
        from sqlalchemy import create_engine

        from mysql_to_sheets.models.organizations import Base as OrgsBase
        from mysql_to_sheets.models.users import Base as UsersBase

        engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        UsersBase.metadata.create_all(engine)
        OrgsBase.metadata.create_all(engine)
        engine.dispose()

        self.repo = WebhookRepository(self.db_path)
        reset_webhook_repository()
        set_tenant(1)

    def teardown_method(self):
        """Clean up temp files."""
        clear_tenant()
        reset_webhook_repository()
        Path(self.db_path).unlink(missing_ok=True)
        Path(self.temp_dir).rmdir()

    def test_create_webhook_subscription(self):
        """Test creating a webhook subscription."""
        sub = WebhookSubscription(
            name="sync-webhook",
            url="https://example.com/webhook",
            secret="test-secret",
            events=["sync.completed", "sync.failed"],
            organization_id=1,
            retry_count=3,
        )

        created = self.repo.create_subscription(sub)

        assert created.id is not None
        assert created.name == "sync-webhook"
        assert created.events == ["sync.completed", "sync.failed"]

    def test_create_webhook_with_custom_headers(self):
        """Test creating webhook with custom headers."""
        sub = WebhookSubscription(
            name="custom-headers",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
            headers={"X-Custom": "value"},
        )

        created = self.repo.create_subscription(sub)
        assert created.headers == {"X-Custom": "value"}

    def test_create_invalid_url_fails(self):
        """Test that invalid URL fails validation."""
        sub = WebhookSubscription(
            name="invalid",
            url="not-a-url",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )

        with pytest.raises(ValueError, match="must start with http"):
            self.repo.create_subscription(sub)

    def test_create_invalid_event_fails(self):
        """Test that invalid event type fails validation."""
        sub = WebhookSubscription(
            name="invalid-event",
            url="https://example.com/webhook",
            secret="secret",
            events=["invalid.event"],
            organization_id=1,
        )

        with pytest.raises(ValueError, match="Invalid event type"):
            self.repo.create_subscription(sub)

    def test_get_subscription_by_id(self):
        """Test retrieving subscription by ID."""
        sub = WebhookSubscription(
            name="test-sub",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created = self.repo.create_subscription(sub)

        found = self.repo.get_subscription_by_id(created.id, organization_id=1)

        assert found is not None
        assert found.id == created.id

    def test_get_subscriptions_for_event(self):
        """Test retrieving subscriptions for specific event."""
        sub1 = WebhookSubscription(
            name="sync-hook",
            url="https://example.com/sync",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        sub2 = WebhookSubscription(
            name="config-hook",
            url="https://example.com/config",
            secret="secret",
            events=["config.created"],
            organization_id=1,
        )
        self.repo.create_subscription(sub1)
        self.repo.create_subscription(sub2)

        sync_subs = self.repo.get_subscriptions_for_event("sync.completed", organization_id=1)

        assert len(sync_subs) == 1
        assert sync_subs[0].name == "sync-hook"

    def test_get_all_subscriptions(self):
        """Test retrieving all subscriptions."""
        for i in range(3):
            sub = WebhookSubscription(
                name=f"sub-{i}",
                url=f"https://example.com/webhook-{i}",
                secret="secret",
                events=["sync.completed"],
                organization_id=1,
            )
            self.repo.create_subscription(sub)

        all_subs = self.repo.get_all_subscriptions(organization_id=1)

        assert len(all_subs) == 3

    def test_update_subscription(self):
        """Test updating a subscription."""
        sub = WebhookSubscription(
            name="original",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created = self.repo.create_subscription(sub)

        created.name = "updated"
        created.url = "https://example.com/new-webhook"
        created.events = ["sync.completed", "sync.failed"]

        updated = self.repo.update_subscription(created)

        assert updated.name == "updated"
        assert updated.url == "https://example.com/new-webhook"
        assert len(updated.events) == 2

    def test_delete_subscription(self):
        """Test deleting a subscription."""
        sub = WebhookSubscription(
            name="to-delete",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created = self.repo.create_subscription(sub)

        result = self.repo.delete_subscription(created.id, organization_id=1)

        assert result is True
        assert self.repo.get_subscription_by_id(created.id, organization_id=1) is None

    def test_update_subscription_triggered_success(self):
        """Test updating subscription after successful delivery."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
            failure_count=2,
        )
        created = self.repo.create_subscription(sub)

        self.repo.update_subscription_triggered(created.id, success=True)

        updated = self.repo.get_subscription_by_id(created.id, organization_id=1)
        assert updated.failure_count == 0
        assert updated.last_triggered_at is not None

    def test_update_subscription_triggered_failure(self):
        """Test updating subscription after failed delivery."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created = self.repo.create_subscription(sub)

        self.repo.update_subscription_triggered(created.id, success=False)

        updated = self.repo.get_subscription_by_id(created.id, organization_id=1)
        assert updated.failure_count == 1

    def test_create_delivery(self):
        """Test creating a delivery record."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created_sub = self.repo.create_subscription(sub)

        delivery = WebhookDelivery(
            subscription_id=created_sub.id,
            delivery_id="del-123",
            event="sync.completed",
            payload={"rows": 100},
        )

        created = self.repo.create_delivery(delivery)

        assert created.id is not None
        assert created.delivery_id == "del-123"

    def test_update_delivery(self):
        """Test updating a delivery record."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created_sub = self.repo.create_subscription(sub)

        delivery = WebhookDelivery(
            subscription_id=created_sub.id,
            delivery_id="del-456",
            event="sync.completed",
            payload={"rows": 100},
        )
        created = self.repo.create_delivery(delivery)

        created.status = "success"
        created.response_code = 200
        created.completed_at = datetime.now(timezone.utc)

        updated = self.repo.update_delivery(created)

        assert updated.status == "success"
        assert updated.response_code == 200

    def test_get_deliveries_for_subscription(self):
        """Test retrieving delivery history."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created_sub = self.repo.create_subscription(sub)

        for i in range(3):
            delivery = WebhookDelivery(
                subscription_id=created_sub.id,
                delivery_id=f"del-{i}",
                event="sync.completed",
                payload={"rows": i * 10},
            )
            self.repo.create_delivery(delivery)

        deliveries = self.repo.get_deliveries_for_subscription(created_sub.id)

        assert len(deliveries) == 3

    def test_get_delivery_by_id(self):
        """Test retrieving delivery by ID."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="secret",
            events=["sync.completed"],
            organization_id=1,
        )
        created_sub = self.repo.create_subscription(sub)

        delivery = WebhookDelivery(
            subscription_id=created_sub.id,
            delivery_id="unique-del",
            event="sync.completed",
            payload={},
        )
        self.repo.create_delivery(delivery)

        found = self.repo.get_delivery_by_id("unique-del")

        assert found is not None
        assert found.delivery_id == "unique-del"

    def test_to_dict_includes_secret_when_requested(self):
        """Test that secret is included only when requested."""
        sub = WebhookSubscription(
            name="test",
            url="https://example.com/webhook",
            secret="super-secret",
            events=["sync.completed"],
            organization_id=1,
        )

        dict_without_secret = sub.to_dict(include_secret=False)
        dict_with_secret = sub.to_dict(include_secret=True)

        assert "secret" not in dict_without_secret
        assert dict_with_secret["secret"] == "super-secret"
