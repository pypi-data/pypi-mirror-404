"""
Admin panel usage example for IdentityPlanKit.

This example shows how to set up the SQLAdmin panel with role-based permissions:
- Superadmin: Full permissions (create, edit, delete) - from env vars
- Admin: View-only permissions - users with 'admin' role in database

Required environment variables:
    IPK_DATABASE_URL: PostgreSQL connection string
    IPK_SECRET_KEY: Secret key for JWT signing (min 32 chars)
    IPK_GOOGLE_CLIENT_ID: Google OAuth client ID
    IPK_GOOGLE_CLIENT_SECRET: Google OAuth client secret
    IPK_GOOGLE_REDIRECT_URI: OAuth callback URL

Admin authentication (required for secure admin panel):
    IPK_ADMIN_EMAIL: Superadmin email (full permissions)
    IPK_ADMIN_PASSWORD: Superadmin password (min 8 chars)

Run:
    IPK_ENV_FILE=examples/playing/.env.local uv run examples/playing/admin_usage.py

Then visit:
    http://localhost:8000/admin

Login options:
    1. Superadmin (from env vars): Full access - can create, edit, delete
    2. Admin (from database): View-only access - users with 'admin' role
"""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig
from identity_plan_kit.admin import AdminAuthBackend, AdminRole, setup_admin

# Load configuration from environment variables
config = IdentityPlanKitConfig(
    access_token_expire_minutes=15,
    refresh_token_expire_days=30,
    enable_remember_me=True,
    enable_usage_tracking=True,
)

# Initialize IdentityPlanKit
kit = IdentityPlanKit(config)

# Create FastAPI app
app = FastAPI(
    title="Admin Panel Example",
    lifespan=kit.lifespan,
)

# Create engine and session factory
engine = create_async_engine(
    config.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# =============================================================================
# ADMIN PANEL SETUP WITH ROLE-BASED AUTHENTICATION
# =============================================================================

# Check if admin credentials are configured
if config.admin_email and config.admin_password:
    # Create authentication backend with role-based permissions
    auth_backend = AdminAuthBackend(
        secret_key=config.secret_key.get_secret_value(),
        # Superadmin credentials from env vars (full permissions)
        admin_email=config.admin_email,
        admin_password=config.admin_password.get_secret_value(),
        # Session factory for authenticating DB admins (view-only)
        session_factory=session_factory,
    )

    # Setup admin with authentication
    admin = setup_admin(
        app,
        engine,
        title="IdentityPlanKit Admin",
        base_url="/admin",
        authentication_backend=auth_backend,
    )

    print("Admin panel configured with authentication:")
    print(f"  - Superadmin email: {config.admin_email}")
    print("  - Superadmin role: FULL PERMISSIONS (create, edit, delete)")
    print("  - Admin role: VIEW ONLY (users with 'admin' role in database)")
else:
    # Setup admin without authentication (development only)
    admin = setup_admin(
        app,
        engine,
        title="IdentityPlanKit Admin (NO AUTH)",
        base_url="/admin",
    )

    print("WARNING: Admin panel running without authentication!")
    print("Set IPK_ADMIN_EMAIL and IPK_ADMIN_PASSWORD for secure access.")

# Setup IdentityPlanKit routes
kit.setup(app)


# =============================================================================
# EXAMPLE: Check admin role in custom endpoints
# =============================================================================


@app.get("/")
async def root() -> dict[str, str]:
    """Public endpoint."""
    return {
        "message": "Welcome! Visit /admin for the admin panel.",
        "admin_url": "/admin",
    }


@app.get("/admin-roles")
async def admin_roles_info() -> dict[str, str]:
    """Information about admin roles."""
    return {
        "superadmin": {
            "description": "Full permissions - can create, edit, delete",
            "auth": "Configured via IPK_ADMIN_EMAIL and IPK_ADMIN_PASSWORD",
            "role_value": AdminRole.SUPERADMIN.value,
        },
        "admin": {
            "description": "View-only permissions - can only view records",
            "auth": "Users with 'admin' role in database",
            "role_value": AdminRole.ADMIN.value,
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("ADMIN PANEL EXAMPLE")
    print("=" * 60)
    print("\nVisit: http://localhost:8000/admin")
    print("\nRoles:")
    print("  SUPERADMIN: Full access (env vars) -> create, edit, delete")
    print("  ADMIN: View-only (DB users with 'admin' role)")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
