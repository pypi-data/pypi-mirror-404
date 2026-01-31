"""Tests for sync module."""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from mysql_to_sheets.core.sync import SyncResult, clean_data, clean_value


class TestCleanValue:
    """Tests for clean_value function."""

    def test_clean_value_none(self):
        """Test None becomes empty string."""
        assert clean_value(None) == ""

    def test_clean_value_decimal(self):
        """Test Decimal becomes float."""
        result = clean_value(Decimal("123.45"))
        assert result == 123.45
        assert isinstance(result, float)

    def test_clean_value_datetime(self):
        """Test datetime becomes formatted string."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = clean_value(dt)
        assert result == "2024-01-15 10:30:45"

    def test_clean_value_date(self):
        """Test date becomes formatted string."""
        d = date(2024, 1, 15)
        result = clean_value(d)
        assert result == "2024-01-15"

    def test_clean_value_bytes(self):
        """Test bytes becomes decoded string."""
        result = clean_value(b"hello world")
        assert result == "hello world"

    def test_clean_value_bytes_invalid_utf8(self):
        """Test bytes with invalid UTF-8 uses replacement."""
        result = clean_value(b"\xff\xfe")
        assert isinstance(result, str)

    def test_clean_value_dict(self):
        """Test dict becomes string representation."""
        result = clean_value({"key": "value"})
        assert result == "{'key': 'value'}"

    def test_clean_value_list(self):
        """Test list becomes string representation."""
        result = clean_value([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_clean_value_passthrough(self):
        """Test other types pass through unchanged."""
        assert clean_value("string") == "string"
        assert clean_value(42) == 42
        assert clean_value(3.14) == 3.14
        assert clean_value(True) is True


class TestCleanData:
    """Tests for clean_data function."""

    def test_clean_data_empty(self):
        """Test cleaning empty data."""
        result = clean_data([])
        assert result == []

    def test_clean_data_all_nulls(self):
        """Test cleaning row where every column is None."""
        rows = [[None, None, None, None]]
        result = clean_data(rows)
        assert result == [["", "", "", ""]]

    def test_clean_data_unicode_emoji(self):
        """Test cleaning data with emoji characters."""
        rows = [["Hello \U0001f600", "\u2705 Done", "\u274c Fail"]]
        result = clean_data(rows)
        assert result[0][0] == "Hello \U0001f600"
        assert result[0][1] == "\u2705 Done"

    def test_clean_data_unicode_cjk(self):
        """Test cleaning data with CJK characters."""
        rows = [["\u4f60\u597d\u4e16\u754c", "\u3053\u3093\u306b\u3061\u306f", "\uc548\ub155\ud558\uc138\uc694"]]
        result = clean_data(rows)
        assert result[0][0] == "\u4f60\u597d\u4e16\u754c"
        assert result[0][1] == "\u3053\u3093\u306b\u3061\u306f"
        assert result[0][2] == "\uc548\ub155\ud558\uc138\uc694"

    def test_clean_data_unicode_combining_marks(self):
        """Test cleaning data with combining diacritical marks."""
        rows = [["caf\u00e9", "nai\u0308ve", "re\u0301sume\u0301"]]
        result = clean_data(rows)
        assert result[0][0] == "caf\u00e9"
        assert result[0][1] == "nai\u0308ve"

    def test_clean_data_single_row(self):
        """Test cleaning single row."""
        rows = [[None, Decimal("10.5"), "text"]]
        result = clean_data(rows)
        assert result == [["", 10.5, "text"]]

    def test_clean_data_multiple_rows(self):
        """Test cleaning multiple rows."""
        rows = [
            [1, None, "a"],
            [2, Decimal("20"), "b"],
        ]
        result = clean_data(rows)
        assert result == [
            [1, "", "a"],
            [2, 20.0, "b"],
        ]


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_sync_result_success(self):
        """Test successful sync result."""
        result = SyncResult(
            success=True,
            rows_synced=100,
            columns=5,
            headers=["a", "b", "c", "d", "e"],
            message="Synced successfully",
        )
        assert result.success is True
        assert result.rows_synced == 100
        assert result.error is None

    def test_sync_result_failure(self):
        """Test failed sync result."""
        result = SyncResult(
            success=False,
            error="Connection failed",
            message="Sync failed",
        )
        assert result.success is False
        assert result.error == "Connection failed"

    def test_sync_result_to_dict(self):
        """Test to_dict for API responses."""
        result = SyncResult(
            success=True,
            rows_synced=50,
            columns=3,
            headers=["x", "y", "z"],
            message="Done",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["rows_synced"] == 50
        assert d["columns"] == 3
        assert d["headers"] == ["x", "y", "z"]
        assert d["message"] == "Done"
        assert d["error"] is None


class TestFetchDataEdgeCases:
    """Edge case tests for fetch_data."""

    @patch("mysql_to_sheets.core.sync_legacy.get_connection")
    def test_fetch_data_empty_result(self, mock_get_conn):
        """Test fetch_data returns empty rows when query yields no data."""
        from mysql_to_sheets.core.sync import fetch_data

        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.headers = ["id", "name"]
        mock_result.rows = []
        mock_result.row_count = 0
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value = mock_result
        mock_get_conn.return_value = mock_conn

        config = MagicMock()
        config.db_type = "mysql"
        config.db_host = "localhost"
        config.db_port = 3306
        config.db_user = "test"
        config.db_password = "test"
        config.db_name = "testdb"
        config.db_connect_timeout = 10
        config.db_read_timeout = 300
        config.db_ssl_mode = None
        config.db_ssl_ca = None
        config.db_pool_enabled = False
        config.sql_query = "SELECT id, name FROM empty_table"

        headers, rows = fetch_data(config)
        assert headers == ["id", "name"]
        assert rows == []

    @patch("mysql_to_sheets.core.sync_legacy.get_connection")
    def test_fetch_data_query_timeout(self, mock_get_conn):
        """Test fetch_data wraps timeout as DatabaseError."""
        from mysql_to_sheets.core.exceptions import DatabaseError
        from mysql_to_sheets.core.sync import fetch_data

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = OSError("Connection timed out")
        mock_get_conn.return_value = mock_conn

        config = MagicMock()
        config.db_type = "mysql"
        config.db_host = "localhost"
        config.db_port = 3306
        config.db_user = "test"
        config.db_password = "test"
        config.db_name = "testdb"
        config.db_connect_timeout = 10
        config.db_read_timeout = 300
        config.db_ssl_mode = None
        config.db_ssl_ca = None
        config.db_pool_enabled = False
        config.sql_query = "SELECT * FROM slow_table"

        import pytest

        with pytest.raises(DatabaseError, match="Unexpected error fetching data"):
            fetch_data(config)
