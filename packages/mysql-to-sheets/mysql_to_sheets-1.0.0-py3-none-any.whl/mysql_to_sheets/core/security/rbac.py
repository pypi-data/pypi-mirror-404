"""Role-Based Access Control (RBAC) system.

Defines permissions and role mappings for the multi-tenant system.
Each user has a role that grants them specific permissions.
"""

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mysql_to_sheets.models.users import User


class Permission(Enum):
    """Permissions available in the system.

    Permissions are atomic actions that can be performed.
    Roles grant sets of permissions to users.
    """

    # Configuration management
    VIEW_CONFIGS = "view_configs"
    EDIT_CONFIGS = "edit_configs"
    DELETE_CONFIGS = "delete_configs"

    # Sync operations
    RUN_SYNC = "run_sync"
    VIEW_HISTORY = "view_history"

    # User management
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"

    # Organization management
    VIEW_ORGANIZATION = "view_organization"
    MANAGE_ORGANIZATION = "manage_organization"

    # API key management
    VIEW_API_KEYS = "view_api_keys"
    MANAGE_API_KEYS = "manage_api_keys"

    # Schedule management
    VIEW_SCHEDULES = "view_schedules"
    MANAGE_SCHEDULES = "manage_schedules"

    # Webhook management
    VIEW_WEBHOOKS = "view_webhooks"
    MANAGE_WEBHOOKS = "manage_webhooks"

    # Notification settings
    VIEW_NOTIFICATIONS = "view_notifications"
    MANAGE_NOTIFICATIONS = "manage_notifications"

    # Audit logging (Phase 4)
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_AUDIT_LOGS = "export_audit_logs"

    # Owner-only permissions
    TRANSFER_OWNERSHIP = "transfer_ownership"
    DELETE_ORGANIZATION = "delete_organization"
    MANAGE_BILLING = "manage_billing"


# Define which permissions each role has
ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "owner": {
        # All permissions including owner-only
        Permission.VIEW_CONFIGS,
        Permission.EDIT_CONFIGS,
        Permission.DELETE_CONFIGS,
        Permission.RUN_SYNC,
        Permission.VIEW_HISTORY,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ORGANIZATION,
        Permission.MANAGE_ORGANIZATION,
        Permission.VIEW_API_KEYS,
        Permission.MANAGE_API_KEYS,
        Permission.VIEW_SCHEDULES,
        Permission.MANAGE_SCHEDULES,
        Permission.VIEW_WEBHOOKS,
        Permission.MANAGE_WEBHOOKS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.MANAGE_NOTIFICATIONS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_AUDIT_LOGS,
        Permission.TRANSFER_OWNERSHIP,
        Permission.DELETE_ORGANIZATION,
        Permission.MANAGE_BILLING,
    },
    "admin": {
        # Full access except owner-only permissions
        Permission.VIEW_CONFIGS,
        Permission.EDIT_CONFIGS,
        Permission.DELETE_CONFIGS,
        Permission.RUN_SYNC,
        Permission.VIEW_HISTORY,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ORGANIZATION,
        Permission.MANAGE_ORGANIZATION,
        Permission.VIEW_API_KEYS,
        Permission.MANAGE_API_KEYS,
        Permission.VIEW_SCHEDULES,
        Permission.MANAGE_SCHEDULES,
        Permission.VIEW_WEBHOOKS,
        Permission.MANAGE_WEBHOOKS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.MANAGE_NOTIFICATIONS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_AUDIT_LOGS,
    },
    "operator": {
        # Run syncs, manage own configs, view history
        Permission.VIEW_CONFIGS,
        Permission.EDIT_CONFIGS,
        Permission.RUN_SYNC,
        Permission.VIEW_HISTORY,
        Permission.VIEW_USERS,
        Permission.VIEW_ORGANIZATION,
        Permission.VIEW_API_KEYS,
        Permission.VIEW_SCHEDULES,
        Permission.MANAGE_SCHEDULES,
        Permission.VIEW_WEBHOOKS,
        Permission.MANAGE_WEBHOOKS,
        Permission.VIEW_NOTIFICATIONS,
    },
    "viewer": {
        # Read-only access
        Permission.VIEW_CONFIGS,
        Permission.VIEW_HISTORY,
        Permission.VIEW_USERS,
        Permission.VIEW_ORGANIZATION,
        Permission.VIEW_API_KEYS,
        Permission.VIEW_SCHEDULES,
        Permission.VIEW_WEBHOOKS,
        Permission.VIEW_NOTIFICATIONS,
    },
}


def has_permission(user: "User", permission: Permission) -> bool:
    """Check if a user has a specific permission.

    Args:
        user: User to check.
        permission: Permission to check for.

    Returns:
        True if user has the permission, False otherwise.
    """
    if not user.is_active:
        return False

    role_perms = ROLE_PERMISSIONS.get(user.role, set())
    return permission in role_perms


def get_permissions(role: str) -> set[Permission]:
    """Get all permissions for a role.

    Args:
        role: Role name.

    Returns:
        Set of permissions for the role.
    """
    return ROLE_PERMISSIONS.get(role, set()).copy()


def has_any_permission(user: "User", permissions: list[Permission]) -> bool:
    """Check if a user has any of the specified permissions.

    Args:
        user: User to check.
        permissions: List of permissions to check.

    Returns:
        True if user has any of the permissions, False otherwise.
    """
    if not user.is_active:
        return False

    role_perms = ROLE_PERMISSIONS.get(user.role, set())
    return any(p in role_perms for p in permissions)


def has_all_permissions(user: "User", permissions: list[Permission]) -> bool:
    """Check if a user has all of the specified permissions.

    Args:
        user: User to check.
        permissions: List of permissions to check.

    Returns:
        True if user has all of the permissions, False otherwise.
    """
    if not user.is_active:
        return False

    role_perms = ROLE_PERMISSIONS.get(user.role, set())
    return all(p in role_perms for p in permissions)


def get_role_hierarchy() -> list[str]:
    """Get roles in order from highest to lowest privilege.

    Returns:
        List of role names in privilege order.
    """
    return ["owner", "admin", "operator", "viewer"]


def is_higher_role(role1: str, role2: str) -> bool:
    """Check if role1 is higher privilege than role2.

    Args:
        role1: First role to compare.
        role2: Second role to compare.

    Returns:
        True if role1 has higher privilege than role2.
    """
    hierarchy = get_role_hierarchy()
    try:
        return hierarchy.index(role1) < hierarchy.index(role2)
    except ValueError:
        return False


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """Check if a user with manager_role can manage users with target_role.

    Rules:
    - Owners can manage any role
    - Admins can manage operators and viewers
    - Users cannot manage users with equal or higher roles

    Args:
        manager_role: Role of the user trying to manage.
        target_role: Role of the user being managed.

    Returns:
        True if manager can manage target, False otherwise.
    """
    if manager_role == "owner":
        return True
    if manager_role == "admin":
        return target_role in ("operator", "viewer")
    return False


def get_assignable_roles(assigner_role: str) -> list[str]:
    """Get roles that a user with assigner_role can assign to others.

    Args:
        assigner_role: Role of the user assigning roles.

    Returns:
        List of roles that can be assigned.
    """
    if assigner_role == "owner":
        return ["admin", "operator", "viewer"]
    if assigner_role == "admin":
        return ["operator", "viewer"]
    return []


def validate_role(role: str) -> bool:
    """Check if a role name is valid.

    Args:
        role: Role name to validate.

    Returns:
        True if role is valid, False otherwise.
    """
    return role in ROLE_PERMISSIONS


# Permission groups for common operations
PERMISSION_GROUPS = {
    "config_admin": {
        Permission.VIEW_CONFIGS,
        Permission.EDIT_CONFIGS,
        Permission.DELETE_CONFIGS,
    },
    "sync_operator": {
        Permission.RUN_SYNC,
        Permission.VIEW_HISTORY,
    },
    "user_admin": {
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
    },
    "org_admin": {
        Permission.VIEW_ORGANIZATION,
        Permission.MANAGE_ORGANIZATION,
    },
    "full_admin": {
        Permission.VIEW_CONFIGS,
        Permission.EDIT_CONFIGS,
        Permission.DELETE_CONFIGS,
        Permission.RUN_SYNC,
        Permission.VIEW_HISTORY,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ORGANIZATION,
        Permission.MANAGE_ORGANIZATION,
        Permission.VIEW_API_KEYS,
        Permission.MANAGE_API_KEYS,
        Permission.VIEW_SCHEDULES,
        Permission.MANAGE_SCHEDULES,
        Permission.VIEW_WEBHOOKS,
        Permission.MANAGE_WEBHOOKS,
        Permission.VIEW_NOTIFICATIONS,
        Permission.MANAGE_NOTIFICATIONS,
    },
}


def has_permission_group(user: "User", group_name: str) -> bool:
    """Check if user has all permissions in a permission group.

    Args:
        user: User to check.
        group_name: Name of the permission group.

    Returns:
        True if user has all permissions in the group, False otherwise.
    """
    if group_name not in PERMISSION_GROUPS:
        return False
    return has_all_permissions(user, list(PERMISSION_GROUPS[group_name]))
