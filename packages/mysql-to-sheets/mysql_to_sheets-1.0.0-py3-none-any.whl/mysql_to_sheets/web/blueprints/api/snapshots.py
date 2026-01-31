"""Snapshots API blueprint for web dashboard.

Handles snapshot CRUD and rollback operations via AJAX.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.rollback import (
    can_rollback,
    preview_rollback,
    rollback_to_snapshot,
)
from mysql_to_sheets.core.snapshot_retention import (
    RetentionConfig,
    cleanup_old_snapshots,
    get_storage_stats,
)
from mysql_to_sheets.core.snapshots import (
    delete_snapshot,
    get_snapshot,
    list_snapshots,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.api.snapshots")

snapshots_api_bp = Blueprint("snapshots_api", __name__, url_prefix="/api/snapshots")


def _snapshot_to_dict(snapshot: Any) -> dict[str, Any]:
    """Convert Snapshot to JSON-serializable dict."""
    return {
        "id": snapshot.id,
        "organization_id": snapshot.organization_id,
        "sync_config_id": snapshot.sync_config_id,
        "sheet_id": snapshot.sheet_id,
        "worksheet_name": snapshot.worksheet_name,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
        "row_count": snapshot.row_count,
        "column_count": snapshot.column_count,
        "size_bytes": snapshot.size_bytes,
        "checksum": snapshot.checksum,
        "headers": snapshot.headers,
    }


def _get_org_id() -> int:
    """Get current organization ID from session."""
    user = get_current_user()
    if user and isinstance(user, dict):
        return int(user.get("organization_id", 1))
    return 1  # Default for single-tenant mode


@snapshots_api_bp.route("", methods=["GET"])
@login_required
def list_all_snapshots() -> tuple[Response, int]:
    """List all snapshots.

    Query params:
    - sheet_id: Filter by sheet ID
    - limit: Maximum results (default 20)
    - offset: Results to skip

    Returns:
        JSON response with snapshot list.
    """
    sheet_id = request.args.get("sheet_id")
    limit = int(request.args.get("limit", "20"))
    offset = int(request.args.get("offset", "0"))

    db_path = get_tenant_db_path()
    org_id = _get_org_id()

    snapshots = list_snapshots(
        organization_id=org_id,
        db_path=db_path,
        sheet_id=sheet_id,
        limit=limit,
        offset=offset,
    )

    return jsonify(
        {
            "success": True,
            "snapshots": [_snapshot_to_dict(s) for s in snapshots],
            "total": len(snapshots),
        }
    ), 200


@snapshots_api_bp.route("/stats", methods=["GET"])
@login_required
def get_stats() -> tuple[Response, int]:
    """Get snapshot storage statistics.

    Returns:
        JSON response with storage stats.
    """
    db_path = get_tenant_db_path()
    org_id = _get_org_id()

    stats = get_storage_stats(
        organization_id=org_id,
        db_path=db_path,
    )

    return jsonify(
        {
            "success": True,
            **stats.to_dict(),
        }
    ), 200


@snapshots_api_bp.route("/cleanup", methods=["POST"])
@login_required
def cleanup() -> tuple[Response, int]:
    """Clean up old snapshots based on retention policy.

    Request body (optional):
    - retention_count: Maximum snapshots per sheet
    - retention_days: Delete snapshots older than N days

    Returns:
        JSON response with cleanup results.
    """
    data = request.get_json() or {}
    config = get_config()
    db_path = get_tenant_db_path()
    org_id = _get_org_id()

    retention_config = RetentionConfig(
        retention_count=data.get("retention_count") or config.snapshot_retention_count,
        retention_days=data.get("retention_days") or config.snapshot_retention_days,
        max_size_mb=config.snapshot_max_size_mb,
    )

    result = cleanup_old_snapshots(
        organization_id=org_id,
        db_path=db_path,
        retention_config=retention_config,
        logger=logger,
    )

    return jsonify(
        {
            "success": True,
            **result.to_dict(),
        }
    ), 200


@snapshots_api_bp.route("/<int:snapshot_id>", methods=["GET"])
@login_required
def get_snapshot_by_id(snapshot_id: int) -> tuple[Response, int]:
    """Get snapshot details by ID.

    Returns:
        JSON response with snapshot details.
    """
    db_path = get_tenant_db_path()
    org_id = _get_org_id()

    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=org_id,
        db_path=db_path,
        include_data=False,
    )

    if not snapshot:
        return jsonify(
            {
                "success": False,
                "error": f"Snapshot {snapshot_id} not found",
                "message": f"Snapshot {snapshot_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "snapshot": _snapshot_to_dict(snapshot),
        }
    ), 200


@snapshots_api_bp.route("/<int:snapshot_id>", methods=["DELETE"])
@login_required
def delete_snapshot_by_id(snapshot_id: int) -> tuple[Response, int]:
    """Delete a snapshot.

    Returns:
        JSON response confirming deletion.
    """
    db_path = get_tenant_db_path()
    org_id = _get_org_id()

    deleted = delete_snapshot(
        snapshot_id=snapshot_id,
        organization_id=org_id,
        db_path=db_path,
        logger=logger,
    )

    if not deleted:
        return jsonify(
            {
                "success": False,
                "error": f"Snapshot {snapshot_id} not found",
                "message": f"Snapshot {snapshot_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "message": f"Snapshot {snapshot_id} deleted",
        }
    ), 200


@snapshots_api_bp.route("/<int:snapshot_id>/preview", methods=["POST"])
@login_required
def preview_snapshot_rollback(snapshot_id: int) -> tuple[Response, int]:
    """Preview what changes a rollback would make.

    Returns:
        JSON response with rollback preview.
    """
    db_path = get_tenant_db_path()
    config = get_config()
    org_id = _get_org_id()

    # Get snapshot to retrieve sheet info
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=org_id,
        db_path=db_path,
        include_data=False,
    )

    if not snapshot:
        return jsonify(
            {
                "success": False,
                "error": f"Snapshot {snapshot_id} not found",
                "message": f"Snapshot {snapshot_id} not found",
            }
        ), 404

    # Create config with snapshot's sheet info
    rollback_config = config.with_overrides(
        google_sheet_id=snapshot.sheet_id,
        google_worksheet_name=snapshot.worksheet_name,
    )

    try:
        preview = preview_rollback(
            snapshot_id=snapshot_id,
            organization_id=org_id,
            config=rollback_config,
            db_path=db_path,
            logger=logger,
        )

        return jsonify(
            {
                "success": True,
                "preview": {
                    "snapshot_id": preview.snapshot_id,
                    "snapshot_created_at": preview.snapshot_created_at,
                    "current_row_count": preview.current_row_count,
                    "snapshot_row_count": preview.snapshot_row_count,
                    "current_column_count": preview.current_column_count,
                    "snapshot_column_count": preview.snapshot_column_count,
                    "message": preview.message,
                    "diff": preview.diff.to_dict() if preview.diff else None,
                },
            }
        ), 200

    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 400
    except Exception as e:
        logger.exception(f"Preview failed: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500


@snapshots_api_bp.route("/<int:snapshot_id>/rollback", methods=["POST"])
@login_required
def execute_rollback(snapshot_id: int) -> tuple[Response, int]:
    """Execute a rollback to restore sheet from snapshot.

    Request body (optional):
    - create_backup: Whether to create backup before rollback (default: true)

    Returns:
        JSON response with rollback result.
    """
    data = request.get_json() or {}
    create_backup = data.get("create_backup", True)

    db_path = get_tenant_db_path()
    config = get_config()
    org_id = _get_org_id()

    # Get snapshot to retrieve sheet info
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=org_id,
        db_path=db_path,
        include_data=False,
    )

    if not snapshot:
        return jsonify(
            {
                "success": False,
                "error": f"Snapshot {snapshot_id} not found",
                "message": f"Snapshot {snapshot_id} not found",
            }
        ), 404

    # Create config with snapshot's sheet info
    rollback_config = config.with_overrides(
        google_sheet_id=snapshot.sheet_id,
        google_worksheet_name=snapshot.worksheet_name,
    )

    # Check if rollback is possible
    can_proceed, reason = can_rollback(
        snapshot_id=snapshot_id,
        organization_id=org_id,
        config=rollback_config,
        db_path=db_path,
        logger=logger,
    )

    if not can_proceed:
        return jsonify(
            {
                "success": False,
                "error": f"Cannot rollback: {reason}",
                "message": f"Cannot rollback: {reason}",
            }
        ), 400

    try:
        result = rollback_to_snapshot(
            snapshot_id=snapshot_id,
            organization_id=org_id,
            config=rollback_config,
            db_path=db_path,
            create_backup=create_backup,
            logger=logger,
        )

        return jsonify(
            {
                "success": result.success,
                "result": result.to_dict(),
            }
        ), 200 if result.success else 500

    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 400
    except Exception as e:
        logger.exception(f"Rollback failed: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500
