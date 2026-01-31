"""Tests for RBAC permission enforcement."""

from mysql_to_sheets.core.rbac import (
    ROLE_PERMISSIONS,
    Permission,
    can_manage_role,
    get_assignable_roles,
    get_permissions,
    get_role_hierarchy,
    has_all_permissions,
    has_any_permission,
    has_permission,
    is_higher_role,
    validate_role,
)
from mysql_to_sheets.models.users import User


def _make_user(role: str, is_active: bool = True) -> User:
    """Create a minimal User for testing."""
    return User(
        id=1,
        email="test@example.com",
        display_name="Test User",
        organization_id=1,
        role=role,
        is_active=is_active,
    )


class TestRolePermissionMatrix:
    """Verify each role has exactly the expected permissions."""

    # Owner-only permissions
    OWNER_ONLY = {
        Permission.TRANSFER_OWNERSHIP,
        Permission.DELETE_ORGANIZATION,
        Permission.MANAGE_BILLING,
    }

    # Permissions admins have but operators don't
    ADMIN_ONLY = {
        Permission.DELETE_CONFIGS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ORGANIZATION,
        Permission.MANAGE_API_KEYS,
        Permission.EXPORT_AUDIT_LOGS,
    }

    def test_owner_has_all_permissions(self):
        user = _make_user("owner")
        for perm in Permission:
            assert has_permission(user, perm), f"Owner should have {perm.name}"

    def test_admin_lacks_owner_only_permissions(self):
        user = _make_user("admin")
        for perm in self.OWNER_ONLY:
            assert not has_permission(user, perm), f"Admin should not have {perm.name}"

    def test_admin_has_management_permissions(self):
        user = _make_user("admin")
        for perm in self.ADMIN_ONLY:
            assert has_permission(user, perm), f"Admin should have {perm.name}"

    def test_operator_lacks_admin_permissions(self):
        user = _make_user("operator")
        for perm in self.ADMIN_ONLY:
            assert not has_permission(user, perm), f"Operator should not have {perm.name}"

    def test_operator_can_run_sync(self):
        user = _make_user("operator")
        assert has_permission(user, Permission.RUN_SYNC)
        assert has_permission(user, Permission.EDIT_CONFIGS)
        assert has_permission(user, Permission.MANAGE_SCHEDULES)

    def test_viewer_is_read_only(self):
        user = _make_user("viewer")
        # Should have view permissions
        assert has_permission(user, Permission.VIEW_CONFIGS)
        assert has_permission(user, Permission.VIEW_HISTORY)
        assert has_permission(user, Permission.VIEW_USERS)

        # Should NOT have write permissions
        assert not has_permission(user, Permission.EDIT_CONFIGS)
        assert not has_permission(user, Permission.DELETE_CONFIGS)
        assert not has_permission(user, Permission.RUN_SYNC)
        assert not has_permission(user, Permission.MANAGE_USERS)
        assert not has_permission(user, Permission.MANAGE_SCHEDULES)


class TestFailClosed:
    """Verify RBAC denies by default for unknown roles and inactive users."""

    def test_unknown_role_denied(self):
        user = _make_user("nonexistent_role")
        for perm in Permission:
            assert not has_permission(user, perm), f"Unknown role should be denied {perm.name}"

    def test_inactive_user_denied(self):
        user = _make_user("owner", is_active=False)
        for perm in Permission:
            assert not has_permission(user, perm), f"Inactive owner should be denied {perm.name}"

    def test_inactive_admin_denied(self):
        user = _make_user("admin", is_active=False)
        assert not has_permission(user, Permission.VIEW_CONFIGS)

    def test_empty_role_denied(self):
        user = _make_user("")
        assert not has_permission(user, Permission.VIEW_CONFIGS)


class TestHasAnyPermission:
    """Test has_any_permission checks."""

    def test_returns_true_if_any_match(self):
        user = _make_user("viewer")
        assert has_any_permission(user, [Permission.VIEW_CONFIGS, Permission.RUN_SYNC])

    def test_returns_false_if_none_match(self):
        user = _make_user("viewer")
        assert not has_any_permission(user, [Permission.RUN_SYNC, Permission.DELETE_CONFIGS])

    def test_inactive_user_returns_false(self):
        user = _make_user("owner", is_active=False)
        assert not has_any_permission(user, [Permission.VIEW_CONFIGS])


class TestHasAllPermissions:
    """Test has_all_permissions checks."""

    def test_returns_true_when_all_present(self):
        user = _make_user("owner")
        assert has_all_permissions(user, [Permission.RUN_SYNC, Permission.DELETE_CONFIGS])

    def test_returns_false_when_missing_one(self):
        user = _make_user("operator")
        assert not has_all_permissions(user, [Permission.RUN_SYNC, Permission.DELETE_CONFIGS])

    def test_inactive_user_returns_false(self):
        user = _make_user("admin", is_active=False)
        assert not has_all_permissions(user, [Permission.VIEW_CONFIGS])


class TestCanManageRole:
    """Test role management hierarchy."""

    def test_owner_can_manage_all(self):
        assert can_manage_role("owner", "admin")
        assert can_manage_role("owner", "operator")
        assert can_manage_role("owner", "viewer")
        assert can_manage_role("owner", "owner")

    def test_admin_can_manage_lower_roles(self):
        assert can_manage_role("admin", "operator")
        assert can_manage_role("admin", "viewer")

    def test_admin_cannot_manage_peers_or_above(self):
        assert not can_manage_role("admin", "admin")
        assert not can_manage_role("admin", "owner")

    def test_operator_cannot_manage_anyone(self):
        assert not can_manage_role("operator", "viewer")
        assert not can_manage_role("operator", "operator")

    def test_viewer_cannot_manage_anyone(self):
        assert not can_manage_role("viewer", "viewer")

    def test_unknown_role_cannot_manage(self):
        assert not can_manage_role("unknown", "viewer")


class TestRoleHierarchy:
    """Test role hierarchy ordering."""

    def test_hierarchy_order(self):
        hierarchy = get_role_hierarchy()
        assert hierarchy == ["owner", "admin", "operator", "viewer"]

    def test_owner_higher_than_admin(self):
        assert is_higher_role("owner", "admin")

    def test_admin_higher_than_operator(self):
        assert is_higher_role("admin", "operator")

    def test_viewer_not_higher_than_anyone(self):
        assert not is_higher_role("viewer", "operator")
        assert not is_higher_role("viewer", "admin")
        assert not is_higher_role("viewer", "owner")

    def test_same_role_not_higher(self):
        assert not is_higher_role("admin", "admin")

    def test_unknown_role_not_higher(self):
        assert not is_higher_role("unknown", "viewer")


class TestGetPermissions:
    """Test get_permissions returns correct sets."""

    def test_returns_copy(self):
        perms = get_permissions("owner")
        perms.add(Permission.VIEW_CONFIGS)  # Modify returned set
        # Original should be unchanged
        assert get_permissions("owner") == ROLE_PERMISSIONS["owner"]

    def test_unknown_role_returns_empty(self):
        assert get_permissions("nonexistent") == set()


class TestAssignableRoles:
    """Test get_assignable_roles."""

    def test_owner_assigns_all_except_owner(self):
        assert get_assignable_roles("owner") == ["admin", "operator", "viewer"]

    def test_admin_assigns_lower(self):
        assert get_assignable_roles("admin") == ["operator", "viewer"]

    def test_operator_assigns_none(self):
        assert get_assignable_roles("operator") == []

    def test_viewer_assigns_none(self):
        assert get_assignable_roles("viewer") == []


class TestValidateRole:
    """Test role validation."""

    def test_valid_roles(self):
        for role in ["owner", "admin", "operator", "viewer"]:
            assert validate_role(role)

    def test_invalid_roles(self):
        assert not validate_role("superadmin")
        assert not validate_role("")
        assert not validate_role("OWNER")  # Case sensitive
