"""Tests for freshness alerting system."""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.freshness import (
    FRESHNESS_STALE,
    FRESHNESS_WARNING,
    FreshnessStatus,
)
from mysql_to_sheets.core.freshness_alerts import (
    _create_alert,
    _send_alert,
    check_and_alert,
    check_and_alert_all,
    get_stale_syncs,
)
from mysql_to_sheets.models.organizations import (
    Organization,
    OrganizationRepository,
)
from mysql_to_sheets.models.sync_configs import (
    SyncConfigDefinition,
    SyncConfigRepository,
    reset_sync_config_repository,
)


class TestAlertCreation:
    """Tests for alert message creation."""

    def test_create_stale_alert_message(self):
        """Test creating alert message for stale config."""
        status = FreshnessStatus(
            config_id=1,
            config_name="production-sync",
            status=FRESHNESS_STALE,
            last_success_at=datetime(2024, 1, 1, 10, 0, 0),
            sla_minutes=60,
            minutes_since_sync=120,
            percent_of_sla=200.0,
            organization_id=1,
        )

        alert = _create_alert(status)

        assert alert["type"] == "freshness_alert"
        assert alert["severity"] == "critical"
        assert alert["status"] == FRESHNESS_STALE
        assert alert["config_id"] == 1
        assert alert["config_name"] == "production-sync"
        assert "stale" in alert["message"].lower()
        assert "120 minutes" in alert["message"]
        assert alert["sla_minutes"] == 60

    def test_create_warning_alert_message(self):
        """Test creating alert message for warning config."""
        status = FreshnessStatus(
            config_id=2,
            config_name="reporting-sync",
            status=FRESHNESS_WARNING,
            last_success_at=datetime(2024, 1, 1, 11, 0, 0),
            sla_minutes=60,
            minutes_since_sync=50,
            percent_of_sla=83.3,
            organization_id=1,
        )

        alert = _create_alert(status)

        assert alert["severity"] == "warning"
        assert alert["status"] == FRESHNESS_WARNING
        assert "approaching" in alert["message"].lower()
        assert "83%" in alert["message"]

    def test_alert_includes_metadata(self):
        """Test that alert includes all required metadata."""
        status = FreshnessStatus(
            config_id=3,
            config_name="test-sync",
            status=FRESHNESS_STALE,
            last_success_at=datetime.now(timezone.utc),
            sla_minutes=30,
            minutes_since_sync=45,
            percent_of_sla=150.0,
            organization_id=5,
        )

        alert = _create_alert(status)

        assert "created_at" in alert
        assert alert["organization_id"] == 5
        assert alert["last_success_at"] is not None


class TestCheckAndAlert:
    """Tests for check_and_alert function."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_sync_config_repository()

    @pytest.fixture
    def org_repo(self, db_path):
        """Create an organization repository."""
        return OrganizationRepository(db_path)

    @pytest.fixture
    def config_repo(self, db_path, org_repo):
        """Create a sync config repository."""
        return SyncConfigRepository(db_path)

    @pytest.fixture
    def org(self, org_repo):
        """Create a test organization."""
        org = Organization(name="Test Org", slug="test-org")
        return org_repo.create(org)

    def test_no_alerts_for_fresh_configs(self, db_path, org, config_repo):
        """Test that fresh configs don't generate alerts."""
        config = SyncConfigDefinition(
            name="fresh-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        config_repo.create(config)

        alerts = check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=False,
        )

        assert len(alerts) == 0

    def test_alerts_for_stale_configs(self, db_path, org, config_repo):
        """Test that stale configs generate alerts."""
        config = SyncConfigDefinition(
            name="stale-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        config_repo.create(config)

        alerts = check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=False,
        )

        assert len(alerts) == 1
        assert alerts[0]["config_name"] == "stale-sync"
        assert alerts[0]["severity"] == "critical"

    def test_alerts_for_warning_configs(self, db_path, org, config_repo):
        """Test that warning configs generate alerts."""
        config = SyncConfigDefinition(
            name="warning-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc) - timedelta(minutes=50),
        )
        config_repo.create(config)

        alerts = check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=False,
        )

        assert len(alerts) == 1
        assert alerts[0]["severity"] == "warning"

    def test_no_alert_during_cooldown(self, db_path, org, config_repo):
        """Test that no alert is sent during cooldown period."""
        # Create stale config with recent alert
        config = SyncConfigDefinition(
            name="cooldown-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            last_alert_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        config_repo.create(config)

        alerts = check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=False,
        )

        assert len(alerts) == 0

    @patch("mysql_to_sheets.core.freshness_alerts._send_alert")
    def test_sends_notification_when_enabled(self, mock_send, db_path, org, config_repo):
        """Test that notifications are sent when enabled."""
        config = SyncConfigDefinition(
            name="notify-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        config_repo.create(config)

        alerts = check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=True,
        )

        assert len(alerts) == 1
        mock_send.assert_called_once()

    @patch("mysql_to_sheets.core.freshness_alerts._send_alert")
    def test_updates_last_alert_at(self, mock_send, db_path, org, config_repo):
        """Test that last_alert_at is updated after sending."""
        config = SyncConfigDefinition(
            name="update-alert-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        created = config_repo.create(config)

        check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=True,
        )

        # Check that last_alert_at was updated
        updated = config_repo.get_by_id(created.id, org.id)
        assert updated.last_alert_at is not None


class TestSendAlert:
    """Tests for alert notification sending."""

    def setup_method(self):
        """Reset config before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    def test_send_alert_without_config_does_not_crash(self):
        """Test that _send_alert doesn't crash when no notification channels configured."""

        alert = {
            "severity": "critical",
            "config_name": "test-sync",
            "config_id": 1,
            "message": "Test alert message",
            "sla_minutes": 60,
        }

        # Should not raise exception even with no notification channels
        # Just use the current config (which has no channels by default)
        _send_alert(alert, organization_id=1)

    @patch("mysql_to_sheets.core.config.get_config")
    @patch("mysql_to_sheets.core.notifications.email.send_email", create=True)
    def test_sends_email_when_configured(self, mock_send_email, mock_get_config):
        """Test sending email alert when SMTP is configured."""
        mock_config = MagicMock()
        mock_config.smtp_host = "smtp.example.com"
        mock_config.smtp_to = "alerts@example.com"
        mock_config.slack_webhook_url = None
        mock_config.notification_webhook_url = None
        mock_get_config.return_value = mock_config

        alert = {
            "severity": "critical",
            "config_name": "test-sync",
            "config_id": 1,
            "message": "Sync is stale",
            "sla_minutes": 60,
        }

        _send_alert(alert, organization_id=1)

        mock_send_email.assert_called_once()

    @patch("mysql_to_sheets.core.config.get_config")
    @patch("mysql_to_sheets.core.notifications.slack.send_slack_message", create=True)
    def test_sends_slack_when_configured(self, mock_send_slack, mock_get_config):
        """Test sending Slack alert when webhook is configured."""
        mock_config = MagicMock()
        mock_config.smtp_host = None
        mock_config.smtp_to = None
        mock_config.slack_webhook_url = "https://hooks.slack.com/test"
        mock_config.notification_webhook_url = None
        mock_get_config.return_value = mock_config

        alert = {
            "severity": "warning",
            "config_name": "slack-sync",
            "config_id": 2,
            "message": "Approaching SLA",
            "sla_minutes": 60,
        }

        _send_alert(alert, organization_id=1)

        mock_send_slack.assert_called_once()

    @patch("mysql_to_sheets.core.config.get_config")
    @patch("mysql_to_sheets.core.notifications.webhook.send_webhook", create=True)
    def test_sends_generic_webhook_when_configured(self, mock_send_webhook, mock_get_config):
        """Test sending generic webhook when configured."""
        mock_config = MagicMock()
        mock_config.smtp_host = None
        mock_config.smtp_to = None
        mock_config.slack_webhook_url = None
        mock_config.notification_webhook_url = "https://example.com/webhook"
        mock_get_config.return_value = mock_config

        alert = {
            "severity": "critical",
            "config_name": "webhook-sync",
            "config_id": 3,
            "message": "Sync is stale",
            "sla_minutes": 30,
        }

        _send_alert(alert, organization_id=1)

        mock_send_webhook.assert_called_once()

    @patch("mysql_to_sheets.core.config.get_config")
    @patch("mysql_to_sheets.core.notifications.webhook.send_webhook", create=True)
    @patch("mysql_to_sheets.core.notifications.slack.send_slack_message", create=True)
    @patch("mysql_to_sheets.core.notifications.email.send_email", create=True)
    def test_sends_multiple_channels(self, mock_email, mock_slack, mock_webhook, mock_get_config):
        """Test sending to multiple notification channels."""
        mock_config = MagicMock()
        mock_config.smtp_host = "smtp.example.com"
        mock_config.smtp_to = "alerts@example.com"
        mock_config.slack_webhook_url = "https://hooks.slack.com/test"
        mock_config.notification_webhook_url = "https://example.com/webhook"
        mock_get_config.return_value = mock_config

        alert = {
            "severity": "critical",
            "config_name": "multi-sync",
            "config_id": 4,
            "message": "Sync is stale",
            "sla_minutes": 60,
        }

        _send_alert(alert, organization_id=1)

        mock_email.assert_called_once()
        mock_slack.assert_called_once()
        mock_webhook.assert_called_once()

    @patch("mysql_to_sheets.core.config.get_config")
    @patch(
        "mysql_to_sheets.core.notifications.email.send_email",
        create=True,
        side_effect=OSError("SMTP error"),
    )
    def test_handles_email_failure_gracefully(self, mock_send_email, mock_get_config):
        """Test that email failures don't crash the alert system."""
        mock_config = MagicMock()
        mock_config.smtp_host = "smtp.example.com"
        mock_config.smtp_to = "alerts@example.com"
        mock_config.slack_webhook_url = None
        mock_config.notification_webhook_url = None
        mock_get_config.return_value = mock_config

        alert = {
            "severity": "critical",
            "config_name": "fail-sync",
            "config_id": 5,
            "message": "Sync is stale",
            "sla_minutes": 60,
        }

        # Should not raise
        _send_alert(alert, organization_id=1)


class TestGetStaleSyncs:
    """Tests for get_stale_syncs function."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_sync_config_repository()

    @pytest.fixture
    def org_repo(self, db_path):
        """Create an organization repository."""
        return OrganizationRepository(db_path)

    @pytest.fixture
    def config_repo(self, db_path, org_repo):
        """Create a sync config repository."""
        return SyncConfigRepository(db_path)

    @pytest.fixture
    def org(self, org_repo):
        """Create a test organization."""
        org = Organization(name="Test Org", slug="test-org")
        return org_repo.create(org)

    def test_returns_only_stale_syncs(self, db_path, org, config_repo):
        """Test that only stale syncs are returned."""
        # Create mixed configs
        config_repo.create(
            SyncConfigDefinition(
                name="fresh",
                sql_query="SELECT 1",
                sheet_id="sheet1",
                organization_id=org.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc),
            )
        )
        config_repo.create(
            SyncConfigDefinition(
                name="stale",
                sql_query="SELECT 2",
                sheet_id="sheet2",
                organization_id=org.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
        )

        stale = get_stale_syncs(organization_id=org.id, db_path=db_path)

        assert len(stale) == 1
        assert stale[0]["config_name"] == "stale"

    def test_includes_minutes_overdue(self, db_path, org, config_repo):
        """Test that stale syncs include minutes overdue."""
        config_repo.create(
            SyncConfigDefinition(
                name="very-stale",
                sql_query="SELECT 1",
                sheet_id="sheet1",
                organization_id=org.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc) - timedelta(minutes=150),
            )
        )

        stale = get_stale_syncs(organization_id=org.id, db_path=db_path)

        assert len(stale) == 1
        # Should be about 90 minutes overdue (150 - 60)
        assert stale[0]["minutes_overdue"] is not None
        assert stale[0]["minutes_overdue"] > 80


class TestCheckAndAlertAll:
    """Tests for check_and_alert_all function."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_sync_config_repository()

    @pytest.fixture
    def org_repo(self, db_path):
        """Create an organization repository."""
        return OrganizationRepository(db_path)

    @pytest.fixture
    def config_repo(self, db_path, org_repo):
        """Create a sync config repository."""
        return SyncConfigRepository(db_path)

    def test_checks_multiple_organizations(self, db_path, org_repo, config_repo):
        """Test that all active organizations are checked."""
        # Create two organizations
        org1 = org_repo.create(Organization(name="Org 1", slug="org1"))
        org2 = org_repo.create(Organization(name="Org 2", slug="org2"))

        # Create stale configs for both
        config_repo.create(
            SyncConfigDefinition(
                name="org1-stale",
                sql_query="SELECT 1",
                sheet_id="sheet1",
                organization_id=org1.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
        )
        config_repo.create(
            SyncConfigDefinition(
                name="org2-stale",
                sql_query="SELECT 2",
                sheet_id="sheet2",
                organization_id=org2.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
        )

        all_alerts = check_and_alert_all(db_path=db_path, send_notifications=False)

        assert len(all_alerts) == 2
        assert org1.id in all_alerts
        assert org2.id in all_alerts

    def test_skips_inactive_organizations(self, db_path, org_repo, config_repo):
        """Test that inactive organizations are skipped."""
        # Create active and inactive orgs
        active_org = org_repo.create(Organization(name="Active", slug="active", is_active=True))
        inactive_org = org_repo.create(
            Organization(name="Inactive", slug="inactive", is_active=False)
        )

        # Create stale configs for both
        config_repo.create(
            SyncConfigDefinition(
                name="active-stale",
                sql_query="SELECT 1",
                sheet_id="sheet1",
                organization_id=active_org.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
        )
        config_repo.create(
            SyncConfigDefinition(
                name="inactive-stale",
                sql_query="SELECT 2",
                sheet_id="sheet2",
                organization_id=inactive_org.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            )
        )

        all_alerts = check_and_alert_all(db_path=db_path, send_notifications=False)

        # Only active org should have alerts
        assert active_org.id in all_alerts
        assert inactive_org.id not in all_alerts

    def test_returns_empty_when_all_fresh(self, db_path, org_repo, config_repo):
        """Test returns empty dict when all configs are fresh."""
        org = org_repo.create(Organization(name="Test", slug="test"))

        config_repo.create(
            SyncConfigDefinition(
                name="fresh",
                sql_query="SELECT 1",
                sheet_id="sheet1",
                organization_id=org.id,
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc),
            )
        )

        all_alerts = check_and_alert_all(db_path=db_path, send_notifications=False)

        assert len(all_alerts) == 0
