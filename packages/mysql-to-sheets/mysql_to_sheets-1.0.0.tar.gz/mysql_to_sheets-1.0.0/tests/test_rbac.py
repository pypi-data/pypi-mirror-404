"""Tests for the RBAC module."""

from mysql_to_sheets.core.rbac import (
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
from mysql_to_sheets.models.users import User


class TestPermission:
    """Tests for Permission enum."""

    def test_permission_values(self):
        """Test that permissions have string values."""
        assert Permission.VIEW_CONFIGS.value == "view_configs"
        assert Permission.EDIT_CONFIGS.value == "edit_configs"
        assert Permission.RUN_SYNC.value == "run_sync"
        assert Permission.MANAGE_USERS.value == "manage_users"

    def test_all_permissions_exist(self):
        """Test that expected permissions are defined."""
        expected = [
            "VIEW_CONFIGS",
            "EDIT_CONFIGS",
            "DELETE_CONFIGS",
            "RUN_SYNC",
            "VIEW_HISTORY",
            "VIEW_USERS",
            "MANAGE_USERS",
            "VIEW_ORGANIZATION",
            "MANAGE_ORGANIZATION",
            "VIEW_API_KEYS",
            "MANAGE_API_KEYS",
            "VIEW_SCHEDULES",
            "MANAGE_SCHEDULES",
            "VIEW_WEBHOOKS",
            "MANAGE_WEBHOOKS",
            "VIEW_NOTIFICATIONS",
            "MANAGE_NOTIFICATIONS",
            "TRANSFER_OWNERSHIP",
            "DELETE_ORGANIZATION",
            "MANAGE_BILLING",
        ]

        for perm_name in expected:
            assert hasattr(Permission, perm_name)


class TestRolePermissions:
    """Tests for role-permission mappings."""

    def test_owner_has_all_permissions(self):
        """Test that owner role has all permissions."""
        owner_perms = ROLE_PERMISSIONS["owner"]

        # Check all permissions exist for owner
        for perm in Permission:
            assert perm in owner_perms

    def test_admin_has_full_access_except_owner_only(self):
        """Test that admin has most permissions but not owner-only ones."""
        admin_perms = ROLE_PERMISSIONS["admin"]

        # Admin should have these
        assert Permission.VIEW_CONFIGS in admin_perms
        assert Permission.EDIT_CONFIGS in admin_perms
        assert Permission.MANAGE_USERS in admin_perms
        assert Permission.MANAGE_WEBHOOKS in admin_perms

        # Admin should NOT have owner-only
        assert Permission.TRANSFER_OWNERSHIP not in admin_perms
        assert Permission.DELETE_ORGANIZATION not in admin_perms
        assert Permission.MANAGE_BILLING not in admin_perms

    def test_operator_permissions(self):
        """Test operator role permissions."""
        operator_perms = ROLE_PERMISSIONS["operator"]

        # Operator should have
        assert Permission.VIEW_CONFIGS in operator_perms
        assert Permission.EDIT_CONFIGS in operator_perms
        assert Permission.RUN_SYNC in operator_perms
        assert Permission.MANAGE_SCHEDULES in operator_perms

        # Operator should NOT have
        assert Permission.MANAGE_USERS not in operator_perms
        assert Permission.DELETE_CONFIGS not in operator_perms

    def test_viewer_permissions(self):
        """Test viewer role has read-only permissions."""
        viewer_perms = ROLE_PERMISSIONS["viewer"]

        # Viewer should have view permissions
        assert Permission.VIEW_CONFIGS in viewer_perms
        assert Permission.VIEW_HISTORY in viewer_perms
        assert Permission.VIEW_USERS in viewer_perms
        assert Permission.VIEW_SCHEDULES in viewer_perms

        # Viewer should NOT have any manage/edit permissions
        assert Permission.EDIT_CONFIGS not in viewer_perms
        assert Permission.RUN_SYNC not in viewer_perms
        assert Permission.MANAGE_USERS not in viewer_perms
        assert Permission.MANAGE_SCHEDULES not in viewer_perms


class TestHasPermission:
    """Tests for has_permission function."""

    def _create_user(self, role: str, is_active: bool = True) -> User:
        """Helper to create a test user."""
        return User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role=role,
            is_active=is_active,
            password_hash="hash",
        )

    def test_owner_has_all_permissions(self):
        """Test that owner has all permissions."""
        user = self._create_user("owner")

        for perm in Permission:
            assert has_permission(user, perm) is True

    def test_viewer_has_view_permissions(self):
        """Test that viewer has view permissions."""
        user = self._create_user("viewer")

        assert has_permission(user, Permission.VIEW_CONFIGS) is True
        assert has_permission(user, Permission.VIEW_HISTORY) is True

    def test_viewer_lacks_edit_permissions(self):
        """Test that viewer lacks edit permissions."""
        user = self._create_user("viewer")

        assert has_permission(user, Permission.EDIT_CONFIGS) is False
        assert has_permission(user, Permission.MANAGE_USERS) is False

    def test_inactive_user_has_no_permissions(self):
        """Test that inactive user has no permissions."""
        user = self._create_user("owner", is_active=False)

        assert has_permission(user, Permission.VIEW_CONFIGS) is False
        assert has_permission(user, Permission.MANAGE_ORGANIZATION) is False

    def test_unknown_role_has_no_permissions(self):
        """Test that unknown role has no permissions."""
        user = self._create_user("unknown_role")

        assert has_permission(user, Permission.VIEW_CONFIGS) is False


class TestGetPermissions:
    """Tests for get_permissions function."""

    def test_get_permissions_for_owner(self):
        """Test getting all permissions for owner."""
        perms = get_permissions("owner")

        assert len(perms) == len(Permission)
        assert Permission.TRANSFER_OWNERSHIP in perms

    def test_get_permissions_for_viewer(self):
        """Test getting permissions for viewer."""
        perms = get_permissions("viewer")

        assert Permission.VIEW_CONFIGS in perms
        assert Permission.EDIT_CONFIGS not in perms

    def test_get_permissions_returns_copy(self):
        """Test that get_permissions returns a copy."""
        perms1 = get_permissions("admin")
        perms2 = get_permissions("admin")

        assert perms1 is not perms2  # Different objects
        assert perms1 == perms2  # Same content

    def test_get_permissions_unknown_role(self):
        """Test get_permissions for unknown role returns empty set."""
        perms = get_permissions("nonexistent")
        assert perms == set()


class TestHasAnyPermission:
    """Tests for has_any_permission function."""

    def _create_user(self, role: str) -> User:
        return User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role=role,
            password_hash="hash",
        )

    def test_has_any_permission_true(self):
        """Test has_any_permission returns True when user has at least one."""
        user = self._create_user("viewer")

        result = has_any_permission(
            user,
            [
                Permission.MANAGE_USERS,  # No
                Permission.VIEW_CONFIGS,  # Yes
            ],
        )

        assert result is True

    def test_has_any_permission_false(self):
        """Test has_any_permission returns False when user has none."""
        user = self._create_user("viewer")

        result = has_any_permission(
            user,
            [
                Permission.MANAGE_USERS,
                Permission.EDIT_CONFIGS,
            ],
        )

        assert result is False

    def test_has_any_permission_inactive_user(self):
        """Test inactive user returns False."""
        user = User(
            id=1,
            email="test@example.com",
            display_name="Test",
            organization_id=1,
            role="owner",
            is_active=False,
            password_hash="hash",
        )

        result = has_any_permission(user, [Permission.VIEW_CONFIGS])
        assert result is False


class TestHasAllPermissions:
    """Tests for has_all_permissions function."""

    def _create_user(self, role: str) -> User:
        return User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role=role,
            password_hash="hash",
        )

    def test_has_all_permissions_true(self):
        """Test has_all_permissions returns True when user has all."""
        user = self._create_user("viewer")

        result = has_all_permissions(
            user,
            [
                Permission.VIEW_CONFIGS,
                Permission.VIEW_HISTORY,
            ],
        )

        assert result is True

    def test_has_all_permissions_false(self):
        """Test has_all_permissions returns False when user lacks one."""
        user = self._create_user("viewer")

        result = has_all_permissions(
            user,
            [
                Permission.VIEW_CONFIGS,
                Permission.EDIT_CONFIGS,  # Viewer doesn't have this
            ],
        )

        assert result is False


class TestRoleHierarchy:
    """Tests for role hierarchy functions."""

    def test_get_role_hierarchy(self):
        """Test get_role_hierarchy returns correct order."""
        hierarchy = get_role_hierarchy()

        assert hierarchy == ["owner", "admin", "operator", "viewer"]
        assert hierarchy[0] == "owner"  # Highest
        assert hierarchy[-1] == "viewer"  # Lowest

    def test_is_higher_role_true(self):
        """Test is_higher_role returns True for higher privilege."""
        assert is_higher_role("owner", "admin") is True
        assert is_higher_role("owner", "viewer") is True
        assert is_higher_role("admin", "operator") is True
        assert is_higher_role("operator", "viewer") is True

    def test_is_higher_role_false_equal(self):
        """Test is_higher_role returns False for equal roles."""
        assert is_higher_role("admin", "admin") is False
        assert is_higher_role("viewer", "viewer") is False

    def test_is_higher_role_false_lower(self):
        """Test is_higher_role returns False for lower privilege."""
        assert is_higher_role("viewer", "owner") is False
        assert is_higher_role("operator", "admin") is False

    def test_is_higher_role_invalid_role(self):
        """Test is_higher_role with invalid role returns False."""
        assert is_higher_role("invalid", "viewer") is False
        assert is_higher_role("owner", "invalid") is False


class TestCanManageRole:
    """Tests for can_manage_role function."""

    def test_owner_can_manage_all(self):
        """Test that owner can manage all roles."""
        assert can_manage_role("owner", "admin") is True
        assert can_manage_role("owner", "operator") is True
        assert can_manage_role("owner", "viewer") is True
        # Owner can even manage owner (for transfer)
        assert can_manage_role("owner", "owner") is True

    def test_admin_can_manage_lower_roles(self):
        """Test that admin can manage operator and viewer."""
        assert can_manage_role("admin", "operator") is True
        assert can_manage_role("admin", "viewer") is True

    def test_admin_cannot_manage_equal_or_higher(self):
        """Test that admin cannot manage admin or owner."""
        assert can_manage_role("admin", "admin") is False
        assert can_manage_role("admin", "owner") is False

    def test_operator_cannot_manage(self):
        """Test that operator cannot manage any role."""
        assert can_manage_role("operator", "viewer") is False
        assert can_manage_role("operator", "operator") is False

    def test_viewer_cannot_manage(self):
        """Test that viewer cannot manage any role."""
        assert can_manage_role("viewer", "viewer") is False


class TestGetAssignableRoles:
    """Tests for get_assignable_roles function."""

    def test_owner_can_assign_all_except_owner(self):
        """Test owner can assign admin, operator, viewer."""
        roles = get_assignable_roles("owner")

        assert "admin" in roles
        assert "operator" in roles
        assert "viewer" in roles
        assert "owner" not in roles  # Can't create another owner

    def test_admin_can_assign_lower_roles(self):
        """Test admin can assign operator and viewer."""
        roles = get_assignable_roles("admin")

        assert "operator" in roles
        assert "viewer" in roles
        assert "admin" not in roles
        assert "owner" not in roles

    def test_operator_cannot_assign(self):
        """Test operator cannot assign any role."""
        roles = get_assignable_roles("operator")
        assert roles == []

    def test_viewer_cannot_assign(self):
        """Test viewer cannot assign any role."""
        roles = get_assignable_roles("viewer")
        assert roles == []


class TestValidateRole:
    """Tests for validate_role function."""

    def test_validate_valid_roles(self):
        """Test validation of valid roles."""
        assert validate_role("owner") is True
        assert validate_role("admin") is True
        assert validate_role("operator") is True
        assert validate_role("viewer") is True

    def test_validate_invalid_roles(self):
        """Test validation of invalid roles."""
        assert validate_role("superadmin") is False
        assert validate_role("") is False
        assert validate_role("OWNER") is False  # Case sensitive


class TestPermissionGroups:
    """Tests for permission groups."""

    def test_config_admin_group(self):
        """Test config_admin permission group."""
        group = PERMISSION_GROUPS["config_admin"]

        assert Permission.VIEW_CONFIGS in group
        assert Permission.EDIT_CONFIGS in group
        assert Permission.DELETE_CONFIGS in group

    def test_sync_operator_group(self):
        """Test sync_operator permission group."""
        group = PERMISSION_GROUPS["sync_operator"]

        assert Permission.RUN_SYNC in group
        assert Permission.VIEW_HISTORY in group

    def test_user_admin_group(self):
        """Test user_admin permission group."""
        group = PERMISSION_GROUPS["user_admin"]

        assert Permission.VIEW_USERS in group
        assert Permission.MANAGE_USERS in group


class TestHasPermissionGroup:
    """Tests for has_permission_group function."""

    def _create_user(self, role: str) -> User:
        return User(
            id=1,
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
            role=role,
            password_hash="hash",
        )

    def test_admin_has_full_admin_group(self):
        """Test that admin has full_admin permission group."""
        user = self._create_user("admin")

        assert has_permission_group(user, "full_admin") is True

    def test_viewer_lacks_config_admin_group(self):
        """Test that viewer lacks config_admin group."""
        user = self._create_user("viewer")

        assert has_permission_group(user, "config_admin") is False

    def test_unknown_group_returns_false(self):
        """Test that unknown group returns False."""
        user = self._create_user("owner")

        assert has_permission_group(user, "nonexistent_group") is False
