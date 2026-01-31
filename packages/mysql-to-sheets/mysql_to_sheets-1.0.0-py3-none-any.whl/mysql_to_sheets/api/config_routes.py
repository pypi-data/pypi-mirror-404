"""Sync configuration management API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from mysql_to_sheets.api.middleware import (
    get_current_organization_id,
    require_permission,
)
from mysql_to_sheets.api.schemas import MessageResponse
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, SheetsError
from mysql_to_sheets.core.sync import run_sync
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.sync_configs import (
    VALID_COLUMN_CASES,
    VALID_SYNC_MODES,
    SyncConfigDefinition,
    get_sync_config_repository,
)
from mysql_to_sheets.models.users import User

router = APIRouter(prefix="/configs", tags=["configs"])


# Request/Response Models


class CreateConfigRequest(BaseModel):
    """Request body for creating a sync configuration."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    sql_query: str = Field(..., min_length=1)
    sheet_id: str = Field(..., min_length=1, max_length=100)
    worksheet_name: str = Field(default="Sheet1", max_length=100)
    column_mapping: dict[str, str] | None = Field(default=None)
    column_order: list[str] | None = Field(default=None)
    column_case: str = Field(default="none")
    sync_mode: str = Field(default="replace")
    enabled: bool = Field(default=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "customers",
                "description": "Sync active customers to Google Sheets",
                "sql_query": "SELECT id, name, email FROM customers WHERE active = 1",
                "sheet_id": "abc123",
                "worksheet_name": "Customers",
                "column_mapping": {"id": "Customer ID", "name": "Full Name"},
                "sync_mode": "replace",
            }
        }
    )


class UpdateConfigRequest(BaseModel):
    """Request body for updating a sync configuration."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    sql_query: str | None = Field(default=None, min_length=1)
    sheet_id: str | None = Field(default=None, min_length=1, max_length=100)
    worksheet_name: str | None = Field(default=None, max_length=100)
    column_mapping: dict[str, str] | None = Field(default=None)
    column_order: list[str] | None = Field(default=None)
    column_case: str | None = Field(default=None)
    sync_mode: str | None = Field(default=None)
    enabled: bool | None = Field(default=None)


class ConfigResponse(BaseModel):
    """Response body for sync configuration."""

    id: int
    name: str
    description: str
    sql_query: str
    sheet_id: str
    worksheet_name: str
    column_mapping: dict[str, str] | None
    column_order: list[str] | None
    column_case: str
    sync_mode: str
    enabled: bool
    created_at: str | None
    updated_at: str | None
    created_by_user_id: int | None
    organization_id: int


class ConfigListResponse(BaseModel):
    """Response body for config list."""

    configs: list[ConfigResponse]
    total: int
    limit: int
    offset: int


class RunConfigRequest(BaseModel):
    """Request to run sync by config name(s)."""

    config_name: str | None = Field(default=None, description="Single config name to run")
    config_names: list[str] | None = Field(default=None, description="Multiple config names to run")
    dry_run: bool = Field(default=False, description="Validate without pushing")
    preview: bool = Field(default=False, description="Show diff without pushing")


class SyncResultResponse(BaseModel):
    """Response for a single sync result."""

    config_name: str
    success: bool
    rows_synced: int = 0
    message: str = ""
    error: str | None = None


class MultiSyncResponse(BaseModel):
    """Response for running multiple configs."""

    results: list[SyncResultResponse]
    total_success: int
    total_failed: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Helper function


def config_to_response(config: SyncConfigDefinition) -> ConfigResponse:
    """Convert SyncConfigDefinition to ConfigResponse."""
    if config.id is None:
        raise ValueError("Config ID cannot be None")

    return ConfigResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        sql_query=config.sql_query,
        sheet_id=config.sheet_id,
        worksheet_name=config.worksheet_name,
        column_mapping=config.column_mapping,
        column_order=config.column_order,
        column_case=config.column_case,
        sync_mode=config.sync_mode,
        enabled=config.enabled,
        created_at=config.created_at.isoformat() if config.created_at else None,
        updated_at=config.updated_at.isoformat() if config.updated_at else None,
        created_by_user_id=config.created_by_user_id,
        organization_id=config.organization_id,
    )


# Endpoints


@router.get(
    "",
    response_model=ConfigListResponse,
    summary="List sync configurations",
    description="List all sync configurations in the organization.",
)
async def list_configs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    enabled_only: bool = Query(default=False),
    user: User = Depends(require_permission("VIEW_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigListResponse:
    """List sync configurations.

    Args:
        limit: Maximum number of configs to return.
        offset: Number of configs to skip.
        enabled_only: Whether to return only enabled configs.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        List of configurations with pagination info.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    configs = config_repo.get_all(
        organization_id=org_id,
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )
    total = config_repo.count(org_id, enabled_only=enabled_only)

    return ConfigListResponse(
        configs=[config_to_response(c) for c in configs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ConfigResponse,
    summary="Create sync configuration",
    description="Create a new sync configuration.",
)
async def create_config(
    request: CreateConfigRequest,
    user: User = Depends(require_permission("EDIT_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigResponse:
    """Create a new sync configuration.

    Args:
        request: Configuration data.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Created configuration.

    Raises:
        HTTPException: On validation errors.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    # Validate sync_mode and column_case
    if request.sync_mode not in VALID_SYNC_MODES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": f"Invalid sync_mode. Must be one of: {VALID_SYNC_MODES}",
            },
        )
    if request.column_case not in VALID_COLUMN_CASES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": f"Invalid column_case. Must be one of: {VALID_COLUMN_CASES}",
            },
        )

    # Check organization quota
    from mysql_to_sheets.models.organizations import get_organization_repository

    org_repo = get_organization_repository(db_path)
    org = org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Organization not found"},
        )

    current_count = config_repo.count(org_id)
    if current_count >= org.max_configs:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "QuotaExceeded",
                "message": f"Organization has reached maximum configs ({org.max_configs})",
            },
        )

    config = SyncConfigDefinition(
        name=request.name,
        description=request.description,
        sql_query=request.sql_query,
        sheet_id=request.sheet_id,
        worksheet_name=request.worksheet_name,
        column_mapping=request.column_mapping,
        column_order=request.column_order,
        column_case=request.column_case,
        sync_mode=request.sync_mode,
        enabled=request.enabled,
        created_by_user_id=user.id,
        organization_id=org_id,
    )

    try:
        config = config_repo.create(config)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    return config_to_response(config)


@router.get(
    "/{config_id}",
    response_model=ConfigResponse,
    summary="Get sync configuration",
    description="Get a specific sync configuration by ID.",
)
async def get_config_by_id(
    config_id: int,
    user: User = Depends(require_permission("VIEW_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigResponse:
    """Get a sync configuration by ID.

    Args:
        config_id: Configuration ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Configuration data.

    Raises:
        HTTPException: If configuration not found.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_id(config_id, org_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    return config_to_response(config)


@router.get(
    "/name/{config_name}",
    response_model=ConfigResponse,
    summary="Get sync configuration by name",
    description="Get a specific sync configuration by name.",
)
async def get_config_by_name(
    config_name: str,
    user: User = Depends(require_permission("VIEW_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigResponse:
    """Get a sync configuration by name.

    Args:
        config_name: Configuration name.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Configuration data.

    Raises:
        HTTPException: If configuration not found.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_name(config_name, org_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"Configuration '{config_name}' not found"},
        )

    return config_to_response(config)


@router.put(
    "/{config_id}",
    response_model=ConfigResponse,
    summary="Update sync configuration",
    description="Update an existing sync configuration.",
)
async def update_config(
    config_id: int,
    request: UpdateConfigRequest,
    user: User = Depends(require_permission("EDIT_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigResponse:
    """Update a sync configuration.

    Args:
        config_id: Configuration ID.
        request: Update data.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Updated configuration.

    Raises:
        HTTPException: On validation errors.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_id(config_id, org_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    # Apply updates
    if request.name is not None:
        config.name = request.name
    if request.description is not None:
        config.description = request.description
    if request.sql_query is not None:
        config.sql_query = request.sql_query
    if request.sheet_id is not None:
        config.sheet_id = request.sheet_id
    if request.worksheet_name is not None:
        config.worksheet_name = request.worksheet_name
    if request.column_mapping is not None:
        config.column_mapping = request.column_mapping
    if request.column_order is not None:
        config.column_order = request.column_order
    if request.column_case is not None:
        if request.column_case not in VALID_COLUMN_CASES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ValidationError",
                    "message": f"Invalid column_case. Must be one of: {VALID_COLUMN_CASES}",
                },
            )
        config.column_case = request.column_case
    if request.sync_mode is not None:
        if request.sync_mode not in VALID_SYNC_MODES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ValidationError",
                    "message": f"Invalid sync_mode. Must be one of: {VALID_SYNC_MODES}",
                },
            )
        config.sync_mode = request.sync_mode
    if request.enabled is not None:
        config.enabled = request.enabled

    try:
        config = config_repo.update(config)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    return config_to_response(config)


@router.delete(
    "/{config_id}",
    response_model=MessageResponse,
    summary="Delete sync configuration",
    description="Delete a sync configuration.",
)
async def delete_config(
    config_id: int,
    user: User = Depends(require_permission("DELETE_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> MessageResponse:
    """Delete a sync configuration.

    Args:
        config_id: Configuration ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Success message.

    Raises:
        HTTPException: If configuration not found.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    config = config_repo.get_by_id(config_id, org_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    config_repo.delete(config_id, org_id)

    return MessageResponse(message=f"Configuration '{config.name}' has been deleted")


@router.post(
    "/{config_id}/enable",
    response_model=ConfigResponse,
    summary="Enable sync configuration",
    description="Enable a sync configuration.",
)
async def enable_config(
    config_id: int,
    user: User = Depends(require_permission("EDIT_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigResponse:
    """Enable a sync configuration.

    Args:
        config_id: Configuration ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Updated configuration.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    if not config_repo.enable(config_id, org_id):
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    config = config_repo.get_by_id(config_id, org_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    return config_to_response(config)


@router.post(
    "/{config_id}/disable",
    response_model=ConfigResponse,
    summary="Disable sync configuration",
    description="Disable a sync configuration.",
)
async def disable_config(
    config_id: int,
    user: User = Depends(require_permission("EDIT_CONFIGS")),
    org_id: int = Depends(get_current_organization_id),
) -> ConfigResponse:
    """Disable a sync configuration.

    Args:
        config_id: Configuration ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Updated configuration.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    if not config_repo.disable(config_id, org_id):
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    config = config_repo.get_by_id(config_id, org_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Configuration not found"},
        )

    return config_to_response(config)


@router.post(
    "/run",
    response_model=MultiSyncResponse,
    summary="Run sync by configuration",
    description="Run sync using saved configuration(s).",
)
async def run_by_config(
    request: RunConfigRequest,
    user: User = Depends(require_permission("RUN_SYNC")),
    org_id: int = Depends(get_current_organization_id),
) -> MultiSyncResponse:
    """Run sync using saved configuration(s).

    Args:
        request: Config names to run.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Results for each configuration.
    """
    db_path = get_tenant_db_path()
    config_repo = get_sync_config_repository(db_path)

    # Determine which configs to run
    config_names = []
    if request.config_name:
        config_names.append(request.config_name)
    if request.config_names:
        config_names.extend(request.config_names)

    if not config_names:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "No configuration specified"},
        )

    results = []
    for name in config_names:
        sync_config = config_repo.get_by_name(name, org_id)
        if not sync_config:
            results.append(
                SyncResultResponse(
                    config_name=name,
                    success=False,
                    error=f"Configuration '{name}' not found",
                )
            )
            continue

        if not sync_config.enabled:
            results.append(
                SyncResultResponse(
                    config_name=name,
                    success=False,
                    error=f"Configuration '{name}' is disabled",
                )
            )
            continue

        # Build config overrides from sync_config
        reset_config()
        app_config = get_config()

        import json

        overrides = {
            "google_sheet_id": sync_config.sheet_id,
            "google_worksheet_name": sync_config.worksheet_name,
            "sql_query": sync_config.sql_query,
            "sync_mode": sync_config.sync_mode,
        }

        if sync_config.column_mapping:
            overrides["column_mapping_enabled"] = "true"
            overrides["column_mapping"] = json.dumps(sync_config.column_mapping)
        if sync_config.column_order:
            overrides["column_mapping_enabled"] = "true"
            overrides["column_order"] = ",".join(sync_config.column_order)
        if sync_config.column_case != "none":
            overrides["column_mapping_enabled"] = "true"
            overrides["column_case"] = sync_config.column_case

        app_config = app_config.with_overrides(**overrides)

        try:
            result = run_sync(
                app_config,
                dry_run=request.dry_run,
                preview=request.preview,
            )
            results.append(
                SyncResultResponse(
                    config_name=name,
                    success=result.success,
                    rows_synced=result.rows_synced,
                    message=result.message,
                    error=result.error,
                )
            )
        except (ConfigError, DatabaseError, SheetsError) as e:
            results.append(
                SyncResultResponse(
                    config_name=name,
                    success=False,
                    error=e.message,
                )
            )
        except Exception as e:
            results.append(
                SyncResultResponse(
                    config_name=name,
                    success=False,
                    error=str(e),
                )
            )

    total_success = sum(1 for r in results if r.success)
    total_failed = len(results) - total_success

    return MultiSyncResponse(
        results=results,
        total_success=total_success,
        total_failed=total_failed,
    )
