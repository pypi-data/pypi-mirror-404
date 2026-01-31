"""Tests for config request override helpers.

This module tests the centralized apply_request_overrides() and
extract_sync_options() functions that eliminate duplicated override
patterns across API, Web, and CLI layers.
"""

import pytest
from argparse import Namespace
from unittest.mock import patch, MagicMock

from mysql_to_sheets.core.config import (
    Config,
    apply_request_overrides,
    extract_sync_options,
)


class TestApplyRequestOverrides:
    """Tests for apply_request_overrides function."""

    def test_returns_config_without_request(self):
        """Verify returns base config when no request provided."""
        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(None)

                assert result is mock_config

    def test_applies_sheet_id_from_dict(self):
        """Verify sheet_id is extracted from dict request."""
        request = {"sheet_id": "test_sheet_123"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.google_sheet_id == "test_sheet_123"

    def test_applies_sheet_id_from_namespace(self):
        """Verify sheet_id is extracted from argparse Namespace."""
        args = Namespace(google_sheet_id="ns_sheet_456", worksheet_name=None)

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(args)

                assert result.google_sheet_id == "ns_sheet_456"

    def test_parses_sheet_url_to_id(self):
        """Verify Google Sheets URLs are parsed to extract sheet ID."""
        url = "https://docs.google.com/spreadsheets/d/abc123def456/edit#gid=0"
        request = {"sheet_id": url}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.google_sheet_id == "abc123def456"

    def test_applies_worksheet_name(self):
        """Verify worksheet_name is applied."""
        request = {"worksheet_name": "Data Export"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.google_worksheet_name == "Data Export"

    def test_applies_sql_query(self):
        """Verify sql_query is applied."""
        request = {"sql_query": "SELECT * FROM users LIMIT 100"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.sql_query == "SELECT * FROM users LIMIT 100"

    def test_applies_db_type(self):
        """Verify db_type is applied."""
        request = {"db_type": "postgres"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.db_type == "postgres"

    def test_applies_column_map_dict(self):
        """Verify column_map as dict is converted to JSON."""
        request = {"column_map": {"old_col": "New Column"}}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.column_mapping_enabled is True
                assert '"old_col"' in result.column_mapping
                assert '"New Column"' in result.column_mapping

    def test_applies_column_map_json_string(self):
        """Verify column_map as JSON string is passed through."""
        request = {"column_map": '{"cust_id": "Customer ID"}'}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.column_mapping_enabled is True
                assert result.column_mapping == '{"cust_id": "Customer ID"}'

    def test_applies_column_map_simple_format(self):
        """Verify column_map as simple old=new format is converted."""
        request = {"column_map": "cust_id=Customer ID,txn_dt=Transaction Date"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.column_mapping_enabled is True
                assert "cust_id" in result.column_mapping
                assert "Customer ID" in result.column_mapping

    def test_applies_columns_list(self):
        """Verify columns as list is converted to comma-separated."""
        request = {"columns": ["Name", "Email", "Status"]}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.column_mapping_enabled is True
                assert result.column_order == "Name,Email,Status"

    def test_applies_column_case(self):
        """Verify column_case is applied."""
        request = {"column_case": "title"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.column_mapping_enabled is True
                assert result.column_case == "title"

    def test_applies_sync_mode(self):
        """Verify mode is applied to sync_mode."""
        request = {"mode": "streaming"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.sync_mode == "streaming"

    def test_applies_chunk_size(self):
        """Verify chunk_size is applied."""
        request = {"chunk_size": 500}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.sync_chunk_size == 500

    def test_applies_notify_true(self):
        """Verify notify=True is applied to both success and failure."""
        request = {"notify": True}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.notify_on_success is True
                assert result.notify_on_failure is True

    def test_applies_notify_false(self):
        """Verify notify=False is applied to both success and failure."""
        request = {"notify": False}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(request)

                assert result.notify_on_success is False
                assert result.notify_on_failure is False

    def test_explicit_args_override_request(self):
        """Verify explicit keyword args take precedence over request."""
        request = {"sheet_id": "from_request", "mode": "append"}

        with patch("mysql_to_sheets.core.config.singleton.reset_config"):
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                result = apply_request_overrides(
                    request,
                    sheet_id="explicit_override",
                    mode="streaming",
                )

                assert result.google_sheet_id == "explicit_override"
                assert result.sync_mode == "streaming"

    def test_uses_base_config_when_provided(self):
        """Verify base_config is used instead of get_config()."""
        base_config = Config()
        base_config = base_config.with_overrides(db_type="postgres")

        request = {"sheet_id": "test123"}

        # Should not call reset_config or get_config
        with patch(
            "mysql_to_sheets.core.config.singleton.reset_config"
        ) as mock_reset:
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                result = apply_request_overrides(request, base_config=base_config)

                mock_reset.assert_not_called()
                mock_get.assert_not_called()

        assert result.db_type == "postgres"
        assert result.google_sheet_id == "test123"

    def test_skips_reset_when_reset_before_false(self):
        """Verify reset_config is skipped when reset_before=False."""
        with patch(
            "mysql_to_sheets.core.config.singleton.reset_config"
        ) as mock_reset:
            with patch(
                "mysql_to_sheets.core.config.singleton.get_config"
            ) as mock_get:
                mock_config = Config()
                mock_get.return_value = mock_config

                apply_request_overrides(None, reset_before=False)

                mock_reset.assert_not_called()
                mock_get.assert_called_once()


class TestExtractSyncOptions:
    """Tests for extract_sync_options function."""

    def test_extracts_dry_run(self):
        """Verify dry_run is extracted."""
        request = {"dry_run": True}
        options = extract_sync_options(request)
        assert options["dry_run"] is True

    def test_extracts_preview(self):
        """Verify preview is extracted."""
        request = {"preview": True}
        options = extract_sync_options(request)
        assert options["preview"] is True

    def test_extracts_atomic(self):
        """Verify atomic is extracted."""
        request = {"atomic": False}
        options = extract_sync_options(request)
        assert options["atomic"] is False

    def test_extracts_preserve_gid(self):
        """Verify preserve_gid is extracted."""
        request = {"preserve_gid": True}
        options = extract_sync_options(request)
        assert options["preserve_gid"] is True

    def test_extracts_resumable(self):
        """Verify resumable is extracted."""
        request = {"resumable": True}
        options = extract_sync_options(request)
        assert options["resumable"] is True

    def test_extracts_create_worksheet(self):
        """Verify create_worksheet is extracted."""
        request = {"create_worksheet": True}
        options = extract_sync_options(request)
        assert options["create_worksheet"] is True

    def test_extracts_schema_policy(self):
        """Verify schema_policy is extracted."""
        request = {"schema_policy": "additive"}
        options = extract_sync_options(request)
        assert options["schema_policy"] == "additive"

    def test_extracts_expected_headers(self):
        """Verify expected_headers is extracted."""
        request = {"expected_headers": ["id", "name", "email"]}
        options = extract_sync_options(request)
        assert options["expected_headers"] == ["id", "name", "email"]

    def test_extracts_detect_pii(self):
        """Verify detect_pii is extracted."""
        request = {"detect_pii": True}
        options = extract_sync_options(request)
        assert options["detect_pii"] is True

    def test_extracts_pii_acknowledged(self):
        """Verify pii_acknowledged is extracted."""
        request = {"pii_acknowledged": True}
        options = extract_sync_options(request)
        assert options["pii_acknowledged"] is True

    def test_explicit_args_override_request(self):
        """Verify explicit args take precedence over request."""
        request = {"dry_run": False, "preview": False}
        options = extract_sync_options(request, dry_run=True, preview=True)
        assert options["dry_run"] is True
        assert options["preview"] is True

    def test_defaults_for_missing_values(self):
        """Verify defaults are applied for missing values."""
        options = extract_sync_options(None)
        assert options["dry_run"] is False
        assert options["preview"] is False

    def test_works_with_namespace(self):
        """Verify extraction works with argparse Namespace."""
        args = Namespace(
            dry_run=True,
            preview=False,
            atomic=None,
            preserve_gid=None,
            resumable=False,
            create_worksheet=None,
            schema_policy=None,
            expected_headers=None,
            detect_pii=None,
            pii_acknowledged=False,
        )
        options = extract_sync_options(args)
        assert options["dry_run"] is True
        assert options["preview"] is False
