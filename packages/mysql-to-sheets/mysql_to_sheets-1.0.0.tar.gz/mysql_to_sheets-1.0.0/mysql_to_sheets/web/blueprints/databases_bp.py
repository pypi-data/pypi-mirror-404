"""Web routes and API endpoints for multi-database dashboard.

This module provides pages and API endpoints for managing database
integrations and viewing their health status.
"""

import logging
import os

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger(__name__)

databases_bp = Blueprint("databases", __name__, url_prefix="/databases")


def _get_db_path() -> str:
    """Get the database path for integrations."""
    from mysql_to_sheets.web.app import get_tenant_db_path

    return get_tenant_db_path()


def _get_organization_id() -> int:
    """Get the current organization ID from session."""
    from flask import session

    return session.get("organization_id", 1)


@databases_bp.route("/")
@login_required
def index():
    """Database integrations list page."""
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        # Get all database integrations (not sheets)
        integrations = repo.get_all(
            organization_id=org_id,
            active_only=False,
        )

        # Filter to database types only
        db_integrations = [
            i for i in integrations
            if i.integration_type in ("mysql", "postgres", "sqlite", "mssql")
        ]

        # Count by status
        status_counts = {
            "connected": 0,
            "disconnected": 0,
            "error": 0,
            "unknown": 0,
        }
        for integration in db_integrations:
            status = integration.health_status or "unknown"
            if status in status_counts:
                status_counts[status] += 1

        return render_template(
            "databases.html",
            integrations=db_integrations,
            status_counts=status_counts,
            total_count=len(db_integrations),
        )

    except Exception as e:
        logger.error(f"Failed to load databases page: {e}")
        flash(f"Error loading databases: {e}", "error")
        return render_template(
            "databases.html",
            integrations=[],
            status_counts={"connected": 0, "disconnected": 0, "error": 0, "unknown": 0},
            total_count=0,
        )


@databases_bp.route("/<int:integration_id>")
@login_required
def detail(integration_id: int):
    """Database integration detail page."""
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        integration = repo.get_by_id(integration_id, org_id)
        if not integration:
            flash("Database not found", "error")
            return redirect(url_for("databases.index"))

        return render_template(
            "database_detail.html",
            integration=integration,
        )

    except Exception as e:
        logger.error(f"Failed to load database detail: {e}")
        flash(f"Error loading database: {e}", "error")
        return redirect(url_for("databases.index"))


@databases_bp.route("/<int:integration_id>/test", methods=["POST"])
@login_required
def test_connection(integration_id: int):
    """Test database connection."""
    from mysql_to_sheets.core.health_monitor import get_health_monitor
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        integration = repo.get_by_id(integration_id, org_id)
        if not integration:
            flash("Database not found", "error")
            return redirect(url_for("databases.index"))

        # Test connection
        monitor = get_health_monitor()
        result = monitor.check_integration(integration)

        # Update health status in database
        repo.update_health_status(
            integration_id=integration_id,
            organization_id=org_id,
            health_status=result.status,
            error_message=result.error_message,
            latency_ms=result.latency_ms,
        )

        if result.status == "connected":
            flash(
                f"Connection successful! Latency: {result.latency_ms:.1f}ms",
                "success",
            )
        else:
            flash(f"Connection failed: {result.error_message}", "error")

        return redirect(url_for("databases.detail", integration_id=integration_id))

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        flash(f"Connection test failed: {e}", "error")
        return redirect(url_for("databases.detail", integration_id=integration_id))


# API Endpoints

@databases_bp.route("/api/list")
@login_required
def api_list():
    """API: List all database integrations."""
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        integrations = repo.get_all(organization_id=org_id, active_only=False)
        db_integrations = [
            i for i in integrations
            if i.integration_type in ("mysql", "postgres", "sqlite", "mssql")
        ]

        return jsonify({
            "success": True,
            "integrations": [i.to_dict() for i in db_integrations],
        })

    except Exception as e:
        logger.error(f"API list failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@databases_bp.route("/api/<int:integration_id>")
@login_required
def api_get(integration_id: int):
    """API: Get database integration details."""
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        integration = repo.get_by_id(integration_id, org_id)
        if not integration:
            return jsonify({"success": False, "error": "Not found"}), 404

        return jsonify({
            "success": True,
            "integration": integration.to_dict(),
        })

    except Exception as e:
        logger.error(f"API get failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@databases_bp.route("/api/<int:integration_id>/health", methods=["POST"])
@login_required
def api_check_health(integration_id: int):
    """API: Check health of a database integration."""
    from mysql_to_sheets.core.health_monitor import get_health_monitor
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        integration = repo.get_by_id(integration_id, org_id)
        if not integration:
            return jsonify({"success": False, "error": "Not found"}), 404

        # Check health
        monitor = get_health_monitor()
        result = monitor.check_integration(integration)

        # Update status
        repo.update_health_status(
            integration_id=integration_id,
            organization_id=org_id,
            health_status=result.status,
            error_message=result.error_message,
            latency_ms=result.latency_ms,
        )

        return jsonify({
            "success": True,
            "health": result.to_dict(),
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@databases_bp.route("/api/health/all", methods=["POST"])
@login_required
def api_check_all_health():
    """API: Check health of all database integrations."""
    from mysql_to_sheets.core.health_monitor import get_health_monitor

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()

        monitor = get_health_monitor()
        results = monitor.check_now(db_path, org_id)

        return jsonify({
            "success": True,
            "results": [r.to_dict() for r in results],
            "summary": {
                "total": len(results),
                "connected": sum(1 for r in results if r.status == "connected"),
                "disconnected": sum(1 for r in results if r.status == "disconnected"),
                "error": sum(1 for r in results if r.status == "error"),
            },
        })

    except Exception as e:
        logger.error(f"Health check all failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@databases_bp.route("/api/status-summary")
@login_required
def api_status_summary():
    """API: Get summary of database health statuses."""
    from mysql_to_sheets.models.integrations import get_integration_repository

    try:
        db_path = _get_db_path()
        org_id = _get_organization_id()
        repo = get_integration_repository(db_path)

        integrations = repo.get_all(organization_id=org_id, active_only=True)
        db_integrations = [
            i for i in integrations
            if i.integration_type in ("mysql", "postgres", "sqlite", "mssql")
        ]

        summary = {
            "total": len(db_integrations),
            "connected": 0,
            "disconnected": 0,
            "error": 0,
            "unknown": 0,
        }

        for integration in db_integrations:
            status = integration.health_status or "unknown"
            if status in summary:
                summary[status] += 1

        return jsonify({
            "success": True,
            "summary": summary,
        })

    except Exception as e:
        logger.error(f"Status summary failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
