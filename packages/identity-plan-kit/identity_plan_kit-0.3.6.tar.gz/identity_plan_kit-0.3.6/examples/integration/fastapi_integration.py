"""
Example: Integrating IdentityPlanKit with a Production-Ready FastAPI Backend.

This example shows how to integrate identity-plan-kit with an existing
FastAPI application that has its own configuration, database, and services.

Key integration points:
1. Configuration mapping from host app settings to IPK config
2. SHARED SESSION FACTORY - Use your existing database pool (no connection duplication!)
3. Transaction participation - IPK operations in your transactions
4. Lifespan composition (running both lifespans)
5. Creating models that reference IPK's User model
6. Token cleanup scheduling (you control it)
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, relationship

# =============================================================================
# Step 1: Import IPK components
# =============================================================================

from identity_plan_kit import (
    # Core
    IdentityPlanKit,
    IdentityPlanKitConfig,
    Environment,
    # Auth
    CurrentUser,
    # Model base classes for extending
    BaseModel,
)
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth import AuthUnitOfWork, UserRepository
from identity_plan_kit.plans import PlansUnitOfWork, PlanRepository
from identity_plan_kit.rbac import requires_permission
from identity_plan_kit.plans import requires_feature


# =============================================================================
# Step 2: Your Existing Database Setup (battle-tested, don't replace!)
# =============================================================================

# This represents YOUR existing database configuration
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/myapp"

# Your existing engine and session factory - IPK will USE THIS!
engine = create_async_engine(
    DATABASE_URL,
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


# =============================================================================
# Step 3: Configuration Mapping
# =============================================================================

# Production-ready backends typically have a structured settings like this:
# from backend.core.conf.settings import SETTINGS


class MockJWTSettings:
    JWT_SECRET = "your-super-secret-jwt-key-at-least-32-characters"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = 15
    JWT_REFRESH_EXPIRE_DAYS = 30


class MockGoogleOAuthSettings:
    GOOGLE_OAUTH_CLIENT_ID = "your-google-client-id"
    GOOGLE_OAUTH_CLIENT_SECRET = "your-google-client-secret"


class MockAppSettings:
    ENVIRONMENT = "local"  # "local", "dev", "prod"


class MockRedisSettings:
    REDIS_URL = "redis://localhost:6379/0"


class MockSettings:
    JWT = MockJWTSettings()
    GOOGLE = MockGoogleOAuthSettings()
    APP = MockAppSettings()
    REDIS = MockRedisSettings()


SETTINGS = MockSettings()


def create_ipk_config() -> IdentityPlanKitConfig:
    """
    Create IPK configuration from your backend's settings.

    Note: We do NOT pass database_url here because we're passing our own
    session_factory to IdentityPlanKit instead!
    """
    env_map = {
        "local": Environment.DEVELOPMENT,
        "dev": Environment.DEVELOPMENT,
        "prod": Environment.PRODUCTION,
    }

    return IdentityPlanKitConfig(
        # Database URL still needed for config validation
        # but IPK won't create its own pool since we pass session_factory
        database_url=DATABASE_URL,

        # Security - map from your JWT settings
        secret_key=SETTINGS.JWT.JWT_SECRET,
        algorithm=SETTINGS.JWT.JWT_ALGORITHM,
        access_token_expire_minutes=SETTINGS.JWT.JWT_EXPIRE_MINUTES,
        refresh_token_expire_days=SETTINGS.JWT.JWT_REFRESH_EXPIRE_DAYS,

        # Google OAuth
        google_client_id=SETTINGS.GOOGLE.GOOGLE_OAUTH_CLIENT_ID,
        google_client_secret=SETTINGS.GOOGLE.GOOGLE_OAUTH_CLIENT_SECRET,
        google_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",

        # Environment
        environment=env_map.get(SETTINGS.APP.ENVIRONMENT, Environment.PRODUCTION),

        # Redis - reuse your backend's Redis
        redis_url=SETTINGS.REDIS.REDIS_URL,
        # Note: require_redis defaults to True in production when redis_url is set

        # API prefix - mount under your API version
        api_prefix="/api/v1",

        # Customize default role/plan for your domain
        default_role_code="user",
        default_plan_code="free",
    )


# =============================================================================
# Step 4: Create Custom Models (extend IPK's User)
# =============================================================================

class ProfileModel(BaseModel):
    """
    User profile that extends IPK's User.

    This demonstrates how to create app-specific models that
    reference IPK's User model via foreign key.
    """
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Profile-specific fields
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationship to IPK's User
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="joined",
    )


class OrganizationModel(BaseModel):
    """Organization/team model for multi-tenant applications."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    owner: Mapped["UserModel"] = relationship(
        "UserModel",
        lazy="joined",
    )


# =============================================================================
# Step 5: Create IPK with YOUR Session Factory (KEY INTEGRATION!)
# =============================================================================

ipk_config = create_ipk_config()

# CRITICAL: Pass your session_factory! IPK will NOT create its own pool.
kit = IdentityPlanKit(
    ipk_config,
    session_factory=session_factory,  # <-- YOUR existing pool!
)


# =============================================================================
# Step 6: Lifespan Composition
# =============================================================================

@asynccontextmanager
async def combined_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Combined lifespan that runs both your backend's and IPK's startup/shutdown.

    Note: Since we passed session_factory, IPK does NOT manage database connections.
    Your app handles that.
    """
    # Startup
    # 1. Start IPK (initializes services, but NOT database - we own that)
    await kit.startup()

    # 2. Your backend's custom startup (if any)
    # await initialize_custom_services()

    try:
        yield
    finally:
        # Shutdown (reverse order)
        # 1. Your backend's custom shutdown
        # await shutdown_custom_services()

        # 2. Shutdown IPK (closes services, but NOT database - we own that)
        await kit.shutdown()

        # 3. YOUR database cleanup (you own it!)
        await engine.dispose()


# =============================================================================
# Step 7: Token Cleanup (YOU schedule it!)
# =============================================================================

# Option A: Using APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    kit.cleanup_expired_tokens,
    'interval',
    hours=6,
    kwargs={'batch_size': 1000},
)
scheduler.start()
"""

# Option B: Simple background task
"""
import asyncio

async def cleanup_loop():
    while True:
        await asyncio.sleep(6 * 3600)  # 6 hours
        try:
            deleted = await kit.cleanup_expired_tokens()
            print(f"Cleaned up {deleted} expired tokens")
        except Exception as e:
            print(f"Cleanup failed: {e}")

# In your lifespan:
cleanup_task = asyncio.create_task(cleanup_loop())
"""

# Option C: Celery Beat
"""
@celery.task
def cleanup_tokens():
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(kit.cleanup_expired_tokens())
"""


# =============================================================================
# Step 8: Application Setup
# =============================================================================

def create_app() -> FastAPI:
    """Create the FastAPI application with IPK integration."""
    app = FastAPI(
        title="Production-Ready API",
        version="1.0.0",
        lifespan=combined_lifespan,
    )

    # Setup IPK (adds auth routes, health checks, etc.)
    kit.setup(
        app,
        register_error_handlers=True,
        include_health_routes=True,
        include_request_id=True,
    )

    return app


# =============================================================================
# Step 9: Using IPK in Endpoints
# =============================================================================

app = create_app()


@app.get("/api/v1/me")
async def get_current_user_profile(
    user: CurrentUser = Depends(CurrentUser(kit)),
):
    """Get current user's profile."""
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role_code,
    }


@app.get("/api/v1/admin/users")
async def list_users(
    user: CurrentUser = Depends(CurrentUser(kit)),
    _: None = Depends(requires_permission("users:read")),
):
    """Admin endpoint - requires 'users:read' permission."""
    return {"users": []}


@app.post("/api/v1/ai/generate")
async def ai_generate(
    user: CurrentUser = Depends(CurrentUser(kit)),
    _: None = Depends(requires_feature("ai_generation", consume=1)),
):
    """
    AI generation endpoint with usage tracking.

    This endpoint:
    - Requires authentication
    - Requires 'ai_generation' feature in user's plan
    - Consumes 1 usage unit per call (tracked against plan limits)
    """
    return {"result": "generated content"}


# =============================================================================
# Step 10: Transaction Participation (IPK + Your Operations)
# =============================================================================

@app.post("/api/v1/orders")
async def create_order_with_plan_check(
    user: CurrentUser = Depends(CurrentUser(kit)),
):
    """
    Example showing IPK operations in YOUR transaction.

    This is the key SaaS integration pattern - single transaction for:
    - Checking user's plan
    - Creating your business entities
    - Consuming quota

    If anything fails, everything rolls back.
    """
    async with session_factory() as session:
        async with session.begin():
            # Use IPK's UoW with YOUR session - shares the transaction!
            async with PlansUnitOfWork(session_factory, session=session) as uow:
                # Check user's plan within YOUR transaction
                user_plan = await uow.plans.get_user_active_plan(user.id)
                if user_plan is None:
                    return {"error": "No active plan"}

                # Your business logic - same transaction!
                # order = Order(user_id=user.id, ...)
                # session.add(order)

                # This all commits together or rolls back together
                pass

    return {"status": "created"}


@app.post("/api/v1/users/{user_id}/upgrade")
async def upgrade_user_plan(
    user_id: UUID,
    new_plan_code: str,
    admin: CurrentUser = Depends(CurrentUser(kit)),
    _: None = Depends(requires_permission("users:write")),
):
    """
    Example: Atomic user update + plan change.

    Both IPK tables and your tables in one transaction.
    """
    async with session_factory() as session:
        async with session.begin():
            # Use both Auth and Plans UoWs with the same session
            async with AuthUnitOfWork(session_factory, session=session) as auth_uow:
                user = await auth_uow.users.get_by_id(user_id)
                if user is None:
                    return {"error": "User not found"}

                # Update user (IPK table)
                # user.some_field = new_value
                # await auth_uow.users.update(user)

            async with PlansUnitOfWork(session_factory, session=session) as plans_uow:
                # Get new plan
                new_plan = await plans_uow.plans.get_plan_by_code(new_plan_code)
                if new_plan is None:
                    return {"error": "Plan not found"}

                # Create new user plan (IPK table)
                await plans_uow.plans.create_user_plan(user_id, new_plan.id)

            # Your custom audit log (YOUR table)
            # audit = AuditLog(admin_id=admin.id, action="upgrade_plan", ...)
            # session.add(audit)

            # All commits together!

    return {"status": "upgraded"}


# =============================================================================
# Step 11: Direct Repository Access (Advanced)
# =============================================================================

async def get_user_by_email_direct(email: str) -> UserModel | None:
    """
    Example: Using repositories directly for simple queries.

    Useful when you just need a quick lookup without the full UoW pattern.
    """
    async with session_factory() as session:
        repo = UserRepository(session)
        return await repo.get_by_email(email)


# =============================================================================
# Step 12: Alembic Migration Setup
# =============================================================================

"""
Integrate IPK with your EXISTING alembic/env.py (don't replace it).

Add these 2 changes to your existing env.py:

```python
# backend/migrations/env.py

# ... your existing imports ...

# ============== ADD THESE LINES ==============

# CHANGE 1: Use IPK's Base instead of your own
from identity_plan_kit import Base

# CHANGE 2: Import IPK models to register them
from identity_plan_kit.migrations import import_all_models
import_all_models()

# Import your models (they should now inherit from identity_plan_kit.BaseModel)
from backend.features.profiles.models import ProfileModel
from backend.features.organizations.models import OrganizationModel

# ============== UPDATE THIS LINE ==============
target_metadata = Base.metadata  # Use IPK's Base metadata

# ... rest of your env.py stays THE SAME ...
```

Then generate migration as usual:
```bash
alembic revision --autogenerate -m "Add IPK and profile models"
alembic upgrade head
```
"""


# =============================================================================
# Step 13: Seeding Initial Data
# =============================================================================

async def seed_initial_data():
    """
    Seed initial roles, permissions, plans, and features.

    Run this once during deployment or via a CLI command.
    """
    from identity_plan_kit.rbac.models.role import RoleModel
    from identity_plan_kit.rbac.models.permission import PermissionModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.plans.models.feature import FeatureModel

    async with session_factory() as session:
        async with session.begin():
            # Create roles
            roles = [
                RoleModel(code="user", name="User", description="Regular user"),
                RoleModel(code="moderator", name="Moderator", description="Content moderator"),
                RoleModel(code="admin", name="Admin", description="Platform administrator"),
            ]

            # Create permissions
            permissions = [
                PermissionModel(code="users:read", name="Read Users"),
                PermissionModel(code="users:write", name="Write Users"),
                PermissionModel(code="content:moderate", name="Moderate Content"),
            ]

            # Create plans
            plans = [
                PlanModel(code="free", name="Free", description="Basic free plan"),
                PlanModel(code="pro", name="Pro", description="Professional plan", price_cents=999),
                PlanModel(code="enterprise", name="Enterprise", description="Enterprise plan", price_cents=4999),
            ]

            # Create features
            features = [
                FeatureModel(code="ai_generation", name="AI Generation"),
                FeatureModel(code="api_access", name="API Access"),
                FeatureModel(code="priority_support", name="Priority Support"),
            ]

            session.add_all(roles + permissions + plans + features)
            # Commits with the transaction context


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
