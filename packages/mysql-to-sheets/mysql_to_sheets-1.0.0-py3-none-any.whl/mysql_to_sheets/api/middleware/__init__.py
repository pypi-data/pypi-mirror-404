"""API middleware components.

This package contains modular middleware for FastAPI:
- auth: API key authentication
- rate_limit: Request rate limiting
- cors: Cross-origin resource sharing
- tracking: Usage analytics and logging
- rbac: Role-based access control
- organization: Multi-tenant organization context
- user_auth: JWT/session-based user authentication
- tier: Subscription tier enforcement
- https: HTTPS enforcement and HSTS
"""

from mysql_to_sheets.api.middleware.audit import AuditContextMiddleware
from mysql_to_sheets.api.middleware.auth import AuthMiddleware
from mysql_to_sheets.api.middleware.cors import CORSMiddleware
from mysql_to_sheets.api.middleware.dependencies import (
    get_current_organization_id,
    get_current_user,
    require_permission,
)
from mysql_to_sheets.api.middleware.https import HTTPSRedirectMiddleware
from mysql_to_sheets.api.middleware.organization import OrganizationContextMiddleware
from mysql_to_sheets.api.middleware.rate_limit import RateLimitMiddleware
from mysql_to_sheets.api.middleware.rbac import RBACMiddleware
from mysql_to_sheets.api.middleware.request_size import RequestSizeLimitMiddleware
from mysql_to_sheets.api.middleware.scope import ScopeMiddleware
from mysql_to_sheets.api.middleware.tier import (
    TierMiddleware,
    TierRateLimitMiddleware,
    require_feature,
)
from mysql_to_sheets.api.middleware.tracking import UsageTrackerMiddleware
from mysql_to_sheets.api.middleware.user_auth import UserAuthMiddleware

__all__ = [
    "AuthMiddleware",
    "RateLimitMiddleware",
    "CORSMiddleware",
    "UsageTrackerMiddleware",
    "RBACMiddleware",
    "OrganizationContextMiddleware",
    "UserAuthMiddleware",
    "TierMiddleware",
    "TierRateLimitMiddleware",
    "require_feature",
    "AuditContextMiddleware",
    "RequestSizeLimitMiddleware",
    "HTTPSRedirectMiddleware",
    "ScopeMiddleware",
    "get_current_user",
    "get_current_organization_id",
    "require_permission",
]
