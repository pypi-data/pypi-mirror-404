"""Tests for Hybrid Agent Observability features.

Tests coverage:
1. models/crash_reports.py - CrashReport model and repository
2. agent/crash_handler.py - Crash sanitization and reporting
3. scheduler agent cleanup - Stale agent detection and cleanup
4. webhooks - Agent state change webhooks
5. web blueprints - Fleet dashboard routes
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from mysql_to_sheets.models.agents import (
    Agent,
    AgentRepository,
    reset_agent_repository,
)
from mysql_to_sheets.models.crash_reports import (
    CrashReport,
    CrashReportModel,
    CrashReportRepository,
    get_crash_report_repository,
    reset_crash_report_repository,
)
from mysql_to_sheets.agent.crash_handler import (
    CrashReporter,
    sanitize_crash_report,
    setup_crash_handler,
    get_crash_reporter,
    teardown_crash_handler,
    SANITIZE_PATTERNS,
)
from mysql_to_sheets.core.webhooks.payload import create_agent_payload


# ============================================================================
# Crash Report Model Tests
# ============================================================================


class TestCrashReportDataclass:
    """Tests for CrashReport dataclass."""

    def test_crash_report_creation(self):
        """Test creating a CrashReport with required fields."""
        report = CrashReport(
            agent_id="agent-test-123",
            organization_id=1,
            exception_type="DatabaseError",
            exception_message="Connection refused",
        )

        assert report.agent_id == "agent-test-123"
        assert report.organization_id == 1
        assert report.exception_type == "DatabaseError"
        assert report.exception_message == "Connection refused"
        assert report.id is None
        assert report.traceback is None
        assert report.job_id is None
        assert report.version is None
        assert report.context == {}

    def test_crash_report_with_optional_fields(self):
        """Test creating a CrashReport with all fields."""
        report = CrashReport(
            agent_id="agent-test-123",
            organization_id=1,
            exception_type="SyncError",
            exception_message="Failed to push data",
            traceback="Traceback (most recent call last):\n  ...",
            job_id=42,
            version="1.0.0",
            context={"config_id": 5, "sync_mode": "streaming"},
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        assert report.traceback == "Traceback (most recent call last):\n  ..."
        assert report.job_id == 42
        assert report.version == "1.0.0"
        assert report.context == {"config_id": 5, "sync_mode": "streaming"}
        assert report.created_at is not None

    def test_crash_report_to_dict(self):
        """Test CrashReport serialization to dictionary."""
        report = CrashReport(
            id=1,
            agent_id="agent-test-123",
            organization_id=1,
            exception_type="ValueError",
            exception_message="Invalid input",
            job_id=10,
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        d = report.to_dict()

        assert d["id"] == 1
        assert d["agent_id"] == "agent-test-123"
        assert d["organization_id"] == 1
        assert d["exception_type"] == "ValueError"
        assert d["exception_message"] == "Invalid input"
        assert d["job_id"] == 10
        assert "2024-01-15" in d["created_at"]

    def test_crash_report_from_dict(self):
        """Test creating CrashReport from dictionary."""
        data = {
            "id": 5,
            "agent_id": "agent-abc",
            "organization_id": 2,
            "exception_type": "TimeoutError",
            "exception_message": "Query timeout",
            "context": {"query": "SELECT * FROM users"},
            "created_at": "2024-01-15T12:00:00Z",
        }

        report = CrashReport.from_dict(data)

        assert report.id == 5
        assert report.agent_id == "agent-abc"
        assert report.organization_id == 2
        assert report.exception_type == "TimeoutError"
        assert report.context == {"query": "SELECT * FROM users"}
        assert report.created_at is not None

    def test_crash_report_from_dict_string_context(self):
        """Test CrashReport.from_dict handles JSON string context."""
        data = {
            "agent_id": "agent-xyz",
            "organization_id": 1,
            "exception_type": "Error",
            "exception_message": "Test",
            "context": '{"key": "value"}',
        }

        report = CrashReport.from_dict(data)
        assert report.context == {"key": "value"}


class TestCrashReportRepository:
    """Tests for CrashReportRepository CRUD operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
        reset_crash_report_repository()

    @pytest.fixture
    def repo(self, temp_db):
        """Create a repository instance."""
        return CrashReportRepository(temp_db)

    def test_create_crash_report(self, repo):
        """Test creating a crash report."""
        report = CrashReport(
            agent_id="agent-test",
            organization_id=1,
            exception_type="TestError",
            exception_message="Test message",
        )

        created = repo.create(report)

        assert created.id is not None
        assert created.agent_id == "agent-test"
        assert created.created_at is not None

    def test_get_by_id(self, repo):
        """Test retrieving a crash report by ID."""
        report = CrashReport(
            agent_id="agent-test",
            organization_id=1,
            exception_type="Error",
            exception_message="Message",
        )
        created = repo.create(report)

        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.agent_id == "agent-test"

    def test_get_by_id_with_org_filter(self, repo):
        """Test get_by_id respects organization filter."""
        report = CrashReport(
            agent_id="agent-test",
            organization_id=1,
            exception_type="Error",
            exception_message="Message",
        )
        created = repo.create(report)

        # Should find with correct org
        found = repo.get_by_id(created.id, organization_id=1)
        assert found is not None

        # Should not find with wrong org
        not_found = repo.get_by_id(created.id, organization_id=999)
        assert not_found is None

    def test_get_by_agent(self, repo):
        """Test retrieving crash reports for an agent."""
        # Create multiple reports for same agent
        for i in range(3):
            repo.create(CrashReport(
                agent_id="agent-abc",
                organization_id=1,
                exception_type=f"Error{i}",
                exception_message=f"Message {i}",
            ))

        # Create report for different agent
        repo.create(CrashReport(
            agent_id="agent-xyz",
            organization_id=1,
            exception_type="OtherError",
            exception_message="Other",
        ))

        reports = repo.get_by_agent("agent-abc", organization_id=1)

        assert len(reports) == 3
        assert all(r.agent_id == "agent-abc" for r in reports)

    def test_get_by_agent_limit(self, repo):
        """Test get_by_agent respects limit parameter."""
        for i in range(10):
            repo.create(CrashReport(
                agent_id="agent-test",
                organization_id=1,
                exception_type=f"Error{i}",
                exception_message=f"Message {i}",
            ))

        reports = repo.get_by_agent("agent-test", organization_id=1, limit=5)
        assert len(reports) == 5

    def test_get_by_organization(self, repo):
        """Test retrieving crash reports for an organization."""
        # Create reports for org 1
        for i in range(3):
            repo.create(CrashReport(
                agent_id=f"agent-{i}",
                organization_id=1,
                exception_type="Error",
                exception_message="Message",
            ))

        # Create reports for org 2
        for i in range(2):
            repo.create(CrashReport(
                agent_id=f"agent-{i}",
                organization_id=2,
                exception_type="Error",
                exception_message="Message",
            ))

        org1_reports = repo.get_by_organization(organization_id=1)
        org2_reports = repo.get_by_organization(organization_id=2)

        assert len(org1_reports) == 3
        assert len(org2_reports) == 2

    def test_count(self, repo):
        """Test counting crash reports."""
        for i in range(5):
            repo.create(CrashReport(
                agent_id="agent-test",
                organization_id=1,
                exception_type="Error",
                exception_message="Message",
            ))

        assert repo.count() == 5
        assert repo.count(organization_id=1) == 5
        assert repo.count(organization_id=999) == 0

    def test_cleanup_old(self, repo):
        """Test deleting old crash reports."""
        # Create an old report (manually set created_at via model)
        from mysql_to_sheets.models.crash_reports import CrashReportModel, Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{repo._db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            old_date = datetime.now(timezone.utc) - timedelta(days=60)
            old_model = CrashReportModel(
                agent_id="agent-old",
                organization_id=1,
                exception_type="OldError",
                exception_message="Old message",
                created_at=old_date,
            )
            session.add(old_model)

            new_model = CrashReportModel(
                agent_id="agent-new",
                organization_id=1,
                exception_type="NewError",
                exception_message="New message",
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_model)
            session.commit()
        finally:
            session.close()

        # Cleanup with 30 day retention
        deleted = repo.cleanup_old(retention_days=30)

        assert deleted == 1
        assert repo.count() == 1

        # Verify the new report remains
        reports = repo.get_by_organization(1)
        assert reports[0].agent_id == "agent-new"


# ============================================================================
# Crash Handler Tests
# ============================================================================


class TestCrashSanitization:
    """Tests for crash report sanitization."""

    def test_sanitize_password_equals(self):
        """Test sanitizing password=value patterns."""
        text = "Error: password=secret123 occurred"
        sanitized = sanitize_crash_report(text)
        assert "secret123" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_sanitize_db_password_env(self):
        """Test sanitizing DB_PASSWORD environment variable."""
        text = "DB_PASSWORD=mysecretpass in config"
        sanitized = sanitize_crash_report(text)
        assert "mysecretpass" not in sanitized
        assert "DB_PASSWORD=***REDACTED***" in sanitized

    def test_sanitize_bearer_token(self):
        """Test sanitizing Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy"
        sanitized = sanitize_crash_report(text)
        assert "eyJhbG" not in sanitized
        assert "Bearer ***REDACTED***" in sanitized

    def test_sanitize_api_key(self):
        """Test sanitizing api_key values."""
        text = "Request with api_key=sk_live_abc123xyz"
        sanitized = sanitize_crash_report(text)
        assert "sk_live" not in sanitized
        assert "api_key=***REDACTED***" in sanitized

    def test_sanitize_jwt_tokens(self):
        """Test sanitizing standalone JWT tokens."""
        # Test a JWT in raw form (not as token=value)
        text = "Found JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U in request"
        sanitized = sanitize_crash_report(text)
        # The JWT pattern should be redacted
        assert "eyJhbG" not in sanitized or "***" in sanitized

    def test_sanitize_email_addresses(self):
        """Test sanitizing email addresses."""
        text = "User user@example.com failed to authenticate"
        sanitized = sanitize_crash_report(text)
        assert "user@example.com" not in sanitized
        assert "***EMAIL_REDACTED***" in sanitized

    def test_sanitize_connection_strings(self):
        """Test sanitizing database connection strings."""
        text = "Connecting to mysql://admin:secretpass@localhost:3306/mydb"
        sanitized = sanitize_crash_report(text)
        assert "secretpass" not in sanitized
        assert "admin" not in sanitized
        assert "mysql://***:***@" in sanitized

    def test_sanitize_link_token(self):
        """Test sanitizing LINK_TOKEN."""
        text = "LINK_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        sanitized = sanitize_crash_report(text)
        assert "eyJhbG" not in sanitized
        assert "LINK_TOKEN=***REDACTED***" in sanitized

    def test_sanitize_truncates_large_text(self):
        """Test that large text is truncated."""
        large_text = "A" * 200000  # 200KB
        sanitized = sanitize_crash_report(large_text, max_size_kb=100)
        assert len(sanitized.encode("utf-8")) <= 100 * 1024 + 100  # Allow for truncation message
        assert "TRUNCATED" in sanitized

    def test_sanitize_preserves_normal_text(self):
        """Test that non-sensitive text is preserved."""
        text = "Error occurred in function process_data at line 42"
        sanitized = sanitize_crash_report(text)
        assert sanitized == text

    def test_sanitize_empty_text(self):
        """Test sanitizing empty/None text."""
        assert sanitize_crash_report("") == ""
        assert sanitize_crash_report(None) is None


class TestCrashReporter:
    """Tests for CrashReporter class."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up crash handler after each test."""
        yield
        teardown_crash_handler()

    def test_reporter_creation(self):
        """Test creating a CrashReporter."""
        reporter = CrashReporter(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
            version="1.0.0",
        )

        assert reporter.agent_id == "agent-test"
        assert reporter.control_plane_url == "https://example.com"
        assert reporter.enabled is True

    def test_reporter_disabled(self):
        """Test that disabled reporter doesn't send reports."""
        reporter = CrashReporter(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
            enabled=False,
        )

        with patch("requests.post") as mock_post:
            result = reporter.report(
                exception_type="Error",
                exception_message="Test",
            )

        assert result is False
        mock_post.assert_not_called()

    @patch("requests.post")
    def test_reporter_sends_sanitized_report(self, mock_post):
        """Test that reporter sanitizes and sends crash reports."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        reporter = CrashReporter(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
            version="1.0.0",
        )

        result = reporter.report(
            exception_type="DatabaseError",
            exception_message="password=secret123",
            tb="Traceback with password=secret in it",
            job_id=42,
        )

        assert result is True
        mock_post.assert_called_once()

        # Check sanitization was applied
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "secret123" not in payload["exception_message"]
        assert "secret" not in payload["traceback"]

    @patch("mysql_to_sheets.agent.crash_handler.requests.post")
    def test_reporter_handles_network_error(self, mock_post):
        """Test that reporter handles network errors gracefully."""
        import requests
        mock_post.side_effect = requests.RequestException("Network error")

        reporter = CrashReporter(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
        )

        result = reporter.report(
            exception_type="Error",
            exception_message="Test",
        )

        assert result is False

    @patch("requests.post")
    def test_report_exception(self, mock_post):
        """Test reporting an exception object."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        reporter = CrashReporter(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
        )

        exc = ValueError("Invalid value")
        result = reporter.report_exception(exc, job_id=10)

        assert result is True
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["exception_type"] == "ValueError"
        assert "Invalid value" in payload["exception_message"]

    def test_setup_crash_handler(self):
        """Test setup_crash_handler creates global reporter."""
        reporter = setup_crash_handler(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
            install_excepthook=False,
        )

        assert reporter is not None
        assert get_crash_reporter() is reporter

    def test_teardown_crash_handler(self):
        """Test teardown clears global reporter."""
        setup_crash_handler(
            agent_id="agent-test",
            control_plane_url="https://example.com",
            link_token="test-token",
            install_excepthook=False,
        )

        teardown_crash_handler()

        assert get_crash_reporter() is None


# ============================================================================
# Agent Webhook Payload Tests
# ============================================================================


class TestAgentWebhookPayload:
    """Tests for agent webhook payload creation."""

    def test_create_agent_online_payload(self):
        """Test creating agent.online webhook payload."""
        payload = create_agent_payload(
            event="agent.online",
            agent_id="agent-test-123",
            organization_id=1,
            hostname="worker-1.internal",
            version="1.0.0",
            previous_status="offline",
            new_status="online",
        )

        assert payload.event == "agent.online"
        assert payload.data["agent_id"] == "agent-test-123"
        assert payload.data["organization_id"] == 1
        assert payload.data["hostname"] == "worker-1.internal"
        assert payload.data["version"] == "1.0.0"
        assert payload.data["previous_status"] == "offline"
        assert payload.data["new_status"] == "online"

    def test_create_agent_offline_payload(self):
        """Test creating agent.offline webhook payload."""
        payload = create_agent_payload(
            event="agent.offline",
            agent_id="agent-test-123",
            organization_id=1,
            previous_status="online",
            new_status="offline",
            offline_reason="graceful_shutdown",
        )

        assert payload.event == "agent.offline"
        assert payload.data["offline_reason"] == "graceful_shutdown"

    def test_create_agent_stale_payload(self):
        """Test creating agent.stale webhook payload."""
        last_seen = datetime(2024, 1, 15, 10, 25, 0, tzinfo=timezone.utc)
        payload = create_agent_payload(
            event="agent.stale",
            agent_id="agent-test-123",
            organization_id=1,
            previous_status="online",
            new_status="offline",
            last_seen_at=last_seen,
            offline_reason="heartbeat_timeout",
        )

        assert payload.event == "agent.stale"
        assert payload.data["offline_reason"] == "heartbeat_timeout"
        assert payload.data["last_seen_at"] == "2024-01-15T10:25:00+00:00"

    def test_payload_to_dict(self):
        """Test webhook payload serialization."""
        payload = create_agent_payload(
            event="agent.online",
            agent_id="agent-test",
            organization_id=1,
        )

        d = payload.to_dict()

        assert d["event"] == "agent.online"
        assert "timestamp" in d
        assert "data" in d
        assert d["data"]["agent_id"] == "agent-test"


# ============================================================================
# Agent Cleanup Tests
# ============================================================================


class TestAgentCleanup:
    """Tests for agent stale cleanup functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
        reset_agent_repository()

    @pytest.fixture
    def repo(self, temp_db):
        """Create an agent repository instance."""
        return AgentRepository(temp_db)

    def test_cleanup_stale_marks_agents_offline(self, repo):
        """Test that stale agents are marked offline."""
        # Create an agent with old last_seen
        agent = repo.upsert(
            agent_id="agent-stale",
            organization_id=1,
            version="1.0.0",
            hostname="worker-1",
        )

        # Manually update last_seen to be old
        from mysql_to_sheets.models.agents import AgentModel
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{repo._db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            model = session.query(AgentModel).filter(
                AgentModel.agent_id == "agent-stale"
            ).first()
            model.last_seen_at = datetime.now(timezone.utc) - timedelta(minutes=10)
            model.status = "online"
            session.commit()
        finally:
            session.close()

        # Run cleanup with 5 minute timeout
        stale_agents = repo.cleanup_stale_with_list(timeout_seconds=300)

        assert len(stale_agents) == 1
        assert stale_agents[0].agent_id == "agent-stale"

        # Verify agent is now offline
        updated = repo.get_by_agent_id("agent-stale")
        assert updated.status == "offline"

    def test_cleanup_stale_ignores_recent_agents(self, repo):
        """Test that recently seen agents are not marked stale."""
        # Create an agent with recent last_seen
        repo.upsert(
            agent_id="agent-active",
            organization_id=1,
            version="1.0.0",
            hostname="worker-1",
        )

        # Run cleanup
        stale_agents = repo.cleanup_stale_with_list(timeout_seconds=300)

        assert len(stale_agents) == 0

        # Verify agent is still online
        agent = repo.get_by_agent_id("agent-active")
        assert agent.status == "online"

    def test_cleanup_stale_returns_previous_status(self, repo):
        """Test that cleanup returns agent with previous status for webhook."""
        repo.upsert(
            agent_id="agent-busy",
            organization_id=1,
        )

        # Set status to busy and make it stale
        from mysql_to_sheets.models.agents import AgentModel
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{repo._db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            model = session.query(AgentModel).filter(
                AgentModel.agent_id == "agent-busy"
            ).first()
            model.status = "busy"
            model.last_seen_at = datetime.now(timezone.utc) - timedelta(minutes=10)
            session.commit()
        finally:
            session.close()

        stale_agents = repo.cleanup_stale_with_list(timeout_seconds=60)

        # Should return agent with 'busy' status (what it was before cleanup)
        assert len(stale_agents) == 1
        assert stale_agents[0].status == "busy"


class TestAgentFleetStats:
    """Tests for fleet statistics."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
        reset_agent_repository()

    @pytest.fixture
    def repo(self, temp_db):
        """Create an agent repository instance."""
        return AgentRepository(temp_db)

    def test_get_fleet_stats_empty(self, repo):
        """Test fleet stats with no agents."""
        stats = repo.get_fleet_stats(organization_id=1)

        assert stats["total"] == 0
        assert stats["online"] == 0
        assert stats["offline"] == 0
        assert stats["busy"] == 0
        assert stats["jobs_completed"] == 0
        assert stats["jobs_failed"] == 0

    def test_get_fleet_stats_with_agents(self, repo):
        """Test fleet stats with multiple agents."""
        # Create agents with different statuses
        repo.upsert("agent-1", 1)  # online
        repo.upsert("agent-2", 1)  # online

        # Update statuses
        repo.update_status("agent-1", 1, "busy")

        # Manually add an offline agent
        from mysql_to_sheets.models.agents import AgentModel
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(f"sqlite:///{repo._db_path}")
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            model = AgentModel(
                agent_id="agent-3",
                organization_id=1,
                status="offline",
                is_active=True,
                jobs_completed=10,
                jobs_failed=2,
            )
            session.add(model)
            session.commit()
        finally:
            session.close()

        stats = repo.get_fleet_stats(organization_id=1)

        assert stats["total"] == 3
        assert stats["online"] == 1
        assert stats["busy"] == 1
        assert stats["offline"] == 1
        assert stats["jobs_completed"] == 10
        assert stats["jobs_failed"] == 2

    def test_get_fleet_stats_filters_by_org(self, repo):
        """Test fleet stats filters by organization."""
        repo.upsert("agent-org1", 1)
        repo.upsert("agent-org2", 2)

        stats1 = repo.get_fleet_stats(organization_id=1)
        stats2 = repo.get_fleet_stats(organization_id=2)

        assert stats1["total"] == 1
        assert stats2["total"] == 1


# ============================================================================
# Config Tests for Agent Observability
# ============================================================================


class TestAgentObservabilityConfig:
    """Tests for agent observability configuration."""

    def test_default_config_values(self):
        """Test default values for agent observability config."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()

        with patch.dict(os.environ, {
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_NAME": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
        }, clear=True):
            config = Config()

            assert config.agent_cleanup_interval_seconds == 60
            assert config.agent_stale_timeout_seconds == 300
            assert config.crash_report_retention_days == 30
            assert config.crash_report_max_size_kb == 100

    def test_custom_config_from_env(self):
        """Test custom values from environment."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()

        with patch.dict(os.environ, {
            "DB_USER": "test",
            "DB_PASSWORD": "test",
            "DB_NAME": "test",
            "GOOGLE_SHEET_ID": "test",
            "SQL_QUERY": "SELECT 1",
            "AGENT_CLEANUP_INTERVAL_SECONDS": "120",
            "AGENT_STALE_TIMEOUT_SECONDS": "600",
            "CRASH_REPORT_RETENTION_DAYS": "60",
            "CRASH_REPORT_MAX_SIZE_KB": "200",
        }, clear=True):
            config = Config()

            assert config.agent_cleanup_interval_seconds == 120
            assert config.agent_stale_timeout_seconds == 600
            assert config.crash_report_retention_days == 60
            assert config.crash_report_max_size_kb == 200
