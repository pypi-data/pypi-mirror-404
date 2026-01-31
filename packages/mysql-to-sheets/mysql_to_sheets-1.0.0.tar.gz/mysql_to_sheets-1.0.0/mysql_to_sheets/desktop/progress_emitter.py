"""Thread-safe progress event emitter for real-time sync tracking.

This module provides a progress emitter that broadcasts sync progress events
to multiple subscribers. It supports Server-Sent Events (SSE) streaming
and local callbacks.
"""

import logging
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Generator

logger = logging.getLogger(__name__)


class SyncPhase(Enum):
    """Phases of a sync operation."""

    CONNECTING = "connecting"
    FETCHING = "fetching"
    CLEANING = "cleaning"
    PUSHING = "pushing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ProgressEvent:
    """A sync progress event."""

    sync_id: str
    phase: SyncPhase
    percent: int  # 0-100
    message: str = ""
    rows_fetched: int = 0
    rows_pushed: int = 0
    total_rows: int = 0
    chunk_current: int = 0
    chunk_total: int = 0
    eta_seconds: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sync_id": self.sync_id,
            "phase": self.phase.value,
            "percent": self.percent,
            "message": self.message,
            "rows_fetched": self.rows_fetched,
            "rows_pushed": self.rows_pushed,
            "total_rows": self.total_rows,
            "chunk_current": self.chunk_current,
            "chunk_total": self.chunk_total,
            "eta_seconds": self.eta_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LogEvent:
    """A sync log entry."""

    sync_id: str
    level: str  # "info", "warning", "error", "debug"
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sync_id": self.sync_id,
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CompleteEvent:
    """A sync completion event."""

    sync_id: str
    success: bool
    rows_synced: int = 0
    duration_seconds: float = 0.0
    error_message: str | None = None
    error_code: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sync_id": self.sync_id,
            "success": self.success,
            "rows_synced": self.rows_synced,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
        }


class SyncProgressEmitter:
    """Thread-safe progress event emitter.

    Supports multiple subscribers via:
    - Local callbacks (for desktop status window)
    - SSE event queues (for web dashboard)

    ETA calculation uses a moving average of the last 10 chunk processing times.
    """

    def __init__(self) -> None:
        """Initialize the progress emitter."""
        self._lock = threading.Lock()

        # Subscribers
        self._callbacks: list[Callable[[Any], None]] = []
        self._sse_queues: dict[str, queue.Queue] = {}

        # ETA calculation state (per sync_id)
        self._chunk_times: dict[str, deque[float]] = {}
        self._last_chunk_time: dict[str, float] = {}

        # Current state per sync
        self._current_progress: dict[str, ProgressEvent] = {}
        self._sync_logs: dict[str, list[LogEvent]] = {}

    def subscribe_callback(
        self, callback: Callable[[Any], None]
    ) -> Callable[[], None]:
        """Subscribe a callback to receive events.

        Args:
            callback: Function to call with each event.

        Returns:
            Unsubscribe function.
        """
        with self._lock:
            self._callbacks.append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._callbacks:
                    self._callbacks.remove(callback)

        return unsubscribe

    def create_sse_queue(self, client_id: str) -> queue.Queue:
        """Create a new SSE event queue for a client.

        Args:
            client_id: Unique identifier for the SSE client.

        Returns:
            Queue that will receive serialized events.
        """
        with self._lock:
            q: queue.Queue = queue.Queue(maxsize=100)
            self._sse_queues[client_id] = q
            return q

    def remove_sse_queue(self, client_id: str) -> None:
        """Remove an SSE queue when client disconnects.

        Args:
            client_id: The client ID to remove.
        """
        with self._lock:
            if client_id in self._sse_queues:
                del self._sse_queues[client_id]

    def _broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast event to all subscribers.

        Args:
            event_type: Type of event ("progress", "log", "complete").
            data: Event data dictionary.
        """
        with self._lock:
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback({"type": event_type, "data": data})
                except Exception as e:
                    logger.debug(f"Callback error: {e}")

            # Add to SSE queues
            event = {"type": event_type, "data": data}
            for client_id, q in list(self._sse_queues.items()):
                try:
                    q.put_nowait(event)
                except queue.Full:
                    logger.warning(f"SSE queue full for client {client_id}")

    def emit_progress(
        self,
        sync_id: str,
        phase: SyncPhase,
        percent: int,
        message: str = "",
        rows_fetched: int = 0,
        rows_pushed: int = 0,
        total_rows: int = 0,
        chunk_current: int = 0,
        chunk_total: int = 0,
    ) -> None:
        """Emit a progress event.

        Args:
            sync_id: Unique sync operation ID.
            phase: Current sync phase.
            percent: Progress percentage (0-100).
            message: Human-readable status message.
            rows_fetched: Rows fetched from database.
            rows_pushed: Rows pushed to sheets.
            total_rows: Total rows to process.
            chunk_current: Current chunk number (for streaming).
            chunk_total: Total chunks (for streaming).
        """
        # Calculate ETA for streaming mode
        eta_seconds = None
        if chunk_total > 0 and chunk_current > 0:
            eta_seconds = self._calculate_eta(sync_id, chunk_current, chunk_total)

        event = ProgressEvent(
            sync_id=sync_id,
            phase=phase,
            percent=min(100, max(0, percent)),
            message=message,
            rows_fetched=rows_fetched,
            rows_pushed=rows_pushed,
            total_rows=total_rows,
            chunk_current=chunk_current,
            chunk_total=chunk_total,
            eta_seconds=eta_seconds,
        )

        with self._lock:
            self._current_progress[sync_id] = event

        self._broadcast("progress", event.to_dict())
        logger.debug(f"[{sync_id}] Progress: {phase.value} {percent}% - {message}")

    def emit_log(
        self,
        sync_id: str,
        level: str,
        message: str,
    ) -> None:
        """Emit a log event.

        Args:
            sync_id: Unique sync operation ID.
            level: Log level ("info", "warning", "error", "debug").
            message: Log message.
        """
        event = LogEvent(
            sync_id=sync_id,
            level=level,
            message=message,
        )

        with self._lock:
            if sync_id not in self._sync_logs:
                self._sync_logs[sync_id] = []
            self._sync_logs[sync_id].append(event)
            # Keep last 100 logs per sync
            if len(self._sync_logs[sync_id]) > 100:
                self._sync_logs[sync_id] = self._sync_logs[sync_id][-100:]

        self._broadcast("log", event.to_dict())

    def emit_complete(
        self,
        sync_id: str,
        success: bool,
        rows_synced: int = 0,
        duration_seconds: float = 0.0,
        error_message: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Emit a completion event.

        Args:
            sync_id: Unique sync operation ID.
            success: Whether sync completed successfully.
            rows_synced: Total rows synced.
            duration_seconds: Total duration in seconds.
            error_message: Error message if failed.
            error_code: Error code if failed.
        """
        event = CompleteEvent(
            sync_id=sync_id,
            success=success,
            rows_synced=rows_synced,
            duration_seconds=duration_seconds,
            error_message=error_message,
            error_code=error_code,
        )

        # Cleanup ETA state
        with self._lock:
            self._chunk_times.pop(sync_id, None)
            self._last_chunk_time.pop(sync_id, None)

        self._broadcast("complete", event.to_dict())
        logger.debug(
            f"[{sync_id}] Complete: success={success}, rows={rows_synced}, "
            f"duration={duration_seconds:.2f}s"
        )

    def record_chunk_time(self, sync_id: str) -> None:
        """Record the completion time of a chunk for ETA calculation.

        Call this after each chunk is processed in streaming mode.

        Args:
            sync_id: Unique sync operation ID.
        """
        current_time = time.time()
        with self._lock:
            if sync_id not in self._chunk_times:
                self._chunk_times[sync_id] = deque(maxlen=10)

            last_time = self._last_chunk_time.get(sync_id)
            if last_time is not None:
                chunk_duration = current_time - last_time
                self._chunk_times[sync_id].append(chunk_duration)

            self._last_chunk_time[sync_id] = current_time

    def _calculate_eta(
        self, sync_id: str, chunk_current: int, chunk_total: int
    ) -> float | None:
        """Calculate estimated time remaining based on moving average.

        Args:
            sync_id: Unique sync operation ID.
            chunk_current: Current chunk number.
            chunk_total: Total number of chunks.

        Returns:
            Estimated seconds remaining, or None if not enough data.
        """
        with self._lock:
            times = self._chunk_times.get(sync_id)
            if not times or len(times) < 2:
                return None

            # Calculate moving average of last 10 chunks
            avg_time = sum(times) / len(times)
            remaining_chunks = chunk_total - chunk_current
            return avg_time * remaining_chunks

    def get_current_progress(self, sync_id: str) -> ProgressEvent | None:
        """Get current progress for a sync operation.

        Args:
            sync_id: Unique sync operation ID.

        Returns:
            Current progress event or None.
        """
        with self._lock:
            return self._current_progress.get(sync_id)

    def get_logs(self, sync_id: str) -> list[LogEvent]:
        """Get logs for a sync operation.

        Args:
            sync_id: Unique sync operation ID.

        Returns:
            List of log events.
        """
        with self._lock:
            return list(self._sync_logs.get(sync_id, []))

    def sse_stream(
        self, client_id: str, timeout: float = 30.0
    ) -> Generator[str, None, None]:
        """Generate SSE event stream for a client.

        Args:
            client_id: Unique client identifier.
            timeout: Seconds to wait for events before sending keepalive.

        Yields:
            SSE-formatted event strings.
        """
        import json

        q = self.create_sse_queue(client_id)
        try:
            while True:
                try:
                    event = q.get(timeout=timeout)
                    event_type = event.get("type", "message")
                    data = json.dumps(event.get("data", {}))
                    yield f"event: {event_type}\ndata: {data}\n\n"
                except queue.Empty:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
        finally:
            self.remove_sse_queue(client_id)

    def cleanup(self, sync_id: str) -> None:
        """Clean up state for a completed sync.

        Args:
            sync_id: Unique sync operation ID.
        """
        with self._lock:
            self._current_progress.pop(sync_id, None)
            self._sync_logs.pop(sync_id, None)
            self._chunk_times.pop(sync_id, None)
            self._last_chunk_time.pop(sync_id, None)


# Global emitter instance
_emitter: SyncProgressEmitter | None = None


def get_progress_emitter() -> SyncProgressEmitter:
    """Get the global progress emitter instance.

    Returns:
        The global SyncProgressEmitter instance.
    """
    global _emitter
    if _emitter is None:
        _emitter = SyncProgressEmitter()
    return _emitter


def reset_progress_emitter() -> None:
    """Reset the global progress emitter. For testing."""
    global _emitter
    _emitter = None
