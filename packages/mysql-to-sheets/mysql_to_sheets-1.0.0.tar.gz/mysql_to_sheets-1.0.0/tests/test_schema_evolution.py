"""Unit tests for schema evolution policy handling.

Tests cover:
- detect_schema_change with various scenarios
- apply_schema_policy for each policy type
- SchemaChangeError exceptions
- Tier gating for non-strict policies
"""

import pytest

from mysql_to_sheets.core.schema_evolution import (
    VALID_SCHEMA_POLICIES,
    SchemaChange,
    SchemaChangeError,
    SchemaPolicy,
    apply_schema_policy,
    detect_schema_change,
    get_policy_tier_requirement,
)


class TestSchemaPolicy:
    """Tests for SchemaPolicy enum."""

    def test_valid_policies(self) -> None:
        """Verify all expected policies exist."""
        assert SchemaPolicy.STRICT.value == "strict"
        assert SchemaPolicy.ADDITIVE.value == "additive"
        assert SchemaPolicy.FLEXIBLE.value == "flexible"
        assert SchemaPolicy.NOTIFY_ONLY.value == "notify_only"

    def test_from_string_valid(self) -> None:
        """Test parsing valid policy strings."""
        assert SchemaPolicy.from_string("strict") == SchemaPolicy.STRICT
        assert SchemaPolicy.from_string("STRICT") == SchemaPolicy.STRICT
        assert SchemaPolicy.from_string("Additive") == SchemaPolicy.ADDITIVE
        assert SchemaPolicy.from_string("flexible") == SchemaPolicy.FLEXIBLE
        assert SchemaPolicy.from_string("notify_only") == SchemaPolicy.NOTIFY_ONLY

    def test_from_string_invalid(self) -> None:
        """Test parsing invalid policy string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SchemaPolicy.from_string("invalid")
        assert "Invalid schema policy" in str(exc_info.value)

    def test_valid_schema_policies_tuple(self) -> None:
        """Verify VALID_SCHEMA_POLICIES contains all policy values."""
        assert VALID_SCHEMA_POLICIES == ("strict", "additive", "flexible", "notify_only")


class TestSchemaChange:
    """Tests for SchemaChange dataclass."""

    def test_default_values(self) -> None:
        """Test default SchemaChange has no changes."""
        change = SchemaChange()
        assert change.has_changes is False
        assert change.added_columns == []
        assert change.removed_columns == []
        assert change.reordered is False

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["new_col"],
            removed_columns=["old_col"],
            reordered=True,
            expected_headers=["id", "old_col"],
            actual_headers=["id", "new_col"],
        )
        result = change.to_dict()

        assert result["has_changes"] is True
        assert result["added_columns"] == ["new_col"]
        assert result["removed_columns"] == ["old_col"]
        assert result["reordered"] is True
        assert result["expected_headers"] == ["id", "old_col"]
        assert result["actual_headers"] == ["id", "new_col"]

    def test_summary_no_changes(self) -> None:
        """Test summary with no changes."""
        change = SchemaChange()
        assert change.summary() == "No schema changes detected"

    def test_summary_with_added(self) -> None:
        """Test summary with added columns."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["col1", "col2"],
        )
        summary = change.summary()
        assert "2 column(s) added" in summary
        assert "col1" in summary

    def test_summary_with_removed(self) -> None:
        """Test summary with removed columns."""
        change = SchemaChange(
            has_changes=True,
            removed_columns=["old1"],
        )
        summary = change.summary()
        assert "1 column(s) removed" in summary

    def test_summary_with_reorder_only(self) -> None:
        """Test summary with reorder only."""
        change = SchemaChange(
            has_changes=True,
            reordered=True,
        )
        summary = change.summary()
        assert "column order changed" in summary


class TestDetectSchemaChange:
    """Tests for detect_schema_change function."""

    def test_no_expected_headers(self) -> None:
        """Test first sync with no expected headers returns no changes."""
        actual = ["id", "name", "email"]
        change = detect_schema_change(None, actual)

        assert change.has_changes is False
        assert change.expected_headers == []
        assert change.actual_headers == actual

    def test_identical_headers(self) -> None:
        """Test identical headers returns no changes."""
        headers = ["id", "name", "email"]
        change = detect_schema_change(headers, headers.copy())

        assert change.has_changes is False
        assert change.added_columns == []
        assert change.removed_columns == []
        assert change.reordered is False

    def test_added_columns(self) -> None:
        """Test detecting added columns."""
        expected = ["id", "name"]
        actual = ["id", "name", "email"]
        change = detect_schema_change(expected, actual)

        assert change.has_changes is True
        assert change.added_columns == ["email"]
        assert change.removed_columns == []

    def test_removed_columns(self) -> None:
        """Test detecting removed columns."""
        expected = ["id", "name", "email"]
        actual = ["id", "name"]
        change = detect_schema_change(expected, actual)

        assert change.has_changes is True
        assert change.added_columns == []
        assert change.removed_columns == ["email"]

    def test_both_added_and_removed(self) -> None:
        """Test detecting both added and removed columns."""
        expected = ["id", "old_col"]
        actual = ["id", "new_col"]
        change = detect_schema_change(expected, actual)

        assert change.has_changes is True
        assert change.added_columns == ["new_col"]
        assert change.removed_columns == ["old_col"]

    def test_reordered_columns(self) -> None:
        """Test detecting reordered columns (same set, different order)."""
        expected = ["id", "name", "email"]
        actual = ["email", "id", "name"]
        change = detect_schema_change(expected, actual)

        assert change.has_changes is True
        assert change.added_columns == []
        assert change.removed_columns == []
        assert change.reordered is True


class TestApplySchemaPolicy:
    """Tests for apply_schema_policy function."""

    def test_no_changes_returns_original(self) -> None:
        """Test that no changes returns original data unchanged."""
        change = SchemaChange(has_changes=False)
        headers = ["id", "name"]
        rows = [[1, "Alice"], [2, "Bob"]]

        result_headers, result_rows, should_notify = apply_schema_policy(
            change, SchemaPolicy.STRICT, headers, rows
        )

        assert result_headers == headers
        assert result_rows == rows
        assert should_notify is False

    def test_strict_policy_fails_on_any_change(self) -> None:
        """Test strict policy raises error on any schema change."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["new_col"],
        )

        with pytest.raises(SchemaChangeError) as exc_info:
            apply_schema_policy(change, SchemaPolicy.STRICT, ["id", "new_col"], [])

        assert exc_info.value.code == "SCHEMA_001"
        assert "strict" in str(exc_info.value).lower()

    def test_strict_policy_fails_on_removed(self) -> None:
        """Test strict policy raises error on removed columns."""
        change = SchemaChange(
            has_changes=True,
            removed_columns=["old_col"],
        )

        with pytest.raises(SchemaChangeError) as exc_info:
            apply_schema_policy(change, SchemaPolicy.STRICT, ["id"], [])

        assert exc_info.value.code == "SCHEMA_001"

    def test_additive_policy_allows_added(self) -> None:
        """Test additive policy allows added columns."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["new_col"],
        )
        headers = ["id", "new_col"]
        rows = [[1, "value"]]

        result_headers, result_rows, should_notify = apply_schema_policy(
            change, SchemaPolicy.ADDITIVE, headers, rows
        )

        assert result_headers == headers
        assert result_rows == rows
        assert should_notify is True

    def test_additive_policy_fails_on_removed(self) -> None:
        """Test additive policy raises error when columns are removed."""
        change = SchemaChange(
            has_changes=True,
            removed_columns=["old_col"],
        )

        with pytest.raises(SchemaChangeError) as exc_info:
            apply_schema_policy(change, SchemaPolicy.ADDITIVE, ["id"], [])

        assert exc_info.value.code == "SCHEMA_002"
        assert "removed" in str(exc_info.value).lower()

    def test_flexible_policy_allows_all_changes(self) -> None:
        """Test flexible policy allows both added and removed columns."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["new_col"],
            removed_columns=["old_col"],
        )
        headers = ["id", "new_col"]
        rows = [[1, "value"]]

        result_headers, result_rows, should_notify = apply_schema_policy(
            change, SchemaPolicy.FLEXIBLE, headers, rows
        )

        assert result_headers == headers
        assert result_rows == rows
        assert should_notify is True

    def test_notify_only_filters_to_intersection(self) -> None:
        """Test notify_only policy filters to common columns."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["new_col"],
            removed_columns=["old_col"],
            expected_headers=["id", "name", "old_col"],
            actual_headers=["id", "name", "new_col"],
        )
        headers = ["id", "name", "new_col"]
        rows = [[1, "Alice", "added"], [2, "Bob", "value"]]

        result_headers, result_rows, should_notify = apply_schema_policy(
            change, SchemaPolicy.NOTIFY_ONLY, headers, rows
        )

        # Should filter to common columns (id, name)
        assert result_headers == ["id", "name"]
        assert result_rows == [[1, "Alice"], [2, "Bob"]]
        assert should_notify is True

    def test_policy_as_string(self) -> None:
        """Test that policy can be passed as string."""
        change = SchemaChange(has_changes=False)

        result_headers, result_rows, should_notify = apply_schema_policy(
            change, "strict", ["id"], [[1]]
        )

        assert result_headers == ["id"]


class TestGetPolicyTierRequirement:
    """Tests for get_policy_tier_requirement function."""

    def test_strict_no_tier_required(self) -> None:
        """Test strict policy requires no special tier."""
        assert get_policy_tier_requirement(SchemaPolicy.STRICT) is None
        assert get_policy_tier_requirement("strict") is None

    def test_additive_requires_pro(self) -> None:
        """Test additive policy requires PRO tier."""
        assert get_policy_tier_requirement(SchemaPolicy.ADDITIVE) == "schema_policy_additive"

    def test_flexible_requires_pro(self) -> None:
        """Test flexible policy requires PRO tier."""
        assert get_policy_tier_requirement(SchemaPolicy.FLEXIBLE) == "schema_policy_flexible"

    def test_notify_only_requires_pro(self) -> None:
        """Test notify_only policy requires PRO tier."""
        assert get_policy_tier_requirement(SchemaPolicy.NOTIFY_ONLY) == "schema_policy_notify_only"


class TestSchemaChangeError:
    """Tests for SchemaChangeError exception."""

    def test_error_with_schema_change(self) -> None:
        """Test error includes schema change details."""
        change = SchemaChange(
            has_changes=True,
            added_columns=["new"],
        )
        error = SchemaChangeError(
            message="Test error",
            code="SCHEMA_001",
            schema_change=change,
            policy="strict",
        )

        assert error.code == "SCHEMA_001"
        assert error.schema_change == change
        assert error.policy == "strict"
        assert "schema_change" in error.details

    def test_error_to_dict(self) -> None:
        """Test error serialization includes details."""
        error = SchemaChangeError(
            message="Test error",
            code="SCHEMA_002",
            policy="additive",
        )

        error_dict = error.to_dict()
        assert error_dict["code"] == "SCHEMA_002"
        assert error_dict["details"]["policy"] == "additive"
