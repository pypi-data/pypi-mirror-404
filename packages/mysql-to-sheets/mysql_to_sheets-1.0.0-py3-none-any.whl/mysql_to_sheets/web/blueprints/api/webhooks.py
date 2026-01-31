"""Webhooks API blueprint for web dashboard.

Handles webhook subscription CRUD operations via AJAX (multi-tenant).
"""

import logging
import secrets
from typing import Any

from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.blueprints.api.auth_helpers import (
    _get_user_or_401,
    _require_admin,
)
from mysql_to_sheets.web.context import get_current_user

logger = logging.getLogger("mysql_to_sheets.web.api.webhooks")

webhooks_api_bp = Blueprint("webhooks_api", __name__, url_prefix="/api/webhooks")


@webhooks_api_bp.route("", methods=["GET"])
def list_webhooks() -> tuple[Response, int]:
    """List webhook subscriptions in current organization.

    Query params:
    - include_inactive: If true, include inactive webhooks

    Returns:
        JSON response with webhook list.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.webhooks import get_webhook_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhooks = webhook_repo.get_all_subscriptions(
        organization_id=current["organization_id"],
        include_inactive=include_inactive,
    )

    return jsonify(
        {
            "success": True,
            "webhooks": [w.to_dict() for w in webhooks],
            "total": len(webhooks),
        }
    ), 200


@webhooks_api_bp.route("", methods=["POST"])
def create_webhook() -> tuple[Response, int]:
    """Create a new webhook subscription in current organization.

    Expects JSON body with:
    - name: Webhook name (required)
    - url: Target URL (required)
    - events: List of event types to subscribe to (required)
    - secret: Webhook secret (optional, auto-generated if not provided)

    Returns:
        JSON response with created webhook.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.webhooks import WebhookSubscription, get_webhook_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    # Validation
    if not data.get("name"):
        return jsonify(
            {"success": False, "error": "Name is required", "message": "Name is required"}
        ), 400
    if not data.get("url"):
        return jsonify(
            {"success": False, "error": "URL is required", "message": "URL is required"}
        ), 400
    if not data.get("events"):
        return jsonify(
            {
                "success": False,
                "error": "Events list is required",
                "message": "Events list is required",
            }
        ), 400

    # Generate secret if not provided
    secret = data.get("secret") or f"whsec_{secrets.token_hex(32)}"

    try:
        db_path = get_tenant_db_path()
        webhook_repo = get_webhook_repository(db_path)

        # Enforce tier quota for webhooks
        from mysql_to_sheets.core.tier import enforce_quota
        from mysql_to_sheets.models.organizations import get_organization_repository

        org_repo = get_organization_repository(db_path)
        org = org_repo.get_by_id(current["organization_id"])
        if org:
            org_tier = org.subscription_tier or "free"
            existing_webhooks = webhook_repo.get_all_subscriptions(
                organization_id=current["organization_id"],
                include_inactive=False,
            )
            try:
                enforce_quota(
                    org_tier,
                    "webhooks",
                    len(existing_webhooks),
                    organization_id=current["organization_id"],
                )
            except Exception as e:  # TierError not exported
                error_msg = str(e)
                return jsonify(
                    {
                        "success": False,
                        "error": error_msg,
                        "message": error_msg,
                        "upgrade_required": True,
                        "current_tier": org_tier,
                    }
                ), 403

        webhook = WebhookSubscription(
            name=data["name"].strip(),
            organization_id=current["organization_id"],
            url=data["url"],
            events=data["events"],
            secret=secret,
            created_by_user_id=current["id"],
        )

        webhook = webhook_repo.create_subscription(webhook)

        return jsonify(
            {
                "success": True,
                "webhook": webhook.to_dict(),
            }
        ), 201

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400
    except Exception as e:
        logger.exception(f"Error creating webhook: {e}")
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 500


@webhooks_api_bp.route("/<int:webhook_id>", methods=["GET"])
def get_webhook(webhook_id: int) -> tuple[Response, int]:
    """Get a webhook subscription by ID.

    Returns:
        JSON response with webhook details.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.webhooks import get_webhook_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(
        webhook_id, organization_id=current["organization_id"]
    )

    if not webhook:
        return jsonify(
            {
                "success": False,
                "error": f"Webhook {webhook_id} not found",
                "message": f"Webhook {webhook_id} not found",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "webhook": webhook.to_dict(),
        }
    ), 200


@webhooks_api_bp.route("/<int:webhook_id>", methods=["PUT"])
def update_webhook(webhook_id: int) -> tuple[Response, int]:
    """Update a webhook subscription.

    Returns:
        JSON response with updated webhook.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.webhooks import get_webhook_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(
        webhook_id, organization_id=current["organization_id"]
    )

    if not webhook:
        return jsonify(
            {
                "success": False,
                "error": f"Webhook {webhook_id} not found",
                "message": f"Webhook {webhook_id} not found",
            }
        ), 404

    # Apply updates
    if "name" in data:
        webhook.name = data["name"].strip()
    if "url" in data:
        webhook.url = data["url"]
    if "events" in data:
        webhook.events = data["events"]
    if "secret" in data:
        webhook.secret = data["secret"]
    if "is_active" in data:
        webhook.is_active = data["is_active"]

    try:
        webhook = webhook_repo.update_subscription(webhook)
        return jsonify(
            {
                "success": True,
                "webhook": webhook.to_dict(),
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400


@webhooks_api_bp.route("/<int:webhook_id>", methods=["DELETE"])
def delete_webhook(webhook_id: int) -> tuple[Response, int]:
    """Deactivate a webhook subscription.

    Query params:
    - hard: If true, permanently delete instead of deactivate

    Returns:
        JSON response confirming deletion.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.webhooks import get_webhook_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    hard_delete = request.args.get("hard", "false").lower() == "true"

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(
        webhook_id, organization_id=current["organization_id"]
    )

    if not webhook:
        return jsonify(
            {
                "success": False,
                "error": f"Webhook {webhook_id} not found",
                "message": f"Webhook {webhook_id} not found",
            }
        ), 404

    if hard_delete:
        webhook_repo.delete_subscription(webhook_id, organization_id=current["organization_id"])
        message = f"Webhook '{webhook.name}' permanently deleted"
    else:
        # Deactivate by updating is_active flag
        webhook.is_active = False
        webhook_repo.update_subscription(webhook)
        message = f"Webhook '{webhook.name}' deactivated"

    return jsonify(
        {
            "success": True,
            "message": message,
        }
    ), 200


@webhooks_api_bp.route("/<int:webhook_id>/test", methods=["POST"])
def test_webhook(webhook_id: int) -> tuple[Response, int]:
    """Send a test event to a webhook.

    Returns:
        JSON response with delivery result.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.core.webhooks.delivery import get_webhook_delivery_service
    from mysql_to_sheets.models.webhooks import get_webhook_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(
        webhook_id, organization_id=current["organization_id"]
    )

    if not webhook:
        return jsonify(
            {
                "success": False,
                "error": f"Webhook {webhook_id} not found",
                "message": f"Webhook {webhook_id} not found",
            }
        ), 404

    try:
        delivery_service = get_webhook_delivery_service(db_path)

        result = delivery_service.deliver_test(webhook)  # type: ignore[attr-defined]  # noqa

        return jsonify(
            {
                "success": result.success,
                "status_code": result.status_code,
                "response_body": result.response_body[:500] if result.response_body else None,
                "error": result.error,
                "duration_ms": result.duration_ms,
            }
        ), 200

    except Exception as e:
        logger.exception(f"Error testing webhook {webhook_id}: {e}")
        return jsonify(
            {
                "success": False,
                "error": str(e),
                "message": str(e),
            }
        ), 500


@webhooks_api_bp.route("/<int:webhook_id>/rotate-secret", methods=["POST"])
def rotate_webhook_secret(webhook_id: int) -> tuple[Response, int]:
    """Rotate a webhook's secret.

    Returns:
        JSON response with updated webhook including new secret.
    """
    auth_error = _require_admin()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.webhooks import get_webhook_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(
        webhook_id, organization_id=current["organization_id"]
    )

    if not webhook:
        return jsonify(
            {
                "success": False,
                "error": f"Webhook {webhook_id} not found",
                "message": f"Webhook {webhook_id} not found",
            }
        ), 404

    # Generate new secret
    webhook.secret = f"whsec_{secrets.token_hex(32)}"

    try:
        webhook = webhook_repo.update_subscription(webhook)
        return jsonify(
            {
                "success": True,
                "webhook": webhook.to_dict(),
                "message": "Secret rotated successfully",
            }
        ), 200

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "message": str(e)}), 400
