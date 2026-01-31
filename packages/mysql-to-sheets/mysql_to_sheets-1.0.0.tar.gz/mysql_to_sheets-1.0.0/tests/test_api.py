"""Tests for API module."""

import os

import pytest

pytest.importorskip("fastapi")

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from mysql_to_sheets.api.app import create_app
from mysql_to_sheets.core.config import reset_config
from mysql_to_sheets.core.sync import SyncResult


@pytest.fixture
def client():
    """Create test client for API with auth disabled."""
    with patch.dict(os.environ, {"API_AUTH_ENABLED": "false"}):
        reset_config()
        app = create_app()
        yield TestClient(app)
        reset_config()


class TestHealthEndpoint:
    """Tests for /api/v1/health endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestValidateEndpoint:
    """Tests for /api/v1/validate endpoint."""

    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_validate_valid_config(self, mock_reset, mock_get_config, client):
        """Test validate endpoint with valid config."""
        mock_config = MagicMock()
        mock_config.validate.return_value = []
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config

        response = client.post("/api/v1/validate", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_validate_invalid_config(self, mock_reset, mock_get_config, client):
        """Test validate endpoint with invalid config."""
        mock_config = MagicMock()
        mock_config.validate.return_value = ["DB_USER is required"]
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config

        response = client.post("/api/v1/validate", json={})
        # Returns 200 - validation succeeded, but found config errors
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "DB_USER is required" in data["errors"]

    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_validate_with_overrides(self, mock_reset, mock_get_config, client):
        """Test validate endpoint applies request overrides."""
        mock_config = MagicMock()
        mock_config.validate.return_value = []
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config

        response = client.post(
            "/api/v1/validate",
            json={
                "sheet_id": "test_sheet",
                "worksheet_name": "TestSheet",
            },
        )

        assert response.status_code == 200
        mock_config.with_overrides.assert_called_once()


class TestSyncEndpoint:
    """Tests for /api/v1/sync endpoint."""

    @patch("mysql_to_sheets.api.routes.run_sync")
    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_sync_success(self, mock_reset, mock_get_config, mock_run_sync, client):
        """Test sync endpoint successful execution."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config

        mock_run_sync.return_value = SyncResult(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["a", "b", "c", "d", "e"],
            message="Success",
        )

        response = client.post("/api/v1/sync", json={"dry_run": True})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["rows_synced"] == 100

    @patch("mysql_to_sheets.api.routes.run_sync")
    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_sync_with_overrides(self, mock_reset, mock_get_config, mock_run_sync, client):
        """Test sync endpoint applies request overrides."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config

        mock_run_sync.return_value = SyncResult(success=True, message="Done")

        response = client.post(
            "/api/v1/sync",
            json={
                "sheet_id": "override_sheet",
                "sql_query": "SELECT 1",
            },
        )

        assert response.status_code == 200
        mock_config.with_overrides.assert_called()
