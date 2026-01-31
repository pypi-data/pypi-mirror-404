"""Backward compatibility shim - import from core.security instead.

This module re-exports all public APIs from the security package.
New code should import directly from mysql_to_sheets.core.security.

Example (preferred):
    >>> from mysql_to_sheets.core.security import Permission, has_permission

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.rbac import Permission, has_permission

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.security.rbac instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.rbac",
    "mysql_to_sheets.core.security.rbac",
)

from mysql_to_sheets.core.security.rbac import (
    PERMISSION_GROUPS,
    ROLE_PERMISSIONS,
    Permission,
    can_manage_role,
    get_assignable_roles,
    get_permissions,
    get_role_hierarchy,
    has_all_permissions,
    has_any_permission,
    has_permission,
    has_permission_group,
    is_higher_role,
    validate_role,
)

__all__ = [
    "Permission",
    "PERMISSION_GROUPS",
    "ROLE_PERMISSIONS",
    "has_permission",
    "get_permissions",
    "has_any_permission",
    "has_all_permissions",
    "get_role_hierarchy",
    "is_higher_role",
    "can_manage_role",
    "get_assignable_roles",
    "validate_role",
    "has_permission_group",
]
