"""Tests for CLI module."""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.cli.main import cli, create_parser


class TestCreateParser:
    """Tests for argument parser creation."""

    def test_parser_version(self):
        """Test --version flag."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_parser_help(self):
        """Test --help flag."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_parser_sync_command(self):
        """Test sync command parsing."""
        parser = create_parser()
        args = parser.parse_args(["sync"])
        assert args.command == "sync"
        assert args.dry_run is False
        assert args.verbose is False

    def test_parser_sync_with_options(self):
        """Test sync command with all options."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "sync",
                "--sheet-id",
                "ABC123",
                "--worksheet",
                "Data",
                "--query",
                "SELECT * FROM t",
                "--dry-run",
                "--verbose",
                "--output",
                "json",
            ]
        )
        assert args.command == "sync"
        assert args.google_sheet_id == "ABC123"
        assert args.google_worksheet_name == "Data"
        assert args.sql_query == "SELECT * FROM t"
        assert args.dry_run is True
        assert args.verbose is True
        assert args.output == "json"

    def test_parser_validate_command(self):
        """Test validate command parsing."""
        parser = create_parser()
        args = parser.parse_args(["validate"])
        assert args.command == "validate"

    def test_parser_test_db_command(self):
        """Test test-db command parsing."""
        parser = create_parser()
        args = parser.parse_args(["test-db"])
        assert args.command == "test-db"

    def test_parser_test_sheets_command(self):
        """Test test-sheets command parsing."""
        parser = create_parser()
        args = parser.parse_args(["test-sheets"])
        assert args.command == "test-sheets"


class TestCli:
    """Tests for main cli function."""

    def test_cli_no_command_shows_help(self):
        """Test CLI with no command returns 0."""
        result = cli([])
        assert result == 0

    @patch("mysql_to_sheets.cli.sync_commands.get_config")
    @patch("mysql_to_sheets.cli.sync_commands.reset_config")
    def test_cli_validate_invalid_config(self, mock_reset, mock_get_config):
        """Test validate command with invalid config."""
        mock_config = MagicMock()
        mock_config.validate.return_value = ["DB_USER is required"]
        mock_get_config.return_value = mock_config

        result = cli(["validate", "--output", "json"])
        assert result == 1

    @patch("mysql_to_sheets.cli.sync_commands.get_config")
    @patch("mysql_to_sheets.cli.sync_commands.reset_config")
    def test_cli_validate_valid_config(self, mock_reset, mock_get_config):
        """Test validate command with valid config."""
        mock_config = MagicMock()
        mock_config.validate.return_value = []
        mock_get_config.return_value = mock_config

        result = cli(["validate"])
        assert result == 0
