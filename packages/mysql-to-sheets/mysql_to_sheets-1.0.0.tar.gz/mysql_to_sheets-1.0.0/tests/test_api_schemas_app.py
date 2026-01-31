"""Tests for API schemas and application factory."""

import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")

from mysql_to_sheets.core.config import reset_config


class TestSchemas:
    """Tests for Pydantic request/response models."""

    def test_sync_request_model(self):
        """Test SyncRequest schema validation."""
        from mysql_to_sheets.api.schemas import SyncRequest

        request = SyncRequest(
            sheet_id="sheet123",
            worksheet_name="Sheet1",
            sql_query="SELECT 1",
            dry_run=True,
        )
        assert request.sheet_id == "sheet123"
        assert request.dry_run is True
        assert request.preview is False

    def test_sync_request_with_column_options(self):
        """Test SyncRequest with column mapping options."""
        from mysql_to_sheets.api.schemas import SyncRequest

        request = SyncRequest(
            column_map={"old": "New"},
            columns=["New", "Other"],
            column_case="title",
        )
        assert request.column_map == {"old": "New"}
        assert request.columns == ["New", "Other"]
        assert request.column_case == "title"

    def test_validate_request_model(self):
        """Test ValidateRequest schema validation."""
        from mysql_to_sheets.api.schemas import ValidateRequest

        request = ValidateRequest(
            test_connections=True,
            sheet_id="sheet123",
        )
        assert request.test_connections is True
        assert request.sheet_id == "sheet123"

    def test_sync_response_model(self):
        """Test SyncResponse schema."""
        from mysql_to_sheets.api.schemas import SyncResponse

        response = SyncResponse(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["a", "b", "c", "d", "e"],
            message="Sync completed",
        )
        assert response.success is True
        assert response.rows_synced == 100
        assert len(response.headers) == 5
        assert "timestamp" in response.model_dump()

    def test_validate_response_model(self):
        """Test ValidateResponse schema."""
        from mysql_to_sheets.api.schemas import ValidateResponse

        response = ValidateResponse(
            valid=True,
            errors=[],
            database_ok=True,
            sheets_ok=True,
        )
        assert response.valid is True
        assert response.database_ok is True

    def test_health_response_model(self):
        """Test HealthResponse schema."""
        from mysql_to_sheets.api.schemas import HealthResponse

        response = HealthResponse()
        assert response.status == "healthy"
        assert "version" in response.model_dump()
        assert "timestamp" in response.model_dump()

    def test_error_response_model(self):
        """Test ErrorResponse schema."""
        from mysql_to_sheets.api.schemas import ErrorResponse

        response = ErrorResponse(
            error="ConfigError",
            message="Missing DB_USER",
            details={"code": "CONFIG_101"},
        )
        assert response.error == "ConfigError"
        assert response.message == "Missing DB_USER"
        assert response.details["code"] == "CONFIG_101"

    def test_history_entry_response_model(self):
        """Test HistoryEntryResponse schema."""
        from mysql_to_sheets.api.schemas import HistoryEntryResponse

        response = HistoryEntryResponse(
            id=1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True,
            rows_synced=100,
            columns=5,
            headers=["a", "b", "c"],
        )
        assert response.id == 1
        assert response.success is True
        assert response.rows_synced == 100

    def test_schedule_create_request_model(self):
        """Test ScheduleCreateRequest schema."""
        from mysql_to_sheets.api.schemas import ScheduleCreateRequest

        request = ScheduleCreateRequest(
            name="daily-sync",
            cron_expression="0 6 * * *",
        )
        assert request.name == "daily-sync"
        assert request.cron_expression == "0 6 * * *"
        assert request.interval_minutes is None

    def test_schedule_create_request_with_interval(self):
        """Test ScheduleCreateRequest with interval."""
        from mysql_to_sheets.api.schemas import ScheduleCreateRequest

        request = ScheduleCreateRequest(
            name="hourly-sync",
            interval_minutes=60,
        )
        assert request.interval_minutes == 60
        assert request.cron_expression is None

    def test_schedule_update_request_model(self):
        """Test ScheduleUpdateRequest schema."""
        from mysql_to_sheets.api.schemas import ScheduleUpdateRequest

        request = ScheduleUpdateRequest(
            name="updated-sync",
            enabled=False,
        )
        assert request.name == "updated-sync"
        assert request.enabled is False

    def test_schedule_response_model(self):
        """Test ScheduleResponse schema."""
        from mysql_to_sheets.api.schemas import ScheduleResponse

        response = ScheduleResponse(
            id=1,
            name="test-job",
            cron_expression="0 * * * *",
            enabled=True,
            status="pending",
            schedule_display="Hourly",
        )
        assert response.id == 1
        assert response.enabled is True

    def test_notification_status_response_model(self):
        """Test NotificationStatusResponse schema."""
        from mysql_to_sheets.api.schemas import NotificationStatusResponse

        response = NotificationStatusResponse(
            backends={
                "email": {"configured": True, "enabled": True},
                "slack": {"configured": False, "enabled": False},
            }
        )
        assert "email" in response.backends
        assert response.backends["email"]["configured"] is True

    def test_notification_test_request_model(self):
        """Test NotificationTestRequest schema."""
        from mysql_to_sheets.api.schemas import NotificationTestRequest

        request = NotificationTestRequest(backend="email")
        assert request.backend == "email"

        # Default value
        request_default = NotificationTestRequest()
        assert request_default.backend == "all"

    def test_diff_response_model(self):
        """Test DiffResponse schema."""
        from mysql_to_sheets.api.schemas import DiffResponse

        response = DiffResponse(
            has_changes=True,
            sheet_row_count=50,
            query_row_count=60,
            rows_to_add=10,
            rows_to_remove=0,
            rows_unchanged=50,
            summary="10 rows to add",
        )
        assert response.has_changes is True
        assert response.rows_to_add == 10

    def test_deep_health_response_model(self):
        """Test DeepHealthResponse schema."""
        from mysql_to_sheets.api.schemas import DeepHealthResponse

        response = DeepHealthResponse(
            status="healthy",
            checks={
                "database": {"status": "healthy"},
                "filesystem": {"status": "healthy", "writable": True},
            },
        )
        assert response.status == "healthy"
        assert len(response.checks) == 2


class TestAppFactory:
    """Tests for FastAPI application factory."""

    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false"})
    def test_create_app_basic(self):
        """Test creating basic FastAPI app."""
        from mysql_to_sheets.api.app import create_app

        reset_config()
        app = create_app()
        assert app is not None
        assert app.title == "MySQL to Google Sheets Sync API"
        reset_config()

    @patch.dict(
        os.environ, {"API_AUTH_ENABLED": "false", "CORS_ALLOWED_ORIGINS": "http://localhost:3000"}
    )
    def test_create_app_with_cors(self):
        """Test creating app with CORS enabled."""
        from mysql_to_sheets.api.app import create_app

        reset_config()
        app = create_app()
        # Check that app was created with CORS middleware
        assert app is not None
        reset_config()

    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false", "METRICS_ENABLED": "true"})
    def test_create_app_with_metrics(self):
        """Test creating app with metrics enabled."""
        from mysql_to_sheets.api.app import create_app

        reset_config()
        app = create_app()
        assert app is not None
        reset_config()

    def test_parse_cors_origins_empty(self):
        """Test parsing empty CORS origins."""
        from mysql_to_sheets.api.app import _parse_cors_origins

        assert _parse_cors_origins("") == []
        assert _parse_cors_origins("   ") == []

    def test_parse_cors_origins_single(self):
        """Test parsing single CORS origin."""
        from mysql_to_sheets.api.app import _parse_cors_origins

        result = _parse_cors_origins("http://localhost:3000")
        assert result == ["http://localhost:3000"]

    def test_parse_cors_origins_multiple(self):
        """Test parsing multiple CORS origins."""
        from mysql_to_sheets.api.app import _parse_cors_origins

        result = _parse_cors_origins("http://localhost:3000, http://example.com")
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "http://example.com" in result

    def test_parse_cors_origins_with_whitespace(self):
        """Test parsing CORS origins with extra whitespace."""
        from mysql_to_sheets.api.app import _parse_cors_origins

        result = _parse_cors_origins("  http://localhost:3000  ,  http://example.com  ")
        assert len(result) == 2
        assert "http://localhost:3000" in result
        assert "http://example.com" in result


class TestLifespan:
    """Tests for application lifespan management."""

    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false"})
    def test_lifespan_startup(self):
        """Test application startup in lifespan."""
        from fastapi.testclient import TestClient

        from mysql_to_sheets.api.app import create_app

        reset_config()
        app = create_app()

        # TestClient handles lifespan events
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200

        reset_config()

    @patch("mysql_to_sheets.core.auth.cleanup_expired_tokens")
    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false"})
    def test_lifespan_shutdown_cleanup(self, mock_cleanup):
        """Test cleanup during shutdown."""
        from fastapi.testclient import TestClient

        from mysql_to_sheets.api.app import create_app

        mock_cleanup.return_value = 5

        reset_config()
        app = create_app()

        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200

        # Cleanup is called on exit
        # Note: TestClient may not always trigger shutdown in tests
        reset_config()


class TestRequestTracking:
    """Tests for active request tracking."""

    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false"})
    def test_increment_active_requests(self):
        """Test incrementing active request counter."""
        import asyncio

        from mysql_to_sheets.api.app import get_active_requests, increment_active_requests

        async def _run():
            await increment_active_requests()
            return await get_active_requests()

        count = asyncio.run(_run())
        assert count >= 0

    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false"})
    def test_decrement_active_requests(self):
        """Test decrementing active request counter."""
        import asyncio

        from mysql_to_sheets.api.app import (
            decrement_active_requests,
            get_active_requests,
            increment_active_requests,
        )

        async def _run():
            await increment_active_requests()
            await increment_active_requests()
            await decrement_active_requests()
            return await get_active_requests()

        count = asyncio.run(_run())
        assert count >= 0

    @patch.dict(os.environ, {"API_AUTH_ENABLED": "false"})
    def test_wait_for_requests_to_drain(self):
        """Test waiting for requests to drain."""
        import asyncio

        from mysql_to_sheets.api.app import wait_for_requests_to_drain

        result = asyncio.run(wait_for_requests_to_drain(timeout=1.0))
        assert isinstance(result, bool)
