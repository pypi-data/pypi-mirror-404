"""Server-Sent Events (SSE) endpoint for real-time sync progress.

This module provides an SSE streaming endpoint that clients can connect to
for real-time sync progress updates.
"""

import logging
import uuid
from typing import Generator

from flask import Blueprint, Response, g, jsonify, request, stream_with_context

logger = logging.getLogger(__name__)

progress_sse_bp = Blueprint("progress_sse", __name__, url_prefix="/api/sync/progress")


@progress_sse_bp.route("/stream")
def progress_stream() -> Response:
    """SSE endpoint for sync progress streaming.

    Clients connect here to receive real-time progress events.
    Events are streamed in SSE format with automatic reconnection support.

    Query parameters:
        sync_id: Optional filter for specific sync operation.

    Returns:
        SSE event stream response.
    """
    from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

    # Generate unique client ID
    client_id = str(uuid.uuid4())
    sync_id_filter = request.args.get("sync_id")

    logger.debug(f"SSE client connected: {client_id}")

    def generate() -> Generator[str, None, None]:
        """Generate SSE events."""
        import json
        import queue

        emitter = get_progress_emitter()
        q = emitter.create_sse_queue(client_id)

        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'client_id': client_id})}\n\n"

            while True:
                try:
                    event = q.get(timeout=30.0)
                    event_type = event.get("type", "message")
                    data = event.get("data", {})

                    # Filter by sync_id if specified
                    if sync_id_filter and data.get("sync_id") != sync_id_filter:
                        continue

                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

                    # If this is a complete event, optionally close the stream
                    if event_type == "complete" and sync_id_filter:
                        logger.debug(
                            f"Sync {sync_id_filter} complete, closing stream for {client_id}"
                        )
                        break

                except queue.Empty:
                    # Send keepalive comment every 30 seconds
                    yield ": keepalive\n\n"

        except GeneratorExit:
            logger.debug(f"SSE client disconnected: {client_id}")
        finally:
            emitter.remove_sse_queue(client_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@progress_sse_bp.route("/current")
def get_current_progress() -> Response:
    """Get current progress state for all active syncs.

    Returns:
        JSON response with current progress states.
    """
    from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

    emitter = get_progress_emitter()
    sync_id = request.args.get("sync_id")

    if sync_id:
        progress = emitter.get_current_progress(sync_id)
        if progress:
            return jsonify({"success": True, "progress": progress.to_dict()})
        return jsonify({"success": False, "error": "No active sync found"}), 404

    # Return all active syncs
    with emitter._lock:
        active = {
            sid: p.to_dict() for sid, p in emitter._current_progress.items()
        }

    return jsonify({"success": True, "active_syncs": active})


@progress_sse_bp.route("/logs/<sync_id>")
def get_sync_logs(sync_id: str) -> Response:
    """Get logs for a specific sync operation.

    Args:
        sync_id: The sync operation ID.

    Returns:
        JSON response with log entries.
    """
    from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

    emitter = get_progress_emitter()
    logs = emitter.get_logs(sync_id)

    return jsonify({
        "success": True,
        "sync_id": sync_id,
        "logs": [log.to_dict() for log in logs],
    })
