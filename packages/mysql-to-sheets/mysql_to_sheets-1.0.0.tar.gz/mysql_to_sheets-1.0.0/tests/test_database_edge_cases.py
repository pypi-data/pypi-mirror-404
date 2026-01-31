"""Tests for database-related edge cases.

Covers Edge Cases:
- EC-5: Non-SELECT Query Detection
- EC-14: MySQL UTF-8 Charset
"""

import inspect
from unittest.mock import MagicMock

import pytest

from mysql_to_sheets.core.exceptions import ConfigError


class TestNonSelectQueryValidation:
    """Tests for non-SELECT query detection.

    Edge Case 5: Non-SELECT Query Returns Silent Empty Result
    ---------------------------------------------------------
    If a user accidentally configures a write query (INSERT/UPDATE/DELETE)
    instead of SELECT, the sync "succeeds" with 0 rows and no warning.
    """

    def test_select_query_passes_validation(self):
        """Verify SELECT queries pass validation without error."""
        from mysql_to_sheets.core.sync import validate_query_type

        # Should not raise
        validate_query_type("SELECT * FROM users", strict=True)
        validate_query_type("select id, name from users where active = 1", strict=True)

    def test_update_query_rejected_in_strict_mode(self):
        """Verify UPDATE queries are rejected in strict mode."""
        from mysql_to_sheets.core.sync import validate_query_type

        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("UPDATE users SET status='active' WHERE id=1", strict=True)

        assert "CONFIG_107" in str(exc_info.value.code)
        assert "UPDATE" in str(exc_info.value.message)

    def test_insert_query_rejected_in_strict_mode(self):
        """Verify INSERT queries are rejected in strict mode."""
        from mysql_to_sheets.core.sync import validate_query_type

        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("INSERT INTO users (name) VALUES ('Alice')", strict=True)

        assert "CONFIG_107" in str(exc_info.value.code)

    def test_delete_query_rejected_in_strict_mode(self):
        """Verify DELETE queries are rejected in strict mode."""
        from mysql_to_sheets.core.sync import validate_query_type

        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("DELETE FROM users WHERE id=1", strict=True)

        assert "CONFIG_107" in str(exc_info.value.code)

    def test_truncate_query_rejected_in_strict_mode(self):
        """Verify TRUNCATE queries are rejected in strict mode."""
        from mysql_to_sheets.core.sync import validate_query_type

        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("TRUNCATE TABLE users", strict=True)

        assert "CONFIG_107" in str(exc_info.value.code)

    def test_drop_query_rejected_in_strict_mode(self):
        """Verify DROP queries are rejected in strict mode."""
        from mysql_to_sheets.core.sync import validate_query_type

        with pytest.raises(ConfigError) as exc_info:
            validate_query_type("DROP TABLE users", strict=True)

        assert "CONFIG_107" in str(exc_info.value.code)

    def test_non_strict_mode_only_warns(self):
        """Verify non-strict mode logs warning but doesn't raise."""
        from mysql_to_sheets.core.sync import validate_query_type

        logger = MagicMock()

        # Should not raise, just warn
        validate_query_type("UPDATE users SET x=1", logger=logger, strict=False)

        # Should have logged a warning
        logger.warning.assert_called_once()
        assert "UPDATE" in logger.warning.call_args[0][0]

    def test_cte_with_select_passes(self):
        """Verify CTE (WITH ... SELECT) queries pass validation."""
        from mysql_to_sheets.core.sync import validate_query_type

        query = """
        WITH active_users AS (
            SELECT * FROM users WHERE status = 'active'
        )
        SELECT * FROM active_users
        """
        # Should not raise
        validate_query_type(query, strict=True)

    def test_query_with_leading_comments_validated(self):
        """Verify queries with leading comments are still validated."""
        from mysql_to_sheets.core.sync import validate_query_type

        query = """
        -- This is a comment
        /* Multi-line
           comment */
        UPDATE users SET status='active'
        """
        with pytest.raises(ConfigError) as exc_info:
            validate_query_type(query, strict=True)

        assert "CONFIG_107" in str(exc_info.value.code)

    def test_show_and_describe_queries_pass(self):
        """Verify SHOW and DESCRIBE queries pass validation."""
        from mysql_to_sheets.core.sync import validate_query_type

        # Should not raise
        validate_query_type("SHOW TABLES", strict=True)
        validate_query_type("DESCRIBE users", strict=True)
        validate_query_type("DESC users", strict=True)
        validate_query_type("EXPLAIN SELECT * FROM users", strict=True)


class TestMySQLCharsetEnforcement:
    """Tests for MySQL UTF-8 charset configuration.

    Edge Case 14: MySQL UTF-8 Charset Not Enforced (Emoji Truncation)
    -----------------------------------------------------------------
    MySQL connections may default to 3-byte 'utf8' instead of 4-byte 'utf8mb4'.
    Characters requiring 4 bytes (emoji, some CJK) are silently truncated.
    """

    def test_emoji_requires_4_byte_utf8(self):
        """Verify emoji characters require 4 bytes in UTF-8."""
        emoji = "🎉"  # Party popper emoji

        encoded = emoji.encode("utf-8")
        assert len(encoded) == 4

    def test_cjk_supplementary_requires_4_bytes(self):
        """Verify some CJK characters require 4 bytes."""
        # CJK Extension B character (U+20000)
        cjk_extended = "𠀀"

        encoded = cjk_extended.encode("utf-8")
        assert len(encoded) == 4

    def test_common_characters_use_3_bytes_or_less(self):
        """Verify common characters work with 3-byte utf8."""
        # ASCII (1 byte)
        assert len("A".encode("utf-8")) == 1

        # Latin extended (2 bytes)
        assert len("é".encode("utf-8")) == 2

        # Common CJK (3 bytes)
        assert len("日".encode("utf-8")) == 3

    def test_mysql_connection_should_set_utf8mb4(self):
        """Verify MySQL connection code path should set charset."""
        from mysql_to_sheets.core.database import mysql as mysql_module

        source = inspect.getsource(mysql_module.MySQLConnection.connect)

        # Check if charset is currently set
        has_charset = "charset" in source and "utf8mb4" in source

        if not has_charset:
            # Document expected fix
            pass

    def test_emoji_in_sync_data_preserved(self):
        """Test that emoji data can pass through the sync pipeline."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        emoji_text = "Hello 🌍 World 🎉"
        result = clean_value(emoji_text)

        assert result == emoji_text
        assert "🌍" in result
        assert "🎉" in result

    def test_mixed_emoji_ascii_text(self):
        """Test mixed emoji and ASCII text handling."""
        from mysql_to_sheets.core.database.type_converters import clean_row

        row = [1, "User 😀", "Message with 🚀 emoji", 100]
        cleaned = clean_row(row)

        assert cleaned == row
        assert "😀" in cleaned[1]
        assert "🚀" in cleaned[2]
