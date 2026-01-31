"""SQLAlchemy model and repository for users.

Users belong to organizations and have roles that determine their permissions.
Email is unique within an organization (same email can exist in different orgs).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import sessionmaker

# Import Base from organizations to share metadata with foreign key targets
from mysql_to_sheets.models.organizations import Base
from mysql_to_sheets.models.repository import validate_tenant

# Valid roles in the system
VALID_ROLES = ("owner", "admin", "operator", "viewer")


@dataclass
class User:
    """User dataclass for business logic.

    Represents a user in the multi-tenant system. Each user belongs
    to exactly one organization and has a role that determines permissions.
    """

    email: str
    display_name: str
    organization_id: int
    id: int | None = None
    password_hash: str = ""
    role: str = "viewer"
    is_active: bool = True
    force_password_change: bool = False
    created_at: datetime | None = None
    last_login_at: datetime | None = None

    def to_dict(self, include_password_hash: bool = False) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Args:
            include_password_hash: Whether to include password hash (default False).

        Returns:
            Dictionary representation of the user.
        """
        result = {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "force_password_change": self.force_password_change,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "organization_id": self.organization_id,
        }
        if include_password_hash:
            result["password_hash"] = self.password_hash
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Create User from dictionary.

        Args:
            data: Dictionary with user data.

        Returns:
            User instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        last_login_at = data.get("last_login_at")
        if isinstance(last_login_at, str):
            last_login_at = datetime.fromisoformat(last_login_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            email=data["email"],
            display_name=data["display_name"],
            password_hash=data.get("password_hash", ""),
            role=data.get("role", "viewer"),
            is_active=data.get("is_active", True),
            force_password_change=data.get("force_password_change", False),
            created_at=created_at,
            last_login_at=last_login_at,
            organization_id=data["organization_id"],
        )


class UserModel(Base):
    """SQLAlchemy model for users.

    Users are scoped to organizations with unique email per org.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)
    force_password_change = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_login_at = Column(DateTime, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Unique email per organization
    __table_args__ = (UniqueConstraint("email", "organization_id", name="uq_user_email_org"),)

    def to_dict(self, include_password_hash: bool = False) -> dict[str, Any]:
        """Convert model to dictionary.

        Args:
            include_password_hash: Whether to include password hash.

        Returns:
            Dictionary representation of the user.
        """
        result = {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "force_password_change": self.force_password_change,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "organization_id": self.organization_id,
        }
        if include_password_hash:
            result["password_hash"] = self.password_hash
        return result

    def to_dataclass(self) -> User:
        """Convert model to User dataclass.

        Returns:
            User dataclass instance.
        """
        # Cast SQLAlchemy Column types to Python types
        return User(
            id=int(self.id) if self.id is not None else None,
            email=str(self.email),
            password_hash=str(self.password_hash),
            display_name=str(self.display_name),
            role=str(self.role),
            is_active=bool(self.is_active),
            force_password_change=bool(self.force_password_change),
            created_at=self.created_at,  # type: ignore[arg-type]
            last_login_at=self.last_login_at,  # type: ignore[arg-type]
            organization_id=int(self.organization_id),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserModel":
        """Create model from dictionary.

        Args:
            data: Dictionary with user data.

        Returns:
            UserModel instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        last_login_at = data.get("last_login_at")
        if isinstance(last_login_at, str):
            last_login_at = datetime.fromisoformat(last_login_at.replace("Z", "+00:00"))

        return cls(
            email=data["email"],
            password_hash=data.get("password_hash", ""),
            display_name=data["display_name"],
            role=data.get("role", "viewer"),
            is_active=data.get("is_active", True),
            force_password_change=data.get("force_password_change", False),
            created_at=created_at,
            last_login_at=last_login_at,
            organization_id=data["organization_id"],
        )

    @classmethod
    def from_dataclass(cls, user: User) -> "UserModel":
        """Create model from User dataclass.

        Args:
            user: User dataclass instance.

        Returns:
            UserModel instance.
        """
        return cls(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active,
            force_password_change=user.force_password_change,
            created_at=user.created_at or datetime.now(timezone.utc),
            last_login_at=user.last_login_at,
            organization_id=user.organization_id,
        )

    def __repr__(self) -> str:
        """String representation of user."""
        status = "active" if self.is_active else "inactive"
        return f"User(id={self.id}, email='{self.email}', role='{self.role}', status={status})"


class UserRepository:
    """Repository for user CRUD operations.

    Provides data access methods for users with SQLite persistence.
    All queries are scoped to organization for multi-tenant isolation.
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

    def _get_session(self) -> Any:
        """Get a new database session."""
        return self._session_factory()

    def create(self, user: User) -> User:
        """Create a new user.

        Args:
            user: User to create.

        Returns:
            Created user with ID.

        Raises:
            ValueError: If email already exists in organization or invalid role.
        """
        if user.role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{user.role}'. Must be one of: {VALID_ROLES}")

        session = self._get_session()
        try:
            # Check for existing email in org
            existing = (
                session.query(UserModel)
                .filter(
                    UserModel.email == user.email,
                    UserModel.organization_id == user.organization_id,
                )
                .first()
            )
            if existing:
                raise ValueError(
                    f"User with email '{user.email}' already exists in this organization"
                )

            model = UserModel.from_dataclass(user)
            session.add(model)
            session.commit()
            user.id = model.id  # type: ignore[assignment]
            user.created_at = model.created_at  # type: ignore[assignment]
            return user
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, user_id: int, organization_id: int | None = None) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID.
            organization_id: Optional org filter for multi-tenant isolation.

        Returns:
            User if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(UserModel).filter(UserModel.id == user_id)
            if organization_id is not None:
                query = query.filter(UserModel.organization_id == organization_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_email(self, email: str, organization_id: int) -> User | None:
        """Get user by email within an organization.

        Args:
            email: User email.
            organization_id: Organization ID.

        Returns:
            User if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(UserModel)
                .filter(
                    UserModel.email == email,
                    UserModel.organization_id == organization_id,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_email_any_org(self, email: str) -> list[User]:
        """Get users by email across all organizations.

        Used for login when org is unknown.

        Args:
            email: User email.

        Returns:
            List of users with this email (one per org).
        """
        session = self._get_session()
        try:
            models = (
                session.query(UserModel)
                .filter(UserModel.email == email, UserModel.is_active == True)
                .all()
            )
            return [model.to_dataclass() for model in models]
        finally:
            session.close()

    def get_by_email_global(self, email: str) -> User | None:
        """Get first user by email across all organizations.

        Used for login when only email is known. Returns the first
        active user found with this email.

        Args:
            email: User email.

        Returns:
            User if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(UserModel)
                .filter(UserModel.email == email, UserModel.is_active == True)
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        include_inactive: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        """Get all users in an organization.

        Args:
            organization_id: Organization ID.
            include_inactive: Whether to include inactive users.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of users.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(UserModel).filter(UserModel.organization_id == organization_id)

            if not include_inactive:
                query = query.filter(UserModel.is_active == True)

            query = query.order_by(UserModel.created_at.desc())

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update(self, user: User) -> User:
        """Update a user.

        Args:
            user: User with updated fields.

        Returns:
            Updated user.

        Raises:
            ValueError: If user not found or invalid role.
        """
        user.organization_id = validate_tenant(user.organization_id)  # type: ignore[assignment]
        if user.id is None:
            raise ValueError("User ID is required for update")

        if user.role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{user.role}'. Must be one of: {VALID_ROLES}")

        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user.id).first()
            if not model:
                raise ValueError(f"User with ID {user.id} not found")

            # Check for email conflict if email changed
            if model.email != user.email:
                existing = (
                    session.query(UserModel)
                    .filter(
                        UserModel.email == user.email,
                        UserModel.organization_id == user.organization_id,
                        UserModel.id != user.id,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(
                        f"User with email '{user.email}' already exists in this organization"
                    )

            model.email = user.email
            model.display_name = user.display_name
            model.role = user.role
            model.is_active = user.is_active
            model.force_password_change = user.force_password_change
            if user.password_hash:
                model.password_hash = user.password_hash

            session.commit()
            result: User = model.to_dataclass()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp.

        Args:
            user_id: User ID.

        Returns:
            True if updated, False if user not found.
        """
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not model:
                return False

            model.last_login_at = datetime.now(timezone.utc)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_password(
        self, user_id: int, password_hash: str, clear_force_change: bool = True
    ) -> bool:
        """Update user's password hash.

        Args:
            user_id: User ID.
            password_hash: New bcrypt password hash.
            clear_force_change: Whether to clear the force_password_change flag.

        Returns:
            True if updated, False if user not found.
        """
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not model:
                return False

            model.password_hash = password_hash
            if clear_force_change:
                model.force_password_change = False
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_force_password_change(self, user_id: int, force: bool = True) -> bool:
        """Set or clear the force_password_change flag for a user.

        Args:
            user_id: User ID.
            force: Whether to require password change on next login.

        Returns:
            True if updated, False if user not found.
        """
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not model:
                return False

            model.force_password_change = force
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, user_id: int, organization_id: int | None = None) -> bool:
        """Delete a user.

        Args:
            user_id: User ID.
            organization_id: Optional org filter for multi-tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(UserModel).filter(UserModel.id == user_id)
            if organization_id is not None:
                query = query.filter(UserModel.organization_id == organization_id)
            model = query.first()

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

    def deactivate(self, user_id: int, organization_id: int | None = None) -> bool:
        """Deactivate a user (soft delete).

        Args:
            user_id: User ID.
            organization_id: Optional org filter for multi-tenant isolation.

        Returns:
            True if deactivated, False if not found.
        """
        organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(UserModel).filter(UserModel.id == user_id)
            if organization_id is not None:
                query = query.filter(UserModel.organization_id == organization_id)
            model = query.first()

            if not model:
                return False

            model.is_active = False
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self, organization_id: int, include_inactive: bool = False) -> int:
        """Count users in an organization.

        Args:
            organization_id: Organization ID.
            include_inactive: Whether to include inactive users.

        Returns:
            Number of users.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(UserModel).filter(UserModel.organization_id == organization_id)
            if not include_inactive:
                query = query.filter(UserModel.is_active == True)
            return int(query.count())
        finally:
            session.close()

    def get_owner(self, organization_id: int) -> User | None:
        """Get the owner of an organization.

        Args:
            organization_id: Organization ID.

        Returns:
            Owner user if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(UserModel)
                .filter(
                    UserModel.organization_id == organization_id,
                    UserModel.role == "owner",
                    UserModel.is_active == True,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all_users_global(
        self,
        include_inactive: bool = False,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        organization_id: int | None = None,
        role: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get all users across all organizations with org info joined.

        This is a privileged operation for super admin dashboards only.
        No tenant context validation is performed.

        Args:
            include_inactive: Whether to include inactive users.
            limit: Maximum number of results (default 50).
            offset: Number of results to skip for pagination.
            search: Optional search term for email or display_name.
            organization_id: Optional filter by specific organization.
            role: Optional filter by role.

        Returns:
            Tuple of (list of user dicts with org info, total count).
        """
        from mysql_to_sheets.models.organizations import OrganizationModel

        session = self._get_session()
        try:
            # Build base query with organization join
            query = session.query(UserModel, OrganizationModel).join(
                OrganizationModel, UserModel.organization_id == OrganizationModel.id
            )

            # Apply filters
            if not include_inactive:
                query = query.filter(UserModel.is_active == True)

            if organization_id is not None:
                query = query.filter(UserModel.organization_id == organization_id)

            if role is not None and role in VALID_ROLES:
                query = query.filter(UserModel.role == role)

            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (UserModel.email.ilike(search_pattern))
                    | (UserModel.display_name.ilike(search_pattern))
                )

            # Get total count before pagination
            total_count = query.count()

            # Apply ordering and pagination
            query = query.order_by(
                OrganizationModel.name.asc(),
                UserModel.created_at.desc(),
            )

            if offset > 0:
                query = query.offset(offset)
            query = query.limit(limit)

            # Build result list with org info
            results: list[dict[str, Any]] = []
            for user_model, org_model in query.all():
                user_dict = user_model.to_dict()
                user_dict["organization_name"] = org_model.name
                user_dict["organization_slug"] = org_model.slug
                user_dict["organization_tier"] = org_model.subscription_tier
                results.append(user_dict)

            return results, total_count
        finally:
            session.close()

    def transfer_ownership(
        self,
        organization_id: int,
        current_owner_id: int,
        new_owner_id: int,
    ) -> bool:
        """Transfer organization ownership to another user.

        Args:
            organization_id: Organization ID.
            current_owner_id: Current owner's user ID.
            new_owner_id: New owner's user ID.

        Returns:
            True if transferred, False if validation failed.

        Raises:
            ValueError: If users not found or new owner not an admin.
        """
        session = self._get_session()
        try:
            current_owner = (
                session.query(UserModel)
                .filter(
                    UserModel.id == current_owner_id,
                    UserModel.organization_id == organization_id,
                    UserModel.role == "owner",
                )
                .first()
            )
            if not current_owner:
                raise ValueError("Current owner not found or not the owner")

            new_owner = (
                session.query(UserModel)
                .filter(
                    UserModel.id == new_owner_id,
                    UserModel.organization_id == organization_id,
                    UserModel.is_active == True,
                )
                .first()
            )
            if not new_owner:
                raise ValueError("New owner not found in organization")

            if new_owner.role not in ("admin", "owner"):
                raise ValueError("New owner must be an admin")

            # Transfer ownership
            current_owner.role = "admin"
            new_owner.role = "owner"

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Singleton instance
_user_repository: UserRepository | None = None


def get_user_repository(db_path: str | None = None) -> UserRepository:
    """Get or create user repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        UserRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _user_repository
    if _user_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _user_repository = UserRepository(db_path)
    return _user_repository


def reset_user_repository() -> None:
    """Reset user repository singleton. For testing."""
    global _user_repository
    _user_repository = None
