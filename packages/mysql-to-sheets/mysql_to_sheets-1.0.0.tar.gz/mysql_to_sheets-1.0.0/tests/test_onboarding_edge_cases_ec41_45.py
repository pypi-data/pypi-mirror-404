"""Tests for onboarding edge cases EC-41 through EC-45.

These tests verify that the sync tool properly handles common mistakes
that new users make during their first setup experience, providing
clear error messages and guidance.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mysql_to_sheets.core.config import (
    Config,
    _detect_sql_file_path,
    _strip_sql_comments,
    _validate_service_account_json,
)
from mysql_to_sheets.core.exceptions import ErrorCode


class TestServiceAccountBOM:
    """EC-41: Service Account JSON Has BOM (Byte Order Mark).

    Problem: Windows editors (Notepad, some IDEs) add UTF-8 BOM to files.
    JSON parser fails with cryptic "Expecting value: line 1 column 1".
    """

    def test_json_with_bom_handled_successfully(self):
        """JSON with UTF-8 BOM should parse successfully with utf-8-sig encoding."""
        bom = b"\xef\xbb\xbf"
        content = b'{"type": "service_account", "client_email": "a@b.iam.gserviceaccount.com", "private_key": "key"}'

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
            f.write(bom + content)
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert is_valid, f"BOM should be handled automatically: {error}"
            assert error is None
        finally:
            os.unlink(path)

    def test_json_without_bom_still_works(self):
        """JSON without BOM should work normally."""
        content = '{"type": "service_account", "client_email": "a@b.iam.gserviceaccount.com", "private_key": "key"}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(content)
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert is_valid
            assert error is None
        finally:
            os.unlink(path)

    def test_invalid_json_with_bom_gives_helpful_error(self):
        """Invalid JSON (even with BOM) should give clear error."""
        bom = b"\xef\xbb\xbf"
        content = b"not valid json {"

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
            f.write(bom + content)
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert not is_valid
            assert error is not None
            # Should mention invalid JSON or BOM
            assert "json" in error.lower() or "bom" in error.lower()
        finally:
            os.unlink(path)


class TestSQLFilePath:
    """EC-42: SQL Query Looks Like File Path.

    Problem: Users from other ETL tools enter file paths like
    /path/to/query.sql instead of actual SQL.
    """

    def test_unix_absolute_path_detected(self):
        """Unix absolute path ending in .sql should be detected."""
        result = _detect_sql_file_path("/path/to/query.sql")

        assert result is not None
        assert "file path" in result.lower()
        assert "SQL_QUERY" in result
        assert "$(cat" in result  # Should suggest how to load file

    def test_unix_relative_path_detected(self):
        """Unix relative path ending in .sql should be detected."""
        result = _detect_sql_file_path("./queries/my_query.sql")

        assert result is not None
        assert "file path" in result.lower()

    def test_unix_parent_relative_path_detected(self):
        """Unix parent-relative path ending in .sql should be detected."""
        result = _detect_sql_file_path("../shared/common_query.sql")

        assert result is not None

    def test_unix_home_path_detected(self):
        """Unix home path (~) ending in .sql should be detected."""
        result = _detect_sql_file_path("~/queries/report.sql")

        assert result is not None

    def test_windows_path_detected(self):
        """Windows path with drive letter should be detected."""
        result = _detect_sql_file_path("C:\\queries\\report.sql")

        assert result is not None
        assert "file path" in result.lower()

    def test_windows_path_with_forward_slash_detected(self):
        """Windows path with drive letter and forward slashes should be detected."""
        result = _detect_sql_file_path("C:/queries/report.sql")

        assert result is not None

    def test_valid_sql_not_flagged(self):
        """Valid SQL query should not be flagged."""
        result = _detect_sql_file_path("SELECT * FROM users WHERE path = '/home/user'")

        assert result is None

    def test_sql_with_file_mention_not_flagged(self):
        """SQL that mentions .sql in a string should not be flagged."""
        result = _detect_sql_file_path("SELECT * FROM scripts WHERE name LIKE '%.sql'")

        assert result is None

    def test_empty_query_not_flagged(self):
        """Empty query should not be flagged (handled by required field check)."""
        assert _detect_sql_file_path("") is None
        assert _detect_sql_file_path("   ") is None
        assert _detect_sql_file_path(None) is None  # type: ignore

    def test_sql_file_path_in_config_validate(self):
        """Config.validate() should catch SQL file paths."""
        config = Config(
            db_type="mysql",
            db_host="localhost",
            db_user="user",
            db_password="pass",
            db_name="testdb",
            google_sheet_id="abc123",
            sql_query="/path/to/query.sql",
        )
        errors = config.validate()

        # Should have error about file path
        file_path_errors = [e for e in errors if "file path" in e.lower()]
        assert len(file_path_errors) > 0


class TestWorksheetWhitespace:
    """EC-43: Worksheet Name with Leading/Trailing Whitespace.

    Problem: Copy-paste from spreadsheets includes invisible whitespace.
    Error shows "Worksheet ' Sheet1' not found" but user doesn't see the space.
    """

    def test_leading_space_stripped(self):
        """Leading space in worksheet name should be auto-stripped."""
        config = Config(
            google_worksheet_name=" Sheet1",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.google_worksheet_name == "Sheet1"

    def test_trailing_space_stripped(self):
        """Trailing space in worksheet name should be auto-stripped."""
        config = Config(
            google_worksheet_name="Sheet1 ",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.google_worksheet_name == "Sheet1"

    def test_both_sides_stripped(self):
        """Whitespace on both sides should be auto-stripped."""
        config = Config(
            google_worksheet_name="  Sheet1  ",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.google_worksheet_name == "Sheet1"

    def test_internal_space_preserved(self):
        """Internal spaces in worksheet name should be preserved."""
        config = Config(
            google_worksheet_name="Sheet 1 Data",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.google_worksheet_name == "Sheet 1 Data"

    def test_tab_and_newline_stripped(self):
        """Tab and newline characters should also be stripped."""
        config = Config(
            google_worksheet_name="\tSheet1\n",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.google_worksheet_name == "Sheet1"

    def test_no_whitespace_unchanged(self):
        """Worksheet name without whitespace should be unchanged."""
        config = Config(
            google_worksheet_name="Sheet1",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.google_worksheet_name == "Sheet1"


class TestTildePath:
    """EC-44: Service Account File Path Uses Tilde (~).

    Problem: User sets SERVICE_ACCOUNT_FILE=~/creds/service_account.json
    but Python doesn't auto-expand ~.
    """

    def test_tilde_expanded_in_post_init(self):
        """Tilde in service account path should be auto-expanded."""
        config = Config(
            service_account_file="~/creds/service_account.json",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert not config.service_account_file.startswith("~")
        assert os.path.expanduser("~") in config.service_account_file
        assert config.service_account_file.endswith("creds/service_account.json")

    def test_tilde_user_path_expanded(self):
        """Tilde with username should be expanded."""
        # This expands to something like /home/username/... or /Users/username/...
        config = Config(
            service_account_file="~/service_account.json",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert not config.service_account_file.startswith("~")
        # Should end with the filename
        assert config.service_account_file.endswith("service_account.json")

    def test_absolute_path_unchanged(self):
        """Absolute path without tilde should be unchanged."""
        config = Config(
            service_account_file="/etc/creds/service_account.json",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.service_account_file == "/etc/creds/service_account.json"

    def test_relative_path_unchanged(self):
        """Relative path without tilde should be unchanged."""
        config = Config(
            service_account_file="./service_account.json",
            db_user="test",
            db_password="test",
            db_name="test",
        )

        assert config.service_account_file == "./service_account.json"


class TestSQLOnlyComments:
    """EC-45: SQL Query Contains Only Comments.

    Problem: User copies SQL with comments but no actual query:
    "-- TODO: write query\\n-- SELECT * FROM users"
    Results in confusing syntax error.
    """

    def test_strip_single_line_dash_comments(self):
        """Single-line dash comments should be stripped."""
        query = "-- This is a comment\nSELECT * FROM users"
        stripped = _strip_sql_comments(query)

        assert "SELECT" in stripped
        assert "--" not in stripped

    def test_strip_single_line_hash_comments(self):
        """Single-line hash comments (MySQL style) should be stripped."""
        query = "# This is a MySQL comment\nSELECT * FROM users"
        stripped = _strip_sql_comments(query)

        assert "SELECT" in stripped
        assert "#" not in stripped

    def test_strip_multi_line_comments(self):
        """Multi-line /* */ comments should be stripped."""
        query = "/* Multi\nline\ncomment */SELECT * FROM users"
        stripped = _strip_sql_comments(query)

        assert "SELECT" in stripped
        assert "/*" not in stripped
        assert "*/" not in stripped

    def test_only_comments_returns_empty(self):
        """Query with only comments should return empty string."""
        query = "-- TODO: write query\n-- SELECT * FROM users"
        stripped = _strip_sql_comments(query)

        assert stripped == ""

    def test_only_multi_line_comments_returns_empty(self):
        """Query with only multi-line comments should return empty string."""
        query = "/* This is a placeholder query\n   SELECT * FROM users */"
        stripped = _strip_sql_comments(query)

        assert stripped == ""

    def test_mixed_comments_and_sql_preserved(self):
        """Query with comments AND SQL should preserve the SQL."""
        query = """
        -- Get all users
        /* Filter by active status */
        SELECT * FROM users WHERE active = 1
        -- End of query
        """
        stripped = _strip_sql_comments(query)

        assert "SELECT" in stripped
        assert "WHERE" in stripped
        assert "active" in stripped

    def test_empty_query_returns_empty(self):
        """Empty query should return empty string."""
        assert _strip_sql_comments("") == ""
        assert _strip_sql_comments("   ") == ""

    def test_comments_only_detected_in_validate(self):
        """Config.validate() should catch comments-only SQL."""
        config = Config(
            db_type="mysql",
            db_host="localhost",
            db_user="user",
            db_password="pass",
            db_name="testdb",
            google_sheet_id="abc123",
            sql_query="-- TODO: write query\n-- SELECT * FROM users",
        )
        errors = config.validate()

        # Should have error about comments only
        comment_errors = [e for e in errors if "comment" in e.lower()]
        assert len(comment_errors) > 0

    def test_valid_sql_with_comments_passes(self):
        """Valid SQL with comments should pass validation."""
        config = Config(
            db_type="mysql",
            db_host="localhost",
            db_user="user",
            db_password="pass",
            db_name="testdb",
            google_sheet_id="abc123",
            sql_query="-- Get all users\nSELECT * FROM users",
        )
        errors = config.validate()

        # Should not have error about comments
        comment_errors = [e for e in errors if "comment" in e.lower()]
        assert len(comment_errors) == 0


class TestErrorCodesDefined:
    """Verify all new error codes are properly defined."""

    def test_config_service_account_bom_code_exists(self):
        """CONFIG_118 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_SERVICE_ACCOUNT_BOM")
        assert ErrorCode.CONFIG_SERVICE_ACCOUNT_BOM == "CONFIG_118"

    def test_config_sql_file_path_code_exists(self):
        """CONFIG_119 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_SQL_FILE_PATH")
        assert ErrorCode.CONFIG_SQL_FILE_PATH == "CONFIG_119"

    def test_config_worksheet_whitespace_code_exists(self):
        """CONFIG_120 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_WORKSHEET_WHITESPACE")
        assert ErrorCode.CONFIG_WORKSHEET_WHITESPACE == "CONFIG_120"

    def test_config_path_tilde_code_exists(self):
        """CONFIG_121 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_PATH_TILDE")
        assert ErrorCode.CONFIG_PATH_TILDE == "CONFIG_121"

    def test_config_sql_only_comments_code_exists(self):
        """CONFIG_122 should be defined."""
        assert hasattr(ErrorCode, "CONFIG_SQL_ONLY_COMMENTS")
        assert ErrorCode.CONFIG_SQL_ONLY_COMMENTS == "CONFIG_122"
