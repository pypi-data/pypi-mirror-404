"""
Production-ready setup example for IdentityPlanKit.

This example demonstrates a complete production configuration with:
- All security features enabled
- Prometheus metrics and observability
- Health checks for Kubernetes/container orchestration
- Proper error handling and logging
- Redis for distributed state (multi-instance support)
- Rate limiting on authentication endpoints
- Graceful shutdown handling

Required environment variables:
    IPK_DATABASE_URL: PostgreSQL async connection string
    IPK_SECRET_KEY: Secret key for JWT signing (min 32 chars, use cryptographically random)
    IPK_GOOGLE_CLIENT_ID: Google OAuth client ID
    IPK_GOOGLE_CLIENT_SECRET: Google OAuth client secret
    IPK_GOOGLE_REDIRECT_URI: OAuth callback URL (must be HTTPS in production)
    IPK_REDIS_URL: Redis URL for distributed state (required in production)

Run with Docker Compose:
    docker-compose -f examples/docker-compose.prod.yml up

Run locally (development mode):
    IPK_ENV_FILE=examples/.env.production.example uv run examples/production_setup.py
"""

import logging
import sys
from typing import Any
from uuid import UUID

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig
from identity_plan_kit.auth import CurrentUser, OptionalUser
from identity_plan_kit.auth.domain.exceptions import (
    AuthError,
    TokenExpiredError,
    UserNotFoundError,
)
from identity_plan_kit.plans import requires_feature, requires_plan
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    QuotaExceededError,
)
from identity_plan_kit.rbac import requires_permission, requires_role
from identity_plan_kit.rbac.domain.exceptions import PermissionDeniedError

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================


def configure_logging(json_format: bool = True) -> None:
    """
    Configure structured logging for production.

    Args:
        json_format: Use JSON format for logs (recommended for production).
                    Set to False for human-readable format in development.
    """
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

# Load configuration from environment
config = IdentityPlanKitConfig(
    # Environment (set via IPK_ENVIRONMENT)
    # Will automatically adjust cookie security, etc.

    # API prefix - mount all routes under /api/v1
    # Results in: /api/v1/auth, /api/v1/health, /api/v1/metrics
    api_prefix="/api/v1",

    # Token settings - shorter access tokens for better security
    access_token_expire_minutes=15,
    refresh_token_expire_days=30,

    # Features - all enabled for production
    enable_remember_me=True,
    enable_usage_tracking=True,

    # Caching - permission cache for performance
    permission_cache_ttl_seconds=60,

    # Auto token cleanup
    enable_auto_cleanup=True,
    cleanup_interval_hours=6.0,

    # Graceful shutdown - wait for in-flight requests
    shutdown_grace_period_seconds=10.0,

    # Proxy settings - enable if behind nginx/load balancer
    # trust_proxy_headers=True,

    # Metrics - requires: pip install identity-plan-kit[metrics]
    enable_metrics=True,
    metrics_path="/metrics",

    # Redis - required for multi-instance deployments
    # require_redis=True,  # Enable in production to fail fast if Redis unavailable
)

# Configure logging based on environment
configure_logging(json_format=config.is_production)

logger = structlog.get_logger(__name__)

# Initialize IdentityPlanKit
kit = IdentityPlanKit(config)


# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Create FastAPI app with kit's lifespan
app = FastAPI(
    title="Production API with IdentityPlanKit",
    description="A production-ready API with authentication, authorization, and usage tracking",
    version="1.0.0",
    lifespan=kit.lifespan,
    # Disable docs in production if needed
    # docs_url=None if config.is_production else "/docs",
    # redoc_url=None if config.is_production else "/redoc",
)


# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# Trusted hosts - prevent host header attacks
if config.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "api.yourdomain.com",
            "*.yourdomain.com",
        ],
    )

# CORS - configure for your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.yourdomain.com",
        "https://yourdomain.com",
    ] if config.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning(
        "auth_error",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )

    status_code = status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, TokenExpiredError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, UserNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND

    return JSONResponse(
        status_code=status_code,
        content={"error": "authentication_error", "message": str(exc)},
    )


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(
    request: Request, exc: PermissionDeniedError
) -> JSONResponse:
    """Handle authorization errors."""
    logger.warning(
        "permission_denied",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": "forbidden", "message": str(exc)},
    )


@app.exception_handler(QuotaExceededError)
async def quota_exceeded_handler(
    request: Request, exc: QuotaExceededError
) -> JSONResponse:
    """Handle quota exceeded errors."""
    logger.info(
        "quota_exceeded",
        error=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "quota_exceeded",
            "message": str(exc),
            "retry_after": "Check /api/usage for reset time",
        },
        headers={"Retry-After": "3600"},  # Suggest retry after 1 hour
    )


@app.exception_handler(FeatureNotAvailableError)
async def feature_not_available_handler(
    request: Request, exc: FeatureNotAvailableError
) -> JSONResponse:
    """Handle feature not available errors (upgrade required)."""
    logger.info(
        "feature_not_available",
        error=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "feature_not_available",
            "message": str(exc),
            "upgrade_url": "/pricing",
        },
    )


# Setup IdentityPlanKit (adds auth routes, health checks)
kit.setup(app)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class UserResponse(BaseModel):
    """User information response."""
    id: str
    email: str
    role: str
    is_verified: bool


class UsageResponse(BaseModel):
    """Feature usage information response."""
    feature: str
    used: int
    limit: int | None
    remaining: int | None
    period: str
    resets_at: str | None = None


class GenerateRequest(BaseModel):
    """Content generation request."""
    prompt: str
    max_tokens: int = 1000


class GenerateResponse(BaseModel):
    """Content generation response."""
    content: str
    tokens_used: int
    user_email: str


class TeamMemberRequest(BaseModel):
    """Team member management request."""
    email: str
    role: str = "member"


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@app.get("/", tags=["Public"])
async def root() -> dict[str, str]:
    """
    Public endpoint - no authentication required.

    Returns basic API information.
    """
    return {
        "name": "Production API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/status", tags=["Public"])
async def status_check(user: OptionalUser = None) -> dict[str, Any]:
    """
    Status endpoint with optional user context.

    Returns different information based on authentication status.
    """
    base_status = {
        "status": "operational",
        "authenticated": user is not None,
    }

    if user:
        base_status["user_email"] = user.email

    return base_status


# =============================================================================
# AUTHENTICATED ENDPOINTS
# =============================================================================

@app.get("/me", response_model=UserResponse, tags=["User"])
async def get_current_user(user: CurrentUser) -> UserResponse:
    """
    Get current user information.

    Requires valid authentication.
    """
    logger.info("user_profile_accessed", user_id=str(user.id))

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role_code,
        is_verified=user.is_verified,
    )


@app.get("/api/usage", response_model=UsageResponse, tags=["User"])
async def get_usage_info(
    user: CurrentUser,
    feature: str = "ai_generation",
) -> UsageResponse:
    """
    Get current usage information for a feature.

    Returns usage stats including used, limit, and remaining quota.
    """
    try:
        usage = await kit.plan_service.get_usage_info(user.id, feature)

        return UsageResponse(
            feature=usage.feature_code,
            used=usage.used,
            limit=usage.limit,
            remaining=usage.remaining,
            period=usage.period,
        )
    except Exception as e:
        logger.exception("usage_info_error", error=str(e), user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage information",
        ) from e


@app.get("/api/plan", tags=["User"])
async def get_current_plan(user: CurrentUser) -> dict[str, Any]:
    """
    Get current user's subscription plan.

    Returns plan details including features and limits.
    """
    try:
        plan = await kit.plan_service.get_user_plan(user.id)

        if not plan:
            return {
                "plan": None,
                "message": "No active plan",
            }

        return {
            "plan": {
                "code": plan.plan_code,
                "name": plan.plan_code.title(),
                "started_at": plan.started_at.isoformat() if plan.started_at else None,
                "expires_at": plan.expires_at.isoformat() if plan.expires_at else None,
                "is_active": plan.is_active,
            },
        }
    except Exception as e:
        logger.exception("plan_info_error", error=str(e), user_id=str(user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan information",
        ) from e


# =============================================================================
# FEATURE-GATED ENDPOINTS
# =============================================================================

@app.post("/api/generate", response_model=GenerateResponse, tags=["AI Features"])
async def generate_content(
    request: GenerateRequest,
    user: CurrentUser,
    _: None = requires_feature("ai_generation", consume=1),
) -> GenerateResponse:
    """
    Generate AI content.

    Requires:
    - Authentication
    - Access to 'ai_generation' feature
    - Available quota (consumes 1 credit per request)

    Returns 403 if feature not available in plan.
    Returns 429 if quota exceeded.
    """
    logger.info(
        "content_generated",
        user_id=str(user.id),
        prompt_length=len(request.prompt),
        max_tokens=request.max_tokens,
    )

    # Simulate content generation
    content = f"Generated content for: {request.prompt[:50]}..."

    return GenerateResponse(
        content=content,
        tokens_used=min(len(content) // 4, request.max_tokens),
        user_email=user.email,
    )


@app.post("/api/analyze", tags=["AI Features"])
async def analyze_data(
    user: CurrentUser,
    _: None = requires_feature("data_analysis", consume=1),
) -> dict[str, Any]:
    """
    Analyze data with AI.

    Requires the 'data_analysis' feature (typically Pro plan or higher).
    """
    logger.info("data_analyzed", user_id=str(user.id))

    return {
        "analysis": "Sample analysis results",
        "confidence": 0.95,
        "user": user.email,
    }


@app.get("/api/export", tags=["Pro Features"])
async def export_data(
    user: CurrentUser,
    format: str = "csv",
    _: None = requires_plan("pro"),
) -> dict[str, Any]:
    """
    Export data in various formats.

    Requires Pro plan or higher.
    """
    logger.info("data_exported", user_id=str(user.id), format=format)

    return {
        "download_url": f"/api/downloads/{user.id}/export.{format}",
        "expires_in": 3600,
        "format": format,
    }


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@app.get("/admin/dashboard", tags=["Admin"])
async def admin_dashboard(
    user: CurrentUser,
    _: None = requires_permission("admin:access"),
) -> dict[str, Any]:
    """
    Admin dashboard - requires admin:access permission.

    Returns system statistics and overview.
    """
    logger.info("admin_dashboard_accessed", admin_id=str(user.id))

    return {
        "message": f"Welcome to admin dashboard, {user.email}",
        "stats": {
            "total_users": 1000,
            "active_today": 150,
            "revenue_mtd": 50000,
        },
    }


@app.get("/admin/users", tags=["Admin"])
async def list_users(
    user: CurrentUser,
    page: int = 1,
    limit: int = 20,
    _: None = requires_permission("users:read"),
) -> dict[str, Any]:
    """
    List all users - requires users:read permission.

    Paginated list of users in the system.
    """
    logger.info(
        "users_listed",
        admin_id=str(user.id),
        page=page,
        limit=limit,
    )

    return {
        "users": [],  # Would return actual user data
        "pagination": {
            "page": page,
            "limit": limit,
            "total": 0,
        },
    }


@app.delete("/admin/users/{user_id}", tags=["Admin"])
async def delete_user(
    user_id: UUID,
    user: CurrentUser,
    _: None = requires_permission("users:delete"),
) -> dict[str, str]:
    """
    Delete a user - requires users:delete permission.

    Permanently removes a user from the system.
    """
    logger.warning(
        "user_deleted",
        admin_id=str(user.id),
        deleted_user_id=str(user_id),
    )

    return {"message": f"User {user_id} deleted"}


@app.get("/admin/audit-log", tags=["Admin"])
async def get_audit_log(
    user: CurrentUser,
    _: None = requires_role("admin"),
) -> dict[str, Any]:
    """
    Get audit log - requires admin role.

    Returns recent system audit events.
    """
    logger.info("audit_log_accessed", admin_id=str(user.id))

    return {
        "events": [
            {"timestamp": "2024-01-01T00:00:00Z", "action": "user.login", "user": "example@example.com"},
        ],
        "total": 1,
    }


# =============================================================================
# TEAM MANAGEMENT ENDPOINTS (Example of complex permission checks)
# =============================================================================

@app.post("/teams/{team_id}/members", tags=["Teams"])
async def add_team_member(
    team_id: UUID,
    member: TeamMemberRequest,
    user: CurrentUser,
    _: None = requires_permission("teams:manage"),
) -> dict[str, Any]:
    """
    Add a member to a team.

    Requires teams:manage permission.
    """
    logger.info(
        "team_member_added",
        team_id=str(team_id),
        added_by=str(user.id),
        member_email=member.email,
    )

    return {
        "message": f"Added {member.email} to team",
        "team_id": str(team_id),
        "role": member.role,
    }


# =============================================================================
# CUSTOM HEALTH CHECK REGISTRATION
# =============================================================================

async def check_external_api() -> tuple[bool, str]:
    """Custom health check for external API dependency."""
    # Implement actual external API health check
    return True, "External API reachable"


# Register custom health check
kit.health_checker.register_check("external_api", check_external_api)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Production server configuration
    uvicorn.run(
        "production_setup:app",
        host="0.0.0.0",
        port=8000,
        # Production settings
        workers=4 if config.is_production else 1,
        log_level="info",
        access_log=True,
        # SSL termination typically handled by reverse proxy
        # ssl_keyfile="path/to/key.pem",
        # ssl_certfile="path/to/cert.pem",
        # Reload only in development
        reload=not config.is_production,
    )
