"""Tests for Google Sheets utility functions."""

from unittest.mock import MagicMock

import gspread
import pytest

from mysql_to_sheets.core.exceptions import SheetsError
from mysql_to_sheets.core.sheets_utils import (
    create_worksheet,
    delete_worksheet,
    get_or_create_worksheet,
    is_sheets_url,
    is_worksheet_url,
    list_worksheets,
    parse_sheet_id,
    parse_worksheet_gid,
    parse_worksheet_identifier,
    resolve_worksheet_name_from_gid,
)


class TestParseSheetId:
    """Tests for parse_sheet_id function."""

    def test_parse_raw_sheet_id(self) -> None:
        """Raw sheet IDs are returned unchanged."""
        sheet_id = "1a2B3c4D5e6F7g8h9i0j1k2l3m4n5o6p"
        assert parse_sheet_id(sheet_id) == sheet_id

    def test_parse_raw_id_with_underscores(self) -> None:
        """Sheet IDs with underscores are valid."""
        sheet_id = "abc_123_def"
        assert parse_sheet_id(sheet_id) == sheet_id

    def test_parse_raw_id_with_hyphens(self) -> None:
        """Sheet IDs with hyphens are valid."""
        sheet_id = "abc-123-def"
        assert parse_sheet_id(sheet_id) == sheet_id

    def test_parse_url_with_edit(self) -> None:
        """URL with /edit suffix is parsed correctly."""
        url = "https://docs.google.com/spreadsheets/d/1a2B3c4D5e6F7g8h9i0j/edit"
        assert parse_sheet_id(url) == "1a2B3c4D5e6F7g8h9i0j"

    def test_parse_url_with_edit_and_gid(self) -> None:
        """URL with /edit#gid=0 suffix is parsed correctly."""
        url = "https://docs.google.com/spreadsheets/d/1a2B3c4D5e6F7g8h9i0j/edit#gid=0"
        assert parse_sheet_id(url) == "1a2B3c4D5e6F7g8h9i0j"

    def test_parse_url_without_edit(self) -> None:
        """URL without /edit suffix is parsed correctly."""
        url = "https://docs.google.com/spreadsheets/d/1a2B3c4D5e6F7g8h9i0j"
        assert parse_sheet_id(url) == "1a2B3c4D5e6F7g8h9i0j"

    def test_parse_url_with_query_params(self) -> None:
        """URL with query parameters is parsed correctly."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit?usp=sharing"
        assert parse_sheet_id(url) == "abc123"

    def test_parse_http_url(self) -> None:
        """HTTP URLs (not HTTPS) are also supported."""
        url = "http://docs.google.com/spreadsheets/d/1a2B3c4D5e6F7g8h9i0j/edit"
        assert parse_sheet_id(url) == "1a2B3c4D5e6F7g8h9i0j"

    def test_parse_url_strips_whitespace(self) -> None:
        """Leading/trailing whitespace is stripped."""
        url = "  https://docs.google.com/spreadsheets/d/abc123/edit  "
        assert parse_sheet_id(url) == "abc123"

    def test_parse_raw_id_strips_whitespace(self) -> None:
        """Leading/trailing whitespace is stripped from raw IDs."""
        sheet_id = "  abc123  "
        assert parse_sheet_id(sheet_id) == "abc123"

    def test_invalid_url_raises_error(self) -> None:
        """Invalid Google Sheets URL raises ValueError."""
        invalid_urls = [
            "https://google.com/spreadsheets/d/abc123",
            "https://docs.google.com/spreadsheets/abc123",
            "https://example.com/abc123",
        ]
        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid Google Sheets URL format"):
                parse_sheet_id(url)

    def test_wrong_google_service_urls_raise_specific_errors(self) -> None:
        """Wrong Google service URLs raise specific helpful errors."""
        # Google Docs URL
        with pytest.raises(ValueError, match="Google Docs URL"):
            parse_sheet_id("https://docs.google.com/document/d/abc123")

        # Google Forms URL
        with pytest.raises(ValueError, match="Google Forms URL"):
            parse_sheet_id("https://docs.google.com/forms/d/abc123")

        # Google Slides URL
        with pytest.raises(ValueError, match="Google Slides URL"):
            parse_sheet_id("https://docs.google.com/presentation/d/abc123")

        # Google Drive URL
        with pytest.raises(ValueError, match="Google Drive URL"):
            parse_sheet_id("https://drive.google.com/file/d/abc123")

    def test_invalid_sheet_id_raises_error(self) -> None:
        """Invalid sheet ID format raises ValueError."""
        invalid_ids = [
            "abc 123",  # Contains space
            "abc@123",  # Contains @
            "abc!123",  # Contains !
            "abc/123",  # Contains /
        ]
        for sheet_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid sheet ID format"):
                parse_sheet_id(sheet_id)

    def test_empty_value_raises_error(self) -> None:
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="Sheet ID cannot be empty"):
            parse_sheet_id("")

    def test_whitespace_only_raises_error(self) -> None:
        """Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="Sheet ID cannot be empty"):
            parse_sheet_id("   ")


class TestIsSheetsUrl:
    """Tests for is_sheets_url function."""

    def test_https_url(self) -> None:
        """HTTPS URLs return True."""
        assert is_sheets_url("https://docs.google.com/spreadsheets/d/abc123") is True

    def test_http_url(self) -> None:
        """HTTP URLs return True."""
        assert is_sheets_url("http://docs.google.com/spreadsheets/d/abc123") is True

    def test_raw_id(self) -> None:
        """Raw sheet IDs return False."""
        assert is_sheets_url("abc123") is False

    def test_url_with_whitespace(self) -> None:
        """URLs with leading whitespace are detected correctly."""
        assert is_sheets_url("  https://example.com") is True

    def test_empty_string(self) -> None:
        """Empty string returns False."""
        assert is_sheets_url("") is False


class TestParseWorksheetGid:
    """Tests for parse_worksheet_gid function."""

    def test_extract_gid_from_url(self) -> None:
        """GID is extracted from URL with #gid= fragment."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=12345"
        assert parse_worksheet_gid(url) == 12345

    def test_extract_gid_zero(self) -> None:
        """GID 0 (default first sheet) is extracted correctly."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=0"
        assert parse_worksheet_gid(url) == 0

    def test_extract_gid_large_number(self) -> None:
        """Large GID values are extracted correctly."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=1234567890"
        assert parse_worksheet_gid(url) == 1234567890

    def test_no_gid_returns_none(self) -> None:
        """URL without #gid= returns None."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit"
        assert parse_worksheet_gid(url) is None

    def test_plain_name_returns_none(self) -> None:
        """Plain worksheet name returns None."""
        assert parse_worksheet_gid("Sheet1") is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None."""
        assert parse_worksheet_gid("") is None

    def test_gid_in_middle_of_url(self) -> None:
        """GID is found even with query params after it."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=999&range=A1"
        assert parse_worksheet_gid(url) == 999


class TestIsWorksheetUrl:
    """Tests for is_worksheet_url function."""

    def test_url_with_gid(self) -> None:
        """URL with #gid= returns True."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=0"
        assert is_worksheet_url(url) is True

    def test_url_without_gid(self) -> None:
        """URL without #gid= returns False."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit"
        assert is_worksheet_url(url) is False

    def test_plain_name(self) -> None:
        """Plain worksheet name returns False."""
        assert is_worksheet_url("Sheet1") is False

    def test_empty_string(self) -> None:
        """Empty string returns False."""
        assert is_worksheet_url("") is False

    def test_url_with_whitespace(self) -> None:
        """URL with leading/trailing whitespace is handled."""
        url = "  https://docs.google.com/spreadsheets/d/abc123/edit#gid=0  "
        assert is_worksheet_url(url) is True

    def test_http_url_with_gid(self) -> None:
        """HTTP URL (not HTTPS) with #gid= returns True."""
        url = "http://docs.google.com/spreadsheets/d/abc123/edit#gid=0"
        assert is_worksheet_url(url) is True


class TestResolveWorksheetNameFromGid:
    """Tests for resolve_worksheet_name_from_gid function."""

    def test_resolve_gid_to_name(self) -> None:
        """GID is resolved to worksheet name."""
        mock_ws1 = MagicMock()
        mock_ws1.id = 0
        mock_ws1.title = "Sheet1"

        mock_ws2 = MagicMock()
        mock_ws2.id = 123
        mock_ws2.title = "Data"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [mock_ws1, mock_ws2]

        assert resolve_worksheet_name_from_gid(mock_spreadsheet, 0) == "Sheet1"
        assert resolve_worksheet_name_from_gid(mock_spreadsheet, 123) == "Data"

    def test_gid_not_found_raises_error(self) -> None:
        """ValueError is raised when GID doesn't exist."""
        mock_ws1 = MagicMock()
        mock_ws1.id = 0
        mock_ws1.title = "Sheet1"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [mock_ws1]

        with pytest.raises(ValueError, match="Worksheet with GID 999 not found"):
            resolve_worksheet_name_from_gid(mock_spreadsheet, 999)

    def test_error_message_lists_available_gids(self) -> None:
        """Error message includes list of available worksheets."""
        mock_ws1 = MagicMock()
        mock_ws1.id = 0
        mock_ws1.title = "Sheet1"

        mock_ws2 = MagicMock()
        mock_ws2.id = 456
        mock_ws2.title = "Reports"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [mock_ws1, mock_ws2]

        with pytest.raises(ValueError) as exc_info:
            resolve_worksheet_name_from_gid(mock_spreadsheet, 999)

        error_msg = str(exc_info.value)
        assert "Sheet1 (gid=0)" in error_msg
        assert "Reports (gid=456)" in error_msg


class TestParseWorksheetIdentifier:
    """Tests for parse_worksheet_identifier function."""

    def test_plain_name_returned_as_is(self) -> None:
        """Plain worksheet name is returned unchanged."""
        assert parse_worksheet_identifier("Sheet1") == "Sheet1"
        assert parse_worksheet_identifier("My Data") == "My Data"

    def test_empty_string_returns_default(self) -> None:
        """Empty string returns Sheet1 default."""
        assert parse_worksheet_identifier("") == "Sheet1"

    def test_whitespace_only_returns_default(self) -> None:
        """Whitespace-only string returns Sheet1 default."""
        assert parse_worksheet_identifier("   ") == "Sheet1"

    def test_url_without_gid_returns_default(self) -> None:
        """URL without #gid= returns Sheet1 default."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit"
        assert parse_worksheet_identifier(url) == "Sheet1"

    def test_url_with_gid_resolves_to_name(self) -> None:
        """URL with #gid= resolves to worksheet name."""
        mock_ws = MagicMock()
        mock_ws.id = 123
        mock_ws.title = "Data"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [mock_ws]

        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=123"
        assert parse_worksheet_identifier(url, spreadsheet=mock_spreadsheet) == "Data"

    def test_url_with_gid_no_spreadsheet_raises_error(self) -> None:
        """URL with GID but no spreadsheet raises ValueError."""
        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=123"
        with pytest.raises(ValueError, match="Cannot resolve worksheet GID"):
            parse_worksheet_identifier(url)

    def test_url_with_invalid_gid_raises_error(self) -> None:
        """URL with GID that doesn't exist raises ValueError."""
        mock_ws = MagicMock()
        mock_ws.id = 0
        mock_ws.title = "Sheet1"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [mock_ws]

        url = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=999"
        with pytest.raises(ValueError, match="Worksheet with GID 999 not found"):
            parse_worksheet_identifier(url, spreadsheet=mock_spreadsheet)

    def test_name_with_whitespace_is_stripped(self) -> None:
        """Leading/trailing whitespace is stripped from names."""
        assert parse_worksheet_identifier("  Sheet1  ") == "Sheet1"


class TestCreateWorksheet:
    """Tests for create_worksheet function."""

    def test_create_worksheet_success(self) -> None:
        """Worksheet is created successfully."""
        mock_worksheet = MagicMock()
        mock_worksheet.title = "NewSheet"
        mock_worksheet.id = 123
        mock_worksheet.row_count = 1000
        mock_worksheet.col_count = 26

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.add_worksheet.return_value = mock_worksheet

        result = create_worksheet(mock_spreadsheet, "NewSheet", rows=1000, cols=26)

        mock_spreadsheet.add_worksheet.assert_called_once_with(title="NewSheet", rows=1000, cols=26)
        assert result.title == "NewSheet"

    def test_create_worksheet_custom_size(self) -> None:
        """Worksheet is created with custom size."""
        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.add_worksheet.return_value = mock_worksheet

        create_worksheet(mock_spreadsheet, "LargeSheet", rows=5000, cols=50)

        mock_spreadsheet.add_worksheet.assert_called_once_with(
            title="LargeSheet", rows=5000, cols=50
        )

    def test_create_worksheet_already_exists_raises_error(self) -> None:
        """SheetsError is raised when worksheet already exists."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 400, "message": "A sheet with the name NewSheet already exists"}
        }

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.add_worksheet.side_effect = gspread.exceptions.APIError(mock_response)

        with pytest.raises(SheetsError) as exc_info:
            create_worksheet(mock_spreadsheet, "NewSheet")

        assert "already exists" in exc_info.value.message

    def test_create_worksheet_api_error_raises_error(self) -> None:
        """SheetsError is raised on other API errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": {"code": 429, "message": "Quota exceeded"}}

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.add_worksheet.side_effect = gspread.exceptions.APIError(mock_response)

        with pytest.raises(SheetsError) as exc_info:
            create_worksheet(mock_spreadsheet, "NewSheet")

        assert "Failed to create worksheet" in exc_info.value.message


class TestDeleteWorksheet:
    """Tests for delete_worksheet function."""

    def test_delete_worksheet_success(self) -> None:
        """Worksheet is deleted successfully."""
        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        result = delete_worksheet(mock_spreadsheet, "OldSheet")

        mock_spreadsheet.worksheet.assert_called_once_with("OldSheet")
        mock_spreadsheet.del_worksheet.assert_called_once_with(mock_worksheet)
        assert result is True

    def test_delete_worksheet_not_found_raises_error(self) -> None:
        """SheetsError is raised when worksheet not found."""
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()

        with pytest.raises(SheetsError) as exc_info:
            delete_worksheet(mock_spreadsheet, "NotFound")

        assert "not found" in exc_info.value.message

    def test_delete_last_worksheet_raises_error(self) -> None:
        """SheetsError is raised when trying to delete last worksheet."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"code": 400, "message": "Cannot delete the last sheet"}
        }

        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_spreadsheet.del_worksheet.side_effect = gspread.exceptions.APIError(mock_response)

        with pytest.raises(SheetsError) as exc_info:
            delete_worksheet(mock_spreadsheet, "LastSheet")

        assert "Cannot delete the last worksheet" in exc_info.value.message


class TestListWorksheets:
    """Tests for list_worksheets function."""

    def test_list_worksheets_success(self) -> None:
        """Worksheets are listed successfully."""
        mock_ws1 = MagicMock()
        mock_ws1.title = "Sheet1"
        mock_ws1.id = 0
        mock_ws1.row_count = 1000
        mock_ws1.col_count = 26

        mock_ws2 = MagicMock()
        mock_ws2.title = "Data"
        mock_ws2.id = 123
        mock_ws2.row_count = 5000
        mock_ws2.col_count = 50

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [mock_ws1, mock_ws2]

        result = list_worksheets(mock_spreadsheet)

        assert len(result) == 2
        assert result[0] == {"title": "Sheet1", "gid": 0, "rows": 1000, "cols": 26}
        assert result[1] == {"title": "Data", "gid": 123, "rows": 5000, "cols": 50}

    def test_list_worksheets_empty(self) -> None:
        """Empty list is returned when no worksheets (unlikely but handled)."""
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = []

        result = list_worksheets(mock_spreadsheet)

        assert result == []


class TestGetOrCreateWorksheet:
    """Tests for get_or_create_worksheet function."""

    def test_get_existing_worksheet(self) -> None:
        """Existing worksheet is returned without creating."""
        mock_worksheet = MagicMock()
        mock_worksheet.title = "Sheet1"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        result = get_or_create_worksheet(mock_spreadsheet, "Sheet1")

        mock_spreadsheet.worksheet.assert_called_once_with("Sheet1")
        mock_spreadsheet.add_worksheet.assert_not_called()
        assert result.title == "Sheet1"

    def test_create_when_missing_and_flag_set(self) -> None:
        """Worksheet is created when missing and create_if_missing=True."""
        mock_new_worksheet = MagicMock()
        mock_new_worksheet.title = "NewSheet"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()
        mock_spreadsheet.add_worksheet.return_value = mock_new_worksheet

        result = get_or_create_worksheet(
            mock_spreadsheet, "NewSheet", create_if_missing=True, rows=500, cols=10
        )

        mock_spreadsheet.add_worksheet.assert_called_once_with(title="NewSheet", rows=500, cols=10)
        assert result.title == "NewSheet"

    def test_raise_when_missing_and_flag_not_set(self) -> None:
        """SheetsError is raised when missing and create_if_missing=False."""
        mock_ws = MagicMock()
        mock_ws.title = "Sheet1"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()
        mock_spreadsheet.worksheets.return_value = [mock_ws]

        with pytest.raises(SheetsError) as exc_info:
            get_or_create_worksheet(mock_spreadsheet, "NotFound", create_if_missing=False)

        assert "not found" in exc_info.value.message
        assert "--create-worksheet" in exc_info.value.message

    def test_hint_includes_available_worksheets(self) -> None:
        """Error message includes list of available worksheets."""
        mock_ws1 = MagicMock()
        mock_ws1.title = "Sheet1"
        mock_ws2 = MagicMock()
        mock_ws2.title = "Data"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "test_sheet_id"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()
        mock_spreadsheet.worksheets.return_value = [mock_ws1, mock_ws2]

        with pytest.raises(SheetsError) as exc_info:
            get_or_create_worksheet(mock_spreadsheet, "NotFound")

        assert "Sheet1" in exc_info.value.message
        assert "Data" in exc_info.value.message
