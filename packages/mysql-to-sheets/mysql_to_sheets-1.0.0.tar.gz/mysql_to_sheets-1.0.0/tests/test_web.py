"""Tests for Flask web dashboard."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("flask")

# Set required environment variables before importing web app
os.environ.setdefault("SESSION_SECRET_KEY", "test-secret-key-for-testing-only")

from flask import Flask
from flask.testing import FlaskClient

from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, SheetsError
from mysql_to_sheets.core.sync import SyncResult
from mysql_to_sheets.web.app import create_app
from mysql_to_sheets.web.history import SyncHistory, SyncHistoryEntry, sync_history


@pytest.fixture
def app() -> Flask:
    """Create test application."""
    test_app = create_app()
    test_app.config["TESTING"] = True
    return test_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_history():
    """Reset sync history before each test."""
    # Clear the global history
    sync_history._entries.clear()
    yield


class TestSyncHistoryEntry:
    """Tests for SyncHistoryEntry dataclass."""

    def test_entry_creation(self) -> None:
        """Test SyncHistoryEntry creation."""
        entry = SyncHistoryEntry(
            timestamp="2024-01-15T10:30:00",
            success=True,
            rows_synced=100,
            message="Success",
            sheet_id="abc123",
            worksheet="Sheet1",
        )

        assert entry.timestamp == "2024-01-15T10:30:00"
        assert entry.success is True
        assert entry.rows_synced == 100
        assert entry.message == "Success"
        assert entry.sheet_id == "abc123"
        assert entry.worksheet == "Sheet1"
        assert entry.duration_ms == 0.0

    def test_entry_with_duration(self) -> None:
        """Test SyncHistoryEntry with duration."""
        entry = SyncHistoryEntry(
            timestamp="2024-01-15T10:30:00",
            success=True,
            rows_synced=100,
            message="Success",
            sheet_id="abc123",
            worksheet="Sheet1",
            duration_ms=1234.56,
        )

        assert entry.duration_ms == 1234.56


class TestSyncHistory:
    """Tests for SyncHistory class."""

    def test_empty_history(self) -> None:
        """Test empty history returns empty list."""
        history = SyncHistory()
        assert history.get_all() == []

    def test_add_entry(self) -> None:
        """Test adding entry to history."""
        history = SyncHistory()
        entry = SyncHistoryEntry(
            timestamp="2024-01-15T10:30:00",
            success=True,
            rows_synced=100,
            message="Success",
            sheet_id="abc123",
            worksheet="Sheet1",
        )

        history.add(entry)
        entries = history.get_all()

        assert len(entries) == 1
        assert entries[0]["rows_synced"] == 100

    def test_max_entries_limit(self) -> None:
        """Test history respects max_entries limit."""
        history = SyncHistory(max_entries=3)

        for i in range(5):
            entry = SyncHistoryEntry(
                timestamp=f"2024-01-15T10:3{i}:00",
                success=True,
                rows_synced=i * 100,
                message=f"Entry {i}",
                sheet_id="abc123",
                worksheet="Sheet1",
            )
            history.add(entry)

        entries = history.get_all()
        assert len(entries) == 3

    def test_newest_first_order(self) -> None:
        """Test entries are ordered newest first."""
        history = SyncHistory()

        for i in range(3):
            entry = SyncHistoryEntry(
                timestamp=f"2024-01-15T10:3{i}:00",
                success=True,
                rows_synced=i * 100,
                message=f"Entry {i}",
                sheet_id="abc123",
                worksheet="Sheet1",
            )
            history.add(entry)

        entries = history.get_all()

        # Newest (Entry 2) should be first
        assert entries[0]["message"] == "Entry 2"
        assert entries[1]["message"] == "Entry 1"
        assert entries[2]["message"] == "Entry 0"

    def test_get_all_returns_dicts(self) -> None:
        """Test get_all returns list of dictionaries."""
        history = SyncHistory()
        entry = SyncHistoryEntry(
            timestamp="2024-01-15T10:30:00",
            success=True,
            rows_synced=100,
            message="Success",
            sheet_id="abc123",
            worksheet="Sheet1",
            duration_ms=500.0,
        )
        history.add(entry)

        entries = history.get_all()

        assert isinstance(entries[0], dict)
        assert entries[0]["timestamp"] == "2024-01-15T10:30:00"
        assert entries[0]["success"] is True
        assert entries[0]["rows_synced"] == 100
        assert entries[0]["message"] == "Success"
        assert entries[0]["sheet_id"] == "abc123"
        assert entries[0]["worksheet"] == "Sheet1"
        assert entries[0]["duration_ms"] == 500.0


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        """Test health endpoint returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client: FlaskClient) -> None:
        """Test health endpoint returns status."""
        response = client.get("/api/health")
        data = json.loads(response.data)

        assert data["status"] == "healthy"

    def test_health_returns_version(self, client: FlaskClient) -> None:
        """Test health endpoint returns version."""
        response = client.get("/api/health")
        data = json.loads(response.data)

        assert "version" in data


class TestHistoryEndpoint:
    """Tests for /api/history endpoint."""

    def test_empty_history(self, client: FlaskClient) -> None:
        """Test history endpoint with empty history."""
        response = client.get("/api/history")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["history"] == []

    def test_history_with_entries(self, client: FlaskClient) -> None:
        """Test history endpoint with entries."""
        # Add entry to global history
        entry = SyncHistoryEntry(
            timestamp="2024-01-15T10:30:00",
            success=True,
            rows_synced=100,
            message="Success",
            sheet_id="abc123",
            worksheet="Sheet1",
        )
        sync_history.add(entry)

        response = client.get("/api/history")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert len(data["history"]) == 1
        assert data["history"][0]["rows_synced"] == 100


class TestIndexRoute:
    """Tests for index (/) route."""

    def test_index_returns_200(self, client: FlaskClient) -> None:
        """Test index route returns 200 when authenticated."""
        # Set up authenticated session
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "owner"

        with patch("mysql_to_sheets.web.blueprints.dashboard.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                google_sheet_id="test-sheet",
                google_worksheet_name="Sheet1",
                sql_query="SELECT 1",
                db_host="localhost",
                db_name="testdb",
            )
            response = client.get("/")

        assert response.status_code == 200

    def test_index_renders_template(self, client: FlaskClient) -> None:
        """Test index route renders HTML template."""
        # Set up authenticated session
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "owner"

        with patch("mysql_to_sheets.web.blueprints.dashboard.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                google_sheet_id="test-sheet",
                google_worksheet_name="Sheet1",
                sql_query="SELECT 1",
                db_host="localhost",
                db_name="testdb",
            )
            response = client.get("/")

        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestSetupRoute:
    """Tests for /setup route."""

    def test_setup_returns_200(self, client: FlaskClient) -> None:
        """Test setup route returns 200."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path") as mock_env:
            with patch(
                "mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path"
            ) as mock_sa:
                with patch(
                    "mysql_to_sheets.web.blueprints.dashboard.get_config_dir"
                ) as mock_config_dir:
                    mock_env.return_value = MagicMock(exists=MagicMock(return_value=False))
                    mock_sa.return_value = MagicMock(exists=MagicMock(return_value=False))
                    mock_config_dir.return_value = "/app/config"

                    response = client.get("/setup")

        assert response.status_code == 200


class TestSetupStatusEndpoint:
    """Tests for /api/setup/status endpoint."""

    def test_setup_status_not_configured(self, client: FlaskClient) -> None:
        """Test setup status when not configured."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path") as mock_env:
            with patch(
                "mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path"
            ) as mock_sa:
                mock_env.return_value = MagicMock(exists=MagicMock(return_value=False))
                mock_sa.return_value = MagicMock(exists=MagicMock(return_value=False))

                response = client.get("/api/setup/status")
                data = json.loads(response.data)

        assert response.status_code == 200
        assert data["env_exists"] is False
        assert data["service_account_exists"] is False
        assert data["setup_complete"] is False

    def test_setup_status_fully_configured(self, client: FlaskClient) -> None:
        """Test setup status when fully configured."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path") as mock_env:
            with patch(
                "mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path"
            ) as mock_sa:
                mock_env_path = MagicMock()
                mock_env_path.exists.return_value = True
                mock_env_path.read_text.return_value = "DB_USER=test\nGOOGLE_SHEET_ID=abc"
                mock_env.return_value = mock_env_path

                mock_sa_path = MagicMock()
                mock_sa_path.exists.return_value = True
                mock_sa.return_value = mock_sa_path

                response = client.get("/api/setup/status")
                data = json.loads(response.data)

        assert response.status_code == 200
        assert data["env_exists"] is True
        assert data["env_configured"] is True
        assert data["service_account_exists"] is True
        assert data["setup_complete"] is True


class TestValidateEndpoint:
    """Tests for /api/validate endpoint."""

    def test_validate_valid_config(self, client: FlaskClient) -> None:
        """Test validate with valid configuration."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_config:
            mock_config_obj = MagicMock()
            mock_config_obj.validate.return_value = []
            mock_config_obj.with_overrides.return_value = mock_config_obj
            mock_config.return_value = mock_config_obj

            response = client.post(
                "/api/validate",
                json={"sheet_id": "test123"},
                content_type="application/json",
            )
            data = json.loads(response.data)

        assert response.status_code == 200
        assert data["valid"] is True
        assert data["errors"] == []

    def test_validate_invalid_config(self, client: FlaskClient) -> None:
        """Test validate with invalid configuration."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_config:
            mock_config_obj = MagicMock()
            mock_config_obj.validate.return_value = ["DB_USER is required"]
            mock_config_obj.with_overrides.return_value = mock_config_obj
            mock_config.return_value = mock_config_obj

            response = client.post(
                "/api/validate",
                json={},
                content_type="application/json",
            )
            data = json.loads(response.data)

        assert response.status_code == 400
        assert data["valid"] is False
        assert "DB_USER is required" in data["errors"]


class TestSyncEndpoint:
    """Tests for /api/sync endpoint."""

    def test_sync_success(self, client: FlaskClient) -> None:
        """Test successful sync."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.return_value = SyncResult(
                    success=True,
                    rows_synced=100,
                    columns=5,
                    headers=["id", "name", "value", "date", "status"],
                    message="Synced 100 rows",
                )

                response = client.post(
                    "/api/sync",
                    json={"sheet_id": "test123"},
                    content_type="application/json",
                )
                data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert data["rows_synced"] == 100
        assert data["columns"] == 5

    def test_sync_dry_run(self, client: FlaskClient) -> None:
        """Test sync with dry_run flag."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.return_value = SyncResult(
                    success=True,
                    rows_synced=50,
                    columns=3,
                    headers=["a", "b", "c"],
                    message="Dry run: validated 50 rows",
                )

                response = client.post(
                    "/api/sync",
                    json={"dry_run": True},
                    content_type="application/json",
                )
                data = json.loads(response.data)

        # Verify dry_run was passed to run_sync
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args[1]
        assert call_kwargs["dry_run"] is True

    def test_sync_adds_to_history(self, client: FlaskClient) -> None:
        """Test successful sync adds entry to history."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.return_value = SyncResult(
                    success=True,
                    rows_synced=100,
                    columns=5,
                    headers=[],
                    message="Success",
                )

                client.post(
                    "/api/sync",
                    json={},
                    content_type="application/json",
                )

        history = sync_history.get_all()
        assert len(history) == 1
        assert history[0]["success"] is True
        assert history[0]["rows_synced"] == 100

    def test_sync_config_error(self, client: FlaskClient) -> None:
        """Test sync with ConfigError."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.side_effect = ConfigError(
                    message="Invalid configuration",
                    missing_fields=["DB_USER", "DB_PASSWORD"],
                )

                response = client.post(
                    "/api/sync",
                    json={},
                    content_type="application/json",
                )
                data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Invalid configuration" in data["message"]
        assert "DB_USER" in data["errors"]

    def test_sync_database_error(self, client: FlaskClient) -> None:
        """Test sync with DatabaseError."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.side_effect = DatabaseError(
                    message="Connection refused",
                    host="localhost",
                    database="testdb",
                )

                response = client.post(
                    "/api/sync",
                    json={},
                    content_type="application/json",
                )
                data = json.loads(response.data)

        assert response.status_code == 500
        assert data["success"] is False
        assert "Connection refused" in data["message"]
        assert data["error_type"] == "DatabaseError"

    def test_sync_database_error_adds_to_history(self, client: FlaskClient) -> None:
        """Test DatabaseError adds failed entry to history."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.side_effect = DatabaseError(
                    message="Connection refused",
                    host="localhost",
                )

                client.post(
                    "/api/sync",
                    json={},
                    content_type="application/json",
                )

        history = sync_history.get_all()
        assert len(history) == 1
        assert history[0]["success"] is False
        assert "Database error" in history[0]["message"]

    def test_sync_sheets_error(self, client: FlaskClient) -> None:
        """Test sync with SheetsError."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.side_effect = SheetsError(
                    message="Spreadsheet not found",
                    sheet_id="test-sheet",
                )

                response = client.post(
                    "/api/sync",
                    json={},
                    content_type="application/json",
                )
                data = json.loads(response.data)

        assert response.status_code == 500
        assert data["success"] is False
        assert "Spreadsheet not found" in data["message"]
        assert data["error_type"] == "SheetsError"

    def test_sync_sheets_error_adds_to_history(self, client: FlaskClient) -> None:
        """Test SheetsError adds failed entry to history."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "test-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.side_effect = SheetsError(
                    message="Rate limit exceeded",
                    sheet_id="test-sheet",
                )

                client.post(
                    "/api/sync",
                    json={},
                    content_type="application/json",
                )

        history = sync_history.get_all()
        assert len(history) == 1
        assert history[0]["success"] is False
        assert "Sheets error" in history[0]["message"]

    def test_sync_with_overrides(self, client: FlaskClient) -> None:
        """Test sync applies overrides from request."""
        with patch("mysql_to_sheets.web.blueprints.api.sync.get_config") as mock_get_config:
            with patch("mysql_to_sheets.web.blueprints.api.sync.run_sync") as mock_sync:
                mock_config = MagicMock()
                mock_config.google_sheet_id = "original-sheet"
                mock_config.google_worksheet_name = "Sheet1"
                mock_config.with_overrides.return_value = mock_config
                mock_get_config.return_value = mock_config

                mock_sync.return_value = SyncResult(
                    success=True,
                    rows_synced=10,
                    columns=2,
                    headers=[],
                    message="Success",
                )

                client.post(
                    "/api/sync",
                    json={
                        "sheet_id": "override-sheet",
                        "worksheet": "CustomSheet",
                        "sql_query": "SELECT * FROM custom",
                    },
                    content_type="application/json",
                )

        # Verify overrides were applied
        mock_config.with_overrides.assert_called_once()
        call_kwargs = mock_config.with_overrides.call_args[1]
        assert call_kwargs["google_sheet_id"] == "override-sheet"
        assert call_kwargs["google_worksheet_name"] == "CustomSheet"
        assert call_kwargs["sql_query"] == "SELECT * FROM custom"


class TestCreateApp:
    """Tests for create_app factory function."""

    def test_creates_flask_app(self) -> None:
        """Test create_app returns Flask instance."""
        app = create_app()
        assert isinstance(app, Flask)

    def test_app_has_required_routes(self) -> None:
        """Test app has all required routes."""
        app = create_app()

        # Get all registered routes
        rules = [rule.rule for rule in app.url_map.iter_rules()]

        assert "/" in rules
        assert "/setup" in rules
        assert "/api/sync" in rules
        assert "/api/validate" in rules
        assert "/api/history" in rules
        assert "/api/health" in rules
        assert "/api/setup/status" in rules

    def test_app_has_secret_key(self) -> None:
        """Test app has secret key configured."""
        app = create_app()
        assert app.config["SECRET_KEY"] is not None


class TestTierPage:
    """Tests for /tier route and API."""

    def test_tier_page_requires_login(self, client: FlaskClient) -> None:
        """Test tier page requires authentication."""
        response = client.get("/tier")
        # Should redirect to login
        assert response.status_code in (302, 401)

    def test_tier_api_status_requires_auth(self, client: FlaskClient) -> None:
        """Test tier status API requires authentication."""
        response = client.get("/api/tier/status")
        assert response.status_code == 401

    def test_tier_api_usage_requires_auth(self, client: FlaskClient) -> None:
        """Test tier usage API requires authentication."""
        response = client.get("/api/tier/usage")
        assert response.status_code == 401

    def test_tier_api_features_requires_auth(self, client: FlaskClient) -> None:
        """Test tier features API requires authentication."""
        response = client.get("/api/tier/features")
        assert response.status_code == 401


class TestFreshnessPage:
    """Tests for /freshness route and API."""

    def test_freshness_page_requires_login(self, client: FlaskClient) -> None:
        """Test freshness page requires authentication."""
        response = client.get("/freshness")
        # Should redirect to login
        assert response.status_code in (302, 401)

    def test_freshness_api_report_requires_auth(self, client: FlaskClient) -> None:
        """Test freshness report API requires authentication."""
        response = client.get("/api/freshness-page/report")
        assert response.status_code == 401

    def test_freshness_api_check_requires_auth(self, client: FlaskClient) -> None:
        """Test freshness check API requires authentication."""
        response = client.post("/api/freshness-page/check")
        assert response.status_code == 401


class TestApiKeysPage:
    """Tests for /api-keys route and API."""

    def test_api_keys_page_requires_login(self, client: FlaskClient) -> None:
        """Test API keys page requires authentication."""
        response = client.get("/api-keys")
        # Should redirect to login
        assert response.status_code in (302, 401)

    def test_api_keys_list_requires_auth(self, client: FlaskClient) -> None:
        """Test API keys list API requires authentication."""
        response = client.get("/api/api-keys")
        assert response.status_code == 401

    def test_api_keys_create_requires_auth(self, client: FlaskClient) -> None:
        """Test API keys create API requires authentication."""
        response = client.post(
            "/api/api-keys",
            json={"name": "test-key"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_api_keys_delete_requires_auth(self, client: FlaskClient) -> None:
        """Test API keys delete API requires authentication."""
        response = client.delete("/api/api-keys/1")
        assert response.status_code == 401


class TestDiagnosticsPage:
    """Tests for /diagnostics route and API."""

    def test_diagnostics_page_returns_200(self, client: FlaskClient) -> None:
        """Test diagnostics page loads without authentication."""
        with patch("mysql_to_sheets.web.blueprints.diagnostics_bp.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                db_name="testdb",
                google_sheet_id="test-sheet",
                sql_query="SELECT 1",
                db_type="mysql",
                service_account_file="./service_account.json",
            )
            response = client.get("/diagnostics")

        assert response.status_code == 200

    def test_diagnostics_api_returns_json(self, client: FlaskClient) -> None:
        """Test diagnostics API returns JSON."""
        with patch("mysql_to_sheets.web.blueprints.diagnostics_bp.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                db_name="testdb",
                google_sheet_id="test-sheet",
                sql_query="SELECT 1",
                db_type="mysql",
                service_account_file="./service_account.json",
            )
            response = client.get("/api/diagnostics")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "version" in data
        assert "system" in data
        assert "environment" in data
        assert "checks" in data

    def test_diagnostics_config_check(self, client: FlaskClient) -> None:
        """Test diagnostics config check endpoint."""
        with patch("mysql_to_sheets.web.blueprints.diagnostics_bp.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                db_name="testdb",
                google_sheet_id="test-sheet",
                sql_query="SELECT 1",
                db_type="mysql",
                service_account_file="./service_account.json",
            )
            with patch("pathlib.Path.exists", return_value=True):
                response = client.get("/api/diagnostics/config")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "status" in data

    def test_diagnostics_export(self, client: FlaskClient) -> None:
        """Test diagnostics export endpoint."""
        with patch("mysql_to_sheets.web.blueprints.diagnostics_bp.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                db_name="testdb",
                google_sheet_id="test-sheet",
                sql_query="SELECT 1",
                db_type="mysql",
                service_account_file="./service_account.json",
            )
            response = client.get("/api/diagnostics/export")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "generated_at" in data
        assert "version" in data


class TestNewRoutesRegistered:
    """Tests to verify new routes are registered."""

    def test_tier_route_exists(self) -> None:
        """Test /tier route is registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/tier" in rules

    def test_freshness_route_exists(self) -> None:
        """Test /freshness route is registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/freshness" in rules

    def test_api_keys_route_exists(self) -> None:
        """Test /api-keys route is registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/api-keys" in rules

    def test_diagnostics_route_exists(self) -> None:
        """Test /diagnostics route is registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/diagnostics" in rules

    def test_tier_api_routes_exist(self) -> None:
        """Test /api/tier/* routes are registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/api/tier/status" in rules
        assert "/api/tier/usage" in rules
        assert "/api/tier/features" in rules

    def test_api_keys_api_routes_exist(self) -> None:
        """Test /api/api-keys routes are registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/api/api-keys" in rules

    def test_diagnostics_api_routes_exist(self) -> None:
        """Test /api/diagnostics routes are registered."""
        app = create_app()
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/api/diagnostics" in rules
        assert "/api/diagnostics/config" in rules
        assert "/api/diagnostics/export" in rules
