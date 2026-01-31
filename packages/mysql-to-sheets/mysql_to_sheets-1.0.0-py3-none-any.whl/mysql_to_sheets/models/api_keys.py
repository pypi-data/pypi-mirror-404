"""SQLAlchemy model for API key persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for API keys models."""

    pass


class APIKeyModel(Base):
    """SQLAlchemy model for API keys.

    Stores API key metadata for authentication.
    The actual key is never stored - only its hash.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_salt = Column(String(32), nullable=True)  # Per-key random salt for hashing
    key_prefix = Column(String(20), nullable=True)  # First few chars for identification
    scopes = Column(JSON, nullable=False, default=lambda: ["*"])  # Permission scopes
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # None = never expires
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime, nullable=True)
    description = Column(String(500), nullable=True)

    # Scope hierarchy: admin > config > sync > read
    SCOPE_HIERARCHY: dict[str, int] = {
        "admin": 3,
        "config": 2,
        "sync": 1,
        "read": 0,
    }

    def has_scope(self, required_scope: str) -> bool:
        """Check if key has the required scope.

        Scope hierarchy: admin > config > sync > read
        Wildcard "*" grants all scopes.

        Args:
            required_scope: The scope required for the operation.

        Returns:
            True if the key has the required scope.
        """
        key_scopes = self.scopes or ["*"]

        # Wildcard grants all permissions
        if "*" in key_scopes:
            return True

        # Direct match
        if required_scope in key_scopes:
            return True

        # Check hierarchy: higher scopes include lower ones
        required_level = self.SCOPE_HIERARCHY.get(required_scope, 99)
        for scope in key_scopes:
            scope_level = self.SCOPE_HIERARCHY.get(scope, -1)
            if scope_level >= required_level:
                return True

        return False

    def is_expired(self) -> bool:
        """Check if the API key has expired.

        Returns:
            True if the key has an expiration date that has passed.
        """
        if self.expires_at is None:
            return False
        result: bool = datetime.now(timezone.utc) > self.expires_at  # type: ignore[assignment]
        return result

    def to_dict(self, include_hash: bool = False) -> dict[str, Any]:
        """Convert model to dictionary.

        Args:
            include_hash: Whether to include the key hash and salt.

        Returns:
            Dictionary representation of the API key.
        """
        data = {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "scopes": self.scopes or ["*"],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "description": self.description,
        }
        if include_hash:
            data["key_hash"] = self.key_hash
            data["key_salt"] = self.key_salt
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "APIKeyModel":
        """Create model from dictionary.

        Args:
            data: Dictionary with API key data.

        Returns:
            APIKeyModel instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        last_used_at = data.get("last_used_at")
        if isinstance(last_used_at, str):
            last_used_at = datetime.fromisoformat(last_used_at.replace("Z", "+00:00"))

        expires_at = data.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

        revoked_at = data.get("revoked_at")
        if isinstance(revoked_at, str):
            revoked_at = datetime.fromisoformat(revoked_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            key_hash=data.get("key_hash", ""),
            key_salt=data.get("key_salt"),
            key_prefix=data.get("key_prefix"),
            scopes=data.get("scopes", ["*"]),
            created_at=created_at or datetime.now(timezone.utc),
            last_used_at=last_used_at,
            expires_at=expires_at,
            revoked=data.get("revoked", False),
            revoked_at=revoked_at,
            description=data.get("description"),
        )

    @property
    def is_active(self) -> bool:
        """Check if the API key is active (not revoked and not expired).

        Returns:
            True if the key is active.
        """
        return not self.revoked and not self.is_expired()

    def __repr__(self) -> str:
        """String representation of API key."""
        status = "REVOKED" if self.revoked else "ACTIVE"
        return (
            f"APIKey(id={self.id}, name={self.name!r}, prefix={self.key_prefix!r}, status={status})"
        )


class APIKeyRepository:
    """Repository for API key operations.

    Provides CRUD operations for API keys with SQLite backend.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize API key repository.

        Args:
            db_path: Path to SQLite database file.
        """
        from pathlib import Path

        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._engine: Engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def create(
        self,
        name: str,
        key_hash: str,
        key_salt: str | None = None,
        key_prefix: str | None = None,
        description: str | None = None,
        expires_at: datetime | None = None,
        scopes: list[str] | None = None,
    ) -> APIKeyModel:
        """Create a new API key.

        Args:
            name: Name for the key.
            key_hash: Hashed API key.
            key_salt: Per-key salt used for hashing.
            key_prefix: First few characters of the key.
            description: Optional description.
            expires_at: Optional expiration datetime (None = never expires).
            scopes: Permission scopes (default ["*"] for full access).

        Returns:
            The created API key model.
        """
        session = self._get_session()
        try:
            api_key = APIKeyModel(
                name=name,
                key_hash=key_hash,
                key_salt=key_salt,
                key_prefix=key_prefix,
                scopes=scopes or ["*"],
                description=description,
                expires_at=expires_at,
            )
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            return api_key
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, key_id: int) -> APIKeyModel | None:
        """Get an API key by ID.

        Args:
            key_id: The key ID.

        Returns:
            APIKeyModel if found, None otherwise.
        """
        session = self._get_session()
        try:
            return session.query(APIKeyModel).filter_by(id=key_id).first()
        finally:
            session.close()

    def get_by_hash(self, key_hash: str) -> APIKeyModel | None:
        """Get an API key by hash.

        Returns None if the key is not found, is revoked, or is expired.

        Args:
            key_hash: The hashed API key.

        Returns:
            APIKeyModel if found and valid, None otherwise.
        """
        session = self._get_session()
        try:
            api_key = session.query(APIKeyModel).filter_by(key_hash=key_hash, revoked=False).first()

            # Check if key is expired
            if api_key is not None and api_key.is_expired():
                return None

            return api_key
        finally:
            session.close()

    def get_by_prefix(
        self,
        prefix: str,
        include_revoked: bool = False,
    ) -> list[APIKeyModel]:
        """Get API keys matching prefix for efficient O(1) lookup.

        This method enables prefix-based filtering before expensive hash
        verification, reducing auth overhead from O(n) to O(1) in typical cases.

        Args:
            prefix: The key prefix to match (typically first 8 chars like "mts_a1b2").
            include_revoked: Whether to include revoked keys.

        Returns:
            List of API keys matching the prefix (typically 0 or 1).
        """
        session = self._get_session()
        try:
            query = session.query(APIKeyModel).filter(
                APIKeyModel.key_prefix == prefix
            )
            if not include_revoked:
                query = query.filter(APIKeyModel.revoked == False)  # noqa: E712
            return query.all()
        finally:
            session.close()

    def get_all(
        self,
        include_revoked: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[APIKeyModel]:
        """Get all API keys with optional pagination.

        Args:
            include_revoked: Whether to include revoked keys.
            limit: Maximum number of keys to return. None for unlimited.
            offset: Number of keys to skip.

        Returns:
            List of API key models.
        """
        session = self._get_session()
        try:
            query = session.query(APIKeyModel)
            if not include_revoked:
                query = query.filter_by(revoked=False)
            query = query.order_by(APIKeyModel.created_at.desc())
            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def revoke(self, key_id: int) -> bool:
        """Revoke an API key.

        Args:
            key_id: The key ID to revoke.

        Returns:
            True if revoked, False if key not found.
        """
        session = self._get_session()
        try:
            api_key = session.query(APIKeyModel).filter_by(id=key_id).first()
            if api_key is None:
                return False

            api_key.revoked = True  # type: ignore[assignment]
            api_key.revoked_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_last_used(self, key_hash: str) -> None:
        """Update the last used timestamp for a key.

        Args:
            key_hash: The hashed API key.
        """
        session = self._get_session()
        try:
            api_key = session.query(APIKeyModel).filter_by(key_hash=key_hash).first()
            if api_key:
                api_key.last_used_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def delete(self, key_id: int) -> bool:
        """Permanently delete an API key.

        Args:
            key_id: The key ID to delete.

        Returns:
            True if deleted, False if key not found.
        """
        session = self._get_session()
        try:
            result = session.query(APIKeyModel).filter_by(id=key_id).delete()
            session.commit()
            return result > 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self, include_revoked: bool = False) -> int:
        """Get total number of API keys.

        Args:
            include_revoked: Whether to count revoked keys.

        Returns:
            Total count of keys.
        """
        session = self._get_session()
        try:
            query = session.query(APIKeyModel)
            if not include_revoked:
                query = query.filter_by(revoked=False)
            return query.count()
        finally:
            session.close()


# Alias for CLI compatibility
ApiKey = APIKeyModel


def get_api_key_repository(db_path: str) -> APIKeyRepository:
    """Get an API key repository instance.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        APIKeyRepository instance.
    """
    return APIKeyRepository(db_path)
