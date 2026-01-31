"""Tests for the multi_sheet_sync module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mysql_to_sheets.core.config import Config, SheetTarget
from mysql_to_sheets.core.multi_sheet_sync import (
    MultiSheetSyncResult,
    MultiSheetSyncService,
    TargetSyncResult,
    evaluate_row_filter,
    filter_columns,
    filter_rows,
    push_to_target,
    run_multi_sheet_sync,
)


class TestSheetTarget:
    """Tests for SheetTarget dataclass."""

    def test_default_values(self):
        """Test default target values."""
        target = SheetTarget(sheet_id="abc123")

        assert target.sheet_id == "abc123"
        assert target.worksheet_name == "Sheet1"
        assert target.column_filter is None
        assert target.row_filter is None
        assert target.mode == "replace"

    def test_custom_values(self):
        """Test custom target values."""
        target = SheetTarget(
            sheet_id="abc123",
            worksheet_name="Active Users",
            column_filter=["name", "email"],
            row_filter="status == 'active'",
            mode="append",
        )

        assert target.sheet_id == "abc123"
        assert target.worksheet_name == "Active Users"
        assert target.column_filter == ["name", "email"]
        assert target.row_filter == "status == 'active'"
        assert target.mode == "append"

    def test_to_dict(self):
        """Test converting target to dictionary."""
        target = SheetTarget(
            sheet_id="abc123",
            worksheet_name="Data",
            column_filter=["a", "b"],
        )

        d = target.to_dict()

        assert d["sheet_id"] == "abc123"
        assert d["worksheet_name"] == "Data"
        assert d["column_filter"] == ["a", "b"]
        assert d["row_filter"] is None
        assert d["mode"] == "replace"

    def test_from_dict(self):
        """Test creating target from dictionary."""
        data = {
            "sheet_id": "xyz789",
            "worksheet_name": "Orders",
            "column_filter": ["id", "total"],
            "mode": "append",
        }

        target = SheetTarget.from_dict(data)

        assert target.sheet_id == "xyz789"
        assert target.worksheet_name == "Orders"
        assert target.column_filter == ["id", "total"]
        assert target.mode == "append"


class TestTargetSyncResult:
    """Tests for TargetSyncResult dataclass."""

    def test_default_values(self):
        """Test default result values."""
        target = SheetTarget(sheet_id="abc123")
        result = TargetSyncResult(target=target, success=True)

        assert result.target == target
        assert result.success is True
        assert result.rows_synced == 0
        assert result.message == ""
        assert result.error is None

    def test_to_dict(self):
        """Test converting result to dictionary."""
        target = SheetTarget(sheet_id="abc123")
        result = TargetSyncResult(
            target=target,
            success=True,
            rows_synced=100,
            message="Success",
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["rows_synced"] == 100
        assert d["message"] == "Success"
        assert d["target"]["sheet_id"] == "abc123"


class TestMultiSheetSyncResult:
    """Tests for MultiSheetSyncResult dataclass."""

    def test_default_values(self):
        """Test default result values."""
        result = MultiSheetSyncResult(success=True)

        assert result.success is True
        assert result.total_rows_fetched == 0
        assert result.target_results == []
        assert result.message == ""
        assert result.error is None

    def test_to_dict(self):
        """Test converting result to dictionary."""
        target = SheetTarget(sheet_id="abc123")
        target_result = TargetSyncResult(
            target=target,
            success=True,
            rows_synced=50,
        )

        result = MultiSheetSyncResult(
            success=True,
            total_rows_fetched=100,
            target_results=[target_result],
            message="All synced",
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["total_rows_fetched"] == 100
        assert d["targets_succeeded"] == 1
        assert d["targets_failed"] == 0
        assert len(d["target_results"]) == 1


class TestFilterColumns:
    """Tests for filter_columns function."""

    def test_filter_subset(self):
        """Test filtering to subset of columns."""
        headers = ["id", "name", "email", "age"]
        rows = [
            [1, "Alice", "alice@example.com", 30],
            [2, "Bob", "bob@example.com", 25],
        ]

        filtered_headers, filtered_rows = filter_columns(headers, rows, ["name", "email"])

        assert filtered_headers == ["name", "email"]
        assert filtered_rows[0] == ["Alice", "alice@example.com"]
        assert filtered_rows[1] == ["Bob", "bob@example.com"]

    def test_filter_single_column(self):
        """Test filtering to single column."""
        headers = ["a", "b", "c"]
        rows = [[1, 2, 3]]

        filtered_headers, filtered_rows = filter_columns(headers, rows, ["b"])

        assert filtered_headers == ["b"]
        assert filtered_rows[0] == [2]

    def test_filter_nonexistent_column(self):
        """Test filtering with nonexistent column (ignored)."""
        headers = ["a", "b"]
        rows = [[1, 2]]

        filtered_headers, filtered_rows = filter_columns(headers, rows, ["a", "nonexistent"])

        assert filtered_headers == ["a"]
        assert filtered_rows[0] == [1]


class TestEvaluateRowFilter:
    """Tests for evaluate_row_filter function."""

    def test_equality_filter(self):
        """Test equality filter."""
        headers = ["name", "status"]
        row = ["Alice", "active"]

        assert evaluate_row_filter(row, headers, "status == 'active'") is True
        assert evaluate_row_filter(row, headers, "status == 'inactive'") is False

    def test_inequality_filter(self):
        """Test inequality filter."""
        headers = ["name", "status"]
        row = ["Alice", "active"]

        assert evaluate_row_filter(row, headers, "status != 'inactive'") is True
        assert evaluate_row_filter(row, headers, "status != 'active'") is False

    def test_numeric_comparison(self):
        """Test numeric comparison filter."""
        headers = ["name", "age"]
        row = ["Alice", 30]

        assert evaluate_row_filter(row, headers, "age > 25") is True
        assert evaluate_row_filter(row, headers, "age < 25") is False
        assert evaluate_row_filter(row, headers, "age >= 30") is True

    def test_empty_filter(self):
        """Test empty filter (always passes)."""
        headers = ["name"]
        row = ["Alice"]

        assert evaluate_row_filter(row, headers, "") is True
        assert evaluate_row_filter(row, headers, None) is True

    def test_invalid_filter(self):
        """Test invalid filter (defaults to passing)."""
        headers = ["name"]
        row = ["Alice"]

        # Invalid syntax should not crash, defaults to True
        assert evaluate_row_filter(row, headers, "invalid syntax +++") is True


class TestFilterRows:
    """Tests for filter_rows function."""

    def test_filter_by_status(self):
        """Test filtering rows by status."""
        headers = ["name", "status"]
        rows = [
            ["Alice", "active"],
            ["Bob", "inactive"],
            ["Charlie", "active"],
        ]

        filtered = filter_rows(headers, rows, "status == 'active'")

        assert len(filtered) == 2
        assert filtered[0][0] == "Alice"
        assert filtered[1][0] == "Charlie"

    def test_filter_by_number(self):
        """Test filtering rows by numeric value."""
        headers = ["name", "age"]
        rows = [
            ["Alice", 30],
            ["Bob", 20],
            ["Charlie", 35],
        ]

        filtered = filter_rows(headers, rows, "age >= 25")

        assert len(filtered) == 2
        assert filtered[0][0] == "Alice"
        assert filtered[1][0] == "Charlie"

    def test_empty_filter(self):
        """Test empty filter (returns all rows)."""
        headers = ["name"]
        rows = [["Alice"], ["Bob"]]

        filtered = filter_rows(headers, rows, "")

        assert len(filtered) == 2


class TestPushToTarget:
    """Tests for push_to_target function."""

    @patch("mysql_to_sheets.core.multi_sheet_sync.gspread")
    def test_successful_push(self, mock_gspread):
        """Test successful push to target."""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()

        mock_gspread.service_account.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        target = SheetTarget(sheet_id="abc123", worksheet_name="Data")
        headers = ["name", "age"]
        rows = [["Alice", 30], ["Bob", 25]]

        result = push_to_target(target, headers, rows, "./service_account.json")

        assert result.success is True
        assert result.rows_synced == 2
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once()

    @patch("mysql_to_sheets.core.multi_sheet_sync.gspread")
    def test_push_with_column_filter(self, mock_gspread):
        """Test push with column filtering."""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()

        mock_gspread.service_account.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        target = SheetTarget(
            sheet_id="abc123",
            column_filter=["name"],
        )
        headers = ["name", "age"]
        rows = [["Alice", 30], ["Bob", 25]]

        result = push_to_target(target, headers, rows, "./service_account.json")

        assert result.success is True
        assert result.rows_synced == 2

    @patch("mysql_to_sheets.core.multi_sheet_sync.gspread")
    def test_push_append_mode(self, mock_gspread):
        """Test push in append mode."""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        # Set up row_values to return matching headers for append mode validation
        mock_worksheet.row_values.return_value = ["name"]

        mock_gspread.service_account.return_value = mock_client
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        target = SheetTarget(sheet_id="abc123", mode="append")
        headers = ["name"]
        rows = [["Alice"]]

        result = push_to_target(target, headers, rows, "./service_account.json")

        assert result.success is True
        mock_worksheet.clear.assert_not_called()
        mock_worksheet.append_rows.assert_called_once()

    @patch("mysql_to_sheets.core.multi_sheet_sync.gspread")
    def test_push_spreadsheet_not_found(self, mock_gspread):
        """Test push when spreadsheet not found."""
        import gspread.exceptions

        mock_client = MagicMock()
        mock_gspread.service_account.return_value = mock_client
        # Use the real exception class for side_effect
        mock_gspread.exceptions = gspread.exceptions
        mock_client.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound()

        target = SheetTarget(sheet_id="invalid")
        headers = ["name"]
        rows = [["Alice"]]

        result = push_to_target(target, headers, rows, "./service_account.json")

        assert result.success is False
        assert "not found" in result.error.lower()


class TestRunMultiSheetSync:
    """Tests for run_multi_sheet_sync function."""

    @patch("mysql_to_sheets.core.multi_sheet_sync.fetch_data")
    @patch("mysql_to_sheets.core.multi_sheet_sync.push_to_target")
    def test_successful_sync(self, mock_push, mock_fetch):
        """Test successful multi-sheet sync."""
        mock_fetch.return_value = (
            ["id", "name"],
            [[1, "Alice"], [2, "Bob"]],
        )
        mock_push.return_value = TargetSyncResult(
            target=SheetTarget(sheet_id="abc"),
            success=True,
            rows_synced=2,
        )

        config = Mock(spec=Config)
        config.db_type = "mysql"
        config.service_account_file = "./sa.json"
        config.column_mapping_enabled = False
        config.column_mapping = {}
        config.column_order = None
        config.column_case = "none"
        config.column_strip_prefix = None
        config.column_strip_suffix = None
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        targets = [
            SheetTarget(sheet_id="abc123"),
            SheetTarget(sheet_id="def456"),
        ]

        result = run_multi_sheet_sync(config=config, targets=targets)

        assert result.success is True
        assert result.total_rows_fetched == 2
        assert len(result.target_results) == 2

    @patch("mysql_to_sheets.core.multi_sheet_sync.fetch_data")
    def test_dry_run(self, mock_fetch):
        """Test dry run mode."""
        mock_fetch.return_value = (
            ["id", "name"],
            [[1, "Alice"], [2, "Bob"]],
        )

        config = Mock(spec=Config)
        config.db_type = "mysql"
        config.column_mapping_enabled = False
        config.column_mapping = {}
        config.column_order = None
        config.column_case = "none"
        config.column_strip_prefix = None
        config.column_strip_suffix = None
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        targets = [SheetTarget(sheet_id="abc123")]

        result = run_multi_sheet_sync(
            config=config,
            targets=targets,
            dry_run=True,
        )

        assert result.success is True
        assert "Dry run" in result.message

    @patch("mysql_to_sheets.core.multi_sheet_sync.fetch_data")
    def test_empty_data(self, mock_fetch):
        """Test sync with empty data."""
        mock_fetch.return_value = ([], [])

        config = Mock(spec=Config)
        config.db_type = "mysql"
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        targets = [SheetTarget(sheet_id="abc123")]

        result = run_multi_sheet_sync(config=config, targets=targets)

        assert result.success is True
        assert result.total_rows_fetched == 0

    def test_no_targets(self):
        """Test sync with no targets."""
        from mysql_to_sheets.core.exceptions import ConfigError

        config = Mock(spec=Config)
        config.multi_sheet_targets = []
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        with pytest.raises(ConfigError, match="No sheet targets"):
            run_multi_sheet_sync(config=config, targets=[])


class TestMultiSheetSyncService:
    """Tests for MultiSheetSyncService class."""

    @patch("mysql_to_sheets.core.multi_sheet_sync.run_multi_sheet_sync")
    def test_sync_method(self, mock_run):
        """Test sync method."""
        mock_run.return_value = MultiSheetSyncResult(success=True)

        config = Mock(spec=Config)
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        service = MultiSheetSyncService(config=config)
        targets = [SheetTarget(sheet_id="abc123")]

        result = service.sync(targets)

        assert result.success is True
        mock_run.assert_called_once()

    @patch("mysql_to_sheets.core.multi_sheet_sync.run_multi_sheet_sync")
    def test_sync_from_config(self, mock_run):
        """Test sync_from_config method."""
        mock_run.return_value = MultiSheetSyncResult(success=True)

        config = Mock(spec=Config)
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5
        config.multi_sheet_targets = [SheetTarget(sheet_id="abc")]
        config.multi_sheet_parallel = True

        service = MultiSheetSyncService(config=config)
        result = service.sync_from_config()

        assert result.success is True
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["parallel"] is True
