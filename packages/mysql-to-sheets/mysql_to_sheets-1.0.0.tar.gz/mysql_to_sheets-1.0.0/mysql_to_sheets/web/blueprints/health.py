"""Health status blueprint for web dashboard.

Provides system health monitoring and connection status.
"""

import logging
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, Response, jsonify, render_template, request

from mysql_to_sheets import __version__
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import DatabaseError, SheetsError

logger = logging.getLogger("mysql_to_sheets.web.health")

health_bp = Blueprint("health", __name__)


# Cache for health check results (to avoid hammering services)
_health_cache: dict[str, dict[str, Any]] = {}
_cache_ttl_seconds = 30


def _get_cached_health(component: str) -> dict[str, Any] | None:
    """Get cached health check result if still valid."""
    cached = _health_cache.get(component)
    if cached:
        cached_at = cached.get("checked_at")
        if cached_at:
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            if age < _cache_ttl_seconds:
                return cached
    return None


def _cache_health(component: str, result: dict[str, Any]) -> None:
    """Cache a health check result."""
    result["checked_at"] = datetime.now(timezone.utc)
    _health_cache[component] = result


@health_bp.route("/health")
def health_page() -> str:
    """Render the health status page.

    Returns:
        Rendered health status template.
    """
    return render_template(
        "health.html",
        version=__version__,
    )


@health_bp.route("/api/health/status", methods=["GET"])
def api_health_status() -> tuple[Response, int]:
    """Get overall health status.

    Query params:
        refresh: If "true", bypass cache and run fresh checks

    Returns:
        JSON response with health status for all components.
    """
    refresh = request.args.get("refresh", "").lower() == "true"

    components = {
        "database": _check_database_health(refresh),
        "sheets": _check_sheets_health(refresh),
        "scheduler": _check_scheduler_health(),
        "system": _check_system_health(),
    }

    # Calculate overall status
    statuses = [c.get("status") for c in components.values()]
    if "error" in statuses:
        overall = "unhealthy"
    elif "warning" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return jsonify(
        {
            "status": overall,
            "version": __version__,
            "components": components,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    ), 200


@health_bp.route("/api/health/database", methods=["POST"])
def api_test_database() -> tuple[Response, int]:
    """Test database connection.

    Returns:
        JSON response with connection test result.
    """
    result = _check_database_health(refresh=True)
    status_code = 200 if result.get("status") == "healthy" else 500
    return jsonify(result), status_code


@health_bp.route("/api/health/sheets", methods=["POST"])
def api_test_sheets() -> tuple[Response, int]:
    """Test Google Sheets connection.

    Returns:
        JSON response with connection test result.
    """
    result = _check_sheets_health(refresh=True)
    status_code = 200 if result.get("status") == "healthy" else 500
    return jsonify(result), status_code


def _check_database_health(refresh: bool = False) -> dict[str, Any]:
    """Check database health.

    Args:
        refresh: If True, bypass cache.

    Returns:
        Health check result dictionary.
    """
    if not refresh:
        cached = _get_cached_health("database")
        if cached:
            return cached

    from mysql_to_sheets.core.sync import SyncService

    try:
        reset_config()
        config = get_config()
        service = SyncService(config)

        start = time.time()
        service.test_database_connection()
        latency_ms = int((time.time() - start) * 1000)

        result = {
            "status": "healthy",
            "latency_ms": latency_ms,
            "host": config.db_host,
            "port": config.db_port,
            "database": config.db_name,
            "db_type": config.db_type,
        }

    except DatabaseError as e:
        result = {
            "status": "error",
            "error": e.message,
            "error_code": e.code,
            "error_category": e.category.value if e.category else None,
            "remediation": e.remediation,
        }

    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
        }

    _cache_health("database", result)
    return result


def _check_sheets_health(refresh: bool = False) -> dict[str, Any]:
    """Check Google Sheets health.

    Args:
        refresh: If True, bypass cache.

    Returns:
        Health check result dictionary.
    """
    if not refresh:
        cached = _get_cached_health("sheets")
        if cached:
            return cached

    from mysql_to_sheets.core.sync import SyncService

    try:
        reset_config()
        config = get_config()
        service = SyncService(config)

        start = time.time()
        service.test_sheets_connection()
        latency_ms = int((time.time() - start) * 1000)

        result = {
            "status": "healthy",
            "latency_ms": latency_ms,
            "sheet_id": config.google_sheet_id,
            "worksheet": config.google_worksheet_name,
        }

    except SheetsError as e:
        result = {
            "status": "error",
            "error": e.message,
            "error_code": e.code,
            "error_category": e.category.value if e.category else None,
            "remediation": e.remediation,
        }

    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
        }

    _cache_health("sheets", result)
    return result


def _check_scheduler_health() -> dict[str, Any]:
    """Check scheduler health.

    Returns:
        Health check result dictionary.
    """
    # For now, just return basic status
    # In a real implementation, this would check APScheduler status
    return {
        "status": "healthy",
        "info": "Scheduler status check not implemented",
    }


def _check_system_health() -> dict[str, Any]:
    """Check system health.

    Returns:
        Health check result dictionary.
    """

    return {
        "status": "healthy",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system(),
        "platform_version": platform.version(),
        "uptime_info": "Process started",
        "memory_usage_mb": _get_memory_usage(),
    }


def _get_memory_usage() -> float | None:
    """Get current process memory usage in MB."""
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        return round(usage.ru_maxrss / 1024 / 1024, 2)  # Convert to MB
    except (ImportError, AttributeError):
        return None
