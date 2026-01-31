"""License key validation for self-hosted subscriptions.

JWT-based license keys embed tier, expiration, and customer info.
Validation is offline-capable using asymmetric RS256 verification.

Security model:
- License keys are signed with a private key (kept secure on license server)
- Validation uses only the public key (embedded in this module)
- Users cannot forge licenses without access to the private key

Key rotation support:
- Multiple public keys can be registered with unique key IDs (kid)
- License JWTs include a 'kid' header to select the verification key
- Keys can be fetched from a remote URL for dynamic rotation

Example:
    >>> from mysql_to_sheets.core.license import validate_license, LicenseStatus
    >>>
    >>> license_info = validate_license("eyJhbGciOiJSUzI1NiI...")
    >>> if license_info.status == LicenseStatus.VALID:
    ...     print(f"Licensed to: {license_info.email}")
    ...     print(f"Tier: {license_info.tier.value}")
"""

import functools
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar

import jwt

from mysql_to_sheets.core.billing.tier import Tier

logger = logging.getLogger(__name__)


class LicenseStatus(str, Enum):
    """License validation status."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    MISSING = "missing"
    GRACE_PERIOD = "grace_period"


@dataclass
class LicenseInfo:
    """Decoded license key information.

    Attributes:
        status: Validation status of the license.
        customer_id: Unique customer identifier from payment processor.
        email: Customer email address.
        tier: Subscription tier (FREE, PRO, BUSINESS, ENTERPRISE).
        issued_at: When the license was issued.
        expires_at: When the license expires.
        features: Optional list of feature flags.
        error: Error message if validation failed.
        days_until_expiry: Number of days until license expires (negative if expired).
    """

    status: LicenseStatus
    customer_id: str | None = None
    email: str | None = None
    tier: Tier = Tier.FREE
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    features: list[str] = field(default_factory=list)
    error: str | None = None
    days_until_expiry: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the license info.
        """
        return {
            "status": self.status.value,
            "customer_id": self.customer_id,
            "email": self.email,
            "tier": self.tier.value,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "features": self.features,
            "error": self.error,
            "days_until_expiry": self.days_until_expiry,
        }


# RSA public key for license verification (RS256 algorithm)
# This public key can only VERIFY signatures - it cannot create them.
# License keys are signed by a separate license generation service using the private key.
#
# To generate a new key pair (for production):
#   openssl genrsa -out private_key.pem 2048
#   openssl rsa -in private_key.pem -pubout -out public_key.pem
#
# IMPORTANT: Never distribute the private key. Keep it secure on your license server.
DEFAULT_LICENSE_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzGmnlzqLuyyqH43V2hUP
Gkl8aUPOIEBbTqnDi40xB0dDgHnVxUWfCYEj5eBO/WLtcJVo84O2DslYsm8xGWqJ
Q5MR6ianUNCqmA7+FHRxYYdqOd6TVQytiNKAP4/pY7d4FcUmol+ufuXdtI2a/d+h
3JpIL2DM+55Zhu2ncYITpGQACNGfqE0OjEctjWxR0xOg4AFBx2zVVrQN3q9VKwqK
ktwzqnuARBcXdeF2agLjA05+KI+LiuJf7PUiadcx9smzFJD8zcmi8T/gJ68dFkOA
Ra7r43s+xFI6UzjaY7fjkqoaYBNx2QaKyA1uGXfi97PDIUQAhfCv/dKC50zWO/vU
lwIDAQAB
-----END PUBLIC KEY-----"""

# JWT algorithm for license validation
# RS256 = RSA signature with SHA-256 (asymmetric - public key can only verify)
LICENSE_JWT_ALGORITHM = "RS256"


# License Public Key Registry for Key Rotation
# Stores multiple public keys indexed by key ID (kid)


@dataclass
class LicensePublicKey:
    """A public key for license verification.

    Attributes:
        key_id: Unique identifier for this key (matches JWT 'kid' header).
        public_key: PEM-encoded RSA public key.
        is_active: Whether this key is currently active for verification.
        created_at: When this key was added.
        expires_at: Optional expiration for the key itself.
    """

    key_id: str
    public_key: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if this key has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class LicenseKeyRegistry:
    """Registry for managing multiple license public keys.

    Supports key rotation by storing multiple public keys indexed
    by key ID. License JWTs can specify which key to use via the
    'kid' header.
    """

    def __init__(self) -> None:
        self._keys: dict[str, LicensePublicKey] = {}
        self._lock = threading.Lock()
        # Register the default key with a default kid
        self.register_key(
            key_id="default",
            public_key=DEFAULT_LICENSE_PUBLIC_KEY,
            is_active=True,
        )

    def register_key(
        self,
        key_id: str,
        public_key: str,
        is_active: bool = True,
        expires_at: datetime | None = None,
    ) -> None:
        """Register a public key for license verification.

        Args:
            key_id: Unique identifier for this key.
            public_key: PEM-encoded RSA public key.
            is_active: Whether this key is active for verification.
            expires_at: Optional expiration for the key.
        """
        with self._lock:
            self._keys[key_id] = LicensePublicKey(
                key_id=key_id,
                public_key=public_key,
                is_active=is_active,
                expires_at=expires_at,
            )
            logger.debug(f"Registered license public key: {key_id}")

    def deactivate_key(self, key_id: str) -> bool:
        """Deactivate a public key.

        Args:
            key_id: Key ID to deactivate.

        Returns:
            True if key was found and deactivated.
        """
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id].is_active = False
                logger.info(f"Deactivated license public key: {key_id}")
                return True
            return False

    def get_key(self, key_id: str) -> LicensePublicKey | None:
        """Get a public key by ID.

        Args:
            key_id: Key ID to look up.

        Returns:
            LicensePublicKey if found and active, None otherwise.
        """
        with self._lock:
            key = self._keys.get(key_id)
            if key and key.is_active and not key.is_expired():
                return key
            return None

    def get_all_active_keys(self) -> list[LicensePublicKey]:
        """Get all active, non-expired keys.

        Returns:
            List of active public keys.
        """
        with self._lock:
            return [
                key
                for key in self._keys.values()
                if key.is_active and not key.is_expired()
            ]

    def clear(self) -> None:
        """Clear all registered keys (for testing)."""
        with self._lock:
            self._keys.clear()
            # Re-register default key
            self._keys["default"] = LicensePublicKey(
                key_id="default",
                public_key=DEFAULT_LICENSE_PUBLIC_KEY,
                is_active=True,
            )


# Global key registry
_key_registry: LicenseKeyRegistry | None = None
_registry_lock = threading.Lock()


def get_key_registry() -> LicenseKeyRegistry:
    """Get the global license key registry.

    Returns:
        LicenseKeyRegistry singleton instance.
    """
    global _key_registry
    with _registry_lock:
        if _key_registry is None:
            _key_registry = LicenseKeyRegistry()
        return _key_registry


def reset_key_registry() -> None:
    """Reset the key registry (for testing)."""
    global _key_registry
    with _registry_lock:
        _key_registry = None


def fetch_remote_keys(url: str | None = None, timeout: int = 10) -> int:
    """Fetch public keys from a remote URL.

    The URL should return a JSON array of key objects:
    [
        {
            "key_id": "key_2024_01",
            "public_key": "-----BEGIN PUBLIC KEY-----...",
            "is_active": true,
            "expires_at": "2025-01-01T00:00:00Z"  // optional
        }
    ]

    Args:
        url: URL to fetch keys from. Defaults to LICENSE_PUBLIC_KEY_URL env var.
        timeout: Request timeout in seconds.

    Returns:
        Number of keys registered.

    Raises:
        ValueError: If URL is not configured.
        RuntimeError: If fetch fails.
    """
    import json
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    if url is None:
        url = os.getenv("LICENSE_PUBLIC_KEY_URL")

    if not url:
        raise ValueError("LICENSE_PUBLIC_KEY_URL is not configured")

    try:
        request = Request(url, headers={"Accept": "application/json"})
        response = urlopen(request, timeout=timeout)
        data = json.loads(response.read().decode("utf-8"))

        if not isinstance(data, list):
            raise RuntimeError(f"Expected JSON array from {url}, got {type(data).__name__}")

        registry = get_key_registry()
        count = 0

        for key_data in data:
            if not isinstance(key_data, dict):
                continue

            key_id = key_data.get("key_id")
            public_key = key_data.get("public_key")

            if not key_id or not public_key:
                logger.warning(f"Skipping key without key_id or public_key: {key_data}")
                continue

            expires_at = None
            expires_str = key_data.get("expires_at")
            if expires_str:
                try:
                    expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid expires_at for key {key_id}: {expires_str}")

            registry.register_key(
                key_id=key_id,
                public_key=public_key,
                is_active=key_data.get("is_active", True),
                expires_at=expires_at,
            )
            count += 1

        logger.info(f"Fetched {count} license public key(s) from {url}")
        return count

    except HTTPError as e:
        raise RuntimeError(f"Failed to fetch keys from {url}: HTTP {e.code}") from e
    except URLError as e:
        raise RuntimeError(f"Failed to fetch keys from {url}: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from {url}: {e}") from e


def _get_key_for_license(license_key: str) -> str | None:
    """Get the appropriate public key for verifying a license.

    Examines the JWT header for a 'kid' claim and returns the
    corresponding public key. If no 'kid' is present or the
    key is not found, returns None to indicate all keys should
    be tried.

    Args:
        license_key: The JWT license key string.

    Returns:
        Public key PEM string if found, None otherwise.
    """
    try:
        # Decode header without verification to get kid
        header = jwt.get_unverified_header(license_key.strip())
        kid = header.get("kid")

        if kid:
            registry = get_key_registry()
            key = registry.get_key(kid)
            if key:
                logger.debug(f"Using license public key: {kid}")
                return key.public_key
            logger.warning(f"License specifies unknown key ID: {kid}")

        return None

    except jwt.DecodeError:
        return None


def validate_license(
    license_key: str,
    public_key: str | None = None,
    grace_days: int = 3,
) -> LicenseInfo:
    """Validate a JWT license key using RS256 asymmetric verification.

    Decodes and validates a JWT license key, checking the signature,
    expiration, and extracting tier information. Uses RS256 (asymmetric)
    algorithm - only the public key is needed for verification.

    Key rotation support:
    - If the license includes a 'kid' header, uses that specific key
    - If no 'kid' or key not found, tries all active keys in the registry
    - Falls back to the provided public_key or default embedded key

    Args:
        license_key: JWT license key string (RS256 signed).
        public_key: RSA public key for verification. If None, uses key registry.
        grace_days: Number of days of grace period after expiration.

    Returns:
        LicenseInfo with validation results.

    Example:
        >>> info = validate_license("eyJhbGciOiJSUzI1NiI...")
        >>> if info.status == LicenseStatus.VALID:
        ...     print(f"Tier: {info.tier.value}")
    """
    if not license_key or not license_key.strip():
        return LicenseInfo(
            status=LicenseStatus.MISSING,
            error="No license key provided",
        )

    # Determine which key(s) to try
    keys_to_try: list[str] = []

    if public_key:
        # Explicit key provided, use only that
        keys_to_try = [public_key]
    else:
        # Check for kid header in JWT
        kid_key = _get_key_for_license(license_key)
        if kid_key:
            keys_to_try = [kid_key]
        else:
            # Try all active keys from registry
            registry = get_key_registry()
            active_keys = registry.get_all_active_keys()
            keys_to_try = [k.public_key for k in active_keys]

            # Ensure default key is always tried
            if not keys_to_try:
                keys_to_try = [DEFAULT_LICENSE_PUBLIC_KEY]

    # Try each key until one works
    last_error: str | None = None
    for key in keys_to_try:
        result = _validate_with_key(license_key, key, grace_days)
        if result.status != LicenseStatus.INVALID:
            return result
        last_error = result.error

    # All keys failed
    return LicenseInfo(
        status=LicenseStatus.INVALID,
        error=last_error or "Invalid license signature - no valid key found",
    )


def _validate_with_key(
    license_key: str,
    key: str,
    grace_days: int,
) -> LicenseInfo:
    """Validate a license with a specific public key.

    Args:
        license_key: JWT license key string.
        key: PEM-encoded public key.
        grace_days: Number of days of grace period.

    Returns:
        LicenseInfo with validation results.
    """
    try:
        # Decode JWT with RS256 algorithm
        # We handle expiry manually for grace period support
        payload = jwt.decode(
            license_key.strip(),
            key,
            algorithms=[LICENSE_JWT_ALGORITHM],
            options={"verify_exp": False},  # We handle expiry manually for grace period
        )

        # Extract timestamps
        iat_timestamp = payload.get("iat")
        exp_timestamp = payload.get("exp")

        issued_at = (
            datetime.fromtimestamp(iat_timestamp, tz=timezone.utc) if iat_timestamp else None
        )
        expires_at = (
            datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None
        )

        # Calculate days until expiry
        now = datetime.now(timezone.utc)
        days_until_expiry: int | None = None
        if expires_at:
            delta = expires_at - now
            days_until_expiry = delta.days

        # Determine status based on expiration
        status = LicenseStatus.VALID
        if expires_at and now > expires_at:
            if (
                grace_days > 0
                and days_until_expiry is not None
                and days_until_expiry >= -grace_days
            ):
                status = LicenseStatus.GRACE_PERIOD
                logger.warning(
                    "License is in grace period. Expired %d days ago.",
                    -days_until_expiry,
                )
            else:
                status = LicenseStatus.EXPIRED
                logger.warning("License has expired.")

        # Map tier string to Tier enum
        tier_str = payload.get("tier", "free").lower()
        try:
            tier = Tier(tier_str)
        except ValueError:
            logger.warning("Unknown tier '%s' in license, defaulting to FREE", tier_str)
            tier = Tier.FREE

        # Extract features
        features = payload.get("features", [])
        if not isinstance(features, list):
            features = []

        return LicenseInfo(
            status=status,
            customer_id=payload.get("sub"),
            email=payload.get("email"),
            tier=tier,
            issued_at=issued_at,
            expires_at=expires_at,
            features=features,
            days_until_expiry=days_until_expiry,
        )

    except jwt.ExpiredSignatureError:
        # This shouldn't happen since we disabled verify_exp, but handle it anyway
        return LicenseInfo(
            status=LicenseStatus.EXPIRED,
            error="License has expired",
        )
    except jwt.InvalidSignatureError:
        return LicenseInfo(
            status=LicenseStatus.INVALID,
            error="Invalid license signature - key may be tampered",
        )
    except jwt.DecodeError as e:
        return LicenseInfo(
            status=LicenseStatus.INVALID,
            error=f"Invalid license format: {e}",
        )
    except jwt.InvalidTokenError as e:
        return LicenseInfo(
            status=LicenseStatus.INVALID,
            error=f"Invalid license: {e}",
        )
    except (OSError, ValueError, KeyError) as e:
        logger.exception("Unexpected error validating license")
        return LicenseInfo(
            status=LicenseStatus.INVALID,
            error=f"License validation error: {e}",
        )


def get_effective_tier(license_info: LicenseInfo) -> Tier:
    """Get the effective tier from license, falling back to FREE.

    Args:
        license_info: Validated license information.

    Returns:
        The tier from the license if valid/grace period, otherwise FREE.
    """
    if license_info.status in (LicenseStatus.VALID, LicenseStatus.GRACE_PERIOD):
        return license_info.tier
    return Tier.FREE


def is_license_valid(license_info: LicenseInfo) -> bool:
    """Check if a license allows operation.

    A license is considered valid for operation if it is VALID
    or in GRACE_PERIOD.

    Args:
        license_info: Validated license information.

    Returns:
        True if the license allows operation.
    """
    return license_info.status in (LicenseStatus.VALID, LicenseStatus.GRACE_PERIOD)


def get_license_info_from_config() -> LicenseInfo:
    """Get license info from the current configuration.

    Reads the license key from config and validates it.

    Returns:
        LicenseInfo from current configuration.
    """
    from mysql_to_sheets.core.config import get_config

    config = get_config()
    return validate_license(
        config.license_key,
        config.license_public_key or None,
        config.license_offline_grace_days,
    )


# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def require_valid_license(func: F) -> F:
    """Decorator to require a valid license before execution.

    Validates the license from configuration before executing the
    decorated function. Raises LicenseError if the license is
    missing, invalid, or expired.

    Args:
        func: Function to decorate.

    Returns:
        Decorated function.

    Example:
        >>> @require_valid_license
        ... def sync_data():
        ...     # This function requires a valid license
        ...     pass
    """
    from mysql_to_sheets.core.exceptions import LicenseError

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        license_info = get_license_info_from_config()

        if license_info.status == LicenseStatus.MISSING:
            raise LicenseError(
                message="License key required. Set LICENSE_KEY in your .env file",
                code="LICENSE_001",
            )
        if license_info.status == LicenseStatus.INVALID:
            raise LicenseError(
                message=f"Invalid license key: {license_info.error}",
                code="LICENSE_002",
            )
        if license_info.status == LicenseStatus.EXPIRED:
            expires_str = (
                license_info.expires_at.strftime("%Y-%m-%d")
                if license_info.expires_at
                else "unknown"
            )
            raise LicenseError(
                message=f"License expired on {expires_str}. Please renew your subscription",
                code="LICENSE_003",
            )

        return func(*args, **kwargs)

    return wrapper  # type: ignore


def require_tier(required_tier: Tier | str) -> Callable[[F], F]:
    """Decorator to require a specific tier level.

    Validates that the license provides at least the required tier
    before executing the decorated function.

    Args:
        required_tier: Minimum tier required (as Tier enum or string).

    Returns:
        Decorator function.

    Example:
        >>> @require_tier(Tier.PRO)
        ... def scheduled_sync():
        ...     # This function requires PRO tier or higher
        ...     pass
    """
    from mysql_to_sheets.core.exceptions import LicenseError

    if isinstance(required_tier, str):
        required_tier = Tier(required_tier.lower())

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            license_info = get_license_info_from_config()

            if not is_license_valid(license_info):
                if license_info.status == LicenseStatus.MISSING:
                    raise LicenseError(
                        message=f"This feature requires {required_tier.value.upper()} tier. "
                        "Set LICENSE_KEY in your .env file",
                        code="LICENSE_001",
                    )
                elif license_info.status == LicenseStatus.EXPIRED:
                    raise LicenseError(
                        message="License has expired. Please renew your subscription",
                        code="LICENSE_003",
                    )
                else:
                    raise LicenseError(
                        message=f"Invalid license: {license_info.error}",
                        code="LICENSE_002",
                    )

            effective_tier = get_effective_tier(license_info)
            if effective_tier < required_tier:
                raise LicenseError(
                    message=f"This feature requires {required_tier.value.upper()} tier or higher. "
                    f"Current tier: {effective_tier.value.upper()}",
                    code="LICENSE_004",
                    current_tier=effective_tier.value,
                    required_tier=required_tier.value,
                )

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


# NOTE: License key generation has been removed from this module for security.
#
# License keys should be generated by a SEPARATE service that has access to the
# private RSA key. This ensures:
# 1. The private key is never distributed with the application
# 2. Users cannot forge license keys
# 3. License generation can be integrated with payment webhooks
#
# Example license generation service (NOT included in this codebase):
#
#   import jwt
#   from datetime import datetime, timedelta, timezone
#
#   PRIVATE_KEY = open("private_key.pem").read()  # NEVER distribute this!
#
#   def generate_license_key(customer_id, email, tier, duration_days=30):
#       now = datetime.now(timezone.utc)
#       payload = {
#           "sub": customer_id,
#           "email": email,
#           "tier": tier,
#           "iat": int(now.timestamp()),
#           "exp": int((now + timedelta(days=duration_days)).timestamp()),
#           "iss": "mysql-to-sheets",
#       }
#       return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
