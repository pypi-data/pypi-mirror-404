"""LINK_TOKEN validation for Hybrid Agent authentication.

RS256-signed JWT tokens that authenticate agents to the control plane.
Follows the same pattern as license.py for consistency.

Security model:
- Tokens are signed with a private key on the control plane
- Agents validate using only the embedded public key
- Tokens are revocable server-side via jti tracking
- No expiration by default (revoked on demand)

Token structure:
{
    "sub": "org_123",           # Organization ID
    "iss": "mysql-to-sheets",   # Issuer
    "iat": 1705320000,          # Issued at timestamp
    "jti": "link_abc123",       # Unique token ID (for revocation)
    "scope": "agent",           # Token scope
    "permissions": ["sync", "read_configs"]  # Granted permissions
}
"""

import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import jwt

logger = logging.getLogger(__name__)


class LinkTokenStatus(str, Enum):
    """Link token validation status."""

    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    REVOKED = "revoked"


@dataclass
class LinkTokenInfo:
    """Decoded link token information.

    Attributes:
        status: Validation status of the token.
        organization_id: Organization this agent belongs to.
        jti: Unique token identifier for revocation.
        scope: Token scope (should be "agent").
        permissions: List of granted permissions.
        issued_at: When the token was issued.
        error: Error message if validation failed.
    """

    status: LinkTokenStatus
    organization_id: str | None = None
    jti: str | None = None
    scope: str | None = None
    permissions: list[str] = field(default_factory=list)
    issued_at: datetime | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the token info.
        """
        return {
            "status": self.status.value,
            "organization_id": self.organization_id,
            "jti": self.jti,
            "scope": self.scope,
            "permissions": self.permissions,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "error": self.error,
        }

    def has_permission(self, permission: str) -> bool:
        """Check if token has a specific permission.

        Args:
            permission: Permission to check (e.g., "sync", "read_configs").

        Returns:
            True if permission is granted.
        """
        return permission in self.permissions


# RSA public key for link token verification (RS256 algorithm)
# This is the same key used for license verification.
# In production, this could be a different key for separation of concerns.
DEFAULT_LINK_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzGmnlzqLuyyqH43V2hUP
Gkl8aUPOIEBbTqnDi40xB0dDgHnVxUWfCYEj5eBO/WLtcJVo84O2DslYsm8xGWqJ
Q5MR6ianUNCqmA7+FHRxYYdqOd6TVQytiNKAP4/pY7d4FcUmol+ufuXdtI2a/d+h
3JpIL2DM+55Zhu2ncYITpGQACNGfqE0OjEctjWxR0xOg4AFBx2zVVrQN3q9VKwqK
ktwzqnuARBcXdeF2agLjA05+KI+LiuJf7PUiadcx9smzFJD8zcmi8T/gJ68dFkOA
Ra7r43s+xFI6UzjaY7fjkqoaYBNx2QaKyA1uGXfi97PDIUQAhfCv/dKC50zWO/vU
lwIDAQAB
-----END PUBLIC KEY-----"""

# JWT algorithm for link token validation
LINK_JWT_ALGORITHM = "RS256"


# Token revocation checking (client-side cache)
_revoked_tokens: set[str] = set()
_revoked_tokens_lock = threading.Lock()


def add_revoked_token(jti: str) -> None:
    """Add a token to the local revocation cache.

    Called when control plane reports a token as revoked.

    Args:
        jti: Token ID to revoke.
    """
    with _revoked_tokens_lock:
        _revoked_tokens.add(jti)
        logger.info(f"Token {jti[:8]}... added to revocation cache")


def is_token_revoked(jti: str) -> bool:
    """Check if a token is in the local revocation cache.

    Args:
        jti: Token ID to check.

    Returns:
        True if token is revoked.
    """
    with _revoked_tokens_lock:
        return jti in _revoked_tokens


def clear_revocation_cache() -> None:
    """Clear the local revocation cache. For testing."""
    with _revoked_tokens_lock:
        _revoked_tokens.clear()


def validate_link_token(
    link_token: str,
    public_key: str | None = None,
    check_revocation: bool = True,
) -> LinkTokenInfo:
    """Validate a LINK_TOKEN using RS256 asymmetric verification.

    Decodes and validates a JWT link token, checking the signature
    and extracting organization and permission information.

    Args:
        link_token: JWT link token string (RS256 signed).
        public_key: RSA public key for verification. If None, uses default.
        check_revocation: Whether to check local revocation cache.

    Returns:
        LinkTokenInfo with validation results.

    Example:
        >>> info = validate_link_token("eyJhbGciOiJSUzI1NiI...")
        >>> if info.status == LinkTokenStatus.VALID:
        ...     print(f"Organization: {info.organization_id}")
    """
    if not link_token or not link_token.strip():
        return LinkTokenInfo(
            status=LinkTokenStatus.MISSING,
            error="No link token provided",
        )

    key = public_key or os.getenv("LINK_PUBLIC_KEY") or DEFAULT_LINK_PUBLIC_KEY

    try:
        # Decode JWT with RS256 algorithm
        payload = jwt.decode(
            link_token.strip(),
            key,
            algorithms=[LINK_JWT_ALGORITHM],
            options={"verify_exp": False},  # Link tokens don't expire by default
        )

        # Extract token ID for revocation check
        jti = payload.get("jti")
        if check_revocation and jti and is_token_revoked(jti):
            return LinkTokenInfo(
                status=LinkTokenStatus.REVOKED,
                jti=jti,
                error="Token has been revoked",
            )

        # Verify scope
        scope = payload.get("scope")
        if scope != "agent":
            return LinkTokenInfo(
                status=LinkTokenStatus.INVALID,
                error=f"Invalid token scope: {scope}. Expected 'agent'",
            )

        # Extract timestamps
        iat_timestamp = payload.get("iat")
        issued_at = (
            datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)
            if iat_timestamp
            else None
        )

        # Extract permissions
        permissions = payload.get("permissions", [])
        if not isinstance(permissions, list):
            permissions = []

        return LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            organization_id=payload.get("sub"),
            jti=jti,
            scope=scope,
            permissions=permissions,
            issued_at=issued_at,
        )

    except jwt.InvalidSignatureError:
        return LinkTokenInfo(
            status=LinkTokenStatus.INVALID,
            error="Invalid token signature - token may be tampered",
        )
    except jwt.DecodeError as e:
        return LinkTokenInfo(
            status=LinkTokenStatus.INVALID,
            error=f"Invalid token format: {e}",
        )
    except jwt.InvalidTokenError as e:
        return LinkTokenInfo(
            status=LinkTokenStatus.INVALID,
            error=f"Invalid token: {e}",
        )
    except (OSError, ValueError, KeyError) as e:
        logger.exception("Unexpected error validating link token")
        return LinkTokenInfo(
            status=LinkTokenStatus.INVALID,
            error=f"Token validation error: {e}",
        )


def get_link_token_from_env() -> str:
    """Get link token from environment variable.

    Returns:
        LINK_TOKEN value or empty string.
    """
    return os.getenv("LINK_TOKEN", "")


def get_link_token_info() -> LinkTokenInfo:
    """Get link token info from environment.

    Convenience function that reads LINK_TOKEN from environment
    and validates it.

    Returns:
        LinkTokenInfo from environment token.
    """
    return validate_link_token(get_link_token_from_env())


def is_link_token_valid(token_info: LinkTokenInfo) -> bool:
    """Check if a link token allows operation.

    Args:
        token_info: Validated token information.

    Returns:
        True if the token is valid for operation.
    """
    return token_info.status == LinkTokenStatus.VALID


# NOTE: Link token generation should be done on the control plane.
#
# Example generation (control plane only):
#
#   import jwt
#   import uuid
#   from datetime import datetime, timezone
#
#   PRIVATE_KEY = open("private_key.pem").read()  # NEVER distribute!
#
#   def generate_link_token(organization_id: str, permissions: list[str]):
#       payload = {
#           "sub": organization_id,
#           "iss": "mysql-to-sheets",
#           "iat": int(datetime.now(timezone.utc).timestamp()),
#           "jti": f"link_{uuid.uuid4().hex}",
#           "scope": "agent",
#           "permissions": permissions,
#       }
#       return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
