"""Tests for the organizations module."""

import os
import tempfile
from datetime import datetime, timezone

import pytest

from mysql_to_sheets.models.organizations import (
    Organization,
    OrganizationModel,
    OrganizationRepository,
    get_organization_repository,
    reset_organization_repository,
)


class TestOrganization:
    """Tests for Organization dataclass."""

    def test_create_organization(self):
        """Test creating an organization."""
        org = Organization(
            name="Acme Corp",
            slug="acme-corp",
        )

        assert org.name == "Acme Corp"
        assert org.slug == "acme-corp"
        assert org.id is None
        assert org.is_active is True
        assert org.subscription_tier == "free"
        assert org.max_users == 5
        assert org.max_configs == 10

    def test_create_organization_with_settings(self):
        """Test creating an organization with custom settings."""
        settings = {"theme": "dark", "timezone": "UTC"}
        org = Organization(
            name="Premium Corp",
            slug="premium-corp",
            settings=settings,
            subscription_tier="pro",
            max_users=50,
            max_configs=100,
        )

        assert org.settings == settings
        assert org.subscription_tier == "pro"
        assert org.max_users == 50
        assert org.max_configs == 100

    def test_to_dict(self):
        """Test converting organization to dictionary."""
        org = Organization(
            id=1,
            name="Test Org",
            slug="test-org",
            is_active=True,
            settings={"key": "value"},
        )

        d = org.to_dict()

        assert d["id"] == 1
        assert d["name"] == "Test Org"
        assert d["slug"] == "test-org"
        assert d["is_active"] is True
        assert d["settings"] == {"key": "value"}
        assert d["subscription_tier"] == "free"

    def test_to_dict_with_created_at(self):
        """Test to_dict with created_at timestamp."""
        now = datetime.now(timezone.utc)
        org = Organization(
            name="Test Org",
            slug="test-org",
            created_at=now,
        )

        d = org.to_dict()
        assert d["created_at"] == now.isoformat()

    def test_from_dict(self):
        """Test creating organization from dictionary."""
        data = {
            "id": 1,
            "name": "From Dict Org",
            "slug": "from-dict-org",
            "is_active": True,
            "subscription_tier": "enterprise",
            "max_users": 100,
            "max_configs": 200,
        }

        org = Organization.from_dict(data)

        assert org.id == 1
        assert org.name == "From Dict Org"
        assert org.slug == "from-dict-org"
        assert org.subscription_tier == "enterprise"
        assert org.max_users == 100

    def test_from_dict_with_iso_timestamp(self):
        """Test from_dict with ISO timestamp string."""
        data = {
            "name": "Test",
            "slug": "test",
            "created_at": "2024-01-15T10:30:00+00:00",
        }

        org = Organization.from_dict(data)
        assert org.created_at is not None
        assert org.created_at.year == 2024
        assert org.created_at.month == 1


class TestOrganizationModel:
    """Tests for OrganizationModel SQLAlchemy model."""

    def test_from_dataclass(self):
        """Test creating model from dataclass."""
        org = Organization(
            name="Test Org",
            slug="test-org",
            settings={"key": "value"},
        )

        model = OrganizationModel.from_dataclass(org)

        assert model.name == "Test Org"
        assert model.slug == "test-org"
        assert model.is_active is True
        # Settings should be JSON-encoded
        assert '"key"' in model.settings

    def test_to_dataclass(self):
        """Test converting model to dataclass."""
        model = OrganizationModel(
            id=1,
            name="Model Org",
            slug="model-org",
            is_active=True,
            subscription_tier="pro",
            max_users=25,
            max_configs=50,
            created_at=datetime.now(timezone.utc),
        )

        org = model.to_dataclass()

        assert isinstance(org, Organization)
        assert org.id == 1
        assert org.name == "Model Org"
        assert org.subscription_tier == "pro"

    def test_repr(self):
        """Test string representation."""
        model = OrganizationModel(
            id=1,
            slug="test-org",
            is_active=True,
        )

        repr_str = repr(model)
        assert "id=1" in repr_str
        assert "test-org" in repr_str
        assert "active" in repr_str


class TestOrganizationRepository:
    """Tests for OrganizationRepository."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_organization_repository()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_organization_repository()

    def test_create_organization(self):
        """Test creating an organization through repository."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = Organization(name="New Org", slug="new-org")

            created = repo.create(org)

            assert created.id is not None
            assert created.id > 0
            assert created.name == "New Org"
            assert created.created_at is not None
        finally:
            os.unlink(db_path)

    def test_create_duplicate_slug_raises_error(self):
        """Test that duplicate slugs raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org1 = Organization(name="First Org", slug="same-slug")
            repo.create(org1)

            org2 = Organization(name="Second Org", slug="same-slug")

            with pytest.raises(ValueError) as exc_info:
                repo.create(org2)

            assert "already exists" in str(exc_info.value)
        finally:
            os.unlink(db_path)

    def test_get_by_id(self):
        """Test getting organization by ID."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = Organization(name="Test Org", slug="test-org")
            created = repo.create(org)

            found = repo.get_by_id(created.id)

            assert found is not None
            assert found.id == created.id
            assert found.name == "Test Org"
        finally:
            os.unlink(db_path)

    def test_get_by_id_not_found(self):
        """Test getting non-existent organization returns None."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            found = repo.get_by_id(999)
            assert found is None
        finally:
            os.unlink(db_path)

    def test_get_by_slug(self):
        """Test getting organization by slug."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = Organization(name="Slug Test", slug="slug-test")
            repo.create(org)

            found = repo.get_by_slug("slug-test")

            assert found is not None
            assert found.slug == "slug-test"
        finally:
            os.unlink(db_path)

    def test_get_all(self):
        """Test getting all organizations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            repo.create(Organization(name="Org 1", slug="org-1"))
            repo.create(Organization(name="Org 2", slug="org-2"))
            repo.create(Organization(name="Org 3", slug="org-3"))

            all_orgs = repo.get_all()

            assert len(all_orgs) == 3
        finally:
            os.unlink(db_path)

    def test_get_all_excludes_inactive_by_default(self):
        """Test that get_all excludes inactive orgs by default."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org1 = repo.create(Organization(name="Active", slug="active"))
            org2 = repo.create(Organization(name="Inactive", slug="inactive"))

            repo.deactivate(org2.id)

            all_orgs = repo.get_all()
            assert len(all_orgs) == 1
            assert all_orgs[0].slug == "active"
        finally:
            os.unlink(db_path)

    def test_get_all_include_inactive(self):
        """Test get_all with include_inactive=True."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org1 = repo.create(Organization(name="Active", slug="active"))
            org2 = repo.create(Organization(name="Inactive", slug="inactive"))

            repo.deactivate(org2.id)

            all_orgs = repo.get_all(include_inactive=True)
            assert len(all_orgs) == 2
        finally:
            os.unlink(db_path)

    def test_get_all_with_pagination(self):
        """Test get_all with limit and offset."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            for i in range(5):
                repo.create(Organization(name=f"Org {i}", slug=f"org-{i}"))

            page1 = repo.get_all(limit=2, offset=0)
            page2 = repo.get_all(limit=2, offset=2)

            assert len(page1) == 2
            assert len(page2) == 2
        finally:
            os.unlink(db_path)

    def test_update_organization(self):
        """Test updating an organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = repo.create(Organization(name="Original", slug="original"))

            org.name = "Updated"
            org.subscription_tier = "pro"
            updated = repo.update(org)

            assert updated.name == "Updated"
            assert updated.subscription_tier == "pro"

            # Verify in database
            found = repo.get_by_id(org.id)
            assert found.name == "Updated"
        finally:
            os.unlink(db_path)

    def test_update_without_id_raises_error(self):
        """Test that updating without ID raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = Organization(name="No ID", slug="no-id")

            with pytest.raises(ValueError) as exc_info:
                repo.update(org)

            assert "ID is required" in str(exc_info.value)
        finally:
            os.unlink(db_path)

    def test_update_slug_conflict_raises_error(self):
        """Test that updating to existing slug raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org1 = repo.create(Organization(name="Org 1", slug="org-1"))
            org2 = repo.create(Organization(name="Org 2", slug="org-2"))

            org2.slug = "org-1"

            with pytest.raises(ValueError) as exc_info:
                repo.update(org2)

            assert "already exists" in str(exc_info.value)
        finally:
            os.unlink(db_path)

    def test_delete_organization(self):
        """Test deleting an organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = repo.create(Organization(name="To Delete", slug="to-delete"))

            deleted = repo.delete(org.id)

            assert deleted is True
            assert repo.get_by_id(org.id) is None
        finally:
            os.unlink(db_path)

    def test_delete_nonexistent_returns_false(self):
        """Test deleting nonexistent organization returns False."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            deleted = repo.delete(999)
            assert deleted is False
        finally:
            os.unlink(db_path)

    def test_deactivate_organization(self):
        """Test soft-deleting an organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org = repo.create(Organization(name="To Deactivate", slug="to-deactivate"))

            deactivated = repo.deactivate(org.id)

            assert deactivated is True
            found = repo.get_by_id(org.id)
            assert found is not None
            assert found.is_active is False
        finally:
            os.unlink(db_path)

    def test_count(self):
        """Test counting organizations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            repo.create(Organization(name="Org 1", slug="org-1"))
            repo.create(Organization(name="Org 2", slug="org-2"))

            count = repo.count()
            assert count == 2
        finally:
            os.unlink(db_path)

    def test_count_exclude_inactive(self):
        """Test count excludes inactive by default."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = OrganizationRepository(db_path)
            org1 = repo.create(Organization(name="Active", slug="active"))
            org2 = repo.create(Organization(name="Inactive", slug="inactive"))
            repo.deactivate(org2.id)

            assert repo.count() == 1
            assert repo.count(include_inactive=True) == 2
        finally:
            os.unlink(db_path)


class TestOrganizationSingleton:
    """Tests for the organization repository singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_organization_repository()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_organization_repository()

    def test_get_organization_repository_requires_path(self):
        """Test that first call requires db_path."""
        with pytest.raises(ValueError) as exc_info:
            get_organization_repository()

        assert "db_path is required" in str(exc_info.value)

    def test_get_organization_repository_singleton(self):
        """Test that singleton returns same instance."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo1 = get_organization_repository(db_path)
            repo2 = get_organization_repository()  # Should work without path

            assert repo1 is repo2
        finally:
            reset_organization_repository()
            os.unlink(db_path)

    def test_reset_organization_repository(self):
        """Test resetting the singleton."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo1 = get_organization_repository(db_path)
            reset_organization_repository()

            # Should require path again after reset
            with pytest.raises(ValueError):
                get_organization_repository()
        finally:
            os.unlink(db_path)
