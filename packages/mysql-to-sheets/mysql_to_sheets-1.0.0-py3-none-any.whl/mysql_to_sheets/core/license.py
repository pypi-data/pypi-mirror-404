"""Backward compatibility shim - import from core.billing instead.

This module re-exports all public APIs from the billing package.
New code should import directly from mysql_to_sheets.core.billing.

Example (preferred):
    >>> from mysql_to_sheets.core.billing import validate_license, LicenseStatus

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.license import validate_license, LicenseStatus

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.billing.license instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.license",
    "mysql_to_sheets.core.billing.license",
)

from mysql_to_sheets.core.billing.license import (
    DEFAULT_LICENSE_PUBLIC_KEY,
    LICENSE_JWT_ALGORITHM,
    LicenseInfo,
    LicenseKeyRegistry,
    LicensePublicKey,
    LicenseStatus,
    fetch_remote_keys,
    get_effective_tier,
    get_key_registry,
    get_license_info_from_config,
    is_license_valid,
    require_tier,
    require_valid_license,
    reset_key_registry,
    validate_license,
)

__all__ = [
    "LicenseStatus",
    "LicenseInfo",
    "LicensePublicKey",
    "LicenseKeyRegistry",
    "DEFAULT_LICENSE_PUBLIC_KEY",
    "LICENSE_JWT_ALGORITHM",
    "validate_license",
    "get_effective_tier",
    "is_license_valid",
    "get_license_info_from_config",
    "require_valid_license",
    "require_tier",
    "get_key_registry",
    "reset_key_registry",
    "fetch_remote_keys",
]
