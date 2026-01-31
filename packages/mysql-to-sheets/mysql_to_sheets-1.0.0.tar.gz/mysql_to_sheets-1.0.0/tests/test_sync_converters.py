"""Tests for SyncResult converters.

This module tests the centralized SyncResultConverter and convenience
functions that eliminate duplicated response marshalling code.
"""

import pytest
from dataclasses import dataclass, field
from typing import Any

from mysql_to_sheets.core.sync.converters import (
    SyncResultConverter,
    diff_result_to_dict,
    schema_changes_to_dict,
    sync_result_to_api_response,
    sync_result_to_dict,
    sync_result_to_web_dict,
)
from mysql_to_sheets.core.sync.dataclasses import SyncResult
from mysql_to_sheets.core.diff import DiffResult, HeaderChange


class TestDiffResultToDict:
    """Tests for diff_result_to_dict function."""

    def test_returns_none_for_none_input(self):
        """Verify None input returns None output."""
        assert diff_result_to_dict(None) is None

    def test_converts_basic_diff(self):
        """Verify basic DiffResult is converted correctly."""
        diff = DiffResult(
            has_changes=True,
            sheet_row_count=100,
            query_row_count=150,
            rows_to_add=50,
            rows_to_remove=10,
            rows_unchanged=90,
        )

        result = diff_result_to_dict(diff)

        assert result["has_changes"] is True
        assert result["sheet_row_count"] == 100
        assert result["query_row_count"] == 150
        assert result["rows_to_add"] == 50
        assert result["rows_to_remove"] == 10
        assert result["rows_unchanged"] == 90

    def test_includes_header_changes(self):
        """Verify header_changes are included."""
        diff = DiffResult(
            has_changes=True,
            header_changes=HeaderChange(
                added=["new_col"],
                removed=["old_col"],
                reordered=True,
            ),
        )

        result = diff_result_to_dict(diff)

        assert result["header_changes"]["added"] == ["new_col"]
        assert result["header_changes"]["removed"] == ["old_col"]
        assert result["header_changes"]["reordered"] is True

    def test_includes_summary(self):
        """Verify summary is generated."""
        diff = DiffResult(
            has_changes=True,
            rows_to_add=50,
            rows_to_remove=10,
        )

        result = diff_result_to_dict(diff)

        assert "summary" in result
        assert "+50 rows" in result["summary"]
        assert "-10 rows" in result["summary"]


class TestSchemaChangesToDict:
    """Tests for schema_changes_to_dict function."""

    def test_returns_none_for_none_input(self):
        """Verify None input returns None output."""
        assert schema_changes_to_dict(None) is None

    def test_converts_schema_changes(self):
        """Verify schema changes dict is normalized."""
        schema = {
            "has_changes": True,
            "added_columns": ["new_col1", "new_col2"],
            "removed_columns": ["old_col"],
            "reordered": True,
            "expected_headers": ["id", "name"],
            "actual_headers": ["id", "name", "new_col1", "new_col2"],
            "policy_applied": "additive",
        }

        result = schema_changes_to_dict(schema)

        assert result["has_changes"] is True
        assert result["added_columns"] == ["new_col1", "new_col2"]
        assert result["removed_columns"] == ["old_col"]
        assert result["reordered"] is True
        assert result["policy_applied"] == "additive"

    def test_provides_defaults_for_missing_keys(self):
        """Verify defaults are provided for missing keys."""
        schema = {"has_changes": True}

        result = schema_changes_to_dict(schema)

        assert result["added_columns"] == []
        assert result["removed_columns"] == []
        assert result["reordered"] is False
        assert result["policy_applied"] is None


class TestSyncResultConverter:
    """Tests for SyncResultConverter class."""

    def test_to_dict_basic(self):
        """Verify basic conversion to dict."""
        result = SyncResult(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["id", "name", "email", "status", "created"],
            message="Sync completed successfully",
        )

        converter = SyncResultConverter(result=result)
        data = converter.to_dict()

        assert data["success"] is True
        assert data["rows_synced"] == 100
        assert data["columns"] == 5
        assert data["headers"] == ["id", "name", "email", "status", "created"]
        assert data["message"] == "Sync completed successfully"
        assert data["error"] is None
        assert data["preview"] is False

    def test_to_dict_with_error(self):
        """Verify error is included in dict."""
        result = SyncResult(
            success=False,
            error="Connection refused",
        )

        converter = SyncResultConverter(result=result)
        data = converter.to_dict()

        assert data["success"] is False
        assert data["error"] == "Connection refused"

    def test_to_dict_with_timestamp(self):
        """Verify timestamp is included when requested."""
        result = SyncResult(success=True)

        converter = SyncResultConverter(result=result, include_timestamp=True)
        data = converter.to_dict()

        assert "timestamp" in data
        # ISO format should contain T and Z or timezone
        assert "T" in data["timestamp"]

    def test_to_dict_with_dry_run(self):
        """Verify dry_run is included when requested."""
        result = SyncResult(success=True)

        converter = SyncResultConverter(
            result=result,
            include_dry_run=True,
            dry_run=True,
        )
        data = converter.to_dict()

        assert data["dry_run"] is True

    def test_to_dict_with_resumable(self):
        """Verify resumable fields are included."""
        result = SyncResult(success=True)

        converter = SyncResultConverter(
            result=result,
            include_resumable=True,
            resumable=True,
            checkpoint_chunk=5,
        )
        data = converter.to_dict()

        assert data["resumable"] is True
        assert data["checkpoint_chunk"] == 5

    def test_to_dict_with_diff(self):
        """Verify diff is converted and included."""
        diff = DiffResult(
            has_changes=True,
            rows_to_add=10,
            rows_to_remove=5,
        )
        result = SyncResult(
            success=True,
            preview=True,
            diff=diff,
        )

        converter = SyncResultConverter(result=result)
        data = converter.to_dict()

        assert data["preview"] is True
        assert data["diff"]["has_changes"] is True
        assert data["diff"]["rows_to_add"] == 10
        assert data["diff"]["rows_to_remove"] == 5

    def test_to_dict_with_schema_changes(self):
        """Verify schema_changes is included."""
        result = SyncResult(
            success=True,
            schema_changes={
                "has_changes": True,
                "added_columns": ["new_col"],
            },
        )

        converter = SyncResultConverter(result=result)
        data = converter.to_dict()

        assert data["schema_changes"]["has_changes"] is True
        assert data["schema_changes"]["added_columns"] == ["new_col"]

    def test_to_dict_with_warnings_ec53(self):
        """Verify warnings are included (EC-53)."""
        result = SyncResult(
            success=True,
            warnings=["Query returned 0 rows", "Using empty result behavior: warn"],
        )

        converter = SyncResultConverter(result=result)
        data = converter.to_dict()

        assert "warnings" in data
        assert len(data["warnings"]) == 2
        assert "Query returned 0 rows" in data["warnings"]

    def test_to_dict_with_empty_result_skipped_ec53(self):
        """Verify empty_result_skipped is included (EC-53)."""
        result = SyncResult(
            success=True,
            empty_result_skipped=True,
        )

        converter = SyncResultConverter(result=result)
        data = converter.to_dict()

        assert data["empty_result_skipped"] is True

    def test_to_api_response(self):
        """Verify conversion to API SyncResponse model."""
        diff = DiffResult(
            has_changes=True,
            rows_to_add=10,
            header_changes=HeaderChange(added=["new_col"], removed=[], reordered=False),
        )
        result = SyncResult(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["id", "name"],
            message="Done",
            preview=True,
            diff=diff,
        )

        converter = SyncResultConverter(result=result)
        response = converter.to_api_response()

        assert response.success is True
        assert response.rows_synced == 100
        assert response.columns == 5
        assert response.headers == ["id", "name"]
        assert response.message == "Done"
        assert response.preview is True
        assert response.diff is not None
        assert response.diff.has_changes is True
        assert response.diff.rows_to_add == 10

    def test_to_api_response_with_schema_changes(self):
        """Verify schema_changes in API response."""
        result = SyncResult(
            success=True,
            schema_changes={
                "has_changes": True,
                "added_columns": ["new_col"],
                "removed_columns": [],
                "reordered": False,
                "expected_headers": ["id"],
                "actual_headers": ["id", "new_col"],
                "policy_applied": "additive",
            },
        )

        converter = SyncResultConverter(result=result)
        response = converter.to_api_response()

        assert response.schema_changes is not None
        assert response.schema_changes.has_changes is True
        assert response.schema_changes.added_columns == ["new_col"]
        assert response.schema_changes.policy_applied == "additive"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_sync_result_to_dict(self):
        """Verify sync_result_to_dict convenience function."""
        result = SyncResult(success=True, rows_synced=50)

        data = sync_result_to_dict(result, include_timestamp=True)

        assert data["success"] is True
        assert data["rows_synced"] == 50
        assert "timestamp" in data

    def test_sync_result_to_api_response(self):
        """Verify sync_result_to_api_response convenience function."""
        result = SyncResult(success=True, rows_synced=50)

        response = sync_result_to_api_response(result)

        assert response.success is True
        assert response.rows_synced == 50

    def test_sync_result_to_api_response_with_resumable(self):
        """Verify resumable fields in API response."""
        result = SyncResult(success=True, rows_synced=50)

        response = sync_result_to_api_response(
            result,
            resumable=True,
            checkpoint_chunk=10,
        )

        assert response.resumable is True
        assert response.checkpoint_chunk == 10

    def test_sync_result_to_web_dict(self):
        """Verify sync_result_to_web_dict convenience function."""
        result = SyncResult(success=True, rows_synced=50)

        data = sync_result_to_web_dict(result, dry_run=True)

        assert data["success"] is True
        assert data["rows_synced"] == 50
        assert data["dry_run"] is True


class TestFieldConsistency:
    """Tests verifying field consistency across all output methods."""

    def test_all_sync_result_fields_in_dict(self):
        """Verify all SyncResult fields are represented in dict output."""
        # Create a fully-populated SyncResult
        diff = DiffResult(
            has_changes=True,
            rows_to_add=10,
            rows_to_remove=5,
            rows_to_modify=2,
            rows_unchanged=80,
            header_changes=HeaderChange(
                added=["new_col"],
                removed=["old_col"],
                reordered=True,
            ),
        )
        result = SyncResult(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["id", "name", "email", "status", "created"],
            message="Success",
            error=None,
            preview=True,
            diff=diff,
            schema_changes={"has_changes": True, "added_columns": ["new_col"]},
            warnings=["Warning 1"],
            empty_result_skipped=False,
        )

        data = sync_result_to_dict(result)

        # Core fields
        assert "success" in data
        assert "rows_synced" in data
        assert "columns" in data
        assert "headers" in data
        assert "message" in data
        assert "error" in data
        assert "preview" in data

        # Diff fields
        assert "diff" in data
        assert data["diff"]["rows_to_modify"] == 2
        assert data["diff"]["header_changes"]["reordered"] is True
        assert "summary" in data["diff"]

        # Schema changes
        assert "schema_changes" in data

        # EC-53 fields
        assert "warnings" in data

    def test_header_changes_reordered_in_all_outputs(self):
        """Verify header_changes.reordered is in all outputs (was missing in Web)."""
        diff = DiffResult(
            has_changes=True,
            header_changes=HeaderChange(reordered=True),
        )
        result = SyncResult(success=True, preview=True, diff=diff)

        # Dict output
        data = sync_result_to_dict(result)
        assert data["diff"]["header_changes"]["reordered"] is True

        # API response
        response = sync_result_to_api_response(result)
        assert response.diff.header_changes["reordered"] is True

        # Web dict
        web_data = sync_result_to_web_dict(result)
        assert web_data["diff"]["header_changes"]["reordered"] is True
