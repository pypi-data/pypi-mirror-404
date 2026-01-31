"""Base repository class with common CRUD patterns and tenant isolation.

This module provides:
- ``TenantContext``: A context-variable holding the current organization_id.
  Set at request boundaries (API/Web middleware) to enforce multi-tenant
  isolation at the ORM layer.
- ``BaseRepository``: Abstract base with session management and CRUD helpers.
- ``TenantAwareRepository``: Extends BaseRepository to auto-inject
  ``organization_id`` filters into every query, preventing cross-tenant
  data leaks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from contextvars import ContextVar, Token
from typing import Any, Generic, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Type variables for generic repository
T = TypeVar("T")  # Dataclass type
M = TypeVar("M")  # Model type


# ---------------------------------------------------------------------------
# Tenant context – set once per request, read by all repositories
# ---------------------------------------------------------------------------

_tenant_context: ContextVar[int | None] = ContextVar("tenant_org_id", default=None)


def set_tenant(organization_id: int) -> Token[int | None]:
    """Set the current tenant organization ID for this context.

    Must be called at the start of every request (API middleware, CLI command,
    etc.) so that tenant-aware repositories can enforce isolation.

    Args:
        organization_id: The organization ID to scope queries to.

    Returns:
        A contextvars Token that can be used to reset the value.

    Raises:
        ValueError: If organization_id is not a positive integer.
    """
    if not isinstance(organization_id, int) or organization_id < 1:
        raise ValueError(f"organization_id must be a positive integer, got {organization_id!r}")
    return _tenant_context.set(organization_id)


def get_tenant() -> int | None:
    """Get the current tenant organization ID, or None if not set."""
    return _tenant_context.get()


def require_tenant() -> int:
    """Get the current tenant organization ID, raising if not set.

    Returns:
        The current organization_id.

    Raises:
        RuntimeError: If no tenant context has been set for this request.
    """
    org_id = _tenant_context.get()
    if org_id is None:
        raise RuntimeError(
            "Tenant context not set. Call set_tenant() at the request boundary "
            "before accessing tenant-scoped repositories."
        )
    return org_id


def clear_tenant(token: Token[int | None] | None = None) -> None:
    """Clear the current tenant context.

    Args:
        token: Optional token from set_tenant() to reset to previous value.
    """
    if token is not None:
        _tenant_context.reset(token)
    else:
        _tenant_context.set(None)


class SessionManager:
    """Manages SQLAlchemy sessions with context manager support.

    Provides a consistent way to handle database sessions across
    all repositories, ensuring proper cleanup and error handling.
    """

    def __init__(self, db_path: str, echo: bool = False) -> None:
        """Initialize session manager.

        Args:
            db_path: Path to SQLite database file.
            echo: Whether to echo SQL statements (for debugging).
        """
        self._db_path = db_path
        self._engine: Engine = create_engine(f"sqlite:///{db_path}", echo=echo)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine."""
        return self._engine

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._db_path

    def get_session(self) -> Session:
        """Create a new database session.

        Returns:
            New SQLAlchemy Session instance.
        """
        return self._session_factory()

    def create_tables(self, base: Any) -> None:
        """Create all tables from the declarative base.

        Args:
            base: SQLAlchemy declarative base with model metadata.
        """
        base.metadata.create_all(self._engine)


class BaseRepository(ABC, Generic[T, M]):
    """Abstract base repository with common CRUD operations.

    Provides a template for repository implementations with
    consistent session management and error handling.

    Type Parameters:
        T: Dataclass type for business logic.
        M: SQLAlchemy model type for persistence.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._session_manager = SessionManager(db_path)
        self._initialize_tables()

    def _initialize_tables(self) -> None:
        """Initialize database tables.

        Override in subclass to call create_tables with appropriate base.
        """
        pass

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._session_manager.db_path

    def _get_session(self) -> Session:
        """Get a new database session.

        Returns:
            New SQLAlchemy Session instance.
        """
        return self._session_manager.get_session()

    @abstractmethod
    def _model_to_dataclass(self, model: M) -> T:
        """Convert model to dataclass.

        Args:
            model: SQLAlchemy model instance.

        Returns:
            Dataclass instance.
        """
        pass

    @abstractmethod
    def _dataclass_to_model(self, entity: T) -> M:
        """Convert dataclass to model.

        Args:
            entity: Dataclass instance.

        Returns:
            SQLAlchemy model instance.
        """
        pass

    def _execute_in_session(
        self,
        operation: Callable[[Session], Any],
        commit: bool = True,
    ) -> Any:
        """Execute an operation within a session context.

        Handles session lifecycle, commits/rollbacks, and cleanup.

        Args:
            operation: Callable that takes a session and returns a result.
            commit: Whether to commit on success.

        Returns:
            Result of the operation.

        Raises:
            Exception: Re-raises any exception after rollback.
        """
        session = self._get_session()
        try:
            result = operation(session)
            if commit:
                session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _get_by_id_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> T | None:
        """Generic get by ID implementation.

        Args:
            model_class: SQLAlchemy model class.
            entity_id: Entity ID to find.
            filters: Optional additional filters as column: value dict.

        Returns:
            Dataclass instance if found, None otherwise.
        """

        def operation(session: Session) -> T | None:
            query = session.query(model_class).filter(model_class.id == entity_id)  # type: ignore[attr-defined]
            if filters:
                for column, value in filters.items():
                    query = query.filter(getattr(model_class, column) == value)
            model = query.first()
            return self._model_to_dataclass(model) if model else None

        return self._execute_in_session(operation, commit=False)  # type: ignore[no-any-return]

    def _delete_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> bool:
        """Generic delete implementation.

        Args:
            model_class: SQLAlchemy model class.
            entity_id: Entity ID to delete.
            filters: Optional additional filters.

        Returns:
            True if deleted, False if not found.
        """

        def operation(session: Session) -> bool:
            query = session.query(model_class).filter(model_class.id == entity_id)  # type: ignore[attr-defined]
            if filters:
                for column, value in filters.items():
                    query = query.filter(getattr(model_class, column) == value)
            model = query.first()
            if not model:
                return False
            session.delete(model)
            return True

        return self._execute_in_session(operation, commit=True)  # type: ignore[no-any-return]

    def _deactivate_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> bool:
        """Generic soft-delete (deactivate) implementation.

        Args:
            model_class: SQLAlchemy model class (must have is_active column).
            entity_id: Entity ID to deactivate.
            filters: Optional additional filters.

        Returns:
            True if deactivated, False if not found.
        """

        def operation(session: Session) -> bool:
            query = session.query(model_class).filter(model_class.id == entity_id)  # type: ignore[attr-defined]
            if filters:
                for column, value in filters.items():
                    query = query.filter(getattr(model_class, column) == value)
            model = query.first()
            if not model:
                return False
            model.is_active = False  # type: ignore[attr-defined]
            return True

        return self._execute_in_session(operation, commit=True)  # type: ignore[no-any-return]

    def _activate_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> bool:
        """Generic activate implementation.

        Args:
            model_class: SQLAlchemy model class (must have is_active column).
            entity_id: Entity ID to activate.
            filters: Optional additional filters.

        Returns:
            True if activated, False if not found.
        """

        def operation(session: Session) -> bool:
            query = session.query(model_class).filter(model_class.id == entity_id)  # type: ignore[attr-defined]
            if filters:
                for column, value in filters.items():
                    query = query.filter(getattr(model_class, column) == value)
            model = query.first()
            if not model:
                return False
            model.is_active = True  # type: ignore[attr-defined]
            return True

        return self._execute_in_session(operation, commit=True)  # type: ignore[no-any-return]

    def _count_impl(
        self,
        model_class: type[M],
        filters: dict[str, Any] | None = None,
        include_inactive: bool = False,
    ) -> int:
        """Generic count implementation.

        Args:
            model_class: SQLAlchemy model class.
            filters: Optional filters as column: value dict.
            include_inactive: Whether to include inactive entities.

        Returns:
            Count of matching entities.
        """

        def operation(session: Session) -> int:
            query = session.query(model_class)
            if filters:
                for column, value in filters.items():
                    query = query.filter(getattr(model_class, column) == value)
            if not include_inactive and hasattr(model_class, "is_active"):
                query = query.filter(model_class.is_active == True)  # type: ignore[attr-defined]
            return query.count()

        return self._execute_in_session(operation, commit=False)  # type: ignore[no-any-return]

    def _get_all_impl(
        self,
        model_class: type[M],
        filters: dict[str, Any] | None = None,
        include_inactive: bool = False,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[T]:
        """Generic get all implementation.

        Args:
            model_class: SQLAlchemy model class.
            filters: Optional filters as column: value dict.
            include_inactive: Whether to include inactive entities.
            order_by: SQLAlchemy column to order by.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of dataclass instances.
        """

        def operation(session: Session) -> list[T]:
            query = session.query(model_class)

            if filters:
                for column, value in filters.items():
                    query = query.filter(getattr(model_class, column) == value)

            if not include_inactive and hasattr(model_class, "is_active"):
                query = query.filter(model_class.is_active == True)  # type: ignore[attr-defined]

            if order_by is not None:
                query = query.order_by(order_by)

            if offset > 0:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            return [self._model_to_dataclass(m) for m in query.all()]

        return self._execute_in_session(operation, commit=False)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Tenant-aware repository base
# ---------------------------------------------------------------------------


class TenantAwareRepository(BaseRepository[T, M]):
    """Repository that auto-applies organization_id filtering to all queries.

    Uses the ``TenantContext`` context-variable to scope every query to the
    current organization.  If an explicit ``organization_id`` is passed to
    the constructor it takes precedence over the context-variable; otherwise
    the context-variable is read lazily on first access (fail-closed).

    Subclasses must set ``_tenant_column`` to the name of the SQLAlchemy
    column that stores the organization_id on their model (default:
    ``"organization_id"``).

    Example::

        class UserRepository(TenantAwareRepository[User, UserModel]):
            ...

        # At request boundary:
        set_tenant(org_id)

        # In handler:
        repo = UserRepository(db_path)
        users = repo.get_all()  # automatically filtered by org_id
    """

    _tenant_column: str = "organization_id"

    def __init__(
        self,
        db_path: str,
        organization_id: int | None = None,
    ) -> None:
        """Initialize tenant-aware repository.

        Args:
            db_path: Path to SQLite database file.
            organization_id: Explicit org_id override. If None, the value
                is read from ``TenantContext`` at query time (fail-closed).
        """
        self._explicit_org_id = organization_id
        super().__init__(db_path)

    @property
    def organization_id(self) -> int:
        """Return the effective organization_id (explicit or from context).

        Raises:
            RuntimeError: If neither an explicit org_id nor a context var
                is available.
        """
        if self._explicit_org_id is not None:
            return self._explicit_org_id
        return require_tenant()

    def _tenant_filters(self) -> dict[str, Any]:
        """Return the tenant filter dict to merge into queries."""
        return {self._tenant_column: self.organization_id}

    # ------------------------------------------------------------------
    # Override _impl helpers to auto-inject tenant filter
    # ------------------------------------------------------------------

    def _get_by_id_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> T | None:
        merged = {**self._tenant_filters(), **(filters or {})}
        return super()._get_by_id_impl(model_class, entity_id, filters=merged)

    def _delete_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> bool:
        merged = {**self._tenant_filters(), **(filters or {})}
        return super()._delete_impl(model_class, entity_id, filters=merged)

    def _deactivate_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> bool:
        merged = {**self._tenant_filters(), **(filters or {})}
        return super()._deactivate_impl(model_class, entity_id, filters=merged)

    def _activate_impl(
        self,
        model_class: type[M],
        entity_id: int,
        filters: dict[str, Any] | None = None,
    ) -> bool:
        merged = {**self._tenant_filters(), **(filters or {})}
        return super()._activate_impl(model_class, entity_id, filters=merged)

    def _count_impl(
        self,
        model_class: type[M],
        filters: dict[str, Any] | None = None,
        include_inactive: bool = False,
    ) -> int:
        merged = {**self._tenant_filters(), **(filters or {})}
        return super()._count_impl(
            model_class,
            filters=merged,
            include_inactive=include_inactive,
        )

    def _get_all_impl(
        self,
        model_class: type[M],
        filters: dict[str, Any] | None = None,
        include_inactive: bool = False,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[T]:
        merged = {**self._tenant_filters(), **(filters or {})}
        return super()._get_all_impl(
            model_class,
            filters=merged,
            include_inactive=include_inactive,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )


# ---------------------------------------------------------------------------
# Tenant validation for standalone repositories (not using BaseRepository)
# ---------------------------------------------------------------------------


def validate_tenant(organization_id: int | None) -> int | None:
    """Validate that the given organization_id matches the tenant context.

    For repositories that manage their own sessions (not inheriting from
    BaseRepository), call this at the start of any public method that
    receives an ``organization_id`` parameter. It ensures:

    1. If both a tenant context and an org_id are present, they must match.
    2. If org_id is None but a tenant context is set, returns the context
       value (auto-fill from context).
    3. If org_id is provided, it must be a valid positive integer.

    Args:
        organization_id: The organization_id to validate. May be None for
            methods where the parameter is optional.

    Returns:
        The validated organization_id, or the context org_id if the
        parameter was None.

    Raises:
        ValueError: If organization_id is provided but not a positive integer.
        PermissionError: If organization_id does not match the tenant context.
    """
    ctx_org = get_tenant()

    if organization_id is None:
        # No explicit org_id — return context value (may be None)
        return ctx_org

    if not isinstance(organization_id, int) or organization_id < 1:
        raise ValueError(f"organization_id must be a positive integer, got {organization_id!r}")

    if ctx_org is not None and ctx_org != organization_id:
        raise PermissionError(
            f"Tenant isolation violation: request scoped to org {ctx_org}, "
            f"but operation targets org {organization_id}"
        )
    return organization_id
