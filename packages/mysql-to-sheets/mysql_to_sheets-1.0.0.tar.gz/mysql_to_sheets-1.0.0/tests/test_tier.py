"""Tests for the tier module."""

import pytest

from mysql_to_sheets.core.tier import (
    FEATURE_TIERS,
    TIER_LIMITS,
    Tier,
    TierError,
    check_feature_access,
    check_quota,
    enforce_quota,
    get_feature_tier,
    get_tier_display_info,
    get_tier_limits,
    get_upgrade_suggestions,
    require_tier,
    set_tier_callback,
    tier_allows,
)


class TestTierEnum:
    """Tests for the Tier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert Tier.FREE.value == "free"
        assert Tier.PRO.value == "pro"
        assert Tier.BUSINESS.value == "business"
        assert Tier.ENTERPRISE.value == "enterprise"

    def test_tier_comparison_less_than(self):
        """Test tier less than comparison."""
        assert Tier.FREE < Tier.PRO
        assert Tier.PRO < Tier.BUSINESS
        assert Tier.BUSINESS < Tier.ENTERPRISE
        assert not Tier.ENTERPRISE < Tier.FREE

    def test_tier_comparison_less_equal(self):
        """Test tier less than or equal comparison."""
        assert Tier.FREE <= Tier.FREE
        assert Tier.FREE <= Tier.PRO
        assert Tier.PRO <= Tier.BUSINESS
        assert not Tier.ENTERPRISE <= Tier.BUSINESS

    def test_tier_comparison_greater_than(self):
        """Test tier greater than comparison."""
        assert Tier.PRO > Tier.FREE
        assert Tier.BUSINESS > Tier.PRO
        assert Tier.ENTERPRISE > Tier.BUSINESS
        assert not Tier.FREE > Tier.PRO

    def test_tier_comparison_greater_equal(self):
        """Test tier greater than or equal comparison."""
        assert Tier.PRO >= Tier.PRO
        assert Tier.PRO >= Tier.FREE
        assert Tier.ENTERPRISE >= Tier.BUSINESS
        assert not Tier.FREE >= Tier.PRO


class TestTierLimits:
    """Tests for TierLimits dataclass."""

    def test_free_tier_limits(self):
        """Test free tier limits."""
        limits = TIER_LIMITS[Tier.FREE]

        assert limits.max_configs == 1
        assert limits.max_users == 1
        assert limits.history_days == 7
        assert limits.max_schedules == 0  # No scheduling
        assert limits.max_webhooks == 0

    def test_pro_tier_limits(self):
        """Test pro tier limits."""
        limits = TIER_LIMITS[Tier.PRO]

        assert limits.max_configs == 10
        assert limits.max_users == 1
        assert limits.history_days == 30
        assert limits.max_schedules == 5
        assert limits.max_webhooks == 3

    def test_business_tier_limits(self):
        """Test business tier limits."""
        limits = TIER_LIMITS[Tier.BUSINESS]

        assert limits.max_configs == 50
        assert limits.max_users == 5
        assert limits.history_days == 90
        assert limits.max_schedules == 25
        assert limits.max_webhooks == 10

    def test_enterprise_tier_limits(self):
        """Test enterprise tier limits (unlimited)."""
        limits = TIER_LIMITS[Tier.ENTERPRISE]

        assert limits.max_configs is None  # Unlimited
        assert limits.max_users is None
        assert limits.history_days is None
        assert limits.max_schedules is None
        assert limits.max_webhooks is None


class TestGetTierLimits:
    """Tests for get_tier_limits function."""

    def test_get_tier_limits_with_enum(self):
        """Test getting limits with Tier enum."""
        limits = get_tier_limits(Tier.PRO)
        assert limits.max_configs == 10

    def test_get_tier_limits_with_string(self):
        """Test getting limits with string."""
        limits = get_tier_limits("pro")
        assert limits.max_configs == 10

    def test_get_tier_limits_case_insensitive(self):
        """Test getting limits is case insensitive."""
        limits = get_tier_limits("PRO")
        assert limits.max_configs == 10

    def test_get_tier_limits_unknown_tier(self):
        """Test getting limits for unknown tier."""
        with pytest.raises(ValueError, match="Unknown tier"):
            get_tier_limits("invalid")


class TestFeatureTiers:
    """Tests for feature tier mapping."""

    def test_free_features(self):
        """Test free tier features."""
        assert FEATURE_TIERS["sync"] == Tier.FREE
        assert FEATURE_TIERS["validate"] == Tier.FREE

    def test_pro_features(self):
        """Test pro tier features."""
        assert FEATURE_TIERS["scheduler"] == Tier.PRO
        assert FEATURE_TIERS["reverse_sync"] == Tier.PRO
        assert FEATURE_TIERS["notifications"] == Tier.PRO

    def test_business_features(self):
        """Test business tier features."""
        assert FEATURE_TIERS["multi_sheet"] == Tier.BUSINESS
        assert FEATURE_TIERS["webhooks"] == Tier.BUSINESS
        assert FEATURE_TIERS["audit_logs"] == Tier.BUSINESS

    def test_enterprise_features(self):
        """Test enterprise tier features."""
        assert FEATURE_TIERS["sso"] == Tier.ENTERPRISE
        assert FEATURE_TIERS["data_masking"] == Tier.ENTERPRISE

    def test_get_feature_tier(self):
        """Test get_feature_tier function."""
        assert get_feature_tier("scheduler") == Tier.PRO
        assert get_feature_tier("multi_sheet") == Tier.BUSINESS

    def test_get_feature_tier_unknown(self):
        """Test get_feature_tier for unknown feature."""
        with pytest.raises(ValueError, match="Unknown feature"):
            get_feature_tier("unknown_feature")


class TestTierAllows:
    """Tests for tier_allows function."""

    def test_same_tier_allowed(self):
        """Test same tier is allowed."""
        assert tier_allows(Tier.PRO, Tier.PRO) is True

    def test_higher_tier_allowed(self):
        """Test higher tier is allowed."""
        assert tier_allows(Tier.ENTERPRISE, Tier.PRO) is True

    def test_lower_tier_not_allowed(self):
        """Test lower tier is not allowed."""
        assert tier_allows(Tier.FREE, Tier.PRO) is False

    def test_tier_allows_with_strings(self):
        """Test tier_allows with string inputs."""
        assert tier_allows("pro", "free") is True
        assert tier_allows("free", "pro") is False


class TestCheckFeatureAccess:
    """Tests for check_feature_access function."""

    def test_free_tier_can_access_free_features(self):
        """Test free tier can access free features."""
        assert check_feature_access(Tier.FREE, "sync") is True

    def test_free_tier_cannot_access_pro_features(self):
        """Test free tier cannot access pro features."""
        assert check_feature_access(Tier.FREE, "scheduler") is False

    def test_pro_tier_can_access_pro_features(self):
        """Test pro tier can access pro features."""
        assert check_feature_access(Tier.PRO, "scheduler") is True

    def test_enterprise_can_access_all_features(self):
        """Test enterprise tier can access all features."""
        assert check_feature_access(Tier.ENTERPRISE, "sync") is True
        assert check_feature_access(Tier.ENTERPRISE, "scheduler") is True
        assert check_feature_access(Tier.ENTERPRISE, "sso") is True


class TestCheckQuota:
    """Tests for check_quota function."""

    def test_within_quota(self):
        """Test count within quota."""
        is_within, limit = check_quota(Tier.PRO, "configs", 5)
        assert is_within is True
        assert limit == 10

    def test_at_quota_limit(self):
        """Test count at quota limit."""
        is_within, limit = check_quota(Tier.PRO, "configs", 10)
        assert is_within is False
        assert limit == 10

    def test_over_quota(self):
        """Test count over quota."""
        is_within, limit = check_quota(Tier.PRO, "configs", 15)
        assert is_within is False
        assert limit == 10

    def test_unlimited_quota(self):
        """Test unlimited quota (enterprise)."""
        is_within, limit = check_quota(Tier.ENTERPRISE, "configs", 1000)
        assert is_within is True
        assert limit is None

    def test_unknown_quota_type(self):
        """Test unknown quota type."""
        with pytest.raises(ValueError, match="Unknown quota type"):
            check_quota(Tier.PRO, "unknown", 5)


class TestEnforceQuota:
    """Tests for enforce_quota function."""

    def test_enforce_quota_within_limit(self):
        """Test enforce_quota when within limit."""
        # Should not raise
        enforce_quota(Tier.PRO, "configs", 5)

    def test_enforce_quota_exceeded(self):
        """Test enforce_quota when limit exceeded."""
        with pytest.raises(TierError) as exc_info:
            enforce_quota(Tier.PRO, "configs", 10)

        error = exc_info.value
        assert "Quota exceeded" in error.message
        assert error.quota_type == "configs"
        assert error.quota_limit == 10


class TestRequireTierDecorator:
    """Tests for require_tier decorator."""

    def test_require_tier_with_callback(self):
        """Test require_tier decorator with callback."""
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        # Clear any cached tier from parallel test execution
        get_tier_cache().invalidate(1)

        # Set up callback to return PRO tier
        set_tier_callback(lambda org_id: Tier.PRO)

        @require_tier("scheduler")
        def pro_feature(data: str, org_id: int) -> str:
            return f"executed for org {org_id}"

        result = pro_feature("test", org_id=1)
        assert result == "executed for org 1"

    def test_require_tier_insufficient_tier(self):
        """Test require_tier decorator with insufficient tier."""
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        # Clear any cached tier from parallel test execution
        get_tier_cache().invalidate(1)

        # Set up callback to return FREE tier
        set_tier_callback(lambda org_id: Tier.FREE)

        @require_tier("scheduler")
        def pro_feature(data: str, org_id: int) -> str:
            return "should not execute"

        with pytest.raises(TierError) as exc_info:
            pro_feature("test", org_id=1)

        error = exc_info.value
        assert "requires pro tier" in error.message.lower()

    def test_require_tier_no_org_id(self):
        """Test require_tier decorator without org_id."""
        set_tier_callback(lambda org_id: Tier.PRO)

        @require_tier("scheduler")
        def pro_feature(data: str) -> str:
            return "should not execute"

        with pytest.raises(TierError) as exc_info:
            pro_feature("test")

        assert "Organization ID required" in exc_info.value.message


class TestGetTierDisplayInfo:
    """Tests for get_tier_display_info function."""

    def test_display_info_structure(self):
        """Test display info has correct structure."""
        info = get_tier_display_info(Tier.PRO)

        assert "name" in info
        assert "tier" in info
        assert "limits" in info
        assert "features" in info

    def test_display_info_name(self):
        """Test display info name is formatted."""
        info = get_tier_display_info(Tier.PRO)
        assert info["name"] == "Pro"

    def test_display_info_includes_features(self):
        """Test display info includes available features."""
        info = get_tier_display_info(Tier.PRO)
        assert "sync" in info["features"]  # Free tier feature
        assert "scheduler" in info["features"]  # Pro tier feature


class TestGetUpgradeSuggestions:
    """Tests for get_upgrade_suggestions function."""

    def test_upgrade_suggestions_structure(self):
        """Test upgrade suggestions has correct structure."""
        suggestions = get_upgrade_suggestions(Tier.FREE, "scheduler")

        assert suggestions["current_tier"] == "free"
        assert suggestions["required_tier"] == "pro"
        assert suggestions["denied_feature"] == "scheduler"
        assert "additional_features" in suggestions

    def test_upgrade_suggestions_additional_features(self):
        """Test upgrade suggestions includes additional features."""
        suggestions = get_upgrade_suggestions(Tier.FREE, "scheduler")

        # Should include other pro features that free doesn't have
        assert len(suggestions["additional_features"]) > 0


class TestTierErrorException:
    """Tests for TierError exception class."""

    def test_tier_error_creation(self):
        """Test creating TierError."""
        error = TierError(
            message="Feature requires higher tier",
            required_tier="pro",
            current_tier="free",
            feature="scheduler",
        )

        assert "Feature requires higher tier" in error.message
        assert error.required_tier == "pro"
        assert error.current_tier == "free"
        assert error.feature == "scheduler"

    def test_tier_error_to_dict(self):
        """Test TierError to_dict method."""
        error = TierError(
            message="Quota exceeded",
            quota_type="configs",
            quota_limit=10,
            quota_used=10,
        )

        d = error.to_dict()
        assert d["error"] == "TierError"
        assert "Quota exceeded" in d["message"]
        assert d["details"]["quota_type"] == "configs"
        assert d["details"]["quota_limit"] == 10
