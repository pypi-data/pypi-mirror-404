"""Tests for tenant isolation system.

This module tests the TenantContext system and TenantAwareRepository to ensure
proper multi-tenant isolation and prevent cross-tenant data access.
"""

import threading
import time
from dataclasses import dataclass

import pytest
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base

from mysql_to_sheets.models.repository import (
    TenantAwareRepository,
    clear_tenant,
    get_tenant,
    require_tenant,
    set_tenant,
    validate_tenant,
)

# Test model for TenantAwareRepository tests
Base = declarative_base()


class _EntityModel(Base):
    """Minimal SQLAlchemy model for testing tenant-aware repository."""

    __tablename__ = "test_entities"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


@dataclass
class _Entity:
    """Dataclass for _EntityModel."""

    id: int | None
    organization_id: int
    name: str
    is_active: bool = True


class _TenantRepository(TenantAwareRepository[_Entity, _EntityModel]):
    """Concrete implementation of TenantAwareRepository for testing."""

    def _initialize_tables(self) -> None:
        """Create test tables."""
        self._session_manager.create_tables(Base)

    def _model_to_dataclass(self, model: _EntityModel) -> _Entity:
        """Convert model to dataclass."""
        return _Entity(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            is_active=model.is_active,
        )

    def _dataclass_to_model(self, entity: _Entity) -> _EntityModel:
        """Convert dataclass to model."""
        model = _EntityModel(
            organization_id=entity.organization_id,
            name=entity.name,
            is_active=entity.is_active,
        )
        if entity.id is not None:
            model.id = entity.id
        return model

    def create(self, entity: _Entity) -> _Entity:
        """Create a new entity."""

        def operation(session):
            # Auto-inject organization_id from context if not set
            if entity.organization_id is None:
                entity.organization_id = self.organization_id
            model = self._dataclass_to_model(entity)
            session.add(model)
            session.flush()
            return self._model_to_dataclass(model)

        return self._execute_in_session(operation, commit=True)

    def get_by_id(self, entity_id: int) -> _Entity | None:
        """Get entity by ID."""
        return self._get_by_id_impl(_EntityModel, entity_id)

    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID."""
        return self._delete_impl(_EntityModel, entity_id)

    def get_all(self) -> list[_Entity]:
        """Get all entities."""
        return self._get_all_impl(_EntityModel)

    def count(self) -> int:
        """Count entities."""
        return self._count_impl(_EntityModel)


class TestTenantContextBasics:
    """Tests for TenantContext basic functionality."""

    def setup_method(self):
        """Reset tenant context before each test."""
        clear_tenant()

    def teardown_method(self):
        """Reset tenant context after each test."""
        clear_tenant()

    def test_set_tenant_with_valid_org_id_returns_token(self):
        """Test set_tenant with valid org_id returns a token."""
        token = set_tenant(1)
        assert token is not None
        assert get_tenant() == 1

    def test_set_tenant_with_zero_raises_value_error(self):
        """Test set_tenant with org_id=0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            set_tenant(0)
        assert "positive integer" in str(exc_info.value)

    def test_set_tenant_with_negative_raises_value_error(self):
        """Test set_tenant with negative org_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            set_tenant(-1)
        assert "positive integer" in str(exc_info.value)

    def test_set_tenant_with_none_raises_value_error(self):
        """Test set_tenant with None raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            set_tenant(None)  # type: ignore
        assert "positive integer" in str(exc_info.value)

    def test_set_tenant_with_string_raises_value_error(self):
        """Test set_tenant with string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            set_tenant("1")  # type: ignore
        assert "positive integer" in str(exc_info.value)

    def test_get_tenant_returns_none_when_not_set(self):
        """Test get_tenant returns None when not set."""
        assert get_tenant() is None

    def test_get_tenant_returns_org_id_after_set_tenant(self):
        """Test get_tenant returns org_id after set_tenant."""
        set_tenant(42)
        assert get_tenant() == 42

    def test_require_tenant_raises_runtime_error_when_not_set(self):
        """Test require_tenant raises RuntimeError when not set."""
        with pytest.raises(RuntimeError) as exc_info:
            require_tenant()
        assert "Tenant context not set" in str(exc_info.value)

    def test_require_tenant_returns_org_id_when_set(self):
        """Test require_tenant returns org_id when set."""
        set_tenant(7)
        assert require_tenant() == 7

    def test_clear_tenant_resets_to_none(self):
        """Test clear_tenant resets to None."""
        set_tenant(10)
        assert get_tenant() == 10
        clear_tenant()
        assert get_tenant() is None

    def test_clear_tenant_with_token_resets_to_previous_value(self):
        """Test clear_tenant with token resets to previous value."""
        # Set initial tenant
        set_tenant(1)
        assert get_tenant() == 1

        # Set new tenant and get token
        token = set_tenant(2)
        assert get_tenant() == 2

        # Reset using token
        clear_tenant(token)
        assert get_tenant() == 1

    def test_multiple_set_tenant_calls_preserve_history(self):
        """Test multiple set_tenant calls preserve history with tokens."""
        token1 = set_tenant(1)
        assert get_tenant() == 1

        token2 = set_tenant(2)
        assert get_tenant() == 2

        token3 = set_tenant(3)
        assert get_tenant() == 3

        # Reset in reverse order
        clear_tenant(token3)
        assert get_tenant() == 2

        clear_tenant(token2)
        assert get_tenant() == 1

        clear_tenant(token1)
        assert get_tenant() is None


class TestValidateTenant:
    """Tests for validate_tenant function."""

    def setup_method(self):
        """Reset tenant context before each test."""
        clear_tenant()

    def teardown_method(self):
        """Reset tenant context after each test."""
        clear_tenant()

    def test_validate_tenant_with_matching_context_passes(self):
        """Test validate_tenant passes when org_id matches context."""
        set_tenant(1)
        result = validate_tenant(1)
        assert result == 1

    def test_validate_tenant_with_no_context_set_passes(self):
        """Test validate_tenant passes when no context set (no restriction)."""
        # No tenant context set
        assert get_tenant() is None
        result = validate_tenant(1)
        assert result == 1

    def test_validate_tenant_with_mismatched_context_raises_permission_error(self):
        """Test validate_tenant raises PermissionError on mismatch."""
        set_tenant(1)
        with pytest.raises(PermissionError) as exc_info:
            validate_tenant(2)
        assert "Tenant isolation violation" in str(exc_info.value)
        assert "org 1" in str(exc_info.value)
        assert "org 2" in str(exc_info.value)

    def test_validate_tenant_with_zero_raises_value_error(self):
        """Test validate_tenant with org_id=0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_tenant(0)
        assert "positive integer" in str(exc_info.value)

    def test_validate_tenant_with_negative_raises_value_error(self):
        """Test validate_tenant with negative org_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_tenant(-1)
        assert "positive integer" in str(exc_info.value)

    def test_validate_tenant_with_none_returns_context_or_none(self):
        """Test validate_tenant with None returns context value or None."""
        # No context set — returns None
        assert validate_tenant(None) is None

        # With context set — returns context value
        token = set_tenant(42)
        try:
            assert validate_tenant(None) == 42
        finally:
            clear_tenant(token)

    def test_validate_tenant_with_string_raises_value_error(self):
        """Test validate_tenant with string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_tenant("1")  # type: ignore
        assert "positive integer" in str(exc_info.value)


class TestCrossTenantPrevention:
    """Tests to ensure cross-tenant data access is prevented."""

    def setup_method(self):
        """Reset tenant context before each test."""
        clear_tenant()

    def teardown_method(self):
        """Reset tenant context after each test."""
        clear_tenant()

    def test_validate_tenant_prevents_org_1_accessing_org_2(self):
        """Test that validate_tenant prevents org 1 from accessing org 2 data."""
        set_tenant(1)

        # Should pass for org 1
        validate_tenant(1)

        # Should fail for org 2
        with pytest.raises(PermissionError) as exc_info:
            validate_tenant(2)
        assert "org 1" in str(exc_info.value)
        assert "org 2" in str(exc_info.value)

    def test_validate_tenant_prevents_org_2_accessing_org_1(self):
        """Test that validate_tenant prevents org 2 from accessing org 1 data."""
        set_tenant(2)

        # Should pass for org 2
        validate_tenant(2)

        # Should fail for org 1
        with pytest.raises(PermissionError) as exc_info:
            validate_tenant(1)
        assert "org 2" in str(exc_info.value)
        assert "org 1" in str(exc_info.value)

    def test_changing_tenant_context_changes_allowed_access(self):
        """Test that changing tenant context changes allowed access."""
        # Start with org 1
        set_tenant(1)
        validate_tenant(1)

        with pytest.raises(PermissionError):
            validate_tenant(2)

        # Switch to org 2
        set_tenant(2)
        validate_tenant(2)

        with pytest.raises(PermissionError):
            validate_tenant(1)


class TestThreadContextSafety:
    """Tests for thread safety and context isolation."""

    def setup_method(self):
        """Reset tenant context before each test."""
        clear_tenant()

    def teardown_method(self):
        """Reset tenant context after each test."""
        clear_tenant()

    def test_tenant_context_isolated_between_threads(self):
        """Test that tenant context is isolated between threads."""
        results = {}
        errors = []

        def thread_func(org_id: int, thread_id: int):
            """Set tenant and verify isolation."""
            try:
                set_tenant(org_id)
                # Sleep to ensure threads overlap
                time.sleep(0.01)
                result = get_tenant()
                results[thread_id] = result
            except Exception as e:
                errors.append(e)

        # Create threads with different org IDs
        threads = []
        for i in range(5):
            org_id = i + 1
            thread = threading.Thread(target=thread_func, args=(org_id, i))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify each thread saw its own org_id
        assert len(results) == 5
        for i in range(5):
            expected_org_id = i + 1
            assert results[i] == expected_org_id

    def test_context_vars_work_with_concurrent_access(self):
        """Test that context vars work correctly with concurrent access."""
        success_count = {"count": 0}
        lock = threading.Lock()
        errors = []

        def worker(org_id: int):
            """Worker that sets and validates tenant multiple times."""
            try:
                for _ in range(10):
                    set_tenant(org_id)
                    time.sleep(0.001)  # Small delay to encourage interleaving
                    current = get_tenant()
                    if current != org_id:
                        errors.append(f"Expected org_id {org_id}, got {current}")
                        return
                with lock:
                    success_count["count"] += 1
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            org_id = (i % 3) + 1  # Use org_ids 1, 2, 3
            thread = threading.Thread(target=worker, args=(org_id,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify all succeeded
        assert len(errors) == 0, f"Errors: {errors}"
        assert success_count["count"] == 10


class TestTenantAwareRepository:
    """Tests for TenantAwareRepository."""

    def setup_method(self):
        """Reset tenant context and create test database."""
        clear_tenant()
        # Use a file-based database instead of :memory: to share across instances
        import tempfile

        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name

    def teardown_method(self):
        """Reset tenant context and clean up database."""
        clear_tenant()
        import os

        if hasattr(self, "db_path") and os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_tenant_filters_returns_correct_dict(self):
        """Test that _tenant_filters returns correct dict."""
        set_tenant(42)
        repo = _TenantRepository(self.db_path)
        filters = repo._tenant_filters()
        assert filters == {"organization_id": 42}

    def test_organization_id_property_uses_explicit_value(self):
        """Test that organization_id property uses explicit value when provided."""
        set_tenant(10)
        repo = _TenantRepository(self.db_path, organization_id=20)
        # Should use explicit value, not context
        assert repo.organization_id == 20

    def test_organization_id_property_falls_back_to_context(self):
        """Test that organization_id property falls back to context var."""
        set_tenant(15)
        repo = _TenantRepository(self.db_path)
        assert repo.organization_id == 15

    def test_organization_id_property_raises_when_neither_available(self):
        """Test that organization_id raises RuntimeError when neither available."""
        # No explicit value, no context
        repo = _TenantRepository(self.db_path)
        with pytest.raises(RuntimeError) as exc_info:
            _ = repo.organization_id
        assert "Tenant context not set" in str(exc_info.value)

    def test_create_and_get_respects_tenant_context(self):
        """Test that create and get operations respect tenant context."""
        # Create entities for org 1
        set_tenant(1)
        repo = _TenantRepository(self.db_path)
        entity1 = _Entity(id=None, organization_id=1, name="Entity 1")
        created1 = repo.create(entity1)
        assert created1.id is not None

        # Create entities for org 2
        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        entity2 = _Entity(id=None, organization_id=2, name="Entity 2")
        created2 = repo2.create(entity2)
        assert created2.id is not None

        # Verify org 1 can only see its entities
        set_tenant(1)
        repo = _TenantRepository(self.db_path)
        found = repo.get_by_id(created1.id)
        assert found is not None
        assert found.name == "Entity 1"

        # Org 1 should not see org 2's entity
        not_found = repo.get_by_id(created2.id)
        assert not_found is None

    def test_get_all_respects_tenant_context(self):
        """Test that get_all respects tenant context."""
        # Create entities for different orgs
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        repo1.create(_Entity(id=None, organization_id=1, name="Org1-A"))
        repo1.create(_Entity(id=None, organization_id=1, name="Org1-B"))

        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        repo2.create(_Entity(id=None, organization_id=2, name="Org2-A"))

        # Verify org 1 only sees 2 entities
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        entities = repo1.get_all()
        assert len(entities) == 2
        assert all(e.organization_id == 1 for e in entities)

        # Verify org 2 only sees 1 entity
        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        entities = repo2.get_all()
        assert len(entities) == 1
        assert all(e.organization_id == 2 for e in entities)

    def test_count_respects_tenant_context(self):
        """Test that count respects tenant context."""
        # Create entities for different orgs
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        repo1.create(_Entity(id=None, organization_id=1, name="E1"))
        repo1.create(_Entity(id=None, organization_id=1, name="E2"))
        repo1.create(_Entity(id=None, organization_id=1, name="E3"))

        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        repo2.create(_Entity(id=None, organization_id=2, name="E4"))

        # Verify counts
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        assert repo1.count() == 3

        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        assert repo2.count() == 1

    def test_delete_respects_tenant_context(self):
        """Test that delete respects tenant context."""
        # Create entities for different orgs
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        e1 = repo1.create(_Entity(id=None, organization_id=1, name="E1"))

        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        e2 = repo2.create(_Entity(id=None, organization_id=2, name="E2"))

        # Org 1 should not be able to delete org 2's entity
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        deleted = repo1.delete(e2.id)
        assert deleted is False

        # Org 2 should still have its entity
        set_tenant(2)
        repo2 = _TenantRepository(self.db_path)
        assert repo2.get_by_id(e2.id) is not None

        # Org 1 can delete its own entity
        set_tenant(1)
        repo1 = _TenantRepository(self.db_path)
        deleted = repo1.delete(e1.id)
        assert deleted is True

    def test_explicit_organization_id_overrides_context(self):
        """Test that explicit organization_id overrides context."""
        # Set context to org 1
        set_tenant(1)

        # Create entities for org 2 using explicit org_id
        repo = _TenantRepository(self.db_path, organization_id=2)
        e = repo.create(_Entity(id=None, organization_id=2, name="E1"))
        assert e.organization_id == 2

        # Repository should only see org 2 entities despite context
        entities = repo.get_all()
        assert len(entities) == 1
        assert entities[0].organization_id == 2

    def test_multiple_repos_with_different_contexts(self):
        """Test multiple repositories with different tenant contexts."""
        # Create repo for org 1 with explicit ID
        repo1 = _TenantRepository(self.db_path, organization_id=1)
        repo1.create(_Entity(id=None, organization_id=1, name="Org1"))

        # Create repo for org 2 with explicit ID
        repo2 = _TenantRepository(self.db_path, organization_id=2)
        repo2.create(_Entity(id=None, organization_id=2, name="Org2"))

        # Each repo should only see its own entities
        assert repo1.count() == 1
        assert repo2.count() == 1

        entities1 = repo1.get_all()
        assert entities1[0].name == "Org1"

        entities2 = repo2.get_all()
        assert entities2[0].name == "Org2"
