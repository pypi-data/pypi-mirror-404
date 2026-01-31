"""Background sync execution for the desktop application.

This module provides the ability to run syncs in the background without
requiring the Flask dashboard to be open in a browser.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Status of a background sync operation."""

    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class SyncResult:
    """Result of a background sync operation."""

    status: SyncStatus
    rows_synced: int = 0
    duration_seconds: float = 0.0
    error_message: str | None = None
    error_code: str | None = None
    completed_at: datetime | None = None
    config_name: str | None = None


@dataclass
class SyncProgress:
    """Progress information for a running sync."""

    phase: str  # "connecting", "fetching", "cleaning", "pushing", "complete"
    percent: int  # 0-100
    rows_fetched: int = 0
    rows_pushed: int = 0
    total_rows: int = 0
    chunk_current: int = 0
    chunk_total: int = 0
    eta_seconds: float | None = None
    message: str = ""


@dataclass
class BackgroundSyncState:
    """State of the background sync manager."""

    current_status: SyncStatus = SyncStatus.IDLE
    last_result: SyncResult | None = None
    is_paused: bool = False
    is_offline: bool = False
    syncs_completed: int = 0
    syncs_failed: int = 0
    queued_syncs: int = 0


class BackgroundSyncManager:
    """Manages background sync operations for the desktop app.

    This class allows syncs to run without the Flask UI being open in a browser.
    It integrates with the notification system to alert users of results.
    It also subscribes to the progress emitter for real-time updates.
    """

    def __init__(
        self,
        on_sync_start: Callable[[str], None] | None = None,
        on_sync_complete: Callable[["SyncResult"], None] | None = None,
        on_status_change: Callable[["SyncStatus"], None] | None = None,
        on_progress: Callable[["SyncProgress"], None] | None = None,
    ) -> None:
        """Initialize the background sync manager.

        Args:
            on_sync_start: Callback when sync starts (receives config name).
            on_sync_complete: Callback when sync completes (receives SyncResult).
            on_status_change: Callback when status changes (receives new status).
            on_progress: Callback when progress updates (receives SyncProgress).
        """
        self._state = BackgroundSyncState()
        self._lock = threading.Lock()
        self._sync_thread: threading.Thread | None = None

        # Callbacks
        self._on_sync_start = on_sync_start
        self._on_sync_complete = on_sync_complete
        self._on_status_change = on_status_change
        self._on_progress = on_progress

        # Subscribe to progress emitter for real-time updates
        self._unsubscribe_progress: Callable[[], None] | None = None
        self._subscribe_to_emitter()

    @property
    def state(self) -> BackgroundSyncState:
        """Get current state (thread-safe copy)."""
        with self._lock:
            return BackgroundSyncState(
                current_status=self._state.current_status,
                last_result=self._state.last_result,
                is_paused=self._state.is_paused,
                is_offline=self._state.is_offline,
                syncs_completed=self._state.syncs_completed,
                syncs_failed=self._state.syncs_failed,
                queued_syncs=self._state.queued_syncs,
            )

    @property
    def is_running(self) -> bool:
        """Check if a sync is currently running."""
        return self._state.current_status == SyncStatus.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if syncs are paused."""
        return self._state.is_paused

    def _set_status(self, status: SyncStatus) -> None:
        """Set status and trigger callback."""
        with self._lock:
            self._state.current_status = status
        if self._on_status_change:
            try:
                self._on_status_change(status)
            except Exception as e:
                logger.warning(f"Status change callback failed: {e}")

    def _subscribe_to_emitter(self) -> None:
        """Subscribe to the global progress emitter for real-time updates."""
        try:
            from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

            emitter = get_progress_emitter()
            self._unsubscribe_progress = emitter.subscribe_callback(
                self._handle_emitter_event
            )
        except Exception as e:
            logger.debug(f"Could not subscribe to progress emitter: {e}")

    def _handle_emitter_event(self, event: dict[str, Any]) -> None:
        """Handle events from the progress emitter.

        Args:
            event: Event dictionary with 'type' and 'data' keys.
        """
        event_type = event.get("type")
        data = event.get("data", {})

        if event_type == "progress" and self._on_progress:
            progress = SyncProgress(
                phase=data.get("phase", ""),
                percent=data.get("percent", 0),
                rows_fetched=data.get("rows_fetched", 0),
                rows_pushed=data.get("rows_pushed", 0),
                total_rows=data.get("total_rows", 0),
                chunk_current=data.get("chunk_current", 0),
                chunk_total=data.get("chunk_total", 0),
                eta_seconds=data.get("eta_seconds"),
                message=data.get("message", ""),
            )
            try:
                self._on_progress(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def _report_progress(self, progress: SyncProgress) -> None:
        """Report progress and trigger callback."""
        if self._on_progress:
            try:
                self._on_progress(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def pause(self) -> None:
        """Pause background syncs (scheduled syncs won't start)."""
        with self._lock:
            self._state.is_paused = True
        logger.info("Background syncs paused")

    def resume(self) -> None:
        """Resume background syncs."""
        with self._lock:
            self._state.is_paused = False
        logger.info("Background syncs resumed")

    def run_sync(
        self,
        config_id: int | None = None,
        config_name: str = "Default",
        sync_options: dict[str, Any] | None = None,
        queue_if_offline: bool = True,
    ) -> bool:
        """Start a sync operation in the background.

        Args:
            config_id: Optional sync configuration ID to use.
            config_name: Display name for the sync.
            sync_options: Additional options to pass to sync.
            queue_if_offline: If True, queue sync when offline instead of failing.

        Returns:
            True if sync was started or queued, False if already running or paused.
        """
        if self.is_running:
            logger.warning("Sync already running, ignoring request")
            return False

        if self.is_paused:
            logger.warning("Syncs are paused, ignoring request")
            return False

        # Queue sync if offline
        if self.is_offline and queue_if_offline:
            logger.info(f"Offline - queuing sync: {config_name}")
            queue_id = self.queue_sync(
                config_id=config_id,
                config_name=config_name,
                sync_options=sync_options,
            )
            return queue_id is not None

        def _run_sync() -> None:
            self._set_status(SyncStatus.RUNNING)

            if self._on_sync_start:
                try:
                    self._on_sync_start(config_name)
                except Exception as e:
                    logger.warning(f"Sync start callback failed: {e}")

            start_time = time.time()
            result = SyncResult(
                status=SyncStatus.RUNNING,
                config_name=config_name,
            )

            try:
                # Phase 1: Connecting
                self._report_progress(SyncProgress(
                    phase="connecting",
                    percent=10,
                    message="Loading configuration...",
                ))

                # Import here to avoid circular imports
                from mysql_to_sheets.core.config import get_config
                from mysql_to_sheets.core.sync import run_sync

                config = get_config()

                # Apply any overrides from sync_options
                if sync_options:
                    config = config.with_overrides(**sync_options)

                # Phase 2: Fetching
                self._report_progress(SyncProgress(
                    phase="fetching",
                    percent=30,
                    message="Connecting to database...",
                ))

                # Phase 3: Pushing (reported before sync starts)
                self._report_progress(SyncProgress(
                    phase="pushing",
                    percent=50,
                    message="Syncing data to Google Sheets...",
                ))

                sync_result = run_sync(config)

                # Phase 4: Complete
                self._report_progress(SyncProgress(
                    phase="complete",
                    percent=100,
                    rows_pushed=sync_result.rows_synced,
                    message=f"Synced {sync_result.rows_synced:,} rows",
                ))

                duration = time.time() - start_time
                result = SyncResult(
                    status=SyncStatus.SUCCESS if sync_result.success else SyncStatus.FAILED,
                    rows_synced=sync_result.rows_synced,
                    duration_seconds=duration,
                    error_message=sync_result.error if not sync_result.success else None,
                    completed_at=datetime.now(),
                    config_name=config_name,
                )

                if sync_result.success:
                    with self._lock:
                        self._state.syncs_completed += 1
                else:
                    with self._lock:
                        self._state.syncs_failed += 1

            except Exception as e:
                duration = time.time() - start_time
                error_code = None
                error_message = str(e)

                # Extract error code if it's a SyncError
                if hasattr(e, "code"):
                    error_code = e.code

                result = SyncResult(
                    status=SyncStatus.FAILED,
                    duration_seconds=duration,
                    error_message=error_message,
                    error_code=error_code,
                    completed_at=datetime.now(),
                    config_name=config_name,
                )

                with self._lock:
                    self._state.syncs_failed += 1

                logger.error(f"Background sync failed: {e}")

            # Update state and trigger callbacks
            with self._lock:
                self._state.last_result = result
                self._state.current_status = result.status

            if self._on_sync_complete:
                try:
                    self._on_sync_complete(result)
                except Exception as e:
                    logger.warning(f"Sync complete callback failed: {e}")

        self._sync_thread = threading.Thread(target=_run_sync, daemon=True)
        self._sync_thread.start()
        return True

    def get_last_result_summary(self) -> str:
        """Get a human-readable summary of the last sync result.

        Returns:
            Summary string for display in tray menu.
        """
        result = self._state.last_result
        if result is None:
            return "No syncs run yet"

        if result.status == SyncStatus.SUCCESS:
            return (
                f"Last sync: {result.rows_synced:,} rows "
                f"({result.duration_seconds:.1f}s)"
            )
        elif result.status == SyncStatus.FAILED:
            error_info = result.error_code or "Error"
            return f"Last sync failed: {error_info}"
        else:
            return f"Status: {result.status.value}"

    def set_offline(self, is_offline: bool) -> None:
        """Set offline state.

        Args:
            is_offline: Whether the app is offline.
        """
        with self._lock:
            self._state.is_offline = is_offline

    @property
    def is_offline(self) -> bool:
        """Check if app is offline."""
        return self._state.is_offline

    def queue_sync(
        self,
        config_id: int | None = None,
        config_name: str = "Default",
        sync_options: dict[str, Any] | None = None,
        priority: int = 0,
    ) -> int | None:
        """Queue a sync for later execution (when online).

        Args:
            config_id: Optional sync configuration ID.
            config_name: Display name for the sync.
            sync_options: Options to pass to sync.
            priority: Higher = processed first.

        Returns:
            Queue entry ID, or None if queueing failed.
        """
        try:
            from mysql_to_sheets.models.offline_queue import (
                QueuedSync,
                get_offline_queue_repository,
            )

            repo = get_offline_queue_repository()
            queued = QueuedSync(
                config_id=config_id,
                config_name=config_name,
                sync_options=sync_options or {},
                priority=priority,
            )
            queued = repo.enqueue(queued)

            with self._lock:
                self._state.queued_syncs = repo.count_pending()

            logger.info(f"Sync queued for offline execution: {config_name}")
            return queued.id

        except Exception as e:
            logger.error(f"Failed to queue sync: {e}")
            return None

    def get_queued_count(self) -> int:
        """Get number of queued syncs.

        Returns:
            Number of pending syncs in queue.
        """
        try:
            from mysql_to_sheets.models.offline_queue import get_offline_queue_repository

            repo = get_offline_queue_repository()
            return repo.count_pending()
        except Exception:
            return 0

    def process_offline_queue(self) -> int:
        """Process all pending syncs in the offline queue.

        Called when connectivity is restored.

        Returns:
            Number of syncs processed (successful or failed).
        """
        try:
            from mysql_to_sheets.models.offline_queue import get_offline_queue_repository

            repo = get_offline_queue_repository()
            processed = 0

            while True:
                # Get next pending sync
                queued = repo.get_next()
                if not queued:
                    break

                if queued.id is None:
                    continue

                logger.info(f"Processing queued sync: {queued.config_name}")
                repo.mark_processing(queued.id)

                try:
                    # Run the sync
                    from mysql_to_sheets.core.config import get_config
                    from mysql_to_sheets.core.sync import run_sync

                    config = get_config()
                    if queued.sync_options:
                        config = config.with_overrides(**queued.sync_options)

                    result = run_sync(config)

                    if result.success:
                        repo.mark_completed(queued.id)
                        with self._lock:
                            self._state.syncs_completed += 1
                    else:
                        repo.mark_failed(queued.id, result.error or "Unknown error")
                        with self._lock:
                            self._state.syncs_failed += 1

                    processed += 1

                except Exception as e:
                    repo.mark_failed(queued.id, str(e))
                    with self._lock:
                        self._state.syncs_failed += 1
                    processed += 1
                    logger.error(f"Queued sync failed: {e}")

            # Update queue count
            with self._lock:
                self._state.queued_syncs = repo.count_pending()

            if processed > 0:
                logger.info(f"Processed {processed} queued syncs")

            return processed

        except Exception as e:
            logger.error(f"Failed to process offline queue: {e}")
            return 0


# Global manager instance
_manager: BackgroundSyncManager | None = None


def get_background_manager(
    on_sync_start: Callable[[str], None] | None = None,
    on_sync_complete: Callable[[SyncResult], None] | None = None,
    on_status_change: Callable[[SyncStatus], None] | None = None,
    on_progress: Callable[[SyncProgress], None] | None = None,
) -> BackgroundSyncManager:
    """Get the global background sync manager.

    Args:
        on_sync_start: Callback when sync starts.
        on_sync_complete: Callback when sync completes.
        on_status_change: Callback when status changes.
        on_progress: Callback when progress updates.

    Returns:
        The global BackgroundSyncManager instance.
    """
    global _manager
    if _manager is None:
        _manager = BackgroundSyncManager(
            on_sync_start=on_sync_start,
            on_sync_complete=on_sync_complete,
            on_status_change=on_status_change,
            on_progress=on_progress,
        )
    return _manager
