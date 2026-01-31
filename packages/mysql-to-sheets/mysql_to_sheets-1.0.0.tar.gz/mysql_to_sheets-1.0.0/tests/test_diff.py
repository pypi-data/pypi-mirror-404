"""Tests for diff and preview functionality."""

from unittest.mock import MagicMock, patch

import gspread.exceptions
import pytest

from mysql_to_sheets.core.diff import (
    DiffResult,
    HeaderChange,
    RowChange,
    _normalize_row,
    _normalize_value,
    compute_diff,
    compute_header_changes,
    fetch_sheet_data,
    run_preview,
)
from mysql_to_sheets.core.exceptions import SheetsError


class TestNormalizeValue:
    """Tests for _normalize_value function."""

    def test_none_to_empty_string(self):
        """Test None converts to empty string."""
        assert _normalize_value(None) == ""

    def test_bool_to_uppercase_string(self):
        """Test booleans convert to uppercase strings."""
        assert _normalize_value(True) == "TRUE"
        assert _normalize_value(False) == "FALSE"

    def test_float_precision(self):
        """Test floats use appropriate precision."""
        # Uses .10g format which may round
        assert _normalize_value(3.14159265359) == "3.141592654"
        assert _normalize_value(0.0) == "0"
        assert _normalize_value(1000000.0) == "1000000"

    def test_string_strip(self):
        """Test strings are stripped."""
        assert _normalize_value("  hello  ") == "hello"
        assert _normalize_value("world") == "world"

    def test_integer(self):
        """Test integers convert to strings."""
        assert _normalize_value(42) == "42"
        assert _normalize_value(0) == "0"


class TestNormalizeRow:
    """Tests for _normalize_row function."""

    def test_empty_row(self):
        """Test empty row returns empty tuple."""
        assert _normalize_row([]) == ()

    def test_mixed_types(self):
        """Test row with mixed types."""
        row = [1, "hello", None, True, 3.14]
        result = _normalize_row(row)
        assert result == ("1", "hello", "", "TRUE", "3.14")

    def test_returns_tuple(self):
        """Test result is a tuple (hashable for sets)."""
        result = _normalize_row([1, 2, 3])
        assert isinstance(result, tuple)


class TestHeaderChange:
    """Tests for HeaderChange dataclass."""

    def test_default_values(self):
        """Test default values."""
        change = HeaderChange()
        assert change.added == []
        assert change.removed == []
        assert change.reordered is False

    def test_with_changes(self):
        """Test with actual changes."""
        change = HeaderChange(
            added=["new_col"],
            removed=["old_col"],
            reordered=True,
        )
        assert change.added == ["new_col"]
        assert change.removed == ["old_col"]
        assert change.reordered is True


class TestRowChange:
    """Tests for RowChange dataclass."""

    def test_add_change(self):
        """Test add change type."""
        change = RowChange(
            change_type="add",
            row_index=0,
            new_values=[1, "Alice", "alice@example.com"],
        )
        assert change.change_type == "add"
        assert change.row_index == 0
        assert change.new_values == [1, "Alice", "alice@example.com"]
        assert change.old_values == []

    def test_remove_change(self):
        """Test remove change type."""
        change = RowChange(
            change_type="remove",
            row_index=5,
            old_values=[2, "Bob", "bob@example.com"],
        )
        assert change.change_type == "remove"
        assert change.row_index == 5
        assert change.old_values == [2, "Bob", "bob@example.com"]
        assert change.new_values == []


class TestDiffResult:
    """Tests for DiffResult dataclass."""

    def test_default_values(self):
        """Test default values."""
        result = DiffResult()
        assert result.has_changes is False
        assert result.sheet_row_count == 0
        assert result.query_row_count == 0
        assert result.rows_to_add == 0
        assert result.rows_to_remove == 0
        assert result.rows_to_modify == 0
        assert result.rows_unchanged == 0
        assert isinstance(result.header_changes, HeaderChange)
        assert result.sample_changes == []
        assert result.message == ""

    def test_summary_no_changes(self):
        """Test summary with no changes."""
        result = DiffResult()
        assert result.summary() == "No changes"

    def test_summary_rows_to_add(self):
        """Test summary with rows to add."""
        result = DiffResult(rows_to_add=50)
        assert result.summary() == "+50 rows"

    def test_summary_rows_to_remove(self):
        """Test summary with rows to remove."""
        result = DiffResult(rows_to_remove=10)
        assert result.summary() == "-10 rows"

    def test_summary_rows_to_modify(self):
        """Test summary with rows to modify."""
        result = DiffResult(rows_to_modify=5)
        assert result.summary() == "~5 modified"

    def test_summary_header_changes(self):
        """Test summary with header changes."""
        result = DiffResult(
            header_changes=HeaderChange(
                added=["col1", "col2"],
                removed=["old_col"],
                reordered=True,
            )
        )
        summary = result.summary()
        assert "+2 columns" in summary
        assert "-1 columns" in summary
        assert "columns reordered" in summary

    def test_summary_combined(self):
        """Test summary with multiple changes."""
        result = DiffResult(
            rows_to_add=50,
            rows_to_remove=10,
            rows_to_modify=5,
        )
        summary = result.summary()
        assert "+50 rows" in summary
        assert "-10 rows" in summary
        assert "~5 modified" in summary

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = DiffResult(
            has_changes=True,
            sheet_row_count=100,
            query_row_count=150,
            rows_to_add=50,
            message="Test message",
        )
        d = result.to_dict()

        assert d["has_changes"] is True
        assert d["sheet_row_count"] == 100
        assert d["query_row_count"] == 150
        assert d["rows_to_add"] == 50
        assert d["message"] == "Test message"
        assert "header_changes" in d
        assert "sample_changes" in d
        assert "summary" in d

    def test_to_dict_with_sample_changes(self):
        """Test to_dict includes sample changes."""
        result = DiffResult(
            sample_changes=[
                RowChange(change_type="add", row_index=0, new_values=[1, 2]),
                RowChange(change_type="remove", row_index=1, old_values=[3, 4]),
            ]
        )
        d = result.to_dict()

        assert len(d["sample_changes"]) == 2
        assert d["sample_changes"][0]["change_type"] == "add"
        assert d["sample_changes"][1]["change_type"] == "remove"


class TestComputeHeaderChanges:
    """Tests for compute_header_changes function."""

    def test_no_changes(self):
        """Test with identical headers."""
        result = compute_header_changes(["a", "b", "c"], ["a", "b", "c"])
        assert result.added == []
        assert result.removed == []
        assert result.reordered is False

    def test_added_columns(self):
        """Test with added columns."""
        result = compute_header_changes(["a", "b"], ["a", "b", "c", "d"])
        assert result.added == ["c", "d"]
        assert result.removed == []

    def test_removed_columns(self):
        """Test with removed columns."""
        result = compute_header_changes(["a", "b", "c"], ["a"])
        assert result.added == []
        assert result.removed == ["b", "c"]

    def test_reordered_columns(self):
        """Test with reordered columns."""
        result = compute_header_changes(["a", "b", "c"], ["c", "b", "a"])
        assert result.added == []
        assert result.removed == []
        assert result.reordered is True

    def test_combined_changes(self):
        """Test with added, removed, and reordered."""
        result = compute_header_changes(["a", "b", "c"], ["c", "a", "d"])
        assert result.added == ["d"]
        assert result.removed == ["b"]
        assert result.reordered is True

    def test_empty_sheets(self):
        """Test with empty sheet headers."""
        result = compute_header_changes([], ["a", "b"])
        assert result.added == ["a", "b"]
        assert result.removed == []

    def test_empty_query(self):
        """Test with empty query headers."""
        result = compute_header_changes(["a", "b"], [])
        assert result.added == []
        assert result.removed == ["a", "b"]


class TestComputeDiff:
    """Tests for compute_diff function."""

    def test_no_changes(self):
        """Test with identical data."""
        headers = ["id", "name"]
        rows = [[1, "Alice"], [2, "Bob"]]

        result = compute_diff(headers, rows, headers, rows)

        assert result.has_changes is False
        assert result.rows_to_add == 0
        assert result.rows_to_remove == 0
        assert result.rows_unchanged == 2

    def test_rows_to_add(self):
        """Test with new rows in query."""
        query_headers = ["id", "name"]
        query_rows = [[1, "Alice"], [2, "Bob"], [3, "Charlie"]]
        sheet_headers = ["id", "name"]
        sheet_rows = [[1, "Alice"]]

        result = compute_diff(query_headers, query_rows, sheet_headers, sheet_rows)

        assert result.has_changes is True
        assert result.rows_to_add == 2
        assert result.rows_to_remove == 0
        assert result.rows_unchanged == 1

    def test_rows_to_remove(self):
        """Test with rows missing from query."""
        query_headers = ["id", "name"]
        query_rows = [[1, "Alice"]]
        sheet_headers = ["id", "name"]
        sheet_rows = [[1, "Alice"], [2, "Bob"], [3, "Charlie"]]

        result = compute_diff(query_headers, query_rows, sheet_headers, sheet_rows)

        assert result.has_changes is True
        assert result.rows_to_add == 0
        assert result.rows_to_remove == 2
        assert result.rows_unchanged == 1

    def test_complete_replacement(self):
        """Test complete data replacement."""
        query_headers = ["id", "name"]
        query_rows = [[10, "New1"], [20, "New2"]]
        sheet_headers = ["id", "name"]
        sheet_rows = [[1, "Old1"], [2, "Old2"]]

        result = compute_diff(query_headers, query_rows, sheet_headers, sheet_rows)

        assert result.has_changes is True
        assert result.rows_to_add == 2
        assert result.rows_to_remove == 2
        assert result.rows_unchanged == 0

    def test_header_changes_triggers_has_changes(self):
        """Test that header changes alone trigger has_changes."""
        query_headers = ["id", "name", "email"]
        query_rows = [[1, "Alice", "alice@example.com"]]
        sheet_headers = ["id", "name"]
        sheet_rows = [[1, "Alice"]]

        result = compute_diff(query_headers, query_rows, sheet_headers, sheet_rows)

        assert result.has_changes is True
        assert result.header_changes.added == ["email"]

    def test_sample_changes_limit(self):
        """Test that sample changes are limited."""
        query_headers = ["id"]
        query_rows = [[i] for i in range(20)]
        sheet_headers = ["id"]
        sheet_rows = []

        result = compute_diff(
            query_headers,
            query_rows,
            sheet_headers,
            sheet_rows,
            max_sample_changes=6,
        )

        # Should have at most 6 total samples (3 add + 3 remove max)
        assert len(result.sample_changes) <= 6

    def test_empty_sheet(self):
        """Test diff against empty sheet."""
        query_headers = ["id", "name"]
        query_rows = [[1, "Alice"], [2, "Bob"]]
        sheet_headers = []
        sheet_rows = []

        result = compute_diff(query_headers, query_rows, sheet_headers, sheet_rows)

        assert result.has_changes is True
        assert result.rows_to_add == 2
        assert result.sheet_row_count == 0
        assert result.query_row_count == 2

    def test_row_counts(self):
        """Test row count tracking."""
        query_rows = [[1], [2], [3]]
        sheet_rows = [[1], [4], [5], [6]]

        result = compute_diff(
            ["id"],
            query_rows,
            ["id"],
            sheet_rows,
        )

        assert result.sheet_row_count == 4
        assert result.query_row_count == 3


class TestFetchSheetData:
    """Tests for fetch_sheet_data function."""

    @patch("mysql_to_sheets.core.diff.gspread")
    def test_fetch_success(self, mock_gspread):
        """Test successful sheet data fetch."""
        # Setup mocks
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [
            ["id", "name", "email"],
            ["1", "Alice", "alice@example.com"],
            ["2", "Bob", "bob@example.com"],
        ]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet

        mock_gspread.service_account.return_value = mock_gc

        # Create config
        config = MagicMock()
        config.service_account_file = "test.json"
        config.google_sheet_id = "sheet123"
        config.google_worksheet_name = "Sheet1"

        # Execute
        headers, rows = fetch_sheet_data(config)

        # Verify
        assert headers == ["id", "name", "email"]
        assert len(rows) == 2
        assert rows[0] == ["1", "Alice", "alice@example.com"]

    @patch("mysql_to_sheets.core.diff.gspread")
    def test_fetch_empty_sheet(self, mock_gspread):
        """Test fetching from empty sheet."""
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = []

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet

        mock_gspread.service_account.return_value = mock_gc

        config = MagicMock()
        config.service_account_file = "test.json"
        config.google_sheet_id = "sheet123"
        config.google_worksheet_name = "Sheet1"

        headers, rows = fetch_sheet_data(config)

        assert headers == []
        assert rows == []

    @patch("mysql_to_sheets.core.diff.gspread")
    def test_fetch_spreadsheet_not_found(self, mock_gspread):
        """Test error when spreadsheet not found."""
        mock_gc = MagicMock()
        mock_gc.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound()

        mock_gspread.service_account.return_value = mock_gc
        # Make sure the mock module has the exceptions attribute for isinstance checks
        mock_gspread.exceptions = gspread.exceptions

        config = MagicMock()
        config.service_account_file = "test.json"
        config.google_sheet_id = "invalid_id"
        config.google_worksheet_name = "Sheet1"

        with pytest.raises(SheetsError) as exc_info:
            fetch_sheet_data(config)

        assert "not found" in exc_info.value.message.lower()

    @patch("mysql_to_sheets.core.diff.gspread")
    def test_fetch_worksheet_not_found(self, mock_gspread):
        """Test error when worksheet not found."""
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()

        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet

        mock_gspread.service_account.return_value = mock_gc
        # Make sure the mock module has the exceptions attribute for isinstance checks
        mock_gspread.exceptions = gspread.exceptions

        config = MagicMock()
        config.service_account_file = "test.json"
        config.google_sheet_id = "sheet123"
        config.google_worksheet_name = "InvalidSheet"

        with pytest.raises(SheetsError) as exc_info:
            fetch_sheet_data(config)

        assert "not found" in exc_info.value.message.lower()


class TestRunPreview:
    """Tests for run_preview function."""

    @patch("mysql_to_sheets.core.diff.fetch_sheet_data")
    def test_run_preview_with_changes(self, mock_fetch):
        """Test preview with changes detected."""
        mock_fetch.return_value = (
            ["id", "name"],
            [["1", "Alice"]],
        )

        config = MagicMock()
        query_headers = ["id", "name"]
        query_rows = [[1, "Alice"], [2, "Bob"]]

        result = run_preview(config, query_headers, query_rows)

        assert result.has_changes is True
        assert result.rows_to_add == 1
        assert result.rows_unchanged == 1
        assert "1" in result.summary() or "row" in result.summary()

    @patch("mysql_to_sheets.core.diff.fetch_sheet_data")
    def test_run_preview_no_changes(self, mock_fetch):
        """Test preview with no changes."""
        mock_fetch.return_value = (
            ["id", "name"],
            [["1", "Alice"], ["2", "Bob"]],
        )

        config = MagicMock()
        query_headers = ["id", "name"]
        query_rows = [["1", "Alice"], ["2", "Bob"]]

        result = run_preview(config, query_headers, query_rows)

        assert result.has_changes is False
        assert result.summary() == "No changes"

    @patch("mysql_to_sheets.core.diff.fetch_sheet_data")
    def test_run_preview_with_logger(self, mock_fetch):
        """Test preview logs progress."""
        mock_fetch.return_value = (["id"], [["1"]])

        config = MagicMock()
        logger = MagicMock()

        run_preview(config, ["id"], [[1]], logger)

        # Should log at least start and completion
        assert logger.info.called

    @patch("mysql_to_sheets.core.diff.fetch_sheet_data")
    def test_run_preview_empty_sheet(self, mock_fetch):
        """Test preview against empty sheet."""
        mock_fetch.return_value = ([], [])

        config = MagicMock()
        query_headers = ["id", "name"]
        query_rows = [[1, "Alice"], [2, "Bob"]]

        result = run_preview(config, query_headers, query_rows)

        assert result.has_changes is True
        assert result.rows_to_add == 2
        assert result.sheet_row_count == 0
