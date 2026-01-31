"""SQLAlchemy models for sheet snapshots.

Snapshots store compressed copies of Google Sheet data before sync operations,
enabling rollback capability. Each snapshot captures the full sheet state
including all rows and columns.
"""

import hashlib
import json
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from mysql_to_sheets.models.repository import validate_tenant


# Use a separate Base for snapshots to avoid FK dependencies
class SnapshotBase(DeclarativeBase):
    pass


@dataclass
class Snapshot:
    """Snapshot dataclass for business logic.

    Represents a point-in-time copy of a Google Sheet's data,
    captured before a sync operation for rollback capability.
    """

    sheet_id: str
    worksheet_name: str
    organization_id: int
    row_count: int
    column_count: int
    size_bytes: int
    checksum: str
    id: int | None = None
    sync_config_id: int | None = None
    created_at: datetime | None = None
    data_compressed: bytes | None = None
    headers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the snapshot (excludes data).
        """
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "sync_config_id": self.sync_config_id,
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snapshot":
        """Create Snapshot from dictionary.

        Args:
            data: Dictionary with snapshot data.

        Returns:
            Snapshot instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            organization_id=data["organization_id"],
            sync_config_id=data.get("sync_config_id"),
            sheet_id=data["sheet_id"],
            worksheet_name=data["worksheet_name"],
            created_at=created_at,
            row_count=data["row_count"],
            column_count=data["column_count"],
            size_bytes=data["size_bytes"],
            checksum=data["checksum"],
            headers=data.get("headers", []),
            data_compressed=data.get("data_compressed"),
        )

    def get_data(self) -> tuple[list[str], list[list[Any]]]:
        """Decompress and return the snapshot data.

        Returns:
            Tuple of (headers, rows).

        Raises:
            ValueError: If data is not available or corrupted.
        """
        if self.data_compressed is None:
            raise ValueError("Snapshot data not loaded")

        try:
            decompressed = zlib.decompress(self.data_compressed)
            data = json.loads(decompressed.decode("utf-8"))
            return data["headers"], data["rows"]
        except (zlib.error, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to decompress snapshot data: {e}") from e

    def verify_checksum(self) -> bool:
        """Verify the data integrity using checksum.

        Returns:
            True if checksum matches, False otherwise.
        """
        if self.data_compressed is None:
            return False

        computed = hashlib.sha256(self.data_compressed).hexdigest()
        return computed == self.checksum


class SnapshotModel(SnapshotBase):
    """SQLAlchemy model for snapshots.

    Stores compressed sheet data with indexes optimized for
    listing snapshots by sheet and time.
    """

    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, index=True)
    sync_config_id = Column(Integer, nullable=True, index=True)
    sheet_id = Column(String(100), nullable=False, index=True)
    worksheet_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    data_compressed = Column(LargeBinary, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA256 hex
    headers_json = Column(String(4000), nullable=True)  # JSON-encoded headers

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_snapshots_org_sheet", "organization_id", "sheet_id"),
        Index("ix_snapshots_sheet_created", "sheet_id", "created_at"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        headers_json_val: str | None = self.headers_json  # type: ignore[assignment]
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "sync_config_id": self.sync_config_id,
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "headers": json.loads(headers_json_val) if headers_json_val else [],
        }

    def to_dataclass(self, include_data: bool = False) -> Snapshot:
        """Convert model to Snapshot dataclass.

        Args:
            include_data: Whether to include compressed data.

        Returns:
            Snapshot instance.
        """
        # Extract actual values from Column types
        id_val: int | None = self.id  # type: ignore[assignment]
        organization_id_val: int = self.organization_id  # type: ignore[assignment]
        sync_config_id_val: int | None = self.sync_config_id  # type: ignore[assignment]
        sheet_id_val: str = self.sheet_id  # type: ignore[assignment]
        worksheet_name_val: str = self.worksheet_name  # type: ignore[assignment]
        created_at_val: datetime | None = self.created_at  # type: ignore[assignment]
        row_count_val: int = self.row_count  # type: ignore[assignment]
        column_count_val: int = self.column_count  # type: ignore[assignment]
        size_bytes_val: int = self.size_bytes  # type: ignore[assignment]
        checksum_val: str = self.checksum  # type: ignore[assignment]
        headers_json_val: str | None = self.headers_json  # type: ignore[assignment]
        data_compressed_val: bytes | None = self.data_compressed  # type: ignore[assignment]

        return Snapshot(
            id=id_val,
            organization_id=organization_id_val,
            sync_config_id=sync_config_id_val,
            sheet_id=sheet_id_val,
            worksheet_name=worksheet_name_val,
            created_at=created_at_val,
            row_count=row_count_val,
            column_count=column_count_val,
            size_bytes=size_bytes_val,
            checksum=checksum_val,
            headers=json.loads(headers_json_val) if headers_json_val else [],
            data_compressed=data_compressed_val if include_data else None,
        )

    @classmethod
    def from_dataclass(cls, snapshot: Snapshot) -> "SnapshotModel":
        """Create model from Snapshot dataclass."""
        return cls(
            id=snapshot.id,
            organization_id=snapshot.organization_id,
            sync_config_id=snapshot.sync_config_id,
            sheet_id=snapshot.sheet_id,
            worksheet_name=snapshot.worksheet_name,
            created_at=snapshot.created_at or datetime.now(tz=None),
            row_count=snapshot.row_count,
            column_count=snapshot.column_count,
            size_bytes=snapshot.size_bytes,
            data_compressed=snapshot.data_compressed,
            checksum=snapshot.checksum,
            headers_json=json.dumps(snapshot.headers) if snapshot.headers else None,
        )

    def __repr__(self) -> str:
        return (
            f"Snapshot(id={self.id}, sheet_id='{self.sheet_id}', "
            f"rows={self.row_count}, created_at={self.created_at})"
        )


class SnapshotRepository:
    """Repository for snapshot operations.

    Provides CRUD operations for snapshots with filtering
    and pagination. All queries are scoped by organization_id.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SnapshotBase.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def add(self, snapshot: Snapshot) -> Snapshot:
        """Add a new snapshot.

        Args:
            snapshot: Snapshot to create.

        Returns:
            Created Snapshot with ID and timestamp.
        """
        org_id = validate_tenant(snapshot.organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        snapshot.organization_id = org_id
        session = self._get_session()
        try:
            model = SnapshotModel.from_dataclass(snapshot)
            session.add(model)
            session.commit()
            session.refresh(model)  # Ensure model attributes are loaded
            model_id: int | None = model.id  # type: ignore[assignment]
            model_created_at: datetime | None = model.created_at  # type: ignore[assignment]
            snapshot.id = model_id
            snapshot.created_at = model_created_at
            return snapshot
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get(
        self,
        snapshot_id: int,
        organization_id: int,
        include_data: bool = False,
    ) -> Snapshot | None:
        """Get a snapshot by ID.

        Args:
            snapshot_id: Snapshot ID.
            organization_id: Organization ID for access control.
            include_data: Whether to include compressed data.

        Returns:
            Snapshot if found, None otherwise.
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            model = (
                session.query(SnapshotModel)
                .filter(SnapshotModel.id == snapshot_id)
                .filter(SnapshotModel.organization_id == org_id)
                .first()
            )
            if model:
                return model.to_dataclass(include_data=include_data)
            return None
        finally:
            session.close()

    def list(
        self,
        organization_id: int,
        sheet_id: str | None = None,
        worksheet_name: str | None = None,
        sync_config_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Snapshot]:
        """List snapshots with filters.

        Args:
            organization_id: Organization to query (required).
            sheet_id: Filter by sheet ID.
            worksheet_name: Filter by worksheet name.
            sync_config_id: Filter by sync config ID.
            limit: Maximum results (default 10).
            offset: Results to skip.

        Returns:
            List of matching snapshots (without data).
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            query = session.query(SnapshotModel).filter(
                SnapshotModel.organization_id == org_id
            )

            if sheet_id:
                query = query.filter(SnapshotModel.sheet_id == sheet_id)
            if worksheet_name:
                query = query.filter(SnapshotModel.worksheet_name == worksheet_name)
            if sync_config_id:
                query = query.filter(SnapshotModel.sync_config_id == sync_config_id)

            query = query.order_by(SnapshotModel.created_at.desc())

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass(include_data=False) for model in query.all()]
        finally:
            session.close()

    def delete(self, snapshot_id: int, organization_id: int) -> bool:
        """Delete a snapshot.

        Args:
            snapshot_id: Snapshot ID to delete.
            organization_id: Organization ID for access control.

        Returns:
            True if deleted, False if not found.
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            model = (
                session.query(SnapshotModel)
                .filter(SnapshotModel.id == snapshot_id)
                .filter(SnapshotModel.organization_id == org_id)
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

    def count(
        self,
        organization_id: int,
        sheet_id: str | None = None,
    ) -> int:
        """Count snapshots.

        Args:
            organization_id: Organization to query.
            sheet_id: Optional filter by sheet ID.

        Returns:
            Count of snapshots.
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            query = session.query(SnapshotModel).filter(
                SnapshotModel.organization_id == org_id
            )
            if sheet_id:
                query = query.filter(SnapshotModel.sheet_id == sheet_id)
            return query.count()
        finally:
            session.close()

    def get_total_size(
        self,
        organization_id: int,
        sheet_id: str | None = None,
    ) -> int:
        """Get total size of snapshots in bytes.

        Args:
            organization_id: Organization to query.
            sheet_id: Optional filter by sheet ID.

        Returns:
            Total size in bytes.
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            from sqlalchemy import func

            query = session.query(func.sum(SnapshotModel.size_bytes)).filter(
                SnapshotModel.organization_id == org_id
            )
            if sheet_id:
                query = query.filter(SnapshotModel.sheet_id == sheet_id)
            result = query.scalar()
            return int(result) if result is not None else 0
        finally:
            session.close()

    def delete_oldest(
        self,
        organization_id: int,
        sheet_id: str,
        keep_count: int,
    ) -> int:
        """Delete oldest snapshots beyond the retention count.

        Args:
            organization_id: Organization ID.
            sheet_id: Sheet ID to prune.
            keep_count: Number of snapshots to keep.

        Returns:
            Number of deleted snapshots.
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            # Find IDs to keep (most recent N)
            keep_subquery = (
                session.query(SnapshotModel.id)
                .filter(SnapshotModel.organization_id == org_id)
                .filter(SnapshotModel.sheet_id == sheet_id)
                .order_by(SnapshotModel.created_at.desc())
                .limit(keep_count)
                .scalar_subquery()
            )

            # Delete all others
            deleted_count = (
                session.query(SnapshotModel)
                .filter(SnapshotModel.organization_id == org_id)
                .filter(SnapshotModel.sheet_id == sheet_id)
                .filter(SnapshotModel.id.notin_(keep_subquery))
                .delete(synchronize_session=False)
            )

            session.commit()
            return deleted_count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_before(
        self,
        cutoff_date: datetime,
        organization_id: int | None = None,
    ) -> int:
        """Delete snapshots older than cutoff date.

        Args:
            cutoff_date: Delete snapshots older than this date.
            organization_id: Optionally scope to specific org.

        Returns:
            Number of deleted snapshots.
        """
        org_id: int | None = None
        if organization_id is not None:
            org_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(SnapshotModel).filter(SnapshotModel.created_at < cutoff_date)

            if org_id is not None:
                query = query.filter(SnapshotModel.organization_id == org_id)

            deleted_count = query.delete(synchronize_session=False)
            session.commit()
            return deleted_count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_stats(self, organization_id: int) -> dict[str, Any]:
        """Get snapshot statistics for an organization.

        Args:
            organization_id: Organization to query.

        Returns:
            Dictionary with statistics.
        """
        org_id = validate_tenant(organization_id)
        if org_id is None:
            raise ValueError("Organization ID is required")
        session = self._get_session()
        try:
            from sqlalchemy import func

            # Total count and size
            totals = (
                session.query(
                    func.count(SnapshotModel.id),
                    func.sum(SnapshotModel.size_bytes),
                )
                .filter(SnapshotModel.organization_id == org_id)
                .first()
            )

            total_count = 0
            total_size = 0
            if totals is not None:
                total_count = int(totals[0]) if totals[0] is not None else 0
                total_size = int(totals[1]) if totals[1] is not None else 0

            # Oldest and newest
            oldest = (
                session.query(func.min(SnapshotModel.created_at))
                .filter(SnapshotModel.organization_id == org_id)
                .scalar()
            )
            newest = (
                session.query(func.max(SnapshotModel.created_at))
                .filter(SnapshotModel.organization_id == org_id)
                .scalar()
            )

            # Count per sheet
            by_sheet = (
                session.query(
                    SnapshotModel.sheet_id,
                    func.count(SnapshotModel.id),
                    func.sum(SnapshotModel.size_bytes),
                )
                .filter(SnapshotModel.organization_id == org_id)
                .group_by(SnapshotModel.sheet_id)
                .all()
            )

            return {
                "total_snapshots": total_count,
                "total_size_bytes": total_size,
                "oldest_snapshot": oldest.isoformat() if oldest else None,
                "newest_snapshot": newest.isoformat() if newest else None,
                "by_sheet": {
                    sheet_id: {"count": count, "size_bytes": size or 0}
                    for sheet_id, count, size in by_sheet
                },
            }
        finally:
            session.close()


# Singleton instance
_snapshot_repository: SnapshotRepository | None = None


def get_snapshot_repository(db_path: str | None = None) -> SnapshotRepository:
    """Get or create snapshot repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        SnapshotRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _snapshot_repository
    if _snapshot_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _snapshot_repository = SnapshotRepository(db_path)
    return _snapshot_repository


def reset_snapshot_repository() -> None:
    """Reset snapshot repository singleton. For testing."""
    global _snapshot_repository
    _snapshot_repository = None
