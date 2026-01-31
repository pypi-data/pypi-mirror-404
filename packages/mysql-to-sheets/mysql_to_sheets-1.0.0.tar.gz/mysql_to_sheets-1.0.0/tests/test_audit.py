"""Unit tests for audit logging feature."""

import io
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from mysql_to_sheets.core.audit import (
    VALID_AUDIT_ACTIONS,
    AuditAction,
    AuditContext,
    clear_request_context,
    get_request_context,
    log_action,
    log_auth_event,
    log_management_event,
    log_sync_event,
    sanitize_sql_query,
    set_request_context,
    update_request_context,
)
from mysql_to_sheets.core.audit_export import (
    ExportOptions,
    export_audit_logs,
    export_to_cef,
    export_to_csv,
    export_to_json,
    export_to_jsonl,
    get_supported_formats,
)
from mysql_to_sheets.core.audit_retention import (
    CleanupResult,
    RetentionStats,
    cleanup_old_logs,
    get_retention_stats,
)
from mysql_to_sheets.models.audit_logs import (
    AuditLog,
    get_audit_log_repository,
    reset_audit_log_repository,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    reset_audit_log_repository()
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def audit_repo(temp_db_path):
    """Create a fresh audit log repository."""
    reset_audit_log_repository()
    return get_audit_log_repository(temp_db_path)


@pytest.fixture
def sample_audit_log():
    """Create a sample audit log entry."""
    return AuditLog(
        action="sync.completed",
        resource_type="sync",
        organization_id=1,
        user_id=1,
        resource_id="sync-123",
        source_ip="192.168.1.1",
        user_agent="Mozilla/5.0",
        query_executed="SELECT * FROM users",
        rows_affected=100,
        metadata={"config_name": "daily_sync"},
    )


class TestAuditLogDataclass:
    """Tests for AuditLog dataclass."""

    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        log = AuditLog(
            action="sync.completed",
            resource_type="sync",
            organization_id=1,
        )
        assert log.action == "sync.completed"
        assert log.resource_type == "sync"
        assert log.organization_id == 1
        assert log.id is None
        assert log.timestamp is None

    def test_to_dict(self, sample_audit_log):
        """Test converting audit log to dictionary."""
        sample_audit_log.id = 1
        sample_audit_log.timestamp = datetime(2024, 1, 15, 10, 30, 0)

        result = sample_audit_log.to_dict()

        assert result["id"] == 1
        assert result["action"] == "sync.completed"
        assert result["resource_type"] == "sync"
        assert result["organization_id"] == 1
        assert result["user_id"] == 1
        assert result["resource_id"] == "sync-123"
        assert result["rows_affected"] == 100
        assert result["metadata"] == {"config_name": "daily_sync"}
        assert "2024-01-15" in result["timestamp"]

    def test_from_dict(self):
        """Test creating audit log from dictionary."""
        data = {
            "id": 1,
            "timestamp": "2024-01-15T10:30:00",
            "action": "auth.login",
            "resource_type": "auth",
            "organization_id": 1,
            "user_id": 5,
            "source_ip": "10.0.0.1",
        }

        log = AuditLog.from_dict(data)

        assert log.id == 1
        assert log.action == "auth.login"
        assert log.resource_type == "auth"
        assert log.organization_id == 1
        assert log.user_id == 5
        assert log.source_ip == "10.0.0.1"
        assert log.timestamp == datetime(2024, 1, 15, 10, 30, 0)


class TestAuditLogRepository:
    """Tests for AuditLogRepository."""

    def test_add_audit_log(self, audit_repo, sample_audit_log):
        """Test adding an audit log entry."""
        result = audit_repo.add(sample_audit_log)

        assert result.id is not None
        assert result.timestamp is not None
        assert result.action == "sync.completed"

    def test_get_all(self, audit_repo, sample_audit_log):
        """Test retrieving all audit logs."""
        audit_repo.add(sample_audit_log)
        audit_repo.add(
            AuditLog(
                action="auth.login",
                resource_type="auth",
                organization_id=1,
            )
        )

        logs = audit_repo.get_all(organization_id=1)

        assert len(logs) == 2

    def test_get_all_with_filters(self, audit_repo):
        """Test filtering audit logs."""
        # Add logs with different actions
        audit_repo.add(
            AuditLog(
                action="sync.completed",
                resource_type="sync",
                organization_id=1,
            )
        )
        audit_repo.add(
            AuditLog(
                action="sync.failed",
                resource_type="sync",
                organization_id=1,
            )
        )
        audit_repo.add(
            AuditLog(
                action="auth.login",
                resource_type="auth",
                organization_id=1,
            )
        )

        # Filter by action
        sync_completed = audit_repo.get_all(organization_id=1, action="sync.completed")
        assert len(sync_completed) == 1
        assert sync_completed[0].action == "sync.completed"

        # Filter by resource type
        auth_logs = audit_repo.get_all(organization_id=1, resource_type="auth")
        assert len(auth_logs) == 1

    def test_multi_tenant_isolation(self, audit_repo):
        """Test that organizations are isolated."""
        audit_repo.add(
            AuditLog(
                action="sync.completed",
                resource_type="sync",
                organization_id=1,
            )
        )
        audit_repo.add(
            AuditLog(
                action="sync.completed",
                resource_type="sync",
                organization_id=2,
            )
        )

        org1_logs = audit_repo.get_all(organization_id=1)
        org2_logs = audit_repo.get_all(organization_id=2)

        assert len(org1_logs) == 1
        assert len(org2_logs) == 1
        assert org1_logs[0].organization_id == 1
        assert org2_logs[0].organization_id == 2

    def test_count(self, audit_repo):
        """Test counting audit logs."""
        for i in range(5):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                )
            )

        count = audit_repo.count(organization_id=1)
        assert count == 5

    def test_delete_before(self, audit_repo, temp_db_path):
        """Test deleting old logs."""
        # Add logs (they will have current timestamp)
        for i in range(3):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                )
            )

        # Delete logs before tomorrow (should delete all)
        cutoff = datetime.now(timezone.utc) + timedelta(days=1)
        deleted = audit_repo.delete_before(cutoff, organization_id=1)

        assert deleted == 3
        assert audit_repo.count(organization_id=1) == 0

    def test_get_stats(self, audit_repo):
        """Test getting statistics."""
        audit_repo.add(AuditLog(action="sync.completed", resource_type="sync", organization_id=1))
        audit_repo.add(AuditLog(action="sync.failed", resource_type="sync", organization_id=1))
        audit_repo.add(AuditLog(action="auth.login", resource_type="auth", organization_id=1))

        stats = audit_repo.get_stats(organization_id=1)

        assert stats["total_logs"] == 3
        assert stats["by_action"]["sync.completed"] == 1
        assert stats["by_action"]["sync.failed"] == 1
        assert stats["by_resource_type"]["sync"] == 2
        assert stats["by_resource_type"]["auth"] == 1

    def test_stream_logs(self, audit_repo):
        """Test streaming logs in batches."""
        # Add 5 logs
        for i in range(5):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                )
            )

        # Stream with batch size of 2
        batches = list(audit_repo.stream_logs(organization_id=1, batch_size=2))

        assert len(batches) == 3  # 2, 2, 1
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1


class TestSanitizeSqlQuery:
    """Tests for SQL query sanitization."""

    def test_sanitize_string_values(self):
        """Test sanitizing quoted string values."""
        query = "SELECT * FROM users WHERE name = 'John Doe'"
        result = sanitize_sql_query(query)
        assert "'John Doe'" not in result
        assert "'?'" in result

    def test_sanitize_double_quoted_values(self):
        """Test sanitizing double-quoted values."""
        query = 'SELECT * FROM users WHERE name = "John"'
        result = sanitize_sql_query(query)
        assert '"John"' not in result
        assert '"?"' in result

    def test_sanitize_numeric_values(self):
        """Test sanitizing numeric values."""
        query = "SELECT * FROM users WHERE id = 123"
        result = sanitize_sql_query(query)
        assert "= 123" not in result
        assert "= ?" in result

    def test_sanitize_in_clause(self):
        """Test sanitizing IN clause."""
        query = "SELECT * FROM users WHERE id IN (1, 2, 3)"
        result = sanitize_sql_query(query)
        assert "(1, 2, 3)" not in result
        assert "IN (?)" in result

    def test_sanitize_limit_offset(self):
        """Test sanitizing LIMIT and OFFSET."""
        query = "SELECT * FROM users LIMIT 100 OFFSET 50"
        result = sanitize_sql_query(query)
        assert "LIMIT 100" not in result
        assert "OFFSET 50" not in result
        assert "LIMIT ?" in result
        assert "OFFSET ?" in result

    def test_sanitize_none(self):
        """Test that None input returns None."""
        assert sanitize_sql_query(None) is None


class TestRequestContext:
    """Tests for request context management."""

    def setup_method(self):
        """Clear context before each test."""
        clear_request_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_request_context()

    def test_set_and_get_context(self):
        """Test setting and getting request context."""
        set_request_context(
            source_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
            user_id=1,
            organization_id=1,
        )

        ctx = get_request_context()

        assert ctx is not None
        assert ctx.source_ip == "192.168.1.1"
        assert ctx.user_agent == "TestAgent/1.0"
        assert ctx.user_id == 1
        assert ctx.organization_id == 1

    def test_clear_context(self):
        """Test clearing request context."""
        set_request_context(source_ip="192.168.1.1")
        clear_request_context()

        ctx = get_request_context()
        assert ctx is None

    def test_update_context(self):
        """Test updating request context."""
        set_request_context(source_ip="192.168.1.1")
        update_request_context(user_id=5, organization_id=2)

        ctx = get_request_context()

        assert ctx.source_ip == "192.168.1.1"
        assert ctx.user_id == 5
        assert ctx.organization_id == 2

    def test_audit_context_manager(self):
        """Test AuditContext context manager."""
        with AuditContext(source_ip="10.0.0.1", user_id=1):
            ctx = get_request_context()
            assert ctx.source_ip == "10.0.0.1"
            assert ctx.user_id == 1

        # Context should be cleared after exiting
        assert get_request_context() is None


class TestLogFunctions:
    """Tests for audit logging functions."""

    def test_log_action(self, audit_repo, temp_db_path):
        """Test log_action function."""
        log_action(
            action=AuditAction.SYNC_COMPLETED,
            resource_type="sync",
            organization_id=1,
            db_path=temp_db_path,
            rows_affected=100,
        )

        logs = audit_repo.get_all(organization_id=1)
        assert len(logs) == 1
        assert logs[0].action == "sync.completed"
        assert logs[0].rows_affected == 100

    def test_log_sync_event(self, audit_repo, temp_db_path):
        """Test log_sync_event convenience function."""
        log_sync_event(
            event="completed",
            organization_id=1,
            db_path=temp_db_path,
            sync_id="sync-123",
            config_name="daily",
            rows_synced=50,
            duration_seconds=5.5,
        )

        logs = audit_repo.get_all(organization_id=1)
        assert len(logs) == 1
        assert logs[0].action == "sync.completed"
        assert logs[0].rows_affected == 50
        assert logs[0].metadata["duration_seconds"] == "5.5"

    def test_log_auth_event(self, audit_repo, temp_db_path):
        """Test log_auth_event convenience function."""
        log_auth_event(
            event="login",
            organization_id=1,
            db_path=temp_db_path,
            user_id=5,
            email="test@example.com",
            success=True,
        )

        logs = audit_repo.get_all(organization_id=1)
        assert len(logs) == 1
        assert logs[0].action == "auth.login"
        assert logs[0].metadata["email"] == "test@example.com"

    def test_log_management_event(self, audit_repo, temp_db_path):
        """Test log_management_event convenience function."""
        log_management_event(
            action=AuditAction.USER_CREATED,
            resource_type="user",
            resource_id=10,
            organization_id=1,
            db_path=temp_db_path,
            changes={"display_name": "New Name"},
        )

        logs = audit_repo.get_all(organization_id=1)
        assert len(logs) == 1
        assert logs[0].action == "user.created"
        assert logs[0].resource_id == "10"


class TestAuditAction:
    """Tests for AuditAction enum."""

    def test_all_actions_in_valid_list(self):
        """Test that all enum values are in VALID_AUDIT_ACTIONS."""
        for action in AuditAction:
            assert action.value in VALID_AUDIT_ACTIONS

    def test_action_format(self):
        """Test action format is resource.verb."""
        for action in AuditAction:
            assert "." in action.value
            parts = action.value.split(".")
            assert len(parts) == 2


class TestAuditExport:
    """Tests for audit log export."""

    @pytest.fixture
    def populated_repo(self, audit_repo, temp_db_path):
        """Create repository with sample data."""
        for i in range(3):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                    user_id=1,
                    rows_affected=100 + i,
                )
            )
        return temp_db_path

    def test_export_to_csv(self, populated_repo, audit_repo):
        """Test CSV export."""
        output = io.StringIO()
        result = export_to_csv(
            organization_id=1,
            output=output,
            db_path=populated_repo,
        )

        assert result.record_count == 3
        assert result.format == "csv"

        csv_content = output.getvalue()
        assert "id,timestamp,user_id" in csv_content
        assert "sync.completed" in csv_content

    def test_export_to_json(self, populated_repo, audit_repo):
        """Test JSON export."""
        output = io.StringIO()
        result = export_to_json(
            organization_id=1,
            output=output,
            db_path=populated_repo,
        )

        assert result.record_count == 3
        assert result.format == "json"

        data = json.loads(output.getvalue())
        assert len(data) == 3
        assert data[0]["action"] == "sync.completed"

    def test_export_to_jsonl(self, populated_repo, audit_repo):
        """Test JSON Lines export."""
        output = io.StringIO()
        result = export_to_jsonl(
            organization_id=1,
            output=output,
            db_path=populated_repo,
        )

        assert result.record_count == 3
        assert result.format == "jsonl"

        lines = output.getvalue().strip().split("\n")
        assert len(lines) == 3
        first_record = json.loads(lines[0])
        assert first_record["action"] == "sync.completed"

    def test_export_to_cef(self, populated_repo, audit_repo):
        """Test CEF export."""
        output = io.StringIO()
        result = export_to_cef(
            organization_id=1,
            output=output,
            db_path=populated_repo,
        )

        assert result.record_count == 3
        assert result.format == "cef"

        lines = output.getvalue().strip().split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("CEF:0|MySQLToSheets|")

    def test_export_with_filters(self, populated_repo, audit_repo, temp_db_path):
        """Test export with filters."""
        # Add an auth log
        audit_repo.add(
            AuditLog(
                action="auth.login",
                resource_type="auth",
                organization_id=1,
            )
        )

        output = io.StringIO()
        options = ExportOptions(action="sync.completed")
        result = export_to_csv(
            organization_id=1,
            output=output,
            db_path=populated_repo,
            options=options,
        )

        assert result.record_count == 3  # Only sync logs

    def test_export_audit_logs_dispatcher(self, populated_repo, audit_repo):
        """Test the export_audit_logs dispatcher function."""
        for fmt in ["csv", "json", "jsonl", "cef"]:
            output = io.StringIO()
            result = export_audit_logs(
                organization_id=1,
                output=output,
                db_path=populated_repo,
                format=fmt,
            )
            assert result.format == fmt
            assert result.record_count == 3

    def test_export_invalid_format(self, populated_repo):
        """Test export with invalid format raises error."""
        output = io.StringIO()
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_audit_logs(
                organization_id=1,
                output=output,
                db_path=populated_repo,
                format="xml",
            )

    def test_get_supported_formats(self):
        """Test getting supported formats list."""
        formats = get_supported_formats()
        assert "csv" in formats
        assert "json" in formats
        assert "jsonl" in formats
        assert "cef" in formats


class TestAuditRetention:
    """Tests for audit log retention management."""

    def test_cleanup_old_logs_dry_run(self, audit_repo, temp_db_path):
        """Test cleanup in dry run mode."""
        # Add some logs
        for i in range(3):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                )
            )

        # Use retention of 1 day (logs just created won't be deleted)
        result = cleanup_old_logs(
            retention_days=1,
            db_path=temp_db_path,
            organization_id=1,
            dry_run=True,
        )

        assert result.dry_run is True
        # Logs should still exist (they're too recent to delete)
        assert audit_repo.count(organization_id=1) == 3

    def test_cleanup_old_logs_real(self, audit_repo, temp_db_path):
        """Test actual cleanup."""
        # Add logs
        for i in range(3):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                )
            )

        # Use 1 day retention - logs just created won't be deleted
        result = cleanup_old_logs(
            retention_days=1,
            db_path=temp_db_path,
            organization_id=1,
            dry_run=False,
        )

        assert result.dry_run is False
        # Recent logs won't be deleted (cutoff is 1 day ago)
        assert audit_repo.count(organization_id=1) == 3

    def test_cleanup_invalid_retention(self, temp_db_path):
        """Test that invalid retention raises error."""
        with pytest.raises(ValueError, match="retention_days must be at least 1"):
            cleanup_old_logs(
                retention_days=0,
                db_path=temp_db_path,
            )

    def test_get_retention_stats(self, audit_repo, temp_db_path):
        """Test getting retention statistics."""
        for i in range(5):
            audit_repo.add(
                AuditLog(
                    action="sync.completed",
                    resource_type="sync",
                    organization_id=1,
                )
            )

        stats = get_retention_stats(
            organization_id=1,
            db_path=temp_db_path,
            retention_days=90,
        )

        assert isinstance(stats, RetentionStats)
        assert stats.total_logs == 5
        assert stats.retention_days == 90
        assert stats.oldest_log is not None
        assert stats.newest_log is not None

    def test_cleanup_result_to_dict(self):
        """Test CleanupResult serialization."""
        result = CleanupResult(
            deleted_count=10,
            cutoff_date=datetime(2024, 1, 1),
            dry_run=False,
            organization_id=1,
        )

        data = result.to_dict()

        assert data["deleted_count"] == 10
        assert "2024-01-01" in data["cutoff_date"]
        assert data["dry_run"] is False
        assert data["organization_id"] == 1


class TestIntegration:
    """Integration tests for the full audit flow."""

    def test_full_audit_flow(self, temp_db_path):
        """Test complete audit logging workflow."""
        reset_audit_log_repository()

        # 1. Set up request context
        with AuditContext(source_ip="192.168.1.100", user_agent="TestBrowser/1.0"):
            # 2. Log sync events
            log_sync_event(
                event="started",
                organization_id=1,
                db_path=temp_db_path,
                sync_id="sync-001",
                source="api",
            )

            log_sync_event(
                event="completed",
                organization_id=1,
                db_path=temp_db_path,
                sync_id="sync-001",
                rows_synced=500,
                duration_seconds=10.5,
                source="api",
            )

            # 3. Log auth event
            log_auth_event(
                event="login",
                organization_id=1,
                db_path=temp_db_path,
                user_id=1,
                email="admin@example.com",
            )

        # 4. Query and verify
        repo = get_audit_log_repository(temp_db_path)
        logs = repo.get_all(organization_id=1)

        assert len(logs) == 3

        # Check context was captured
        for log in logs:
            assert log.source_ip == "192.168.1.100"
            assert log.user_agent == "TestBrowser/1.0"

        # 5. Export
        output = io.StringIO()
        result = export_to_json(
            organization_id=1,
            output=output,
            db_path=temp_db_path,
        )
        assert result.record_count == 3

        # 6. Get stats
        stats = repo.get_stats(organization_id=1)
        assert stats["total_logs"] == 3
        assert "sync.started" in stats["by_action"]
        assert "sync.completed" in stats["by_action"]
        assert "auth.login" in stats["by_action"]

        reset_audit_log_repository()
