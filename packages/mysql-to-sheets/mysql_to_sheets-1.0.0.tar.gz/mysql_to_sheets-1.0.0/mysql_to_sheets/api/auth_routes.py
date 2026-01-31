"""Authentication API routes for user management and JWT tokens."""

import re
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mysql_to_sheets.api.middleware import get_current_user
from mysql_to_sheets.core.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    get_auth_config,
    hash_password,
    is_token_blacklisted,
    validate_password_strength,
    verify_password,
    verify_token,
)
from mysql_to_sheets.api.schemas import MessageResponse
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.organizations import (
    Organization,
    get_organization_repository,
)
from mysql_to_sheets.models.users import (
    User,
    get_user_repository,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Request/Response Models


class RegisterRequest(BaseModel):
    """Request body for organization registration."""

    org_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Organization display name",
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Owner email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, uppercase, lowercase, number)",
    )
    display_name: str | None = Field(
        default=None,
        max_length=255,
        description="User display name (defaults to email)",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "org_name": "Acme Corporation",
                "email": "admin@acme.com",
                "password": "SecurePass123",
                "display_name": "Admin User",
            }
        }
    )


class LoginRequest(BaseModel):
    """Request body for login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    org_slug: str | None = Field(
        default=None,
        description="Organization slug (required if email exists in multiple orgs)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "admin@acme.com",
                "password": "SecurePass123",
                "org_slug": "acme-corp",
            }
        }
    )


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class ChangePasswordRequest(BaseModel):
    """Request body for password change."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 chars, uppercase, lowercase, number)",
    )


class UpdateProfileRequest(BaseModel):
    """Request body for profile update."""

    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format if provided."""
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v.lower()


class TokenResponse(BaseModel):
    """Response body with JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiration in seconds")
    organization: dict[str, Any]
    user: dict[str, Any]


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


class OrganizationResponse(BaseModel):
    """Response body for organization data."""

    id: int
    name: str
    slug: str
    is_active: bool
    subscription_tier: str
    max_users: int
    max_configs: int


# Helper functions


def slugify(name: str) -> str:
    """Convert organization name to URL-safe slug.

    Args:
        name: Organization name.

    Returns:
        URL-safe slug.
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)  # Remove special chars
    slug = re.sub(r"[\s_]+", "-", slug)  # Replace spaces/underscores with hyphens
    slug = re.sub(r"-+", "-", slug)  # Remove duplicate hyphens
    slug = slug.strip("-")  # Remove leading/trailing hyphens

    # Add random suffix to ensure uniqueness
    suffix = secrets.token_hex(4)
    return f"{slug}-{suffix}"


# Endpoints


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register new organization",
    description="Create a new organization and owner user account.",
    responses={
        400: {"description": "Invalid request or email already exists"},
    },
)
async def register(request: RegisterRequest) -> TokenResponse:
    """Register a new organization with owner user.

    Creates both the organization and the first user (owner).
    Returns JWT tokens for immediate authentication.

    Args:
        request: Registration request with org and user details.

    Returns:
        JWT tokens and user/organization info.

    Raises:
        HTTPException: On validation or creation errors.
    """
    db_path = get_tenant_db_path()

    # Validate password strength
    valid, errors = validate_password_strength(request.password)
    if not valid:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "; ".join(errors)},
        )

    # Create organization
    org_repo = get_organization_repository(db_path)
    slug = slugify(request.org_name)

    org = Organization(
        name=request.org_name,
        slug=slug,
    )

    try:
        org = org_repo.create(org)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "OrganizationError", "message": str(e)},
        )

    if org.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "Organization creation failed"},
        )

    # Create owner user
    user_repo = get_user_repository(db_path)
    password_hash = hash_password(request.password)

    user = User(
        email=request.email,
        password_hash=password_hash,
        display_name=request.display_name or request.email.split("@")[0],
        role="owner",
        organization_id=org.id,
    )

    try:
        user = user_repo.create(user)
    except ValueError as e:
        # Rollback organization creation
        org_repo.delete(org.id)
        raise HTTPException(
            status_code=400,
            detail={"error": "UserError", "message": str(e)},
        )

    # Generate tokens
    auth_config = get_auth_config()
    access_token = create_access_token(user, auth_config)
    refresh_token = create_refresh_token(user, auth_config)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_config.access_token_expire_minutes * 60,
        organization={
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
        },
        user={
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password to get JWT tokens.",
    responses={
        401: {"description": "Invalid credentials"},
    },
)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT tokens.

    If email exists in multiple organizations, org_slug is required.

    Args:
        request: Login credentials.

    Returns:
        JWT tokens and user/organization info.

    Raises:
        HTTPException: On authentication failure.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)
    org_repo = get_organization_repository(db_path)

    # Find user(s) by email
    if request.org_slug:
        # Specific organization
        org = org_repo.get_by_slug(request.org_slug)
        if not org or org.id is None:
            raise HTTPException(
                status_code=401,
                detail={"error": "AuthenticationError", "message": "Invalid credentials"},
            )
        user = user_repo.get_by_email(request.email, org.id)
    else:
        # Search across orgs
        users = user_repo.get_by_email_any_org(request.email)
        if len(users) > 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "AmbiguousLogin",
                    "message": "Email exists in multiple organizations. Please specify org_slug.",
                },
            )
        user = users[0] if users else None
        if user:
            org = org_repo.get_by_id(user.organization_id)
        else:
            org = None

    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "Invalid credentials"},
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "Invalid credentials"},
        )

    # Check user is active
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "Account is inactive"},
        )

    # Check organization is active
    if not org or not org.is_active:
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "Organization is inactive"},
        )

    if user.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "User ID missing"},
        )

    # Update last login
    user_repo.update_last_login(user.id)

    # Generate tokens
    auth_config = get_auth_config()
    access_token = create_access_token(user, auth_config)
    refresh_token = create_refresh_token(user, auth_config)

    if org.id is None or org.name is None or org.slug is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "Organization data incomplete"},
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_config.access_token_expire_minutes * 60,
        organization={
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
        },
        user={
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Invalidate the current access token.",
)
async def logout(request: Request) -> MessageResponse:
    """Logout and invalidate current token.

    Args:
        request: Current request (to get token from state).

    Returns:
        Success message.
    """
    # Get token payload from middleware
    if hasattr(request.state, "token_payload"):
        payload = request.state.token_payload
        blacklist_token(payload.jti, expires_at=payload.exp, reason="logout")

    return MessageResponse(message="Successfully logged out")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Get new access token using refresh token.",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_tokens(request: RefreshRequest) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request.

    Returns:
        New JWT tokens.

    Raises:
        HTTPException: On invalid refresh token.
    """
    auth_config = get_auth_config()
    payload = verify_token(request.refresh_token, auth_config, expected_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "Invalid or expired refresh token"},
        )

    # Check if blacklisted
    if is_token_blacklisted(payload.jti):
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "Token has been revoked"},
        )

    # Get user and org
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)
    org_repo = get_organization_repository(db_path)

    user = user_repo.get_by_id(payload.user_id, payload.organization_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"error": "AuthenticationError", "message": "User not found or inactive"},
        )

    org = org_repo.get_by_id(payload.organization_id)
    if not org or not org.is_active:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "AuthenticationError",
                "message": "Organization not found or inactive",
            },
        )

    # Generate new tokens
    access_token = create_access_token(user, auth_config)
    refresh_token = create_refresh_token(user, auth_config)

    # Blacklist old refresh token
    blacklist_token(payload.jti, expires_at=payload.exp, reason="token_refresh")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_config.access_token_expire_minutes * 60,
        organization={
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
        },
        user={
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


# User self-service routes

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile.",
)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Get current user profile.

    Args:
        user: Current authenticated user.

    Returns:
        User profile data.
    """
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
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the currently authenticated user's profile.",
)
async def update_me(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Update current user profile.

    Args:
        request: Profile update request.
        user: Current authenticated user.

    Returns:
        Updated user profile.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    # Apply updates
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.email is not None:
        user.email = request.email

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


@users_router.put(
    "/me/password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the currently authenticated user's password.",
)
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
) -> MessageResponse:
    """Change current user's password.

    Args:
        request: Password change request.
        user: Current authenticated user.

    Returns:
        Success message.
    """
    db_path = get_tenant_db_path()
    user_repo = get_user_repository(db_path)

    # Verify current password
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "Current password is incorrect"},
        )

    # Validate new password
    valid, errors = validate_password_strength(request.new_password)
    if not valid:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": "; ".join(errors)},
        )

    if user.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": "User ID missing"},
        )

    # Update password
    new_hash = hash_password(request.new_password)
    user_repo.update_password(user.id, new_hash)

    return MessageResponse(message="Password changed successfully")
