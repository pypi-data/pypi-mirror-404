"""Database models base configuration.

This module provides SQLAlchemy engine, session, and Base declarative class
for persistence of sync history, users, organizations, and API keys.
"""

from collections.abc import Generator

# SQLAlchemy imports are optional - only needed when database persistence is enabled
try:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

    SQLALCHEMY_AVAILABLE = True

    class Base(DeclarativeBase):
        pass

except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = object  # type: ignore[misc,assignment]
    Engine = object  # type: ignore[misc,assignment]
    Session = object  # type: ignore[misc,assignment]

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(database_url: str | None = None) -> Engine:
    """Get or create SQLAlchemy engine.

    Args:
        database_url: Database connection URL. If None, uses sqlite in-memory.

    Returns:
        SQLAlchemy engine instance.

    Raises:
        ImportError: If SQLAlchemy is not installed.
    """
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError(
            "SQLAlchemy is required for database persistence. Install with: pip install sqlalchemy"
        )

    global _engine
    if _engine is None:
        url = database_url or "sqlite:///:memory:"
        _engine = create_engine(url, echo=False)
    return _engine


def get_session() -> Generator[Session, None, None]:
    """Get database session as context manager.

    Yields:
        SQLAlchemy session instance.

    Raises:
        ImportError: If SQLAlchemy is not installed.
    """
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError(
            "SQLAlchemy is required for database persistence. Install with: pip install sqlalchemy"
        )

    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(database_url: str | None = None) -> None:
    """Initialize database tables.

    Args:
        database_url: Database connection URL.

    Raises:
        ImportError: If SQLAlchemy is not installed.
    """
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError(
            "SQLAlchemy is required for database persistence. Install with: pip install sqlalchemy"
        )

    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
