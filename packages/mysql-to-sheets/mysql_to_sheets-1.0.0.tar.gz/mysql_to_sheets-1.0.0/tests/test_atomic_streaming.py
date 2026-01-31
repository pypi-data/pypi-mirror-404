"""Tests for atomic streaming module.

Tests transactional consistency via staging worksheets for large dataset syncs.
"""

import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import ANY, MagicMock, patch

import gspread
import pytest


def _make_mock_response(message: str = "API Error") -> MagicMock:
    """Create a mock Response object for gspread.exceptions.APIError.

    gspread's APIError expects a Response object with .json() and .text attributes.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": {"code": 400, "message": message}}
    mock_response.text = message
    return mock_response


from mysql_to_sheets.core.atomic_streaming import (
    AtomicStreamingConfig,
    AtomicStreamingResult,
    STAGING_NAME_PATTERN,
    _generate_staging_name,
    _parse_staging_timestamp,
    atomic_swap_copy,
    atomic_swap_rename,
    atomic_swap_staging_to_live,
    cleanup_staging_worksheet,
    cleanup_stale_staging_sheets,
    create_staging_worksheet,
    push_chunk_to_staging,
    run_atomic_streaming_sync,
    validate_staging_complete,
)
from mysql_to_sheets.core.exceptions import SheetsError, SyncError


class TestAtomicStreamingConfig:
    """Tests for AtomicStreamingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AtomicStreamingConfig()

        assert config.staging_prefix == "_staging_"
        assert config.cleanup_on_failure is True
        assert config.preserve_gid is False
        assert config.verification_enabled is True
        assert config.max_staging_age_minutes == 60
        # Inherited from StreamingConfig
        assert config.chunk_size == 1000
        assert config.abort_on_failure is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AtomicStreamingConfig(
            staging_prefix="_temp_",
            cleanup_on_failure=False,
            preserve_gid=True,
            verification_enabled=False,
            max_staging_age_minutes=120,
            chunk_size=500,
        )

        assert config.staging_prefix == "_temp_"
        assert config.cleanup_on_failure is False
        assert config.preserve_gid is True
        assert config.verification_enabled is False
        assert config.max_staging_age_minutes == 120
        assert config.chunk_size == 500


class TestAtomicStreamingResult:
    """Tests for AtomicStreamingResult dataclass."""

    def test_default_values(self):
        """Test default result values."""
        result = AtomicStreamingResult()

        assert result.staging_worksheet_name is None
        assert result.swap_successful is False
        assert result.verification_passed is False
        assert result.staging_cleanup_done is False
        assert result.swap_mode == "rename"
        # Inherited
        assert result.total_rows == 0
        assert result.total_chunks == 0
        assert result.success is True  # No failed chunks

    def test_to_dict(self):
        """Test to_dict includes atomic-specific fields."""
        result = AtomicStreamingResult(
            total_rows=1000,
            total_chunks=2,
            successful_chunks=2,
            staging_worksheet_name="_staging_20240115_100000",
            swap_successful=True,
            verification_passed=True,
            swap_mode="copy",
        )

        data = result.to_dict()

        assert data["total_rows"] == 1000
        assert data["staging_worksheet_name"] == "_staging_20240115_100000"
        assert data["swap_successful"] is True
        assert data["verification_passed"] is True
        assert data["swap_mode"] == "copy"


class TestStagingNameGeneration:
    """Tests for staging worksheet name generation."""

    def test_generate_staging_name_format(self):
        """Test staging name has correct format."""
        name = _generate_staging_name()

        assert name.startswith("_staging_")
        # Should match YYYYMMDD_HHMMSS
        assert STAGING_NAME_PATTERN.match(name)

    def test_generate_staging_name_custom_prefix(self):
        """Test staging name with custom prefix."""
        name = _generate_staging_name(prefix="_temp_sync_")

        assert name.startswith("_temp_sync_")

    def test_parse_staging_timestamp_valid(self):
        """Test parsing valid staging timestamp."""
        name = "_staging_20240115_103045"
        timestamp = _parse_staging_timestamp(name)

        assert timestamp is not None
        assert timestamp.year == 2024
        assert timestamp.month == 1
        assert timestamp.day == 15
        assert timestamp.hour == 10
        assert timestamp.minute == 30
        assert timestamp.second == 45

    def test_parse_staging_timestamp_invalid(self):
        """Test parsing invalid staging name returns None."""
        assert _parse_staging_timestamp("Sheet1") is None
        assert _parse_staging_timestamp("_staging_invalid") is None
        assert _parse_staging_timestamp("_staging_20241301_000000") is None  # Invalid date


class TestCreateStagingWorksheet:
    """Tests for create_staging_worksheet function."""

    def test_create_staging_worksheet_success(self):
        """Test successful staging worksheet creation."""
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_spreadsheet.add_worksheet.return_value = mock_worksheet

        worksheet = create_staging_worksheet(mock_spreadsheet, prefix="_staging_")

        mock_spreadsheet.add_worksheet.assert_called_once()
        call_args = mock_spreadsheet.add_worksheet.call_args
        assert call_args.kwargs["title"].startswith("_staging_")
        assert worksheet == mock_worksheet

    def test_create_staging_worksheet_api_error(self):
        """Test staging worksheet creation handles API errors."""
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "sheet123"
        mock_spreadsheet.add_worksheet.side_effect = gspread.exceptions.APIError(
            _make_mock_response("Quota exceeded")
        )

        with pytest.raises(SheetsError) as exc_info:
            create_staging_worksheet(mock_spreadsheet)

        assert "Failed to create staging worksheet" in str(exc_info.value)


class TestCleanupStagingWorksheet:
    """Tests for cleanup_staging_worksheet function."""

    def test_cleanup_success(self):
        """Test successful cleanup."""
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        result = cleanup_staging_worksheet(mock_spreadsheet, "_staging_20240115_100000")

        assert result is True
        mock_spreadsheet.del_worksheet.assert_called_once_with(mock_worksheet)

    def test_cleanup_not_found(self):
        """Test cleanup when worksheet not found."""
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()

        result = cleanup_staging_worksheet(mock_spreadsheet, "_staging_20240115_100000")

        assert result is False

    def test_cleanup_api_error(self):
        """Test cleanup handles API errors gracefully."""
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_spreadsheet.del_worksheet.side_effect = gspread.exceptions.APIError(
            _make_mock_response("Cannot delete")
        )

        result = cleanup_staging_worksheet(mock_spreadsheet, "_staging_20240115_100000")

        assert result is False


class TestCleanupStaleStagingSheets:
    """Tests for cleanup_stale_staging_sheets function."""

    def test_cleanup_old_staging_sheets(self):
        """Test cleanup of old staging sheets."""
        mock_spreadsheet = MagicMock()

        # Create mock worksheets - one old, one new
        old_ws = MagicMock()
        old_ws.title = "_staging_20240101_000000"  # Old
        old_ws.id = 1

        new_ws = MagicMock()
        new_ws.title = "_staging_99991231_235959"  # Far future
        new_ws.id = 2

        regular_ws = MagicMock()
        regular_ws.title = "Sheet1"  # Not a staging sheet
        regular_ws.id = 0

        mock_spreadsheet.worksheets.return_value = [old_ws, new_ws, regular_ws]

        cleaned = cleanup_stale_staging_sheets(mock_spreadsheet, max_age_minutes=60)

        assert cleaned == 1
        mock_spreadsheet.del_worksheet.assert_called_once_with(old_ws)

    def test_cleanup_no_staging_sheets(self):
        """Test cleanup when no staging sheets exist."""
        mock_spreadsheet = MagicMock()
        mock_ws = MagicMock()
        mock_ws.title = "Sheet1"
        mock_spreadsheet.worksheets.return_value = [mock_ws]

        cleaned = cleanup_stale_staging_sheets(mock_spreadsheet)

        assert cleaned == 0
        mock_spreadsheet.del_worksheet.assert_not_called()


class TestPushChunkToStaging:
    """Tests for push_chunk_to_staging function."""

    def test_push_first_chunk(self):
        """Test pushing first chunk writes headers and data."""
        mock_worksheet = MagicMock()
        mock_worksheet.spreadsheet = MagicMock(id="sheet123")
        headers = ["id", "name"]
        rows = [[1, "Alice"], [2, "Bob"]]

        push_chunk_to_staging(mock_worksheet, headers, rows, 0, is_first_chunk=True)

        mock_worksheet.update.assert_called_once()
        call_args = mock_worksheet.update.call_args
        assert call_args.kwargs["values"] == [["id", "name"], [1, "Alice"], [2, "Bob"]]
        assert call_args.kwargs["range_name"] == "A1"

    def test_push_subsequent_chunk(self):
        """Test pushing subsequent chunks appends rows."""
        mock_worksheet = MagicMock()
        mock_worksheet.spreadsheet = MagicMock(id="sheet123")
        headers = ["id", "name"]
        rows = [[3, "Charlie"], [4, "Diana"]]

        push_chunk_to_staging(mock_worksheet, headers, rows, 1, is_first_chunk=False)

        mock_worksheet.append_rows.assert_called_once()
        call_args = mock_worksheet.append_rows.call_args
        assert call_args.kwargs["values"] == [[3, "Charlie"], [4, "Diana"]]

    def test_push_chunk_api_error(self):
        """Test chunk push handles API errors."""
        mock_worksheet = MagicMock()
        mock_worksheet.spreadsheet = MagicMock(id="sheet123")
        mock_worksheet.title = "_staging_test"
        mock_worksheet.update.side_effect = gspread.exceptions.APIError(
            _make_mock_response("Rate limited")
        )

        with pytest.raises(SheetsError) as exc_info:
            push_chunk_to_staging(mock_worksheet, ["id"], [[1]], 0, is_first_chunk=True)

        assert "Failed to push chunk 0 to staging" in str(exc_info.value)


class TestValidateStagingComplete:
    """Tests for validate_staging_complete function."""

    def test_validation_success(self):
        """Test validation passes with correct row count."""
        mock_worksheet = MagicMock()
        mock_worksheet.spreadsheet = MagicMock(id="sheet123")
        # 1 header + 100 data rows = 101 total
        mock_worksheet.get_all_values.return_value = [["header"]] + [[i] for i in range(100)]

        result = validate_staging_complete(mock_worksheet, expected_rows=100)

        assert result is True

    def test_validation_row_mismatch(self):
        """Test validation fails with incorrect row count."""
        mock_worksheet = MagicMock()
        mock_worksheet.spreadsheet = MagicMock(id="sheet123")
        # 1 header + 50 data rows = 51 total (expected 100)
        mock_worksheet.get_all_values.return_value = [["header"]] + [[i] for i in range(50)]

        with pytest.raises(SyncError) as exc_info:
            validate_staging_complete(mock_worksheet, expected_rows=100)

        assert "expected 100 rows, found 50 rows" in str(exc_info.value)


class TestAtomicSwapRename:
    """Tests for atomic_swap_rename function."""

    def test_swap_rename_success(self):
        """Test successful rename swap."""
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_20240115_100000"
        mock_live_ws = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_live_ws

        atomic_swap_rename(mock_spreadsheet, mock_staging_ws, "Sheet1")

        # Should delete live, then rename staging
        mock_spreadsheet.del_worksheet.assert_called_once_with(mock_live_ws)
        mock_staging_ws.update_title.assert_called_once_with("Sheet1")

    def test_swap_rename_no_existing_live(self):
        """Test swap when no existing live worksheet."""
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_20240115_100000"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()

        atomic_swap_rename(mock_spreadsheet, mock_staging_ws, "Sheet1")

        # Should not delete (not found), but should rename
        mock_spreadsheet.del_worksheet.assert_not_called()
        mock_staging_ws.update_title.assert_called_once_with("Sheet1")

    def test_swap_rename_failure(self):
        """Test swap failure when rename fails."""
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.id = "sheet123"
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_20240115_100000"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()
        mock_staging_ws.update_title.side_effect = gspread.exceptions.APIError(
            _make_mock_response("Rename failed")
        )

        with pytest.raises(SheetsError) as exc_info:
            atomic_swap_rename(mock_spreadsheet, mock_staging_ws, "Sheet1")

        assert "Critical: Failed to rename staging" in str(exc_info.value)


class TestAtomicSwapCopy:
    """Tests for atomic_swap_copy function."""

    def test_swap_copy_success(self):
        """Test successful copy swap."""
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_20240115_100000"
        mock_staging_ws.get_all_values.return_value = [["id"], [1], [2]]

        mock_live_ws = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_live_ws

        atomic_swap_copy(mock_spreadsheet, mock_staging_ws, "Sheet1")

        # Should clear live, copy data, then delete staging
        mock_live_ws.clear.assert_called_once()
        mock_live_ws.update.assert_called_once()
        mock_spreadsheet.del_worksheet.assert_called_once_with(mock_staging_ws)

    def test_swap_copy_creates_live_if_missing(self):
        """Test swap creates live worksheet if missing."""
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_20240115_100000"
        mock_staging_ws.get_all_values.return_value = [["id"], [1]]

        mock_live_ws = MagicMock()
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()
        mock_spreadsheet.add_worksheet.return_value = mock_live_ws

        atomic_swap_copy(mock_spreadsheet, mock_staging_ws, "Sheet1")

        mock_spreadsheet.add_worksheet.assert_called_once()
        mock_live_ws.update.assert_called_once()


class TestAtomicSwapStagingToLive:
    """Tests for atomic_swap_staging_to_live function."""

    def test_swap_uses_rename_by_default(self):
        """Test swap uses rename mode by default."""
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_test"
        mock_spreadsheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()

        mode = atomic_swap_staging_to_live(mock_spreadsheet, mock_staging_ws, "Sheet1")

        assert mode == "rename"
        mock_staging_ws.update_title.assert_called_once()

    def test_swap_uses_copy_when_preserve_gid(self):
        """Test swap uses copy mode when preserve_gid=True."""
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_test"
        mock_staging_ws.get_all_values.return_value = [["id"]]

        mock_live_ws = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_live_ws

        mode = atomic_swap_staging_to_live(
            mock_spreadsheet, mock_staging_ws, "Sheet1", preserve_gid=True
        )

        assert mode == "copy"
        mock_live_ws.clear.assert_called_once()


class TestRunAtomicStreamingSync:
    """Tests for run_atomic_streaming_sync function."""

    @patch("mysql_to_sheets.core.atomic_streaming.fetch_data_streaming")
    @patch("mysql_to_sheets.core.sheets_client.get_sheets_client")
    @patch("mysql_to_sheets.core.sync.clean_data")
    @patch("mysql_to_sheets.core.sync.validate_batch_size")
    def test_dry_run_skips_sheets_operations(
        self, mock_validate, mock_clean, mock_client, mock_fetch
    ):
        """Test dry run doesn't create staging or push data."""
        mock_config = MagicMock()
        mock_config.service_account_file = "test.json"
        mock_config.sheets_timeout = 60
        mock_config.google_sheet_id = "sheet123"
        mock_config.google_worksheet_name = "Sheet1"
        mock_config.worksheet_default_rows = 1000
        mock_config.worksheet_default_cols = 26

        mock_fetch.return_value = iter([(["id", "name"], [[1, "Alice"]])])
        mock_clean.return_value = [[1, "Alice"]]

        result = run_atomic_streaming_sync(mock_config, dry_run=True)

        assert result.success is True
        assert result.total_rows == 1
        mock_client.assert_not_called()

    @patch("mysql_to_sheets.core.atomic_streaming.fetch_data_streaming")
    @patch("mysql_to_sheets.core.sheets_client.get_sheets_client")
    @patch("mysql_to_sheets.core.sheets_utils.parse_worksheet_identifier")
    @patch("mysql_to_sheets.core.atomic_streaming.cleanup_stale_staging_sheets")
    @patch("mysql_to_sheets.core.atomic_streaming.create_staging_worksheet")
    @patch("mysql_to_sheets.core.atomic_streaming.push_chunk_to_staging")
    @patch("mysql_to_sheets.core.atomic_streaming.validate_staging_complete")
    @patch("mysql_to_sheets.core.atomic_streaming.atomic_swap_staging_to_live")
    @patch("mysql_to_sheets.core.sync.clean_data")
    @patch("mysql_to_sheets.core.sync.validate_batch_size")
    def test_full_atomic_sync_flow(
        self,
        mock_validate_batch,
        mock_clean,
        mock_swap,
        mock_validate_staging,
        mock_push,
        mock_create_staging,
        mock_cleanup_stale,
        mock_parse_ws,
        mock_client,
        mock_fetch,
    ):
        """Test complete atomic streaming flow."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.service_account_file = "test.json"
        mock_config.sheets_timeout = 60
        mock_config.google_sheet_id = "sheet123"
        mock_config.google_worksheet_name = "Sheet1"
        mock_config.worksheet_default_rows = 1000
        mock_config.worksheet_default_cols = 26

        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_test"

        mock_client.return_value = mock_gc
        mock_gc.open_by_key.return_value = mock_spreadsheet
        mock_parse_ws.return_value = "Sheet1"
        mock_create_staging.return_value = mock_staging_ws
        mock_cleanup_stale.return_value = 0
        mock_validate_staging.return_value = True
        mock_swap.return_value = "rename"

        mock_fetch.return_value = iter(
            [
                (["id", "name"], [[1, "Alice"], [2, "Bob"]]),
                (["id", "name"], [[3, "Charlie"]]),
            ]
        )
        mock_clean.side_effect = lambda rows, log: rows

        # Execute
        atomic_config = AtomicStreamingConfig(chunk_size=2)
        result = run_atomic_streaming_sync(mock_config, atomic_config=atomic_config)

        # Verify
        assert result.success is True
        assert result.total_rows == 3
        assert result.total_chunks == 2
        assert result.swap_successful is True
        assert result.verification_passed is True
        assert result.staging_worksheet_name == "_staging_test"
        mock_swap.assert_called_once()

    @patch("mysql_to_sheets.core.atomic_streaming.fetch_data_streaming")
    @patch("mysql_to_sheets.core.sheets_client.get_sheets_client")
    @patch("mysql_to_sheets.core.sheets_utils.parse_worksheet_identifier")
    @patch("mysql_to_sheets.core.atomic_streaming.cleanup_stale_staging_sheets")
    @patch("mysql_to_sheets.core.atomic_streaming.create_staging_worksheet")
    @patch("mysql_to_sheets.core.atomic_streaming.push_chunk_to_staging")
    @patch("mysql_to_sheets.core.atomic_streaming.cleanup_staging_worksheet")
    @patch("mysql_to_sheets.core.sync.clean_data")
    @patch("mysql_to_sheets.core.sync.validate_batch_size")
    def test_cleanup_on_chunk_failure(
        self,
        mock_validate_batch,
        mock_clean,
        mock_cleanup,
        mock_push,
        mock_create_staging,
        mock_cleanup_stale,
        mock_parse_ws,
        mock_client,
        mock_fetch,
    ):
        """Test staging is cleaned up when chunk push fails."""
        mock_config = MagicMock()
        mock_config.service_account_file = "test.json"
        mock_config.sheets_timeout = 60
        mock_config.google_sheet_id = "sheet123"
        mock_config.google_worksheet_name = "Sheet1"
        mock_config.worksheet_default_rows = 1000
        mock_config.worksheet_default_cols = 26

        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_staging_ws = MagicMock()
        mock_staging_ws.title = "_staging_test"

        mock_client.return_value = mock_gc
        mock_gc.open_by_key.return_value = mock_spreadsheet
        mock_parse_ws.return_value = "Sheet1"
        mock_create_staging.return_value = mock_staging_ws
        mock_cleanup_stale.return_value = 0

        # First chunk succeeds, second fails
        mock_push.side_effect = [None, SheetsError("Push failed", sheet_id="sheet123")]
        mock_fetch.return_value = iter(
            [
                (["id"], [[1]]),
                (["id"], [[2]]),
            ]
        )
        mock_clean.side_effect = lambda rows, log: rows

        atomic_config = AtomicStreamingConfig(cleanup_on_failure=True)

        with pytest.raises(SheetsError):
            run_atomic_streaming_sync(mock_config, atomic_config=atomic_config)

        # Verify cleanup was called (use ANY for logger since it uses module-level logger)
        mock_cleanup.assert_called_once_with(mock_spreadsheet, "_staging_test", ANY)
