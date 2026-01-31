"""Tests for trial period management module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.config import reset_config
from mysql_to_sheets.core.trial import (
    TrialInfo,
    TrialStatus,
    check_expiring_trials,
    check_trial_status,
    convert_trial,
    expire_trial,
    get_trial_days_remaining,
    get_trial_tier_for_feature_check,
    is_trial_active,
    start_trial,
)


class TestTrialStatus:
    """Tests for TrialStatus enum."""

    def test_trial_status_values(self):
        """Test trial status enum values."""
        assert TrialStatus.ACTIVE.value == "active"
        assert TrialStatus.EXPIRED.value == "expired"
        assert TrialStatus.CONVERTED.value == "converted"
        assert TrialStatus.NONE.value == "none"


class TestTrialInfo:
    """Tests for TrialInfo dataclass."""

    def test_trial_info_creation(self):
        """Test creating trial info."""
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=7)

        info = TrialInfo(
            organization_id=1,
            status=TrialStatus.ACTIVE,
            trial_ends_at=trial_end,
            days_remaining=7,
            billing_status="trialing",
            subscription_tier="pro",
        )

        assert info.organization_id == 1
        assert info.status == TrialStatus.ACTIVE
        assert info.days_remaining == 7
        assert info.billing_status == "trialing"
        assert info.subscription_tier == "pro"

    def test_trial_info_defaults(self):
        """Test trial info default values."""
        info = TrialInfo(
            organization_id=1,
            status=TrialStatus.NONE,
        )

        assert info.trial_ends_at is None
        assert info.days_remaining == 0
        assert info.billing_status == "active"
        assert info.subscription_tier == "free"

    def test_trial_info_to_dict(self):
        """Test converting trial info to dictionary."""
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=7)

        info = TrialInfo(
            organization_id=1,
            status=TrialStatus.ACTIVE,
            trial_ends_at=trial_end,
            days_remaining=7,
        )

        d = info.to_dict()
        assert d["organization_id"] == 1
        assert d["status"] == "active"
        assert d["days_remaining"] == 7
        assert d["trial_ends_at"] is not None


class TestStartTrial:
    """Tests for start_trial function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_start_trial_success(self, mock_get_repo):
        """Test starting a trial successfully."""
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.slug = "test-org"
        mock_org.billing_status = "active"
        mock_org.trial_ends_at = None

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        info = start_trial(organization_id=1, days=14, db_path="/tmp/test.db")

        assert info.status == TrialStatus.ACTIVE
        assert info.days_remaining == 14
        assert info.billing_status == "trialing"
        assert info.subscription_tier == "pro"

        # Verify org was updated
        assert mock_org.billing_status == "trialing"
        assert mock_org.subscription_tier == "pro"
        assert mock_org.trial_ends_at is not None
        mock_repo.update.assert_called_once_with(mock_org)

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_start_trial_org_not_found(self, mock_get_repo):
        """Test starting trial for non-existent org."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        mock_get_repo.return_value = mock_repo

        with pytest.raises(ValueError, match="not found"):
            start_trial(organization_id=999, db_path="/tmp/test.db")

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_start_trial_already_active(self, mock_get_repo):
        """Test starting trial when one is already active."""
        future = datetime.now(timezone.utc) + timedelta(days=5)

        mock_org = MagicMock()
        mock_org.billing_status = "trialing"
        mock_org.trial_ends_at = future

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        with pytest.raises(ValueError, match="already has an active trial"):
            start_trial(organization_id=1, db_path="/tmp/test.db")


class TestCheckTrialStatus:
    """Tests for check_trial_status function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_trial_status_active(self, mock_get_repo):
        """Test checking active trial status."""
        future = datetime.now(timezone.utc) + timedelta(days=7)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "trialing"
        mock_org.trial_ends_at = future
        mock_org.subscription_tier = "pro"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        info = check_trial_status(organization_id=1, db_path="/tmp/test.db")

        assert info.status == TrialStatus.ACTIVE
        assert info.days_remaining > 0

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_trial_status_expired(self, mock_get_repo):
        """Test checking expired trial status."""
        past = datetime.now(timezone.utc) - timedelta(days=7)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "trialing"
        mock_org.trial_ends_at = past
        mock_org.subscription_tier = "pro"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        info = check_trial_status(organization_id=1, db_path="/tmp/test.db")

        assert info.status == TrialStatus.EXPIRED
        assert info.days_remaining == 0

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_trial_status_converted(self, mock_get_repo):
        """Test checking converted trial status."""
        past = datetime.now(timezone.utc) - timedelta(days=7)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "active"
        mock_org.trial_ends_at = past
        mock_org.subscription_tier = "pro"  # Paid tier after trial

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        info = check_trial_status(organization_id=1, db_path="/tmp/test.db")

        assert info.status == TrialStatus.CONVERTED

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_trial_status_none(self, mock_get_repo):
        """Test checking when no trial was started."""
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "active"
        mock_org.trial_ends_at = None
        mock_org.subscription_tier = "free"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        info = check_trial_status(organization_id=1, db_path="/tmp/test.db")

        assert info.status == TrialStatus.NONE
        assert info.days_remaining == 0

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_trial_status_org_not_found(self, mock_get_repo):
        """Test checking trial status for non-existent org."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        mock_get_repo.return_value = mock_repo

        with pytest.raises(ValueError, match="not found"):
            check_trial_status(organization_id=999, db_path="/tmp/test.db")


class TestTrialHelperFunctions:
    """Tests for trial helper functions."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.core.billing.trial.check_trial_status")
    def test_get_trial_days_remaining(self, mock_check):
        """Test getting trial days remaining."""
        mock_check.return_value = TrialInfo(
            organization_id=1,
            status=TrialStatus.ACTIVE,
            days_remaining=10,
        )

        days = get_trial_days_remaining(organization_id=1, db_path="/tmp/test.db")

        assert days == 10

    @patch("mysql_to_sheets.core.billing.trial.check_trial_status")
    def test_is_trial_active_true(self, mock_check):
        """Test checking if trial is active when it is."""
        mock_check.return_value = TrialInfo(
            organization_id=1,
            status=TrialStatus.ACTIVE,
        )

        result = is_trial_active(organization_id=1, db_path="/tmp/test.db")

        assert result is True

    @patch("mysql_to_sheets.core.billing.trial.check_trial_status")
    def test_is_trial_active_false(self, mock_check):
        """Test checking if trial is active when it's not."""
        mock_check.return_value = TrialInfo(
            organization_id=1,
            status=TrialStatus.EXPIRED,
        )

        result = is_trial_active(organization_id=1, db_path="/tmp/test.db")

        assert result is False


class TestExpireTrial:
    """Tests for expire_trial function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.core.billing.trial.check_trial_status")
    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_expire_trial_success(self, mock_get_repo, mock_check):
        """Test expiring a trial successfully."""
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "trialing"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        mock_check.return_value = TrialInfo(
            organization_id=1,
            status=TrialStatus.EXPIRED,
        )

        info = expire_trial(organization_id=1, db_path="/tmp/test.db")

        # Verify org was updated
        assert mock_org.billing_status == "active"
        assert mock_org.subscription_tier == "free"
        mock_repo.update.assert_called_once()

    @patch("mysql_to_sheets.core.billing.trial.check_trial_status")
    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_expire_trial_not_on_trial(self, mock_get_repo, mock_check):
        """Test expiring when not on trial."""
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "active"  # Not on trial

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        mock_check.return_value = TrialInfo(
            organization_id=1,
            status=TrialStatus.NONE,
        )

        expire_trial(organization_id=1, db_path="/tmp/test.db")

        # Should not update if not on trial
        mock_repo.update.assert_not_called()


class TestConvertTrial:
    """Tests for convert_trial function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.core.billing.trial.check_trial_status")
    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_convert_trial_success(self, mock_get_repo, mock_check):
        """Test converting a trial to paid subscription."""
        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.slug = "test-org"
        mock_org.billing_status = "trialing"
        mock_org.subscription_tier = "pro"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        mock_check.return_value = TrialInfo(
            organization_id=1,
            status=TrialStatus.CONVERTED,
        )

        info = convert_trial(
            organization_id=1,
            new_tier="business",
            billing_customer_id="cus_123",
            db_path="/tmp/test.db",
        )

        # Verify org was updated
        assert mock_org.subscription_tier == "business"
        assert mock_org.billing_status == "active"
        assert mock_org.billing_customer_id == "cus_123"
        mock_repo.update.assert_called_once()


class TestCheckExpiringTrials:
    """Tests for check_expiring_trials function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_expiring_trials_finds_expiring(self, mock_get_repo):
        """Test finding trials that are expiring soon."""
        now = datetime.now(timezone.utc)
        expiring_soon = now + timedelta(days=2)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.slug = "test-org"
        mock_org.billing_status = "trialing"
        mock_org.trial_ends_at = expiring_soon
        mock_org.subscription_tier = "pro"

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [mock_org]
        mock_get_repo.return_value = mock_repo

        expiring = check_expiring_trials(days_threshold=3, db_path="/tmp/test.db")

        assert len(expiring) == 1
        assert expiring[0].organization_id == 1
        assert expiring[0].status == TrialStatus.ACTIVE

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_check_expiring_trials_ignores_not_expiring(self, mock_get_repo):
        """Test ignoring trials not expiring soon."""
        now = datetime.now(timezone.utc)
        far_future = now + timedelta(days=30)

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.billing_status = "trialing"
        mock_org.trial_ends_at = far_future
        mock_org.subscription_tier = "pro"

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [mock_org]
        mock_get_repo.return_value = mock_repo

        expiring = check_expiring_trials(days_threshold=3, db_path="/tmp/test.db")

        assert len(expiring) == 0


class TestGetTrialTierForFeatureCheck:
    """Tests for get_trial_tier_for_feature_check function."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_returns_pro_for_active_trial(self, mock_get_repo):
        """Test returns PRO tier for active trial."""
        future = datetime.now(timezone.utc) + timedelta(days=7)

        mock_org = MagicMock()
        mock_org.billing_status = "trialing"
        mock_org.trial_ends_at = future
        mock_org.subscription_tier = "free"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        tier = get_trial_tier_for_feature_check(organization_id=1, db_path="/tmp/test.db")

        assert tier == "pro"

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_returns_actual_tier_when_not_on_trial(self, mock_get_repo):
        """Test returns actual tier when not on trial."""
        mock_org = MagicMock()
        mock_org.billing_status = "active"
        mock_org.trial_ends_at = None
        mock_org.subscription_tier = "business"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_org
        mock_get_repo.return_value = mock_repo

        tier = get_trial_tier_for_feature_check(organization_id=1, db_path="/tmp/test.db")

        assert tier == "business"

    @patch("mysql_to_sheets.models.organizations.get_organization_repository")
    def test_returns_free_on_error(self, mock_get_repo):
        """Test returns free tier on error."""
        mock_get_repo.side_effect = RuntimeError("Database error")

        tier = get_trial_tier_for_feature_check(organization_id=1, db_path="/tmp/test.db")

        assert tier == "free"
