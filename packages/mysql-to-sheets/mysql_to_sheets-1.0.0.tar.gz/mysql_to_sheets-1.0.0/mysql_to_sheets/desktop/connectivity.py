"""Connectivity monitoring for offline mode support.

This module provides connectivity monitoring for database and Google Sheets
API access. It enables queuing syncs when offline and auto-execution when
connectivity is restored.
"""

import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


class ConnectivityState(Enum):
    """Network connectivity states."""

    ONLINE = "online"  # Both database and Sheets accessible
    OFFLINE = "offline"  # Neither accessible
    PARTIAL_DB_ONLY = "partial_db_only"  # Database accessible, Sheets not
    PARTIAL_SHEETS_ONLY = "partial_sheets_only"  # Sheets accessible, database not
    UNKNOWN = "unknown"  # Not yet checked


@dataclass
class ConnectivityStatus:
    """Detailed connectivity status."""

    state: ConnectivityState
    database_reachable: bool = False
    sheets_reachable: bool = False
    database_latency_ms: float | None = None
    sheets_latency_ms: float | None = None
    last_check_time: float | None = None
    error_message: str | None = None

    @property
    def is_fully_online(self) -> bool:
        """Check if both database and Sheets are reachable."""
        return self.state == ConnectivityState.ONLINE

    @property
    def can_sync(self) -> bool:
        """Check if syncing is possible (both services reachable)."""
        return self.database_reachable and self.sheets_reachable


class ConnectivityMonitor:
    """Monitors connectivity to database and Google Sheets.

    Features:
    - Periodic connectivity checks (configurable interval)
    - State change callbacks for UI updates
    - Latency tracking for health monitoring
    - Graceful handling of transient failures
    """

    def __init__(
        self,
        check_interval_seconds: float = 30.0,
        on_state_change: Callable[[ConnectivityState, ConnectivityState], None] | None = None,
        on_online: Callable[[], None] | None = None,
        on_offline: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the connectivity monitor.

        Args:
            check_interval_seconds: Seconds between connectivity checks.
            on_state_change: Callback when state changes (old_state, new_state).
            on_online: Callback when connectivity is restored.
            on_offline: Callback when connectivity is lost.
        """
        self._check_interval = check_interval_seconds
        self._on_state_change = on_state_change
        self._on_online = on_online
        self._on_offline = on_offline

        self._current_status = ConnectivityStatus(state=ConnectivityState.UNKNOWN)
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

        # Consecutive failure tracking for debouncing
        self._consecutive_failures = 0
        self._failure_threshold = 2  # Require 2 consecutive failures to go offline

    @property
    def status(self) -> ConnectivityStatus:
        """Get current connectivity status."""
        with self._lock:
            return self._current_status

    @property
    def state(self) -> ConnectivityState:
        """Get current connectivity state."""
        return self._current_status.state

    @property
    def is_online(self) -> bool:
        """Check if fully online."""
        return self._current_status.is_fully_online

    def _check_database_connectivity(self) -> tuple[bool, float | None, str | None]:
        """Check if database is reachable.

        Returns:
            Tuple of (reachable, latency_ms, error_message).
        """
        try:
            from mysql_to_sheets.core.config import get_config
            from mysql_to_sheets.core.database import get_connection

            config = get_config()
            start_time = time.time()

            # Try to establish connection and run simple query
            conn = get_connection(config)
            try:
                conn.execute_query("SELECT 1")
                latency = (time.time() - start_time) * 1000
                return True, latency, None
            finally:
                conn.close()

        except Exception as e:
            logger.debug(f"Database connectivity check failed: {e}")
            return False, None, str(e)

    def _check_sheets_connectivity(self) -> tuple[bool, float | None, str | None]:
        """Check if Google Sheets API is reachable.

        Returns:
            Tuple of (reachable, latency_ms, error_message).
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            from mysql_to_sheets.core.config import get_config

            config = get_config()
            start_time = time.time()

            # Load credentials and try to open a sheet
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.metadata.readonly",
            ]
            credentials = Credentials.from_service_account_file(
                config.service_account_file, scopes=scopes
            )
            client = gspread.authorize(credentials)

            # Try to open the configured sheet (read-only operation)
            if config.google_sheet_id:
                client.open_by_key(config.google_sheet_id)
                latency = (time.time() - start_time) * 1000
                return True, latency, None
            else:
                # No sheet configured, just check API is reachable
                client.list_spreadsheet_files(page_size=1)
                latency = (time.time() - start_time) * 1000
                return True, latency, None

        except Exception as e:
            logger.debug(f"Sheets connectivity check failed: {e}")
            return False, None, str(e)

    def check_now(self) -> ConnectivityStatus:
        """Perform an immediate connectivity check.

        Returns:
            Updated ConnectivityStatus.
        """
        db_ok, db_latency, db_error = self._check_database_connectivity()
        sheets_ok, sheets_latency, sheets_error = self._check_sheets_connectivity()

        # Determine state
        if db_ok and sheets_ok:
            state = ConnectivityState.ONLINE
        elif db_ok and not sheets_ok:
            state = ConnectivityState.PARTIAL_DB_ONLY
        elif not db_ok and sheets_ok:
            state = ConnectivityState.PARTIAL_SHEETS_ONLY
        else:
            state = ConnectivityState.OFFLINE

        # Build error message
        errors = []
        if db_error:
            errors.append(f"Database: {db_error}")
        if sheets_error:
            errors.append(f"Sheets: {sheets_error}")
        error_message = "; ".join(errors) if errors else None

        new_status = ConnectivityStatus(
            state=state,
            database_reachable=db_ok,
            sheets_reachable=sheets_ok,
            database_latency_ms=db_latency,
            sheets_latency_ms=sheets_latency,
            last_check_time=time.time(),
            error_message=error_message,
        )

        # Handle state transition
        old_status = self._current_status
        with self._lock:
            self._current_status = new_status

        self._handle_state_transition(old_status.state, new_status.state)

        return new_status

    def _handle_state_transition(
        self, old_state: ConnectivityState, new_state: ConnectivityState
    ) -> None:
        """Handle state transitions with debouncing.

        Args:
            old_state: Previous state.
            new_state: New state.
        """
        # Debounce offline transitions
        if new_state in (ConnectivityState.OFFLINE, ConnectivityState.PARTIAL_DB_ONLY, ConnectivityState.PARTIAL_SHEETS_ONLY):
            self._consecutive_failures += 1
            if self._consecutive_failures < self._failure_threshold:
                logger.debug(
                    f"Connectivity check failed ({self._consecutive_failures}/{self._failure_threshold})"
                )
                return  # Don't trigger callbacks yet
        else:
            self._consecutive_failures = 0

        # Trigger callbacks on actual state change
        if old_state != new_state:
            logger.info(f"Connectivity state changed: {old_state.value} -> {new_state.value}")

            if self._on_state_change:
                try:
                    self._on_state_change(old_state, new_state)
                except Exception as e:
                    logger.warning(f"State change callback failed: {e}")

            # Specific callbacks
            if new_state == ConnectivityState.ONLINE and old_state != ConnectivityState.ONLINE:
                if self._on_online:
                    try:
                        self._on_online()
                    except Exception as e:
                        logger.warning(f"Online callback failed: {e}")

            elif new_state != ConnectivityState.ONLINE and old_state == ConnectivityState.ONLINE:
                if self._on_offline:
                    try:
                        self._on_offline()
                    except Exception as e:
                        logger.warning(f"Offline callback failed: {e}")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        logger.info(f"Connectivity monitor started (interval: {self._check_interval}s)")

        while self._running:
            try:
                self.check_now()
            except Exception as e:
                logger.warning(f"Connectivity check error: {e}")

            # Sleep in small increments for responsive shutdown
            sleep_time = 0.0
            while sleep_time < self._check_interval and self._running:
                time.sleep(1.0)
                sleep_time += 1.0

        logger.info("Connectivity monitor stopped")

    def start(self) -> None:
        """Start the background connectivity monitor."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="connectivity-monitor"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the background connectivity monitor."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)


# Global monitor instance
_monitor: ConnectivityMonitor | None = None


def get_connectivity_monitor(
    check_interval_seconds: float = 30.0,
    on_state_change: Callable[[ConnectivityState, ConnectivityState], None] | None = None,
    on_online: Callable[[], None] | None = None,
    on_offline: Callable[[], None] | None = None,
) -> ConnectivityMonitor:
    """Get or create the global connectivity monitor.

    Args:
        check_interval_seconds: Check interval (used on first call).
        on_state_change: State change callback.
        on_online: Online callback.
        on_offline: Offline callback.

    Returns:
        Global ConnectivityMonitor instance.
    """
    global _monitor
    if _monitor is None:
        _monitor = ConnectivityMonitor(
            check_interval_seconds=check_interval_seconds,
            on_state_change=on_state_change,
            on_online=on_online,
            on_offline=on_offline,
        )
    return _monitor


def reset_connectivity_monitor() -> None:
    """Reset the global monitor. For testing."""
    global _monitor
    if _monitor:
        _monitor.stop()
    _monitor = None
