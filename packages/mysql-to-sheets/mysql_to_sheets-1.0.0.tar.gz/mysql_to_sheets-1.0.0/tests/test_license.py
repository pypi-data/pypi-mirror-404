"""Tests for the license validation module.

License validation uses RS256 (asymmetric) algorithm. Only the public key
is embedded in the codebase - the private key is kept secure on the license server.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from mysql_to_sheets.core.exceptions import LicenseError
from mysql_to_sheets.core.license import (
    DEFAULT_LICENSE_PUBLIC_KEY,
    LICENSE_JWT_ALGORITHM,
    LicenseInfo,
    LicenseStatus,
    get_effective_tier,
    is_license_valid,
    require_tier,
    require_valid_license,
    validate_license,
)
from mysql_to_sheets.core.tier import Tier

# Test RSA key pair for testing purposes only
# These are NOT production keys - they are used only for unit tests
TEST_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAl0Mj4jNYrGOD1vyB79gz9CFdrcpuRAtmy2gR/pf05ch+qy3F
c74ApgDItPScZCwIG3Zp+yVk7WqAictGHDtdmDjHHbri4Qc98Xs+VuhZs5yMrUpC
qN3lAY5RRIb3hzHTxDyRZ3ZR1ri0AtvuskKO2idLzHSQRO/7CQSfMxIhlvQZdRPx
FLYDnPO0FZc96jVjbjQW0AiAftUmRIp3+rY1zv63p4o35hF4sflUADjrquw6ExOl
MRYvkU3mXbHKIE2hE+sBdP+oT/0W/p/BKi/pr/EEFxZH5nztVVBlDRW05f9UTvX+
uXniFfiBg0VFOZVzxfPwIPvsubOlraoR+TDPPwIDAQABAoIBAAzbrTo2SSxmTTfC
QT1lMI1pJLB4S8VG/tb9osH0ouHBmFruyiEbnqx91pHjVUQCpjHHcBzkQd8YtZKB
EBWoSj19Xhe94jlkxzQ22MbEe5OUFDVK4b2/Fw95zJi5rGL2rly5FVcpLK3HB65S
icjndYM/4eagZf8mMz3CAdJykR5mwg5XVIqq2XMGVywyRDfkOoNKWVTZ11GhhcyW
8IjKGF3+2VqB6s9lbLBrNEWkQhS8IW9cs4Y0V8KwdxJlC10X8+Lr5GvDgRjZYyWP
/4dKcZgEM5imhjeKMGpZL2fnBSctMJPrz1cHmqhvmAIrpQ6Q83JqdVQqskAc6uoZ
qt2IzwECgYEA1W7QplXpZ3e/XcB6Y1rPggdLIA6HHrAuAgUkLwEWH4SE6fghOy/z
cUtWNa/RZgvngdkRNwQ8FLKX/e5mOqNQVjDVvPFRWWZ0hGo7VqnfD7mTyHQs/d4J
SBHPFzHbjnMHseA9H01witMGawDAAhNZMgqUhr6IIUJZ/5+LPhcXPL8CgYEAtW4Y
4ih4sh3FE+gjxgMhk6xCIO5NCN4xKZKtUlDcF/DnqMTnP9VO30qz/0Hnsg6sNTGv
lWw56sGoi/w5sjjIIG7VhCDLik/wVTxXUMEzoY7MFmv+KFjZelHQiX+UKwkIGMEk
huEgGgFcN5s2fVx1a7cmQkAf9W3sGOOWfSl6jYECgYEAvcUVEgBrUksfxN0iNPsG
bCfN/UfNjlS546PsozqFECsE/v9XlMey3fZNRdj5B5HoGwUFEHTccs7E48w360VQ
ZgJv2Np8KVA2o5HNBuZtZg7sPpxFcMgeWo0zI/15qTPQELE/x3hUa6rsFvIIxw+r
DBpqK1B3u5LCcM3Lwb5INAMCgYAnoQvIYoSyizQf/AXMW6S659Zt8P9cn4Pni8VW
BJl+lT1UrOXCGKqotV2JtPCSAQh2egrbPY+NCo3xPb+wgRydkPgMa0lqRbm+NHby
CbFoaZOElkQmtfmS8Un2rqpDmC5vkciTuZrUc1WcQ8fsLATt6UxvDiis6Dy41wVp
A2VkgQKBgEv2GZizzCaWHri5UO1bx3CmuxSED/lJwUEMy2W5JvvO4STLJYmjwhrE
9rPFBP8WBZrUcMkONeagYO9Y5L/1iAvHXryprKZ2nIjtL9aJJCMT5hwAVmpnDRNH
uqzbQY6Vra7QudfLZCZ3kHuDTq0g5EVUaHfUYNbA79JUVoa7LoOK
-----END RSA PRIVATE KEY-----"""

# The matching public key for testing
TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAl0Mj4jNYrGOD1vyB79gz
9CFdrcpuRAtmy2gR/pf05ch+qy3Fc74ApgDItPScZCwIG3Zp+yVk7WqAictGHDtd
mDjHHbri4Qc98Xs+VuhZs5yMrUpCqN3lAY5RRIb3hzHTxDyRZ3ZR1ri0AtvuskKO
2idLzHSQRO/7CQSfMxIhlvQZdRPxFLYDnPO0FZc96jVjbjQW0AiAftUmRIp3+rY1
zv63p4o35hF4sflUADjrquw6ExOlMRYvkU3mXbHKIE2hE+sBdP+oT/0W/p/BKi/p
r/EEFxZH5nztVVBlDRW05f9UTvX+uXniFfiBg0VFOZVzxfPwIPvsubOlraoR+TDP
PwIDAQAB
-----END PUBLIC KEY-----"""


def create_test_license(
    customer_id: str = "cust_123",
    email: str = "test@example.com",
    tier: str = "pro",
    expires_in_days: int = 30,
    features: list[str] | None = None,
    private_key: str = TEST_PRIVATE_KEY,
) -> str:
    """Create a test license key signed with the test private key.

    This simulates what the license generation service would do.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=expires_in_days)

    payload = {
        "sub": customer_id,
        "email": email,
        "tier": tier,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "iss": "mysql-to-sheets",
    }

    if features:
        payload["features"] = features

    return jwt.encode(payload, private_key, algorithm="RS256")


def validate_test_license(token: str, grace_days: int = 3) -> "LicenseInfo":
    """Validate a license with our test public key."""
    return validate_license(token, public_key=TEST_PUBLIC_KEY, grace_days=grace_days)


class TestLicenseStatus:
    """Tests for LicenseStatus enum."""

    def test_status_values(self):
        """Test that all status values are defined."""
        assert LicenseStatus.VALID.value == "valid"
        assert LicenseStatus.EXPIRED.value == "expired"
        assert LicenseStatus.INVALID.value == "invalid"
        assert LicenseStatus.MISSING.value == "missing"
        assert LicenseStatus.GRACE_PERIOD.value == "grace_period"


class TestLicenseInfo:
    """Tests for LicenseInfo dataclass."""

    def test_default_values(self):
        """Test default values for LicenseInfo."""
        info = LicenseInfo(status=LicenseStatus.MISSING)
        assert info.status == LicenseStatus.MISSING
        assert info.customer_id is None
        assert info.email is None
        assert info.tier == Tier.FREE
        assert info.issued_at is None
        assert info.expires_at is None
        assert info.features == []
        assert info.error is None
        assert info.days_until_expiry is None

    def test_to_dict(self):
        """Test to_dict method."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)
        info = LicenseInfo(
            status=LicenseStatus.VALID,
            customer_id="cust_123",
            email="test@example.com",
            tier=Tier.PRO,
            issued_at=now,
            expires_at=expires,
            features=["scheduler", "webhooks"],
            days_until_expiry=30,
        )

        data = info.to_dict()

        assert data["status"] == "valid"
        assert data["customer_id"] == "cust_123"
        assert data["email"] == "test@example.com"
        assert data["tier"] == "pro"
        assert data["features"] == ["scheduler", "webhooks"]
        assert data["days_until_expiry"] == 30


class TestValidateLicense:
    """Tests for validate_license function."""

    def test_missing_license(self):
        """Test validation with missing license."""
        result = validate_license("")
        assert result.status == LicenseStatus.MISSING
        assert result.error == "No license key provided"

        result = validate_license(None)
        assert result.status == LicenseStatus.MISSING

        result = validate_license("   ")
        assert result.status == LicenseStatus.MISSING

    def test_invalid_license_format(self):
        """Test validation with invalid license format."""
        result = validate_license("not-a-valid-jwt")
        assert result.status == LicenseStatus.INVALID
        assert "Invalid license" in result.error

    def test_invalid_signature_hs256(self):
        """Test that HS256 tokens are rejected (wrong algorithm)."""
        # Create a token with HS256 (should be rejected)
        payload = {
            "sub": "cust_123",
            "email": "test@example.com",
            "tier": "pro",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        }
        token = jwt.encode(payload, "any-secret", algorithm="HS256")

        result = validate_license(token)
        assert result.status == LicenseStatus.INVALID
        # HS256 tokens will fail because RS256 public key can't verify HS256 signature

    def test_invalid_signature_wrong_key(self):
        """Test validation with wrong RSA private key."""
        # Generate a different RSA key pair (this simulates someone trying to forge)
        # We'll create a token with a different key that won't validate
        payload = {
            "sub": "forged_customer",
            "email": "forged@example.com",
            "tier": "enterprise",  # Trying to forge enterprise!
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(days=9999)).timestamp()),
        }

        # Create a different RSA key for the "attacker"
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        attacker_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        attacker_private_pem = attacker_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        # Sign with attacker's key
        forged_token = jwt.encode(payload, attacker_private_pem, algorithm="RS256")

        # Should fail validation with the real public key
        result = validate_license(forged_token)
        assert result.status == LicenseStatus.INVALID
        assert "signature" in result.error.lower() or "invalid" in result.error.lower()

    def test_valid_license(self):
        """Test validation with valid license."""
        token = create_test_license(
            customer_id="cust_123",
            email="test@example.com",
            tier="pro",
            expires_in_days=30,
            features=["scheduler", "notifications"],
        )

        # Use validate_test_license to verify with matching key pair
        result = validate_test_license(token)

        assert result.status == LicenseStatus.VALID
        assert result.customer_id == "cust_123"
        assert result.email == "test@example.com"
        assert result.tier == Tier.PRO
        assert result.features == ["scheduler", "notifications"]
        assert result.days_until_expiry == 29 or result.days_until_expiry == 30
        assert result.error is None

    def test_expired_license(self):
        """Test validation with expired license."""
        token = create_test_license(
            tier="pro",
            expires_in_days=-10,  # Expired 10 days ago
        )

        # With default 3-day grace period, should be expired
        result = validate_test_license(token, grace_days=3)
        assert result.status == LicenseStatus.EXPIRED

    def test_grace_period(self):
        """Test validation with license in grace period."""
        token = create_test_license(
            tier="pro",
            expires_in_days=-2,  # Expired 2 days ago
        )

        # With 3-day grace period, should be in grace
        result = validate_test_license(token, grace_days=3)
        assert result.status == LicenseStatus.GRACE_PERIOD
        assert result.tier == Tier.PRO  # Still has tier during grace

    def test_unknown_tier_defaults_to_free(self):
        """Test that unknown tier defaults to FREE."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "cust_123",
            "tier": "unknown_tier",
            "exp": int((now + timedelta(days=30)).timestamp()),
            "iat": int(now.timestamp()),
        }
        token = jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256")

        # Use validate_test_license to verify with matching key pair
        result = validate_test_license(token)
        assert result.status == LicenseStatus.VALID
        assert result.tier == Tier.FREE

    def test_all_tier_levels(self):
        """Test validation with all tier levels."""
        for tier in ["free", "pro", "business", "enterprise"]:
            token = create_test_license(tier=tier)

            # Use validate_test_license to verify with matching key pair
            result = validate_test_license(token)
            assert result.status == LicenseStatus.VALID
            assert result.tier == Tier(tier)


class TestRS256Security:
    """Tests specifically for RS256 security properties."""

    def test_algorithm_is_rs256(self):
        """Test that the algorithm constant is RS256."""
        assert LICENSE_JWT_ALGORITHM == "RS256"

    def test_public_key_is_embedded(self):
        """Test that a public key is embedded in the module."""
        assert DEFAULT_LICENSE_PUBLIC_KEY is not None
        assert "BEGIN PUBLIC KEY" in DEFAULT_LICENSE_PUBLIC_KEY
        assert "END PUBLIC KEY" in DEFAULT_LICENSE_PUBLIC_KEY

    def test_cannot_create_valid_token_without_private_key(self):
        """Test that tokens cannot be created with just the public key."""
        # Attempting to sign with a public key should fail or produce invalid token
        payload = {
            "sub": "forged_customer",
            "tier": "enterprise",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=9999)).timestamp()),
        }

        # PyJWT should raise an error when trying to sign with a public key
        with pytest.raises(Exception):
            jwt.encode(payload, DEFAULT_LICENSE_PUBLIC_KEY, algorithm="RS256")


class TestGetEffectiveTier:
    """Tests for get_effective_tier function."""

    def test_valid_license_returns_tier(self):
        """Test that valid license returns its tier."""
        info = LicenseInfo(status=LicenseStatus.VALID, tier=Tier.PRO)
        assert get_effective_tier(info) == Tier.PRO

    def test_grace_period_returns_tier(self):
        """Test that grace period returns its tier."""
        info = LicenseInfo(status=LicenseStatus.GRACE_PERIOD, tier=Tier.BUSINESS)
        assert get_effective_tier(info) == Tier.BUSINESS

    def test_expired_returns_free(self):
        """Test that expired license returns FREE."""
        info = LicenseInfo(status=LicenseStatus.EXPIRED, tier=Tier.PRO)
        assert get_effective_tier(info) == Tier.FREE

    def test_invalid_returns_free(self):
        """Test that invalid license returns FREE."""
        info = LicenseInfo(status=LicenseStatus.INVALID, tier=Tier.ENTERPRISE)
        assert get_effective_tier(info) == Tier.FREE

    def test_missing_returns_free(self):
        """Test that missing license returns FREE."""
        info = LicenseInfo(status=LicenseStatus.MISSING)
        assert get_effective_tier(info) == Tier.FREE


class TestIsLicenseValid:
    """Tests for is_license_valid function."""

    def test_valid_is_valid(self):
        """Test VALID status is considered valid."""
        info = LicenseInfo(status=LicenseStatus.VALID)
        assert is_license_valid(info) is True

    def test_grace_period_is_valid(self):
        """Test GRACE_PERIOD status is considered valid."""
        info = LicenseInfo(status=LicenseStatus.GRACE_PERIOD)
        assert is_license_valid(info) is True

    def test_expired_is_not_valid(self):
        """Test EXPIRED status is not considered valid."""
        info = LicenseInfo(status=LicenseStatus.EXPIRED)
        assert is_license_valid(info) is False

    def test_invalid_is_not_valid(self):
        """Test INVALID status is not considered valid."""
        info = LicenseInfo(status=LicenseStatus.INVALID)
        assert is_license_valid(info) is False

    def test_missing_is_not_valid(self):
        """Test MISSING status is not considered valid."""
        info = LicenseInfo(status=LicenseStatus.MISSING)
        assert is_license_valid(info) is False


class TestRequireValidLicenseDecorator:
    """Tests for require_valid_license decorator."""

    def test_missing_license_raises(self):
        """Test that missing license raises LicenseError."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(status=LicenseStatus.MISSING)

            @require_valid_license
            def protected_function():
                return "success"

            with pytest.raises(LicenseError) as exc_info:
                protected_function()

            assert "LICENSE_KEY" in str(exc_info.value)

    def test_invalid_license_raises(self):
        """Test that invalid license raises LicenseError."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.INVALID,
                error="Test error",
            )

            @require_valid_license
            def protected_function():
                return "success"

            with pytest.raises(LicenseError) as exc_info:
                protected_function()

            assert "Invalid license" in str(exc_info.value)

    def test_expired_license_raises(self):
        """Test that expired license raises LicenseError."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.EXPIRED,
                expires_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )

            @require_valid_license
            def protected_function():
                return "success"

            with pytest.raises(LicenseError) as exc_info:
                protected_function()

            assert "expired" in str(exc_info.value).lower()

    def test_valid_license_allows(self):
        """Test that valid license allows execution."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.PRO,
            )

            @require_valid_license
            def protected_function():
                return "success"

            result = protected_function()
            assert result == "success"

    def test_grace_period_allows(self):
        """Test that grace period allows execution."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.GRACE_PERIOD,
                tier=Tier.PRO,
            )

            @require_valid_license
            def protected_function():
                return "success"

            result = protected_function()
            assert result == "success"


class TestRequireTierDecorator:
    """Tests for require_tier decorator."""

    def test_insufficient_tier_raises(self):
        """Test that insufficient tier raises LicenseError."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.FREE,
            )

            @require_tier(Tier.PRO)
            def pro_feature():
                return "success"

            with pytest.raises(LicenseError) as exc_info:
                pro_feature()

            assert "PRO" in str(exc_info.value)
            assert "requires" in str(exc_info.value).lower()

    def test_matching_tier_allows(self):
        """Test that matching tier allows execution."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.PRO,
            )

            @require_tier(Tier.PRO)
            def pro_feature():
                return "success"

            result = pro_feature()
            assert result == "success"

    def test_higher_tier_allows(self):
        """Test that higher tier allows execution."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.ENTERPRISE,
            )

            @require_tier(Tier.PRO)
            def pro_feature():
                return "success"

            result = pro_feature()
            assert result == "success"

    def test_string_tier_works(self):
        """Test that string tier specification works."""
        with patch("mysql_to_sheets.core.billing.license.get_license_info_from_config") as mock:
            mock.return_value = LicenseInfo(
                status=LicenseStatus.VALID,
                tier=Tier.BUSINESS,
            )

            @require_tier("pro")
            def pro_feature():
                return "success"

            result = pro_feature()
            assert result == "success"
