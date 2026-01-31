"""Tests for CLI tier enforcement module."""

import argparse
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from mysql_to_sheets.cli.tier_check import (
    check_cli_tier,
    get_tier_status_for_cli,
    require_cli_tier,
)
from mysql_to_sheets.core.license import LicenseInfo, LicenseStatus
from mysql_to_sheets.core.tier import Tier


class TestCheckCliTier:
    """Tests for check_cli_tier function."""

    def test_check_allowed_feature_free_tier(self):
        """Test that FREE tier features are allowed without license."""
        with patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                license_key="",
                license_public_key=None,
                license_offline_grace_days=3,
            )

            # 'sync' is a FREE tier feature
            allowed, error = check_cli_tier("sync")

            assert allowed is True
            assert error is None

    def test_check_premium_feature_without_license(self):
        """Test that premium features are denied without license."""
        with patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config:
            mock_config.return_value = MagicMock(
                license_key="",
                license_public_key=None,
                license_offline_grace_days=3,
            )

            # 'scheduler' requires PRO tier
            allowed, error = check_cli_tier("scheduler")

            assert allowed is False
            assert error is not None
            assert error["code"] == "LICENSE_001"
            assert "PRO" in error["message"]
            assert error["feature"] == "scheduler"
            assert error["required_tier"] == "pro"
            assert error["current_tier"] == "free"

    def test_check_premium_feature_with_valid_license(self):
        """Test that premium features are allowed with valid license."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            mock_config.return_value = MagicMock(
                license_key="valid-license-key",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.PRO,
            )

            allowed, error = check_cli_tier("scheduler")

            assert allowed is True
            assert error is None

    def test_check_business_feature_with_pro_license(self):
        """Test that BUSINESS features are denied with PRO license."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            mock_config.return_value = MagicMock(
                license_key="pro-license-key",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.PRO,
            )

            # 'webhooks' requires BUSINESS tier
            allowed, error = check_cli_tier("webhooks")

            assert allowed is False
            assert error is not None
            assert error["code"] == "LICENSE_004"
            assert "BUSINESS" in error["message"]
            assert error["required_tier"] == "business"
            assert error["current_tier"] == "pro"

    def test_check_expired_license(self):
        """Test that expired license returns appropriate error."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            mock_config.return_value = MagicMock(
                license_key="expired-license",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.EXPIRED,
                tier=Tier.PRO,
                expires_at=datetime.now(timezone.utc) - timedelta(days=30),
            )

            allowed, error = check_cli_tier("scheduler")

            assert allowed is False
            assert error is not None
            assert error["code"] == "LICENSE_003"
            assert "expired" in error["message"].lower()

    def test_check_invalid_license(self):
        """Test that invalid license returns appropriate error."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            mock_config.return_value = MagicMock(
                license_key="invalid-license",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.INVALID,
                tier=Tier.FREE,
                error="Invalid signature",
            )

            allowed, error = check_cli_tier("scheduler")

            assert allowed is False
            assert error is not None
            assert error["code"] == "LICENSE_002"
            assert "invalid" in error["message"].lower()

    def test_check_unknown_feature_allowed(self):
        """Test that unknown features are allowed (fail-open)."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.MISSING,
            )

            # Unknown feature should be allowed
            allowed, error = check_cli_tier("unknown_feature_xyz")

            assert allowed is True
            assert error is None


class TestRequireCliTierDecorator:
    """Tests for require_cli_tier decorator."""

    def test_decorator_blocks_premium_feature(self):
        """Test that decorator blocks premium feature without license."""
        with patch("mysql_to_sheets.cli.tier_check.check_cli_tier") as mock_check:
            mock_check.return_value = (
                False,
                {
                    "success": False,
                    "message": "Requires PRO tier",
                    "code": "LICENSE_001",
                    "feature": "scheduler",
                    "required_tier": "pro",
                    "current_tier": "free",
                    "license_status": "missing",
                },
            )

            @require_cli_tier("scheduler")
            def cmd_schedule(args):
                return 0

            args = argparse.Namespace(output="text")
            result = cmd_schedule(args)

            assert result == 1  # Exit code 1 for blocked

    def test_decorator_allows_permitted_feature(self):
        """Test that decorator allows feature with sufficient tier."""
        with patch("mysql_to_sheets.cli.tier_check.check_cli_tier") as mock_check:
            mock_check.return_value = (True, None)

            @require_cli_tier("scheduler")
            def cmd_schedule(args):
                return 0

            args = argparse.Namespace(output="text")
            result = cmd_schedule(args)

            assert result == 0  # Success

    def test_decorator_with_json_output(self, capsys):
        """Test that decorator outputs JSON when requested."""
        with patch("mysql_to_sheets.cli.tier_check.check_cli_tier") as mock_check:
            mock_check.return_value = (
                False,
                {
                    "success": False,
                    "message": "Requires PRO tier",
                    "code": "LICENSE_001",
                    "feature": "scheduler",
                    "required_tier": "pro",
                    "current_tier": "free",
                    "license_status": "missing",
                },
            )

            @require_cli_tier("scheduler")
            def cmd_schedule(args):
                return 0

            args = argparse.Namespace(output="json")
            result = cmd_schedule(args)

            captured = capsys.readouterr()
            assert result == 1
            assert '"code": "LICENSE_001"' in captured.out


class TestGetTierStatusForCli:
    """Tests for get_tier_status_for_cli function."""

    def test_status_without_license(self):
        """Test tier status without license."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            mock_config.return_value = MagicMock(
                license_key="",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.MISSING,
                tier=Tier.FREE,
            )

            status = get_tier_status_for_cli()

            assert status["tier"] == "free"
            assert status["license_status"] == "missing"
            assert status["is_licensed"] is False

    def test_status_with_valid_license(self):
        """Test tier status with valid license."""
        with (
            patch("mysql_to_sheets.cli.tier_check.get_config") as mock_config,
            patch("mysql_to_sheets.cli.tier_check.validate_license") as mock_validate,
        ):
            expires = datetime.now(timezone.utc) + timedelta(days=30)
            mock_config.return_value = MagicMock(
                license_key="valid-key",
                license_public_key=None,
                license_offline_grace_days=3,
            )
            mock_validate.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.PRO,
                customer_id="cust_123",
                email="test@example.com",
                expires_at=expires,
                days_until_expiry=30,
            )

            status = get_tier_status_for_cli()

            assert status["tier"] == "pro"
            assert status["license_status"] == "valid"
            assert status["customer_id"] == "cust_123"
            assert status["email"] == "test@example.com"
            assert status["is_licensed"] is True
            assert status["days_until_expiry"] == 30
