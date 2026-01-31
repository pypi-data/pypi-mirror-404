"""Tests for billing webhook receiver module."""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from mysql_to_sheets.api.billing_webhook_routes import (
    _check_idempotency,
    _process_billing_event,
    _verify_signature,
    router,
)
from mysql_to_sheets.core.config import reset_config
from mysql_to_sheets.models.webhook_events import (
    ProcessedWebhookEventModel,
    _get_engine,
)


def create_test_app():
    """Create a test FastAPI app with billing webhook routes."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


class TestVerifySignature:
    """Tests for signature verification function."""

    def test_verify_signature_valid(self):
        """Test verifying a valid signature."""
        payload = b'{"event": "test"}'
        secret = "test_secret"

        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        assert _verify_signature(payload, f"sha256={expected}", secret) is True

    def test_verify_signature_valid_without_prefix(self):
        """Test verifying a valid signature without sha256= prefix."""
        payload = b'{"event": "test"}'
        secret = "test_secret"

        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        assert _verify_signature(payload, expected, secret) is True

    def test_verify_signature_invalid(self):
        """Test verifying an invalid signature."""
        payload = b'{"event": "test"}'
        secret = "test_secret"

        assert _verify_signature(payload, "sha256=invalid_signature", secret) is False

    def test_verify_signature_empty_signature(self):
        """Test with empty signature."""
        payload = b'{"event": "test"}'
        secret = "test_secret"

        assert _verify_signature(payload, "", secret) is False

    def test_verify_signature_empty_secret(self):
        """Test with empty secret."""
        payload = b'{"event": "test"}'

        assert _verify_signature(payload, "sha256=signature", "") is False


class TestCheckIdempotency:
    """Tests for idempotency check function."""

    def setup_method(self, tmp_path_factory=None):
        """Set up temp DB path for each test."""
        import tempfile
        import os

        self._tmp_dir = tempfile.mkdtemp()
        self._db_path = os.path.join(self._tmp_dir, "test_webhook.db")

    @patch("mysql_to_sheets.api.billing_webhook_routes.get_tenant_db_path")
    def test_check_idempotency_new_key(self, mock_db_path):
        """Test idempotency check for new key."""
        mock_db_path.return_value = self._db_path
        assert _check_idempotency("new_key_123") is False

    @patch("mysql_to_sheets.api.billing_webhook_routes.get_tenant_db_path")
    def test_check_idempotency_duplicate_key(self, mock_db_path):
        """Test idempotency check for duplicate key."""
        mock_db_path.return_value = self._db_path
        _check_idempotency("dup_key_456")
        # Second call should return True (already processed)
        assert _check_idempotency("dup_key_456") is True

    def test_check_idempotency_none_key(self):
        """Test idempotency check with None key."""
        assert _check_idempotency(None) is False


class TestProcessBillingEvent:
    """Tests for billing event processing."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_subscription_created(self, mock_update):
        """Test processing subscription.created event."""
        data = {
            "organization_id": 1,
            "customer_id": "cus_123",
            "tier": "pro",
        }

        result = _process_billing_event("subscription.created", data)

        assert "created" in result
        mock_update.assert_called_once_with(
            organization_id=1,
            billing_customer_id="cus_123",
            subscription_tier="pro",
            billing_status="active",
        )

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_subscription_created_missing_org_id(self, mock_update):
        """Test subscription.created with missing org_id."""
        data = {"customer_id": "cus_123", "tier": "pro"}

        with pytest.raises(ValueError, match="Missing organization_id"):
            _process_billing_event("subscription.created", data)

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_subscription_updated(self, mock_update):
        """Test processing subscription.updated event."""
        data = {
            "organization_id": 1,
            "tier": "business",
            "status": "active",
        }

        result = _process_billing_event("subscription.updated", data)

        assert "updated" in result
        mock_update.assert_called_once()

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_subscription_canceled(self, mock_update):
        """Test processing subscription.canceled event."""
        data = {"organization_id": 1}

        result = _process_billing_event("subscription.canceled", data)

        assert "canceled" in result
        mock_update.assert_called_once_with(
            organization_id=1,
            subscription_tier="free",
            billing_status="canceled",
        )

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_payment_failed(self, mock_update):
        """Test processing payment.failed event."""
        data = {"organization_id": 1}

        result = _process_billing_event("payment.failed", data)

        assert "failed" in result
        mock_update.assert_called_once_with(
            organization_id=1,
            billing_status="past_due",
        )

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_payment_succeeded(self, mock_update):
        """Test processing payment.succeeded event."""
        data = {"organization_id": 1}

        result = _process_billing_event("payment.succeeded", data)

        assert "succeeded" in result
        mock_update.assert_called_once_with(
            organization_id=1,
            billing_status="active",
        )

    @patch("mysql_to_sheets.api.billing_webhook_routes._update_organization")
    def test_process_payment_succeeded_with_period_end(self, mock_update):
        """Test payment.succeeded with subscription period end."""
        period_end = datetime.now(timezone.utc).isoformat()
        data = {
            "organization_id": 1,
            "period_end": period_end,
        }

        result = _process_billing_event("payment.succeeded", data)

        assert "succeeded" in result
        mock_update.assert_called_once()
        call_kwargs = mock_update.call_args[1]
        assert call_kwargs["billing_status"] == "active"
        assert call_kwargs["subscription_period_end"] is not None

    def test_process_unknown_event(self):
        """Test processing unknown event type."""
        result = _process_billing_event("unknown.event", {})

        assert "not handled" in result


class TestBillingWebhookEndpoint:
    """Tests for billing webhook HTTP endpoint."""

    def setup_method(self):
        """Reset state before each test."""
        reset_config()

    @patch("mysql_to_sheets.api.billing_webhook_routes.get_config")
    def test_webhook_disabled_returns_success(self, mock_get_config):
        """Test webhook returns success when billing disabled."""
        mock_config = MagicMock()
        mock_config.billing_enabled = False
        mock_get_config.return_value = mock_config

        app = create_test_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/billing/webhook",
            json={
                "event": "subscription.created",
                "data": {"organization_id": 1, "tier": "pro"},
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "not enabled" in response.json()["message"]

    @patch("mysql_to_sheets.api.billing_webhook_routes._process_billing_event")
    @patch("mysql_to_sheets.api.billing_webhook_routes.get_config")
    def test_webhook_missing_signature_when_required(self, mock_get_config, mock_process):
        """Test webhook requires signature when secret is configured."""
        mock_config = MagicMock()
        mock_config.billing_enabled = True
        mock_config.billing_webhook_secret = "test_secret"
        mock_get_config.return_value = mock_config

        app = create_test_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/billing/webhook",
            json={
                "event": "subscription.created",
                "data": {"organization_id": 1, "tier": "pro"},
            },
        )

        assert response.status_code == 401
        assert "Missing" in response.json()["detail"]

    @patch("mysql_to_sheets.api.billing_webhook_routes._process_billing_event")
    @patch("mysql_to_sheets.api.billing_webhook_routes.get_config")
    def test_webhook_invalid_signature(self, mock_get_config, mock_process):
        """Test webhook rejects invalid signature."""
        mock_config = MagicMock()
        mock_config.billing_enabled = True
        mock_config.billing_webhook_secret = "test_secret"
        mock_get_config.return_value = mock_config

        app = create_test_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/billing/webhook",
            json={
                "event": "subscription.created",
                "data": {"organization_id": 1, "tier": "pro"},
            },
            headers={"X-Webhook-Signature": "sha256=invalid"},
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    @patch("mysql_to_sheets.api.billing_webhook_routes._process_billing_event")
    @patch("mysql_to_sheets.api.billing_webhook_routes.get_config")
    def test_webhook_valid_signature(self, mock_get_config, mock_process):
        """Test webhook accepts valid signature."""
        secret = "test_secret"
        mock_config = MagicMock()
        mock_config.billing_enabled = True
        mock_config.billing_webhook_secret = secret
        mock_get_config.return_value = mock_config

        mock_process.return_value = "Processed successfully"

        app = create_test_app()
        client = TestClient(app)

        # Create payload and signature
        payload = {
            "event": "subscription.created",
            "data": {"organization_id": 1, "tier": "pro"},
        }
        body = json.dumps(payload)
        signature = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/api/v1/billing/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": f"sha256={signature}",
            },
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch("mysql_to_sheets.api.billing_webhook_routes.get_tenant_db_path")
    @patch("mysql_to_sheets.api.billing_webhook_routes._process_billing_event")
    @patch("mysql_to_sheets.api.billing_webhook_routes.get_config")
    def test_webhook_idempotency(self, mock_get_config, mock_process, mock_db_path):
        """Test webhook idempotency handling."""
        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        mock_db_path.return_value = os.path.join(tmp_dir, "test_idemp.db")

        secret = "test_secret_for_idempotency"
        mock_config = MagicMock()
        mock_config.billing_enabled = True
        mock_config.billing_webhook_secret = secret
        mock_get_config.return_value = mock_config

        mock_process.return_value = "Processed"

        app = create_test_app()
        client = TestClient(app)

        # Create payload and signature for first request
        payload1 = {
            "event": "subscription.created",
            "data": {"organization_id": 1, "tier": "pro"},
        }
        body1 = json.dumps(payload1)
        signature1 = hmac.new(
            secret.encode("utf-8"),
            body1.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # First request
        response1 = client.post(
            "/api/v1/billing/webhook",
            content=body1,
            headers={
                "Content-Type": "application/json",
                "X-Idempotency-Key": "unique_key_123",
                "X-Webhook-Signature": f"sha256={signature1}",
            },
        )

        assert response1.status_code == 200
        assert mock_process.call_count == 1

        # Second request with same idempotency key (same body)
        response2 = client.post(
            "/api/v1/billing/webhook",
            content=body1,
            headers={
                "Content-Type": "application/json",
                "X-Idempotency-Key": "unique_key_123",
                "X-Webhook-Signature": f"sha256={signature1}",
            },
        )

        assert response2.status_code == 200
        assert response2.json()["message"] == "Already processed"
        # Should not call process again
        assert mock_process.call_count == 1

    @patch("mysql_to_sheets.api.billing_webhook_routes._process_billing_event")
    @patch("mysql_to_sheets.api.billing_webhook_routes.get_config")
    def test_webhook_process_error_returns_400(self, mock_get_config, mock_process):
        """Test webhook returns 400 on ValueError."""
        secret = "test_secret_for_error"
        mock_config = MagicMock()
        mock_config.billing_enabled = True
        mock_config.billing_webhook_secret = secret
        mock_get_config.return_value = mock_config

        mock_process.side_effect = ValueError("Missing required field")

        app = create_test_app()
        client = TestClient(app)

        # Create payload and signature
        payload = {
            "event": "subscription.created",
            "data": {},
        }
        body = json.dumps(payload)
        signature = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        response = client.post(
            "/api/v1/billing/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": f"sha256={signature}",
            },
        )

        assert response.status_code == 400
        assert "Missing required field" in response.json()["detail"]


class TestUpdateOrganization:
    """Tests for _update_organization function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_update_organization_success(self, mock_get_repo):
        """Test updating organization successfully."""
        from mysql_to_sheets.api.billing_webhook_routes import _update_organization

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.slug = "test-org"
        mock_org.subscription_tier = "free"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        _update_organization(
            organization_id=1,
            billing_customer_id="cus_123",
            subscription_tier="pro",
            billing_status="active",
        )

        assert mock_org.billing_customer_id == "cus_123"
        assert mock_org.subscription_tier == "pro"
        assert mock_org.billing_status == "active"
        mock_repo.update.assert_called_once()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_update_organization_not_found(self, mock_get_repo):
        """Test updating non-existent organization."""
        from mysql_to_sheets.api.billing_webhook_routes import _update_organization

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        mock_get_repo.return_value = mock_repo

        with pytest.raises(ValueError, match="not found"):
            _update_organization(organization_id=999)

    @patch("mysql_to_sheets.core.webhooks.payload.create_subscription_payload")
    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_update_organization_emits_tier_change_webhook(
        self, mock_get_repo, mock_create_payload
    ):
        """Test tier change emits webhook."""
        from mysql_to_sheets.api.billing_webhook_routes import _update_organization

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.slug = "test-org"
        mock_org.subscription_tier = "free"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        _update_organization(
            organization_id=1,
            subscription_tier="pro",
        )

        # Verify webhook payload was created
        mock_create_payload.assert_called_once()
        call_kwargs = mock_create_payload.call_args[1]
        assert call_kwargs["event"] == "subscription.tier_changed"
        assert call_kwargs["old_tier"] == "free"
        assert call_kwargs["new_tier"] == "pro"
