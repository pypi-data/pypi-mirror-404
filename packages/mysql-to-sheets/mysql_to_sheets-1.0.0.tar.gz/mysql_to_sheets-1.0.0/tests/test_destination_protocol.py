"""Tests for the destination protocol and Google Sheets adapter.

These tests verify:
1. Protocol compliance for destination connections
2. Google Sheets adapter functionality with mocked gspread
3. Factory function behavior
4. Error handling and exception mapping
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.destinations import (
    BaseDestinationConnection,
    DestinationConfig,
    DestinationConnection,
    UnsupportedDestinationError,
    WriteResult,
    get_destination,
    list_supported_destinations,
    register_destination,
)
from mysql_to_sheets.core.destinations.google_sheets import GoogleSheetsDestination
from mysql_to_sheets.core.exceptions import DestinationError, SheetsError


class TestDestinationConfig:
    """Tests for DestinationConfig dataclass."""

    def test_default_values(self) -> None:
        """Test DestinationConfig default values."""
        config = DestinationConfig()
        assert config.destination_type == "google_sheets"
        assert config.target_id == ""
        assert config.target_name == "Sheet1"
        assert config.credentials_file is None
        assert config.timeout == 60
        assert config.options == {}

    def test_custom_values(self) -> None:
        """Test DestinationConfig with custom values."""
        config = DestinationConfig(
            destination_type="excel_online",
            target_id="workbook123",
            target_name="DataSheet",
            credentials_file="/path/to/creds.json",
            timeout=120,
            options={"create_if_missing": True},
        )
        assert config.destination_type == "excel_online"
        assert config.target_id == "workbook123"
        assert config.target_name == "DataSheet"
        assert config.credentials_file == "/path/to/creds.json"
        assert config.timeout == 120
        assert config.options == {"create_if_missing": True}


class TestWriteResult:
    """Tests for WriteResult dataclass."""

    def test_default_values(self) -> None:
        """Test WriteResult default values."""
        result = WriteResult(success=True)
        assert result.success is True
        assert result.rows_written == 0
        assert result.message == ""
        assert result.metadata == {}

    def test_with_all_fields(self) -> None:
        """Test WriteResult with all fields populated."""
        result = WriteResult(
            success=True,
            rows_written=100,
            message="Data written successfully",
            metadata={"mode": "replace", "sheet_id": "abc123"},
        )
        assert result.success is True
        assert result.rows_written == 100
        assert result.message == "Data written successfully"
        assert result.metadata["mode"] == "replace"


class TestDestinationConnectionProtocol:
    """Tests for DestinationConnection protocol compliance."""

    def test_google_sheets_implements_protocol(self) -> None:
        """Verify GoogleSheetsDestination implements DestinationConnection protocol."""
        config = DestinationConfig(
            target_id="test_sheet_id",
            target_name="Sheet1",
        )
        dest = GoogleSheetsDestination(config)

        # Check that it's a valid DestinationConnection
        assert isinstance(dest, DestinationConnection)

    def test_protocol_has_required_methods(self) -> None:
        """Verify protocol defines all required methods."""
        # These should be defined in the protocol
        assert hasattr(DestinationConnection, "destination_type")
        assert hasattr(DestinationConnection, "connect")
        assert hasattr(DestinationConnection, "write")
        assert hasattr(DestinationConnection, "read")
        assert hasattr(DestinationConnection, "clear")
        assert hasattr(DestinationConnection, "close")
        assert hasattr(DestinationConnection, "test_connection")
        assert hasattr(DestinationConnection, "__enter__")
        assert hasattr(DestinationConnection, "__exit__")


class TestGoogleSheetsDestination:
    """Tests for GoogleSheetsDestination adapter."""

    @pytest.fixture
    def config(self) -> DestinationConfig:
        """Create a test configuration."""
        return DestinationConfig(
            destination_type="google_sheets",
            target_id="test_spreadsheet_id",
            target_name="TestSheet",
            credentials_file="/fake/path/service_account.json",
            timeout=30,
        )

    @pytest.fixture
    def mock_gspread(self):
        """Create mock gspread module and client."""
        import gspread.exceptions

        with patch(
            "mysql_to_sheets.core.destinations.google_sheets.gspread"
        ) as mock_gspread_module:
            # Create mock objects
            mock_client = MagicMock()
            mock_spreadsheet = MagicMock()
            mock_worksheet = MagicMock()

            # Configure mock behavior
            mock_gspread_module.service_account.return_value = mock_client
            mock_client.open_by_key.return_value = mock_spreadsheet
            mock_spreadsheet.worksheet.return_value = mock_worksheet
            mock_spreadsheet.worksheets.return_value = [mock_worksheet]
            mock_worksheet.title = "TestSheet"
            mock_worksheet.id = 0
            mock_worksheet.row_count = 1000
            mock_worksheet.col_count = 26

            # Keep real exception classes for proper except clause handling
            mock_gspread_module.exceptions = gspread.exceptions

            yield {
                "gspread": mock_gspread_module,
                "client": mock_client,
                "spreadsheet": mock_spreadsheet,
                "worksheet": mock_worksheet,
            }

    def test_destination_type(self, config: DestinationConfig) -> None:
        """Test destination_type property."""
        dest = GoogleSheetsDestination(config)
        assert dest.destination_type == "google_sheets"

    def test_connect_success(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test successful connection."""
        dest = GoogleSheetsDestination(config)
        dest.connect()

        # Verify gspread calls
        mock_gspread["gspread"].service_account.assert_called_once()
        mock_gspread["client"].open_by_key.assert_called_once_with("test_spreadsheet_id")
        mock_gspread["spreadsheet"].worksheet.assert_called_once_with("TestSheet")

        assert dest._connected is True

    def test_connect_spreadsheet_not_found(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test error when spreadsheet not found."""
        mock_gspread["client"].open_by_key.side_effect = (
            mock_gspread["gspread"].exceptions.SpreadsheetNotFound()
        )

        dest = GoogleSheetsDestination(config)
        with pytest.raises(SheetsError) as exc_info:
            dest.connect()

        assert "not found" in str(exc_info.value).lower()

    def test_connect_worksheet_not_found(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test error when worksheet not found."""
        mock_gspread["spreadsheet"].worksheet.side_effect = (
            mock_gspread["gspread"].exceptions.WorksheetNotFound()
        )
        mock_gspread["spreadsheet"].worksheets.return_value = [MagicMock(title="Sheet1")]

        dest = GoogleSheetsDestination(config)
        with pytest.raises(SheetsError) as exc_info:
            dest.connect()

        assert "not found" in str(exc_info.value).lower()

    def test_connect_creates_worksheet_if_missing(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test worksheet creation when create_if_missing is True."""
        config.options["create_if_missing"] = True
        mock_gspread["spreadsheet"].worksheet.side_effect = (
            mock_gspread["gspread"].exceptions.WorksheetNotFound()
        )

        mock_new_worksheet = MagicMock()
        mock_gspread["spreadsheet"].add_worksheet.return_value = mock_new_worksheet

        dest = GoogleSheetsDestination(config)
        dest.connect()

        mock_gspread["spreadsheet"].add_worksheet.assert_called_once()

    def test_write_replace_mode(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test write with replace mode."""
        dest = GoogleSheetsDestination(config)
        dest.connect()

        headers = ["Name", "Age"]
        rows = [["Alice", 30], ["Bob", 25]]
        result = dest.write(headers, rows, mode="replace")

        # Verify worksheet operations
        mock_gspread["worksheet"].clear.assert_called_once()
        mock_gspread["worksheet"].update.assert_called_once()

        assert result.success is True
        assert result.rows_written == 2
        assert result.metadata["mode"] == "replace"

    def test_write_append_mode(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test write with append mode."""
        dest = GoogleSheetsDestination(config)
        dest.connect()

        rows = [["Alice", 30], ["Bob", 25]]
        result = dest.write([], rows, mode="append")

        mock_gspread["worksheet"].append_rows.assert_called_once()
        assert result.success is True
        assert result.rows_written == 2
        assert result.metadata["mode"] == "append"

    def test_write_invalid_mode(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test write with invalid mode raises error."""
        dest = GoogleSheetsDestination(config)
        dest.connect()

        with pytest.raises(SheetsError) as exc_info:
            dest.write(["Name"], [["Alice"]], mode="invalid")

        assert "unsupported" in str(exc_info.value.message).lower()

    def test_read(self, config: DestinationConfig, mock_gspread: dict) -> None:
        """Test reading data from worksheet."""
        mock_gspread["worksheet"].get_all_values.return_value = [
            ["Name", "Age"],
            ["Alice", "30"],
            ["Bob", "25"],
        ]

        dest = GoogleSheetsDestination(config)
        dest.connect()
        headers, rows = dest.read()

        assert headers == ["Name", "Age"]
        assert rows == [["Alice", "30"], ["Bob", "25"]]

    def test_read_empty_sheet(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test reading from empty worksheet."""
        mock_gspread["worksheet"].get_all_values.return_value = []

        dest = GoogleSheetsDestination(config)
        dest.connect()
        headers, rows = dest.read()

        assert headers == []
        assert rows == []

    def test_clear(self, config: DestinationConfig, mock_gspread: dict) -> None:
        """Test clearing worksheet."""
        dest = GoogleSheetsDestination(config)
        dest.connect()
        dest.clear()

        mock_gspread["worksheet"].clear.assert_called_once()

    def test_close(self, config: DestinationConfig, mock_gspread: dict) -> None:
        """Test closing connection."""
        dest = GoogleSheetsDestination(config)
        dest.connect()
        dest.close()

        assert dest._connected is False
        assert dest._client is None
        assert dest._spreadsheet is None
        assert dest._worksheet is None

    def test_context_manager(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test context manager protocol."""
        with GoogleSheetsDestination(config) as dest:
            assert dest._connected is True
            result = dest.write(["A"], [["1"]])
            assert result.success is True

        # After exiting context, connection should be closed
        assert dest._connected is False

    def test_test_connection_success(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test test_connection returns True on success."""
        dest = GoogleSheetsDestination(config)
        result = dest.test_connection()
        assert result is True

    def test_test_connection_failure(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test test_connection returns False on failure."""
        mock_gspread["client"].open_by_key.side_effect = (
            mock_gspread["gspread"].exceptions.SpreadsheetNotFound()
        )

        dest = GoogleSheetsDestination(config)
        result = dest.test_connection()
        assert result is False

    def test_list_worksheets(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test listing all worksheets."""
        mock_ws1 = MagicMock()
        mock_ws1.title = "Sheet1"
        mock_ws1.id = 0
        mock_ws1.row_count = 1000
        mock_ws1.col_count = 26

        mock_ws2 = MagicMock()
        mock_ws2.title = "Data"
        mock_ws2.id = 123
        mock_ws2.row_count = 500
        mock_ws2.col_count = 10

        mock_gspread["spreadsheet"].worksheets.return_value = [mock_ws1, mock_ws2]

        dest = GoogleSheetsDestination(config)
        dest.connect()
        worksheets = dest.list_worksheets()

        assert len(worksheets) == 2
        assert worksheets[0]["title"] == "Sheet1"
        assert worksheets[1]["title"] == "Data"

    def test_select_worksheet(
        self, config: DestinationConfig, mock_gspread: dict
    ) -> None:
        """Test switching to a different worksheet."""
        mock_new_ws = MagicMock()
        mock_new_ws.title = "NewSheet"
        mock_gspread["spreadsheet"].worksheet.return_value = mock_new_ws

        dest = GoogleSheetsDestination(config)
        dest.connect()
        dest.select_worksheet("NewSheet")

        assert dest.config.target_name == "NewSheet"


class TestDestinationFactory:
    """Tests for the destination factory function."""

    def test_get_google_sheets_destination(self) -> None:
        """Test creating Google Sheets destination."""
        config = DestinationConfig(
            destination_type="google_sheets",
            target_id="test_id",
        )
        dest = get_destination(config)
        assert isinstance(dest, GoogleSheetsDestination)

    def test_get_sheets_alias(self) -> None:
        """Test 'sheets' alias works."""
        config = DestinationConfig(
            destination_type="sheets",
            target_id="test_id",
        )
        dest = get_destination(config)
        assert isinstance(dest, GoogleSheetsDestination)

    def test_get_gsheets_alias(self) -> None:
        """Test 'gsheets' alias works."""
        config = DestinationConfig(
            destination_type="gsheets",
            target_id="test_id",
        )
        dest = get_destination(config)
        assert isinstance(dest, GoogleSheetsDestination)

    def test_unsupported_destination(self) -> None:
        """Test error for unsupported destination type."""
        config = DestinationConfig(
            destination_type="unknown_destination",
            target_id="test_id",
        )
        with pytest.raises(UnsupportedDestinationError) as exc_info:
            get_destination(config)

        assert "unsupported" in str(exc_info.value).lower()
        assert exc_info.value.destination_type == "unknown_destination"

    def test_list_supported_destinations(self) -> None:
        """Test listing supported destinations."""
        supported = list_supported_destinations()
        assert "google_sheets" in supported

    def test_register_custom_destination(self) -> None:
        """Test registering a custom destination adapter."""

        class MockDestination(BaseDestinationConnection):
            """Mock destination for testing registration."""

            @property
            def destination_type(self) -> str:
                return "mock"

            def connect(self) -> None:
                pass

            def write(
                self, headers: list[str], rows: list[list[Any]], mode: str = "replace"
            ) -> WriteResult:
                return WriteResult(success=True, rows_written=len(rows))

            def read(self) -> tuple[list[str], list[list[Any]]]:
                return [], []

            def clear(self) -> None:
                pass

            def close(self) -> None:
                pass

        # Register the mock destination
        register_destination("mock", MockDestination)

        # Now it should be creatable
        config = DestinationConfig(
            destination_type="mock",
            target_id="test_id",
        )
        dest = get_destination(config)
        assert isinstance(dest, MockDestination)

        # Should appear in supported list
        supported = list_supported_destinations()
        assert "mock" in supported


class TestDestinationError:
    """Tests for DestinationError exception."""

    def test_basic_error(self) -> None:
        """Test creating a basic DestinationError."""
        error = DestinationError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_error_with_details(self) -> None:
        """Test DestinationError with all details."""
        original = ValueError("underlying issue")
        error = DestinationError(
            message="Write operation failed",
            destination_type="google_sheets",
            target_id="sheet123",
            target_name="Data",
            original_error=original,
            code="DEST_002",
        )

        assert error.destination_type == "google_sheets"
        assert error.target_id == "sheet123"
        assert error.target_name == "Data"
        assert error.original_error is original
        assert error.code == "DEST_002"

    def test_error_to_dict(self) -> None:
        """Test DestinationError serialization."""
        error = DestinationError(
            message="Connection failed",
            destination_type="google_sheets",
            target_id="sheet123",
        )
        data = error.to_dict()

        assert data["message"] == "Connection failed"
        assert data["details"]["destination_type"] == "google_sheets"
        assert data["details"]["target_id"] == "sheet123"


class TestRateLimitHandling:
    """Tests for Google Sheets rate limit handling."""

    @pytest.fixture
    def config(self) -> DestinationConfig:
        """Create a test configuration."""
        return DestinationConfig(
            destination_type="google_sheets",
            target_id="test_spreadsheet_id",
            target_name="TestSheet",
            credentials_file="/fake/path/service_account.json",
        )

    def test_rate_limit_error_on_write(self, config: DestinationConfig) -> None:
        """Test rate limit error is properly handled during write."""
        import gspread
        import gspread.exceptions

        with patch(
            "mysql_to_sheets.core.destinations.google_sheets.gspread"
        ) as mock_gspread:
            mock_client = MagicMock()
            mock_spreadsheet = MagicMock()
            mock_worksheet = MagicMock()

            mock_gspread.service_account.return_value = mock_client
            mock_client.open_by_key.return_value = mock_spreadsheet
            mock_spreadsheet.worksheet.return_value = mock_worksheet
            mock_worksheet.title = "TestSheet"

            # Keep real exception classes
            mock_gspread.exceptions = gspread.exceptions

            # Create mock response object for APIError
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "error": {"message": "Quota exceeded", "code": 429}
            }

            # Simulate rate limit on write
            rate_limit_error = gspread.exceptions.APIError(mock_response)
            mock_worksheet.clear.side_effect = rate_limit_error

            dest = GoogleSheetsDestination(config)
            dest.connect()

            with pytest.raises(SheetsError) as exc_info:
                dest.write(["A"], [["1"]])

            assert exc_info.value.rate_limited is True
            assert exc_info.value.retry_after == 60.0
