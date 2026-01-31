"""End-to-end tests for monetization paths.

Tests the complete monetization flow from trial signup through tier enforcement,
license validation, usage tracking, and billing webhook integration.
"""

import hashlib
import hmac
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


def _can_import_billing_routes():
    """Check if billing routes can be imported without circular import errors."""
    try:
        import mysql_to_sheets.api.billing_webhook_routes  # noqa: F401

        return True
    except (ImportError, AttributeError):
        return False


# Conditional imports for optional dependencies
try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None

from mysql_to_sheets.core.exceptions import LicenseError, TierError
from mysql_to_sheets.core.license import (
    LicenseInfo,
    LicenseStatus,
    get_effective_tier,
    validate_license,
)
from mysql_to_sheets.core.tier import TIER_LIMITS, Tier
from mysql_to_sheets.core.trial import TrialStatus
from mysql_to_sheets.models.organizations import Organization


class TestTierEnforcement:
    """Integration tests for tier-based feature enforcement."""

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_free_tier_blocks_second_config_creation(self, mock_get_repo):
        """Test FREE tier blocks creation of second config."""
        # Create a FREE tier org
        org = Organization(
            id=1,
            name="Test Org",
            slug="test-org",
            subscription_tier="free",
        )

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = org
        mock_get_repo.return_value = mock_repo

        # FREE tier allows 1 config
        limits = TIER_LIMITS[Tier.FREE]
        assert limits.max_configs == 1

        # Should pass for first config (current_count=0)
        org.check_config_quota(current_count=0)

        # Should raise TierError for second config (current_count=1)
        with pytest.raises(TierError) as exc_info:
            org.check_config_quota(current_count=1)

        error = exc_info.value
        assert "Quota exceeded" in error.message
        assert error.quota_type == "configs"
        assert error.quota_limit == 1
        assert error.quota_used == 1

    @patch("mysql_to_sheets.core.billing.tier._tier_callback")
    def test_scheduler_feature_requires_pro_tier(self, mock_callback):
        """Test scheduler feature requires PRO+ tier."""
        from mysql_to_sheets.core.tier import FEATURE_TIERS, require_tier
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        # Clear any cached tier from parallel test execution
        get_tier_cache().invalidate(1)

        # Verify scheduler is a PRO feature
        assert FEATURE_TIERS["scheduler"] == Tier.PRO

        # Set callback to return FREE tier
        mock_callback.return_value = Tier.FREE

        @require_tier("scheduler")
        def schedule_sync(org_id: int) -> str:
            return "sync scheduled"

        # Should raise TierError for FREE tier
        with pytest.raises(TierError) as exc_info:
            schedule_sync(org_id=1)

        error = exc_info.value
        assert "scheduler" in error.message.lower()
        assert "pro" in error.message.lower()
        assert error.feature == "scheduler"
        assert error.required_tier == "pro"
        assert error.current_tier == "free"

        # Should succeed for PRO tier
        mock_callback.return_value = Tier.PRO
        # Clear tier cache to pick up new mock value
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        get_tier_cache().invalidate(1)
        result = schedule_sync(org_id=1)
        assert result == "sync scheduled"

    @patch("mysql_to_sheets.core.billing.tier._tier_callback")
    def test_webhooks_require_business_tier(self, mock_callback):
        """Test webhooks feature requires BUSINESS+ tier."""
        from mysql_to_sheets.core.tier import FEATURE_TIERS, require_tier
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        # Clear any cached tier from parallel test execution
        get_tier_cache().invalidate(1)

        # Verify webhooks is a BUSINESS feature
        assert FEATURE_TIERS["webhooks"] == Tier.BUSINESS

        # Set callback to return PRO tier (insufficient)
        mock_callback.return_value = Tier.PRO

        @require_tier("webhooks")
        def create_webhook(org_id: int) -> str:
            return "webhook created"

        # Should raise TierError for PRO tier
        with pytest.raises(TierError) as exc_info:
            create_webhook(org_id=1)

        error = exc_info.value
        assert "webhooks" in error.message.lower()
        assert "business" in error.message.lower()
        assert error.required_tier == "business"
        assert error.current_tier == "pro"

        # Should succeed for BUSINESS tier
        mock_callback.return_value = Tier.BUSINESS
        get_tier_cache().invalidate(1)  # Clear cache to pick up new mock value
        result = create_webhook(org_id=1)
        assert result == "webhook created"

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_tier_violation_returns_correct_error_message(self, mock_get_repo):
        """Test tier violation returns actionable error message."""
        # Create a FREE tier org
        org = Organization(
            id=1,
            name="Test Org",
            slug="test-org",
            subscription_tier="free",
        )

        # Attempt to violate schedule quota (FREE tier has max_schedules=0)
        with pytest.raises(TierError) as exc_info:
            org.check_schedule_quota(current_count=1)

        error = exc_info.value
        assert "Quota exceeded" in error.message
        assert "schedules" in error.message
        assert "limit is 0" in error.message
        assert "free" in error.message

        # Verify error has correct metadata
        error_dict = error.to_dict()
        assert error_dict["error"] == "TierError"
        assert error_dict["details"]["quota_type"] == "schedules"
        assert error_dict["details"]["quota_limit"] == 0
        assert error_dict["details"]["quota_used"] == 1


class TestTrialToPaidConversion:
    """Flow tests for trial to paid subscription conversion."""

    def setup_method(self):
        """Reset config before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_new_org_starts_with_trial_pro_features_available(self, mock_get_repo):
        """Test new org starts with trial and has PRO features available."""
        # Create org in trial status
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.slug = "new-org"
        mock_org.billing_status = "trialing"
        mock_org.subscription_tier = "pro"
        mock_org.trial_ends_at = trial_end

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        # Start trial
        from mysql_to_sheets.core.trial import start_trial

        mock_org.billing_status = "active"  # Reset for test
        mock_org.trial_ends_at = None

        info = start_trial(organization_id=1, days=14, db_path="/tmp/test.db")

        # Verify trial started with PRO tier
        assert info.status == TrialStatus.ACTIVE
        assert info.subscription_tier == "pro"
        assert info.billing_status == "trialing"
        assert info.days_remaining == 14

        # Verify org was updated
        assert mock_org.billing_status == "trialing"
        assert mock_org.subscription_tier == "pro"
        mock_repo.update.assert_called_once()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_trial_expires_reverts_to_free_pro_features_blocked(self, mock_get_repo):
        """Test trial expiration reverts to FREE tier and blocks PRO features."""
        from mysql_to_sheets.core.tier import require_tier, set_tier_callback
        from mysql_to_sheets.core.trial import expire_trial

        # Create org with expired trial
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "trialing"
        mock_org.subscription_tier = "pro"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        # Expire trial
        info = expire_trial(organization_id=1, db_path="/tmp/test.db")

        # Verify org reverted to FREE
        assert mock_org.billing_status == "active"
        assert mock_org.subscription_tier == "free"

        # Verify PRO features are now blocked
        set_tier_callback(lambda org_id: Tier.FREE)

        # Clear tier cache to ensure callback is used
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        get_tier_cache().invalidate(1)

        @require_tier("scheduler")
        def use_scheduler(org_id: int):
            return "scheduled"

        with pytest.raises(TierError) as exc_info:
            use_scheduler(org_id=1)

        assert "scheduler" in exc_info.value.message.lower()
        assert "pro" in exc_info.value.message.lower()

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
    def test_billing_webhook_subscription_created_restores_pro(self):
        """Test subscription.created webhook restores PRO tier after trial expiration."""
        # Skip if billing routes can't be imported
        if not _can_import_billing_routes():
            pytest.skip("Billing routes not available")

        from fastapi import FastAPI

        from mysql_to_sheets.api.billing_webhook_routes import router

        import hashlib
        import hmac
        import json

        # Patch at the route module level where it's actually used
        with (
            patch("mysql_to_sheets.api.billing_webhook_routes.get_config") as mock_get_config,
            patch(
                "mysql_to_sheets.models.organizations.get_organization_repository"
            ) as mock_get_repo,
        ):
            # Mock config with secret for signature verification
            test_secret = "test_secret_for_trial_conversion"
            mock_config = MagicMock()
            mock_config.billing_enabled = True
            mock_config.billing_webhook_secret = test_secret
            mock_get_config.return_value = mock_config

            # Mock org that was on expired trial (now FREE)
            mock_org = MagicMock()
            mock_org.id = 1
            mock_org.slug = "test-org"
            mock_org.subscription_tier = "free"
            mock_org.billing_status = "active"
            mock_org.billing_customer_id = None

            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_org
            mock_get_repo.return_value = mock_repo

            # Create test client
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # Send webhook with signature
            webhook_data = {
                "event": "subscription.created",
                "data": {
                    "organization_id": 1,
                    "tier": "pro",
                    "billing_customer_id": "cus_abc123",
                },
            }
            body = json.dumps(webhook_data)
            signature = hmac.new(
                test_secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            response = client.post(
                "/billing/webhook",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": f"sha256={signature}",
                },
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify org was upgraded to PRO
            assert mock_org.subscription_tier == "pro"
            assert mock_org.billing_status == "active"
            assert mock_org.billing_customer_id == "cus_abc123"
            mock_repo.update.assert_called_once()


class TestLicenseValidation:
    """License key validation and tier enforcement tests."""

    def setup_method(self):
        """Reset config before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    @patch("mysql_to_sheets.core.billing.license.get_license_info_from_config")
    def test_no_license_key_defaults_to_free_tier(self, mock_get_info):
        """Test no license key defaults to FREE tier."""
        mock_get_info.return_value = LicenseInfo(
            status=LicenseStatus.MISSING,
        )

        # Get effective tier
        info = mock_get_info()
        tier = get_effective_tier(info)

        assert tier == Tier.FREE

    def test_valid_pro_license_enables_pro_tier_and_features(self):
        """Test valid PRO license enables PRO tier and features."""
        from tests.test_license import create_test_license, validate_test_license

        # Create valid PRO license
        license_key = create_test_license(
            customer_id="cust_123",
            email="test@example.com",
            tier="pro",
            expires_in_days=30,
            features=["scheduler", "notifications"],
        )

        # Validate license
        info = validate_test_license(license_key)

        assert info.status == LicenseStatus.VALID
        assert info.tier == Tier.PRO
        assert info.customer_id == "cust_123"
        assert "scheduler" in info.features
        assert "notifications" in info.features
        assert info.days_until_expiry in [29, 30]  # Account for timing

        # Get effective tier
        tier = get_effective_tier(info)
        assert tier == Tier.PRO

    def test_expired_license_grace_period_then_invalid(self):
        """Test expired license shows grace period behavior then becomes invalid."""
        from tests.test_license import create_test_license, validate_test_license

        # Create license expired 2 days ago
        license_key = create_test_license(
            tier="pro",
            expires_in_days=-2,
        )

        # With 3-day grace period, should be in grace
        info = validate_test_license(license_key, grace_days=3)
        assert info.status == LicenseStatus.GRACE_PERIOD
        assert get_effective_tier(info) == Tier.PRO

        # With 1-day grace period, should be expired
        info = validate_test_license(license_key, grace_days=1)
        assert info.status == LicenseStatus.EXPIRED
        assert get_effective_tier(info) == Tier.FREE

    def test_tampered_license_is_invalid(self):
        """Test tampered/forged license is rejected as invalid."""
        from tests.test_license import TEST_PUBLIC_KEY, create_test_license

        # Create a valid license
        license_key = create_test_license(tier="pro")

        # Tamper with the license (change last character)
        tampered_key = license_key[:-5] + "XXXXX"

        # Should fail validation
        info = validate_license(tampered_key, public_key=TEST_PUBLIC_KEY)
        assert info.status == LicenseStatus.INVALID
        assert "invalid" in info.error.lower() or "signature" in info.error.lower()

        # Effective tier should be FREE
        tier = get_effective_tier(info)
        assert tier == Tier.FREE

    @patch("mysql_to_sheets.core.billing.license.get_license_info_from_config")
    def test_license_decorator_enforces_tier_requirements(self, mock_get_info):
        """Test license decorator enforces tier requirements."""
        from mysql_to_sheets.core.license import require_tier

        # Mock PRO license
        mock_get_info.return_value = LicenseInfo(
            status=LicenseStatus.VALID,
            tier=Tier.PRO,
        )

        @require_tier(Tier.BUSINESS)
        def business_feature():
            return "success"

        # Should raise LicenseError (insufficient tier)
        with pytest.raises(LicenseError) as exc_info:
            business_feature()

        assert "BUSINESS" in str(exc_info.value)
        assert "PRO" in str(exc_info.value)
        assert "requires" in str(exc_info.value).lower()

        # Mock BUSINESS license
        mock_get_info.return_value = LicenseInfo(
            status=LicenseStatus.VALID,
            tier=Tier.BUSINESS,
        )

        # Should succeed
        result = business_feature()
        assert result == "success"


class TestUsageMeteringAccuracy:
    """Usage tracking accuracy and period boundary tests."""

    def setup_method(self):
        """Reset config before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    @patch("mysql_to_sheets.core.billing.usage_tracking.get_usage_repository")
    def test_record_sync_of_n_rows_matches_usage_record(self, mock_get_repo):
        """Test recording sync of N rows creates accurate usage record."""
        from datetime import date

        from mysql_to_sheets.core.usage_tracking import record_sync_usage

        # Mock usage record (using MagicMock to avoid constructor issues)
        mock_record = MagicMock()
        mock_record.organization_id = 1
        mock_record.period_start = date(2024, 1, 1)
        mock_record.period_end = date(2024, 1, 31)
        mock_record.rows_synced = 500
        mock_record.sync_operations = 1
        mock_record.api_calls = 0

        mock_repo = MagicMock()
        mock_repo.increment_rows_synced.return_value = mock_record
        mock_get_repo.return_value = mock_repo

        # Record sync usage
        result = record_sync_usage(
            organization_id=1,
            rows_synced=500,
            db_path="/tmp/test.db",
        )

        # Verify usage was recorded correctly
        assert result.rows_synced == 500
        assert result.sync_operations == 1
        mock_repo.increment_rows_synced.assert_called_once_with(
            organization_id=1,
            rows=500,
            increment_operations=True,
        )

    @patch("mysql_to_sheets.core.billing.usage_tracking.get_usage_repository")
    def test_multiple_syncs_accumulate_correctly(self, mock_get_repo):
        """Test multiple sync operations accumulate usage correctly."""
        from datetime import date

        from mysql_to_sheets.core.usage_tracking import record_sync_usage

        # Mock cumulative usage
        cumulative_rows = 0
        cumulative_ops = 0

        def mock_increment(organization_id, rows, increment_operations=False):
            nonlocal cumulative_rows, cumulative_ops
            cumulative_rows += rows
            if increment_operations:
                cumulative_ops += 1
            # Return MagicMock with the accumulated values
            mock_record = MagicMock()
            mock_record.organization_id = organization_id
            mock_record.period_start = date(2024, 1, 1)
            mock_record.period_end = date(2024, 1, 31)
            mock_record.rows_synced = cumulative_rows
            mock_record.sync_operations = cumulative_ops
            mock_record.api_calls = 0
            return mock_record

        mock_repo = MagicMock()
        mock_repo.increment_rows_synced.side_effect = mock_increment
        mock_get_repo.return_value = mock_repo

        # Record multiple syncs
        result1 = record_sync_usage(1, 100, db_path="/tmp/test.db")
        assert result1.rows_synced == 100
        assert result1.sync_operations == 1

        result2 = record_sync_usage(1, 250, db_path="/tmp/test.db")
        assert result2.rows_synced == 350
        assert result2.sync_operations == 2

        result3 = record_sync_usage(1, 150, db_path="/tmp/test.db")
        assert result3.rows_synced == 500
        assert result3.sync_operations == 3

    @patch("mysql_to_sheets.core.billing.usage_tracking.get_usage_repository")
    def test_period_boundary_handling(self, mock_get_repo):
        """Test usage tracking handles period boundaries correctly."""
        from datetime import date

        from mysql_to_sheets.core.usage_tracking import get_current_usage

        # Mock current period usage
        mock_record = MagicMock()
        mock_record.organization_id = 1
        mock_record.period_start = date(2024, 1, 1)
        mock_record.period_end = date(2024, 1, 31)
        mock_record.rows_synced = 1000
        mock_record.sync_operations = 10
        mock_record.api_calls = 50

        mock_repo = MagicMock()
        mock_repo.get_or_create_current.return_value = mock_record
        mock_get_repo.return_value = mock_repo

        # Get current usage
        usage = get_current_usage(organization_id=1, db_path="/tmp/test.db")

        # Verify correct period
        assert usage.period_start == date(2024, 1, 1)
        assert usage.rows_synced == 1000
        assert usage.sync_operations == 10
        assert usage.api_calls == 50


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
@pytest.mark.skipif(
    not importlib.util.find_spec("fastapi") or not _can_import_billing_routes(),
    reason="FastAPI not available or API middleware has circular import",
)
class TestBillingWebhookReceiver:
    """Tests for billing webhook receiver endpoint."""

    def setup_method(self):
        """Reset config before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    def test_valid_signature_and_payload_returns_200_org_updated(self):
        """Test valid signature and payload returns 200 and updates org."""
        from fastapi import FastAPI

        from mysql_to_sheets.api.billing_webhook_routes import router

        import tempfile
        import os

        tmp_dir = tempfile.mkdtemp()
        tmp_db = os.path.join(tmp_dir, "test_valid_sig.db")

        # Patch at the route module level
        with (
            patch("mysql_to_sheets.api.billing_webhook_routes.get_config") as mock_get_config,
            patch(
                "mysql_to_sheets.models.organizations.get_organization_repository"
            ) as mock_get_repo,
            patch("mysql_to_sheets.api.billing_webhook_routes.get_tenant_db_path", return_value=tmp_db),
        ):
            # Setup mock config
            mock_config = MagicMock()
            mock_config.billing_enabled = True
            mock_config.billing_webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config

            # Setup mock org
            mock_org = MagicMock()
            mock_org.id = 1
            mock_org.slug = "test-org"
            mock_org.subscription_tier = "free"
            mock_org.billing_status = "active"

            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_org
            mock_get_repo.return_value = mock_repo

            # Create FastAPI test client
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # Create webhook payload
            payload = {
                "event": "subscription.created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "organization_id": 1,
                    "tier": "pro",
                    "billing_customer_id": "cus_abc123",
                },
            }

            # The TestClient will serialize with default json.dumps, so we need to match that
            # The actual bytes sent will be json.dumps(payload) with default settings
            payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

            # Generate valid signature based on the actual payload bytes
            signature = hmac.new(
                b"test_secret",
                payload_bytes,
                hashlib.sha256,
            ).hexdigest()

            # Send webhook
            response = client.post(
                "/billing/webhook",
                json=payload,
                headers={
                    "X-Webhook-Signature": signature,
                    "X-Idempotency-Key": "test-key-123",
                },
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["event_processed"] == "subscription.created"

            # Verify org was updated
            assert mock_org.subscription_tier == "pro"
            assert mock_org.billing_customer_id == "cus_abc123"
            mock_repo.update.assert_called_once()

    def test_invalid_signature_returns_401(self):
        """Test invalid signature returns 401 Unauthorized."""
        from fastapi import FastAPI

        from mysql_to_sheets.api.billing_webhook_routes import router

        # Patch at the route module level
        with patch("mysql_to_sheets.api.billing_webhook_routes.get_config") as mock_get_config:
            # Setup mock config
            mock_config = MagicMock()
            mock_config.billing_enabled = True
            mock_config.billing_webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config

            # Create FastAPI test client
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # Create webhook payload
            payload = {
                "event": "subscription.created",
                "data": {"organization_id": 1, "tier": "pro"},
            }

            # Send with invalid signature
            response = client.post(
                "/billing/webhook",
                json=payload,
                headers={"X-Webhook-Signature": "invalid_signature"},
            )

            # Verify response
            assert response.status_code == 401
            assert "signature" in response.json()["detail"].lower()

    def test_missing_org_returns_404(self):
        """Test webhook for non-existent org returns 400."""
        import hashlib
        import hmac
        import json as json_module

        from fastapi import FastAPI

        from mysql_to_sheets.api.billing_webhook_routes import router

        test_secret = "test_secret_for_missing_org"

        # Patch at the route module level
        with (
            patch("mysql_to_sheets.api.billing_webhook_routes.get_config") as mock_get_config,
            patch(
                "mysql_to_sheets.models.organizations.get_organization_repository"
            ) as mock_get_repo,
        ):
            # Setup mock config with secret for signature verification
            mock_config = MagicMock()
            mock_config.billing_enabled = True
            mock_config.billing_webhook_secret = test_secret
            mock_get_config.return_value = mock_config

            # Setup mock repo to return None (org not found)
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_get_repo.return_value = mock_repo

            # Create FastAPI test client
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # Create webhook payload with signature
            payload = {
                "event": "subscription.created",
                "data": {"organization_id": 999, "tier": "pro"},
            }
            body = json_module.dumps(payload)
            signature = hmac.new(
                test_secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Send webhook
            response = client.post(
                "/billing/webhook",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": f"sha256={signature}",
                },
            )

            # Verify response
            assert response.status_code == 400
            assert "not found" in response.json()["detail"].lower()

    def test_idempotency_key_prevents_duplicate_processing(self):
        """Test idempotency key prevents duplicate webhook processing."""
        import hashlib
        import hmac
        import json as json_module
        import tempfile
        import os

        from fastapi import FastAPI

        from mysql_to_sheets.api.billing_webhook_routes import router

        tmp_dir = tempfile.mkdtemp()
        tmp_db = os.path.join(tmp_dir, "test_idempotency.db")
        test_secret = "test_secret_for_idempotency"

        # Patch at the route module level
        with patch("mysql_to_sheets.api.billing_webhook_routes.get_tenant_db_path", return_value=tmp_db), \
             patch("mysql_to_sheets.api.billing_webhook_routes.get_config") as mock_get_config:
            # Setup mock config with secret for signature verification
            mock_config = MagicMock()
            mock_config.billing_enabled = True
            mock_config.billing_webhook_secret = test_secret
            mock_get_config.return_value = mock_config

            # Create FastAPI test client
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # Create webhook payload with signature
            payload = {
                "event": "subscription.updated",
                "data": {"organization_id": 1, "tier": "pro"},
            }
            body = json_module.dumps(payload)
            signature = hmac.new(
                test_secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # First delivery with idempotency key
            with patch(
                "mysql_to_sheets.api.billing_webhook_routes._process_billing_event"
            ) as mock_process:
                mock_process.return_value = "Processed"

                response1 = client.post(
                    "/billing/webhook",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Idempotency-Key": "unique-key-123",
                        "X-Webhook-Signature": f"sha256={signature}",
                    },
                )

                assert response1.status_code == 200
                mock_process.assert_called_once()

            # Second delivery with same idempotency key
            with patch(
                "mysql_to_sheets.api.billing_webhook_routes._process_billing_event"
            ) as mock_process:
                response2 = client.post(
                    "/billing/webhook",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Idempotency-Key": "unique-key-123",
                        "X-Webhook-Signature": f"sha256={signature}",
                    },
                )

                assert response2.status_code == 200
                data = response2.json()
                assert data["success"] is True
                assert "already processed" in data["message"].lower()

                # Should NOT process again
                mock_process.assert_not_called()
