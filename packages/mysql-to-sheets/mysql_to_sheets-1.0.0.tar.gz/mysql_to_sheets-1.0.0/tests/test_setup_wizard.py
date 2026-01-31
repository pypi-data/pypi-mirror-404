"""Tests for setup wizard API endpoints."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("flask")

# Set required environment variables before importing web app
os.environ.setdefault("SESSION_SECRET_KEY", "test-secret-key-for-testing-only")

from flask import Flask
from flask.testing import FlaskClient

from mysql_to_sheets.web.app import create_app
from mysql_to_sheets.web.blueprints.dashboard import (
    _get_db_error_remediation,
    _get_sheets_error_remediation,
)


@pytest.fixture
def app() -> Flask:
    """Create test application."""
    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["WTF_CSRF_ENABLED"] = False
    return test_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


class TestSetupStatusEndpoint:
    """Tests for /api/setup/status endpoint."""

    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    def test_status_complete(self, mock_sa_path, mock_env_path, client, tmp_path):
        """Test status when setup is complete."""
        env_file = tmp_path / ".env"
        env_file.write_text("DB_USER=myuser\nDB_PASSWORD=secret\nGOOGLE_SHEET_ID=abc123\n")
        sa_file = tmp_path / "service_account.json"
        sa_file.write_text('{"client_email": "test@test.iam.gserviceaccount.com"}')

        mock_env_path.return_value = env_file
        mock_sa_path.return_value = sa_file

        response = client.get("/api/setup/status")
        data = response.get_json()

        assert response.status_code == 200
        assert data["env_exists"] is True
        assert data["env_configured"] is True
        assert data["service_account_exists"] is True
        assert data["setup_complete"] is True

    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    def test_status_missing_files(self, mock_sa_path, mock_env_path, client, tmp_path):
        """Test status when files are missing."""
        mock_env_path.return_value = tmp_path / ".env"  # Non-existent
        mock_sa_path.return_value = tmp_path / "service_account.json"  # Non-existent

        response = client.get("/api/setup/status")
        data = response.get_json()

        assert response.status_code == 200
        assert data["env_exists"] is False
        assert data["env_configured"] is False
        assert data["service_account_exists"] is False
        assert data["setup_complete"] is False

    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    def test_status_env_not_configured(self, mock_sa_path, mock_env_path, client, tmp_path):
        """Test status when env exists but not configured."""
        env_file = tmp_path / ".env"
        env_file.write_text("DB_PASSWORD=your_password\nGOOGLE_SHEET_ID=your_spreadsheet_id_here\n")
        sa_file = tmp_path / "service_account.json"
        sa_file.write_text("{}")

        mock_env_path.return_value = env_file
        mock_sa_path.return_value = sa_file

        response = client.get("/api/setup/status")
        data = response.get_json()

        assert data["env_exists"] is True
        assert data["env_configured"] is False  # Contains placeholder values


class TestDatabaseTestEndpoint:
    """Tests for /api/setup/test-db endpoint."""

    def test_no_data_provided(self, client):
        """Test error when no data provided."""
        response = client.post(
            "/api/setup/test-db",
            data=json.dumps(None),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "No data" in data["message"]

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_successful_mysql_connection(self, mock_get_conn, client):
        """Test successful MySQL connection."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        response = client.post(
            "/api/setup/test-db",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "root",
                    "db_password": "password",
                    "db_name": "testdb",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is True
        assert "successful" in data["message"].lower()

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_failed_connection(self, mock_get_conn, client):
        """Test failed database connection."""
        mock_get_conn.side_effect = Exception("Connection refused")

        response = client.post(
            "/api/setup/test-db",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "db_host": "badhost",
                    "db_port": 3306,
                    "db_user": "root",
                    "db_password": "password",
                    "db_name": "testdb",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "Connection refused" in data["message"]
        assert "remediation" in data

    def test_sqlite_missing_path(self, client):
        """Test SQLite with missing database path."""
        response = client.post(
            "/api/setup/test-db",
            data=json.dumps(
                {
                    "db_type": "sqlite",
                    "db_name": "",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "required" in data["message"].lower()

    def test_sqlite_file_not_found(self, client):
        """Test SQLite with non-existent file."""
        response = client.post(
            "/api/setup/test-db",
            data=json.dumps(
                {
                    "db_type": "sqlite",
                    "db_name": "/nonexistent/path/db.sqlite",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "not found" in data["message"].lower()


class TestSheetsTestEndpoint:
    """Tests for /api/setup/test-sheets endpoint."""

    def test_no_data_provided(self, client):
        """Test error when no data provided."""
        response = client.post(
            "/api/setup/test-sheets",
            data=json.dumps(None),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "No data" in data["message"]

    def test_missing_service_account(self, client):
        """Test error when service account is missing."""
        response = client.post(
            "/api/setup/test-sheets",
            data=json.dumps(
                {
                    "sheet_id": "abc123",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "service account" in data["message"].lower()

    def test_missing_sheet_id(self, client):
        """Test error when sheet ID is missing."""
        response = client.post(
            "/api/setup/test-sheets",
            data=json.dumps(
                {
                    "service_account": {"client_email": "test@test.iam.gserviceaccount.com"},
                    "sheet_id": "",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "sheet id" in data["message"].lower()

    @patch("gspread.authorize")
    @patch("google.oauth2.service_account.Credentials.from_service_account_info")
    def test_successful_connection(self, mock_creds, mock_authorize, client):
        """Test successful Google Sheets connection."""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "My Test Sheet"
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_authorize.return_value = mock_client

        response = client.post(
            "/api/setup/test-sheets",
            data=json.dumps(
                {
                    "service_account": {
                        "client_email": "test@test.iam.gserviceaccount.com",
                        "private_key": "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----",
                    },
                    "sheet_id": "abc123xyz",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is True
        assert data["sheet_title"] == "My Test Sheet"

    @patch("gspread.authorize")
    @patch("google.oauth2.service_account.Credentials.from_service_account_info")
    def test_extracts_id_from_url(self, mock_creds, mock_authorize, client):
        """Test sheet ID extraction from full URL."""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Sheet"
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_authorize.return_value = mock_client

        response = client.post(
            "/api/setup/test-sheets",
            data=json.dumps(
                {
                    "service_account": {"client_email": "test@test.iam.gserviceaccount.com"},
                    "sheet_id": "https://docs.google.com/spreadsheets/d/abc123xyz/edit#gid=0",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is True
        mock_client.open_by_key.assert_called_with("abc123xyz")


class TestPreviewQueryEndpoint:
    """Tests for /api/setup/preview-query endpoint."""

    def test_no_data_provided(self, client):
        """Test error when no data provided."""
        response = client.post(
            "/api/setup/preview-query",
            data=json.dumps(None),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "No data" in data["message"]

    def test_missing_query(self, client):
        """Test error when query is missing."""
        response = client.post(
            "/api/setup/preview-query",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "sql_query": "",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "query required" in data["message"].lower()

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_successful_query(self, mock_get_conn, client):
        """Test successful query preview."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.headers = ["id", "name", "email"]
        mock_result.rows = [[1, "Alice", "alice@example.com"], [2, "Bob", "bob@example.com"]]
        mock_conn.execute.return_value = mock_result
        mock_get_conn.return_value = mock_conn

        response = client.post(
            "/api/setup/preview-query",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "root",
                    "db_password": "password",
                    "db_name": "testdb",
                    "sql_query": "SELECT * FROM users",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is True
        assert data["row_count"] == 2
        assert data["headers"] == ["id", "name", "email"]
        assert len(data["preview_rows"]) == 2

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_query_failure(self, mock_get_conn, client):
        """Test query execution failure."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = Exception("Table 'users' doesn't exist")
        mock_get_conn.return_value = mock_conn

        response = client.post(
            "/api/setup/preview-query",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "root",
                    "db_password": "password",
                    "db_name": "testdb",
                    "sql_query": "SELECT * FROM users",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "doesn't exist" in data["message"]


class TestRunSyncEndpoint:
    """Tests for /api/setup/run-sync endpoint."""

    def test_no_data_provided(self, client):
        """Test error when no data provided."""
        response = client.post(
            "/api/setup/run-sync",
            data=json.dumps(None),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "No data" in data["message"]

    @patch("mysql_to_sheets.core.sync.run_sync")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    def test_successful_sync(self, mock_sa_path, mock_run_sync, client, tmp_path):
        """Test successful sync execution."""
        # Create temp service account file
        sa_file = tmp_path / "service_account.json"
        sa_file.write_text("{}")
        mock_sa_path.return_value = str(sa_file)

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.rows_synced = 50
        mock_run_sync.return_value = mock_result

        response = client.post(
            "/api/setup/run-sync",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "root",
                    "db_password": "password",
                    "db_name": "testdb",
                    "sheet_id": "abc123",
                    "worksheet": "Sheet1",
                    "sql_query": "SELECT * FROM users",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is True
        assert data["rows_synced"] == 50

    @patch("mysql_to_sheets.core.sync.run_sync")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    def test_failed_sync(self, mock_sa_path, mock_run_sync, client, tmp_path):
        """Test failed sync execution."""
        sa_file = tmp_path / "service_account.json"
        sa_file.write_text("{}")
        mock_sa_path.return_value = str(sa_file)

        mock_result = MagicMock(spec=["success", "error", "rows_synced"])
        mock_result.success = False
        mock_result.error = "Permission denied"
        mock_run_sync.return_value = mock_result

        response = client.post(
            "/api/setup/run-sync",
            data=json.dumps(
                {
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "root",
                    "db_password": "password",
                    "db_name": "testdb",
                    "sheet_id": "abc123",
                    "worksheet": "Sheet1",
                    "sql_query": "SELECT * FROM users",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "Permission denied" in data["message"]


class TestSaveConfigEndpoint:
    """Tests for /api/setup/save-config endpoint."""

    def test_no_data_provided(self, client):
        """Test error when no data provided."""
        response = client.post(
            "/api/setup/save-config",
            data=json.dumps(None),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is False
        assert "No data" in data["message"]

    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path")
    def test_successful_save(self, mock_env_path, client, tmp_path):
        """Test successful config save."""
        env_file = tmp_path / ".env"
        mock_env_path.return_value = env_file

        response = client.post(
            "/api/setup/save-config",
            data=json.dumps(
                {
                    "DB_TYPE": "mysql",
                    "DB_HOST": "localhost",
                    "DB_PORT": "3306",
                    "DB_USER": "myuser",
                    "DB_PASSWORD": "mypass",
                    "DB_NAME": "mydb",
                    "GOOGLE_SHEET_ID": "sheet123",
                }
            ),
            content_type="application/json",
        )
        data = response.get_json()

        assert data["success"] is True
        assert env_file.exists()

        content = env_file.read_text()
        assert "DB_TYPE=mysql" in content
        assert "DB_HOST=localhost" in content
        assert "GOOGLE_SHEET_ID=sheet123" in content
        assert "LOG_LEVEL=INFO" in content  # Default added


class TestErrorRemediationHelpers:
    """Tests for error remediation helper functions."""

    def test_db_connection_refused(self):
        """Test remediation for connection refused."""
        result = _get_db_error_remediation("Connection refused on port 3306")
        assert "running" in result.lower() and "host" in result.lower()

    def test_db_access_denied(self):
        """Test remediation for access denied."""
        result = _get_db_error_remediation("Access denied for user 'root'@'localhost'")
        assert "username" in result.lower() or "password" in result.lower()

    def test_db_authentication_failed(self):
        """Test remediation for authentication failure."""
        result = _get_db_error_remediation("Authentication failed")
        assert "username" in result.lower() or "password" in result.lower()

    def test_db_unknown_database(self):
        """Test remediation for unknown database."""
        result = _get_db_error_remediation("Unknown database 'testdb'")
        assert "database name" in result.lower()

    def test_db_timeout(self):
        """Test remediation for timeout."""
        result = _get_db_error_remediation("Connection timeout error")
        # Function returns firewall/network hints for timeout
        assert "network" in result.lower() or "firewall" in result.lower()

    def test_db_ssl_error(self):
        """Test remediation for SSL error."""
        result = _get_db_error_remediation("SSL connection error")
        assert "ssl" in result.lower()

    def test_db_generic_error(self):
        """Test remediation for generic error."""
        result = _get_db_error_remediation("Some random error")
        assert "credentials" in result.lower()

    def test_sheets_not_found(self):
        """Test remediation for sheet not found."""
        result = _get_sheets_error_remediation("Spreadsheet not found")
        assert "sheet id" in result.lower()

    def test_sheets_permission_denied(self):
        """Test remediation for permission denied."""
        result = _get_sheets_error_remediation("Permission denied")
        assert "share" in result.lower()

    def test_sheets_forbidden(self):
        """Test remediation for forbidden access."""
        result = _get_sheets_error_remediation("403 Forbidden")
        assert "share" in result.lower()

    def test_sheets_invalid_credentials(self):
        """Test remediation for invalid credentials."""
        result = _get_sheets_error_remediation("Invalid credential format")
        assert "service account" in result.lower() or "json" in result.lower()

    def test_sheets_quota_exceeded(self):
        """Test remediation for quota exceeded."""
        result = _get_sheets_error_remediation("Quota exceeded for writes")
        assert "quota" in result.lower()

    def test_sheets_generic_error(self):
        """Test remediation for generic sheets error."""
        result = _get_sheets_error_remediation("Unknown API error")
        assert "service account" in result.lower()


class TestSetupPage:
    """Tests for setup page rendering."""

    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_config_dir")
    def test_setup_page_renders(
        self, mock_config_dir, mock_sa_path, mock_env_path, client, tmp_path
    ):
        """Test setup page renders correctly."""
        mock_env_path.return_value = tmp_path / ".env"
        mock_sa_path.return_value = tmp_path / "service_account.json"
        mock_config_dir.return_value = tmp_path

        response = client.get("/setup")

        assert response.status_code == 200
        assert b"Setup Wizard" in response.data

    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path")
    @patch("mysql_to_sheets.web.blueprints.dashboard.get_config_dir")
    def test_setup_page_shows_configured_state(
        self, mock_config_dir, mock_sa_path, mock_env_path, client, tmp_path
    ):
        """Test setup page shows correct state when configured."""
        env_file = tmp_path / ".env"
        env_file.write_text("DB_USER=myuser\nDB_PASSWORD=secret\n")
        sa_file = tmp_path / "service_account.json"
        sa_file.write_text("{}")

        mock_env_path.return_value = env_file
        mock_sa_path.return_value = sa_file
        mock_config_dir.return_value = tmp_path

        response = client.get("/setup")

        assert response.status_code == 200
