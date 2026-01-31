"""Tests for integrations model and repository."""

import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from mysql_to_sheets.models.integrations import (
    VALID_INTEGRATION_TYPES,
    Integration,
    IntegrationCredentials,
    IntegrationRepository,
    reset_integration_repository,
)


class TestIntegrationCredentials:
    """Tests for IntegrationCredentials dataclass."""

    def test_empty_credentials(self):
        """Default credentials are empty."""
        creds = IntegrationCredentials()
        assert creds.is_empty()
        assert creds.to_dict() == {}

    def test_database_credentials(self):
        """Database credentials have user and password."""
        creds = IntegrationCredentials(user="dbuser", password="secret")
        assert not creds.is_empty()
        assert creds.to_dict() == {"user": "dbuser", "password": "secret"}

    def test_sheets_credentials(self):
        """Sheets credentials have service account JSON."""
        creds = IntegrationCredentials(
            service_account_json='{"type": "service_account"}'
        )
        assert not creds.is_empty()
        assert "service_account_json" in creds.to_dict()

    def test_from_dict(self):
        """Can create credentials from dict."""
        data = {"user": "test", "password": "pass", "api_key": "key123"}
        creds = IntegrationCredentials.from_dict(data)
        assert creds.user == "test"
        assert creds.password == "pass"
        assert creds.api_key == "key123"


class TestIntegration:
    """Tests for Integration dataclass."""

    def test_minimal_integration(self):
        """Can create integration with required fields only."""
        integration = Integration(
            name="test-db",
            integration_type="mysql",
            organization_id=1,
        )
        assert integration.name == "test-db"
        assert integration.integration_type == "mysql"
        assert integration.is_active is True

    def test_full_database_integration(self):
        """Can create full database integration."""
        integration = Integration(
            name="production-mysql",
            integration_type="mysql",
            organization_id=1,
            description="Production database",
            host="db.example.com",
            port=3306,
            database_name="myapp",
            ssl_mode="require",
            credentials=IntegrationCredentials(
                user="prod_user",
                password="secret123",
            ),
        )
        assert integration.host == "db.example.com"
        assert integration.database_name == "myapp"
        assert integration.credentials.user == "prod_user"

    def test_sheets_integration(self):
        """Can create Google Sheets integration."""
        integration = Integration(
            name="reports-sheet",
            integration_type="google_sheets",
            organization_id=1,
            sheet_id="abc123",
            worksheet_name="Data",
            credentials=IntegrationCredentials(
                service_account_json='{"type": "service_account"}',
            ),
        )
        assert integration.sheet_id == "abc123"
        assert integration.credentials.service_account_json is not None

    def test_to_dict_without_credentials(self):
        """to_dict excludes credentials by default."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            credentials=IntegrationCredentials(password="secret"),
        )
        data = integration.to_dict(include_credentials=False)
        assert "credentials" not in data
        assert data["has_credentials"] is True

    def test_to_dict_with_credentials(self):
        """to_dict includes credentials when requested."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            credentials=IntegrationCredentials(password="secret"),
        )
        data = integration.to_dict(include_credentials=True)
        assert "credentials" in data
        assert data["credentials"]["password"] == "secret"

    def test_from_dict(self):
        """Can create integration from dict."""
        data = {
            "name": "test-db",
            "integration_type": "postgres",
            "organization_id": 1,
            "host": "localhost",
            "port": 5432,
            "database_name": "testdb",
            "credentials": {"user": "test", "password": "pass"},
        }
        integration = Integration.from_dict(data)
        assert integration.name == "test-db"
        assert integration.integration_type == "postgres"
        assert integration.credentials.user == "test"


class TestIntegrationValidation:
    """Tests for integration validation."""

    def test_validate_valid_mysql(self):
        """Valid MySQL integration passes validation."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        errors = integration.validate()
        assert errors == []

    def test_validate_missing_name(self):
        """Missing name fails validation."""
        integration = Integration(
            name="",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        errors = integration.validate()
        assert any("Name" in e for e in errors)

    def test_validate_invalid_type(self):
        """Invalid type fails validation."""
        integration = Integration(
            name="test",
            integration_type="invalid",
            organization_id=1,
        )
        errors = integration.validate()
        assert any("integration_type" in e for e in errors)

    def test_validate_mysql_missing_host(self):
        """MySQL without host fails validation."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            database_name="testdb",
        )
        errors = integration.validate()
        assert any("Host" in e for e in errors)

    def test_validate_mysql_missing_database(self):
        """MySQL without database fails validation."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
        )
        errors = integration.validate()
        assert any("Database" in e for e in errors)

    def test_validate_sheets_missing_service_account(self):
        """Sheets without service account fails validation."""
        integration = Integration(
            name="test",
            integration_type="google_sheets",
            organization_id=1,
        )
        errors = integration.validate()
        assert any("service account" in e.lower() for e in errors)

    def test_valid_integration_types(self):
        """All valid integration types are defined."""
        assert "mysql" in VALID_INTEGRATION_TYPES
        assert "postgres" in VALID_INTEGRATION_TYPES
        assert "sqlite" in VALID_INTEGRATION_TYPES
        assert "mssql" in VALID_INTEGRATION_TYPES
        assert "google_sheets" in VALID_INTEGRATION_TYPES


class TestIntegrationRepository:
    """Tests for IntegrationRepository."""

    @pytest.fixture
    def db_path(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def encryption_key(self):
        """Set up encryption key."""
        from mysql_to_sheets.core.encryption import generate_encryption_key, reset_encryption

        reset_encryption()
        key = generate_encryption_key()
        with patch.dict(os.environ, {"INTEGRATION_ENCRYPTION_KEY": key}):
            yield key
        reset_encryption()

    @pytest.fixture
    def repo(self, db_path, encryption_key):
        """Create repository with temp database."""
        reset_integration_repository()
        return IntegrationRepository(db_path)

    def test_create_integration(self, repo):
        """Can create integration."""
        integration = Integration(
            name="test-mysql",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            port=3306,
            database_name="testdb",
            credentials=IntegrationCredentials(user="test", password="secret"),
        )
        created = repo.create(integration)
        assert created.id is not None
        assert created.name == "test-mysql"

    def test_create_duplicate_name_fails(self, repo):
        """Creating duplicate name in same org fails."""
        integration = Integration(
            name="duplicate",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        repo.create(integration)

        with pytest.raises(ValueError, match="already exists"):
            repo.create(integration)

    def test_create_same_name_different_org(self, repo):
        """Same name in different org is allowed."""
        integration1 = Integration(
            name="shared-name",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        integration2 = Integration(
            name="shared-name",
            integration_type="mysql",
            organization_id=2,
            host="localhost",
            database_name="testdb",
        )
        repo.create(integration1)
        created2 = repo.create(integration2)
        assert created2.id is not None

    def test_get_by_id(self, repo):
        """Can get integration by ID."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
            credentials=IntegrationCredentials(password="secret"),
        )
        created = repo.create(integration)

        retrieved = repo.get_by_id(created.id, 1)  # type: ignore
        assert retrieved is not None
        assert retrieved.name == "test"
        assert retrieved.credentials.password == "secret"

    def test_get_by_id_wrong_org(self, repo):
        """Cannot get integration from different org."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        created = repo.create(integration)

        retrieved = repo.get_by_id(created.id, 999)  # type: ignore
        assert retrieved is None

    def test_get_by_name(self, repo):
        """Can get integration by name."""
        integration = Integration(
            name="named-integration",
            integration_type="postgres",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        repo.create(integration)

        retrieved = repo.get_by_name("named-integration", 1)
        assert retrieved is not None
        assert retrieved.integration_type == "postgres"

    def test_get_all(self, repo):
        """Can get all integrations in org."""
        for i in range(3):
            repo.create(
                Integration(
                    name=f"integration-{i}",
                    integration_type="mysql",
                    organization_id=1,
                    host="localhost",
                    database_name="testdb",
                )
            )

        integrations = repo.get_all(1)
        assert len(integrations) == 3

    def test_get_all_with_type_filter(self, repo):
        """Can filter by integration type."""
        repo.create(
            Integration(
                name="mysql-1",
                integration_type="mysql",
                organization_id=1,
                host="localhost",
                database_name="testdb",
            )
        )
        repo.create(
            Integration(
                name="postgres-1",
                integration_type="postgres",
                organization_id=1,
                host="localhost",
                database_name="testdb",
            )
        )

        mysql_only = repo.get_all(1, integration_type="mysql")
        assert len(mysql_only) == 1
        assert mysql_only[0].integration_type == "mysql"

    def test_update_integration(self, repo):
        """Can update integration."""
        integration = Integration(
            name="original",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="original-db",
        )
        created = repo.create(integration)

        created.database_name = "updated-db"
        updated = repo.update(created)
        assert updated.database_name == "updated-db"

    def test_update_credentials(self, repo):
        """Can update credentials."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
            credentials=IntegrationCredentials(password="old-pass"),
        )
        created = repo.create(integration)

        created.credentials = IntegrationCredentials(password="new-pass")
        updated = repo.update(created)

        # Verify by fetching fresh
        retrieved = repo.get_by_id(updated.id, 1)  # type: ignore
        assert retrieved is not None
        assert retrieved.credentials.password == "new-pass"

    def test_delete_integration(self, repo):
        """Can delete integration."""
        integration = Integration(
            name="to-delete",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        created = repo.create(integration)

        result = repo.delete(created.id, 1)  # type: ignore
        assert result is True

        retrieved = repo.get_by_id(created.id, 1)  # type: ignore
        assert retrieved is None

    def test_deactivate_integration(self, repo):
        """Can soft-delete integration."""
        integration = Integration(
            name="to-deactivate",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        created = repo.create(integration)

        result = repo.deactivate(created.id, 1)  # type: ignore
        assert result is True

        retrieved = repo.get_by_id(created.id, 1)  # type: ignore
        assert retrieved is not None
        assert retrieved.is_active is False

    def test_activate_integration(self, repo):
        """Can reactivate integration."""
        integration = Integration(
            name="to-activate",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
            is_active=False,
        )
        created = repo.create(integration)
        repo.deactivate(created.id, 1)  # type: ignore

        result = repo.activate(created.id, 1)  # type: ignore
        assert result is True

        retrieved = repo.get_by_id(created.id, 1)  # type: ignore
        assert retrieved is not None
        assert retrieved.is_active is True

    def test_count_integrations(self, repo):
        """Can count integrations."""
        for i in range(5):
            repo.create(
                Integration(
                    name=f"integration-{i}",
                    integration_type="mysql" if i % 2 == 0 else "postgres",
                    organization_id=1,
                    host="localhost",
                    database_name="testdb",
                )
            )

        total = repo.count(1)
        assert total == 5

        mysql_count = repo.count(1, integration_type="mysql")
        assert mysql_count == 3

    def test_update_verified_at(self, repo):
        """Can update last_verified_at timestamp."""
        integration = Integration(
            name="test",
            integration_type="mysql",
            organization_id=1,
            host="localhost",
            database_name="testdb",
        )
        created = repo.create(integration)
        assert created.last_verified_at is None

        result = repo.update_verified_at(created.id, 1)  # type: ignore
        assert result is True

        retrieved = repo.get_by_id(created.id, 1)  # type: ignore
        assert retrieved is not None
        assert retrieved.last_verified_at is not None
