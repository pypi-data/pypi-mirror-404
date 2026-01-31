"""Tests for the users module."""

import os
import tempfile
from datetime import datetime, timezone

import pytest

from mysql_to_sheets.models.organizations import (
    Organization,
    OrganizationRepository,
    reset_organization_repository,
)
from mysql_to_sheets.models.users import (
    VALID_ROLES,
    User,
    UserModel,
    UserRepository,
    get_user_repository,
    reset_user_repository,
)


class TestUser:
    """Tests for User dataclass."""

    def test_create_user(self):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            display_name="Test User",
            organization_id=1,
        )

        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.organization_id == 1
        assert user.id is None
        assert user.role == "viewer"
        assert user.is_active is True
        assert user.password_hash == ""

    def test_create_user_with_role(self):
        """Test creating a user with specific role."""
        user = User(
            email="admin@example.com",
            display_name="Admin User",
            organization_id=1,
            role="admin",
            password_hash="hashed_password",
        )

        assert user.role == "admin"
        assert user.password_hash == "hashed_password"

    def test_valid_roles(self):
        """Test that VALID_ROLES contains expected roles."""
        assert "owner" in VALID_ROLES
        assert "admin" in VALID_ROLES
        assert "operator" in VALID_ROLES
        assert "viewer" in VALID_ROLES
        assert len(VALID_ROLES) == 4

    def test_to_dict(self):
        """Test converting user to dictionary."""
        user = User(
            id=1,
            email="user@example.com",
            display_name="Test User",
            organization_id=1,
            role="operator",
            is_active=True,
        )

        d = user.to_dict()

        assert d["id"] == 1
        assert d["email"] == "user@example.com"
        assert d["display_name"] == "Test User"
        assert d["role"] == "operator"
        assert d["organization_id"] == 1
        assert "password_hash" not in d  # Should not include by default

    def test_to_dict_with_password_hash(self):
        """Test to_dict includes password hash when requested."""
        user = User(
            email="user@example.com",
            display_name="Test User",
            organization_id=1,
            password_hash="secret_hash",
        )

        d = user.to_dict(include_password_hash=True)
        assert d["password_hash"] == "secret_hash"

    def test_to_dict_with_timestamps(self):
        """Test to_dict with timestamps."""
        now = datetime.now(timezone.utc)
        user = User(
            email="user@example.com",
            display_name="Test User",
            organization_id=1,
            created_at=now,
            last_login_at=now,
        )

        d = user.to_dict()
        assert d["created_at"] == now.isoformat()
        assert d["last_login_at"] == now.isoformat()

    def test_from_dict(self):
        """Test creating user from dictionary."""
        data = {
            "id": 1,
            "email": "from_dict@example.com",
            "display_name": "From Dict User",
            "organization_id": 1,
            "role": "admin",
            "is_active": True,
        }

        user = User.from_dict(data)

        assert user.id == 1
        assert user.email == "from_dict@example.com"
        assert user.role == "admin"
        assert user.organization_id == 1

    def test_from_dict_with_iso_timestamp(self):
        """Test from_dict with ISO timestamp strings."""
        data = {
            "email": "test@example.com",
            "display_name": "Test",
            "organization_id": 1,
            "created_at": "2024-01-15T10:30:00+00:00",
            "last_login_at": "2024-01-16T08:00:00Z",
        }

        user = User.from_dict(data)
        assert user.created_at is not None
        assert user.last_login_at is not None


class TestUserModel:
    """Tests for UserModel SQLAlchemy model."""

    def test_from_dataclass(self):
        """Test creating model from dataclass."""
        user = User(
            email="model@example.com",
            display_name="Model User",
            organization_id=1,
            role="operator",
            password_hash="hashed",
        )

        model = UserModel.from_dataclass(user)

        assert model.email == "model@example.com"
        assert model.display_name == "Model User"
        assert model.role == "operator"
        assert model.password_hash == "hashed"

    def test_to_dataclass(self):
        """Test converting model to dataclass."""
        model = UserModel(
            id=1,
            email="model@example.com",
            display_name="Model User",
            password_hash="hashed",
            role="admin",
            organization_id=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

        user = model.to_dataclass()

        assert isinstance(user, User)
        assert user.id == 1
        assert user.email == "model@example.com"
        assert user.role == "admin"

    def test_repr(self):
        """Test string representation."""
        model = UserModel(
            id=1,
            email="test@example.com",
            role="viewer",
            is_active=True,
        )

        repr_str = repr(model)
        assert "id=1" in repr_str
        assert "test@example.com" in repr_str
        assert "viewer" in repr_str


class TestUserRepository:
    """Tests for UserRepository."""

    def setup_method(self):
        """Reset singletons before each test."""
        reset_user_repository()
        reset_organization_repository()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_user_repository()
        reset_organization_repository()

    def _create_org(self, db_path: str, slug: str = "test-org") -> Organization:
        """Helper to create a test organization."""
        org_repo = OrganizationRepository(db_path)
        return org_repo.create(Organization(name="Test Org", slug=slug))

    def test_create_user(self):
        """Test creating a user through repository."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = User(
                email="new@example.com",
                display_name="New User",
                organization_id=org.id,
                password_hash="hashed",
            )

            created = repo.create(user)

            assert created.id is not None
            assert created.email == "new@example.com"
            assert created.created_at is not None
        finally:
            os.unlink(db_path)

    def test_create_duplicate_email_in_org_raises_error(self):
        """Test that duplicate emails in same org raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user1 = User(
                email="same@example.com",
                display_name="User 1",
                organization_id=org.id,
                password_hash="hash1",
            )
            repo.create(user1)

            user2 = User(
                email="same@example.com",
                display_name="User 2",
                organization_id=org.id,
                password_hash="hash2",
            )

            with pytest.raises(ValueError) as exc_info:
                repo.create(user2)

            assert "already exists" in str(exc_info.value)
        finally:
            os.unlink(db_path)

    def test_same_email_different_orgs_allowed(self):
        """Test that same email can exist in different organizations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org1 = self._create_org(db_path, "org-1")
            org2 = self._create_org(db_path, "org-2")
            repo = UserRepository(db_path)

            user1 = User(
                email="same@example.com",
                display_name="User 1",
                organization_id=org1.id,
                password_hash="hash1",
            )
            user2 = User(
                email="same@example.com",
                display_name="User 2",
                organization_id=org2.id,
                password_hash="hash2",
            )

            created1 = repo.create(user1)
            created2 = repo.create(user2)

            assert created1.id != created2.id
            assert created1.organization_id != created2.organization_id
        finally:
            os.unlink(db_path)

    def test_create_invalid_role_raises_error(self):
        """Test that invalid role raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = User(
                email="user@example.com",
                display_name="User",
                organization_id=org.id,
                role="invalid_role",
                password_hash="hash",
            )

            with pytest.raises(ValueError) as exc_info:
                repo.create(user)

            assert "Invalid role" in str(exc_info.value)
        finally:
            os.unlink(db_path)

    def test_get_by_id(self):
        """Test getting user by ID."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="test@example.com",
                    display_name="Test User",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            found = repo.get_by_id(user.id)

            assert found is not None
            assert found.id == user.id
            assert found.email == "test@example.com"
        finally:
            os.unlink(db_path)

    def test_get_by_id_with_org_filter(self):
        """Test get_by_id with organization filter."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org1 = self._create_org(db_path, "org-1")
            org2 = self._create_org(db_path, "org-2")
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="test@example.com",
                    display_name="Test User",
                    organization_id=org1.id,
                    password_hash="hash",
                )
            )

            # Should find with correct org
            found = repo.get_by_id(user.id, organization_id=org1.id)
            assert found is not None

            # Should not find with different org
            not_found = repo.get_by_id(user.id, organization_id=org2.id)
            assert not_found is None
        finally:
            os.unlink(db_path)

    def test_get_by_email(self):
        """Test getting user by email within organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            repo.create(
                User(
                    email="find@example.com",
                    display_name="Find User",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            found = repo.get_by_email("find@example.com", org.id)

            assert found is not None
            assert found.email == "find@example.com"
        finally:
            os.unlink(db_path)

    def test_get_by_email_global(self):
        """Test getting first user by email across organizations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            repo.create(
                User(
                    email="global@example.com",
                    display_name="Global User",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            found = repo.get_by_email_global("global@example.com")

            assert found is not None
            assert found.email == "global@example.com"
        finally:
            os.unlink(db_path)

    def test_get_by_email_any_org(self):
        """Test getting users by email across all organizations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org1 = self._create_org(db_path, "org-1")
            org2 = self._create_org(db_path, "org-2")
            repo = UserRepository(db_path)

            repo.create(
                User(
                    email="multi@example.com",
                    display_name="User 1",
                    organization_id=org1.id,
                    password_hash="hash1",
                )
            )
            repo.create(
                User(
                    email="multi@example.com",
                    display_name="User 2",
                    organization_id=org2.id,
                    password_hash="hash2",
                )
            )

            users = repo.get_by_email_any_org("multi@example.com")

            assert len(users) == 2
        finally:
            os.unlink(db_path)

    def test_get_all(self):
        """Test getting all users in an organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            for i in range(3):
                repo.create(
                    User(
                        email=f"user{i}@example.com",
                        display_name=f"User {i}",
                        organization_id=org.id,
                        password_hash="hash",
                    )
                )

            users = repo.get_all(org.id)
            assert len(users) == 3
        finally:
            os.unlink(db_path)

    def test_update_user(self):
        """Test updating a user."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="original@example.com",
                    display_name="Original",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            user.display_name = "Updated"
            user.role = "operator"
            updated = repo.update(user)

            assert updated.display_name == "Updated"
            assert updated.role == "operator"
        finally:
            os.unlink(db_path)

    def test_update_last_login(self):
        """Test updating user's last login timestamp."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="login@example.com",
                    display_name="Login User",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            assert user.last_login_at is None

            updated = repo.update_last_login(user.id)
            assert updated is True

            found = repo.get_by_id(user.id)
            assert found.last_login_at is not None
        finally:
            os.unlink(db_path)

    def test_update_password(self):
        """Test updating user's password hash."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="password@example.com",
                    display_name="Password User",
                    organization_id=org.id,
                    password_hash="old_hash",
                )
            )

            updated = repo.update_password(user.id, "new_hash")
            assert updated is True

            found = repo.get_by_id(user.id)
            assert found.password_hash == "new_hash"
        finally:
            os.unlink(db_path)

    def test_deactivate_user(self):
        """Test soft-deleting a user."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="deactivate@example.com",
                    display_name="Deactivate User",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            deactivated = repo.deactivate(user.id)
            assert deactivated is True

            found = repo.get_by_id(user.id)
            assert found.is_active is False
        finally:
            os.unlink(db_path)

    def test_delete_user(self):
        """Test deleting a user."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            user = repo.create(
                User(
                    email="delete@example.com",
                    display_name="Delete User",
                    organization_id=org.id,
                    password_hash="hash",
                )
            )

            deleted = repo.delete(user.id)
            assert deleted is True
            assert repo.get_by_id(user.id) is None
        finally:
            os.unlink(db_path)

    def test_get_owner(self):
        """Test getting the owner of an organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            repo.create(
                User(
                    email="owner@example.com",
                    display_name="Owner",
                    organization_id=org.id,
                    role="owner",
                    password_hash="hash",
                )
            )
            repo.create(
                User(
                    email="admin@example.com",
                    display_name="Admin",
                    organization_id=org.id,
                    role="admin",
                    password_hash="hash",
                )
            )

            owner = repo.get_owner(org.id)
            assert owner is not None
            assert owner.role == "owner"
            assert owner.email == "owner@example.com"
        finally:
            os.unlink(db_path)

    def test_transfer_ownership(self):
        """Test transferring ownership to another user."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            owner = repo.create(
                User(
                    email="owner@example.com",
                    display_name="Owner",
                    organization_id=org.id,
                    role="owner",
                    password_hash="hash",
                )
            )
            admin = repo.create(
                User(
                    email="admin@example.com",
                    display_name="Admin",
                    organization_id=org.id,
                    role="admin",
                    password_hash="hash",
                )
            )

            transferred = repo.transfer_ownership(org.id, owner.id, admin.id)
            assert transferred is True

            # Check roles were swapped
            new_admin = repo.get_by_id(owner.id)
            new_owner = repo.get_by_id(admin.id)

            assert new_admin.role == "admin"
            assert new_owner.role == "owner"
        finally:
            os.unlink(db_path)

    def test_count(self):
        """Test counting users in organization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            org = self._create_org(db_path)
            repo = UserRepository(db_path)

            for i in range(3):
                repo.create(
                    User(
                        email=f"user{i}@example.com",
                        display_name=f"User {i}",
                        organization_id=org.id,
                        password_hash="hash",
                    )
                )

            count = repo.count(org.id)
            assert count == 3
        finally:
            os.unlink(db_path)


class TestUserSingleton:
    """Tests for the user repository singleton."""

    def setup_method(self):
        """Reset singletons before each test."""
        reset_user_repository()
        reset_organization_repository()

    def teardown_method(self):
        """Cleanup after each test."""
        reset_user_repository()
        reset_organization_repository()

    def test_get_user_repository_requires_path(self):
        """Test that first call requires db_path."""
        with pytest.raises(ValueError) as exc_info:
            get_user_repository()

        assert "db_path is required" in str(exc_info.value)

    def test_reset_user_repository(self):
        """Test resetting the singleton."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            get_user_repository(db_path)
            reset_user_repository()

            with pytest.raises(ValueError):
                get_user_repository()
        finally:
            os.unlink(db_path)
