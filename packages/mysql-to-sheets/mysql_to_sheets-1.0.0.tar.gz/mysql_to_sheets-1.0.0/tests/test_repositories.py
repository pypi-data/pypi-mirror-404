"""Tests for model repositories (Organization, User)."""

import tempfile
from pathlib import Path

import pytest

from mysql_to_sheets.models.organizations import Organization, OrganizationRepository
from mysql_to_sheets.models.users import VALID_ROLES, User, UserRepository


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_repos.db"


class TestOrganizationRepository:
    """Tests for OrganizationRepository CRUD operations."""

    @pytest.fixture
    def repo(self, temp_db):
        """Create organization repository with temp database."""
        return OrganizationRepository(str(temp_db))

    def test_create_organization(self, repo):
        """Test creating a new organization."""
        org = Organization(name="Test Org", slug="test-org")

        created = repo.create(org)

        assert created.id is not None
        assert created.name == "Test Org"
        assert created.slug == "test-org"
        assert created.is_active is True
        assert created.created_at is not None
        assert created.subscription_tier == "free"

    def test_create_organization_with_settings(self, repo):
        """Test creating organization with custom settings."""
        org = Organization(
            name="Custom Org",
            slug="custom-org",
            settings={"feature_flags": {"beta": True}},
            subscription_tier="pro",
            max_users=50,
            max_configs=100,
        )

        created = repo.create(org)

        assert created.settings == {"feature_flags": {"beta": True}}
        assert created.subscription_tier == "pro"
        assert created.max_users == 50
        assert created.max_configs == 100

    def test_create_duplicate_slug_fails(self, repo):
        """Test creating org with duplicate slug raises error."""
        repo.create(Organization(name="First Org", slug="unique-slug"))

        with pytest.raises(ValueError) as exc_info:
            repo.create(Organization(name="Second Org", slug="unique-slug"))

        assert "already exists" in str(exc_info.value)

    def test_get_by_id_found(self, repo):
        """Test getting organization by ID."""
        created = repo.create(Organization(name="Test", slug="test-by-id"))

        found = repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.name == "Test"

    def test_get_by_id_not_found(self, repo):
        """Test getting non-existent organization."""
        found = repo.get_by_id(99999)

        assert found is None

    def test_get_by_slug_found(self, repo):
        """Test getting organization by slug."""
        repo.create(Organization(name="Slug Test", slug="slug-test-org"))

        found = repo.get_by_slug("slug-test-org")

        assert found is not None
        assert found.slug == "slug-test-org"

    def test_get_by_slug_not_found(self, repo):
        """Test getting non-existent organization by slug."""
        found = repo.get_by_slug("nonexistent-slug")

        assert found is None

    def test_get_all_organizations(self, repo):
        """Test listing all organizations."""
        repo.create(Organization(name="Org 1", slug="org-1"))
        repo.create(Organization(name="Org 2", slug="org-2"))
        repo.create(Organization(name="Org 3", slug="org-3"))

        orgs = repo.get_all()

        assert len(orgs) == 3

    def test_get_all_excludes_inactive_by_default(self, repo):
        """Test get_all excludes inactive orgs by default."""
        org1 = repo.create(Organization(name="Active", slug="active-org"))
        org2 = repo.create(Organization(name="Inactive", slug="inactive-org"))
        repo.deactivate(org2.id)

        orgs = repo.get_all(include_inactive=False)

        assert len(orgs) == 1
        assert orgs[0].id == org1.id

    def test_get_all_includes_inactive_when_requested(self, repo):
        """Test get_all can include inactive orgs."""
        repo.create(Organization(name="Active", slug="active-org-2"))
        org2 = repo.create(Organization(name="Inactive", slug="inactive-org-2"))
        repo.deactivate(org2.id)

        orgs = repo.get_all(include_inactive=True)

        assert len(orgs) == 2

    def test_get_all_with_pagination(self, repo):
        """Test get_all with limit and offset."""
        for i in range(5):
            repo.create(Organization(name=f"Org {i}", slug=f"org-{i}"))

        page1 = repo.get_all(limit=2, offset=0)
        page2 = repo.get_all(limit=2, offset=2)
        page3 = repo.get_all(limit=2, offset=4)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

    def test_update_organization(self, repo):
        """Test updating an organization."""
        created = repo.create(Organization(name="Original", slug="original-org"))
        created.name = "Updated"
        created.subscription_tier = "enterprise"

        updated = repo.update(created)

        assert updated.name == "Updated"
        assert updated.subscription_tier == "enterprise"

    def test_update_organization_without_id_fails(self, repo):
        """Test updating org without ID raises error."""
        org = Organization(name="No ID", slug="no-id-org")

        with pytest.raises(ValueError) as exc_info:
            repo.update(org)

        assert "ID is required" in str(exc_info.value)

    def test_update_organization_not_found(self, repo):
        """Test updating non-existent org raises error."""
        org = Organization(name="Missing", slug="missing-org")
        org.id = 99999

        with pytest.raises(ValueError) as exc_info:
            repo.update(org)

        assert "not found" in str(exc_info.value)

    def test_update_slug_conflict(self, repo):
        """Test updating to conflicting slug raises error."""
        repo.create(Organization(name="First", slug="first-slug"))
        second = repo.create(Organization(name="Second", slug="second-slug"))
        second.slug = "first-slug"

        with pytest.raises(ValueError) as exc_info:
            repo.update(second)

        assert "already exists" in str(exc_info.value)

    def test_delete_organization(self, repo):
        """Test deleting an organization."""
        created = repo.create(Organization(name="To Delete", slug="to-delete"))

        result = repo.delete(created.id)

        assert result is True
        assert repo.get_by_id(created.id) is None

    def test_delete_organization_not_found(self, repo):
        """Test deleting non-existent org returns False."""
        result = repo.delete(99999)

        assert result is False

    def test_deactivate_organization(self, repo):
        """Test deactivating an organization (soft delete)."""
        created = repo.create(Organization(name="To Deactivate", slug="to-deactivate"))

        result = repo.deactivate(created.id)

        assert result is True
        org = repo.get_by_id(created.id)
        assert org.is_active is False

    def test_deactivate_organization_not_found(self, repo):
        """Test deactivating non-existent org returns False."""
        result = repo.deactivate(99999)

        assert result is False

    def test_count_organizations(self, repo):
        """Test counting organizations."""
        repo.create(Organization(name="Org 1", slug="count-org-1"))
        repo.create(Organization(name="Org 2", slug="count-org-2"))

        count = repo.count()

        assert count == 2

    def test_count_excludes_inactive_by_default(self, repo):
        """Test count excludes inactive by default."""
        repo.create(Organization(name="Active", slug="count-active"))
        inactive = repo.create(Organization(name="Inactive", slug="count-inactive"))
        repo.deactivate(inactive.id)

        count = repo.count(include_inactive=False)
        count_all = repo.count(include_inactive=True)

        assert count == 1
        assert count_all == 2

    def test_organization_to_dict(self, repo):
        """Test Organization.to_dict() method."""
        org = Organization(
            name="Dict Test",
            slug="dict-test",
            settings={"key": "value"},
        )
        created = repo.create(org)

        d = created.to_dict()

        assert d["id"] == created.id
        assert d["name"] == "Dict Test"
        assert d["slug"] == "dict-test"
        assert d["settings"] == {"key": "value"}
        assert d["is_active"] is True

    def test_organization_from_dict(self):
        """Test Organization.from_dict() class method."""
        data = {
            "id": 1,
            "name": "From Dict",
            "slug": "from-dict",
            "is_active": False,
            "subscription_tier": "pro",
        }

        org = Organization.from_dict(data)

        assert org.id == 1
        assert org.name == "From Dict"
        assert org.is_active is False


class TestUserRepository:
    """Tests for UserRepository CRUD operations."""

    @pytest.fixture
    def org_repo(self, temp_db):
        """Create organization repository."""
        return OrganizationRepository(str(temp_db))

    @pytest.fixture
    def user_repo(self, temp_db):
        """Create user repository."""
        return UserRepository(str(temp_db))

    @pytest.fixture
    def test_org(self, org_repo):
        """Create a test organization."""
        return org_repo.create(Organization(name="User Test Org", slug="user-test-org"))

    @pytest.fixture
    def test_org2(self, org_repo):
        """Create a second test organization."""
        return org_repo.create(Organization(name="User Test Org 2", slug="user-test-org-2"))

    def test_create_user(self, user_repo, test_org):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            display_name="Test User",
            password_hash="hash123",
            role="admin",
            organization_id=test_org.id,
        )

        created = user_repo.create(user)

        assert created.id is not None
        assert created.email == "test@example.com"
        assert created.display_name == "Test User"
        assert created.role == "admin"
        assert created.is_active is True
        assert created.created_at is not None
        assert created.organization_id == test_org.id

    def test_create_user_invalid_role(self, user_repo, test_org):
        """Test creating user with invalid role fails."""
        user = User(
            email="invalid@example.com",
            display_name="Invalid Role",
            password_hash="hash",
            role="superadmin",  # Invalid role
            organization_id=test_org.id,
        )

        with pytest.raises(ValueError) as exc_info:
            user_repo.create(user)

        assert "Invalid role" in str(exc_info.value)

    def test_create_duplicate_email_in_org_fails(self, user_repo, test_org):
        """Test creating user with duplicate email in same org fails."""
        user_repo.create(
            User(
                email="dup@example.com",
                display_name="First",
                password_hash="hash1",
                organization_id=test_org.id,
            )
        )

        with pytest.raises(ValueError) as exc_info:
            user_repo.create(
                User(
                    email="dup@example.com",
                    display_name="Second",
                    password_hash="hash2",
                    organization_id=test_org.id,
                )
            )

        assert "already exists" in str(exc_info.value)

    def test_same_email_different_orgs_allowed(self, user_repo, test_org, test_org2):
        """Test same email can exist in different organizations."""
        user1 = user_repo.create(
            User(
                email="shared@example.com",
                display_name="User Org1",
                password_hash="hash1",
                organization_id=test_org.id,
            )
        )
        user2 = user_repo.create(
            User(
                email="shared@example.com",
                display_name="User Org2",
                password_hash="hash2",
                organization_id=test_org2.id,
            )
        )

        assert user1.id != user2.id
        assert user1.email == user2.email

    def test_get_by_id_found(self, user_repo, test_org):
        """Test getting user by ID."""
        created = user_repo.create(
            User(
                email="byid@example.com",
                display_name="By ID",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        found = user_repo.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    def test_get_by_id_with_org_filter(self, user_repo, test_org, test_org2):
        """Test getting user by ID with organization filter."""
        user = user_repo.create(
            User(
                email="filtered@example.com",
                display_name="Filtered",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        # Can find in correct org
        found = user_repo.get_by_id(user.id, organization_id=test_org.id)
        assert found is not None

        # Cannot find in wrong org (multi-tenant isolation)
        not_found = user_repo.get_by_id(user.id, organization_id=test_org2.id)
        assert not_found is None

    def test_get_by_id_not_found(self, user_repo):
        """Test getting non-existent user."""
        found = user_repo.get_by_id(99999)

        assert found is None

    def test_get_by_email(self, user_repo, test_org):
        """Test getting user by email within organization."""
        user_repo.create(
            User(
                email="byemail@example.com",
                display_name="By Email",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        found = user_repo.get_by_email("byemail@example.com", test_org.id)

        assert found is not None
        assert found.email == "byemail@example.com"

    def test_get_by_email_not_found(self, user_repo, test_org):
        """Test getting non-existent user by email."""
        found = user_repo.get_by_email("nonexistent@example.com", test_org.id)

        assert found is None

    def test_get_by_email_any_org(self, user_repo, test_org, test_org2):
        """Test getting users by email across all orgs."""
        user_repo.create(
            User(
                email="multi@example.com",
                display_name="Multi Org1",
                password_hash="hash1",
                organization_id=test_org.id,
            )
        )
        user_repo.create(
            User(
                email="multi@example.com",
                display_name="Multi Org2",
                password_hash="hash2",
                organization_id=test_org2.id,
            )
        )

        users = user_repo.get_by_email_any_org("multi@example.com")

        assert len(users) == 2

    def test_get_all_users_in_org(self, user_repo, test_org):
        """Test listing all users in an organization."""
        user_repo.create(
            User(
                email="user1@example.com",
                display_name="User 1",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        user_repo.create(
            User(
                email="user2@example.com",
                display_name="User 2",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        users = user_repo.get_all(test_org.id)

        assert len(users) == 2

    def test_get_all_excludes_inactive_by_default(self, user_repo, test_org):
        """Test get_all excludes inactive users by default."""
        user1 = user_repo.create(
            User(
                email="active@example.com",
                display_name="Active",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        user2 = user_repo.create(
            User(
                email="inactive@example.com",
                display_name="Inactive",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        user_repo.deactivate(user2.id)

        users = user_repo.get_all(test_org.id, include_inactive=False)

        assert len(users) == 1
        assert users[0].id == user1.id

    def test_update_user(self, user_repo, test_org):
        """Test updating a user."""
        created = user_repo.create(
            User(
                email="update@example.com",
                display_name="Original",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        created.display_name = "Updated"
        created.role = "admin"

        updated = user_repo.update(created)

        assert updated.display_name == "Updated"
        assert updated.role == "admin"

    def test_update_user_without_id_fails(self, user_repo, test_org):
        """Test updating user without ID raises error."""
        user = User(
            email="noid@example.com",
            display_name="No ID",
            password_hash="hash",
            organization_id=test_org.id,
        )

        with pytest.raises(ValueError) as exc_info:
            user_repo.update(user)

        assert "ID is required" in str(exc_info.value)

    def test_update_user_email_conflict(self, user_repo, test_org):
        """Test updating to conflicting email raises error."""
        user_repo.create(
            User(
                email="first@example.com",
                display_name="First",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        second = user_repo.create(
            User(
                email="second@example.com",
                display_name="Second",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        second.email = "first@example.com"

        with pytest.raises(ValueError) as exc_info:
            user_repo.update(second)

        assert "already exists" in str(exc_info.value)

    def test_update_last_login(self, user_repo, test_org):
        """Test updating user's last login timestamp."""
        user = user_repo.create(
            User(
                email="login@example.com",
                display_name="Login Test",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        assert user.last_login_at is None

        result = user_repo.update_last_login(user.id)

        assert result is True
        updated = user_repo.get_by_id(user.id)
        assert updated.last_login_at is not None

    def test_update_last_login_not_found(self, user_repo):
        """Test update_last_login for non-existent user."""
        result = user_repo.update_last_login(99999)

        assert result is False

    def test_update_password(self, user_repo, test_org):
        """Test updating user's password hash."""
        user = user_repo.create(
            User(
                email="password@example.com",
                display_name="Password Test",
                password_hash="old_hash",
                organization_id=test_org.id,
            )
        )

        result = user_repo.update_password(user.id, "new_hash")

        assert result is True
        updated = user_repo.get_by_id(user.id)
        assert updated.password_hash == "new_hash"

    def test_delete_user(self, user_repo, test_org):
        """Test deleting a user."""
        user = user_repo.create(
            User(
                email="delete@example.com",
                display_name="To Delete",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        result = user_repo.delete(user.id)

        assert result is True
        assert user_repo.get_by_id(user.id) is None

    def test_delete_user_with_org_filter(self, user_repo, test_org, test_org2):
        """Test deleting user with organization filter (multi-tenant isolation)."""
        user = user_repo.create(
            User(
                email="delete2@example.com",
                display_name="Org Filtered Delete",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        # Cannot delete from wrong org
        result_wrong_org = user_repo.delete(user.id, organization_id=test_org2.id)
        assert result_wrong_org is False
        assert user_repo.get_by_id(user.id) is not None

        # Can delete from correct org
        result_correct_org = user_repo.delete(user.id, organization_id=test_org.id)
        assert result_correct_org is True
        assert user_repo.get_by_id(user.id) is None

    def test_deactivate_user(self, user_repo, test_org):
        """Test deactivating a user (soft delete)."""
        user = user_repo.create(
            User(
                email="deactivate@example.com",
                display_name="To Deactivate",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        result = user_repo.deactivate(user.id)

        assert result is True
        updated = user_repo.get_by_id(user.id)
        assert updated.is_active is False

    def test_count_users(self, user_repo, test_org):
        """Test counting users in organization."""
        user_repo.create(
            User(
                email="count1@example.com",
                display_name="Count 1",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )
        user_repo.create(
            User(
                email="count2@example.com",
                display_name="Count 2",
                password_hash="hash",
                organization_id=test_org.id,
            )
        )

        count = user_repo.count(test_org.id)

        assert count == 2

    def test_get_owner(self, user_repo, test_org):
        """Test getting organization owner."""
        user_repo.create(
            User(
                email="admin@example.com",
                display_name="Admin",
                password_hash="hash",
                role="admin",
                organization_id=test_org.id,
            )
        )
        owner = user_repo.create(
            User(
                email="owner@example.com",
                display_name="Owner",
                password_hash="hash",
                role="owner",
                organization_id=test_org.id,
            )
        )

        found_owner = user_repo.get_owner(test_org.id)

        assert found_owner is not None
        assert found_owner.id == owner.id
        assert found_owner.role == "owner"

    def test_transfer_ownership(self, user_repo, test_org):
        """Test transferring organization ownership."""
        owner = user_repo.create(
            User(
                email="old_owner@example.com",
                display_name="Old Owner",
                password_hash="hash",
                role="owner",
                organization_id=test_org.id,
            )
        )
        admin = user_repo.create(
            User(
                email="new_owner@example.com",
                display_name="New Owner",
                password_hash="hash",
                role="admin",
                organization_id=test_org.id,
            )
        )

        result = user_repo.transfer_ownership(test_org.id, owner.id, admin.id)

        assert result is True

        # Verify roles changed
        old_owner = user_repo.get_by_id(owner.id)
        new_owner = user_repo.get_by_id(admin.id)
        assert old_owner.role == "admin"
        assert new_owner.role == "owner"

    def test_user_to_dict(self, user_repo, test_org):
        """Test User.to_dict() method."""
        user = user_repo.create(
            User(
                email="dict@example.com",
                display_name="Dict Test",
                password_hash="secret_hash",
                role="viewer",
                organization_id=test_org.id,
            )
        )

        d = user.to_dict()

        assert d["email"] == "dict@example.com"
        assert d["display_name"] == "Dict Test"
        assert d["role"] == "viewer"
        assert "password_hash" not in d  # Should NOT include password by default

        # Test with password hash included
        d_with_pass = user.to_dict(include_password_hash=True)
        assert d_with_pass["password_hash"] == "secret_hash"

    def test_user_from_dict(self):
        """Test User.from_dict() class method."""
        data = {
            "id": 1,
            "email": "fromdict@example.com",
            "display_name": "From Dict",
            "password_hash": "hash123",
            "role": "admin",
            "is_active": True,
            "organization_id": 5,
        }

        user = User.from_dict(data)

        assert user.id == 1
        assert user.email == "fromdict@example.com"
        assert user.role == "admin"
        assert user.organization_id == 5

    def test_valid_roles_constant(self):
        """Test VALID_ROLES contains expected roles."""
        assert "owner" in VALID_ROLES
        assert "admin" in VALID_ROLES
        assert "operator" in VALID_ROLES
        assert "viewer" in VALID_ROLES
        assert len(VALID_ROLES) == 4


class TestMultiTenantIsolation:
    """Tests for multi-tenant data isolation."""

    @pytest.fixture
    def setup_repos(self, temp_db):
        """Set up repositories and test orgs."""
        org_repo = OrganizationRepository(str(temp_db))
        user_repo = UserRepository(str(temp_db))

        org1 = org_repo.create(Organization(name="Org 1", slug="org-1"))
        org2 = org_repo.create(Organization(name="Org 2", slug="org-2"))

        return {
            "org_repo": org_repo,
            "user_repo": user_repo,
            "org1": org1,
            "org2": org2,
        }

    def test_user_in_org1_not_visible_to_org2(self, setup_repos):
        """Test user created in org1 is not visible to org2 queries."""
        user_repo = setup_repos["user_repo"]
        org1 = setup_repos["org1"]
        org2 = setup_repos["org2"]

        # Create user in org1
        user = user_repo.create(
            User(
                email="org1user@example.com",
                display_name="Org1 User",
                password_hash="hash",
                organization_id=org1.id,
            )
        )

        # User visible in org1
        org1_users = user_repo.get_all(org1.id)
        assert len(org1_users) == 1
        assert org1_users[0].id == user.id

        # User NOT visible in org2
        org2_users = user_repo.get_all(org2.id)
        assert len(org2_users) == 0

    def test_user_count_scoped_to_org(self, setup_repos):
        """Test user count is scoped to organization."""
        user_repo = setup_repos["user_repo"]
        org1 = setup_repos["org1"]
        org2 = setup_repos["org2"]

        # Create 3 users in org1, 1 in org2
        for i in range(3):
            user_repo.create(
                User(
                    email=f"org1user{i}@example.com",
                    display_name=f"Org1 User {i}",
                    password_hash="hash",
                    organization_id=org1.id,
                )
            )
        user_repo.create(
            User(
                email="org2user@example.com",
                display_name="Org2 User",
                password_hash="hash",
                organization_id=org2.id,
            )
        )

        assert user_repo.count(org1.id) == 3
        assert user_repo.count(org2.id) == 1

    def test_email_lookup_scoped_to_org(self, setup_repos):
        """Test email lookup is scoped to organization."""
        user_repo = setup_repos["user_repo"]
        org1 = setup_repos["org1"]
        org2 = setup_repos["org2"]

        # Same email in both orgs
        user_repo.create(
            User(
                email="shared@example.com",
                display_name="Org1 Version",
                password_hash="hash1",
                organization_id=org1.id,
            )
        )
        user_repo.create(
            User(
                email="shared@example.com",
                display_name="Org2 Version",
                password_hash="hash2",
                organization_id=org2.id,
            )
        )

        # Lookup in org1 returns org1's user
        org1_user = user_repo.get_by_email("shared@example.com", org1.id)
        assert org1_user.display_name == "Org1 Version"

        # Lookup in org2 returns org2's user
        org2_user = user_repo.get_by_email("shared@example.com", org2.id)
        assert org2_user.display_name == "Org2 Version"

    def test_delete_user_respects_org_boundary(self, setup_repos):
        """Test delete operation respects organization boundary."""
        user_repo = setup_repos["user_repo"]
        org1 = setup_repos["org1"]
        org2 = setup_repos["org2"]

        user = user_repo.create(
            User(
                email="protect@example.com",
                display_name="Protected",
                password_hash="hash",
                organization_id=org1.id,
            )
        )

        # Attempt to delete from wrong org should fail
        deleted = user_repo.delete(user.id, organization_id=org2.id)
        assert deleted is False

        # User should still exist
        assert user_repo.get_by_id(user.id) is not None

    def test_deactivate_user_respects_org_boundary(self, setup_repos):
        """Test deactivate operation respects organization boundary."""
        user_repo = setup_repos["user_repo"]
        org1 = setup_repos["org1"]
        org2 = setup_repos["org2"]

        user = user_repo.create(
            User(
                email="deact@example.com",
                display_name="To Deactivate",
                password_hash="hash",
                organization_id=org1.id,
            )
        )

        # Attempt to deactivate from wrong org should fail
        deactivated = user_repo.deactivate(user.id, organization_id=org2.id)
        assert deactivated is False

        # User should still be active
        assert user_repo.get_by_id(user.id).is_active is True
