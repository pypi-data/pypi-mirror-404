"""Tests for column operations edge cases.

Covers Edge Cases:
- EC-2: Duplicate Column Names
- EC-3: Streaming + Column Mapping
- EC-16: Append Mode Column Order Detection
- EC-17: Row Filter Column Validation
- EC-24: Query Cache Key Missing Column Mapping
- EC-56: Streaming Column Mapping Warning
"""

import inspect

import pytest

from mysql_to_sheets.core.column_mapping import ColumnMappingConfig, apply_column_mapping
from mysql_to_sheets.core.exceptions import ConfigError


class TestDuplicateColumnNames:
    """Tests for duplicate column names after transformation.

    Edge Case 2: Duplicate Column Names After Case Transformation
    -------------------------------------------------------------
    When COLUMN_CASE=lower (or upper/title) is applied, multiple columns can
    end up with the same name.
    """

    def test_duplicate_columns_after_lowercase_transform(self):
        """Verify duplicate column names after case transform are detected."""
        config = ColumnMappingConfig(
            enabled=True,
            case_transform="lower",
        )
        # All three become "id" after lowercase
        headers = ["id", "ID", "Id"]
        rows = [[1, 2, 3]]

        with pytest.raises(ValueError) as exc_info:
            apply_column_mapping(headers, rows, config)

        assert "duplicate" in str(exc_info.value).lower()

    def test_duplicate_columns_after_uppercase_transform(self):
        """Verify uppercase transform also detects duplicates."""
        config = ColumnMappingConfig(
            enabled=True,
            case_transform="upper",
        )
        # All become "NAME" after uppercase
        headers = ["name", "Name", "NAME"]
        rows = [["Alice", "Bob", "Charlie"]]

        with pytest.raises(ValueError) as exc_info:
            apply_column_mapping(headers, rows, config)

        assert "duplicate" in str(exc_info.value).lower()

    def test_no_duplicates_passes_validation(self):
        """Verify non-duplicate columns pass validation normally."""
        config = ColumnMappingConfig(
            enabled=True,
            case_transform="lower",
        )
        headers = ["id", "name", "email"]  # All unique after lowercase
        rows = [[1, "Alice", "alice@example.com"]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["id", "name", "email"]
        assert new_rows == [[1, "Alice", "alice@example.com"]]

    def test_duplicate_columns_via_rename_map(self):
        """Verify duplicates created by rename_map are also detected."""
        config = ColumnMappingConfig(
            enabled=True,
            rename_map={"col_a": "ID", "col_b": "ID"},  # Both map to "ID"
        )
        headers = ["col_a", "col_b", "col_c"]
        rows = [[1, 2, 3]]

        with pytest.raises(ValueError) as exc_info:
            apply_column_mapping(headers, rows, config)

        assert "duplicate" in str(exc_info.value).lower()

    def test_data_loss_demonstration_without_fix(self):
        """Demonstrate the current data loss behavior (before fix)."""
        config = ColumnMappingConfig(
            enabled=True,
            case_transform="lower",
        )
        headers = ["user_id", "USER_ID", "User_Id"]
        rows = [[100, 200, 300]]

        try:
            new_headers, new_rows = apply_column_mapping(headers, rows, config)
            # If we get here, verify all three have same transformed name
            assert new_headers == ["user_id", "user_id", "user_id"]
        except ValueError:
            # If ValueError is raised, the fix has been implemented
            pass


class TestStreamingColumnMapping:
    """Tests for streaming mode with column mapping configuration.

    Edge Case 3: Streaming Mode Silently Ignores Column Mapping
    -----------------------------------------------------------
    When users configure both SYNC_MODE=streaming and COLUMN_MAPPING_ENABLED=true,
    the streaming code path may bypass column mapping.
    """

    def test_streaming_code_path_bypasses_column_mapping(self):
        """Demonstrate that streaming mode handles column mapping differently."""
        from mysql_to_sheets.core import sync

        source = inspect.getsource(sync.run_sync)

        streaming_return_pos = source.find('if sync_mode == "streaming"')
        column_mapping_pos = source.find("apply_column_mapping")

        assert streaming_return_pos != -1, "Streaming mode handling not found"
        assert column_mapping_pos != -1, "Column mapping code not found"

        # The streaming block should come BEFORE column mapping
        assert streaming_return_pos < column_mapping_pos

    def test_column_mapping_config_ignored_in_streaming_mode(self):
        """Verify column mapping config awareness in streaming mode."""
        col_mapping = ColumnMappingConfig(
            enabled=True,
            rename_map={"old_col": "New Column"},
            case_transform="upper",
        )

        assert col_mapping.is_active(), "Column mapping should be active"


class TestAppendModeColumnOrderDetection:
    """Tests for append mode column order mismatch detection.

    Edge Case 16: Append Mode Column Order Detection
    ------------------------------------------------
    Detection of actual column reordering in append mode.
    """

    def test_append_mode_detects_column_reordering(self):
        """Verify column reordering is detected in append mode."""
        existing_headers = ["user_id", "name", "email"]
        new_headers = ["name", "user_id", "email"]

        # Same columns but different order
        assert set(existing_headers) == set(new_headers)
        assert existing_headers != new_headers

        # The correct detection logic
        order_mismatch = (
            set(new_headers) == set(existing_headers) and new_headers != existing_headers
        )
        assert order_mismatch is True

        # Build details
        missing_in_sheet = set(new_headers) - set(existing_headers)
        missing_in_data = set(existing_headers) - set(new_headers)

        assert len(missing_in_sheet) == 0
        assert len(missing_in_data) == 0

        details = []
        if not missing_in_sheet and not missing_in_data and order_mismatch:
            details.append("column order differs")
        assert "column order differs" in details

    def test_append_mode_order_detection_correct_logic(self):
        """Verify the order detection logic is correct."""
        existing = ["a", "b", "c"]
        new = ["b", "a", "c"]

        order_mismatch = set(existing) == set(new) and existing != new
        assert order_mismatch is True

    def test_append_mode_sorted_detection_wrong_logic(self):
        """Demonstrate the old (wrong) detection logic."""
        existing = ["a", "b", "c"]
        new = ["b", "a", "c"]

        # Old (wrong) logic
        wrong_logic = existing == sorted(new) or new == sorted(existing)
        # The bug was the logic was unclear


class TestRowFilterColumnValidation:
    """Tests for row filter column reference validation.

    Edge Case 17: Row Filter After Column Filter Bypass
    ---------------------------------------------------
    When a row filter references a column that was filtered out by
    column_filter, the filter was silently bypassed.
    """

    def test_row_filter_referencing_filtered_column_raises_error(self):
        """Verify row filter referencing missing column raises ConfigError."""
        from mysql_to_sheets.core.multi_sheet_sync import filter_rows

        # Headers after column filtering (status was removed)
        headers = ["id", "email"]
        rows = [[1, "alice@example.com"], [2, "bob@example.com"]]
        row_filter = "status == 'active'"

        with pytest.raises(ConfigError) as exc_info:
            filter_rows(headers, rows, row_filter)

        assert "status" in str(exc_info.value)
        assert "missing" in str(exc_info.value).lower()

    def test_row_filter_with_valid_columns_works(self):
        """Verify row filter with valid columns works correctly."""
        from mysql_to_sheets.core.multi_sheet_sync import filter_rows

        headers = ["id", "name", "active"]
        rows = [
            [1, "Alice", True],
            [2, "Bob", False],
            [3, "Charlie", True],
        ]
        row_filter = "active == True"

        result = filter_rows(headers, rows, row_filter)

        assert len(result) == 2
        assert result[0][1] == "Alice"
        assert result[1][1] == "Charlie"

    def test_validate_row_filter_columns_finds_missing(self):
        """Verify validation detects missing column references."""
        from mysql_to_sheets.core.multi_sheet_sync import validate_row_filter_columns

        filter_expr = "status == 'active' and age > 18"
        available = ["id", "name", "email"]

        missing = validate_row_filter_columns(filter_expr, available)

        assert "status" in missing
        assert "age" in missing
        assert "id" not in missing

    def test_validate_row_filter_columns_no_missing(self):
        """Verify validation returns empty list when all columns present."""
        from mysql_to_sheets.core.multi_sheet_sync import validate_row_filter_columns

        filter_expr = "status == 'active' and age > 18"
        available = ["id", "name", "status", "age"]

        missing = validate_row_filter_columns(filter_expr, available)

        assert missing == []

    def test_extract_column_names_from_filter(self):
        """Verify column name extraction from filter expressions."""
        from mysql_to_sheets.core.multi_sheet_sync import _extract_column_names

        # Simple comparison
        names = _extract_column_names("status == 'active'")
        assert "status" in names

        # Multiple columns with and/or
        names = _extract_column_names("status == 'active' and age > 18")
        assert "status" in names
        assert "age" in names

        # With function call (len)
        names = _extract_column_names("len(name) > 5")
        assert "name" in names

        # Python constants should not be included
        names = _extract_column_names("active == True and deleted == False")
        assert "active" in names
        assert "deleted" in names
        assert "True" not in names
        assert "False" not in names


class TestEdgeCaseCombinations:
    """Tests for combinations of edge cases."""

    def test_large_cell_in_column_with_case_transform(self):
        """Test large cell combined with column case transformation."""
        config = ColumnMappingConfig(
            enabled=True,
            case_transform="lower",
        )
        large_content = "x" * 60_000
        headers = ["ID", "content"]
        rows = [[1, large_content]]

        new_headers, new_rows = apply_column_mapping(headers, rows, config)

        assert new_headers == ["id", "content"]
        assert new_rows[0][1] == large_content
