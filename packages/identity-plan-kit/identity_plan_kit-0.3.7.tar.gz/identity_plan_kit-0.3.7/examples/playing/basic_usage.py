"""
Basic usage example for IdentityPlanKit.

This example shows how to set up IdentityPlanKit with a FastAPI application.

Required environment variables:
    IPK_DATABASE_URL: PostgreSQL connection string
    IPK_SECRET_KEY: Secret key for JWT signing (min 32 chars)
    IPK_GOOGLE_CLIENT_ID: Google OAuth client ID
    IPK_GOOGLE_CLIENT_SECRET: Google OAuth client secret
    IPK_GOOGLE_REDIRECT_URI: OAuth callback URL

Optional:
    IPK_REDIS_URL: Redis URL for multi-instance deployments
    IPK_ENABLE_METRICS: Enable Prometheus metrics (requires: pip install identity-plan-kit[metrics])

Run:
    IPK_ENV_FILE=examples/playing/.env.local uv run examples/playing/basic_usage.py
"""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig
from identity_plan_kit.admin import setup_admin
from identity_plan_kit.auth import CurrentUser
from identity_plan_kit.plans import requires_feature
from identity_plan_kit.rbac import requires_permission

# Load configuration from environment variables
config = IdentityPlanKitConfig(
    # Token settings
    access_token_expire_minutes=15,
    refresh_token_expire_days=30,
    # Features
    enable_remember_me=True,
    enable_usage_tracking=True,
    # Auto token cleanup (enabled by default)
    enable_auto_cleanup=True,
    cleanup_interval_hours=6.0,
    # Metrics (optional - requires prometheus-client)
    # enable_metrics=True,
    # metrics_path="/metrics",
)

# Setup admin

# Initialize IdentityPlanKit
kit = IdentityPlanKit(config)

# Create FastAPI app with kit's lifespan (handles startup/shutdown)
app = FastAPI(
    title="My App with IdentityPlanKit",
    lifespan=kit.lifespan,
)
engine = create_async_engine(
    config.database_url,
    echo=False,
    pool_size=20,  # Your tuned pool size
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Your existing session factory
session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

setup_admin(app, engine)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup IdentityPlanKit (adds auth routes, health checks, request ID tracking)
kit.setup(app)


# =============================================================================
# ENDPOINTS
# =============================================================================


@app.get("/")
async def root() -> dict[str, str]:
    """Public endpoint - no authentication required."""
    return {"message": "Welcome to the API"}


@app.get("/me")
async def get_me(user: CurrentUser) -> dict[str, Any]:
    """Get current user info - requires authentication."""
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role_code,
    }


@app.get("/admin/dashboard")
async def admin_dashboard(
    user: CurrentUser,
    _: None = requires_permission("admin:access"),
) -> dict[str, str]:
    """Admin dashboard - requires admin:access permission."""
    return {"message": f"Welcome to admin dashboard, {user.email}"}


@app.post("/api/generate")
async def generate_content(
    user: CurrentUser,
    _: None = requires_feature("ai_generation", consume=1),
) -> dict[str, str]:
    """
    Generate content - requires ai_generation feature and consumes 1 quota.

    Returns 429 if quota exceeded.
    """
    return {"message": "Content generated!", "user": user.email}


@app.get("/api/usage")
async def get_usage(user: CurrentUser) -> dict[str, Any]:
    """Get current usage for a feature."""
    try:
        usage = await kit.plan_service.get_usage_info(user.id, "ai_generation")
        return {
            "feature": usage.feature_code,
            "used": usage.used,
            "limit": usage.limit,
            "remaining": usage.remaining,
            "period": usage.period,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
