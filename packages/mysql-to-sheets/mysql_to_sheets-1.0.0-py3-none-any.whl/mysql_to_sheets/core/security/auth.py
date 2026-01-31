"""Authentication module for JWT tokens and password handling.

Provides secure password hashing with bcrypt and JWT token
generation/verification with organization context.
"""

import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from mysql_to_sheets.models.users import User

# Default configuration values
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7
DEFAULT_PASSWORD_MIN_LENGTH = 8


@dataclass
class TokenPayload:
    """Decoded JWT token payload.

    Contains user identity and organization context
    extracted from a valid JWT token.
    """

    user_id: int
    email: str
    role: str
    organization_id: int
    token_type: str  # "access" or "refresh"
    exp: datetime
    iat: datetime
    jti: str  # Unique token ID

    def is_expired(self) -> bool:
        """Check if token is expired.

        Returns:
            True if token is expired, False otherwise.
        """
        return datetime.now(timezone.utc) > self.exp


@dataclass
class AuthConfig:
    """Authentication configuration.

    Loaded from environment variables with sensible defaults.
    """

    jwt_secret_key: str
    jwt_algorithm: str = DEFAULT_JWT_ALGORITHM
    access_token_expire_minutes: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
    refresh_token_expire_days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
    password_min_length: int = DEFAULT_PASSWORD_MIN_LENGTH

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Create config from environment variables.

        Returns:
            AuthConfig instance.

        Raises:
            ValueError: If JWT_SECRET_KEY is not set.
        """
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required for authentication")

        return cls(
            jwt_secret_key=secret_key,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM),
            access_token_expire_minutes=int(
                os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
            ),
            refresh_token_expire_days=int(
                os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS)
            ),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", DEFAULT_PASSWORD_MIN_LENGTH)),
        )


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        Bcrypt password hash.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        password: Plain text password to verify.
        password_hash: Bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, AttributeError):
        return False


def validate_password_strength(
    password: str,
    min_length: int = DEFAULT_PASSWORD_MIN_LENGTH,
) -> tuple[bool, list[str]]:
    """Validate password strength.

    Args:
        password: Password to validate.
        min_length: Minimum password length.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []

    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    return len(errors) == 0, errors


def create_access_token(
    user: User,
    config: AuthConfig,
    logger: logging.Logger | None = None,
) -> str:
    """Create a JWT access token for a user.

    The token includes user identity and organization context
    for multi-tenant isolation.

    Args:
        user: User to create token for.
        config: Authentication configuration.
        logger: Optional logger.

    Returns:
        JWT access token string.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=config.access_token_expire_minutes)

    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "token_type": "access",
        "exp": expires,
        "iat": now,
        "jti": secrets.token_hex(16),  # Unique token ID
    }

    token = jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)

    if logger:
        logger.debug(f"Created access token for user {user.id} (org {user.organization_id})")

    return token


def create_refresh_token(
    user: User,
    config: AuthConfig,
    logger: logging.Logger | None = None,
) -> str:
    """Create a JWT refresh token for a user.

    Refresh tokens have longer expiration and can be used
    to obtain new access tokens.

    Args:
        user: User to create token for.
        config: Authentication configuration.
        logger: Optional logger.

    Returns:
        JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=config.refresh_token_expire_days)

    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "token_type": "refresh",
        "exp": expires,
        "iat": now,
        "jti": secrets.token_hex(16),
    }

    token = jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)

    if logger:
        logger.debug(f"Created refresh token for user {user.id} (org {user.organization_id})")

    return token


def verify_token(
    token: str,
    config: AuthConfig,
    expected_type: str | None = None,
    logger: logging.Logger | None = None,
) -> TokenPayload | None:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string.
        config: Authentication configuration.
        expected_type: Expected token type ("access" or "refresh").
        logger: Optional logger.

    Returns:
        TokenPayload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret_key,
            algorithms=[config.jwt_algorithm],
        )

        # Verify token type if specified
        if expected_type and payload.get("token_type") != expected_type:
            if logger:
                logger.warning(
                    f"Token type mismatch: expected {expected_type}, got {payload.get('token_type')}"
                )
            return None

        # Convert timestamps to datetime
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        return TokenPayload(
            user_id=payload["user_id"],
            email=payload["email"],
            role=payload["role"],
            organization_id=payload["organization_id"],
            token_type=payload["token_type"],
            exp=exp,
            iat=iat,
            jti=payload["jti"],
        )

    except jwt.ExpiredSignatureError:
        if logger:
            logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        if logger:
            logger.warning(f"Invalid token: {e}")
        return None


def check_account_locked(
    email: str,
    db_path: str | None = None,
    logger: logging.Logger | None = None,
    fail_open: bool | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """Check if an account is locked due to too many failed attempts.

    SECURITY: This function is fail-closed by default. If the lockout database
    cannot be accessed, login is blocked to prevent brute-force attacks during
    database unavailability. Set fail_open=True or LOCKOUT_FAIL_OPEN=true to
    allow login when lockout state cannot be verified (not recommended for
    production).

    Args:
        email: User email to check.
        db_path: Path to database. Uses tenant DB if None.
        logger: Optional logger.
        fail_open: If True, allow login when lockout DB is unavailable.
            Defaults to LOCKOUT_FAIL_OPEN env var (default: False).

    Returns:
        Tuple of (is_locked, lockout_info_dict).
        lockout_info_dict contains lockout_until and remaining_attempts if locked.
    """
    try:
        from mysql_to_sheets.models.login_attempts import get_login_attempt_repository

        repo = get_login_attempt_repository(db_path)
        status = repo.check_lockout(email)

        if status.is_locked:
            if logger:
                logger.warning(f"Account locked: {email} until {status.lockout_until}")
            return True, status.to_dict()

        return False, None

    except (ImportError, OSError, RuntimeError) as e:
        # Determine fail-open behavior from config or parameter
        if fail_open is None:
            import os

            fail_open = os.getenv("LOCKOUT_FAIL_OPEN", "").lower() in ("true", "1", "yes", "on")

        if fail_open:
            # Fail-open: Allow login when lockout DB unavailable (not recommended)
            if logger:
                logger.warning(
                    f"Failed to check account lockout (fail-open mode, allowing login): {e}"
                )
            return False, None
        else:
            # SECURITY: Fail-closed - block login when lockout state cannot be verified.
            # This prevents brute-force attacks during database unavailability.
            if logger:
                logger.error(
                    f"Critical: Cannot verify lockout state for {email} (blocking login): {e}"
                )
            return True, {"reason": "lockout_db_unavailable", "error": str(e)}


def record_login_attempt(
    email: str,
    success: bool,
    ip_address: str | None = None,
    failure_reason: str | None = None,
    db_path: str | None = None,
    logger: logging.Logger | None = None,
) -> None:
    """Record a login attempt for security tracking.

    Args:
        email: User email attempted.
        success: Whether the login succeeded.
        ip_address: Client IP address.
        failure_reason: Reason for failure if unsuccessful.
        db_path: Path to database. Uses tenant DB if None.
        logger: Optional logger.
    """
    try:
        from mysql_to_sheets.models.login_attempts import get_login_attempt_repository

        repo = get_login_attempt_repository(db_path)
        repo.record_attempt(
            email=email,
            success=success,
            ip_address=ip_address,
            failure_reason=failure_reason,
        )

        if not success and logger:
            status = repo.check_lockout(email)
            if status.remaining_attempts > 0:
                logger.debug(
                    f"Failed login for {email}: {status.remaining_attempts} attempts remaining"
                )
            elif status.is_locked:
                logger.warning(f"Account {email} is now locked until {status.lockout_until}")

    except (ImportError, OSError, RuntimeError) as e:
        # Log but don't fail
        if logger:
            logger.warning(f"Failed to record login attempt: {e}")


def clear_account_lockout(
    email: str,
    db_path: str | None = None,
    logger: logging.Logger | None = None,
) -> bool:
    """Clear lockout for an account (admin override).

    Args:
        email: Email address to unlock.
        db_path: Path to database. Uses tenant DB if None.
        logger: Optional logger.

    Returns:
        True if a lockout was cleared, False if none existed.
    """
    try:
        from mysql_to_sheets.models.login_attempts import get_login_attempt_repository

        repo = get_login_attempt_repository(db_path)
        cleared = repo.clear_lockout(email)

        if cleared and logger:
            logger.info(f"Account lockout cleared for: {email}")

        return cleared

    except (ImportError, OSError, RuntimeError) as e:
        if logger:
            logger.warning(f"Failed to clear account lockout: {e}")
        return False


def authenticate_user(
    email: str,
    password: str,
    user_repo: Any,
    organization_id: int,
    ip_address: str | None = None,
    db_path: str | None = None,
    logger: logging.Logger | None = None,
) -> User | None:
    """Authenticate a user by email and password.

    Includes account lockout protection. After MAX_ATTEMPTS failed
    attempts, the account is locked for LOCKOUT_DURATION minutes.
    Lockout duration doubles with each consecutive lockout.

    Args:
        email: User email.
        password: Plain text password.
        user_repo: UserRepository instance.
        organization_id: Organization to authenticate against.
        ip_address: Client IP address for tracking.
        db_path: Path to database for lockout tracking.
        logger: Optional logger.

    Returns:
        User if authenticated, None if invalid credentials or locked.

    Raises:
        AuthenticationError: If account is locked (includes lockout_until).
    """
    from mysql_to_sheets.core.exceptions import AuthenticationError, ErrorCode

    # Check if account is locked
    is_locked, lockout_info = check_account_locked(email, db_path, logger)
    if is_locked:
        raise AuthenticationError(
            message="Account is temporarily locked due to too many failed attempts",
            email=email,
            reason="account_locked",
            code=ErrorCode.AUTH_RATE_LIMITED,
        )

    user = user_repo.get_by_email(email, organization_id)

    if not user:
        if logger:
            logger.debug(f"User not found: {email} in org {organization_id}")
        # Record failed attempt
        record_login_attempt(
            email=email,
            success=False,
            ip_address=ip_address,
            failure_reason="user_not_found",
            db_path=db_path,
            logger=logger,
        )
        return None

    if not user.is_active:
        if logger:
            logger.debug(f"User is inactive: {email}")
        # Record failed attempt
        record_login_attempt(
            email=email,
            success=False,
            ip_address=ip_address,
            failure_reason="user_inactive",
            db_path=db_path,
            logger=logger,
        )
        return None

    if not verify_password(password, user.password_hash):
        if logger:
            logger.debug(f"Invalid password for user: {email}")
        # Record failed attempt
        record_login_attempt(
            email=email,
            success=False,
            ip_address=ip_address,
            failure_reason="invalid_password",
            db_path=db_path,
            logger=logger,
        )
        return None

    # Successful login - record and clear any lockout
    record_login_attempt(
        email=email,
        success=True,
        ip_address=ip_address,
        db_path=db_path,
        logger=logger,
    )

    # Update last login timestamp
    user_repo.update_last_login(user.id)

    if logger:
        logger.info(f"User authenticated: {email} (org {organization_id})")

    return user  # type: ignore[no-any-return]


def generate_password_reset_token(
    user: User,
    config: AuthConfig,
    expires_hours: int = 24,
) -> str:
    """Generate a password reset token.

    Args:
        user: User requesting reset.
        config: Authentication configuration.
        expires_hours: Token expiration in hours.

    Returns:
        JWT reset token string.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=expires_hours)

    payload = {
        "user_id": user.id,
        "email": user.email,
        "organization_id": user.organization_id,
        "token_type": "password_reset",
        "exp": expires,
        "iat": now,
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)


def verify_password_reset_token(
    token: str,
    config: AuthConfig,
) -> dict[str, Any] | None:
    """Verify a password reset token.

    Args:
        token: JWT reset token string.
        config: Authentication configuration.

    Returns:
        Dict with user_id, email, organization_id if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret_key,
            algorithms=[config.jwt_algorithm],
        )

        if payload.get("token_type") != "password_reset":
            return None

        # Reject already-used reset tokens
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            return None

        return {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "organization_id": payload["organization_id"],
            "jti": jti,
        }

    except jwt.InvalidTokenError:
        return None


# Persistent token blacklist using SQLite
# Falls back to in-memory if DB unavailable


def blacklist_token(
    jti: str,
    expires_at: datetime | None = None,
    reason: str = "logout",
    db_path: str | None = None,
) -> None:
    """Add a token to the persistent blacklist.

    Args:
        jti: Token ID to blacklist.
        expires_at: When the token expires (for cleanup). If None, uses 7 days.
        reason: Reason for blacklisting (default: "logout").
        db_path: Path to database. Uses tenant DB if None.
    """
    try:
        from mysql_to_sheets.models.token_blacklist import get_token_blacklist_repository

        if expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        repo = get_token_blacklist_repository(db_path)
        repo.add(jti, expires_at, reason)
    except (ImportError, OSError, RuntimeError) as e:
        # Log but don't fail - blacklisting is best-effort
        logger = logging.getLogger("mysql_to_sheets.core.auth")
        logger.warning(f"Failed to blacklist token: {e}")


def is_token_blacklisted(jti: str, db_path: str | None = None) -> bool:
    """Check if a token is blacklisted.

    Args:
        jti: Token ID to check.
        db_path: Path to database. Uses tenant DB if None.

    Returns:
        True if blacklisted, False otherwise.
    """
    try:
        from mysql_to_sheets.models.token_blacklist import get_token_blacklist_repository

        repo = get_token_blacklist_repository(db_path)
        return repo.is_blacklisted(jti)
    except (ImportError, OSError, RuntimeError) as e:
        # SECURITY: Fail-closed - if we can't check the blacklist, treat the token
        # as blacklisted to prevent revoked tokens from being accepted.
        # This is Edge Case 25: Token blacklist DB unavailable should fail-closed.
        logger = logging.getLogger("mysql_to_sheets.core.auth")
        logger.error(f"Failed to check token blacklist (treating as blacklisted): {e}")
        return True


def cleanup_expired_tokens(db_path: str | None = None) -> int:
    """Remove expired entries from the token blacklist.

    Args:
        db_path: Path to database. Uses tenant DB if None.

    Returns:
        Number of entries removed.
    """
    try:
        from mysql_to_sheets.models.token_blacklist import get_token_blacklist_repository

        repo = get_token_blacklist_repository(db_path)
        return repo.cleanup_expired()
    except (ImportError, OSError, RuntimeError) as e:
        logger = logging.getLogger("mysql_to_sheets.core.auth")
        logger.warning(f"Failed to cleanup expired tokens: {e}")
        return 0


def clear_token_blacklist(db_path: str | None = None) -> None:
    """Clear the token blacklist. FOR TESTING ONLY.

    Args:
        db_path: Path to database. Uses tenant DB if None.
    """
    try:
        from mysql_to_sheets.models.token_blacklist import (
            get_token_blacklist_repository,
            reset_token_blacklist_repository,
        )

        repo = get_token_blacklist_repository(db_path)
        repo.clear()
        reset_token_blacklist_repository()
    except (ImportError, OSError, RuntimeError):
        pass


# Singleton config instance
_auth_config: AuthConfig | None = None


def get_auth_config() -> AuthConfig:
    """Get or create authentication config singleton.

    Returns:
        AuthConfig instance.
    """
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig.from_env()
    return _auth_config


def reset_auth_config() -> None:
    """Reset auth config singleton. For testing."""
    global _auth_config
    _auth_config = None
