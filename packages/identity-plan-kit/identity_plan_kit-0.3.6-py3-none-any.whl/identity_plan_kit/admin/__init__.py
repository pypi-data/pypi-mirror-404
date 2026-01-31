"""
SQLAdmin integration for IdentityPlanKit.

Provides pre-configured admin views for all models with role-based permissions.

Admin Roles:
    - Superadmin: Full permissions (create, edit, delete) - configured via env vars
    - Admin: View-only permissions - created by superadmin in the database

Usage:
    from identity_plan_kit.admin import (
        setup_admin,
        AdminAuthBackend,
        AdminRole,
        UserAdmin,
        RoleAdmin,
        # ... etc
    )

    # Option 1: Auto-setup with role-based authentication (recommended)
    auth_backend = AdminAuthBackend(
        secret_key=config.secret_key.get_secret_value(),
        admin_email=config.admin_email,  # IPK_ADMIN_EMAIL
        admin_password=config.admin_password.get_secret_value(),  # IPK_ADMIN_PASSWORD
        session_factory=kit.db_manager.async_session_factory,
    )
    admin = setup_admin(app, engine, authentication_backend=auth_backend)

    # Option 2: Auto-setup without authentication (development only)
    admin = setup_admin(app, engine)

    # Option 3: Manual setup with customization
    admin = Admin(app, engine, authentication_backend=auth_backend)
    admin.add_view(UserAdmin)
    admin.add_view(RoleAdmin)
    # ... add only the views you need

Requires:
    pip install identity-plan-kit[admin]
"""

from identity_plan_kit.admin.auth import AdminAuthBackend, AdminRole
from identity_plan_kit.admin.views import (
    AdminValidationError,
    BaseAdminView,
    FeatureAdmin,
    FeatureUsageAdmin,
    PermissionAdmin,
    PlanAdmin,
    PlanLimitAdmin,
    PlanPermissionAdmin,
    RefreshTokenAdmin,
    RoleAdmin,
    RolePermissionAdmin,
    UserAdmin,
    UserPlanAdmin,
    UserProviderAdmin,
    get_all_admin_views,
    setup_admin,
)

__all__ = [
    # Authentication
    "AdminAuthBackend",
    "AdminRole",
    # Base classes
    "BaseAdminView",
    "AdminValidationError",
    # Auth views
    "UserAdmin",
    "UserProviderAdmin",
    "RefreshTokenAdmin",
    # RBAC views
    "RoleAdmin",
    "PermissionAdmin",
    "RolePermissionAdmin",
    # Plan views
    "PlanAdmin",
    "FeatureAdmin",
    "PlanLimitAdmin",
    "PlanPermissionAdmin",
    "UserPlanAdmin",
    "FeatureUsageAdmin",
    # Setup helpers
    "setup_admin",
    "get_all_admin_views",
]
