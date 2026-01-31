"""Tests for CLI confirmation prompt (FR-03).

Tests the human-in-the-loop confirmation behavior for sync operations
that prevents automation without a PRO license.
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


class TestCliYesFlag:
    """Tests for --yes flag license gating."""

    def test_yes_flag_requires_pro_tier(self) -> None:
        """Verify --yes flag requires PRO tier or higher."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(yes=True)

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
                sync_mode="replace",
            )

            result = cmd_sync(args)

            assert result == EXIT_TIER
            mock_output.assert_called_once()
            call_args = mock_output.call_args[0][0]
            assert call_args["success"] is False
            assert "PRO license" in call_args["message"]
            assert call_args["code"] == "LICENSE_004"

    def test_yes_flag_allowed_for_pro_tier(self) -> None:
        """Verify --yes flag is allowed for PRO tier."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(yes=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.PRO,
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

    def test_yes_flag_not_needed_for_dry_run(self) -> None:
        """Verify dry-run mode skips confirmation regardless of tier."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(dry_run=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
                sync_mode="replace",
                with_overrides=MagicMock(return_value=MagicMock()),
            )
            mock_run_sync.return_value = MagicMock(
                success=True,
                rows_synced=0,
                columns=5,
                headers=["a", "b", "c", "d", "e"],
                message="Dry run",
                error=None,
                preview=False,
                diff=None,
            )

            result = cmd_sync(args)

            assert result == 0

    def test_yes_flag_not_needed_for_preview(self) -> None:
        """Verify preview mode skips confirmation regardless of tier."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(preview=True)

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                google_sheet_id="test_sheet",
                google_worksheet_name="Sheet1",
                sync_mode="replace",
                with_overrides=MagicMock(return_value=MagicMock()),
            )
            mock_run_sync.return_value = MagicMock(
                success=True,
                rows_synced=0,
                columns=5,
                headers=["a", "b", "c", "d", "e"],
                message="Preview",
                error=None,
                preview=True,
                diff=MagicMock(
                    has_changes=True,
                    sheet_row_count=0,
                    query_row_count=100,
                    rows_to_add=100,
                    rows_to_remove=0,
                    rows_unchanged=0,
                    header_changes=MagicMock(added=[], removed=[], reordered=False),
                ),
            )

            result = cmd_sync(args)

            assert result == 0


class TestInteractiveConfirmation:
    """Tests for interactive confirmation prompt."""

    def test_confirmation_prompt_for_free_tier_push(self) -> None:
        """Verify confirmation prompt appears for FREE tier push operations."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args()

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.output_result") as mock_output,
            patch("builtins.input", return_value="n"),
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                google_sheet_id="test_sheet_123456",
                google_worksheet_name="Sheet1",
                sync_mode="replace",
                with_overrides=MagicMock(return_value=MagicMock()),
            )

            result = cmd_sync(args)

            assert result == 0
            mock_output.assert_called_once()
            call_args = mock_output.call_args[0][0]
            assert call_args["cancelled"] is True

    def test_confirmation_prompt_user_confirms(self) -> None:
        """Verify sync proceeds when user confirms."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args()

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
            patch("builtins.input", return_value="y"),
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                google_sheet_id="test_sheet_123456",
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

    def test_json_output_skips_confirmation(self) -> None:
        """Verify JSON output mode skips interactive confirmation."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = make_sync_args(output="json")

        with (
            patch(
                "mysql_to_sheets.cli.sync_commands.get_tier_from_license",
                return_value=Tier.FREE,
            ),
            patch("mysql_to_sheets.cli.sync_commands.get_config") as mock_config,
            patch("mysql_to_sheets.cli.sync_commands.run_sync") as mock_run_sync,
            patch("mysql_to_sheets.cli.sync_commands.output_result"),
            patch("builtins.input") as mock_input,
        ):
            mock_config.return_value = MagicMock(
                license_key="",
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

            mock_input.assert_not_called()
            assert result == 0


class TestExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_tier_code_value(self) -> None:
        """Verify EXIT_TIER has the correct value."""
        from mysql_to_sheets.cli.main import EXIT_LICENSE, EXIT_TIER

        assert EXIT_LICENSE == 5
        assert EXIT_TIER == 6
