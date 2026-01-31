"""History repository with in-memory and SQLite backends.

This module provides a repository pattern for storing sync history,
with pluggable backends for different storage needs.
"""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)


@dataclass
class HistoryEntry:
    """A single sync history entry.

    Attributes:
        timestamp: When the sync occurred.
        success: Whether the sync succeeded.
        rows_synced: Number of rows synced.
        columns: Number of columns in the data.
        headers: List of column headers.
        message: Status message.
        error: Error message if failed.
        sheet_id: Target Google Sheet ID.
        worksheet: Target worksheet name.
        duration_ms: Sync duration in milliseconds.
        request_id: Unique identifier for the request.
        source: Where the sync was initiated ('cli', 'api', 'web').
        id: Unique identifier for the entry (set by repository).
    """

    timestamp: datetime
    success: bool
    rows_synced: int = 0
    columns: int = 0
    headers: list[str] = field(default_factory=list)
    message: str = ""
    error: str | None = None
    sheet_id: str | None = None
    worksheet: str | None = None
    duration_ms: float = 0.0
    request_id: str | None = None
    source: str | None = None
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary.

        Returns:
            Dictionary representation of the entry.
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "success": self.success,
            "rows_synced": self.rows_synced,
            "columns": self.columns,
            "headers": self.headers,
            "message": self.message,
            "error": self.error,
            "sheet_id": self.sheet_id,
            "worksheet": self.worksheet,
            "duration_ms": self.duration_ms,
            "request_id": self.request_id,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        """Create entry from dictionary.

        Args:
            data: Dictionary with entry data.

        Returns:
            HistoryEntry instance.
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            id=data.get("id"),
            timestamp=timestamp,
            success=data.get("success", False),
            rows_synced=data.get("rows_synced", 0),
            columns=data.get("columns", 0),
            headers=data.get("headers", []),
            message=data.get("message", ""),
            error=data.get("error"),
            sheet_id=data.get("sheet_id"),
            worksheet=data.get("worksheet"),
            duration_ms=data.get("duration_ms", 0.0),
            request_id=data.get("request_id"),
            source=data.get("source"),
        )


class HistoryRepository(ABC):
    """Abstract base class for history storage backends."""

    @abstractmethod
    def add(self, entry: HistoryEntry) -> HistoryEntry:
        """Add a new history entry.

        Args:
            entry: The entry to add.

        Returns:
            The entry with ID populated.
        """
        pass

    @abstractmethod
    def get_all(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[HistoryEntry]:
        """Get all history entries.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of history entries, most recent first.
        """
        pass

    @abstractmethod
    def get_by_id(self, entry_id: int) -> HistoryEntry | None:
        """Get a specific entry by ID.

        Args:
            entry_id: The entry ID.

        Returns:
            The entry if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_by_request_id(self, request_id: str) -> HistoryEntry | None:
        """Get a specific entry by request ID.

        Args:
            request_id: The request ID.

        Returns:
            The entry if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_by_sheet_id(
        self,
        sheet_id: str,
        limit: int | None = None,
    ) -> list[HistoryEntry]:
        """Get entries for a specific sheet.

        Args:
            sheet_id: The Google Sheet ID.
            limit: Maximum number of entries to return.

        Returns:
            List of history entries for the sheet.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Get total number of history entries.

        Returns:
            Total count of entries.
        """
        pass

    @abstractmethod
    def clear(self) -> int:
        """Clear all history entries.

        Returns:
            Number of entries deleted.
        """
        pass


class InMemoryHistoryRepository(HistoryRepository):
    """In-memory history storage with bounded size.

    Suitable for development and testing. Data is lost on restart.
    """

    def __init__(self, max_entries: int = 100) -> None:
        """Initialize in-memory repository.

        Args:
            max_entries: Maximum entries to keep.
        """
        self._entries: deque[HistoryEntry] = deque(maxlen=max_entries)
        self._next_id = 1

    def add(self, entry: HistoryEntry) -> HistoryEntry:
        """Add a new history entry."""
        entry.id = self._next_id
        self._next_id += 1
        self._entries.appendleft(entry)
        logger.debug(f"Added history entry {entry.id}")
        return entry

    def get_all(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[HistoryEntry]:
        """Get all history entries."""
        entries = list(self._entries)
        if offset > 0:
            entries = entries[offset:]
        if limit is not None:
            entries = entries[:limit]
        return entries

    def get_by_id(self, entry_id: int) -> HistoryEntry | None:
        """Get a specific entry by ID."""
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_by_request_id(self, request_id: str) -> HistoryEntry | None:
        """Get a specific entry by request ID."""
        for entry in self._entries:
            if entry.request_id == request_id:
                return entry
        return None

    def get_by_sheet_id(
        self,
        sheet_id: str,
        limit: int | None = None,
    ) -> list[HistoryEntry]:
        """Get entries for a specific sheet."""
        entries = [e for e in self._entries if e.sheet_id == sheet_id]
        if limit is not None:
            entries = entries[:limit]
        return entries

    def count(self) -> int:
        """Get total number of history entries."""
        return len(self._entries)

    def clear(self) -> int:
        """Clear all history entries."""
        count = len(self._entries)
        self._entries.clear()
        self._next_id = 1
        return count


class SQLiteHistoryRepository(HistoryRepository):
    """SQLite-backed history storage.

    Persists history to a SQLite database file.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize SQLite repository.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._engine = None
        self._session_factory = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database connection and create tables."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from mysql_to_sheets.models.history import Base

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(f"sqlite:///{self.db_path}", echo=False)  # type: ignore[assignment]
        Base.metadata.create_all(self._engine)  # type: ignore[arg-type]
        self._session_factory = sessionmaker(bind=self._engine)  # type: ignore[assignment]
        logger.info(f"Initialized SQLite history database at {self.db_path}")

    def _get_session(self) -> Any:
        """Get a new database session."""
        return self._session_factory()  # type: ignore[misc]

    def add(self, entry: HistoryEntry) -> HistoryEntry:
        """Add a new history entry."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            model = SyncHistoryModel.from_dict(entry.to_dict())
            session.add(model)
            session.commit()
            entry.id = model.id  # type: ignore[assignment]
            logger.debug(f"Added history entry {entry.id} to SQLite")
            return entry
        except (SQLAlchemyError, ValueError) as e:
            session.rollback()
            logger.error(f"Failed to add history entry: {e}")
            raise
        finally:
            session.close()

    def get_all(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[HistoryEntry]:
        """Get all history entries."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            query = session.query(SyncHistoryModel).order_by(SyncHistoryModel.timestamp.desc())
            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [HistoryEntry.from_dict(m.to_dict()) for m in query.all()]
        finally:
            session.close()

    def get_by_id(self, entry_id: int) -> HistoryEntry | None:
        """Get a specific entry by ID."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            model = session.query(SyncHistoryModel).filter_by(id=entry_id).first()
            if model:
                return HistoryEntry.from_dict(model.to_dict())
            return None
        finally:
            session.close()

    def get_by_request_id(self, request_id: str) -> HistoryEntry | None:
        """Get a specific entry by request ID."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            model = session.query(SyncHistoryModel).filter_by(request_id=request_id).first()
            if model:
                return HistoryEntry.from_dict(model.to_dict())
            return None
        finally:
            session.close()

    def get_by_sheet_id(
        self,
        sheet_id: str,
        limit: int | None = None,
    ) -> list[HistoryEntry]:
        """Get entries for a specific sheet."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            query = (
                session.query(SyncHistoryModel)
                .filter_by(sheet_id=sheet_id)
                .order_by(SyncHistoryModel.timestamp.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            return [HistoryEntry.from_dict(m.to_dict()) for m in query.all()]
        finally:
            session.close()

    def count(self) -> int:
        """Get total number of history entries."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            return session.query(SyncHistoryModel).count()  # type: ignore[no-any-return]
        finally:
            session.close()

    def clear(self) -> int:
        """Clear all history entries."""
        from mysql_to_sheets.models.history import SyncHistoryModel

        session = self._get_session()
        try:
            count = session.query(SyncHistoryModel).delete()
            session.commit()
            return count  # type: ignore[no-any-return]
        except (SQLAlchemyError, ValueError) as e:
            session.rollback()
            logger.error(f"Failed to clear history: {e}")
            raise
        finally:
            session.close()


# Global repository instance
_repository: HistoryRepository | None = None


def get_history_repository(
    backend: str = "memory",
    db_path: str | None = None,
    max_entries: int = 100,
) -> HistoryRepository:
    """Get or create the global history repository.

    Args:
        backend: Storage backend ('memory' or 'sqlite').
        db_path: Path to SQLite database (required for sqlite backend).
        max_entries: Max entries for in-memory backend.

    Returns:
        HistoryRepository instance.

    Raises:
        ValueError: If backend is unknown or sqlite path not provided.
    """
    global _repository

    if _repository is None:
        if backend == "memory":
            _repository = InMemoryHistoryRepository(max_entries)
            logger.info("Using in-memory history repository")
        elif backend == "sqlite":
            if not db_path:
                raise ValueError("db_path is required for sqlite backend")
            _repository = SQLiteHistoryRepository(db_path)
            logger.info(f"Using SQLite history repository at {db_path}")
        else:
            raise ValueError(f"Unknown history backend: {backend}")

    return _repository


def reset_history_repository() -> None:
    """Reset the global history repository (useful for testing)."""
    global _repository
    _repository = None
