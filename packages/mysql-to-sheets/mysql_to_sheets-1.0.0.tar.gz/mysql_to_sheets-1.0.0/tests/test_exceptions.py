"""Tests for custom exceptions."""

from mysql_to_sheets.core.exceptions import (
    ConfigError,
    DatabaseError,
    SheetsError,
    SyncError,
)


class TestSyncError:
    """Tests for base SyncError."""

    def test_sync_error_message(self):
        """Test SyncError stores message."""
        error = SyncError("Test error message")
        assert error.message == "Test error message"
        assert str(error) == "Test error message"

    def test_sync_error_details(self):
        """Test SyncError stores details."""
        error = SyncError("Error", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_sync_error_to_dict(self):
        """Test to_dict for API responses."""
        error = SyncError("Error message", details={"foo": "bar"})
        result = error.to_dict()
        assert result["error"] == "SyncError"
        assert result["message"] == "Error message"
        assert result["details"] == {"foo": "bar"}


class TestConfigError:
    """Tests for ConfigError."""

    def test_config_error_missing_fields(self):
        """Test ConfigError with missing fields."""
        error = ConfigError("Invalid config", missing_fields=["DB_USER", "DB_PASSWORD"])
        assert error.message == "Invalid config"
        assert error.missing_fields == ["DB_USER", "DB_PASSWORD"]
        assert error.details["missing_fields"] == ["DB_USER", "DB_PASSWORD"]

    def test_config_error_to_dict(self):
        """Test ConfigError to_dict includes missing fields."""
        error = ConfigError("Invalid", missing_fields=["FIELD1"])
        result = error.to_dict()
        assert result["error"] == "ConfigError"
        assert "FIELD1" in result["details"]["missing_fields"]


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_database_error_with_host(self):
        """Test DatabaseError captures host info."""
        error = DatabaseError(
            "Connection failed",
            host="localhost",
            database="testdb",
        )
        assert error.host == "localhost"
        assert error.database == "testdb"
        assert error.details["host"] == "localhost"
        assert error.details["database"] == "testdb"

    def test_database_error_with_original(self):
        """Test DatabaseError captures original exception."""
        original = Exception("Original error")
        error = DatabaseError(
            "Wrapped error",
            original_error=original,
        )
        assert error.original_error is original
        assert "Original error" in error.details["original_error"]


class TestSheetsError:
    """Tests for SheetsError."""

    def test_sheets_error_with_sheet_info(self):
        """Test SheetsError captures sheet info."""
        error = SheetsError(
            "Sheet not found",
            sheet_id="abc123",
            worksheet_name="Sheet1",
        )
        assert error.sheet_id == "abc123"
        assert error.worksheet_name == "Sheet1"
        assert error.details["sheet_id"] == "abc123"
        assert error.details["worksheet_name"] == "Sheet1"

    def test_sheets_error_to_dict(self):
        """Test SheetsError to_dict for API responses."""
        error = SheetsError("API error", sheet_id="xyz")
        result = error.to_dict()
        assert result["error"] == "SheetsError"
        assert result["details"]["sheet_id"] == "xyz"
