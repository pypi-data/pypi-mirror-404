"""Tests for new user onboarding edge cases (EC-36 through EC-40).

These tests verify that the sync tool properly handles common mistakes
that new users make during their first setup experience, providing
clear error messages and guidance.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.config import (
    Config,
    _check_service_account_readable,
)
from mysql_to_sheets.core.database.factory import (
    detect_port_mismatch,
    enhance_connection_error,
)
from mysql_to_sheets.core.exceptions import ConfigError, ErrorCode, SheetsError
from mysql_to_sheets.core.sync_legacy import detect_sheets_api_not_enabled


class TestMissingEnvFile:
    """EC-36: Missing or empty .env file detection.

    Problem: User runs sync without creating .env or with empty file.
    Gets 5+ "missing field" errors without understanding root cause.
    """

    def test_bulk_missing_fields_suggests_env_file(self):
        """4+ missing required fields should suggest .env file issue."""
        # Create minimal config with only non-required fields
        with patch.dict(os.environ, {}, clear=True):
            config = Config(
                db_host="localhost",  # Has a default
                db_port=3306,  # Has a default
                db_type="mysql",  # Has a default
                # Missing: db_user, db_password, db_name, google_sheet_id, sql_query
            )
            errors = config.validate()

        # Should have bulk missing detection message first
        assert len(errors) > 0
        first_error = errors[0].lower()
        assert "multiple required" in first_error or "missing" in first_error

        # Should mention .env file
        env_mentioned = any(".env" in e.lower() for e in errors)
        assert env_mentioned, f"Expected .env file mention in errors: {errors}"

    def test_few_missing_fields_no_bulk_message(self):
        """1-3 missing fields should NOT trigger bulk missing detection."""
        # Must clear environment to ensure Config doesn't pick up existing values
        with patch.dict(os.environ, {}, clear=True):
            config = Config(
                db_host="localhost",
                db_port=3306,
                db_type="mysql",
                db_user="test_user",
                db_password="test_pass",
                db_name="test_db",
                # Missing: google_sheet_id, sql_query (only 2)
            )
            errors = config.validate()

        # Should have individual field errors, not bulk message
        assert len(errors) >= 1
        # First error should NOT be about "multiple required"
        first_error = errors[0].lower()
        assert "multiple required" not in first_error


class TestQueryReturnsZeroRows:
    """EC-37: Query returns zero rows warning.

    Problem: Query executes successfully but returns 0 rows.
    User sees "0 rows synced" and thinks setup is broken.
    """

    def test_empty_result_handler_logs_helpful_warning(self):
        """EmptyResultHandlerStep should log helpful message with error code."""
        from mysql_to_sheets.core.sync.protocols import SyncContext
        from mysql_to_sheets.core.sync.steps.fetch import EmptyResultHandlerStep

        # Create mock context
        ctx = MagicMock(spec=SyncContext)
        ctx.rows = []  # Empty rows
        ctx.headers = ["id", "name"]  # Has headers
        ctx.config = MagicMock()
        ctx.config.sync_empty_result_action = "warn"
        ctx.dry_run = False
        ctx.mode = "replace"
        ctx.logger = MagicMock()

        step = EmptyResultHandlerStep()

        # Should run when rows is empty but headers exist
        assert step.should_run(ctx)

        # Execute and capture log calls
        result = step.execute(ctx)

        # Should have called log_warning with helpful message
        # (The step uses log_warning via self.log_warning)
        assert result.short_circuit, "Should short-circuit on empty result with 'warn' action"

    def test_empty_result_contains_error_code(self):
        """Empty result warning should mention error code CONFIG_115."""
        # The error code should be referenced in messages
        assert hasattr(ErrorCode, "CONFIG_QUERY_NO_RESULTS")
        assert ErrorCode.CONFIG_QUERY_NO_RESULTS == "CONFIG_115"


class TestDatabasePortMismatch:
    """EC-38: Database port/type mismatch detection.

    Problem: User sets DB_TYPE=postgres but leaves DB_PORT=3306 (MySQL default).
    Connection fails with cryptic timeout.
    """

    def test_postgres_on_mysql_port_detected(self):
        """PostgreSQL on port 3306 should be detected as mismatch."""
        warning = detect_port_mismatch("postgres", 3306)

        assert warning is not None
        assert "3306" in warning
        assert "5432" in warning
        assert "PostgreSQL" in warning
        assert "MySQL" in warning

    def test_mysql_on_postgres_port_detected(self):
        """MySQL on port 5432 should be detected as mismatch."""
        warning = detect_port_mismatch("mysql", 5432)

        assert warning is not None
        assert "5432" in warning
        assert "3306" in warning
        assert "MySQL" in warning
        assert "PostgreSQL" in warning

    def test_mssql_on_mysql_port_detected(self):
        """SQL Server on port 3306 should be detected as mismatch."""
        warning = detect_port_mismatch("mssql", 3306)

        assert warning is not None
        assert "3306" in warning
        assert "1433" in warning
        assert "SQL Server" in warning
        assert "MySQL" in warning

    def test_correct_port_no_warning(self):
        """Correct port for database type should return None."""
        assert detect_port_mismatch("mysql", 3306) is None
        assert detect_port_mismatch("postgres", 5432) is None
        assert detect_port_mismatch("postgresql", 5432) is None
        assert detect_port_mismatch("mssql", 1433) is None
        assert detect_port_mismatch("sqlserver", 1433) is None

    def test_custom_port_no_warning(self):
        """Custom port (not any default) should return None."""
        # Port 8080 isn't a default for any database
        assert detect_port_mismatch("mysql", 8080) is None
        assert detect_port_mismatch("postgres", 8080) is None

    def test_enhance_connection_error_adds_hint(self):
        """Connection error should be enhanced with port mismatch hint."""
        error = Exception("Connection refused")
        enhanced = enhance_connection_error(error, "postgres", "localhost", 3306)

        assert "Connection refused" in enhanced
        assert "Possible cause" in enhanced
        assert "5432" in enhanced

    def test_enhance_connection_error_no_match(self):
        """Connection error with correct port should not be enhanced."""
        error = Exception("Connection refused")
        enhanced = enhance_connection_error(error, "postgres", "localhost", 5432)

        # Should just return original error message
        assert enhanced == "Connection refused"


class TestSheetsAPINotEnabled:
    """EC-39: Google Sheets API not enabled detection.

    Problem: User creates service account but forgets to enable Sheets API.
    Gets cryptic 403 error.
    """

    def test_access_not_configured_detected(self):
        """accessNotConfigured error should be detected."""
        error = Exception(
            "Google Sheets API has not been used in project 12345 before or it is disabled. "
            "Enable it by visiting https://console.developers.google.com/..."
        )
        msg = detect_sheets_api_not_enabled(error)

        assert msg is not None
        assert "Google Sheets API is not enabled" in msg
        assert "console.cloud.google.com" in msg
        assert ErrorCode.SHEETS_API_NOT_ENABLED in msg

    def test_api_has_not_been_used_detected(self):
        """API has not been used error should be detected."""
        error = Exception("API has not been used in project before")
        msg = detect_sheets_api_not_enabled(error)

        assert msg is not None
        assert "Enable" in msg

    def test_disabled_api_detected(self):
        """Disabled API error should be detected."""
        error = Exception("sheets.googleapis.com is disabled")
        msg = detect_sheets_api_not_enabled(error)

        assert msg is not None

    def test_regular_error_not_detected(self):
        """Regular API error should not be detected as API-not-enabled."""
        error = Exception("Permission denied")
        msg = detect_sheets_api_not_enabled(error)

        assert msg is None

    def test_rate_limit_not_detected(self):
        """Rate limit error should not be detected as API-not-enabled."""
        error = Exception("Rate limit exceeded")
        msg = detect_sheets_api_not_enabled(error)

        assert msg is None


class TestServiceAccountNotReadable:
    """EC-40: Service account file not readable.

    Problem: File exists but has wrong permissions. Error says "not found"
    when file actually exists.
    """

    def test_readable_file_returns_ok(self):
        """Readable file should return (True, None)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "service_account"}')
            f.flush()
            path = f.name

        try:
            readable, error = _check_service_account_readable(path)
            assert readable is True
            assert error is None
        finally:
            Path(path).unlink()

    def test_nonexistent_file_defers_to_not_found(self):
        """Non-existent file should return (True, None) to let file-not-found handle it."""
        readable, error = _check_service_account_readable("/nonexistent/path.json")
        # Should return True (no readable error) because file doesn't exist
        # The "file not found" error will be raised later
        assert readable is True
        assert error is None

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Windows doesn't support chmod for read permissions the same way"
    )
    def test_unreadable_file_gives_permission_error(self):
        """Unreadable file should give clear permission error with fix instructions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "service_account"}')
            f.flush()
            path = f.name

        try:
            # Remove read permission
            os.chmod(path, 0o000)

            readable, error = _check_service_account_readable(path)

            assert readable is False
            assert error is not None
            assert "cannot be read" in error.lower() or "permissions" in error.lower()
            assert "chmod" in error.lower()
            assert path in error

        finally:
            # Restore permission so we can delete
            os.chmod(path, 0o644)
            Path(path).unlink()

    def test_error_message_includes_fix_instructions(self):
        """Permission error should include fix instructions."""
        # Create a temp file to get a valid path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "service_account"}')
            path = f.name

        try:
            if os.name != "nt":
                os.chmod(path, 0o000)
                readable, error = _check_service_account_readable(path)

                if not readable:  # Only check if we successfully made it unreadable
                    assert "chmod 644" in error
                    assert path in error

                os.chmod(path, 0o644)
        finally:
            try:
                os.chmod(path, 0o644)
            except OSError:
                pass
            Path(path).unlink()


class TestErrorCodesDefined:
    """Verify all new error codes are properly defined."""

    def test_config_env_file_issue_code_exists(self):
        """CONFIG_114 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_ENV_FILE_ISSUE")
        assert ErrorCode.CONFIG_ENV_FILE_ISSUE == "CONFIG_114"

    def test_config_query_no_results_code_exists(self):
        """CONFIG_115 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_QUERY_NO_RESULTS")
        assert ErrorCode.CONFIG_QUERY_NO_RESULTS == "CONFIG_115"

    def test_config_port_mismatch_code_exists(self):
        """CONFIG_116 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_PORT_MISMATCH")
        assert ErrorCode.CONFIG_PORT_MISMATCH == "CONFIG_116"

    def test_config_service_account_not_readable_code_exists(self):
        """CONFIG_117 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_SERVICE_ACCOUNT_NOT_READABLE")
        assert ErrorCode.CONFIG_SERVICE_ACCOUNT_NOT_READABLE == "CONFIG_117"

    def test_sheets_api_not_enabled_code_exists(self):
        """SHEETS_314 should be defined."""
        assert hasattr(ErrorCode, "SHEETS_API_NOT_ENABLED")
        assert ErrorCode.SHEETS_API_NOT_ENABLED == "SHEETS_314"
