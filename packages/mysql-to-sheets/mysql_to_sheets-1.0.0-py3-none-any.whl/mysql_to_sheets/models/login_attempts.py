"""Login attempt tracking for account lockout security.

Provides persistent tracking of failed login attempts to implement
account lockout after consecutive failures.
"""

import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("mysql_to_sheets.models.login_attempts")

# Default lockout configuration
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LOCKOUT_MINUTES = 15
DEFAULT_WINDOW_MINUTES = 30  # Time window to count failures


@dataclass
class LoginAttempt:
    """Record of a login attempt.

    Attributes:
        id: Unique identifier.
        email: Email address attempted.
        ip_address: Client IP address.
        success: Whether the attempt succeeded.
        failure_reason: Reason for failure if unsuccessful.
        attempted_at: Timestamp of the attempt.
    """

    email: str
    ip_address: str | None
    success: bool
    failure_reason: str | None = None
    attempted_at: datetime | None = None
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "email": self.email,
            "ip_address": self.ip_address,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "attempted_at": self.attempted_at.isoformat() if self.attempted_at else None,
        }


@dataclass
class LockoutStatus:
    """Account lockout status.

    Attributes:
        is_locked: Whether the account is currently locked.
        failed_attempts: Number of failed attempts in the window.
        lockout_until: When the lockout expires (if locked).
        remaining_attempts: Attempts remaining before lockout.
    """

    is_locked: bool
    failed_attempts: int
    lockout_until: datetime | None = None
    remaining_attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_locked": self.is_locked,
            "failed_attempts": self.failed_attempts,
            "lockout_until": self.lockout_until.isoformat() if self.lockout_until else None,
            "remaining_attempts": self.remaining_attempts,
        }


class LoginAttemptRepository:
    """Repository for managing login attempt records.

    Uses SQLite for persistence with automatic table creation.
    """

    def __init__(
        self,
        db_path: str,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        lockout_minutes: int = DEFAULT_LOCKOUT_MINUTES,
        window_minutes: int = DEFAULT_WINDOW_MINUTES,
    ) -> None:
        """Initialize repository.

        Args:
            db_path: Path to SQLite database file.
            max_attempts: Maximum failed attempts before lockout.
            lockout_minutes: Base lockout duration in minutes.
            window_minutes: Time window for counting failures.
        """
        self.db_path = db_path
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self.window_minutes = window_minutes
        self._ensure_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Login attempts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    ip_address TEXT,
                    success INTEGER NOT NULL DEFAULT 0,
                    failure_reason TEXT,
                    attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes for efficient queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time
                ON login_attempts(email, attempted_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time
                ON login_attempts(ip_address, attempted_at)
            """)

            # Account lockouts table (tracks lockout state)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_lockouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    locked_at TEXT NOT NULL,
                    lockout_until TEXT NOT NULL,
                    consecutive_lockouts INTEGER NOT NULL DEFAULT 1,
                    last_failure_reason TEXT
                )
            """)

            conn.commit()
        finally:
            conn.close()

    def record_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str | None = None,
        failure_reason: str | None = None,
    ) -> LoginAttempt:
        """Record a login attempt.

        Args:
            email: Email address attempted.
            success: Whether the attempt succeeded.
            ip_address: Client IP address.
            failure_reason: Reason for failure if unsuccessful.

        Returns:
            The recorded LoginAttempt.
        """
        now = datetime.now(timezone.utc)
        attempt = LoginAttempt(
            email=email.lower(),
            ip_address=ip_address,
            success=success,
            failure_reason=failure_reason,
            attempted_at=now,
        )

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO login_attempts (email, ip_address, success, failure_reason, attempted_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (attempt.email, attempt.ip_address, int(success), failure_reason, now.isoformat()),
            )
            attempt.id = cursor.lastrowid

            # If successful, clear lockout
            if success:
                cursor.execute("DELETE FROM account_lockouts WHERE email = ?", (attempt.email,))

            conn.commit()
            return attempt
        finally:
            conn.close()

    def get_failed_attempts_count(
        self,
        email: str,
        window_minutes: int | None = None,
    ) -> int:
        """Get count of failed login attempts in the time window.

        Args:
            email: Email address to check.
            window_minutes: Time window in minutes (uses default if None).

        Returns:
            Number of failed attempts in the window.
        """
        window = window_minutes or self.window_minutes
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM login_attempts
                WHERE email = ? AND success = 0 AND attempted_at > ?
                """,
                (email.lower(), cutoff.isoformat()),
            )
            row = cursor.fetchone()
            return row["count"] if row else 0
        finally:
            conn.close()

    def check_lockout(self, email: str) -> LockoutStatus:
        """Check if an account is locked out.

        Uses exponential backoff for repeat offenders:
        - 1st lockout: base duration
        - 2nd lockout: base * 2
        - 3rd lockout: base * 4
        - etc.

        Args:
            email: Email address to check.

        Returns:
            LockoutStatus with current lockout information.
        """
        email = email.lower()
        now = datetime.now(timezone.utc)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Check for active lockout
            cursor.execute(
                """
                SELECT * FROM account_lockouts WHERE email = ?
                """,
                (email,),
            )
            lockout_row = cursor.fetchone()

            if lockout_row:
                lockout_until = datetime.fromisoformat(lockout_row["lockout_until"])
                if lockout_until.tzinfo is None:
                    lockout_until = lockout_until.replace(tzinfo=timezone.utc)

                if now < lockout_until:
                    # Still locked out
                    return LockoutStatus(
                        is_locked=True,
                        failed_attempts=self.max_attempts,
                        lockout_until=lockout_until,
                        remaining_attempts=0,
                    )
                else:
                    # Lockout expired, don't delete yet (keep for escalation tracking)
                    pass

            # Check recent failures
            failed_count = self.get_failed_attempts_count(email)

            if failed_count >= self.max_attempts:
                # Should be locked out - create/update lockout record
                consecutive = 1
                if lockout_row:
                    consecutive = lockout_row["consecutive_lockouts"] + 1

                # Exponential backoff: base * 2^(consecutive-1)
                lockout_duration = self.lockout_minutes * (2 ** (consecutive - 1))
                # Cap at 24 hours
                lockout_duration = min(lockout_duration, 24 * 60)

                lockout_until = now + timedelta(minutes=lockout_duration)

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO account_lockouts
                    (email, locked_at, lockout_until, consecutive_lockouts)
                    VALUES (?, ?, ?, ?)
                    """,
                    (email, now.isoformat(), lockout_until.isoformat(), consecutive),
                )
                conn.commit()

                logger.warning(
                    f"Account locked: {email} for {lockout_duration} minutes "
                    f"(consecutive lockouts: {consecutive})"
                )

                return LockoutStatus(
                    is_locked=True,
                    failed_attempts=failed_count,
                    lockout_until=lockout_until,
                    remaining_attempts=0,
                )

            return LockoutStatus(
                is_locked=False,
                failed_attempts=failed_count,
                lockout_until=None,
                remaining_attempts=max(0, self.max_attempts - failed_count),
            )
        finally:
            conn.close()

    def clear_lockout(self, email: str) -> bool:
        """Clear lockout for an account (admin override).

        Args:
            email: Email address to unlock.

        Returns:
            True if a lockout was cleared, False if none existed.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM account_lockouts WHERE email = ?", (email.lower(),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def cleanup_old_attempts(self, days: int = 30) -> int:
        """Remove old login attempt records.

        Args:
            days: Remove attempts older than this many days.

        Returns:
            Number of records removed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM login_attempts WHERE attempted_at < ?",
                (cutoff.isoformat(),),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def get_recent_attempts(
        self,
        email: str | None = None,
        ip_address: str | None = None,
        limit: int = 100,
    ) -> list[LoginAttempt]:
        """Get recent login attempts.

        Args:
            email: Filter by email address.
            ip_address: Filter by IP address.
            limit: Maximum number of records to return.

        Returns:
            List of recent LoginAttempt records.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            query = "SELECT * FROM login_attempts"
            params: list[Any] = []
            conditions = []

            if email:
                conditions.append("email = ?")
                params.append(email.lower())
            if ip_address:
                conditions.append("ip_address = ?")
                params.append(ip_address)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY attempted_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            attempts = []
            for row in rows:
                attempted_at = datetime.fromisoformat(row["attempted_at"])
                if attempted_at.tzinfo is None:
                    attempted_at = attempted_at.replace(tzinfo=timezone.utc)

                attempts.append(
                    LoginAttempt(
                        id=row["id"],
                        email=row["email"],
                        ip_address=row["ip_address"],
                        success=bool(row["success"]),
                        failure_reason=row["failure_reason"],
                        attempted_at=attempted_at,
                    )
                )
            return attempts
        finally:
            conn.close()


# Singleton repository instance
_login_attempt_repo: LoginAttemptRepository | None = None


def get_login_attempt_repository(db_path: str | None = None) -> LoginAttemptRepository:
    """Get or create the singleton LoginAttemptRepository.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        LoginAttemptRepository instance.
    """
    global _login_attempt_repo

    if db_path is None:
        from mysql_to_sheets.core.tenant import get_tenant_db_path

        db_path = get_tenant_db_path()

    if _login_attempt_repo is None or _login_attempt_repo.db_path != db_path:
        # Load configuration from environment
        max_attempts = int(os.getenv("LOCKOUT_MAX_ATTEMPTS", str(DEFAULT_MAX_ATTEMPTS)))
        lockout_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", str(DEFAULT_LOCKOUT_MINUTES)))
        window_minutes = int(os.getenv("LOCKOUT_WINDOW_MINUTES", str(DEFAULT_WINDOW_MINUTES)))

        _login_attempt_repo = LoginAttemptRepository(
            db_path=db_path,
            max_attempts=max_attempts,
            lockout_minutes=lockout_minutes,
            window_minutes=window_minutes,
        )

    return _login_attempt_repo


def reset_login_attempt_repository() -> None:
    """Reset the singleton repository. For testing."""
    global _login_attempt_repo
    _login_attempt_repo = None
