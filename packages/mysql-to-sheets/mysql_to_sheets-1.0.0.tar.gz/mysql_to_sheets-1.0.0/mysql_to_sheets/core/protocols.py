"""Protocol interfaces for clean module boundaries.

Defines structural typing protocols that allow extractable modules
(tla-errors, tla-retry, tla-sql-guard, etc.) to depend on interfaces
rather than concrete implementations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SyncConfigProtocol(Protocol):
    """Minimal configuration interface for sync operations.

    Modules that need database and sheet configuration can depend on this
    protocol instead of the concrete ``Config`` dataclass, enabling cleaner
    extraction into standalone packages.
    """

    db_type: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    sql_query: str
    google_sheet_id: str
