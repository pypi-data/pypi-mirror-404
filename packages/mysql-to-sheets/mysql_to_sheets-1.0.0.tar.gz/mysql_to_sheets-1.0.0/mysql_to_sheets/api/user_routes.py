"""User and organization management API routes."""

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mysql_to_sheets.api.middleware import (
    get_current_organization_id,
    require_permission,
)
from mysql_to_sheets.api.schemas import MessageResponse
from mysql_to_sheets.core.auth import hash_password, validate_password_strength
from mysql_to_sheets.core.rbac import (
    can_manage_role,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.organizations import (
    get_organization_repository,
)
from mysql_to_sheets.models.users import (
    VALID_ROLES,
    User,
    get_user_repository,
)

# Request/Response Models


class CreateUserRequest(BaseModel):
    """Request body for creating/inviting a user."""

    email: str = Field(..., min_length=5, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    role: str = Field(default="viewer", description="User role: admin, operator, viewer")
    password: str | None = Field(
        default=None,
        min_length=8,
        description="Password (generated if not provided)",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "operator", "viewer"):
            raise ValueError("Role must be admin, operator, or viewer")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "display_name": "New User",
                "role": "operator",
            }
        }
    )


class UpdateUserRequest(BaseModel):
    """Request body for updating a user."""

    display_name: str | None = Field(default=None, max_length=255)
    role: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {VALID_ROLES}")
        return v


class UserResponse(BaseModel):
    """Response body for user data."""

    id: int
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: str | None
    last_login_at: str | None
    organization_id: int


class UserListResponse(BaseModel):
    """Response body for user list."""

    users: list[UserResponse]
    total: int
    limit: int
    offset: int


class UpdateOrganizationRequest(BaseModel):
    """Request body for updating organization."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    settings: dict[str, Any] | None = Field(default=None)


class OrganizationResponse(BaseModel):
    """Response body for organization data."""

    id: int
    name: str
    slug: str
    is_active: bool
    created_at: str | None
    settings: dict[str, Any] | None
    subscription_tier: str
    max_users: int
    max_configs: int


# Routers

users_router = APIRouter(prefix="/users", tags=["users"])
org_router = APIRouter(prefix="/organization", tags=["organization"])


# User management endpoints


@users_router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="List all users in the current organization.",
)
async def list_users(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_inactive: bool = Query(default=False),
    user: User = Depends(require_permission("VIEW_USERS")),
    org_id: int = Depends(get_current_organization_id),
) -> UserListResponse:
    """List users in the current organization.

    Args:
        limit: Maximum number of users to return.
        offset: Number of users to skip.
        include_inactive: Whether to include inactive users.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        List of users with pagination info.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    users = user_repo.get_all(
        organization_id=org_id,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    total = user_repo.count(org_id, include_inactive=include_inactive)

    return UserListResponse(
        users=[
            UserResponse(
                id=u.id if u.id is not None else 0,
                email=u.email,
                display_name=u.display_name,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at.isoformat() if u.created_at else None,
                last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
                organization_id=u.organization_id,
            )
            for u in users
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@users_router.post(
    "",
    response_model=UserResponse,
    summary="Create user",
    description="Invite a new user to the organization.",
)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_permission("MANAGE_USERS")),
    org_id: int = Depends(get_current_organization_id),
) -> UserResponse:
    """Create/invite a new user.

    Args:
        request: User creation request.
        current_user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Created user data.

    Raises:
        HTTPException: On validation or quota errors.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)
    org_repo = get_organization_repository(db_path)

    # Check if current user can assign the requested role
    if not can_manage_role(current_user.role, request.role):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "AuthorizationError",
                "message": f"Cannot assign role '{request.role}' with your current role",
            },
        )

    # Check organization quota
    org = org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Organization not found"},
        )

    current_count = user_repo.count(org_id)
    if current_count >= org.max_users:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "QuotaExceeded",
                "message": f"Organization has reached maximum users ({org.max_users})",
            },
        )

    # Generate or validate password
    import secrets

    if request.password:
        valid, errors = validate_password_strength(request.password)
        if not valid:
            raise HTTPException(
                status_code=400,
                detail={"error": "ValidationError", "message": "; ".join(errors)},
            )
        password = request.password
    else:
        # Generate random password (user will need to reset)
        password = secrets.token_urlsafe(16)

    password_hash = hash_password(password)

    # Create user
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        display_name=request.display_name or request.email.split("@")[0],
        role=request.role,
        organization_id=org_id,
    )

    try:
        new_user = user_repo.create(new_user)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    # Note: Invitation email with temporary password is deferred to the
    # notification service (see STANDALONE_PROJECTS.md). For now, the admin
    # creating the user must communicate credentials out-of-band.

    if new_user.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "User creation failed"},
        )

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        display_name=new_user.display_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() if new_user.created_at else None,
        last_login_at=None,
        organization_id=new_user.organization_id,
    )


@users_router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
    description="Get a specific user by ID.",
)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_permission("VIEW_USERS")),
    org_id: int = Depends(get_current_organization_id),
) -> UserResponse:
    """Get a specific user.

    Args:
        user_id: User ID to retrieve.
        current_user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        User data.

    Raises:
        HTTPException: If user not found.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, org_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "User not found"},
        )

    if user.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "User ID missing"},
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        organization_id=user.organization_id,
    )


@users_router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update a user's profile or role.",
)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(require_permission("MANAGE_USERS")),
    org_id: int = Depends(get_current_organization_id),
) -> UserResponse:
    """Update a user.

    Args:
        user_id: User ID to update.
        request: Update request.
        current_user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Updated user data.

    Raises:
        HTTPException: On validation or authorization errors.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, org_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "User not found"},
        )

    # Check role change permissions
    if request.role is not None and request.role != user.role:
        if not can_manage_role(current_user.role, user.role):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "AuthorizationError",
                    "message": "Cannot modify a user with equal or higher role",
                },
            )
        if not can_manage_role(current_user.role, request.role):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "AuthorizationError",
                    "message": f"Cannot assign role '{request.role}'",
                },
            )
        # Cannot demote owner
        if user.role == "owner":
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "AuthorizationError",
                    "message": "Cannot change owner role. Use ownership transfer instead.",
                },
            )
        user.role = request.role

    if request.display_name is not None:
        user.display_name = request.display_name

    if request.is_active is not None:
        # Cannot deactivate yourself
        if user.id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail={"error": "ValidationError", "message": "Cannot deactivate yourself"},
            )
        # Cannot deactivate owner
        if user.role == "owner":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "ValidationError",
                    "message": "Cannot deactivate organization owner",
                },
            )
        user.is_active = request.is_active

    try:
        user = user_repo.update(user)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    if user.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "User ID missing"},
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        organization_id=user.organization_id,
    )


@users_router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate user",
    description="Deactivate a user account (soft delete).",
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("MANAGE_USERS")),
    org_id: int = Depends(get_current_organization_id),
) -> MessageResponse:
    """Deactivate a user (soft delete).

    Args:
        user_id: User ID to deactivate.
        current_user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Success message.

    Raises:
        HTTPException: On validation or authorization errors.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    user = user_repo.get_by_id(user_id, org_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "User not found"},
        )

    # Cannot deactivate yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "Cannot deactivate yourself"},
        )

    # Cannot deactivate owner
    if user.role == "owner":
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "Cannot deactivate organization owner"},
        )

    # Check role permissions
    if not can_manage_role(current_user.role, user.role):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "AuthorizationError",
                "message": "Cannot deactivate a user with equal or higher role",
            },
        )

    user_repo.deactivate(user_id, org_id)

    return MessageResponse(message=f"User {user.email} has been deactivated")


# Organization management endpoints


@org_router.get(
    "",
    response_model=OrganizationResponse,
    summary="Get organization",
    description="Get the current organization details.",
)
async def get_organization(
    user: User = Depends(require_permission("VIEW_ORGANIZATION")),
    org_id: int = Depends(get_current_organization_id),
) -> OrganizationResponse:
    """Get current organization details.

    Args:
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Organization data.
    """
    db_path = get_tenant_db_path()
    org_repo = get_organization_repository(db_path)

    org = org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Organization not found"},
        )

    if org.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "Organization ID missing"},
        )

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        created_at=org.created_at.isoformat() if org.created_at else None,
        settings=org.settings,
        subscription_tier=org.subscription_tier,
        max_users=org.max_users,
        max_configs=org.max_configs,
    )


@org_router.put(
    "",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update organization settings (owner only).",
)
async def update_organization(
    request: UpdateOrganizationRequest,
    user: User = Depends(require_permission("MANAGE_ORGANIZATION")),
    org_id: int = Depends(get_current_organization_id),
) -> OrganizationResponse:
    """Update organization settings.

    Args:
        request: Update request.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Updated organization data.
    """
    db_path = get_tenant_db_path()
    org_repo = get_organization_repository(db_path)

    org = org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Organization not found"},
        )

    if request.name is not None:
        org.name = request.name

    if request.settings is not None:
        # Merge settings (don't replace entirely)
        current_settings = org.settings or {}
        current_settings.update(request.settings)
        org.settings = current_settings

    try:
        org = org_repo.update(org)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    if org.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "Organization ID missing"},
        )

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        created_at=org.created_at.isoformat() if org.created_at else None,
        settings=org.settings,
        subscription_tier=org.subscription_tier,
        max_users=org.max_users,
        max_configs=org.max_configs,
    )
