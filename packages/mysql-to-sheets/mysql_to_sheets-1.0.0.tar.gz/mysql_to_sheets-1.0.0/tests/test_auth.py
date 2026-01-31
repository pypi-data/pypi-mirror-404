"""Tests for the authentication module."""

import os
import unittest.mock
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.auth import (
    AuthConfig,
    TokenPayload,
    authenticate_user,
    blacklist_token,
    clear_token_blacklist,
    create_access_token,
    create_refresh_token,
    generate_password_reset_token,
    get_auth_config,
    hash_password,
    is_token_blacklisted,
    reset_auth_config,
    validate_password_strength,
    verify_password,
    verify_password_reset_token,
    verify_token,
)
from mysql_to_sheets.models.users import User


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test that hash_password returns a bcrypt hash."""
        password = "MySecretPassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "SamePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salt each time

    def test_verify_password_correct(self):
        """Test that correct password verifies."""
        password = "CorrectPassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that incorrect password does not verify."""
        password = "CorrectPassword123"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test that invalid hash returns False."""
        assert verify_password("password", "invalid_hash") is False
        assert verify_password("password", "") is False


class TestPasswordStrengthValidation:
    """Tests for password strength validation."""

    def test_valid_password(self):
        """Test that strong password passes validation."""
        is_valid, errors = validate_password_strength("StrongPass123")

        assert is_valid is True
        assert len(errors) == 0

    def test_too_short(self):
        """Test that short password fails."""
        is_valid, errors = validate_password_strength("Ab1")

        assert is_valid is False
        assert any("at least" in e for e in errors)

    def test_no_uppercase(self):
        """Test that password without uppercase fails."""
        is_valid, errors = validate_password_strength("lowercase123")

        assert is_valid is False
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase(self):
        """Test that password without lowercase fails."""
        is_valid, errors = validate_password_strength("UPPERCASE123")

        assert is_valid is False
        assert any("lowercase" in e for e in errors)

    def test_no_number(self):
        """Test that password without number fails."""
        is_valid, errors = validate_password_strength("NoNumberHere")

        assert is_valid is False
        assert any("number" in e for e in errors)

    def test_multiple_failures(self):
        """Test that multiple failures are reported."""
        is_valid, errors = validate_password_strength("abc")

        assert is_valid is False
        assert len(errors) >= 2  # At least short + missing uppercase


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_auth_config()

    def teardown_method(self):
        """Cleanup after test."""
        reset_auth_config()

    def test_create_auth_config(self):
        """Test creating AuthConfig directly."""
        config = AuthConfig(
            jwt_secret_key="test-secret",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14,
        )

        assert config.jwt_secret_key == "test-secret"
        assert config.access_token_expire_minutes == 60
        assert config.refresh_token_expire_days == 14
        assert config.jwt_algorithm == "HS256"

    def test_from_env(self):
        """Test loading AuthConfig from environment."""
        env_vars = {
            "JWT_SECRET_KEY": "env-secret",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "45",
            "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "10",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = AuthConfig.from_env()

            assert config.jwt_secret_key == "env-secret"
            assert config.access_token_expire_minutes == 45
            assert config.refresh_token_expire_days == 10

    def test_from_env_missing_secret_raises(self):
        """Test that missing JWT_SECRET_KEY raises ValueError."""
        env_vars = {"JWT_SECRET_KEY": ""}

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError) as exc_info:
                AuthConfig.from_env()

            assert "JWT_SECRET_KEY" in str(exc_info.value)


class TestTokenPayload:
    """Tests for TokenPayload dataclass."""

    def test_is_expired_true(self):
        """Test that expired token returns True."""
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        payload = TokenPayload(
            user_id=1,
            email="test@example.com",
            role="viewer",
            organization_id=1,
            token_type="access",
            exp=expired,
            iat=datetime.now(timezone.utc),
            jti="test-jti",
        )

        assert payload.is_expired() is True

    def test_is_expired_false(self):
        """Test that valid token returns False."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = TokenPayload(
            user_id=1,
            email="test@example.com",
            role="viewer",
            organization_id=1,
            token_type="access",
            exp=future,
            iat=datetime.now(timezone.utc),
            jti="test-jti",
        )

        assert payload.is_expired() is False


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token(self):
        """Test creating an access token."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role="admin",
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")

        token = create_access_token(user, config)

        assert token is not None
        assert len(token) > 0
        assert "." in token  # JWT has 3 parts separated by dots

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role="viewer",
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")

        token = create_refresh_token(user, config)

        assert token is not None
        assert "." in token

    def test_verify_access_token(self):
        """Test verifying a valid access token."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role="operator",
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")
        token = create_access_token(user, config)

        payload = verify_token(token, config)

        assert payload is not None
        assert payload.user_id == 1
        assert payload.email == "test@example.com"
        assert payload.role == "operator"
        assert payload.organization_id == 1
        assert payload.token_type == "access"

    def test_verify_refresh_token(self):
        """Test verifying a valid refresh token."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role="viewer",
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")
        token = create_refresh_token(user, config)

        payload = verify_token(token, config, expected_type="refresh")

        assert payload is not None
        assert payload.token_type == "refresh"

    def test_verify_token_wrong_type(self):
        """Test that wrong token type returns None."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role="viewer",
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")
        access_token = create_access_token(user, config)

        # Try to verify access token as refresh token
        payload = verify_token(access_token, config, expected_type="refresh")

        assert payload is None

    def test_verify_token_invalid(self):
        """Test that invalid token returns None."""
        config = AuthConfig(jwt_secret_key="test-secret")
        payload = verify_token("invalid.token.here", config)

        assert payload is None

    def test_verify_token_wrong_secret(self):
        """Test that token with wrong secret returns None."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role="viewer",
            password_hash="hash",
        )
        config1 = AuthConfig(jwt_secret_key="secret-1")
        config2 = AuthConfig(jwt_secret_key="secret-2")

        token = create_access_token(user, config1)
        payload = verify_token(token, config2)

        assert payload is None


class TestPasswordResetTokens:
    """Tests for password reset token functionality."""

    def test_generate_password_reset_token(self):
        """Test generating a password reset token."""
        user = User(
            id=1,
            email="reset@example.com",
            display_name="Reset User",
            organization_id=1,
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")

        token = generate_password_reset_token(user, config)

        assert token is not None
        assert "." in token

    def test_verify_password_reset_token(self):
        """Test verifying a password reset token."""
        user = User(
            id=1,
            email="reset@example.com",
            display_name="Reset User",
            organization_id=1,
            password_hash="hash",
        )
        config = AuthConfig(jwt_secret_key="test-secret")
        token = generate_password_reset_token(user, config)

        result = verify_password_reset_token(token, config)

        assert result is not None
        assert result["user_id"] == 1
        assert result["email"] == "reset@example.com"
        assert result["organization_id"] == 1

    def test_verify_password_reset_token_invalid(self):
        """Test that invalid reset token returns None."""
        config = AuthConfig(jwt_secret_key="test-secret")
        result = verify_password_reset_token("invalid.token", config)

        assert result is None


class TestTokenBlacklist:
    """Tests for token blacklist functionality."""

    def setup_method(self):
        """Clear blacklist before each test."""
        clear_token_blacklist()

    def teardown_method(self):
        """Clear blacklist after each test."""
        clear_token_blacklist()

    def test_blacklist_token(self):
        """Test adding token to blacklist."""
        jti = "test-token-id"

        assert is_token_blacklisted(jti) is False

        blacklist_token(jti)

        assert is_token_blacklisted(jti) is True

    def test_multiple_blacklisted_tokens(self):
        """Test multiple tokens in blacklist."""
        blacklist_token("token-1")
        blacklist_token("token-2")

        assert is_token_blacklisted("token-1") is True
        assert is_token_blacklisted("token-2") is True
        assert is_token_blacklisted("token-3") is False

    def test_clear_token_blacklist(self):
        """Test clearing the blacklist."""
        blacklist_token("token-1")
        assert is_token_blacklisted("token-1") is True

        clear_token_blacklist()

        assert is_token_blacklisted("token-1") is False


class TestAuthenticateUser:
    """Tests for authenticate_user function."""

    def setup_method(self):
        """Patch account lockout check so tests don't depend on SQLite lockout state."""
        # Patch at the actual location where the function is defined
        self._patcher = unittest.mock.patch(
            "mysql_to_sheets.core.security.auth.check_account_locked",
            return_value=(False, None),
        )
        self._patcher.start()

    def teardown_method(self):
        """Stop the lockout patcher."""
        self._patcher.stop()

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        password = "TestPassword123"
        password_hash = hash_password(password)

        user = User(
            id=1,
            email="auth@example.com",
            display_name="Auth User",
            organization_id=1,
            password_hash=password_hash,
            is_active=True,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_email.return_value = user
        mock_repo.update_last_login.return_value = True

        result = authenticate_user(
            email="auth@example.com",
            password=password,
            user_repo=mock_repo,
            organization_id=1,
        )

        assert result is not None
        assert result.email == "auth@example.com"
        mock_repo.update_last_login.assert_called_once_with(1)

    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        mock_repo = MagicMock()
        mock_repo.get_by_email.return_value = None

        result = authenticate_user(
            email="notfound@example.com",
            password="password",
            user_repo=mock_repo,
            organization_id=1,
        )

        assert result is None

    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user."""
        user = User(
            id=1,
            email="inactive@example.com",
            display_name="Inactive User",
            organization_id=1,
            password_hash=hash_password("password"),
            is_active=False,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_email.return_value = user

        result = authenticate_user(
            email="inactive@example.com",
            password="password",
            user_repo=mock_repo,
            organization_id=1,
        )

        assert result is None

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        user = User(
            id=1,
            email="auth@example.com",
            display_name="Auth User",
            organization_id=1,
            password_hash=hash_password("CorrectPassword"),
            is_active=True,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_email.return_value = user

        result = authenticate_user(
            email="auth@example.com",
            password="WrongPassword",
            user_repo=mock_repo,
            organization_id=1,
        )

        assert result is None


class TestAuthConfigSingleton:
    """Tests for auth config singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_auth_config()

    def teardown_method(self):
        """Cleanup after test."""
        reset_auth_config()

    def test_get_auth_config_caches(self):
        """Test that get_auth_config returns cached instance."""
        env_vars = {"JWT_SECRET_KEY": "test-secret"}

        with patch.dict(os.environ, env_vars, clear=False):
            config1 = get_auth_config()
            config2 = get_auth_config()

            assert config1 is config2

    def test_reset_auth_config(self):
        """Test resetting the auth config singleton."""
        env_vars = {"JWT_SECRET_KEY": "test-secret"}

        with patch.dict(os.environ, env_vars, clear=False):
            config1 = get_auth_config()
            reset_auth_config()

            # After reset, it should create new instance
            config2 = get_auth_config()
            # Can't guarantee same object, but values should work
            assert config2.jwt_secret_key == "test-secret"
