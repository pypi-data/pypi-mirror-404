"""Tests for the reverse_sync module."""

from unittest.mock import Mock, patch

from mysql_to_sheets.core.config import Config
from mysql_to_sheets.core.database import WriteResult
from mysql_to_sheets.core.reverse_sync import (
    ConflictMode,
    ReverseSyncConfig,
    ReverseSyncResult,
    ReverseSyncService,
    convert_value,
    prepare_rows_for_db,
    run_reverse_sync,
)


class TestConflictMode:
    """Tests for ConflictMode enum."""

    def test_conflict_mode_values(self):
        """Test conflict mode enum values."""
        assert ConflictMode.OVERWRITE.value == "overwrite"
        assert ConflictMode.SKIP.value == "skip"
        assert ConflictMode.ERROR.value == "error"

    def test_conflict_mode_from_string(self):
        """Test creating conflict mode from string."""
        assert ConflictMode("overwrite") == ConflictMode.OVERWRITE
        assert ConflictMode("skip") == ConflictMode.SKIP
        assert ConflictMode("error") == ConflictMode.ERROR


class TestReverseSyncConfig:
    """Tests for ReverseSyncConfig dataclass."""

    def test_default_values(self):
        """Test default config values."""
        config = ReverseSyncConfig(table_name="users")

        assert config.table_name == "users"
        assert config.key_columns == []
        assert config.conflict_mode == ConflictMode.OVERWRITE
        assert config.update_columns is None
        assert config.batch_size == 1000
        assert config.column_mapping is None
        assert config.skip_header is True
        assert config.sheet_range is None

    def test_custom_values(self):
        """Test custom config values."""
        config = ReverseSyncConfig(
            table_name="orders",
            key_columns=["id"],
            conflict_mode=ConflictMode.SKIP,
            update_columns=["status", "updated_at"],
            batch_size=500,
            column_mapping={"Order ID": "id", "Status": "status"},
            skip_header=False,
            sheet_range="A1:E100",
        )

        assert config.table_name == "orders"
        assert config.key_columns == ["id"]
        assert config.conflict_mode == ConflictMode.SKIP
        assert config.update_columns == ["status", "updated_at"]
        assert config.batch_size == 500
        assert config.column_mapping == {"Order ID": "id", "Status": "status"}
        assert config.skip_header is False
        assert config.sheet_range == "A1:E100"


class TestReverseSyncResult:
    """Tests for ReverseSyncResult dataclass."""

    def test_default_values(self):
        """Test default result values."""
        result = ReverseSyncResult(success=True)

        assert result.success is True
        assert result.rows_processed == 0
        assert result.rows_inserted == 0
        assert result.rows_updated == 0
        assert result.rows_skipped == 0
        assert result.message == ""
        assert result.error is None

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = ReverseSyncResult(
            success=True,
            rows_processed=100,
            rows_inserted=80,
            rows_updated=15,
            rows_skipped=5,
            message="Sync completed",
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["rows_processed"] == 100
        assert d["rows_inserted"] == 80
        assert d["rows_updated"] == 15
        assert d["rows_skipped"] == 5
        assert d["message"] == "Sync completed"
        assert d["error"] is None

    def test_to_dict_with_error(self):
        """Test to_dict with error."""
        result = ReverseSyncResult(
            success=False,
            error="Database connection failed",
        )

        d = result.to_dict()

        assert d["success"] is False
        assert d["error"] == "Database connection failed"


class TestConvertValue:
    """Tests for convert_value function."""

    def test_convert_none(self):
        """Test converting None value."""
        assert convert_value(None) is None

    def test_convert_empty_string(self):
        """Test converting empty string."""
        assert convert_value("") is None

    def test_convert_integer_string(self):
        """Test converting integer string."""
        assert convert_value("123") == 123
        assert convert_value("-456") == -456

    def test_convert_float_string(self):
        """Test converting float string."""
        assert convert_value("123.45") == 123.45
        assert convert_value("1e5") == 100000.0

    def test_convert_boolean_true(self):
        """Test converting true boolean strings."""
        assert convert_value("true") is True
        assert convert_value("True") is True
        assert convert_value("yes") is True
        assert convert_value("1") == 1  # Could be int or bool

    def test_convert_boolean_false(self):
        """Test converting false boolean strings."""
        assert convert_value("false") is False
        assert convert_value("False") is False
        assert convert_value("no") is False

    def test_convert_date_string(self):
        """Test converting date string."""
        result = convert_value("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_convert_datetime_string(self):
        """Test converting datetime string."""
        result = convert_value("2024-01-15T10:30:00")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_convert_regular_string(self):
        """Test converting regular string (no conversion)."""
        assert convert_value("hello world") == "hello world"
        assert convert_value("  spaced  ") == "spaced"

    def test_convert_already_typed(self):
        """Test passing already typed values."""
        assert convert_value(123) == 123
        assert convert_value(123.45) == 123.45
        assert convert_value(True) is True


class TestPrepareRowsForDb:
    """Tests for prepare_rows_for_db function."""

    def test_basic_preparation(self):
        """Test basic row preparation."""
        headers = ["name", "age"]
        rows = [["Alice", "30"], ["Bob", "25"]]
        config = ReverseSyncConfig(table_name="users")

        db_columns, prepared = prepare_rows_for_db(headers, rows, config)

        assert db_columns == ["name", "age"]
        assert len(prepared) == 2
        assert prepared[0] == ["Alice", 30]
        assert prepared[1] == ["Bob", 25]

    def test_with_column_mapping(self):
        """Test preparation with column mapping."""
        headers = ["Full Name", "Years"]
        rows = [["Alice", "30"]]
        config = ReverseSyncConfig(
            table_name="users",
            column_mapping={"Full Name": "name", "Years": "age"},
        )

        db_columns, prepared = prepare_rows_for_db(headers, rows, config)

        assert db_columns == ["name", "age"]


class TestRunReverseSync:
    """Tests for run_reverse_sync function."""

    @patch("mysql_to_sheets.core.reverse_sync.fetch_sheet_data")
    @patch("mysql_to_sheets.core.reverse_sync.push_to_database")
    def test_successful_sync(self, mock_push, mock_fetch):
        """Test successful reverse sync."""
        mock_fetch.return_value = (
            ["id", "name"],
            [["1", "Alice"], ["2", "Bob"]],
        )
        mock_push.return_value = WriteResult(
            rows_affected=2,
            rows_inserted=2,
        )

        config = Mock(spec=Config)
        config.db_type = "mysql"
        config.db_host = "localhost"
        config.db_port = 3306
        config.db_user = "user"
        config.db_password = "pass"
        config.db_name = "testdb"
        config.db_connect_timeout = 10
        config.db_read_timeout = 300
        config.db_ssl_mode = ""
        config.db_ssl_ca = ""
        config.google_sheet_id = "abc123"
        config.google_worksheet_name = "Sheet1"
        config.service_account_file = "./service_account.json"
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        reverse_config = ReverseSyncConfig(
            table_name="users",
            key_columns=["id"],
        )

        result = run_reverse_sync(
            config=config,
            reverse_config=reverse_config,
            dry_run=False,
        )

        assert result.success is True
        assert result.rows_processed == 2
        mock_fetch.assert_called_once()
        mock_push.assert_called_once()

    @patch("mysql_to_sheets.core.reverse_sync.fetch_sheet_data")
    def test_dry_run(self, mock_fetch):
        """Test dry run mode."""
        mock_fetch.return_value = (
            ["id", "name"],
            [["1", "Alice"], ["2", "Bob"]],
        )

        config = Mock(spec=Config)
        config.db_type = "mysql"
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        reverse_config = ReverseSyncConfig(
            table_name="users",
            key_columns=["id"],
        )

        result = run_reverse_sync(
            config=config,
            reverse_config=reverse_config,
            dry_run=True,
        )

        assert result.success is True
        assert result.rows_processed == 2
        assert "Dry run" in result.message

    @patch("mysql_to_sheets.core.reverse_sync.fetch_sheet_data")
    def test_empty_dataset(self, mock_fetch):
        """Test sync with empty dataset."""
        mock_fetch.return_value = ([], [])

        config = Mock(spec=Config)
        config.db_type = "mysql"
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        reverse_config = ReverseSyncConfig(table_name="users")

        result = run_reverse_sync(
            config=config,
            reverse_config=reverse_config,
        )

        assert result.success is True
        assert result.rows_processed == 0
        assert "empty dataset" in result.message.lower()


class TestReverseSyncService:
    """Tests for ReverseSyncService class."""

    @patch("mysql_to_sheets.core.reverse_sync.run_reverse_sync")
    def test_sync_method(self, mock_run):
        """Test sync method."""
        mock_run.return_value = ReverseSyncResult(
            success=True,
            rows_processed=10,
        )

        config = Mock(spec=Config)
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        service = ReverseSyncService(config=config)
        reverse_config = ReverseSyncConfig(table_name="users")

        result = service.sync(reverse_config)

        assert result.success is True
        mock_run.assert_called_once()

    @patch("mysql_to_sheets.core.reverse_sync.run_reverse_sync")
    def test_sync_simple_method(self, mock_run):
        """Test sync_simple method."""
        mock_run.return_value = ReverseSyncResult(
            success=True,
            rows_processed=10,
        )

        config = Mock(spec=Config)
        config.log_level = "INFO"
        config.log_file = "./test.log"
        config.log_max_bytes = 10485760
        config.log_backup_count = 5

        service = ReverseSyncService(config=config)
        result = service.sync_simple(
            table_name="users",
            key_columns=["id"],
            conflict_mode="overwrite",
        )

        assert result.success is True
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["table_name"] == "users"
        assert call_kwargs["key_columns"] == ["id"]
        assert call_kwargs["conflict_mode"] == "overwrite"
