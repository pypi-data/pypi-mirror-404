"""Tests for worksheets API blueprint."""

import json
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("flask")

import gspread
from flask import Flask
from flask.testing import FlaskClient

from mysql_to_sheets.web.app import create_app


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


class TestListWorksheets:
    """Tests for GET /api/worksheets endpoint."""

    def test_list_worksheets_success(self, client: FlaskClient) -> None:
        """Test successful worksheet listing."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Test Spreadsheet"
        mock_spreadsheet.id = "test-sheet-id"

        # Mock worksheets
        mock_ws1 = MagicMock()
        mock_ws1.title = "Sheet1"
        mock_ws1.id = 0
        mock_ws1.row_count = 1000
        mock_ws1.col_count = 26

        mock_ws2 = MagicMock()
        mock_ws2.title = "Data Export"
        mock_ws2.id = 123456
        mock_ws2.row_count = 500
        mock_ws2.col_count = 10

        mock_spreadsheet.worksheets.return_value = [mock_ws1, mock_ws2]
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.get("/api/worksheets")
                    data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert data["total"] == 2
        assert data["spreadsheet_title"] == "Test Spreadsheet"
        assert data["spreadsheet_id"] == "test-sheet-id"
        assert len(data["worksheets"]) == 2
        assert data["worksheets"][0]["title"] == "Sheet1"
        assert data["worksheets"][0]["gid"] == 0
        assert data["worksheets"][1]["title"] == "Data Export"
        assert data["worksheets"][1]["gid"] == 123456

    def test_list_worksheets_with_sheet_id_override(self, client: FlaskClient) -> None:
        """Test listing worksheets with sheet_id query parameter."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Override Spreadsheet"
        mock_spreadsheet.id = "override-sheet-id"

        mock_ws = MagicMock()
        mock_ws.title = "Sheet1"
        mock_ws.id = 0
        mock_ws.row_count = 1000
        mock_ws.col_count = 26
        mock_spreadsheet.worksheets.return_value = [mock_ws]

        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    with patch(
                        "mysql_to_sheets.web.blueprints.api.worksheets.parse_sheet_id"
                    ) as mock_parse:
                        mock_config.return_value = MagicMock(
                            google_sheet_id="default-sheet-id",
                            service_account_file="./service_account.json",
                        )
                        mock_parse.return_value = "override-sheet-id"

                        response = client.get("/api/worksheets?sheet_id=override-sheet-id")
                        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["spreadsheet_id"] == "override-sheet-id"
        mock_parse.assert_called_once_with("override-sheet-id")

    def test_list_worksheets_sheets_error(self, client: FlaskClient) -> None:
        """Test listing worksheets with SheetsError."""
        mock_gc = MagicMock()

        # Create a real APIError with properly mocked response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 404, "message": "Spreadsheet not found"}
        }
        api_error = gspread.exceptions.APIError(response=mock_response)
        mock_gc.open_by_key.side_effect = api_error

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="invalid-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.get("/api/worksheets")
                    data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        # The error message will contain "Spreadsheet not found"
        assert "spreadsheet" in data["error"].lower() or "not found" in data["error"].lower()

    def test_list_worksheets_no_sheet_id_configured(self, client: FlaskClient) -> None:
        """Test listing worksheets without configured sheet ID."""
        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                mock_config.return_value = MagicMock(
                    google_sheet_id="",
                    service_account_file="./service_account.json",
                )

                response = client.get("/api/worksheets")
                data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "No sheet ID provided" in data["error"]

    def test_list_worksheets_service_account_not_found(self, client: FlaskClient) -> None:
        """Test listing worksheets with missing service account file."""
        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch(
                    "gspread.service_account", side_effect=FileNotFoundError("File not found")
                ):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./nonexistent.json",
                    )

                    response = client.get("/api/worksheets")
                    data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Service account file not found" in data["error"]

    def test_list_worksheets_unexpected_error(self, client: FlaskClient) -> None:
        """Test listing worksheets with unexpected error."""
        mock_gc = MagicMock()
        mock_gc.open_by_key.side_effect = RuntimeError("Unexpected error")

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.get("/api/worksheets")
                    data = json.loads(response.data)

        assert response.status_code == 500
        assert data["success"] is False
        assert "Unexpected error" in data["error"]


class TestCreateWorksheet:
    """Tests for POST /api/worksheets endpoint."""

    def test_create_worksheet_success(self, client: FlaskClient) -> None:
        """Test successful worksheet creation."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_new_worksheet = MagicMock()
        mock_new_worksheet.title = "New Sheet"
        mock_new_worksheet.id = 789
        mock_new_worksheet.row_count = 1000
        mock_new_worksheet.col_count = 26

        mock_spreadsheet.add_worksheet.return_value = mock_new_worksheet
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.post(
                        "/api/worksheets",
                        json={"title": "New Sheet"},
                        content_type="application/json",
                    )
                    data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        assert data["message"] == "Worksheet 'New Sheet' created successfully"
        assert data["worksheet"]["title"] == "New Sheet"
        assert data["worksheet"]["gid"] == 789
        assert data["worksheet"]["rows"] == 1000
        assert data["worksheet"]["cols"] == 26

        # Verify default dimensions were used
        mock_spreadsheet.add_worksheet.assert_called_once_with(
            title="New Sheet", rows=1000, cols=26
        )

    def test_create_worksheet_custom_dimensions(self, client: FlaskClient) -> None:
        """Test creating worksheet with custom rows and columns."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_new_worksheet = MagicMock()
        mock_new_worksheet.title = "Large Sheet"
        mock_new_worksheet.id = 999
        mock_new_worksheet.row_count = 5000
        mock_new_worksheet.col_count = 50

        mock_spreadsheet.add_worksheet.return_value = mock_new_worksheet
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.post(
                        "/api/worksheets",
                        json={"title": "Large Sheet", "rows": 5000, "cols": 50},
                        content_type="application/json",
                    )
                    data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        assert data["worksheet"]["rows"] == 5000
        assert data["worksheet"]["cols"] == 50

        # Verify custom dimensions were passed
        mock_spreadsheet.add_worksheet.assert_called_once_with(
            title="Large Sheet", rows=5000, cols=50
        )

    def test_create_worksheet_empty_title(self, client: FlaskClient) -> None:
        """Test creating worksheet with empty title."""
        response = client.post(
            "/api/worksheets",
            json={"title": ""},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Worksheet title is required" in data["error"]

    def test_create_worksheet_missing_title(self, client: FlaskClient) -> None:
        """Test creating worksheet without title field."""
        response = client.post(
            "/api/worksheets",
            json={},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Worksheet title is required" in data["error"]

    def test_create_worksheet_whitespace_title(self, client: FlaskClient) -> None:
        """Test creating worksheet with whitespace-only title."""
        response = client.post(
            "/api/worksheets",
            json={"title": "   "},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Worksheet title is required" in data["error"]

    def test_create_worksheet_invalid_rows_negative(self, client: FlaskClient) -> None:
        """Test creating worksheet with negative rows."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "rows": -1},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Rows must be between" in data["error"]

    def test_create_worksheet_invalid_rows_zero(self, client: FlaskClient) -> None:
        """Test creating worksheet with zero rows."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "rows": 0},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Rows must be between" in data["error"]

    def test_create_worksheet_invalid_rows_too_large(self, client: FlaskClient) -> None:
        """Test creating worksheet with rows exceeding Google Sheets limit."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "rows": 20000000},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Rows must be between" in data["error"]

    def test_create_worksheet_invalid_cols_negative(self, client: FlaskClient) -> None:
        """Test creating worksheet with negative columns."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "cols": -5},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Columns must be between" in data["error"]

    def test_create_worksheet_invalid_cols_too_large(self, client: FlaskClient) -> None:
        """Test creating worksheet with columns exceeding Google Sheets limit."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "cols": 20000},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Columns must be between" in data["error"]

    def test_create_worksheet_invalid_rows_string(self, client: FlaskClient) -> None:
        """Test creating worksheet with non-numeric rows."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "rows": "not a number"},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Invalid rows or cols value" in data["error"]

    def test_create_worksheet_invalid_cols_string(self, client: FlaskClient) -> None:
        """Test creating worksheet with non-numeric cols."""
        response = client.post(
            "/api/worksheets",
            json={"title": "Test", "cols": "abc"},
            content_type="application/json",
        )
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Invalid rows or cols value" in data["error"]

    def test_create_worksheet_already_exists(self, client: FlaskClient) -> None:
        """Test creating worksheet that already exists."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        # Create a real APIError with properly mocked response that includes "already exists"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 400, "message": "A sheet with this name already exists"}
        }
        api_error = gspread.exceptions.APIError(response=mock_response)

        # Patch str() to return the message we want
        with patch.object(
            api_error, "__str__", return_value="A sheet with this name already exists"
        ):
            mock_spreadsheet.add_worksheet.side_effect = api_error
            mock_gc.open_by_key.return_value = mock_spreadsheet

            with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
                with patch(
                    "mysql_to_sheets.web.blueprints.api.worksheets.get_config"
                ) as mock_config:
                    with patch("gspread.service_account", return_value=mock_gc):
                        mock_config.return_value = MagicMock(
                            google_sheet_id="test-sheet-id",
                            service_account_file="./service_account.json",
                        )

                        response = client.post(
                            "/api/worksheets",
                            json={"title": "Duplicate Sheet"},
                            content_type="application/json",
                        )
                        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "already exists" in data["error"].lower()

    def test_create_worksheet_with_sheet_id_override(self, client: FlaskClient) -> None:
        """Test creating worksheet with sheet_id in request body."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "override-sheet-id"

        mock_new_worksheet = MagicMock()
        mock_new_worksheet.title = "New Sheet"
        mock_new_worksheet.id = 111
        mock_new_worksheet.row_count = 1000
        mock_new_worksheet.col_count = 26

        mock_spreadsheet.add_worksheet.return_value = mock_new_worksheet
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    with patch(
                        "mysql_to_sheets.web.blueprints.api.worksheets.parse_sheet_id"
                    ) as mock_parse:
                        mock_config.return_value = MagicMock(
                            google_sheet_id="default-sheet-id",
                            service_account_file="./service_account.json",
                        )
                        mock_parse.return_value = "override-sheet-id"

                        response = client.post(
                            "/api/worksheets",
                            json={"title": "New Sheet", "sheet_id": "override-sheet-id"},
                            content_type="application/json",
                        )
                        data = json.loads(response.data)

        assert response.status_code == 201
        assert data["success"] is True
        mock_parse.assert_called_once_with("override-sheet-id")

    def test_create_worksheet_api_error(self, client: FlaskClient) -> None:
        """Test creating worksheet with generic API error."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        api_error = gspread.exceptions.APIError(
            response=MagicMock(status_code=500, text="Internal error")
        )
        mock_spreadsheet.add_worksheet.side_effect = api_error
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.post(
                        "/api/worksheets",
                        json={"title": "Test Sheet"},
                        content_type="application/json",
                    )
                    data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Failed to create worksheet" in data["error"]


class TestDeleteWorksheet:
    """Tests for DELETE /api/worksheets/<title> endpoint."""

    def test_delete_worksheet_success(self, client: FlaskClient) -> None:
        """Test successful worksheet deletion."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_worksheet = MagicMock()
        mock_worksheet.title = "OldSheet"
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.delete("/api/worksheets/OldSheet")
                    data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        assert data["message"] == "Worksheet 'OldSheet' deleted successfully"
        mock_spreadsheet.del_worksheet.assert_called_once_with(mock_worksheet)

    def test_delete_worksheet_not_found(self, client: FlaskClient) -> None:
        """Test deleting non-existent worksheet."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound(
            "Worksheet not found"
        )
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.delete("/api/worksheets/NonExistent")
                    data = json.loads(response.data)

        assert response.status_code == 404
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_delete_worksheet_empty_title(self, client: FlaskClient) -> None:
        """Test deleting worksheet with empty title."""
        response = client.delete("/api/worksheets/   ")
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Worksheet title is required" in data["error"]

    def test_delete_worksheet_last_sheet(self, client: FlaskClient) -> None:
        """Test deleting the last worksheet in spreadsheet."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_worksheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        # Create a real APIError with properly mocked response that includes "cannot delete"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 400, "message": "Cannot delete the last sheet"}
        }
        api_error = gspread.exceptions.APIError(response=mock_response)

        # Patch str() to return the message we want
        with patch.object(api_error, "__str__", return_value="Cannot delete the last sheet"):
            mock_spreadsheet.del_worksheet.side_effect = api_error
            mock_gc.open_by_key.return_value = mock_spreadsheet

            with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
                with patch(
                    "mysql_to_sheets.web.blueprints.api.worksheets.get_config"
                ) as mock_config:
                    with patch("gspread.service_account", return_value=mock_gc):
                        mock_config.return_value = MagicMock(
                            google_sheet_id="test-sheet-id",
                            service_account_file="./service_account.json",
                        )

                        response = client.delete("/api/worksheets/Sheet1")
                        data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "cannot delete the last worksheet" in data["error"].lower()

    def test_delete_worksheet_with_sheet_id_override(self, client: FlaskClient) -> None:
        """Test deleting worksheet with sheet_id query parameter."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "override-sheet-id"

        mock_worksheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    with patch(
                        "mysql_to_sheets.web.blueprints.api.worksheets.parse_sheet_id"
                    ) as mock_parse:
                        mock_config.return_value = MagicMock(
                            google_sheet_id="default-sheet-id",
                            service_account_file="./service_account.json",
                        )
                        mock_parse.return_value = "override-sheet-id"

                        response = client.delete(
                            "/api/worksheets/OldSheet?sheet_id=override-sheet-id"
                        )
                        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["success"] is True
        mock_parse.assert_called_once_with("override-sheet-id")

    def test_delete_worksheet_api_error(self, client: FlaskClient) -> None:
        """Test deleting worksheet with generic API error."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_worksheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        api_error = gspread.exceptions.APIError(
            response=MagicMock(status_code=500, text="Internal error")
        )
        mock_spreadsheet.del_worksheet.side_effect = api_error
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.delete("/api/worksheets/TestSheet")
                    data = json.loads(response.data)

        assert response.status_code == 400
        assert data["success"] is False
        assert "Failed to delete worksheet" in data["error"]

    def test_delete_worksheet_unexpected_error(self, client: FlaskClient) -> None:
        """Test deleting worksheet with unexpected error."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test-sheet-id"

        mock_worksheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_spreadsheet.del_worksheet.side_effect = RuntimeError("Unexpected error")
        mock_gc.open_by_key.return_value = mock_spreadsheet

        with patch("mysql_to_sheets.web.blueprints.api.worksheets.reset_config"):
            with patch("mysql_to_sheets.web.blueprints.api.worksheets.get_config") as mock_config:
                with patch("gspread.service_account", return_value=mock_gc):
                    mock_config.return_value = MagicMock(
                        google_sheet_id="test-sheet-id",
                        service_account_file="./service_account.json",
                    )

                    response = client.delete("/api/worksheets/TestSheet")
                    data = json.loads(response.data)

        assert response.status_code == 500
        assert data["success"] is False
        assert "Unexpected error" in data["error"]
