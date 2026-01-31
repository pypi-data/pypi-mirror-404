"""Configs API blueprint for web dashboard.

Handles sync config CRUD operations via AJAX (multi-tenant).
"""

import logging

from flask import Blueprint, Response, jsonify, request

from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.web.blueprints.api.auth_helpers import (
    _get_user_or_401,
    _require_login,
    _require_operator,
)
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.responses import (
    error_response,
    not_found_response,
    success_response,
)

logger = logging.getLogger("mysql_to_sheets.web.api.configs")

configs_api_bp = Blueprint("configs_api", __name__, url_prefix="/api/configs")


@configs_api_bp.route("", methods=["GET"])
def list_configs() -> tuple[Response, int]:
    """List sync configs in current organization.

    Query params:
    - include_inactive: If true, include inactive configs

    Returns:
        JSON response with config list.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    configs = config_repo.get_all(
        organization_id=current["organization_id"],
    )

    return success_response({"configs": [c.to_dict() for c in configs], "total": len(configs)})


@configs_api_bp.route("", methods=["POST"])
def create_config() -> tuple[Response, int]:
    """Create a new sync config in current organization.

    Expects JSON body with:
    - name: Config name (required)
    - sheet_id: Google Sheet ID (required)
    - worksheet_name: Worksheet name (optional)
    - sql_query: SQL query (optional)
    - sync_mode: Sync mode (optional)

    Returns:
        JSON response with created config.
    """
    auth_error = _require_operator()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.sync_configs import SyncConfigDefinition, get_sync_config_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    # Validation
    if not data.get("name"):
        return error_response("VALIDATION_ERROR", "Name is required")
    if not data.get("sheet_id"):
        return error_response("VALIDATION_ERROR", "Sheet ID is required")

    # Parse sheet_id if it's a URL
    from mysql_to_sheets.core.sheets_utils import parse_sheet_id

    try:
        parsed_sheet_id = parse_sheet_id(data["sheet_id"])
    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e))

    try:
        db_path = get_tenant_db_path()
        config_repo = get_sync_config_repository(db_path)

        # Enforce tier quota for configs
        from mysql_to_sheets.core.tier import enforce_quota
        from mysql_to_sheets.models.organizations import get_organization_repository

        org_repo = get_organization_repository(db_path)
        org = org_repo.get_by_id(current["organization_id"])
        if org:
            org_tier = org.subscription_tier or "free"
            existing_configs = config_repo.get_all(
                organization_id=current["organization_id"],
            )
            try:
                enforce_quota(
                    org_tier,
                    "configs",
                    len(existing_configs),
                    organization_id=current["organization_id"],
                )
            except Exception as e:  # TierError not exported
                return error_response(
                    "TIER_QUOTA_EXCEEDED",
                    str(e),
                    status_code=403,
                    details={"upgrade_required": True, "current_tier": org_tier},
                )

        config = SyncConfigDefinition(
            name=data["name"].strip(),
            organization_id=current["organization_id"],
            sheet_id=parsed_sheet_id,
            worksheet_name=data.get("worksheet_name", "Sheet1"),
            sql_query=data.get("sql_query") or "",
            sync_mode=data.get("sync_mode", "replace"),
            column_mapping=data.get("column_mapping"),
            column_order=data.get("column_order"),
            column_case=data.get("column_case") or "none",
            created_by_user_id=current["id"],
        )

        config = config_repo.create(config)

        return success_response({"config": config.to_dict()}, status_code=201)

    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e))
    except Exception as e:
        logger.exception(f"Error creating config: {e}")
        return error_response("INTERNAL_ERROR", str(e), status_code=500)


@configs_api_bp.route("/<int:config_id>", methods=["GET"])
def get_config(config_id: int) -> tuple[Response, int]:
    """Get a sync config by ID.

    Returns:
        JSON response with config details.
    """
    auth_error = _require_login()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_id(config_id, organization_id=current["organization_id"])

    if not config:
        return not_found_response("Config", config_id)

    return success_response({"config": config.to_dict()})


@configs_api_bp.route("/<int:config_id>", methods=["PUT"])
def update_config(config_id: int) -> tuple[Response, int]:
    """Update a sync config.

    Returns:
        JSON response with updated config.
    """
    auth_error = _require_operator()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    data = request.get_json() or {}
    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_id(config_id, organization_id=current["organization_id"])

    if not config:
        return not_found_response("Config", config_id)

    # Apply updates
    if "name" in data:
        config.name = data["name"].strip()
    if "sheet_id" in data:
        from mysql_to_sheets.core.sheets_utils import parse_sheet_id

        try:
            config.sheet_id = parse_sheet_id(data["sheet_id"])
        except ValueError as e:
            return error_response("VALIDATION_ERROR", str(e))
    if "worksheet_name" in data:
        config.worksheet_name = data["worksheet_name"]
    if "sql_query" in data:
        config.sql_query = data["sql_query"]
    if "sync_mode" in data:
        config.sync_mode = data["sync_mode"]
    if "column_mapping" in data:
        config.column_mapping = data["column_mapping"]
    if "column_order" in data:
        config.column_order = data["column_order"]
    if "column_case" in data:
        config.column_case = data["column_case"]
    if "enabled" in data:
        config.enabled = data["enabled"]

    try:
        config = config_repo.update(config)
        return success_response({"config": config.to_dict()})

    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e))


@configs_api_bp.route("/<int:config_id>", methods=["DELETE"])
def delete_config(config_id: int) -> tuple[Response, int]:
    """Deactivate a sync config.

    Query params:
    - hard: If true, permanently delete instead of deactivate

    Returns:
        JSON response confirming deletion.
    """
    auth_error = _require_operator()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    hard_delete = request.args.get("hard", "false").lower() == "true"

    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_id(config_id, organization_id=current["organization_id"])

    if not config:
        return not_found_response("Config", config_id)

    if hard_delete:
        config_repo.delete(config_id, organization_id=current["organization_id"])
        message = f"Config '{config.name}' permanently deleted"
    else:
        config_repo.disable(config_id, organization_id=current["organization_id"])
        message = f"Config '{config.name}' deactivated"

    return success_response({"message": message})


@configs_api_bp.route("/<int:config_id>/sync", methods=["POST"])
def run_config_sync(config_id: int) -> tuple[Response, int]:
    """Run sync for a specific config.

    Returns:
        JSON response with sync result.
    """
    auth_error = _require_operator()
    if auth_error:
        return jsonify(auth_error[0]), auth_error[1]

    from mysql_to_sheets.core.config import get_config, reset_config
    from mysql_to_sheets.core.sync import run_sync
    from mysql_to_sheets.models.sync_configs import get_sync_config_repository

    current = get_current_user()
    user_result = _get_user_or_401(current)
    if isinstance(user_result, tuple):
        return jsonify(user_result[0]), user_result[1]
    current = user_result

    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    sync_config = config_repo.get_by_id(config_id, organization_id=current["organization_id"])

    if not sync_config:
        return not_found_response("Config", config_id)

    if not sync_config.enabled:
        return error_response("CONFIG_INACTIVE", "Config is inactive")

    try:
        # Get base config and apply overrides from sync config
        reset_config()
        base_config = get_config()

        overrides = {
            "google_sheet_id": sync_config.sheet_id,
            "google_worksheet_name": sync_config.worksheet_name,
        }
        if sync_config.sql_query:
            overrides["sql_query"] = sync_config.sql_query

        config = base_config.with_overrides(**overrides)
        result = run_sync(config)

        # Build response - ensure message is never None for failures
        message = result.message
        if not result.success and not message:
            message = result.error or "Sync failed"

        return success_response({
            "rows_synced": result.rows_synced,
            "columns": result.columns,
            "message": message,
            "error": result.error,
        })

    except Exception as e:
        logger.exception(f"Error running sync for config {config_id}: {e}")
        return error_response("SYNC_ERROR", str(e), status_code=500)
