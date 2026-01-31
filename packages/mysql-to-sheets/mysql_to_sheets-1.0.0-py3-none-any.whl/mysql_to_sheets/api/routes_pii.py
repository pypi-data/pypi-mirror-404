"""PII API routes for detection, transformation, and policy management."""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from mysql_to_sheets.api.schemas import (
    ErrorResponse,
    PIIAcknowledgmentRequest,
    PIIAcknowledgmentResponse,
    PIIColumnResponse,
    PIIDetectionResponse,
    PIIDetectRequest,
    PIIPolicyResponse,
    PIIPolicyUpdateRequest,
    PIITransformPreviewRequest,
    PIITransformPreviewResponse,
    PIITransformPreviewRow,
)
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, PIIError
from mysql_to_sheets.core.pii import PIITransform, PIITransformConfig
from mysql_to_sheets.core.pii_detection import detect_pii_in_columns
from mysql_to_sheets.core.pii_transform import apply_pii_transforms, get_transform_preview
from mysql_to_sheets.core.tier import check_feature_access, get_tier_from_license

router = APIRouter(prefix="/pii", tags=["PII"])


# Dependency for optional API key authentication
async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str | None:
    """Verify API key header for optional per-route authentication."""
    return x_api_key


def _get_current_tier() -> str:
    """Get the current tier from license or default to FREE."""
    try:
        tier = get_tier_from_license()
        return tier.value
    except Exception:
        return "free"


@router.post(
    "/detect",
    response_model=PIIDetectionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Detection error"},
    },
    summary="Detect PII in query results",
    description="Analyze query results for PII columns using pattern and content detection.",
)
async def detect_pii(
    request: PIIDetectRequest,
    api_key: str | None = Depends(verify_api_key),
) -> PIIDetectionResponse:
    """Detect PII columns in query results."""
    config = get_config()

    # Use request query or fall back to config
    query = request.query or config.sql_query
    if not query:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "No query provided"},
        )

    try:
        # Fetch data from database
        from mysql_to_sheets.core.sync import fetch_data

        headers, rows = fetch_data(config)

        # Limit rows for sampling
        sample_rows = rows[: request.sample_size]

        # Run PII detection
        result = detect_pii_in_columns(
            headers=headers,
            rows=sample_rows,
            confidence_threshold=request.confidence_threshold,
        )

        return PIIDetectionResponse(
            columns=[
                PIIColumnResponse(
                    column_name=col.column_name,
                    category=col.category.value,
                    confidence=col.confidence,
                    suggested_transform=col.suggested_transform.value,
                )
                for col in result.columns
            ],
            has_pii=result.has_pii,
            requires_acknowledgment=result.requires_acknowledgment,
            detection_method="combined",
        )

    except ConfigError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.to_dict())
    except PIIError as e:
        raise HTTPException(status_code=500, detail=e.to_dict())


@router.post(
    "/preview",
    response_model=PIITransformPreviewResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Preview error"},
    },
    summary="Preview PII transformations",
    description="Preview how PII transforms would affect query data.",
)
async def preview_transforms(
    request: PIITransformPreviewRequest,
    api_key: str | None = Depends(verify_api_key),
) -> PIITransformPreviewResponse:
    """Preview PII transformations on sample data."""
    config = get_config()

    # Check tier for advanced transforms
    tier = _get_current_tier()
    for column, transform in request.transform_map.items():
        if transform == "redact" and not check_feature_access(tier, "pii_redact_transform"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "TierError",
                    "message": f"Redact transform requires PRO tier or higher",
                    "feature": "pii_redact_transform",
                },
            )
        if transform == "partial_mask" and not check_feature_access(
            tier, "pii_partial_mask_transform"
        ):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "TierError",
                    "message": f"Partial mask transform requires PRO tier or higher",
                    "feature": "pii_partial_mask_transform",
                },
            )

    # Use request query or fall back to config
    query = request.query or config.sql_query
    if not query:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "No query provided"},
        )

    try:
        from mysql_to_sheets.core.sync import fetch_data

        headers, rows = fetch_data(config)

        # Limit to sample size
        sample_rows = rows[: request.sample_size]

        # Build PII config from request
        transform_map = {
            col: PIITransform(t) for col, t in request.transform_map.items()
        }
        pii_config = PIITransformConfig(
            enabled=True,
            transform_map=transform_map,
        )

        # Get preview
        preview_rows = get_transform_preview(
            headers=headers,
            rows=sample_rows,
            pii_config=pii_config,
        )

        return PIITransformPreviewResponse(
            rows=[
                PIITransformPreviewRow(
                    original=row["original"],
                    transformed=row["transformed"],
                )
                for row in preview_rows
            ],
            columns_transformed=list(request.transform_map.keys()),
            transform_map=request.transform_map,
        )

    except ConfigError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.to_dict())
    except (ValueError, PIIError) as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "PIIError", "message": str(e)},
        )


@router.get(
    "/policies",
    response_model=list[PIIPolicyResponse],
    summary="List PII policies",
    description="List all PII policies for the organization.",
)
async def list_policies(
    org_id: int = Query(..., description="Organization ID"),
    api_key: str | None = Depends(verify_api_key),
) -> list[PIIPolicyResponse]:
    """List PII policies for an organization."""
    # Check tier - org policies require BUSINESS
    tier = _get_current_tier()
    if not check_feature_access(tier, "pii_org_policy"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TierError",
                "message": "Organization PII policies require BUSINESS tier or higher",
                "feature": "pii_org_policy",
            },
        )

    # For now, return empty list until models are implemented
    # This will be populated once PIIPolicyModel is created
    return []


@router.get(
    "/policies/{policy_id}",
    response_model=PIIPolicyResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Policy not found"},
    },
    summary="Get PII policy",
    description="Get a specific PII policy by ID.",
)
async def get_policy(
    policy_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> PIIPolicyResponse:
    """Get a PII policy by ID."""
    # Check tier
    tier = _get_current_tier()
    if not check_feature_access(tier, "pii_org_policy"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TierError",
                "message": "Organization PII policies require BUSINESS tier or higher",
                "feature": "pii_org_policy",
            },
        )

    # Placeholder - will be implemented with models
    raise HTTPException(
        status_code=404,
        detail={"error": "NotFound", "message": f"Policy {policy_id} not found"},
    )


@router.put(
    "/policies/{policy_id}",
    response_model=PIIPolicyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Policy not found"},
    },
    summary="Update PII policy",
    description="Update an existing PII policy.",
)
async def update_policy(
    policy_id: int,
    request: PIIPolicyUpdateRequest,
    api_key: str | None = Depends(verify_api_key),
) -> PIIPolicyResponse:
    """Update a PII policy."""
    # Check tier
    tier = _get_current_tier()
    if not check_feature_access(tier, "pii_org_policy"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TierError",
                "message": "Organization PII policies require BUSINESS tier or higher",
                "feature": "pii_org_policy",
            },
        )

    # Check block_unacknowledged requires ENTERPRISE
    if request.block_unacknowledged is not None and request.block_unacknowledged:
        if not check_feature_access(tier, "pii_block_unacknowledged"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "TierError",
                    "message": "Blocking unacknowledged PII requires ENTERPRISE tier",
                    "feature": "pii_block_unacknowledged",
                },
            )

    # Placeholder - will be implemented with models
    raise HTTPException(
        status_code=404,
        detail={"error": "NotFound", "message": f"Policy {policy_id} not found"},
    )


@router.post(
    "/acknowledge",
    response_model=PIIAcknowledgmentResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Config not found"},
    },
    summary="Acknowledge PII column",
    description="Record acknowledgment that a PII column has been reviewed and approved.",
)
async def acknowledge_pii(
    request: PIIAcknowledgmentRequest,
    api_key: str | None = Depends(verify_api_key),
) -> PIIAcknowledgmentResponse:
    """Acknowledge PII in a sync configuration."""
    # Validate transform type
    try:
        PIITransform(request.transform)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": f"Invalid transform: {request.transform}. "
                f"Valid values: none, hash, redact, partial_mask",
            },
        )

    # Check tier for advanced transforms
    tier = _get_current_tier()
    if request.transform == "redact" and not check_feature_access(
        tier, "pii_redact_transform"
    ):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TierError",
                "message": "Redact transform requires PRO tier or higher",
                "feature": "pii_redact_transform",
            },
        )
    if request.transform == "partial_mask" and not check_feature_access(
        tier, "pii_partial_mask_transform"
    ):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "TierError",
                "message": "Partial mask transform requires PRO tier or higher",
                "feature": "pii_partial_mask_transform",
            },
        )

    # Placeholder - will be implemented with models
    # For now, return a mock response
    from datetime import datetime, timezone

    return PIIAcknowledgmentResponse(
        id=1,
        sync_config_id=request.config_id,
        column_name=request.column_name,
        category=request.category,
        transform=request.transform,
        acknowledged_by_user_id=1,  # Placeholder until auth integration
        acknowledged_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/acknowledgments",
    response_model=list[PIIAcknowledgmentResponse],
    summary="List PII acknowledgments",
    description="List all PII acknowledgments for a sync configuration.",
)
async def list_acknowledgments(
    config_id: int = Query(..., description="Sync configuration ID"),
    api_key: str | None = Depends(verify_api_key),
) -> list[PIIAcknowledgmentResponse]:
    """List PII acknowledgments for a sync config."""
    # Placeholder - will be implemented with models
    return []
