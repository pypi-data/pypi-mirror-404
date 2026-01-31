"""Tests for the favorites module."""

import os
import tempfile

import pytest

from mysql_to_sheets.models.favorites import (
    FavoriteQuery,
    FavoriteQueryRepository,
    FavoriteSheet,
    FavoriteSheetRepository,
    get_favorite_query_repository,
    get_favorite_sheet_repository,
    reset_favorite_query_repository,
    reset_favorite_sheet_repository,
)


class TestFavoriteQuery:
    """Tests for FavoriteQuery dataclass."""

    def test_create_favorite_query(self):
        """Test creating a favorite query."""
        fav = FavoriteQuery(
            name="Daily Users",
            sql_query="SELECT * FROM users",
            organization_id=1,
        )

        assert fav.name == "Daily Users"
        assert fav.sql_query == "SELECT * FROM users"
        assert fav.organization_id == 1
        assert fav.id is None
        assert fav.description == ""
        assert fav.tags == []
        assert fav.use_count == 0
        assert fav.is_private is False
        assert fav.is_active is True

    def test_create_favorite_query_with_options(self):
        """Test creating a favorite query with all options."""
        fav = FavoriteQuery(
            name="Private Query",
            sql_query="SELECT * FROM orders",
            organization_id=1,
            description="Get all orders",
            tags=["orders", "daily"],
            is_private=True,
            created_by_user_id=5,
        )

        assert fav.description == "Get all orders"
        assert fav.tags == ["orders", "daily"]
        assert fav.is_private is True
        assert fav.created_by_user_id == 5

    def test_to_dict(self):
        """Test converting favorite query to dictionary."""
        fav = FavoriteQuery(
            id=1,
            name="Test Query",
            sql_query="SELECT 1",
            organization_id=1,
            tags=["test"],
            use_count=5,
        )

        d = fav.to_dict()

        assert d["id"] == 1
        assert d["name"] == "Test Query"
        assert d["sql_query"] == "SELECT 1"
        assert d["organization_id"] == 1
        assert d["tags"] == ["test"]
        assert d["use_count"] == 5
        assert d["is_private"] is False

    def test_from_dict(self):
        """Test creating favorite query from dictionary."""
        data = {
            "id": 2,
            "name": "From Dict",
            "sql_query": "SELECT * FROM products",
            "organization_id": 3,
            "tags": ["products"],
            "is_private": True,
            "use_count": 10,
        }

        fav = FavoriteQuery.from_dict(data)

        assert fav.id == 2
        assert fav.name == "From Dict"
        assert fav.sql_query == "SELECT * FROM products"
        assert fav.is_private is True
        assert fav.use_count == 10

    def test_validate_valid_query(self):
        """Test validation of a valid query."""
        fav = FavoriteQuery(
            name="Valid",
            sql_query="SELECT 1",
            organization_id=1,
        )

        errors = fav.validate()
        assert errors == []

    def test_validate_missing_name(self):
        """Test validation with missing name."""
        fav = FavoriteQuery(
            name="",
            sql_query="SELECT 1",
            organization_id=1,
        )

        errors = fav.validate()
        assert "Name is required" in errors

    def test_validate_missing_query(self):
        """Test validation with missing query."""
        fav = FavoriteQuery(
            name="Test",
            sql_query="",
            organization_id=1,
        )

        errors = fav.validate()
        assert "SQL query is required" in errors


class TestFavoriteSheet:
    """Tests for FavoriteSheet dataclass."""

    def test_create_favorite_sheet(self):
        """Test creating a favorite sheet."""
        fav = FavoriteSheet(
            name="Sales Report",
            sheet_id="abc123def456",
            organization_id=1,
        )

        assert fav.name == "Sales Report"
        assert fav.sheet_id == "abc123def456"
        assert fav.organization_id == 1
        assert fav.default_worksheet == "Sheet1"
        assert fav.use_count == 0
        assert fav.is_private is False

    def test_create_favorite_sheet_with_options(self):
        """Test creating a favorite sheet with all options."""
        fav = FavoriteSheet(
            name="Private Sheet",
            sheet_id="xyz789",
            organization_id=1,
            default_worksheet="Data",
            description="My private sales data",
            tags=["sales", "private"],
            is_private=True,
            created_by_user_id=3,
        )

        assert fav.default_worksheet == "Data"
        assert fav.description == "My private sales data"
        assert fav.tags == ["sales", "private"]
        assert fav.is_private is True
        assert fav.created_by_user_id == 3

    def test_to_dict(self):
        """Test converting favorite sheet to dictionary."""
        fav = FavoriteSheet(
            id=1,
            name="Test Sheet",
            sheet_id="test123",
            organization_id=1,
            default_worksheet="Results",
            use_count=3,
        )

        d = fav.to_dict()

        assert d["id"] == 1
        assert d["name"] == "Test Sheet"
        assert d["sheet_id"] == "test123"
        assert d["default_worksheet"] == "Results"
        assert d["use_count"] == 3

    def test_from_dict(self):
        """Test creating favorite sheet from dictionary."""
        data = {
            "id": 2,
            "name": "From Dict",
            "sheet_id": "dict123",
            "organization_id": 3,
            "default_worksheet": "Import",
            "tags": ["import"],
            "is_private": True,
        }

        fav = FavoriteSheet.from_dict(data)

        assert fav.id == 2
        assert fav.name == "From Dict"
        assert fav.sheet_id == "dict123"
        assert fav.default_worksheet == "Import"
        assert fav.is_private is True

    def test_validate_valid_sheet(self):
        """Test validation of a valid sheet."""
        fav = FavoriteSheet(
            name="Valid",
            sheet_id="abc123",
            organization_id=1,
        )

        errors = fav.validate()
        assert errors == []

    def test_validate_missing_name(self):
        """Test validation with missing name."""
        fav = FavoriteSheet(
            name="",
            sheet_id="abc123",
            organization_id=1,
        )

        errors = fav.validate()
        assert "Name is required" in errors

    def test_validate_missing_sheet_id(self):
        """Test validation with missing sheet_id."""
        fav = FavoriteSheet(
            name="Test",
            sheet_id="",
            organization_id=1,
        )

        errors = fav.validate()
        assert "Sheet ID is required" in errors


class TestFavoriteQueryRepository:
    """Tests for FavoriteQueryRepository."""

    @pytest.fixture
    def repo(self):
        """Create a test repository with a temporary database."""
        reset_favorite_query_repository()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        repo = FavoriteQueryRepository(db_path)
        yield repo

        # Cleanup
        reset_favorite_query_repository()
        try:
            os.unlink(db_path)
        except OSError:
            pass

    def test_create_and_get(self, repo):
        """Test creating and retrieving a favorite query."""
        fav = FavoriteQuery(
            name="Test Query",
            sql_query="SELECT * FROM test",
            organization_id=1,
        )

        created = repo.create(fav)
        assert created.id is not None

        retrieved = repo.get_by_id(created.id, organization_id=1)
        assert retrieved is not None
        assert retrieved.name == "Test Query"
        assert retrieved.sql_query == "SELECT * FROM test"

    def test_get_by_name(self, repo):
        """Test getting a favorite query by name."""
        fav = FavoriteQuery(
            name="Named Query",
            sql_query="SELECT 1",
            organization_id=1,
        )

        repo.create(fav)

        retrieved = repo.get_by_name("Named Query", organization_id=1)
        assert retrieved is not None
        assert retrieved.name == "Named Query"

    def test_get_all(self, repo):
        """Test getting all favorite queries."""
        for i in range(3):
            fav = FavoriteQuery(
                name=f"Query {i}",
                sql_query=f"SELECT {i}",
                organization_id=1,
            )
            repo.create(fav)

        all_queries = repo.get_all(organization_id=1)
        assert len(all_queries) == 3

    def test_update(self, repo):
        """Test updating a favorite query."""
        fav = FavoriteQuery(
            name="Original",
            sql_query="SELECT 1",
            organization_id=1,
        )

        created = repo.create(fav)

        created.name = "Updated"
        created.sql_query = "SELECT 2"
        updated = repo.update(created)

        assert updated.name == "Updated"
        assert updated.sql_query == "SELECT 2"

    def test_delete(self, repo):
        """Test deleting a favorite query."""
        fav = FavoriteQuery(
            name="To Delete",
            sql_query="SELECT 1",
            organization_id=1,
        )

        created = repo.create(fav)
        assert repo.delete(created.id, organization_id=1) is True

        retrieved = repo.get_by_id(created.id, organization_id=1)
        assert retrieved is None

    def test_deactivate(self, repo):
        """Test soft-deleting a favorite query."""
        fav = FavoriteQuery(
            name="To Deactivate",
            sql_query="SELECT 1",
            organization_id=1,
        )

        created = repo.create(fav)
        assert repo.deactivate(created.id, organization_id=1) is True

        # Should not be found without include_inactive
        retrieved = repo.get_by_id(created.id, organization_id=1)
        assert retrieved is None

    def test_increment_use_count(self, repo):
        """Test incrementing use count."""
        fav = FavoriteQuery(
            name="Counter",
            sql_query="SELECT 1",
            organization_id=1,
        )

        created = repo.create(fav)
        assert created.use_count == 0

        repo.increment_use_count(created.id, organization_id=1)
        repo.increment_use_count(created.id, organization_id=1)

        updated = repo.get_by_id(created.id, organization_id=1)
        assert updated.use_count == 2
        assert updated.last_used_at is not None

    def test_duplicate_name_raises_error(self, repo):
        """Test that duplicate names raise an error."""
        fav1 = FavoriteQuery(
            name="Duplicate",
            sql_query="SELECT 1",
            organization_id=1,
        )
        repo.create(fav1)

        fav2 = FavoriteQuery(
            name="Duplicate",
            sql_query="SELECT 2",
            organization_id=1,
        )

        with pytest.raises(ValueError) as exc_info:
            repo.create(fav2)

        assert "already exists" in str(exc_info.value)

    def test_private_visibility(self, repo):
        """Test that private queries are only visible to creator."""
        # Create a private query by user 1
        private = FavoriteQuery(
            name="Private",
            sql_query="SELECT 1",
            organization_id=1,
            is_private=True,
            created_by_user_id=1,
        )
        repo.create(private)

        # Create a shared query
        shared = FavoriteQuery(
            name="Shared",
            sql_query="SELECT 2",
            organization_id=1,
            is_private=False,
        )
        repo.create(shared)

        # User 1 should see both
        user1_queries = repo.get_all(organization_id=1, user_id=1)
        assert len(user1_queries) == 2

        # User 2 should only see shared
        user2_queries = repo.get_all(organization_id=1, user_id=2)
        assert len(user2_queries) == 1
        assert user2_queries[0].name == "Shared"


class TestFavoriteSheetRepository:
    """Tests for FavoriteSheetRepository."""

    @pytest.fixture
    def repo(self):
        """Create a test repository with a temporary database."""
        reset_favorite_sheet_repository()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        repo = FavoriteSheetRepository(db_path)
        yield repo

        # Cleanup
        reset_favorite_sheet_repository()
        try:
            os.unlink(db_path)
        except OSError:
            pass

    def test_create_and_get(self, repo):
        """Test creating and retrieving a favorite sheet."""
        fav = FavoriteSheet(
            name="Test Sheet",
            sheet_id="abc123",
            organization_id=1,
        )

        created = repo.create(fav)
        assert created.id is not None

        retrieved = repo.get_by_id(created.id, organization_id=1)
        assert retrieved is not None
        assert retrieved.name == "Test Sheet"
        assert retrieved.sheet_id == "abc123"

    def test_get_by_name(self, repo):
        """Test getting a favorite sheet by name."""
        fav = FavoriteSheet(
            name="Named Sheet",
            sheet_id="xyz789",
            organization_id=1,
        )

        repo.create(fav)

        retrieved = repo.get_by_name("Named Sheet", organization_id=1)
        assert retrieved is not None
        assert retrieved.name == "Named Sheet"

    def test_get_by_sheet_id(self, repo):
        """Test getting a favorite sheet by Google Sheet ID."""
        fav = FavoriteSheet(
            name="By Sheet ID",
            sheet_id="unique123",
            organization_id=1,
        )

        repo.create(fav)

        retrieved = repo.get_by_sheet_id("unique123", organization_id=1)
        assert retrieved is not None
        assert retrieved.name == "By Sheet ID"

    def test_get_all(self, repo):
        """Test getting all favorite sheets."""
        for i in range(3):
            fav = FavoriteSheet(
                name=f"Sheet {i}",
                sheet_id=f"sheet{i}",
                organization_id=1,
            )
            repo.create(fav)

        all_sheets = repo.get_all(organization_id=1)
        assert len(all_sheets) == 3

    def test_update(self, repo):
        """Test updating a favorite sheet."""
        fav = FavoriteSheet(
            name="Original",
            sheet_id="orig123",
            organization_id=1,
        )

        created = repo.create(fav)

        created.name = "Updated"
        created.default_worksheet = "Data"
        updated = repo.update(created)

        assert updated.name == "Updated"
        assert updated.default_worksheet == "Data"

    def test_delete(self, repo):
        """Test deleting a favorite sheet."""
        fav = FavoriteSheet(
            name="To Delete",
            sheet_id="del123",
            organization_id=1,
        )

        created = repo.create(fav)
        assert repo.delete(created.id, organization_id=1) is True

        retrieved = repo.get_by_id(created.id, organization_id=1)
        assert retrieved is None

    def test_deactivate(self, repo):
        """Test soft-deleting a favorite sheet."""
        fav = FavoriteSheet(
            name="To Deactivate",
            sheet_id="deact123",
            organization_id=1,
        )

        created = repo.create(fav)
        assert repo.deactivate(created.id, organization_id=1) is True

        # Should not be found without include_inactive
        retrieved = repo.get_by_id(created.id, organization_id=1)
        assert retrieved is None

    def test_increment_use_count(self, repo):
        """Test incrementing use count."""
        fav = FavoriteSheet(
            name="Counter",
            sheet_id="count123",
            organization_id=1,
        )

        created = repo.create(fav)
        assert created.use_count == 0

        repo.increment_use_count(created.id, organization_id=1)
        repo.increment_use_count(created.id, organization_id=1)

        updated = repo.get_by_id(created.id, organization_id=1)
        assert updated.use_count == 2
        assert updated.last_used_at is not None

    def test_update_verified(self, repo):
        """Test updating verification timestamp."""
        fav = FavoriteSheet(
            name="To Verify",
            sheet_id="verify123",
            organization_id=1,
        )

        created = repo.create(fav)
        assert created.last_verified_at is None

        repo.update_verified(created.id, organization_id=1)

        updated = repo.get_by_id(created.id, organization_id=1)
        assert updated.last_verified_at is not None

    def test_duplicate_name_raises_error(self, repo):
        """Test that duplicate names raise an error."""
        fav1 = FavoriteSheet(
            name="Duplicate",
            sheet_id="dup1",
            organization_id=1,
        )
        repo.create(fav1)

        fav2 = FavoriteSheet(
            name="Duplicate",
            sheet_id="dup2",
            organization_id=1,
        )

        with pytest.raises(ValueError) as exc_info:
            repo.create(fav2)

        assert "already exists" in str(exc_info.value)

    def test_private_visibility(self, repo):
        """Test that private sheets are only visible to creator."""
        # Create a private sheet by user 1
        private = FavoriteSheet(
            name="Private",
            sheet_id="priv123",
            organization_id=1,
            is_private=True,
            created_by_user_id=1,
        )
        repo.create(private)

        # Create a shared sheet
        shared = FavoriteSheet(
            name="Shared",
            sheet_id="share123",
            organization_id=1,
            is_private=False,
        )
        repo.create(shared)

        # User 1 should see both
        user1_sheets = repo.get_all(organization_id=1, user_id=1)
        assert len(user1_sheets) == 2

        # User 2 should only see shared
        user2_sheets = repo.get_all(organization_id=1, user_id=2)
        assert len(user2_sheets) == 1
        assert user2_sheets[0].name == "Shared"


class TestSingletonAccessors:
    """Tests for singleton accessor functions."""

    def test_get_favorite_query_repository_requires_path(self):
        """Test that first call requires db_path."""
        reset_favorite_query_repository()

        with pytest.raises(ValueError) as exc_info:
            get_favorite_query_repository()

        assert "db_path is required" in str(exc_info.value)

    def test_get_favorite_sheet_repository_requires_path(self):
        """Test that first call requires db_path."""
        reset_favorite_sheet_repository()

        with pytest.raises(ValueError) as exc_info:
            get_favorite_sheet_repository()

        assert "db_path is required" in str(exc_info.value)

    def test_singleton_returns_same_instance(self):
        """Test that singleton returns the same instance."""
        reset_favorite_query_repository()
        reset_favorite_sheet_repository()

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo1 = get_favorite_query_repository(db_path)
            repo2 = get_favorite_query_repository()

            assert repo1 is repo2

            sheet_repo1 = get_favorite_sheet_repository(db_path)
            sheet_repo2 = get_favorite_sheet_repository()

            assert sheet_repo1 is sheet_repo2
        finally:
            reset_favorite_query_repository()
            reset_favorite_sheet_repository()
            try:
                os.unlink(db_path)
            except OSError:
                pass
