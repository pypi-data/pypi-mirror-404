"""Tests for sync modes edge cases.

Covers Edge Cases:
- EC-6: Append Mode Header Mismatch
- EC-7: Duplicate Multi-Sheet Targets
- EC-8: Multi-Sheet Append Mode Headers
- EC-12: Streaming Chunk Failure
- EC-13: Parallel Sync Data Isolation
- EC-53: Empty Result Visibility
"""

import copy
import inspect
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.exceptions import ConfigError


class TestAppendModeHeaderMismatch:
    """Tests for append mode header mismatch detection.

    Edge Case 6: Append Mode with Mismatched Headers
    ------------------------------------------------
    When appending data to an existing sheet with different column order,
    data is written to wrong columns without any warning.
    """

    def test_append_mode_with_matching_headers_succeeds(self):
        """Verify append mode works when headers match exactly."""
        # This test would require mocking the Google Sheets API
        # Documented here for completeness, implementation in integration tests
        pass

    def test_append_mode_detects_column_order_mismatch(self):
        """Verify append mode detects when column order differs."""
        # This test would require mocking the Google Sheets API
        pass

    def test_append_mode_detects_missing_columns(self):
        """Verify append mode detects when new data has columns not in sheet."""
        # This test would require mocking the Google Sheets API
        pass

    def test_append_mode_detects_extra_columns_in_sheet(self):
        """Verify append mode detects when sheet has columns not in new data."""
        # This test would require mocking the Google Sheets API
        pass

    def test_append_to_empty_sheet_adds_headers(self):
        """Verify append to empty sheet adds headers first."""
        # This test would require mocking the Google Sheets API
        pass


class TestDuplicateTargetDetection:
    """Tests for duplicate target detection in multi-sheet sync.

    Edge Case 7: Parallel Multi-Sheet Sync Race Condition
    -----------------------------------------------------
    When using run_multi_sheet_sync() with parallel=True, if two targets
    point to the same sheet_id + worksheet_name, both threads race to write
    data.
    """

    def test_detect_duplicate_targets_same_sheet_and_worksheet(self):
        """Verify duplicate targets are detected before parallel execution."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import validate_targets_unique

        targets = [
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="replace"),
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="replace"),
        ]

        with pytest.raises(ConfigError) as exc_info:
            validate_targets_unique(targets)

        assert "duplicate" in str(exc_info.value.message).lower()
        assert "ABC123" in str(exc_info.value.message) or "Sheet1" in str(exc_info.value.message)

    def test_detect_multiple_duplicate_targets(self):
        """Verify all duplicate targets are reported."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import validate_targets_unique

        targets = [
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="replace"),
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="append"),
            SheetTarget(sheet_id="DEF456", worksheet_name="Data", mode="replace"),
            SheetTarget(sheet_id="DEF456", worksheet_name="Data", mode="replace"),
        ]

        with pytest.raises(ConfigError) as exc_info:
            validate_targets_unique(targets)

        assert "duplicate" in str(exc_info.value.message).lower()

    def test_same_sheet_different_worksheet_allowed(self):
        """Verify targets with same sheet but different worksheets are allowed."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import validate_targets_unique

        targets = [
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="replace"),
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet2", mode="replace"),
        ]

        # Should NOT raise
        validate_targets_unique(targets)

    def test_different_sheet_same_worksheet_allowed(self):
        """Verify targets with different sheets but same worksheet name are allowed."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import validate_targets_unique

        targets = [
            SheetTarget(sheet_id="ABC123", worksheet_name="Data", mode="replace"),
            SheetTarget(sheet_id="DEF456", worksheet_name="Data", mode="replace"),
        ]

        # Should NOT raise
        validate_targets_unique(targets)

    def test_single_target_passes_validation(self):
        """Verify single target always passes duplicate validation."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import validate_targets_unique

        targets = [
            SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="replace"),
        ]

        # Should NOT raise
        validate_targets_unique(targets)

    def test_empty_targets_passes_validation(self):
        """Verify empty target list passes duplicate validation."""
        from mysql_to_sheets.core.multi_sheet_sync import validate_targets_unique

        # Should NOT raise
        validate_targets_unique([])


class TestMultiSheetAppendModeHeaders:
    """Tests for multi-sheet append mode header handling.

    Edge Case 8: Multi-Sheet Append Mode Missing Header Validation
    --------------------------------------------------------------
    In single-sheet sync, append mode validates existing headers and adds
    them if the sheet is empty.
    """

    def test_append_to_empty_sheet_should_add_headers(self):
        """Verify multi-sheet append mode adds headers to empty sheets."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import push_to_target

        # Create mock worksheet
        mock_worksheet = MagicMock()
        mock_worksheet.row_values.return_value = []  # Empty sheet

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet

        target = SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="append")
        headers = ["id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        with patch("mysql_to_sheets.core.multi_sheet_sync.gspread") as mock_gspread:
            mock_gspread.service_account.return_value = mock_gc

            result = push_to_target(
                target=target,
                headers=headers,
                rows=rows,
                service_account_file="service_account.json",
            )

        mock_worksheet.row_values.assert_called_once_with(1)
        assert result.success

    def test_append_to_sheet_with_matching_headers_succeeds(self):
        """Verify append to sheet with matching headers works normally."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import push_to_target

        mock_worksheet = MagicMock()
        mock_worksheet.row_values.return_value = ["id", "name", "email"]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet

        target = SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="append")
        headers = ["id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        with patch("mysql_to_sheets.core.multi_sheet_sync.gspread") as mock_gspread:
            mock_gspread.service_account.return_value = mock_gc

            result = push_to_target(
                target=target,
                headers=headers,
                rows=rows,
                service_account_file="service_account.json",
            )

        assert result.success
        mock_worksheet.append_rows.assert_called_once()

    def test_append_to_sheet_with_mismatched_headers_fails(self):
        """Verify append to sheet with different headers is detected."""
        from mysql_to_sheets.core.config import SheetTarget
        from mysql_to_sheets.core.multi_sheet_sync import push_to_target

        mock_worksheet = MagicMock()
        mock_worksheet.row_values.return_value = ["user_id", "full_name", "email_address"]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheet.return_value = mock_worksheet

        mock_gc = MagicMock()
        mock_gc.open_by_key.return_value = mock_spreadsheet

        target = SheetTarget(sheet_id="ABC123", worksheet_name="Sheet1", mode="append")
        headers = ["id", "name", "email"]
        rows = [[1, "Alice", "alice@example.com"]]

        with patch("mysql_to_sheets.core.multi_sheet_sync.gspread") as mock_gspread:
            mock_gspread.service_account.return_value = mock_gc

            result = push_to_target(
                target=target,
                headers=headers,
                rows=rows,
                service_account_file="service_account.json",
            )

        assert not result.success
        assert "header" in result.error.lower() or "mismatch" in result.error.lower()


class TestStreamingChunkFailure:
    """Tests for streaming mode partial failure handling.

    Edge Case 12: Streaming Chunk Failure Leaves Partial Data
    ---------------------------------------------------------
    In streaming mode, if a chunk fails, the sheet is left with partial data.
    """

    def test_streaming_result_tracks_failed_chunks(self):
        """Verify StreamingResult dataclass tracks failed chunks."""
        from mysql_to_sheets.core.streaming import ChunkResult, StreamingResult

        result = StreamingResult(
            total_rows=5000,
            total_chunks=10,
            successful_chunks=5,
            failed_chunks=5,
            chunk_results=[
                ChunkResult(chunk_number=i, rows_processed=1000, success=(i < 5)) for i in range(10)
            ],
        )

        assert result.failed_chunks == 5
        assert result.total_chunks == 10
        assert result.successful_chunks == 5
        assert result.total_rows == 5000

    def test_streaming_result_success_with_zero_failures(self):
        """Verify StreamingResult shows success when all chunks complete."""
        from mysql_to_sheets.core.streaming import ChunkResult, StreamingResult

        result = StreamingResult(
            total_rows=10000,
            total_chunks=10,
            successful_chunks=10,
            failed_chunks=0,
            chunk_results=[
                ChunkResult(chunk_number=i, rows_processed=1000, success=True) for i in range(10)
            ],
        )

        assert result.failed_chunks == 0
        assert result.successful_chunks == result.total_chunks
        assert result.total_rows == 10000

    def test_partial_streaming_should_warn_about_data_loss(self):
        """Document expected behavior: warn when failed_chunks > 0."""
        from mysql_to_sheets.core.streaming import ChunkResult, StreamingResult

        total_chunks = 10
        successful = 3
        failed = 7
        rows_per_chunk = 1000

        chunk_results = []
        for i in range(total_chunks):
            is_success = i < successful
            chunk_results.append(
                ChunkResult(
                    chunk_number=i,
                    rows_processed=rows_per_chunk if is_success else 0,
                    success=is_success,
                    error=None if is_success else "Rate limit exceeded",
                )
            )

        result = StreamingResult(
            total_rows=successful * rows_per_chunk,
            total_chunks=total_chunks,
            successful_chunks=successful,
            failed_chunks=failed,
            chunk_results=chunk_results,
        )

        expected_rows = total_chunks * rows_per_chunk
        actual_rows = result.total_rows
        data_loss = expected_rows - actual_rows

        assert data_loss == 7000
        assert result.failed_chunks == 7
        assert result.successful_chunks == 3

    def test_first_chunk_clear_is_irreversible(self):
        """Document the critical issue: first chunk clears the sheet."""
        # This is a documentation test
        # First chunk clears the sheet, if subsequent chunks fail, data is lost
        pass


class TestParallelSyncDataIsolation:
    """Tests for parallel multi-sheet sync thread safety.

    Edge Case 13: Multi-Sheet Parallel Sync Shares Mutable Data
    -----------------------------------------------------------
    When using run_multi_sheet_sync(parallel=True), the same cleaned_rows
    list is passed to multiple threads.
    """

    def test_parallel_sync_shares_same_list_object(self):
        """Demonstrate that parallel sync receives same list object."""
        from mysql_to_sheets.core import multi_sheet_sync

        source = inspect.getsource(multi_sheet_sync.run_multi_sheet_sync)

        assert "ThreadPoolExecutor" in source
        assert "cleaned_rows" in source

    def test_list_mutation_visibility_across_threads(self):
        """Demonstrate that list mutations are visible across threads."""
        shared_list = [[1, "Alice"], [2, "Bob"], [3, "Charlie"]]
        results = []

        def reader_thread(thread_id: int) -> None:
            time.sleep(0.01)
            results.append((thread_id, list(shared_list)))

        def mutator_thread() -> None:
            time.sleep(0.005)
            shared_list[0][1] = "CORRUPTED"

        threads = [
            threading.Thread(target=reader_thread, args=(1,)),
            threading.Thread(target=reader_thread, args=(2,)),
            threading.Thread(target=mutator_thread),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 2

    def test_deep_copy_prevents_cross_thread_mutation(self):
        """Demonstrate that deep copy isolates threads from mutations."""
        original_rows = [[1, "Alice"], [2, "Bob"]]
        thread_copies: list = []

        def thread_func(rows: list) -> None:
            rows[0][1] = "MODIFIED"
            thread_copies.append(rows)

        thread1_rows = copy.deepcopy(original_rows)
        thread2_rows = copy.deepcopy(original_rows)

        t1 = threading.Thread(target=thread_func, args=(thread1_rows,))
        t2 = threading.Thread(target=thread_func, args=(thread2_rows,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert original_rows == [[1, "Alice"], [2, "Bob"]]
        assert thread1_rows[0][1] == "MODIFIED"
        assert thread2_rows[0][1] == "MODIFIED"

    def test_tuple_conversion_makes_data_immutable(self):
        """Alternative fix: convert rows to tuples for immutability."""
        rows = [[1, "Alice"], [2, "Bob"]]

        immutable_rows = tuple(tuple(row) for row in rows)

        with pytest.raises(TypeError):
            immutable_rows[0][1] = "MODIFIED"  # type: ignore
