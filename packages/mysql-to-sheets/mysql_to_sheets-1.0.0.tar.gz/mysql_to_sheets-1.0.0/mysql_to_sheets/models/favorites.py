"""SQLAlchemy models and repositories for favorite queries and sheets.

Favorites allow users to save and reuse SQL queries and Google Sheet IDs
with friendly names, supporting both shared and private visibility.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Query, Session

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    or_,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from mysql_to_sheets.models.repository import validate_tenant


class Base(DeclarativeBase):
    pass


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass
class FavoriteQuery:
    """A saved SQL query with metadata.

    Attributes:
        name: User-friendly name (unique per org+owner for private).
        sql_query: The SQL query string.
        organization_id: Organization scope for multi-tenant isolation.
        id: Primary key (auto-generated).
        description: Optional description of the query.
        tags: Optional list of tags for categorization.
        use_count: Number of times this query has been used.
        last_used_at: When the query was last used.
        created_by_user_id: User who created this favorite.
        is_private: If true, only visible to creator.
        is_active: Soft delete flag.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    name: str
    sql_query: str
    organization_id: int
    id: int | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)
    use_count: int = 0
    last_used_at: datetime | None = None
    created_by_user_id: int | None = None
    is_private: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the favorite query.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sql_query": self.sql_query,
            "tags": self.tags,
            "use_count": self.use_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "organization_id": self.organization_id,
            "created_by_user_id": self.created_by_user_id,
            "is_private": self.is_private,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FavoriteQuery":
        """Create FavoriteQuery from dictionary.

        Args:
            data: Dictionary with query data.

        Returns:
            FavoriteQuery instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        last_used_at = data.get("last_used_at")
        if isinstance(last_used_at, str):
            last_used_at = datetime.fromisoformat(last_used_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            sql_query=data["sql_query"],
            tags=data.get("tags", []),
            use_count=data.get("use_count", 0),
            last_used_at=last_used_at,
            organization_id=data["organization_id"],
            created_by_user_id=data.get("created_by_user_id"),
            is_private=data.get("is_private", False),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
        )

    def validate(self) -> list[str]:
        """Validate the favorite query.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.name:
            errors.append("Name is required")
        if not self.sql_query:
            errors.append("SQL query is required")

        return errors


@dataclass
class FavoriteSheet:
    """A saved Google Sheet reference with metadata.

    Attributes:
        name: User-friendly name (unique per org+owner for private).
        sheet_id: Google Sheet ID from URL.
        organization_id: Organization scope for multi-tenant isolation.
        id: Primary key (auto-generated).
        description: Optional description of the sheet.
        default_worksheet: Default worksheet name to use.
        tags: Optional list of tags for categorization.
        use_count: Number of times this sheet has been used.
        last_used_at: When the sheet was last used.
        last_verified_at: When sheet access was last verified.
        created_by_user_id: User who created this favorite.
        is_private: If true, only visible to creator.
        is_active: Soft delete flag.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    name: str
    sheet_id: str
    organization_id: int
    id: int | None = None
    description: str = ""
    default_worksheet: str = "Sheet1"
    tags: list[str] = field(default_factory=list)
    use_count: int = 0
    last_used_at: datetime | None = None
    last_verified_at: datetime | None = None
    created_by_user_id: int | None = None
    is_private: bool = False
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the favorite sheet.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sheet_id": self.sheet_id,
            "default_worksheet": self.default_worksheet,
            "tags": self.tags,
            "use_count": self.use_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_verified_at": self.last_verified_at.isoformat()
            if self.last_verified_at
            else None,
            "organization_id": self.organization_id,
            "created_by_user_id": self.created_by_user_id,
            "is_private": self.is_private,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FavoriteSheet":
        """Create FavoriteSheet from dictionary.

        Args:
            data: Dictionary with sheet data.

        Returns:
            FavoriteSheet instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        last_used_at = data.get("last_used_at")
        if isinstance(last_used_at, str):
            last_used_at = datetime.fromisoformat(last_used_at.replace("Z", "+00:00"))

        last_verified_at = data.get("last_verified_at")
        if isinstance(last_verified_at, str):
            last_verified_at = datetime.fromisoformat(last_verified_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            sheet_id=data["sheet_id"],
            default_worksheet=data.get("default_worksheet", "Sheet1"),
            tags=data.get("tags", []),
            use_count=data.get("use_count", 0),
            last_used_at=last_used_at,
            last_verified_at=last_verified_at,
            organization_id=data["organization_id"],
            created_by_user_id=data.get("created_by_user_id"),
            is_private=data.get("is_private", False),
            is_active=data.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
        )

    def validate(self) -> list[str]:
        """Validate the favorite sheet.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.name:
            errors.append("Name is required")
        if not self.sheet_id:
            errors.append("Sheet ID is required")

        return errors


# ============================================================================
# SQLAlchemy Models
# ============================================================================


class FavoriteQueryModel(Base):
    """SQLAlchemy model for favorite queries.

    Stores saved SQL queries scoped to organizations with privacy control.
    """

    __tablename__ = "favorite_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sql_query = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)  # JSON-encoded list
    use_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    organization_id = Column(Integer, nullable=False, index=True)
    created_by_user_id = Column(Integer, nullable=True, index=True)
    is_private = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Unique constraint: name must be unique per org for shared, per user for private
    __table_args__ = (
        UniqueConstraint(
            "name",
            "organization_id",
            "created_by_user_id",
            "is_private",
            name="uq_fav_query_name_org_user_private",
        ),
    )

    def to_dataclass(self) -> FavoriteQuery:
        """Convert model to FavoriteQuery dataclass.

        Returns:
            FavoriteQuery instance.
        """
        tags_str: str | None = str(self.tags) if self.tags else None
        return FavoriteQuery(
            id=self.id,  # type: ignore[arg-type]
            name=self.name,  # type: ignore[arg-type]
            description=self.description or "",  # type: ignore[arg-type]
            sql_query=self.sql_query,  # type: ignore[arg-type]
            tags=json.loads(tags_str) if tags_str else [],
            use_count=self.use_count,  # type: ignore[arg-type]
            last_used_at=self.last_used_at,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            created_by_user_id=self.created_by_user_id,  # type: ignore[arg-type]
            is_private=self.is_private,  # type: ignore[arg-type]
            is_active=self.is_active,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, fav: FavoriteQuery) -> "FavoriteQueryModel":
        """Create model from FavoriteQuery dataclass.

        Args:
            fav: FavoriteQuery instance.

        Returns:
            FavoriteQueryModel instance.
        """
        return cls(
            id=fav.id,
            name=fav.name,
            description=fav.description,
            sql_query=fav.sql_query,
            tags=json.dumps(fav.tags) if fav.tags else None,
            use_count=fav.use_count,
            last_used_at=fav.last_used_at,
            organization_id=fav.organization_id,
            created_by_user_id=fav.created_by_user_id,
            is_private=fav.is_private,
            is_active=fav.is_active,
            created_at=fav.created_at or datetime.now(timezone.utc),
            updated_at=fav.updated_at,
        )

    def __repr__(self) -> str:
        """String representation of favorite query."""
        visibility = "private" if self.is_private else "shared"
        return f"FavoriteQuery(id={self.id}, name='{self.name}', {visibility})"


class FavoriteSheetModel(Base):
    """SQLAlchemy model for favorite sheets.

    Stores saved Google Sheet references scoped to organizations with privacy control.
    """

    __tablename__ = "favorite_sheets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sheet_id = Column(String(100), nullable=False, index=True)
    default_worksheet = Column(String(100), default="Sheet1", nullable=False)
    tags = Column(Text, nullable=True)  # JSON-encoded list
    use_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    organization_id = Column(Integer, nullable=False, index=True)
    created_by_user_id = Column(Integer, nullable=True, index=True)
    is_private = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Unique constraint: name must be unique per org for shared, per user for private
    __table_args__ = (
        UniqueConstraint(
            "name",
            "organization_id",
            "created_by_user_id",
            "is_private",
            name="uq_fav_sheet_name_org_user_private",
        ),
    )

    def to_dataclass(self) -> FavoriteSheet:
        """Convert model to FavoriteSheet dataclass.

        Returns:
            FavoriteSheet instance.
        """
        tags_str: str | None = str(self.tags) if self.tags else None
        return FavoriteSheet(
            id=self.id,  # type: ignore[arg-type]
            name=self.name,  # type: ignore[arg-type]
            description=self.description or "",  # type: ignore[arg-type]
            sheet_id=self.sheet_id,  # type: ignore[arg-type]
            default_worksheet=self.default_worksheet,  # type: ignore[arg-type]
            tags=json.loads(tags_str) if tags_str else [],
            use_count=self.use_count,  # type: ignore[arg-type]
            last_used_at=self.last_used_at,  # type: ignore[arg-type]
            last_verified_at=self.last_verified_at,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            created_by_user_id=self.created_by_user_id,  # type: ignore[arg-type]
            is_private=self.is_private,  # type: ignore[arg-type]
            is_active=self.is_active,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, fav: FavoriteSheet) -> "FavoriteSheetModel":
        """Create model from FavoriteSheet dataclass.

        Args:
            fav: FavoriteSheet instance.

        Returns:
            FavoriteSheetModel instance.
        """
        return cls(
            id=fav.id,
            name=fav.name,
            description=fav.description,
            sheet_id=fav.sheet_id,
            default_worksheet=fav.default_worksheet,
            tags=json.dumps(fav.tags) if fav.tags else None,
            use_count=fav.use_count,
            last_used_at=fav.last_used_at,
            last_verified_at=fav.last_verified_at,
            organization_id=fav.organization_id,
            created_by_user_id=fav.created_by_user_id,
            is_private=fav.is_private,
            is_active=fav.is_active,
            created_at=fav.created_at or datetime.now(timezone.utc),
            updated_at=fav.updated_at,
        )

    def __repr__(self) -> str:
        """String representation of favorite sheet."""
        visibility = "private" if self.is_private else "shared"
        return f"FavoriteSheet(id={self.id}, name='{self.name}', {visibility})"


# ============================================================================
# Repositories
# ============================================================================


class FavoriteQueryRepository:
    """Repository for favorite query CRUD operations.

    Provides data access methods for favorite queries with
    SQLite persistence. Supports privacy filtering.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> "Session":
        """Get a new database session."""
        return self._session_factory()

    def _visibility_filter(
        self, query: "Query[FavoriteQueryModel]", organization_id: int, user_id: int | None
    ) -> "Query[FavoriteQueryModel]":
        """Apply visibility filter for privacy.

        Shows: all shared favorites OR private favorites created by user.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        query = query.filter(FavoriteQueryModel.organization_id == organization_id)
        if user_id is not None:
            query = query.filter(
                or_(
                    FavoriteQueryModel.is_private == False,
                    FavoriteQueryModel.created_by_user_id == user_id,
                )
            )
        else:
            # If no user, only show shared
            query = query.filter(FavoriteQueryModel.is_private == False)
        return query

    def create(self, favorite: FavoriteQuery) -> FavoriteQuery:
        """Create a new favorite query.

        Args:
            favorite: Favorite query to create.

        Returns:
            Created favorite with ID.

        Raises:
            ValueError: If name already exists or validation fails.
        """
        favorite.organization_id = validate_tenant(favorite.organization_id)  # type: ignore[assignment]
        errors = favorite.validate()
        if errors:
            raise ValueError(f"Invalid favorite query: {', '.join(errors)}")

        session = self._get_session()
        try:
            # Check for existing name (respecting privacy rules)
            existing_query = session.query(FavoriteQueryModel).filter(
                FavoriteQueryModel.name == favorite.name,
                FavoriteQueryModel.organization_id == favorite.organization_id,
                FavoriteQueryModel.is_active == True,
            )

            if favorite.is_private:
                existing_query = existing_query.filter(
                    FavoriteQueryModel.is_private == True,
                    FavoriteQueryModel.created_by_user_id == favorite.created_by_user_id,
                )
            else:
                existing_query = existing_query.filter(
                    FavoriteQueryModel.is_private == False,
                )

            if existing_query.first():
                raise ValueError(f"Favorite query with name '{favorite.name}' already exists")

            model = FavoriteQueryModel.from_dataclass(favorite)
            session.add(model)
            session.commit()
            favorite.id = model.id  # type: ignore[assignment]
            favorite.created_at = model.created_at  # type: ignore[assignment]
            return favorite
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(
        self,
        favorite_id: int,
        organization_id: int,
        user_id: int | None = None,
    ) -> FavoriteQuery | None:
        """Get favorite query by ID with visibility check.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.
            user_id: Current user ID for privacy filtering.

        Returns:
            Favorite query if found and visible, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteQueryModel).filter(
                FavoriteQueryModel.id == favorite_id,
                FavoriteQueryModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_name(
        self,
        name: str,
        organization_id: int,
        user_id: int | None = None,
    ) -> FavoriteQuery | None:
        """Get favorite query by name with visibility check.

        Args:
            name: Favorite name.
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.

        Returns:
            Favorite query if found and visible, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteQueryModel).filter(
                FavoriteQueryModel.name == name,
                FavoriteQueryModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        user_id: int | None = None,
        include_inactive: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[FavoriteQuery]:
        """Get all favorite queries visible to user.

        Args:
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.
            include_inactive: Whether to include inactive favorites.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of favorite queries.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteQueryModel)
            query = self._visibility_filter(query, organization_id, user_id)

            if not include_inactive:
                query = query.filter(FavoriteQueryModel.is_active == True)

            # Order by use count (most used first), then by name
            query = query.order_by(
                FavoriteQueryModel.use_count.desc(),
                FavoriteQueryModel.name.asc(),
            )

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update(self, favorite: FavoriteQuery) -> FavoriteQuery:
        """Update a favorite query.

        Args:
            favorite: Favorite with updated fields.

        Returns:
            Updated favorite query.

        Raises:
            ValueError: If favorite not found or name conflict.
        """
        favorite.organization_id = validate_tenant(favorite.organization_id)  # type: ignore[assignment]
        if favorite.id is None:
            raise ValueError("Favorite ID is required for update")

        errors = favorite.validate()
        if errors:
            raise ValueError(f"Invalid favorite query: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = (
                session.query(FavoriteQueryModel)
                .filter(
                    FavoriteQueryModel.id == favorite.id,
                    FavoriteQueryModel.organization_id == favorite.organization_id,
                )
                .first()
            )

            if not model:
                raise ValueError(f"Favorite query with ID {favorite.id} not found")

            # Check for name conflict if name changed
            if model.name != favorite.name:
                existing_query = session.query(FavoriteQueryModel).filter(
                    FavoriteQueryModel.name == favorite.name,
                    FavoriteQueryModel.organization_id == favorite.organization_id,
                    FavoriteQueryModel.id != favorite.id,
                    FavoriteQueryModel.is_active == True,
                )
                if favorite.is_private:
                    existing_query = existing_query.filter(
                        FavoriteQueryModel.is_private == True,
                        FavoriteQueryModel.created_by_user_id == favorite.created_by_user_id,
                    )
                else:
                    existing_query = existing_query.filter(
                        FavoriteQueryModel.is_private == False,
                    )

                if existing_query.first():
                    raise ValueError(f"Favorite query with name '{favorite.name}' already exists")

            model.name = favorite.name  # type: ignore[assignment]
            model.description = favorite.description  # type: ignore[assignment]
            model.sql_query = favorite.sql_query  # type: ignore[assignment]
            model.tags = json.dumps(favorite.tags) if favorite.tags else None  # type: ignore[assignment]
            model.is_private = favorite.is_private  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]  # type: ignore[assignment]

            session.commit()
            result: FavoriteQuery = model.to_dataclass()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, favorite_id: int, organization_id: int) -> bool:
        """Hard delete a favorite query.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteQueryModel)
                .filter(
                    FavoriteQueryModel.id == favorite_id,
                    FavoriteQueryModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            session.delete(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deactivate(self, favorite_id: int, organization_id: int) -> bool:
        """Soft delete (deactivate) a favorite query.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if deactivated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteQueryModel)
                .filter(
                    FavoriteQueryModel.id == favorite_id,
                    FavoriteQueryModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.is_active = False  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def increment_use_count(
        self,
        favorite_id: int,
        organization_id: int,
    ) -> bool:
        """Increment use count and update last_used_at.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteQueryModel)
                .filter(
                    FavoriteQueryModel.id == favorite_id,
                    FavoriteQueryModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.use_count += 1  # type: ignore[assignment]
            model.last_used_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def search(
        self,
        organization_id: int,
        user_id: int | None = None,
        query_text: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[FavoriteQuery]:
        """Search favorite queries by text or tags.

        Args:
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.
            query_text: Text to search in name and description.
            tags: Tags to filter by (any match).
            limit: Maximum results.

        Returns:
            List of matching favorite queries.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteQueryModel).filter(
                FavoriteQueryModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)

            if query_text:
                search_pattern = f"%{query_text}%"
                query = query.filter(
                    or_(
                        FavoriteQueryModel.name.ilike(search_pattern),
                        FavoriteQueryModel.description.ilike(search_pattern),
                    )
                )

            # Tag filtering would require JSON parsing in SQLite
            # For simplicity, we filter in Python after fetching
            results = query.order_by(FavoriteQueryModel.use_count.desc()).all()

            if tags:
                filtered = []
                for model in results:
                    tags_str = str(model.tags) if model.tags else None
                    model_tags = json.loads(tags_str) if tags_str else []
                    if any(t in model_tags for t in tags):
                        filtered.append(model)
                results = filtered

            return [m.to_dataclass() for m in results[:limit]]
        finally:
            session.close()

    def count(
        self,
        organization_id: int,
        user_id: int | None = None,
        include_inactive: bool = False,
    ) -> int:
        """Count favorite queries visible to user.

        Args:
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.
            include_inactive: Whether to count inactive favorites.

        Returns:
            Count of favorite queries.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteQueryModel)
            query = self._visibility_filter(query, organization_id, user_id)

            if not include_inactive:
                query = query.filter(FavoriteQueryModel.is_active == True)

            count_result: int = query.count()
            return count_result
        finally:
            session.close()


class FavoriteSheetRepository:
    """Repository for favorite sheet CRUD operations.

    Provides data access methods for favorite sheets with
    SQLite persistence. Supports privacy filtering.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> "Session":
        """Get a new database session."""
        return self._session_factory()

    def _visibility_filter(
        self, query: "Query[FavoriteSheetModel]", organization_id: int, user_id: int | None
    ) -> "Query[FavoriteSheetModel]":
        """Apply visibility filter for privacy.

        Shows: all shared favorites OR private favorites created by user.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        query = query.filter(FavoriteSheetModel.organization_id == organization_id)
        if user_id is not None:
            query = query.filter(
                or_(
                    FavoriteSheetModel.is_private == False,
                    FavoriteSheetModel.created_by_user_id == user_id,
                )
            )
        else:
            # If no user, only show shared
            query = query.filter(FavoriteSheetModel.is_private == False)
        return query

    def create(self, favorite: FavoriteSheet) -> FavoriteSheet:
        """Create a new favorite sheet.

        Args:
            favorite: Favorite sheet to create.

        Returns:
            Created favorite with ID.

        Raises:
            ValueError: If name already exists or validation fails.
        """
        favorite.organization_id = validate_tenant(favorite.organization_id)  # type: ignore[assignment]
        errors = favorite.validate()
        if errors:
            raise ValueError(f"Invalid favorite sheet: {', '.join(errors)}")

        session = self._get_session()
        try:
            # Check for existing name (respecting privacy rules)
            existing_query = session.query(FavoriteSheetModel).filter(
                FavoriteSheetModel.name == favorite.name,
                FavoriteSheetModel.organization_id == favorite.organization_id,
                FavoriteSheetModel.is_active == True,
            )

            if favorite.is_private:
                existing_query = existing_query.filter(
                    FavoriteSheetModel.is_private == True,
                    FavoriteSheetModel.created_by_user_id == favorite.created_by_user_id,
                )
            else:
                existing_query = existing_query.filter(
                    FavoriteSheetModel.is_private == False,
                )

            if existing_query.first():
                raise ValueError(f"Favorite sheet with name '{favorite.name}' already exists")

            model = FavoriteSheetModel.from_dataclass(favorite)
            session.add(model)
            session.commit()
            favorite.id = model.id  # type: ignore[assignment]
            favorite.created_at = model.created_at  # type: ignore[assignment]
            return favorite
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(
        self,
        favorite_id: int,
        organization_id: int,
        user_id: int | None = None,
    ) -> FavoriteSheet | None:
        """Get favorite sheet by ID with visibility check.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.
            user_id: Current user ID for privacy filtering.

        Returns:
            Favorite sheet if found and visible, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteSheetModel).filter(
                FavoriteSheetModel.id == favorite_id,
                FavoriteSheetModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_name(
        self,
        name: str,
        organization_id: int,
        user_id: int | None = None,
    ) -> FavoriteSheet | None:
        """Get favorite sheet by name with visibility check.

        Args:
            name: Favorite name.
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.

        Returns:
            Favorite sheet if found and visible, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteSheetModel).filter(
                FavoriteSheetModel.name == name,
                FavoriteSheetModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_sheet_id(
        self,
        sheet_id: str,
        organization_id: int,
        user_id: int | None = None,
    ) -> FavoriteSheet | None:
        """Get favorite sheet by Google Sheet ID.

        Args:
            sheet_id: Google Sheet ID.
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.

        Returns:
            First matching favorite sheet if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteSheetModel).filter(
                FavoriteSheetModel.sheet_id == sheet_id,
                FavoriteSheetModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        user_id: int | None = None,
        include_inactive: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[FavoriteSheet]:
        """Get all favorite sheets visible to user.

        Args:
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.
            include_inactive: Whether to include inactive favorites.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of favorite sheets.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteSheetModel)
            query = self._visibility_filter(query, organization_id, user_id)

            if not include_inactive:
                query = query.filter(FavoriteSheetModel.is_active == True)

            # Order by use count (most used first), then by name
            query = query.order_by(
                FavoriteSheetModel.use_count.desc(),
                FavoriteSheetModel.name.asc(),
            )

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update(self, favorite: FavoriteSheet) -> FavoriteSheet:
        """Update a favorite sheet.

        Args:
            favorite: Favorite with updated fields.

        Returns:
            Updated favorite sheet.

        Raises:
            ValueError: If favorite not found or name conflict.
        """
        favorite.organization_id = validate_tenant(favorite.organization_id)  # type: ignore[assignment]
        if favorite.id is None:
            raise ValueError("Favorite ID is required for update")

        errors = favorite.validate()
        if errors:
            raise ValueError(f"Invalid favorite sheet: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = (
                session.query(FavoriteSheetModel)
                .filter(
                    FavoriteSheetModel.id == favorite.id,
                    FavoriteSheetModel.organization_id == favorite.organization_id,
                )
                .first()
            )

            if not model:
                raise ValueError(f"Favorite sheet with ID {favorite.id} not found")

            # Check for name conflict if name changed
            if model.name != favorite.name:
                existing_query = session.query(FavoriteSheetModel).filter(
                    FavoriteSheetModel.name == favorite.name,
                    FavoriteSheetModel.organization_id == favorite.organization_id,
                    FavoriteSheetModel.id != favorite.id,
                    FavoriteSheetModel.is_active == True,
                )
                if favorite.is_private:
                    existing_query = existing_query.filter(
                        FavoriteSheetModel.is_private == True,
                        FavoriteSheetModel.created_by_user_id == favorite.created_by_user_id,
                    )
                else:
                    existing_query = existing_query.filter(
                        FavoriteSheetModel.is_private == False,
                    )

                if existing_query.first():
                    raise ValueError(f"Favorite sheet with name '{favorite.name}' already exists")

            model.name = favorite.name  # type: ignore[assignment]
            model.description = favorite.description  # type: ignore[assignment]
            model.sheet_id = favorite.sheet_id  # type: ignore[assignment]
            model.default_worksheet = favorite.default_worksheet  # type: ignore[assignment]
            model.tags = json.dumps(favorite.tags) if favorite.tags else None  # type: ignore[assignment]
            model.is_private = favorite.is_private  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            session.commit()
            result: FavoriteSheet = model.to_dataclass()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, favorite_id: int, organization_id: int) -> bool:
        """Hard delete a favorite sheet.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteSheetModel)
                .filter(
                    FavoriteSheetModel.id == favorite_id,
                    FavoriteSheetModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            session.delete(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deactivate(self, favorite_id: int, organization_id: int) -> bool:
        """Soft delete (deactivate) a favorite sheet.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if deactivated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteSheetModel)
                .filter(
                    FavoriteSheetModel.id == favorite_id,
                    FavoriteSheetModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.is_active = False  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def increment_use_count(
        self,
        favorite_id: int,
        organization_id: int,
    ) -> bool:
        """Increment use count and update last_used_at.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteSheetModel)
                .filter(
                    FavoriteSheetModel.id == favorite_id,
                    FavoriteSheetModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.use_count += 1  # type: ignore[assignment]
            model.last_used_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_verified(
        self,
        favorite_id: int,
        organization_id: int,
    ) -> bool:
        """Update last_verified_at timestamp.

        Args:
            favorite_id: Favorite ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(FavoriteSheetModel)
                .filter(
                    FavoriteSheetModel.id == favorite_id,
                    FavoriteSheetModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.last_verified_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def search(
        self,
        organization_id: int,
        user_id: int | None = None,
        query_text: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[FavoriteSheet]:
        """Search favorite sheets by text or tags.

        Args:
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.
            query_text: Text to search in name and description.
            tags: Tags to filter by (any match).
            limit: Maximum results.

        Returns:
            List of matching favorite sheets.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteSheetModel).filter(
                FavoriteSheetModel.is_active == True,
            )
            query = self._visibility_filter(query, organization_id, user_id)

            if query_text:
                search_pattern = f"%{query_text}%"
                query = query.filter(
                    or_(
                        FavoriteSheetModel.name.ilike(search_pattern),
                        FavoriteSheetModel.description.ilike(search_pattern),
                    )
                )

            # Tag filtering would require JSON parsing in SQLite
            # For simplicity, we filter in Python after fetching
            results = query.order_by(FavoriteSheetModel.use_count.desc()).all()

            if tags:
                filtered = []
                for model in results:
                    tags_str = str(model.tags) if model.tags else None
                    model_tags = json.loads(tags_str) if tags_str else []
                    if any(t in model_tags for t in tags):
                        filtered.append(model)
                results = filtered

            return [m.to_dataclass() for m in results[:limit]]
        finally:
            session.close()

    def count(
        self,
        organization_id: int,
        user_id: int | None = None,
        include_inactive: bool = False,
    ) -> int:
        """Count favorite sheets visible to user.

        Args:
            organization_id: Organization ID.
            user_id: Current user ID for privacy filtering.
            include_inactive: Whether to count inactive favorites.

        Returns:
            Count of favorite sheets.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(FavoriteSheetModel)
            query = self._visibility_filter(query, organization_id, user_id)

            if not include_inactive:
                query = query.filter(FavoriteSheetModel.is_active == True)

            count_result: int = query.count()
            return count_result
        finally:
            session.close()


# ============================================================================
# Singleton Accessors
# ============================================================================


_favorite_query_repository: FavoriteQueryRepository | None = None
_favorite_sheet_repository: FavoriteSheetRepository | None = None


def get_favorite_query_repository(db_path: str | None = None) -> FavoriteQueryRepository:
    """Get or create favorite query repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        FavoriteQueryRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _favorite_query_repository
    if _favorite_query_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _favorite_query_repository = FavoriteQueryRepository(db_path)
    return _favorite_query_repository


def reset_favorite_query_repository() -> None:
    """Reset favorite query repository singleton. For testing."""
    global _favorite_query_repository
    _favorite_query_repository = None


def get_favorite_sheet_repository(db_path: str | None = None) -> FavoriteSheetRepository:
    """Get or create favorite sheet repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        FavoriteSheetRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _favorite_sheet_repository
    if _favorite_sheet_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _favorite_sheet_repository = FavoriteSheetRepository(db_path)
    return _favorite_sheet_repository


def reset_favorite_sheet_repository() -> None:
    """Reset favorite sheet repository singleton. For testing."""
    global _favorite_sheet_repository
    _favorite_sheet_repository = None
