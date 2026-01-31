"""Tests for sheet commands CLI module."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.cli.sheet_commands import (
    _get_spreadsheet,
    add_sheet_parsers,
    cmd_sheet_create,
    cmd_sheet_delete,
    cmd_sheet_list,
    handle_sheet_command,
)
from mysql_to_sheets.core.exceptions import ConfigError, SheetsError


class TestAddSheetParsers:
    """Tests for add_sheet_parsers."""

    def test_adds_sheet_parser(self):
        """Test that sheet parser is added."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_sheet_parsers(subparsers)

        # Parse sheet create command
        args = parser.parse_args(["sheet", "create", "--name", "Test"])
        assert args.name == "Test"

    def test_create_command_options(self):
        """Test create command accepts all options."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_sheet_parsers(subparsers)

        args = parser.parse_args(
            [
                "sheet",
                "create",
                "--name",
                "Test Sheet",
                "--rows",
                "500",
                "--cols",
                "10",
                "--sheet-id",
                "abc123",
                "--output",
                "json",
            ]
        )
        assert args.name == "Test Sheet"
        assert args.rows == 500
        assert args.cols == 10
        assert args.sheet_id == "abc123"
        assert args.output == "json"

    def test_list_command_options(self):
        """Test list command accepts all options."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_sheet_parsers(subparsers)

        args = parser.parse_args(
            [
                "sheet",
                "list",
                "--sheet-id",
                "xyz789",
                "--output",
                "json",
            ]
        )
        assert args.sheet_id == "xyz789"
        assert args.output == "json"

    def test_delete_command_options(self):
        """Test delete command accepts all options."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_sheet_parsers(subparsers)

        args = parser.parse_args(
            [
                "sheet",
                "delete",
                "--name",
                "OldSheet",
                "--sheet-id",
                "abc123",
                "--force",
                "--output",
                "json",
            ]
        )
        assert args.name == "OldSheet"
        assert args.sheet_id == "abc123"
        assert args.force is True
        assert args.output == "json"


class TestGetSpreadsheet:
    """Tests for _get_spreadsheet helper."""

    @patch("mysql_to_sheets.cli.sheet_commands.gspread")
    def test_uses_cli_sheet_id_over_config(self, mock_gspread):
        """Test CLI sheet ID takes precedence over config."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_gspread.service_account.return_value = mock_gc
        mock_gc.open_by_key.return_value = mock_spreadsheet

        spreadsheet, sheet_id = _get_spreadsheet(
            config_sheet_id="config_id",
            cli_sheet_id="cli_id",
            service_account_file="/path/to/sa.json",
        )

        mock_gc.open_by_key.assert_called_once_with("cli_id")
        assert sheet_id == "cli_id"

    @patch("mysql_to_sheets.cli.sheet_commands.gspread")
    def test_uses_config_sheet_id_when_no_cli(self, mock_gspread):
        """Test config sheet ID is used when no CLI override."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_gspread.service_account.return_value = mock_gc
        mock_gc.open_by_key.return_value = mock_spreadsheet

        spreadsheet, sheet_id = _get_spreadsheet(
            config_sheet_id="config_id",
            cli_sheet_id=None,
            service_account_file="/path/to/sa.json",
        )

        mock_gc.open_by_key.assert_called_once_with("config_id")
        assert sheet_id == "config_id"

    def test_raises_config_error_when_no_sheet_id(self):
        """Test raises ConfigError when no sheet ID is provided."""
        with pytest.raises(ConfigError, match="No Google Sheet ID provided"):
            _get_spreadsheet(
                config_sheet_id=None,
                cli_sheet_id=None,
                service_account_file="/path/to/sa.json",
            )

    @patch("mysql_to_sheets.cli.sheet_commands.gspread")
    def test_parses_url_from_cli(self, mock_gspread):
        """Test parses Google Sheets URL from CLI argument."""
        mock_gc = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_gspread.service_account.return_value = mock_gc
        mock_gc.open_by_key.return_value = mock_spreadsheet

        url = "https://docs.google.com/spreadsheets/d/abc123xyz/edit"
        spreadsheet, sheet_id = _get_spreadsheet(
            config_sheet_id=None,
            cli_sheet_id=url,
            service_account_file="/path/to/sa.json",
        )

        mock_gc.open_by_key.assert_called_once_with("abc123xyz")
        assert sheet_id == "abc123xyz"


class TestCmdSheetCreate:
    """Tests for cmd_sheet_create."""

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.create_worksheet")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_create_worksheet_success(
        self, mock_reset, mock_get_config, mock_create, mock_get_spreadsheet
    ):
        """Test successful worksheet creation."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.google_sheet_id = "test_sheet_id"
        mock_config.service_account_file = "/path/to/sa.json"
        mock_config.worksheet_default_rows = 1000
        mock_config.worksheet_default_cols = 26
        mock_get_config.return_value = mock_config

        mock_spreadsheet = MagicMock()
        mock_get_spreadsheet.return_value = (mock_spreadsheet, "test_sheet_id")

        mock_worksheet = MagicMock()
        mock_worksheet.title = "NewSheet"
        mock_worksheet.id = 123
        mock_worksheet.row_count = 1000
        mock_worksheet.col_count = 26
        mock_create.return_value = mock_worksheet

        # Create args
        args = argparse.Namespace(
            name="NewSheet",
            rows=None,
            cols=None,
            sheet_id=None,
            output="text",
        )

        result = cmd_sheet_create(args)

        assert result == 0
        mock_create.assert_called_once_with(
            mock_spreadsheet,
            "NewSheet",
            rows=1000,
            cols=26,
        )

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.create_worksheet")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_create_worksheet_with_custom_size(
        self, mock_reset, mock_get_config, mock_create, mock_get_spreadsheet
    ):
        """Test worksheet creation with custom size."""
        mock_config = MagicMock()
        mock_config.google_sheet_id = "test_sheet_id"
        mock_config.service_account_file = "/path/to/sa.json"
        mock_config.worksheet_default_rows = 1000
        mock_config.worksheet_default_cols = 26
        mock_get_config.return_value = mock_config

        mock_spreadsheet = MagicMock()
        mock_get_spreadsheet.return_value = (mock_spreadsheet, "test_sheet_id")

        mock_worksheet = MagicMock()
        mock_worksheet.title = "LargeSheet"
        mock_worksheet.id = 456
        mock_worksheet.row_count = 5000
        mock_worksheet.col_count = 50
        mock_create.return_value = mock_worksheet

        args = argparse.Namespace(
            name="LargeSheet",
            rows=5000,
            cols=50,
            sheet_id=None,
            output="text",
        )

        result = cmd_sheet_create(args)

        assert result == 0
        mock_create.assert_called_once_with(
            mock_spreadsheet,
            "LargeSheet",
            rows=5000,
            cols=50,
        )

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_create_worksheet_error(self, mock_reset, mock_get_config, mock_get_spreadsheet):
        """Test worksheet creation error handling."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_get_spreadsheet.side_effect = SheetsError(
            message="Spreadsheet not found",
            sheet_id="bad_id",
        )

        args = argparse.Namespace(
            name="NewSheet",
            rows=None,
            cols=None,
            sheet_id="bad_id",
            output="text",
        )

        result = cmd_sheet_create(args)

        assert result == 1


class TestCmdSheetList:
    """Tests for cmd_sheet_list."""

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.list_worksheets")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_list_worksheets_success(
        self, mock_reset, mock_get_config, mock_list, mock_get_spreadsheet
    ):
        """Test successful worksheet listing."""
        mock_config = MagicMock()
        mock_config.google_sheet_id = "test_sheet_id"
        mock_config.service_account_file = "/path/to/sa.json"
        mock_get_config.return_value = mock_config

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Test Spreadsheet"
        mock_get_spreadsheet.return_value = (mock_spreadsheet, "test_sheet_id")

        mock_list.return_value = [
            {"title": "Sheet1", "gid": 0, "rows": 1000, "cols": 26},
            {"title": "Sheet2", "gid": 123, "rows": 500, "cols": 10},
        ]

        args = argparse.Namespace(
            sheet_id=None,
            output="text",
        )

        result = cmd_sheet_list(args)

        assert result == 0
        mock_list.assert_called_once_with(mock_spreadsheet)


class TestCmdSheetDelete:
    """Tests for cmd_sheet_delete."""

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.delete_worksheet")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_delete_worksheet_with_force(
        self, mock_reset, mock_get_config, mock_delete, mock_get_spreadsheet
    ):
        """Test worksheet deletion with --force flag."""
        mock_config = MagicMock()
        mock_config.google_sheet_id = "test_sheet_id"
        mock_config.service_account_file = "/path/to/sa.json"
        mock_get_config.return_value = mock_config

        mock_spreadsheet = MagicMock()
        mock_get_spreadsheet.return_value = (mock_spreadsheet, "test_sheet_id")

        mock_delete.return_value = True

        args = argparse.Namespace(
            name="OldSheet",
            sheet_id=None,
            force=True,
            output="text",
        )

        result = cmd_sheet_delete(args)

        assert result == 0
        mock_delete.assert_called_once_with(mock_spreadsheet, "OldSheet")

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.delete_worksheet")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_delete_worksheet_json_output_no_prompt(
        self, mock_reset, mock_get_config, mock_delete, mock_get_spreadsheet
    ):
        """Test worksheet deletion with JSON output skips prompt."""
        mock_config = MagicMock()
        mock_config.google_sheet_id = "test_sheet_id"
        mock_config.service_account_file = "/path/to/sa.json"
        mock_get_config.return_value = mock_config

        mock_spreadsheet = MagicMock()
        mock_get_spreadsheet.return_value = (mock_spreadsheet, "test_sheet_id")

        mock_delete.return_value = True

        args = argparse.Namespace(
            name="OldSheet",
            sheet_id=None,
            force=False,
            output="json",  # JSON output should skip prompt
        )

        result = cmd_sheet_delete(args)

        assert result == 0
        mock_delete.assert_called_once_with(mock_spreadsheet, "OldSheet")

    @patch("mysql_to_sheets.cli.sheet_commands._get_spreadsheet")
    @patch("mysql_to_sheets.cli.sheet_commands.get_config")
    @patch("mysql_to_sheets.cli.sheet_commands.reset_config")
    def test_delete_worksheet_not_found(self, mock_reset, mock_get_config, mock_get_spreadsheet):
        """Test worksheet deletion when worksheet not found."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_get_spreadsheet.side_effect = SheetsError(
            message="Worksheet not found",
            sheet_id="test_sheet_id",
            worksheet_name="NotFound",
        )

        args = argparse.Namespace(
            name="NotFound",
            sheet_id=None,
            force=True,
            output="text",
        )

        result = cmd_sheet_delete(args)

        assert result == 1


class TestHandleSheetCommand:
    """Tests for handle_sheet_command."""

    def test_no_subcommand_prints_help(self, capsys):
        """Test no subcommand prints usage help."""
        args = argparse.Namespace(sheet_command=None)

        result = handle_sheet_command(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "mysql-to-sheets sheet" in captured.out
        assert "create" in captured.out
        assert "list" in captured.out
        assert "delete" in captured.out

    def test_unknown_subcommand(self, capsys):
        """Test unknown subcommand returns error."""
        args = argparse.Namespace(sheet_command="unknown")

        result = handle_sheet_command(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown sheet command" in captured.out

    @patch("mysql_to_sheets.cli.sheet_commands.cmd_sheet_create")
    def test_routes_to_create(self, mock_create):
        """Test routes create command to handler."""
        mock_create.return_value = 0
        args = argparse.Namespace(sheet_command="create")

        result = handle_sheet_command(args)

        assert result == 0
        mock_create.assert_called_once_with(args)

    @patch("mysql_to_sheets.cli.sheet_commands.cmd_sheet_list")
    def test_routes_to_list(self, mock_list):
        """Test routes list command to handler."""
        mock_list.return_value = 0
        args = argparse.Namespace(sheet_command="list")

        result = handle_sheet_command(args)

        assert result == 0
        mock_list.assert_called_once_with(args)

    @patch("mysql_to_sheets.cli.sheet_commands.cmd_sheet_delete")
    def test_routes_to_delete(self, mock_delete):
        """Test routes delete command to handler."""
        mock_delete.return_value = 0
        args = argparse.Namespace(sheet_command="delete")

        result = handle_sheet_command(args)

        assert result == 0
        mock_delete.assert_called_once_with(args)
