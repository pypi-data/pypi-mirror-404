"""Tests for the notification system."""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.exceptions import NotificationError
from mysql_to_sheets.core.notifications.base import (
    NotificationConfig,
    NotificationPayload,
)
from mysql_to_sheets.core.notifications.email import EmailNotificationBackend
from mysql_to_sheets.core.notifications.manager import (
    NotificationManager,
    get_notification_manager,
    reset_notification_manager,
)
from mysql_to_sheets.core.notifications.slack import SlackNotificationBackend
from mysql_to_sheets.core.notifications.webhook import WebhookNotificationBackend


class TestNotificationPayload:
    """Tests for NotificationPayload dataclass."""

    def test_success_payload(self):
        """Test creating a success payload."""
        payload = NotificationPayload(
            success=True,
            rows_synced=100,
            sheet_id="abc123",
            worksheet="Sheet1",
            message="Synced successfully",
        )

        assert payload.success is True
        assert payload.rows_synced == 100
        assert payload.status_emoji == "\u2705"  # checkmark
        assert payload.status_text == "Sync Successful"

    def test_failure_payload(self):
        """Test creating a failure payload."""
        payload = NotificationPayload(
            success=False,
            error="Connection refused",
        )

        assert payload.success is False
        assert payload.status_emoji == "\u274c"  # X mark
        assert payload.status_text == "Sync Failed"

    def test_dry_run_payload(self):
        """Test creating a dry run payload."""
        payload = NotificationPayload(
            success=True,
            dry_run=True,
        )

        assert payload.status_emoji == "\U0001f50d"  # magnifying glass
        assert payload.status_text == "Dry Run Complete"

    def test_to_dict(self):
        """Test converting payload to dictionary."""
        payload = NotificationPayload(
            success=True,
            rows_synced=50,
            sheet_id="test123",
            source="cli",
        )

        data = payload.to_dict()

        assert data["success"] is True
        assert data["rows_synced"] == 50
        assert data["sheet_id"] == "test123"
        assert data["source"] == "cli"
        assert "timestamp" in data


class TestNotificationConfig:
    """Tests for NotificationConfig dataclass."""

    def test_has_email_config_complete(self):
        """Test email config detection with complete config."""
        config = NotificationConfig(
            smtp_host="smtp.example.com",
            smtp_user="user@example.com",
            smtp_password="secret",
            smtp_from="sender@example.com",
            smtp_to="recipient@example.com",
        )

        assert config.has_email_config() is True

    def test_has_email_config_incomplete(self):
        """Test email config detection with incomplete config."""
        config = NotificationConfig(
            smtp_host="smtp.example.com",
            # Missing other required fields
        )

        assert config.has_email_config() is False

    def test_has_slack_config(self):
        """Test Slack config detection."""
        config_with = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/services/xxx",
        )
        config_without = NotificationConfig()

        assert config_with.has_slack_config() is True
        assert config_without.has_slack_config() is False

    def test_has_webhook_config(self):
        """Test webhook config detection."""
        config_with = NotificationConfig(
            notification_webhook_url="https://example.com/webhook",
        )
        config_without = NotificationConfig()

        assert config_with.has_webhook_config() is True
        assert config_without.has_webhook_config() is False

    def test_get_email_recipients(self):
        """Test parsing email recipients."""
        config = NotificationConfig(
            smtp_to="a@example.com, b@example.com, c@example.com",
        )

        recipients = config.get_email_recipients()

        assert len(recipients) == 3
        assert "a@example.com" in recipients
        assert "b@example.com" in recipients

    def test_get_email_recipients_empty(self):
        """Test parsing empty recipients."""
        config = NotificationConfig()
        assert config.get_email_recipients() == []


class TestEmailNotificationBackend:
    """Tests for EmailNotificationBackend."""

    def test_name(self):
        """Test backend name."""
        backend = EmailNotificationBackend()
        assert backend.name == "email"

    def test_is_configured(self):
        """Test configuration detection."""
        backend = EmailNotificationBackend()

        config_complete = NotificationConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            smtp_from="from@example.com",
            smtp_to="to@example.com",
        )
        config_incomplete = NotificationConfig()

        assert backend.is_configured(config_complete) is True
        assert backend.is_configured(config_incomplete) is False

    def test_should_notify_on_success(self):
        """Test should_notify with success notification enabled."""
        backend = EmailNotificationBackend()

        config = NotificationConfig(
            notify_on_success=True,
            notify_on_failure=False,
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            smtp_from="from@example.com",
            smtp_to="to@example.com",
        )

        success_payload = NotificationPayload(success=True)
        failure_payload = NotificationPayload(success=False)

        assert backend.should_notify(success_payload, config) is True
        assert backend.should_notify(failure_payload, config) is False

    def test_should_not_notify_on_dry_run(self):
        """Test that dry runs don't trigger notifications."""
        backend = EmailNotificationBackend()

        config = NotificationConfig(
            notify_on_success=True,
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            smtp_from="from@example.com",
            smtp_to="to@example.com",
        )

        payload = NotificationPayload(success=True, dry_run=True)
        assert backend.should_notify(payload, config) is False

    @patch("smtplib.SMTP")
    def test_send_success(self, mock_smtp):
        """Test successful email send."""
        backend = EmailNotificationBackend()

        config = NotificationConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
            smtp_from="from@example.com",
            smtp_to="to@example.com",
            smtp_use_tls=True,
        )

        payload = NotificationPayload(
            success=True,
            rows_synced=100,
            message="Test sync",
        )

        # Mock SMTP context manager
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = backend.send(payload, config)

        assert result is True
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()

    def test_send_not_configured_raises(self):
        """Test that sending without config raises error."""
        backend = EmailNotificationBackend()
        config = NotificationConfig()  # No email config
        payload = NotificationPayload(success=True)

        with pytest.raises(NotificationError) as exc_info:
            backend.send(payload, config)

        assert "not configured" in str(exc_info.value)


class TestSlackNotificationBackend:
    """Tests for SlackNotificationBackend."""

    def test_name(self):
        """Test backend name."""
        backend = SlackNotificationBackend()
        assert backend.name == "slack"

    def test_is_configured(self):
        """Test configuration detection."""
        backend = SlackNotificationBackend()

        config_with = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/xxx",
        )
        config_without = NotificationConfig()

        assert backend.is_configured(config_with) is True
        assert backend.is_configured(config_without) is False

    @patch("urllib.request.urlopen")
    def test_send_success(self, mock_urlopen):
        """Test successful Slack notification send."""
        backend = SlackNotificationBackend()

        config = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/services/xxx",
        )

        payload = NotificationPayload(
            success=True,
            rows_synced=50,
            sheet_id="test123",
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = backend.send(payload, config)

        assert result is True
        mock_urlopen.assert_called_once()

    def test_send_not_configured_raises(self):
        """Test that sending without config raises error."""
        backend = SlackNotificationBackend()
        config = NotificationConfig()
        payload = NotificationPayload(success=True)

        with pytest.raises(NotificationError) as exc_info:
            backend.send(payload, config)

        assert "not configured" in str(exc_info.value)


class TestWebhookNotificationBackend:
    """Tests for WebhookNotificationBackend."""

    def test_name(self):
        """Test backend name."""
        backend = WebhookNotificationBackend()
        assert backend.name == "webhook"

    def test_is_configured(self):
        """Test configuration detection."""
        backend = WebhookNotificationBackend()

        config_with = NotificationConfig(
            notification_webhook_url="https://example.com/hook",
        )
        config_without = NotificationConfig()

        assert backend.is_configured(config_with) is True
        assert backend.is_configured(config_without) is False

    @patch("urllib.request.urlopen")
    def test_send_success(self, mock_urlopen):
        """Test successful webhook send."""
        backend = WebhookNotificationBackend()

        config = NotificationConfig(
            notification_webhook_url="https://example.com/webhook",
        )

        payload = NotificationPayload(
            success=True,
            rows_synced=100,
        )

        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = backend.send(payload, config)

        assert result is True

    def test_build_payload(self):
        """Test webhook payload structure."""
        backend = WebhookNotificationBackend()

        payload = NotificationPayload(
            success=True,
            rows_synced=100,
            sheet_id="abc123",
            source="test",
        )

        webhook_payload = backend._build_payload(payload)

        assert webhook_payload["event"] == "sync_complete"
        assert webhook_payload["success"] is True
        assert webhook_payload["data"]["rows_synced"] == 100
        assert webhook_payload["data"]["sheet_id"] == "abc123"
        assert webhook_payload["source"] == "test"


class TestNotificationManager:
    """Tests for NotificationManager."""

    def setup_method(self):
        """Reset manager before each test."""
        reset_notification_manager()

    def test_register_backend(self):
        """Test registering a backend."""
        manager = NotificationManager()
        backend = EmailNotificationBackend()

        manager.register_backend(backend)

        assert len(manager.backends) == 1
        assert manager.backends[0].name == "email"

    def test_register_default_backends(self):
        """Test registering all default backends."""
        manager = NotificationManager()
        manager.register_default_backends()

        assert len(manager.backends) == 3
        names = [b.name for b in manager.backends]
        assert "email" in names
        assert "slack" in names
        assert "webhook" in names

    def test_get_configured_backends(self):
        """Test filtering configured backends."""
        manager = NotificationManager()
        manager.register_default_backends()

        config = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/xxx",
            # No email or webhook config
        )

        configured = manager.get_configured_backends(config)

        assert len(configured) == 1
        assert configured[0].name == "slack"

    @patch("urllib.request.urlopen")
    def test_send_notification(self, mock_urlopen):
        """Test sending notification to multiple backends."""
        manager = NotificationManager()
        manager.register_default_backends()

        config = NotificationConfig(
            notify_on_success=True,
            slack_webhook_url="https://hooks.slack.com/xxx",
            notification_webhook_url="https://example.com/hook",
            # No email config
        )

        payload = NotificationPayload(success=True)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        results = manager.send_notification(payload, config)

        assert "slack" in results["sent"]
        assert "webhook" in results["sent"]
        assert "email" in results["skipped"]
        assert len(results["failed"]) == 0

    def test_get_status(self):
        """Test getting backend status."""
        manager = NotificationManager()
        manager.register_default_backends()

        config = NotificationConfig(
            notify_on_success=True,
            notify_on_failure=True,
            slack_webhook_url="https://hooks.slack.com/xxx",
        )

        status = manager.get_status(config)

        assert "email" in status
        assert "slack" in status
        assert "webhook" in status
        assert status["slack"]["configured"] is True
        assert status["email"]["configured"] is False

    def test_get_notification_manager_singleton(self):
        """Test that get_notification_manager returns singleton."""
        manager1 = get_notification_manager()
        manager2 = get_notification_manager()

        assert manager1 is manager2
        assert len(manager1.backends) == 3  # Default backends registered
