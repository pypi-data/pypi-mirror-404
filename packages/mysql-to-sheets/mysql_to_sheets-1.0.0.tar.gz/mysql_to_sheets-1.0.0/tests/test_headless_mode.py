"""Tests for headless mode (FR-12).

Tests the --headless flag which requires ENTERPRISE license for
unattended CI/CD pipeline usage.
"""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.cli.main import EXIT_TIER
from mysql_to_sheets.core.tier import Tier


def make_sync_args(**overrides: object) -> argparse.Namespace:
    """Create a mock sync args namespace with all required attributes."""
    defaults = {
        "dry_run": False,
        "preview": False,
        "yes": False,
        "headless": False,
        "output": "text",
        "sheet_id": None,
        "worksheet": None,
        "query": None,
        "mode": None,
        "chunk_size": None,
        "incremental": None,
        "incremental_since": None,
        "notify": None,
        "db_type": None,
        "create_worksheet": False,
        "atomic": None,
        "preserve_gid": None,
        "column_map": None,
        "column_order": None,
        "column_case": None,
        "use_query": None,
        "use_sheet": None,
        "org_slug": None,
        "verbose": False,
        # Additional args used by cmd_sync
        "google_sheet_id": None,
        "google_worksheet_name": None,
        "sql_query": None,
        # Schema evolution args
        "schema_policy": None,
        "expected_headers": None,
        # Resumable streaming args
        "resumable": None,
        "resume_job": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class TestHeadlessMode:
    """Tests for --headless flag."""

    def test_headless_requires_enterprise_tier(self) -> None:
        """Verify --headless flag requires ENTERPRISE tier."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.output_result") as mock_output,
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
            )

            result = cmd_sync(args)

            assert result == EXIT_TIER
            mock_output.assert_called_once()
            call_args = mock_output.call_args[0][0]
            assert call_args["success"] is False
            assert "ENTERPRISE" in call_args["message"]
            assert call_args["code"] == "LICENSE_004"

    def test_headless_denied_for_pro_tier(self) -> None:
        """Verify --headless is denied for PRO tier (requires ENTERPRISE)."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.PRO,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.output_result") as mock_output,
        ):
            mock_config.return_value = MagicMock(
                license_key="",  # Empty to skip license validation block
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
            )

            result = cmd_sync(args)

            assert result == EXIT_TIER
            mock_output.assert_called_once()
            call_args = mock_output.call_args[0][0]
            assert call_args["required_tier"] == "enterprise"
            assert call_args["current_tier"] == "pro"

    def test_headless_denied_for_business_tier(self) -> None:
        """Verify --headless is denied for BUSINESS tier (requires ENTERPRISE)."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.BUSINESS,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.output_result") as mock_output,
        ):
            mock_config.return_value = MagicMock(
                license_key="",  # Empty to skip license validation block
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
            )

            result = cmd_sync(args)

            assert result == EXIT_TIER
            mock_output.assert_called_once()
            call_args = mock_output.call_args[0][0]
            assert call_args["required_tier"] == "enterprise"
            assert call_args["current_tier"] == "business"

    def test_headless_allowed_for_enterprise_tier(self) -> None:
        """Verify --headless is allowed for ENTERPRISE tier."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.ENTERPRISE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
        ):
            mock_config.return_value = MagicMock(
                license_key="",  # Empty to skip license validation block
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
                sync_mode="replace",
                with_overrides=MagicMock(return_value=MagicMock()),
            )
            mock_run_sync.return_value = MagicMock(
                success=True,
                rows_synced=100,
                columns=5,
                headers=["a", "b", "c", "d", "e"],
                message="Success",
                error=None,
                preview=False,
                diff=None,
            )

            result = cmd_sync(args)

            assert result == 0
            mock_run_sync.assert_called_once()

    def test_headless_forces_json_output(self) -> None:
        """Verify --headless forces JSON output format."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.ENTERPRISE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
        ):
            mock_config.return_value = MagicMock(
                license_key="",  # Empty to skip license validation block
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
                sync_mode="replace",
                with_overrides=MagicMock(return_value=MagicMock()),
            )
            mock_run_sync.return_value = MagicMock(
                success=True,
                rows_synced=100,
                columns=5,
                headers=["a", "b", "c", "d", "e"],
                message="Success",
                error=None,
                preview=False,
                diff=None,
            )

            result = cmd_sync(args)

            assert result == 0
            assert args.output == "json"

    def test_headless_sets_yes_flag(self) -> None:
        """Verify --headless automatically sets --yes flag."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.ENTERPRISE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
            patch("builtins.input") as mock_input,
        ):
            mock_config.return_value = MagicMock(
                license_key="",  # Empty to skip license validation block
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
                sync_mode="replace",
                with_overrides=MagicMock(return_value=MagicMock()),
            )
            mock_run_sync.return_value = MagicMock(
                success=True,
                rows_synced=100,
                columns=5,
                headers=["a", "b", "c", "d", "e"],
                message="Success",
                error=None,
                preview=False,
                diff=None,
            )

            result = cmd_sync(args)

            assert result == 0
            mock_input.assert_not_called()
            assert args.yes is True

    def test_headless_error_includes_upgrade_url(self) -> None:
        """Verify headless error includes upgrade URL."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(headless=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.output_result") as mock_output,
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
            )

            result = cmd_sync(args)

            assert result == EXIT_TIER
            call_args = mock_output.call_args[0][0]
            assert "upgrade_url" in call_args
