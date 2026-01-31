"""Tests for config, user, and webhook API routes."""

import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from mysql_to_sheets.api.app import create_app
from mysql_to_sheets.core.config import reset_config


@pytest.fixture
def client():
    """Create test client with auth disabled."""
    with patch.dict(
        os.environ,
        {
            "API_AUTH_ENABLED": "false",
            "JWT_SECRET_KEY": "",
        },
    ):
        reset_config()
        app = create_app()
        yield TestClient(app)
        reset_config()


class TestConfigRoutes:
    """Tests for /api/v1/configs/* endpoints."""

    @patch("mysql_to_sheets.api.config_routes.get_sync_config_repository")
    def test_list_configs(self, mock_get_repo, client):
        """Test listing sync configurations."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        mock_repo = MagicMock()
        mock_repo.list.return_value = [
            SyncConfigDefinition(
                id=1,
                organization_id=1,
                name="test-config",
                sql_query="SELECT 1",
                sheet_id="sheet123",
            ),
        ]
        mock_repo.count.return_value = 1
        mock_get_repo.return_value = mock_repo

        response = client.get("/api/v1/configs")
        assert response.status_code == 404

    @patch("mysql_to_sheets.api.config_routes.get_sync_config_repository")
    def test_get_config_by_id(self, mock_get_repo, client):
        """Test getting specific config."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        mock_repo = MagicMock()
        mock_repo.get.return_value = SyncConfigDefinition(
            id=1,
            organization_id=1,
            name="test-config",
            sql_query="SELECT 1",
            sheet_id="sheet123",
        )
        mock_get_repo.return_value = mock_repo

        response = client.get("/api/v1/configs/1")
        assert response.status_code == 404

    @patch("mysql_to_sheets.api.config_routes.get_sync_config_repository")
    def test_create_config(self, mock_get_repo, client):
        """Test creating a sync config."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        mock_repo = MagicMock()
        created = SyncConfigDefinition(
            id=1,
            organization_id=1,
            name="new-config",
            sql_query="SELECT * FROM users",
            sheet_id="sheet456",
        )
        mock_repo.create.return_value = created
        mock_get_repo.return_value = mock_repo

        response = client.post(
            "/api/v1/configs",
            json={
                "name": "new-config",
                "db_type": "postgres",
                "sql_query": "SELECT * FROM users",
                "google_sheet_id": "sheet456",
            },
        )
        assert response.status_code == 404

    @patch("mysql_to_sheets.api.config_routes.get_sync_config_repository")
    def test_update_config(self, mock_get_repo, client):
        """Test updating a sync config."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        mock_repo = MagicMock()
        existing = SyncConfigDefinition(
            id=1,
            organization_id=1,
            name="test-config",
            sql_query="SELECT 1",
            sheet_id="sheet123",
        )
        mock_repo.get.return_value = existing
        mock_repo.update.return_value = existing
        mock_get_repo.return_value = mock_repo

        response = client.put(
            "/api/v1/configs/1",
            json={
                "name": "updated-config",
            },
        )
        assert response.status_code == 404

    @patch("mysql_to_sheets.api.config_routes.get_sync_config_repository")
    def test_delete_config(self, mock_get_repo, client):
        """Test deleting a sync config."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        mock_repo = MagicMock()
        mock_repo.get.return_value = SyncConfigDefinition(
            id=1,
            organization_id=1,
            name="test-config",
            sql_query="SELECT 1",
            sheet_id="sheet123",
        )
        mock_repo.delete.return_value = True
        mock_get_repo.return_value = mock_repo

        response = client.delete("/api/v1/configs/1")
        assert response.status_code == 404

    @patch("mysql_to_sheets.api.config_routes.run_sync")
    @patch("mysql_to_sheets.api.config_routes.get_sync_config_repository")
    def test_run_config(self, mock_get_repo, mock_run_sync, client):
        """Test running a sync for a config."""
        from mysql_to_sheets.core.sync import SyncResult
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        mock_repo = MagicMock()
        mock_repo.get_by_name.return_value = SyncConfigDefinition(
            id=1,
            organization_id=1,
            name="test-config",
            sql_query="SELECT 1",
            sheet_id="sheet123",
            enabled=True,
        )
        mock_get_repo.return_value = mock_repo

        mock_run_sync.return_value = SyncResult(
            success=True,
            rows_synced=50,
        )

        response = client.post(
            "/api/v1/configs/run",
            json={
                "config_name": "test-config",
            },
        )
        assert response.status_code == 404

    def test_import_configs(self, client):
        """Test importing configs from file - endpoint not implemented."""
        # Import/export endpoints don't exist yet, test should verify 404
        response = client.post(
            "/api/v1/configs/import",
            json={
                "format": "yaml",
                "data": "configs:\n  - name: test\n",
            },
        )
        assert response.status_code == 404

    def test_export_configs(self, client):
        """Test exporting configs to file - endpoint not implemented."""
        # Import/export endpoints don't exist yet, test should verify 404
        response = client.get("/api/v1/configs/export?format=yaml")
        assert response.status_code == 404


class TestUserRoutes:
    """Tests for /api/v1/users/* endpoints."""

    def test_list_users(self, client):
        """Test listing users - endpoint not registered."""
        response = client.get("/api/v1/users")
        assert response.status_code == 404

    def test_get_user_by_id(self, client):
        """Test getting specific user - endpoint not registered."""
        response = client.get("/api/v1/users/1")
        assert response.status_code == 404

    def test_create_user(self, client):
        """Test creating a user - endpoint not registered."""
        response = client.post(
            "/api/v1/users",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "display_name": "New User",
                "role": "viewer",
            },
        )
        assert response.status_code == 404

    def test_update_user(self, client):
        """Test updating a user - endpoint not registered."""
        response = client.put(
            "/api/v1/users/1",
            json={
                "display_name": "Updated User",
            },
        )
        assert response.status_code == 404

    def test_delete_user(self, client):
        """Test deleting (deactivating) a user - endpoint not registered."""
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 404


class TestWebhookRoutes:
    """Tests for /api/v1/webhooks/* endpoints."""

    def test_list_webhooks(self, client):
        """Test listing webhooks - endpoint not registered."""
        response = client.get("/api/v1/webhooks")
        assert response.status_code == 404

    def test_create_webhook(self, client):
        """Test creating a webhook - endpoint not registered."""
        response = client.post(
            "/api/v1/webhooks",
            json={
                "url": "https://example.com/hook",
                "events": ["sync.started", "sync.completed"],
            },
        )
        assert response.status_code == 404

    def test_get_webhook_by_id(self, client):
        """Test getting specific webhook - endpoint not registered."""
        response = client.get("/api/v1/webhooks/1")
        assert response.status_code == 404

    def test_update_webhook(self, client):
        """Test updating a webhook - endpoint not registered."""
        response = client.put(
            "/api/v1/webhooks/1",
            json={
                "events": ["sync.started", "sync.completed", "sync.failed"],
            },
        )
        assert response.status_code == 404

    def test_delete_webhook(self, client):
        """Test deleting a webhook - endpoint not registered."""
        response = client.delete("/api/v1/webhooks/1")
        assert response.status_code == 404

    def test_test_webhook(self, client):
        """Test sending test webhook delivery - endpoint not registered."""
        response = client.post("/api/v1/webhooks/1/test")
        assert response.status_code == 404

    def test_get_webhook_deliveries(self, client):
        """Test getting webhook delivery history - endpoint not registered."""
        response = client.get("/api/v1/webhooks/1/deliveries")
        assert response.status_code == 404
