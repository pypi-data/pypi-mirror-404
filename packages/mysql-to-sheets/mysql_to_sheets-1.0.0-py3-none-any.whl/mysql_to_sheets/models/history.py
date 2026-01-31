"""SQLAlchemy model for sync history persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for sync history models."""

    pass


class SyncHistoryModel(Base):
    """SQLAlchemy model for sync history entries.

    Stores a record of each sync operation for auditing,
    debugging, and analytics purposes.
    """

    __tablename__ = "sync_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    success = Column(Boolean, nullable=False)
    rows_synced = Column(Integer, default=0)
    columns = Column(Integer, default=0)
    headers = Column(Text, nullable=True)  # JSON-encoded list
    message = Column(String(500), nullable=True)
    error = Column(Text, nullable=True)
    sheet_id = Column(String(100), nullable=True, index=True)
    worksheet = Column(String(100), nullable=True)
    duration_ms = Column(Float, default=0.0)
    request_id = Column(String(36), nullable=True, index=True)
    source = Column(String(20), nullable=True)  # 'cli', 'api', 'web'

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the history entry.
        """
        import json

        headers_str = str(self.headers) if self.headers else "[]"

        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "success": self.success,
            "rows_synced": self.rows_synced,
            "columns": self.columns,
            "headers": json.loads(headers_str),
            "message": self.message,
            "error": self.error,
            "sheet_id": self.sheet_id,
            "worksheet": self.worksheet,
            "duration_ms": self.duration_ms,
            "request_id": self.request_id,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncHistoryModel":
        """Create model from dictionary.

        Args:
            data: Dictionary with history entry data.

        Returns:
            SyncHistoryModel instance.
        """
        import json
        from datetime import datetime, timezone

        headers = data.get("headers", [])
        if isinstance(headers, list):
            headers = json.dumps(headers)

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            timestamp=timestamp,
            success=data.get("success", False),
            rows_synced=data.get("rows_synced", 0),
            columns=data.get("columns", 0),
            headers=headers,
            message=data.get("message"),
            error=data.get("error"),
            sheet_id=data.get("sheet_id"),
            worksheet=data.get("worksheet"),
            duration_ms=data.get("duration_ms", 0.0),
            request_id=data.get("request_id"),
            source=data.get("source"),
        )

    def __repr__(self) -> str:
        """String representation of history entry."""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"SyncHistory(id={self.id}, status={status}, "
            f"rows={self.rows_synced}, timestamp={self.timestamp})"
        )
