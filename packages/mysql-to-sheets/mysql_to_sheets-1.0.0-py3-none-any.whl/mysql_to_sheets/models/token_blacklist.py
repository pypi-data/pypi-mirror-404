"""SQLAlchemy model for persistent JWT token blacklist.

Stores blacklisted JWT tokens (by their JTI) to ensure logged-out tokens
remain invalid even after server restart.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for token blacklist models."""

    pass


class TokenBlacklistModel(Base):
    """SQLAlchemy model for blacklisted tokens.

    Stores the JTI (JWT ID) of tokens that have been revoked,
    along with their expiration time for cleanup purposes.
    """

    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)  # Index defined in table_args
    blacklisted_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    reason = Column(String(100), nullable=True)  # "logout", "revoked", etc.

    def is_expired(self) -> bool:
        """Check if the blacklisted token has expired.

        Expired entries can be safely cleaned up.

        Returns:
            True if the token's expiration time has passed.
        """
        result: bool = datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the blacklist entry.
        """
        return {
            "id": self.id,
            "jti": self.jti,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "blacklisted_at": self.blacklisted_at.isoformat() if self.blacklisted_at else None,
            "reason": self.reason,
        }

    def __repr__(self) -> str:
        """String representation of blacklist entry."""
        return f"TokenBlacklist(jti={self.jti!r}, expires_at={self.expires_at})"


class TokenBlacklistRepository:
    """Repository for token blacklist operations.

    Provides methods to add tokens to blacklist, check if a token
    is blacklisted, and clean up expired entries.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize token blacklist repository.

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

    def add(
        self,
        jti: str,
        expires_at: datetime,
        reason: str = "logout",
    ) -> TokenBlacklistModel:
        """Add a token to the blacklist.

        Args:
            jti: The JWT ID to blacklist.
            expires_at: When the token expires (for cleanup).
            reason: Reason for blacklisting (default: "logout").

        Returns:
            The created blacklist entry.
        """
        session = self._get_session()
        try:
            # Check if already blacklisted (idempotent)
            existing = session.query(TokenBlacklistModel).filter_by(jti=jti).first()
            if existing:
                return existing

            entry = TokenBlacklistModel(
                jti=jti,
                expires_at=expires_at,
                reason=reason,
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            jti: The JWT ID to check.

        Returns:
            True if the token is blacklisted, False otherwise.
        """
        session = self._get_session()
        try:
            entry = session.query(TokenBlacklistModel).filter_by(jti=jti).first()
            return entry is not None
        finally:
            session.close()

    def cleanup_expired(self) -> int:
        """Remove expired entries from the blacklist.

        Expired tokens no longer need to be tracked since they
        would be rejected anyway during JWT validation.

        Returns:
            Number of entries removed.
        """
        session = self._get_session()
        try:
            now = datetime.now(timezone.utc)
            result = (
                session.query(TokenBlacklistModel)
                .filter(TokenBlacklistModel.expires_at < now)
                .delete()
            )
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self) -> int:
        """Get total number of blacklisted tokens.

        Returns:
            Total count of blacklist entries.
        """
        session = self._get_session()
        try:
            return session.query(TokenBlacklistModel).count()
        finally:
            session.close()

    def clear(self) -> int:
        """Clear all entries from the blacklist.

        FOR TESTING ONLY - do not use in production.

        Returns:
            Number of entries removed.
        """
        session = self._get_session()
        try:
            result = session.query(TokenBlacklistModel).delete()
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Singleton instance for the repository
_blacklist_repo: TokenBlacklistRepository | None = None


def get_token_blacklist_repository(db_path: str | None = None) -> TokenBlacklistRepository:
    """Get or create the token blacklist repository singleton.

    Args:
        db_path: Path to SQLite database. Uses tenant DB path if None.

    Returns:
        TokenBlacklistRepository instance.
    """
    global _blacklist_repo

    if _blacklist_repo is None:
        if db_path is None:
            from mysql_to_sheets.core.tenant import get_tenant_db_path

            db_path = get_tenant_db_path()
        _blacklist_repo = TokenBlacklistRepository(db_path)

    return _blacklist_repo


def reset_token_blacklist_repository() -> None:
    """Reset the token blacklist repository singleton.

    FOR TESTING ONLY.
    """
    global _blacklist_repo
    _blacklist_repo = None
