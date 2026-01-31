"""Tests for CLI quickstart commands."""

import argparse
import sys
from unittest.mock import MagicMock, patch

from mysql_to_sheets.cli.quickstart_commands import (
    Colors,
    add_quickstart_parsers,
    cmd_quickstart,
    colorize,
    print_error,
    print_header,
    print_hint,
    print_info,
    print_step,
    print_success,
    prompt,
    prompt_choice,
    run_sync,
    save_env_file,
    supports_color,
    validate_database_connection,
    validate_query,
    validate_sheets_connection,
)


class TestColorSupport:
    """Tests for color support functions."""

    def test_supports_color_with_no_color_env(self, monkeypatch):
        """Test supports_color returns False when NO_COLOR is set."""
        monkeypatch.setenv("NO_COLOR", "1")
        assert supports_color() is False

    def test_supports_color_without_tty(self, monkeypatch):
        """Test supports_color returns False for non-TTY stdout."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        mock_stdout = MagicMock()
        mock_stdout.isatty.return_value = False
        monkeypatch.setattr(sys, "stdout", mock_stdout)
        assert supports_color() is False

    def test_supports_color_with_tty(self, monkeypatch):
        """Test supports_color returns True for TTY stdout."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        mock_stdout = MagicMock()
        mock_stdout.isatty.return_value = True
        monkeypatch.setattr(sys, "stdout", mock_stdout)
        assert supports_color() is True

    def test_supports_color_without_isatty(self, monkeypatch):
        """Test supports_color returns False when stdout has no isatty."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        mock_stdout = object()  # No isatty method
        monkeypatch.setattr(sys, "stdout", mock_stdout)
        assert supports_color() is False


class TestColorize:
    """Tests for colorize function."""

    def test_colorize_with_color_support(self, monkeypatch):
        """Test colorize applies color codes when supported."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        mock_stdout = MagicMock()
        mock_stdout.isatty.return_value = True
        monkeypatch.setattr(sys, "stdout", mock_stdout)

        result = colorize("test", Colors.GREEN)
        assert result == f"{Colors.GREEN}test{Colors.RESET}"

    def test_colorize_without_color_support(self, monkeypatch):
        """Test colorize returns plain text when color not supported."""
        monkeypatch.setenv("NO_COLOR", "1")

        result = colorize("test", Colors.GREEN)
        assert result == "test"


class TestPrintHelpers:
    """Tests for print helper functions."""

    def test_print_header(self, capsys, monkeypatch):
        """Test print_header outputs formatted header."""
        monkeypatch.setenv("NO_COLOR", "1")
        print_header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out
        assert "=" * 50 in captured.out

    def test_print_step(self, capsys, monkeypatch):
        """Test print_step outputs step indicator."""
        monkeypatch.setenv("NO_COLOR", "1")
        print_step(1, 4, "Database")
        captured = capsys.readouterr()
        assert "Step 1/4: Database" in captured.out
        assert "-" * 40 in captured.out

    def test_print_success(self, capsys, monkeypatch):
        """Test print_success outputs success message."""
        monkeypatch.setenv("NO_COLOR", "1")
        print_success("Connection established")
        captured = capsys.readouterr()
        assert "Connection established" in captured.out

    def test_print_error(self, capsys, monkeypatch):
        """Test print_error outputs error message."""
        monkeypatch.setenv("NO_COLOR", "1")
        print_error("Connection failed")
        captured = capsys.readouterr()
        assert "Connection failed" in captured.out

    def test_print_info(self, capsys, monkeypatch):
        """Test print_info outputs info message."""
        monkeypatch.setenv("NO_COLOR", "1")
        print_info("Testing connection...")
        captured = capsys.readouterr()
        assert "Testing connection..." in captured.out

    def test_print_hint(self, capsys, monkeypatch):
        """Test print_hint outputs hint message."""
        monkeypatch.setenv("NO_COLOR", "1")
        print_hint("Check your credentials")
        captured = capsys.readouterr()
        assert "Check your credentials" in captured.out


class TestPromptFunctions:
    """Tests for prompt functions."""

    def test_prompt_with_default(self, monkeypatch):
        """Test prompt returns default when input is empty."""
        monkeypatch.setattr("builtins.input", lambda _: "")
        result = prompt("Host", default="localhost")
        assert result == "localhost"

    def test_prompt_with_input(self, monkeypatch):
        """Test prompt returns user input."""
        monkeypatch.setattr("builtins.input", lambda _: "myhost")
        result = prompt("Host", default="localhost")
        assert result == "myhost"

    def test_prompt_without_default(self, monkeypatch):
        """Test prompt without default returns empty string when no input."""
        monkeypatch.setattr("builtins.input", lambda _: "")
        result = prompt("Host")
        assert result == ""

    @patch("getpass.getpass")
    def test_prompt_password(self, mock_getpass):
        """Test prompt with password=True uses getpass."""
        mock_getpass.return_value = "secret123"
        result = prompt("Password", password=True)
        assert result == "secret123"
        mock_getpass.assert_called_once()

    def test_prompt_choice_default(self, monkeypatch, capsys):
        """Test prompt_choice returns default on empty input."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setattr("builtins.input", lambda _: "")
        options = [("mysql", "MySQL"), ("postgres", "PostgreSQL")]
        result = prompt_choice("Select database:", options, default=0)
        assert result == "mysql"

    def test_prompt_choice_selection(self, monkeypatch, capsys):
        """Test prompt_choice returns selected option."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setattr("builtins.input", lambda _: "2")
        options = [("mysql", "MySQL"), ("postgres", "PostgreSQL")]
        result = prompt_choice("Select database:", options, default=0)
        assert result == "postgres"

    def test_prompt_choice_invalid_then_valid(self, monkeypatch, capsys):
        """Test prompt_choice handles invalid input then valid."""
        monkeypatch.setenv("NO_COLOR", "1")
        inputs = iter(["5", "invalid", "1"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        options = [("mysql", "MySQL"), ("postgres", "PostgreSQL")]
        result = prompt_choice("Select database:", options, default=0)
        assert result == "mysql"


class TestDatabaseConnectionTest:
    """Tests for validate_database_connection function."""

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_successful_mysql_connection(self, mock_get_conn):
        """Test successful MySQL connection."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        config = {
            "db_type": "mysql",
            "db_host": "localhost",
            "db_port": "3306",
            "db_user": "root",
            "db_password": "password",
            "db_name": "testdb",
        }
        success, message = validate_database_connection(config)

        assert success is True
        assert "successful" in message.lower()

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_successful_sqlite_connection(self, mock_get_conn):
        """Test successful SQLite connection."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_get_conn.return_value = mock_conn

        config = {"db_type": "sqlite", "db_name": "/path/to/test.db"}
        success, message = validate_database_connection(config)

        assert success is True
        mock_get_conn.assert_called_once()
        call_args = mock_get_conn.call_args[0][0]
        assert call_args.db_type == "sqlite"
        assert call_args.database == "/path/to/test.db"

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_failed_connection(self, mock_get_conn):
        """Test failed database connection."""
        mock_get_conn.side_effect = Exception("Connection refused")

        config = {
            "db_type": "mysql",
            "db_host": "badhost",
            "db_port": "3306",
            "db_user": "root",
            "db_password": "password",
            "db_name": "testdb",
        }
        success, message = validate_database_connection(config)

        assert success is False
        assert "Connection refused" in message


class TestSheetsConnectionTest:
    """Tests for validate_sheets_connection function."""

    @patch("gspread.authorize")
    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("os.path.exists")
    def test_successful_sheets_connection(self, mock_exists, mock_creds, mock_authorize):
        """Test successful Google Sheets connection."""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "Test Sheet"
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_authorize.return_value = mock_client

        config = {
            "service_account_file": "./service_account.json",
            "google_sheet_id": "abc123xyz",
        }
        success, message = validate_sheets_connection(config)

        assert success is True
        assert "Test Sheet" in message

    @patch("os.path.exists")
    def test_missing_service_account_file(self, mock_exists):
        """Test error when service account file is missing."""
        mock_exists.return_value = False

        config = {
            "service_account_file": "./missing.json",
            "google_sheet_id": "abc123xyz",
        }
        success, message = validate_sheets_connection(config)

        assert success is False
        assert "not found" in message.lower()

    def test_missing_sheet_id(self):
        """Test error when sheet ID is missing."""
        config = {
            "service_account_file": "./service_account.json",
            "google_sheet_id": "",
        }
        success, message = validate_sheets_connection(config)

        assert success is False
        assert "sheet ID" in message.lower() or "no sheet" in message.lower()

    @patch("gspread.authorize")
    @patch("google.oauth2.service_account.Credentials.from_service_account_file")
    @patch("os.path.exists")
    def test_sheets_connection_with_url(self, mock_exists, mock_creds, mock_authorize):
        """Test sheets connection extracts ID from full URL."""
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.title = "My Sheet"
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_authorize.return_value = mock_client

        config = {
            "service_account_file": "./service_account.json",
            "google_sheet_id": "https://docs.google.com/spreadsheets/d/abc123xyz/edit#gid=0",
        }
        success, message = validate_sheets_connection(config)

        assert success is True
        mock_client.open_by_key.assert_called_with("abc123xyz")


class TestQueryTest:
    """Tests for validate_query function."""

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_successful_query(self, mock_get_conn):
        """Test successful query execution."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_result = MagicMock()
        mock_result.rows = [["row1"], ["row2"], ["row3"]]
        mock_conn.execute.return_value = mock_result
        mock_get_conn.return_value = mock_conn

        config = {
            "db_type": "mysql",
            "db_host": "localhost",
            "db_port": "3306",
            "db_user": "root",
            "db_password": "password",
            "db_name": "testdb",
        }
        success, count, message = validate_query(config, "SELECT * FROM users")

        assert success is True
        assert count == 3

    @patch("mysql_to_sheets.core.database.get_connection")
    def test_failed_query(self, mock_get_conn):
        """Test failed query execution."""
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = Exception("Table not found")
        mock_get_conn.return_value = mock_conn

        config = {
            "db_type": "mysql",
            "db_host": "localhost",
            "db_port": "3306",
            "db_user": "root",
            "db_password": "password",
            "db_name": "testdb",
        }
        success, count, message = validate_query(config, "SELECT * FROM nonexistent")

        assert success is False
        assert count == 0
        assert "Table not found" in message


class TestSaveEnvFile:
    """Tests for save_env_file function."""

    def test_save_env_file_mysql(self, tmp_path):
        """Test saving env file for MySQL config."""
        env_path = tmp_path / ".env"
        config = {
            "db_type": "mysql",
            "db_host": "localhost",
            "db_port": "3306",
            "db_user": "myuser",
            "db_password": "mypass",
            "db_name": "mydb",
            "google_sheet_id": "sheet123",
            "worksheet": "Data",
            "service_account_file": "./sa.json",
            "sql_query": "SELECT * FROM users",
        }

        success, message = save_env_file(config, str(env_path))

        assert success is True
        assert env_path.exists()

        content = env_path.read_text()
        assert "DB_TYPE=mysql" in content
        assert "DB_HOST=localhost" in content
        assert "DB_USER=myuser" in content
        assert "DB_PASSWORD=mypass" in content
        assert "DB_NAME=mydb" in content
        assert "GOOGLE_SHEET_ID=sheet123" in content
        assert "SQL_QUERY=SELECT * FROM users" in content

    def test_save_env_file_sqlite(self, tmp_path):
        """Test saving env file for SQLite config."""
        env_path = tmp_path / ".env"
        config = {
            "db_type": "sqlite",
            "db_name": "/path/to/db.sqlite",
            "google_sheet_id": "sheet123",
            "worksheet": "Sheet1",
            "service_account_file": "./sa.json",
            "sql_query": "SELECT * FROM data",
        }

        success, message = save_env_file(config, str(env_path))

        assert success is True
        content = env_path.read_text()
        assert "DB_TYPE=sqlite" in content
        assert "DB_NAME=/path/to/db.sqlite" in content
        assert "DB_HOST" not in content  # SQLite shouldn't have host

    def test_save_env_file_error(self):
        """Test save_env_file handles write errors."""
        success, message = save_env_file({}, "/nonexistent/path/.env")
        assert success is False


class TestRunSync:
    """Tests for run_sync function."""

    @patch("mysql_to_sheets.core.sync.run_sync")
    def test_successful_sync(self, mock_run_sync):
        """Test successful sync execution."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.rows_synced = 100
        mock_run_sync.return_value = mock_result

        config = {
            "db_type": "mysql",
            "db_host": "localhost",
            "db_port": 3306,
            "db_user": "root",
            "db_password": "pass",
            "db_name": "testdb",
            "google_sheet_id": "sheet123",
            "worksheet": "Sheet1",
            "service_account_file": "./sa.json",
            "sql_query": "SELECT * FROM users",
        }

        success, rows, message = run_sync(config)

        assert success is True
        assert rows == 100

    @patch("mysql_to_sheets.core.sync.run_sync")
    def test_failed_sync(self, mock_run_sync):
        """Test failed sync execution."""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Permission denied"
        mock_run_sync.return_value = mock_result

        config = {
            "db_type": "mysql",
            "db_host": "localhost",
            "db_port": 3306,
            "db_user": "root",
            "db_password": "pass",
            "db_name": "testdb",
            "google_sheet_id": "sheet123",
            "worksheet": "Sheet1",
            "service_account_file": "./sa.json",
            "sql_query": "SELECT * FROM users",
        }

        success, rows, message = run_sync(config)

        assert success is False
        assert rows == 0
        assert "Permission denied" in message


class TestAddQuickstartParsers:
    """Tests for add_quickstart_parsers function."""

    def test_adds_quickstart_subcommand(self):
        """Test that quickstart subcommand is added."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_quickstart_parsers(subparsers)

        # Parse quickstart command
        args = parser.parse_args(["quickstart"])
        assert args.env_path == ".env"
        assert args.skip_test is False

    def test_quickstart_with_custom_env_path(self):
        """Test quickstart with custom env path."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_quickstart_parsers(subparsers)

        args = parser.parse_args(["quickstart", "--env-path", "/custom/.env"])
        assert args.env_path == "/custom/.env"

    def test_quickstart_with_skip_test(self):
        """Test quickstart with skip-test flag."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_quickstart_parsers(subparsers)

        args = parser.parse_args(["quickstart", "--skip-test"])
        assert args.skip_test is True


class TestCmdQuickstart:
    """Integration tests for cmd_quickstart function."""

    @patch("pathlib.Path.rename")
    @patch("mysql_to_sheets.cli.quickstart_commands.save_env_file")
    @patch("mysql_to_sheets.cli.quickstart_commands.run_sync")
    @patch("mysql_to_sheets.cli.quickstart_commands.validate_query")
    @patch("mysql_to_sheets.cli.quickstart_commands.validate_sheets_connection")
    @patch("mysql_to_sheets.cli.quickstart_commands.validate_database_connection")
    @patch("os.path.exists")
    def test_quickstart_success_flow(
        self,
        mock_exists,
        mock_validate_db,
        mock_validate_sheets,
        mock_validate_query,
        mock_run_sync,
        mock_save_env,
        mock_rename,
        monkeypatch,
        capsys,
    ):
        """Test successful quickstart flow."""
        monkeypatch.setenv("NO_COLOR", "1")

        # Mock file exists
        mock_exists.return_value = True
        # Mock Path.rename to avoid "file not found" error
        mock_rename.return_value = None

        # Mock all connection tests
        mock_validate_db.return_value = (True, "Connected!")
        mock_validate_sheets.return_value = (True, "Sheet found!")
        mock_validate_query.return_value = (True, 50, "Query OK")
        mock_run_sync.return_value = (True, 50, "Sync complete")
        mock_save_env.return_value = (True, "Saved to .env")

        # Simulate user inputs
        inputs = iter(
            [
                "",  # connection string (empty to skip)
                "",  # db_type: mysql (default)
                "localhost",  # host
                "3306",  # port
                "root",  # user
                "testdb",  # db_name
                "./sa.json",  # service account
                "abc123",  # sheet_id
                "Sheet1",  # worksheet
                "",  # use default query (empty = yes in demo mode, but we're not in demo)
                "SELECT * FROM users",  # query
                "",  # empty line to end query
                "y",  # run sync
                "y",  # save config
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        with patch("getpass.getpass", return_value="password"):
            args = argparse.Namespace(env_path=".env", skip_test=False)
            result = cmd_quickstart(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Setup Complete!" in captured.out

    def test_quickstart_keyboard_interrupt(self, monkeypatch, capsys):
        """Test quickstart handles keyboard interrupt."""
        monkeypatch.setenv("NO_COLOR", "1")

        def raise_interrupt(_):
            raise KeyboardInterrupt()

        monkeypatch.setattr("builtins.input", raise_interrupt)

        args = argparse.Namespace(env_path=".env", skip_test=False)
        result = cmd_quickstart(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()

    @patch("mysql_to_sheets.cli.quickstart_commands.validate_database_connection")
    def test_quickstart_db_test_failure(self, mock_validate_db, monkeypatch, capsys):
        """Test quickstart handles database test failure."""
        monkeypatch.setenv("NO_COLOR", "1")
        mock_validate_db.return_value = (False, "Connection refused")

        inputs = iter(
            [
                "",  # connection string (skip)
                "",  # db_type: mysql
                "localhost",
                "3306",
                "root",
                "testdb",
                "n",  # Don't retry
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        with patch("getpass.getpass", return_value="password"):
            args = argparse.Namespace(env_path=".env", skip_test=False)
            result = cmd_quickstart(args)

        assert result == 1

    @patch("mysql_to_sheets.cli.quickstart_commands.validate_database_connection")
    @patch("os.path.exists")
    def test_quickstart_service_account_missing(
        self, mock_exists, mock_validate_db, monkeypatch, capsys
    ):
        """Test quickstart handles missing service account file."""
        monkeypatch.setenv("NO_COLOR", "1")
        mock_validate_db.return_value = (True, "Connected!")
        mock_exists.return_value = False

        inputs = iter(
            [
                "",  # connection string (skip)
                "",  # db_type: mysql
                "localhost",
                "3306",
                "root",
                "testdb",
                "./missing.json",  # service account
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        with patch("getpass.getpass", return_value="password"):
            args = argparse.Namespace(env_path=".env", skip_test=False)
            result = cmd_quickstart(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "missing" in captured.out.lower()
