"""API endpoints for offline mode status and queue management.

This module provides endpoints for checking connectivity status
and managing the offline sync queue.
"""

import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

offline_bp = Blueprint("offline", __name__, url_prefix="/api/offline")


@offline_bp.route("/status")
def get_status():
    """Get current connectivity and offline queue status.

    Returns:
        JSON response with connectivity state and queue info.
    """
    try:
        from mysql_to_sheets.desktop.connectivity import (
            ConnectivityState,
            get_connectivity_monitor,
        )

        monitor = get_connectivity_monitor()
        status = monitor.status

        # Get queue info
        queue_count = 0
        queued_syncs = []
        try:
            from mysql_to_sheets.models.offline_queue import get_offline_queue_repository

            repo = get_offline_queue_repository()
            queue_count = repo.count_pending()
            queued_syncs = [q.to_dict() for q in repo.get_all_pending()]
        except Exception as e:
            logger.debug(f"Could not get queue info: {e}")

        return jsonify({
            "success": True,
            "connectivity": {
                "state": status.state.value,
                "is_online": status.is_fully_online,
                "database_reachable": status.database_reachable,
                "sheets_reachable": status.sheets_reachable,
                "database_latency_ms": status.database_latency_ms,
                "sheets_latency_ms": status.sheets_latency_ms,
                "last_check_time": status.last_check_time,
                "error_message": status.error_message,
            },
            "queue": {
                "count": queue_count,
                "syncs": queued_syncs,
            },
        })

    except Exception as e:
        logger.error(f"Failed to get offline status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@offline_bp.route("/check", methods=["POST"])
def check_connectivity():
    """Force an immediate connectivity check.

    Returns:
        JSON response with updated connectivity status.
    """
    try:
        from mysql_to_sheets.desktop.connectivity import get_connectivity_monitor

        monitor = get_connectivity_monitor()
        status = monitor.check_now()

        return jsonify({
            "success": True,
            "connectivity": {
                "state": status.state.value,
                "is_online": status.is_fully_online,
                "database_reachable": status.database_reachable,
                "sheets_reachable": status.sheets_reachable,
                "database_latency_ms": status.database_latency_ms,
                "sheets_latency_ms": status.sheets_latency_ms,
                "error_message": status.error_message,
            },
        })

    except Exception as e:
        logger.error(f"Connectivity check failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@offline_bp.route("/queue/<int:queue_id>", methods=["DELETE"])
def delete_queued_sync(queue_id: int):
    """Delete a queued sync.

    Args:
        queue_id: Queue entry ID.

    Returns:
        JSON response indicating success.
    """
    try:
        from mysql_to_sheets.models.offline_queue import get_offline_queue_repository

        repo = get_offline_queue_repository()
        if repo.delete(queue_id):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Not found"}), 404

    except Exception as e:
        logger.error(f"Failed to delete queued sync: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@offline_bp.route("/queue/process", methods=["POST"])
def process_queue():
    """Process all pending syncs in the offline queue.

    Returns:
        JSON response with number of syncs processed.
    """
    try:
        from mysql_to_sheets.desktop.background import get_background_manager

        manager = get_background_manager()
        processed = manager.process_offline_queue()

        return jsonify({
            "success": True,
            "processed": processed,
        })

    except Exception as e:
        logger.error(f"Failed to process queue: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500
