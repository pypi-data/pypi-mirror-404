"""Heartbeat endpoint for browser-to-app connection tracking.

This module provides a heartbeat endpoint that the browser pings periodically
to indicate it's still open. The desktop app monitors this to detect when
the browser is closed and decide whether to exit or stay in tray.
"""

import time

from flask import Blueprint, current_app, jsonify

heartbeat_bp = Blueprint("heartbeat", __name__)


@heartbeat_bp.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    """Receive heartbeat from browser.

    The browser sends this every 5 seconds to indicate it's still open.
    The desktop app monitors the timestamp to detect browser closure.

    Returns:
        JSON response with status.
    """
    current_app.config["LAST_HEARTBEAT"] = time.time()
    return jsonify({"status": "ok"})


@heartbeat_bp.route("/api/heartbeat", methods=["GET"])
def heartbeat_status():
    """Get current heartbeat status.

    Returns:
        JSON with last heartbeat timestamp and age.
    """
    last = current_app.config.get("LAST_HEARTBEAT", 0)
    age = time.time() - last if last else None
    return jsonify({
        "last_heartbeat": last,
        "age_seconds": age,
        "browser_connected": age is not None and age < 15,
    })
