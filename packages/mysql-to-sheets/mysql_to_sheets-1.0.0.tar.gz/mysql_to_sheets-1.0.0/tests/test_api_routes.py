"""Tests for API routes including schedules.

Note: Auth route tests are skipped because auth_routes.py is not currently
included in the main app router (see app.py). These tests can be enabled
once auth routes are integrated.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from mysql_to_sheets.api.app import create_app
from mysql_to_sheets.core.config import reset_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, SheetsError


@pytest.fixture
def client():
    """Create test client for API with auth disabled."""
    with patch.dict(os.environ, {"API_AUTH_ENABLED": "false"}):
        reset_config()
        app = create_app()
        yield TestClient(app)
        reset_config()


class TestScheduleRoutes:
    """Tests for /api/v1/schedules/* endpoints."""

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_create_schedule_with_cron(self, mock_get_service, client):
        """Test creating a schedule with cron expression."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "daily-sync"
        mock_job.cron_expression = "0 6 * * *"
        mock_job.interval_minutes = None
        mock_job.sheet_id = None
        mock_job.worksheet_name = None
        mock_job.sql_query = None
        mock_job.notify_on_success = None
        mock_job.notify_on_failure = None
        mock_job.enabled = True
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = None
        mock_job.last_run_at = None
        mock_job.last_run_success = None
        mock_job.last_run_message = None
        mock_job.last_run_rows = None
        mock_job.last_run_duration_ms = None
        mock_job.next_run_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_job.status = MagicMock(value="pending")
        mock_job.schedule_display = "0 6 * * *"
        mock_service.add_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/schedules",
            json={
                "name": "daily-sync",
                "cron_expression": "0 6 * * *",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "daily-sync"
        assert data["cron_expression"] == "0 6 * * *"
        assert data["enabled"] is True

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_create_schedule_with_interval(self, mock_get_service, client):
        """Test creating a schedule with interval."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 2
        mock_job.name = "hourly-sync"
        mock_job.cron_expression = None
        mock_job.interval_minutes = 60
        mock_job.sheet_id = None
        mock_job.worksheet_name = None
        mock_job.sql_query = None
        mock_job.notify_on_success = None
        mock_job.notify_on_failure = None
        mock_job.enabled = True
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = None
        mock_job.last_run_at = None
        mock_job.last_run_success = None
        mock_job.last_run_message = None
        mock_job.last_run_rows = None
        mock_job.last_run_duration_ms = None
        mock_job.next_run_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_job.status = MagicMock(value="pending")
        mock_job.schedule_display = "Every 60 minutes"
        mock_service.add_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/schedules",
            json={
                "name": "hourly-sync",
                "interval_minutes": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "hourly-sync"
        assert data["interval_minutes"] == 60

    def test_create_schedule_missing_schedule(self, client):
        """Test creating a schedule fails without cron or interval."""
        response = client.post(
            "/api/v1/schedules",
            json={"name": "invalid-sync"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "cron_expression or interval_minutes" in data["detail"]["message"]

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_list_schedules(self, mock_get_service, client):
        """Test listing all schedules."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "test-job"
        mock_job.cron_expression = "0 * * * *"
        mock_job.interval_minutes = None
        mock_job.sheet_id = None
        mock_job.worksheet_name = None
        mock_job.sql_query = None
        mock_job.notify_on_success = None
        mock_job.notify_on_failure = None
        mock_job.enabled = True
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = None
        mock_job.last_run_at = None
        mock_job.last_run_success = None
        mock_job.last_run_message = None
        mock_job.last_run_rows = None
        mock_job.last_run_duration_ms = None
        mock_job.next_run_at = None
        mock_job.status = MagicMock(value="pending")
        mock_job.schedule_display = "0 * * * *"
        mock_service.get_all_jobs.return_value = [mock_job]
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/schedules")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["schedules"]) == 1
        assert data["schedules"][0]["name"] == "test-job"

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_list_schedules_empty(self, mock_get_service, client):
        """Test listing schedules when none exist."""
        mock_service = MagicMock()
        mock_service.get_all_jobs.return_value = []
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/schedules")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["schedules"] == []

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_get_schedule_success(self, mock_get_service, client):
        """Test getting a specific schedule."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 5
        mock_job.name = "specific-job"
        mock_job.cron_expression = "0 12 * * *"
        mock_job.interval_minutes = None
        mock_job.sheet_id = "sheet123"
        mock_job.worksheet_name = "Data"
        mock_job.sql_query = "SELECT * FROM users"
        mock_job.notify_on_success = None
        mock_job.notify_on_failure = None
        mock_job.enabled = True
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = None
        mock_job.last_run_at = None
        mock_job.last_run_success = None
        mock_job.last_run_message = None
        mock_job.last_run_rows = None
        mock_job.last_run_duration_ms = None
        mock_job.next_run_at = None
        mock_job.status = MagicMock(value="pending")
        mock_job.schedule_display = "0 12 * * *"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/schedules/5")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 5
        assert data["name"] == "specific-job"
        assert data["sheet_id"] == "sheet123"

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_get_schedule_not_found(self, mock_get_service, client):
        """Test getting a non-existent schedule."""
        mock_service = MagicMock()
        mock_service.get_job.return_value = None
        mock_get_service.return_value = mock_service

        response = client.get("/api/v1/schedules/999")

        assert response.status_code == 404
        data = response.json()
        assert "NotFound" in data["detail"]["error"]

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_update_schedule_success(self, mock_get_service, client):
        """Test updating a schedule."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "updated-job"
        mock_job.cron_expression = "0 18 * * *"
        mock_job.interval_minutes = None
        mock_job.sheet_id = None
        mock_job.worksheet_name = None
        mock_job.sql_query = None
        mock_job.notify_on_success = None
        mock_job.notify_on_failure = None
        mock_job.enabled = True
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = datetime.now(timezone.utc)
        mock_job.last_run_at = None
        mock_job.last_run_success = None
        mock_job.last_run_message = None
        mock_job.last_run_rows = None
        mock_job.last_run_duration_ms = None
        mock_job.next_run_at = None
        mock_job.status = MagicMock(value="pending")
        mock_job.schedule_display = "0 18 * * *"
        mock_service.get_job.return_value = mock_job
        mock_service.update_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = client.put(
            "/api/v1/schedules/1",
            json={
                "name": "updated-job",
                "cron_expression": "0 18 * * *",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-job"

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_update_schedule_not_found(self, mock_get_service, client):
        """Test updating a non-existent schedule."""
        mock_service = MagicMock()
        mock_service.get_job.return_value = None
        mock_get_service.return_value = mock_service

        response = client.put(
            "/api/v1/schedules/999",
            json={"name": "new-name"},
        )

        assert response.status_code == 404

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_delete_schedule_success(self, mock_get_service, client):
        """Test deleting a schedule."""
        mock_service = MagicMock()
        mock_service.delete_job.return_value = True
        mock_get_service.return_value = mock_service

        response = client.delete("/api/v1/schedules/1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_delete_schedule_not_found(self, mock_get_service, client):
        """Test deleting a non-existent schedule."""
        mock_service = MagicMock()
        mock_service.delete_job.return_value = False
        mock_get_service.return_value = mock_service

        response = client.delete("/api/v1/schedules/999")

        assert response.status_code == 404

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_trigger_schedule_success(self, mock_get_service, client):
        """Test triggering a schedule."""
        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.name = "triggered-job"
        mock_job.cron_expression = "0 * * * *"
        mock_job.interval_minutes = None
        mock_job.sheet_id = None
        mock_job.worksheet_name = None
        mock_job.sql_query = None
        mock_job.notify_on_success = None
        mock_job.notify_on_failure = None
        mock_job.enabled = True
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = None
        mock_job.last_run_at = datetime.now(timezone.utc)
        mock_job.last_run_success = True
        mock_job.last_run_message = "Sync completed"
        mock_job.last_run_rows = 100
        mock_job.last_run_duration_ms = 1500.0
        mock_job.next_run_at = None
        mock_job.status = MagicMock(value="completed")
        mock_job.schedule_display = "0 * * * *"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = client.post("/api/v1/schedules/1/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["last_run_success"] is True
        assert data["last_run_rows"] == 100

    @patch("mysql_to_sheets.core.scheduler.get_scheduler_service")
    def test_trigger_schedule_not_found(self, mock_get_service, client):
        """Test triggering a non-existent schedule."""
        mock_service = MagicMock()
        mock_service.get_job.return_value = None
        mock_get_service.return_value = mock_service

        response = client.post("/api/v1/schedules/999/trigger")

        assert response.status_code == 404


class TestErrorHandling:
    """Tests for API error handling."""

    @patch("mysql_to_sheets.api.routes.run_sync")
    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_config_error_returns_400(self, mock_reset, mock_get_config, mock_run_sync, client):
        """Test ConfigError returns 400."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config
        mock_run_sync.side_effect = ConfigError("Missing required config")

        response = client.post("/api/v1/sync", json={})

        assert response.status_code == 400

    @patch("mysql_to_sheets.api.routes.run_sync")
    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_database_error_returns_500(self, mock_reset, mock_get_config, mock_run_sync, client):
        """Test DatabaseError returns 500."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config
        mock_run_sync.side_effect = DatabaseError("Connection failed")

        response = client.post("/api/v1/sync", json={})

        assert response.status_code == 500

    @patch("mysql_to_sheets.api.routes.run_sync")
    @patch("mysql_to_sheets.api.routes.get_config")
    @patch("mysql_to_sheets.api.routes.reset_config")
    def test_sheets_error_returns_500(self, mock_reset, mock_get_config, mock_run_sync, client):
        """Test SheetsError returns 500."""
        mock_config = MagicMock()
        mock_config.with_overrides.return_value = mock_config
        mock_get_config.return_value = mock_config
        mock_run_sync.side_effect = SheetsError("API quota exceeded")

        response = client.post("/api/v1/sync", json={})

        assert response.status_code == 500


class TestDeepHealthCheck:
    """Tests for /api/v1/health/deep endpoint."""

    def test_deep_health_check_success(self, client):
        """Test deep health check returns healthy status."""
        response = client.get("/api/v1/health/deep")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "checks" in data
        assert "filesystem" in data["checks"]
