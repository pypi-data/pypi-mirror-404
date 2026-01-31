"""FastAPI dependencies for authentication and authorization.

Provides injectable dependencies for route handlers to access
the current user, organization context, and permission checks.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger("mysql_to_sheets.api.middleware.dependencies")


async def get_current_user(request: Request) -> Any:
    """FastAPI dependency to get the current authenticated user.

    Returns:
        The authenticated user from request state.

    Raises:
        HTTPException: If no user is authenticated.
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )
    return user


async def get_current_organization_id(request: Request) -> int:
    """FastAPI dependency to get the current organization ID.

    Returns:
        Organization ID from request state.

    Raises:
        HTTPException: If no organization context is set.
    """
    org_id = getattr(request.state, "organization_id", None)
    if org_id is None:
        raise HTTPException(
            status_code=401,
            detail="Organization context required",
        )
    return int(org_id)


def require_permission(permission_name: str) -> Callable[[Request], Awaitable[Any]]:
    """FastAPI dependency factory to require a specific permission.

    Args:
        permission_name: Permission name to check (e.g., "VIEW_CONFIGS").

    Returns:
        Dependency function that returns the authenticated user if authorized.
    """

    async def dependency(request: Request) -> Any:
        user = getattr(request.state, "user", None)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )

        try:
            from mysql_to_sheets.core.rbac import Permission, has_permission

            permission = Permission[permission_name]
            if not has_permission(user, permission):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Forbidden",
                        "required_permission": permission_name,
                        "user_role": user.role,
                    },
                )
        except KeyError:
            logger.error("Unknown permission '%s' - denying access", permission_name)
            raise HTTPException(
                status_code=403,
                detail="Unknown permission",
            )

        return user

    return dependency


__all__ = ["get_current_user", "get_current_organization_id", "require_permission"]
