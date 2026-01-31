"""Integration tests for schema evolution with sync flow.

Tests cover:
- Schema checking during run_sync
- Streaming mode first-chunk validation
- Tier gating for non-strict policies
- Notification sent when changes detected
"""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.schema_evolution import (
    SchemaChangeError,
    SchemaPolicy,
    apply_schema_policy,
    detect_schema_change,
)


class TestSchemaEvolutionInSync:
    """Tests for schema evolution in run_sync flow."""

    @patch("mysql_to_sheets.core.sync_legacy.fetch_data")
    @patch("mysql_to_sheets.core.sync_legacy.push_to_sheets")
    @patch("mysql_to_sheets.core.sync_legacy.get_config")
    def test_sync_with_no_expected_headers_skips_check(
        self,
        mock_get_config: MagicMock,
        mock_push: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        """Test that first sync (no expected_headers) skips schema check."""
        from mysql_to_sheets.core.sync import run_sync

        # Mock config with all required attributes
        mock_config = MagicMock()
        mock_config.sql_query = "SELECT id, name FROM users"
        mock_config.sync_mode = "replace"
        mock_config.sync_chunk_size = 1000
        mock_config.db_type = "mysql"
        mock_config.google_sheet_id = "test123"
        mock_config.google_worksheet_name = "Sheet1"
        mock_config.log_file = "/tmp/test.log"
        mock_config.log_level = "INFO"
        mock_config.log_max_bytes = 1000000
        mock_config.log_backup_count = 5
        mock_config.snapshot_enabled = False
        mock_config.column_mapping_enabled = False
        # PII detection settings (needed for sync flow)
        mock_config.pii_detect_enabled = False
        mock_config.pii_confidence_threshold = 0.7
        mock_config.pii_sample_size = 100
        mock_config.pii_default_transform = "hash"
        mock_config.pii_require_acknowledgment = True
        # Streaming settings
        mock_config.streaming_atomic_enabled = True
        mock_config.streaming_preserve_gid = False
        # License
        mock_config.license_key = ""
        mock_get_config.return_value = mock_config

        # Mock fetch_data to return some data
        mock_fetch.return_value = (["id", "name"], [[1, "Alice"]])

        # Run sync without schema_policy or expected_headers (first sync)
        # The schema check should only run when BOTH are provided
        result = run_sync(
            config=mock_config,
            dry_run=True,
            schema_policy=None,  # No policy = skip check
            expected_headers=None,  # First sync
        )

        assert result.success is True
        assert result.schema_changes is None  # No check performed

    def test_schema_check_with_strict_policy_violation(self) -> None:
        """Test that strict policy raises error on schema change."""
        expected = ["id", "name"]
        actual = ["id", "name", "email"]  # Added column

        change = detect_schema_change(expected, actual)

        with pytest.raises(SchemaChangeError) as exc_info:
            apply_schema_policy(change, SchemaPolicy.STRICT, actual, [[1, "Alice", "a@b.com"]])

        assert exc_info.value.code == "SCHEMA_001"

    def test_schema_check_with_additive_policy_allows_added(self) -> None:
        """Test that additive policy allows added columns."""
        expected = ["id", "name"]
        actual = ["id", "name", "email"]  # Added column

        change = detect_schema_change(expected, actual)
        headers, rows, should_notify = apply_schema_policy(
            change, SchemaPolicy.ADDITIVE, actual, [[1, "Alice", "a@b.com"]]
        )

        assert headers == actual  # No filtering
        assert should_notify is True

    def test_schema_check_with_additive_policy_fails_on_removed(self) -> None:
        """Test that additive policy fails when columns removed."""
        expected = ["id", "name", "email"]
        actual = ["id", "name"]  # Removed column

        change = detect_schema_change(expected, actual)

        with pytest.raises(SchemaChangeError) as exc_info:
            apply_schema_policy(change, SchemaPolicy.ADDITIVE, actual, [[1, "Alice"]])

        assert exc_info.value.code == "SCHEMA_002"

    def test_schema_check_with_flexible_policy(self) -> None:
        """Test that flexible policy allows all changes."""
        expected = ["id", "old_col"]
        actual = ["id", "new_col"]  # Changed column

        change = detect_schema_change(expected, actual)
        headers, rows, should_notify = apply_schema_policy(
            change, SchemaPolicy.FLEXIBLE, actual, [[1, "value"]]
        )

        assert headers == actual
        assert should_notify is True


class TestSchemaEvolutionTierGating:
    """Tests for tier gating of schema policies."""

    def test_strict_policy_available_in_free_tier(self) -> None:
        """Test strict policy is available in FREE tier."""
        from mysql_to_sheets.core.schema_evolution import get_policy_tier_requirement

        feature_key = get_policy_tier_requirement("strict")
        assert feature_key is None  # No tier required

    def test_non_strict_policies_require_pro_tier(self) -> None:
        """Test non-strict policies require PRO tier."""
        from mysql_to_sheets.core.schema_evolution import get_policy_tier_requirement
        from mysql_to_sheets.core.tier import Tier, check_feature_access

        for policy in ["additive", "flexible", "notify_only"]:
            feature_key = get_policy_tier_requirement(policy)
            assert feature_key is not None

            # Should require at least PRO tier
            assert not check_feature_access(Tier.FREE, feature_key)
            assert check_feature_access(Tier.PRO, feature_key)


class TestSchemaEvolutionInStreamingMode:
    """Tests for schema evolution in streaming sync."""

    def test_streaming_schema_check_on_first_chunk(self) -> None:
        """Test that schema is checked on first chunk in streaming mode."""
        # The schema check happens when headers are first obtained
        expected = ["id", "name"]
        actual = ["id", "name", "email"]

        change = detect_schema_change(expected, actual)
        assert change.has_changes is True
        assert change.added_columns == ["email"]

        # With strict policy, this would fail before any data is pushed
        with pytest.raises(SchemaChangeError):
            apply_schema_policy(change, "strict", actual, [])

    def test_streaming_allows_changes_with_flexible_policy(self) -> None:
        """Test streaming allows changes with flexible policy."""
        expected = ["id", "old"]
        actual = ["id", "new"]

        change = detect_schema_change(expected, actual)
        headers, rows, should_notify = apply_schema_policy(
            change, "flexible", actual, []
        )

        assert headers == actual
        assert should_notify is True


class TestSyncConfigSchemaFields:
    """Tests for SyncConfigDefinition schema fields."""

    def test_sync_config_has_schema_fields(self) -> None:
        """Test SyncConfigDefinition includes schema_policy and expected_headers."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT * FROM users",
            sheet_id="abc123",
            organization_id=1,
            schema_policy="additive",
            expected_headers=["id", "name", "email"],
        )

        assert config.schema_policy == "additive"
        assert config.expected_headers == ["id", "name", "email"]

    def test_sync_config_default_schema_policy(self) -> None:
        """Test default schema_policy is 'strict'."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT * FROM users",
            sheet_id="abc123",
            organization_id=1,
        )

        assert config.schema_policy == "strict"
        assert config.expected_headers is None

    def test_sync_config_validates_schema_policy(self) -> None:
        """Test SyncConfigDefinition validates schema_policy."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT * FROM users",
            sheet_id="abc123",
            organization_id=1,
            schema_policy="invalid_policy",
        )

        errors = config.validate()
        assert any("schema_policy" in e.lower() for e in errors)

    def test_sync_config_to_dict_includes_schema_fields(self) -> None:
        """Test to_dict includes schema evolution fields."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        config = SyncConfigDefinition(
            name="test",
            sql_query="SELECT * FROM users",
            sheet_id="abc123",
            organization_id=1,
            schema_policy="flexible",
            expected_headers=["id", "name"],
        )

        data = config.to_dict()
        assert data["schema_policy"] == "flexible"
        assert data["expected_headers"] == ["id", "name"]

    def test_sync_config_from_dict_parses_schema_fields(self) -> None:
        """Test from_dict parses schema evolution fields."""
        from mysql_to_sheets.models.sync_configs import SyncConfigDefinition

        data = {
            "name": "test",
            "sql_query": "SELECT * FROM users",
            "sheet_id": "abc123",
            "organization_id": 1,
            "schema_policy": "notify_only",
            "expected_headers": ["id", "email"],
        }

        config = SyncConfigDefinition.from_dict(data)
        assert config.schema_policy == "notify_only"
        assert config.expected_headers == ["id", "email"]
