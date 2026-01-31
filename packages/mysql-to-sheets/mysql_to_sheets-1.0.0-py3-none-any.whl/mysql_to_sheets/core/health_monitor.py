"""Connection health monitoring for database integrations.

This module provides background health checking for database connections,
updating integration health status in the database.
"""

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check for an integration."""

    integration_id: int
    integration_name: str
    integration_type: str
    status: str  # "connected", "disconnected", "error"
    latency_ms: float | None = None
    error_message: str | None = None
    checked_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "integration_id": self.integration_id,
            "integration_name": self.integration_name,
            "integration_type": self.integration_type,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }


class ConnectionHealthMonitor:
    """Monitors health of database connections.

    Periodically checks database connectivity and updates health status
    in the integrations table.
    """

    def __init__(
        self,
        check_interval_seconds: float = 60.0,
        timeout_seconds: float = 10.0,
        on_status_change: Callable[[HealthCheckResult], None] | None = None,
    ) -> None:
        """Initialize the health monitor.

        Args:
            check_interval_seconds: Seconds between health checks.
            timeout_seconds: Timeout for each connection test.
            on_status_change: Callback when health status changes.
        """
        self._check_interval = check_interval_seconds
        self._timeout = timeout_seconds
        self._on_status_change = on_status_change

        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # Track previous status for change detection
        self._previous_status: dict[int, str] = {}

    def start(self, db_path: str, organization_id: int) -> None:
        """Start background health monitoring.

        Args:
            db_path: Path to SQLite database for integrations.
            organization_id: Organization ID to monitor.
        """
        if self._running:
            logger.warning("Health monitor already running")
            return

        self._running = True
        self._db_path = db_path
        self._organization_id = organization_id

        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="health-monitor",
        )
        self._thread.start()
        logger.info("Health monitor started")

    def stop(self) -> None:
        """Stop background health monitoring."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("Health monitor stopped")

    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                self._check_all_integrations()
            except Exception as e:
                logger.error(f"Health check failed: {e}")

            # Sleep in small increments to allow quick shutdown
            for _ in range(int(self._check_interval)):
                if not self._running:
                    break
                time.sleep(1.0)

    def _check_all_integrations(self) -> list[HealthCheckResult]:
        """Check health of all active integrations.

        Returns:
            List of health check results.
        """
        from mysql_to_sheets.models.integrations import get_integration_repository

        repo = get_integration_repository(self._db_path)
        integrations = repo.get_all(
            organization_id=self._organization_id,
            active_only=True,
        )

        results = []
        for integration in integrations:
            # Only check database integrations
            if integration.integration_type not in ("mysql", "postgres", "sqlite", "mssql"):
                continue

            result = self.check_integration(integration)
            results.append(result)

            # Update database
            if integration.id is not None:
                repo.update_health_status(
                    integration_id=integration.id,
                    organization_id=integration.organization_id,
                    health_status=result.status,
                    error_message=result.error_message,
                    latency_ms=result.latency_ms,
                )

                # Check for status change
                with self._lock:
                    prev_status = self._previous_status.get(integration.id)
                    if prev_status != result.status:
                        self._previous_status[integration.id] = result.status
                        if self._on_status_change:
                            try:
                                self._on_status_change(result)
                            except Exception as e:
                                logger.warning(f"Status change callback failed: {e}")

        return results

    def check_integration(self, integration: Any) -> HealthCheckResult:
        """Check health of a single integration.

        Args:
            integration: Integration dataclass instance.

        Returns:
            Health check result.
        """
        from mysql_to_sheets.models.integrations import Integration

        if not isinstance(integration, Integration):
            raise TypeError("Expected Integration instance")

        start_time = time.time()
        result = HealthCheckResult(
            integration_id=integration.id or 0,
            integration_name=integration.name,
            integration_type=integration.integration_type,
            status="unknown",
            checked_at=datetime.now(),
        )

        try:
            # Test connection based on type
            if integration.integration_type == "mysql":
                self._check_mysql(integration)
            elif integration.integration_type == "postgres":
                self._check_postgres(integration)
            elif integration.integration_type == "sqlite":
                self._check_sqlite(integration)
            elif integration.integration_type == "mssql":
                self._check_mssql(integration)
            else:
                result.status = "error"
                result.error_message = f"Unsupported type: {integration.integration_type}"
                return result

            # Success
            latency_ms = (time.time() - start_time) * 1000
            result.status = "connected"
            result.latency_ms = round(latency_ms, 2)

        except Exception as e:
            result.status = "disconnected"
            result.error_message = str(e)[:500]
            logger.debug(f"Health check failed for {integration.name}: {e}")

        return result

    def _check_mysql(self, integration: Any) -> None:
        """Check MySQL connection health."""
        import mysql.connector

        config = {
            "host": integration.host,
            "port": integration.port or 3306,
            "database": integration.database_name,
            "user": integration.credentials.user,
            "password": integration.credentials.password,
            "connection_timeout": int(self._timeout),
        }
        if integration.ssl_mode:
            config["ssl_disabled"] = integration.ssl_mode == "disabled"

        conn = mysql.connector.connect(**config)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

    def _check_postgres(self, integration: Any) -> None:
        """Check PostgreSQL connection health."""
        import psycopg2

        conn = psycopg2.connect(
            host=integration.host,
            port=integration.port or 5432,
            dbname=integration.database_name,
            user=integration.credentials.user,
            password=integration.credentials.password,
            connect_timeout=int(self._timeout),
            sslmode=integration.ssl_mode or "prefer",
        )
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

    def _check_sqlite(self, integration: Any) -> None:
        """Check SQLite connection health."""
        import sqlite3

        conn = sqlite3.connect(
            integration.database_name,
            timeout=self._timeout,
        )
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

    def _check_mssql(self, integration: Any) -> None:
        """Check SQL Server connection health."""
        import pymssql

        conn = pymssql.connect(
            server=integration.host,
            port=str(integration.port or 1433),
            database=integration.database_name,
            user=integration.credentials.user,
            password=integration.credentials.password,
            login_timeout=int(self._timeout),
        )
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

    def check_now(self, db_path: str, organization_id: int) -> list[HealthCheckResult]:
        """Force an immediate health check of all integrations.

        Args:
            db_path: Path to SQLite database.
            organization_id: Organization ID.

        Returns:
            List of health check results.
        """
        self._db_path = db_path
        self._organization_id = organization_id
        return self._check_all_integrations()


# Global monitor instance
_monitor: ConnectionHealthMonitor | None = None


def get_health_monitor(
    check_interval_seconds: float = 60.0,
    on_status_change: Callable[[HealthCheckResult], None] | None = None,
) -> ConnectionHealthMonitor:
    """Get or create the global health monitor.

    Args:
        check_interval_seconds: Seconds between checks (used on first call).
        on_status_change: Callback for status changes (used on first call).

    Returns:
        ConnectionHealthMonitor instance.
    """
    global _monitor
    if _monitor is None:
        _monitor = ConnectionHealthMonitor(
            check_interval_seconds=check_interval_seconds,
            on_status_change=on_status_change,
        )
    return _monitor


def reset_health_monitor() -> None:
    """Reset the global health monitor. For testing."""
    global _monitor
    if _monitor is not None:
        _monitor.stop()
    _monitor = None
