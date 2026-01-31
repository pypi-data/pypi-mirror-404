"""Distributed locks for scheduler job execution.

Prevents multiple scheduler instances from executing the same job
concurrently. Supports SQLite and Redis backends.
"""

import os
import socket
import threading
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generator

from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)

# Default lock TTL in seconds (5 minutes)
DEFAULT_LOCK_TTL_SECONDS = 300

# Default heartbeat interval in seconds
DEFAULT_HEARTBEAT_INTERVAL = 30


@dataclass
class LockInfo:
    """Information about an acquired lock.

    Attributes:
        job_id: The job ID this lock is for.
        lock_id: Unique identifier for this lock acquisition.
        holder: Identifier of the lock holder (worker ID).
        acquired_at: When the lock was acquired.
        expires_at: When the lock expires.
    """

    job_id: int
    lock_id: str
    holder: str
    acquired_at: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if this lock has expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)


def _generate_lock_id() -> str:
    """Generate a unique lock identifier."""
    return uuid.uuid4().hex[:16]


def _get_worker_id() -> str:
    """Get the current worker identifier."""
    worker_id = os.getenv("WORKER_ID")
    if worker_id:
        return worker_id
    return f"{socket.gethostname()}-{os.getpid()}"


class SchedulerLockBackend(ABC):
    """Abstract base class for scheduler lock backends."""

    @abstractmethod
    def acquire(
        self,
        job_id: int,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> LockInfo | None:
        """Attempt to acquire a lock for a job.

        Args:
            job_id: The job ID to lock.
            ttl_seconds: Lock time-to-live in seconds.

        Returns:
            LockInfo if lock acquired, None if already locked.
        """
        pass

    @abstractmethod
    def release(self, job_id: int, lock_id: str) -> bool:
        """Release a lock.

        Args:
            job_id: The job ID to unlock.
            lock_id: The lock ID (must match the acquired lock).

        Returns:
            True if released, False if lock not held or wrong lock_id.
        """
        pass

    @abstractmethod
    def extend(
        self,
        job_id: int,
        lock_id: str,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> bool:
        """Extend a lock's TTL.

        Args:
            job_id: The job ID.
            lock_id: The lock ID (must match the acquired lock).
            ttl_seconds: New TTL from now.

        Returns:
            True if extended, False if lock not held or wrong lock_id.
        """
        pass

    @abstractmethod
    def get_lock_info(self, job_id: int) -> LockInfo | None:
        """Get information about a lock.

        Args:
            job_id: The job ID to check.

        Returns:
            LockInfo if locked, None if not locked.
        """
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Clean up expired locks.

        Returns:
            Number of locks cleaned up.
        """
        pass


class SQLiteSchedulerLockBackend(SchedulerLockBackend):
    """SQLite-based scheduler lock backend.

    Uses SQLite's EXCLUSIVE transaction for lock acquisition,
    ensuring only one process can acquire the lock at a time.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize the SQLite lock backend.

        Args:
            db_path: Path to the SQLite database.
        """
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure the scheduler_locks table exists."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduler_locks (
                    job_id INTEGER PRIMARY KEY,
                    lock_id TEXT NOT NULL,
                    holder TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scheduler_locks_expires
                ON scheduler_locks(expires_at)
            """)
            conn.commit()
        finally:
            conn.close()

    def acquire(
        self,
        job_id: int,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> LockInfo | None:
        """Acquire a lock using SQLite EXCLUSIVE transaction."""
        import sqlite3

        lock_id = _generate_lock_id()
        holder = _get_worker_id()
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)

        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            # Use EXCLUSIVE to prevent concurrent access
            conn.execute("BEGIN EXCLUSIVE")

            # Check for existing lock
            cursor = conn.execute(
                "SELECT lock_id, holder, acquired_at, expires_at FROM scheduler_locks WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()

            if row:
                existing_expires = datetime.fromisoformat(row[3].replace("Z", "+00:00"))
                if existing_expires.tzinfo is None:
                    existing_expires = existing_expires.replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) < existing_expires:
                    # Lock is still valid
                    conn.rollback()
                    logger.debug(f"Job {job_id} already locked by {row[1]}")
                    return None

                # Lock expired, delete it
                conn.execute("DELETE FROM scheduler_locks WHERE job_id = ?", (job_id,))

            # Insert new lock
            conn.execute(
                """
                INSERT INTO scheduler_locks (job_id, lock_id, holder, acquired_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    lock_id,
                    holder,
                    now.isoformat(),
                    expires_at.isoformat(),
                ),
            )
            conn.commit()

            logger.debug(f"Acquired lock for job {job_id} (lock_id={lock_id})")
            return LockInfo(
                job_id=job_id,
                lock_id=lock_id,
                holder=holder,
                acquired_at=now,
                expires_at=expires_at,
            )

        except sqlite3.OperationalError as e:
            conn.rollback()
            logger.debug(f"Failed to acquire lock for job {job_id}: {e}")
            return None
        finally:
            conn.close()

    def release(self, job_id: int, lock_id: str) -> bool:
        """Release a lock."""
        import sqlite3

        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            cursor = conn.execute(
                "DELETE FROM scheduler_locks WHERE job_id = ? AND lock_id = ?",
                (job_id, lock_id),
            )
            conn.commit()
            released = cursor.rowcount > 0
            if released:
                logger.debug(f"Released lock for job {job_id}")
            return released
        finally:
            conn.close()

    def extend(
        self,
        job_id: int,
        lock_id: str,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> bool:
        """Extend a lock's TTL."""
        import sqlite3

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)

        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            cursor = conn.execute(
                "UPDATE scheduler_locks SET expires_at = ? WHERE job_id = ? AND lock_id = ?",
                (expires_at.isoformat(), job_id, lock_id),
            )
            conn.commit()
            extended = cursor.rowcount > 0
            if extended:
                logger.debug(f"Extended lock for job {job_id}")
            return extended
        finally:
            conn.close()

    def get_lock_info(self, job_id: int) -> LockInfo | None:
        """Get lock information."""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT lock_id, holder, acquired_at, expires_at FROM scheduler_locks WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            acquired_at = datetime.fromisoformat(row[2].replace("Z", "+00:00"))
            expires_at = datetime.fromisoformat(row[3].replace("Z", "+00:00"))

            if acquired_at.tzinfo is None:
                acquired_at = acquired_at.replace(tzinfo=timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            return LockInfo(
                job_id=job_id,
                lock_id=row[0],
                holder=row[1],
                acquired_at=acquired_at,
                expires_at=expires_at,
            )
        finally:
            conn.close()

    def cleanup_expired(self) -> int:
        """Clean up expired locks."""
        import sqlite3

        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            cursor = conn.execute(
                "DELETE FROM scheduler_locks WHERE expires_at < ?",
                (now,),
            )
            conn.commit()
            count = cursor.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired scheduler lock(s)")
            return count
        finally:
            conn.close()


class RedisSchedulerLockBackend(SchedulerLockBackend):
    """Redis-based scheduler lock backend.

    Uses Redis SETNX for atomic lock acquisition with TTL.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """Initialize the Redis lock backend.

        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis

                self._client = redis.from_url(self.redis_url)
            except ImportError as e:
                raise ImportError(
                    "Redis is required for distributed locks. Install with: pip install redis"
                ) from e
        return self._client

    def _lock_key(self, job_id: int) -> str:
        """Get the Redis key for a job lock."""
        return f"scheduler:lock:{job_id}"

    def acquire(
        self,
        job_id: int,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> LockInfo | None:
        """Acquire a lock using Redis SETNX."""
        import json

        client = self._get_client()
        key = self._lock_key(job_id)
        lock_id = _generate_lock_id()
        holder = _get_worker_id()
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)

        lock_data = json.dumps({
            "lock_id": lock_id,
            "holder": holder,
            "acquired_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        })

        # Try to set with NX (only if not exists) and EX (expiration)
        acquired = client.set(key, lock_data, nx=True, ex=ttl_seconds)

        if acquired:
            logger.debug(f"Acquired lock for job {job_id} (lock_id={lock_id})")
            return LockInfo(
                job_id=job_id,
                lock_id=lock_id,
                holder=holder,
                acquired_at=now,
                expires_at=expires_at,
            )

        logger.debug(f"Job {job_id} already locked")
        return None

    def release(self, job_id: int, lock_id: str) -> bool:
        """Release a lock using Lua script for atomicity."""
        import json

        client = self._get_client()
        key = self._lock_key(job_id)

        # Lua script: only delete if lock_id matches
        lua_script = """
        local data = redis.call('GET', KEYS[1])
        if data then
            local lock = cjson.decode(data)
            if lock.lock_id == ARGV[1] then
                redis.call('DEL', KEYS[1])
                return 1
            end
        end
        return 0
        """

        try:
            result = client.eval(lua_script, 1, key, lock_id)
            released = result == 1
            if released:
                logger.debug(f"Released lock for job {job_id}")
            return released
        except Exception:
            # Fallback: simple delete if Lua fails
            data = client.get(key)
            if data:
                lock_data = json.loads(data)
                if lock_data.get("lock_id") == lock_id:
                    client.delete(key)
                    return True
            return False

    def extend(
        self,
        job_id: int,
        lock_id: str,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> bool:
        """Extend a lock's TTL."""
        import json

        client = self._get_client()
        key = self._lock_key(job_id)

        # Get current lock data
        data = client.get(key)
        if not data:
            return False

        lock_data = json.loads(data)
        if lock_data.get("lock_id") != lock_id:
            return False

        # Update expiration
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)
        lock_data["expires_at"] = expires_at.isoformat()

        # Set with new TTL
        client.set(key, json.dumps(lock_data), ex=ttl_seconds)
        logger.debug(f"Extended lock for job {job_id}")
        return True

    def get_lock_info(self, job_id: int) -> LockInfo | None:
        """Get lock information."""
        import json

        client = self._get_client()
        key = self._lock_key(job_id)

        data = client.get(key)
        if not data:
            return None

        lock_data = json.loads(data)

        acquired_at = datetime.fromisoformat(lock_data["acquired_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(lock_data["expires_at"].replace("Z", "+00:00"))

        if acquired_at.tzinfo is None:
            acquired_at = acquired_at.replace(tzinfo=timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return LockInfo(
            job_id=job_id,
            lock_id=lock_data["lock_id"],
            holder=lock_data["holder"],
            acquired_at=acquired_at,
            expires_at=expires_at,
        )

    def cleanup_expired(self) -> int:
        """Clean up expired locks (Redis TTL handles this automatically)."""
        return 0


def get_scheduler_lock_backend(
    db_path: str | None = None,
    backend_type: str | None = None,
) -> SchedulerLockBackend:
    """Get a scheduler lock backend.

    Args:
        db_path: Path for SQLite backend.
        backend_type: Backend type ('sqlite' or 'redis'). Defaults to
            SCHEDULER_LOCK_BACKEND env var or 'sqlite'.

    Returns:
        SchedulerLockBackend instance.
    """
    if backend_type is None:
        backend_type = os.getenv("SCHEDULER_LOCK_BACKEND", "sqlite")

    if backend_type == "redis":
        return RedisSchedulerLockBackend()
    else:
        if db_path is None:
            db_path = os.getenv("SCHEDULER_DB_PATH", "./data/scheduler.db")
        return SQLiteSchedulerLockBackend(db_path)


def _heartbeat_worker(
    stop_event: threading.Event,
    backend: SchedulerLockBackend,
    job_id: int,
    lock_id: str,
    ttl_seconds: int,
    heartbeat_interval: int,
) -> None:
    """Background thread that periodically extends the lock TTL.

    This prevents lock expiration for long-running jobs by calling
    backend.extend() at regular intervals.

    Args:
        stop_event: Event to signal the thread to stop.
        backend: Lock backend to use for extension.
        job_id: The job ID whose lock to extend.
        lock_id: The lock ID to verify ownership.
        ttl_seconds: TTL to set on each extension.
        heartbeat_interval: Seconds between heartbeats.
    """
    while not stop_event.wait(timeout=heartbeat_interval):
        try:
            extended = backend.extend(job_id, lock_id, ttl_seconds)
            if extended:
                logger.debug(f"Heartbeat: extended lock for job {job_id}")
            else:
                logger.warning(f"Heartbeat: failed to extend lock for job {job_id}")
                break
        except Exception as e:
            logger.warning(f"Heartbeat error for job {job_id}: {e}")


@contextmanager
def job_lock(
    job_id: int,
    backend: SchedulerLockBackend | None = None,
    ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
) -> Generator[LockInfo | None, None, None]:
    """Context manager for acquiring a job lock with automatic heartbeat.

    The heartbeat thread periodically extends the lock's TTL to prevent
    expiration during long-running jobs. This ensures that another scheduler
    instance won't steal the lock while the job is still executing.

    Args:
        job_id: The job ID to lock.
        backend: Lock backend. If None, uses default.
        ttl_seconds: Lock TTL in seconds (default: 300).
        heartbeat_interval: Interval for lock heartbeat/extension (default: 30).
            Should be less than ttl_seconds to ensure lock doesn't expire.

    Yields:
        LockInfo if lock acquired, None otherwise.

    Example:
        >>> with job_lock(job_id) as lock:
        ...     if lock:
        ...         # Do work while holding lock
        ...         # Heartbeat thread keeps lock alive automatically
        ...         long_running_operation()
        ...     else:
        ...         print("Job already running")
    """
    if backend is None:
        backend = get_scheduler_lock_backend()

    lock_info = backend.acquire(job_id, ttl_seconds)
    if lock_info is None:
        yield None
        return

    # Start heartbeat thread to keep lock alive during long-running jobs
    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_heartbeat_worker,
        args=(stop_event, backend, job_id, lock_info.lock_id, ttl_seconds, heartbeat_interval),
        daemon=True,
        name=f"lock-heartbeat-{job_id}",
    )
    heartbeat_thread.start()
    logger.debug(f"Started heartbeat thread for job {job_id} (interval={heartbeat_interval}s)")

    try:
        yield lock_info
    finally:
        # Signal heartbeat thread to stop and wait for it
        stop_event.set()
        heartbeat_thread.join(timeout=2.0)
        if heartbeat_thread.is_alive():
            logger.warning(f"Heartbeat thread for job {job_id} did not stop cleanly")

        # Release the lock
        backend.release(job_id, lock_info.lock_id)
        logger.debug(f"Released lock and stopped heartbeat for job {job_id}")


def is_lock_enabled() -> bool:
    """Check if scheduler locking is enabled.

    Returns:
        True if locking is enabled (default), False otherwise.
    """
    return os.getenv("SCHEDULER_LOCK_ENABLED", "true").lower() in ("true", "1", "yes")


__all__ = [
    "LockInfo",
    "SchedulerLockBackend",
    "SQLiteSchedulerLockBackend",
    "RedisSchedulerLockBackend",
    "get_scheduler_lock_backend",
    "job_lock",
    "is_lock_enabled",
    "DEFAULT_LOCK_TTL_SECONDS",
    "DEFAULT_HEARTBEAT_INTERVAL",
]
