"""
SQLAdmin ModelViews for IdentityPlanKit.

Provides pre-configured admin views for all models:
- Auth: Users, UserProviders, RefreshTokens
- RBAC: Roles, Permissions, RolePermissions
- Plans: Plans, Features, PlanLimits, PlanPermissions, UserPlans, FeatureUsage
"""

from __future__ import annotations

import os
import re
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqladmin import Admin, ModelView

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from wtforms import validators

from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.models.user_provider import UserProviderModel
from identity_plan_kit.plans.models.feature import FeatureModel
from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel
from identity_plan_kit.plans.models.plan import PlanModel
from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
from identity_plan_kit.plans.models.plan_permission import PlanPermissionModel
from identity_plan_kit.plans.models.user_plan import UserPlanModel
from identity_plan_kit.rbac.models.permission import PermissionModel
from identity_plan_kit.rbac.models.role import RoleModel
from identity_plan_kit.rbac.models.role_permission import RolePermissionModel

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncEngine
    from wtforms import Form


# =============================================================================
# ERROR HANDLING UTILITIES
# =============================================================================


def _parse_integrity_error(exc: IntegrityError) -> str:
    """
    Parse IntegrityError to provide user-friendly error messages.

    Handles common constraint violations:
    - NOT NULL violations
    - UNIQUE constraint violations
    - FOREIGN KEY violations
    - CHECK constraint violations
    """
    error_msg = str(exc.orig) if exc.orig else str(exc)

    # NOT NULL violation
    if "NotNullViolationError" in error_msg or "null value in column" in error_msg:
        match = re.search(r'column "(\w+)"', error_msg)
        column = match.group(1) if match else "unknown field"
        return f"The field '{column}' is required and cannot be empty."

    # UNIQUE constraint violation
    if "UniqueViolationError" in error_msg or "duplicate key" in error_msg:
        match = re.search(r'constraint "(\w+)"', error_msg)
        constraint = match.group(1) if match else None
        if constraint:
            # Try to extract meaningful field names from constraint name
            if "uq_" in constraint:
                fields = constraint.replace("uq_", "").replace("_", ", ")
                return f"A record with this combination of ({fields}) already exists."
            elif "email" in constraint.lower():
                return "This email address is already in use."
            elif "code" in constraint.lower():
                return "This code is already in use."
        return "A record with these values already exists. Please use unique values."

    # FOREIGN KEY violation
    if "ForeignKeyViolationError" in error_msg or "foreign key constraint" in error_msg:
        if "is still referenced" in error_msg:
            match = re.search(r'table "(\w+)"', error_msg)
            table = match.group(1) if match else "other records"
            return f"Cannot delete: this record is still referenced by {table}."
        match = re.search(r'table "(\w+)"', error_msg)
        table = match.group(1) if match else "unknown table"
        return f"Invalid reference: the selected {table.rstrip('s')} does not exist."

    # CHECK constraint violation
    if "CheckViolationError" in error_msg or "check constraint" in error_msg:
        match = re.search(r'constraint "(\w+)"', error_msg)
        constraint = match.group(1) if match else None
        if constraint:
            if "period" in constraint:
                return "Invalid period value. Must be 'daily', 'monthly', or 'lifetime'."
            if "type" in constraint:
                return "Invalid type value. Must be 'role' or 'plan'."
        return "Invalid value: does not meet validation requirements."

    # Generic fallback
    return f"Database constraint violation: {error_msg[:200]}"


class AdminValidationError(Exception):
    """Custom validation error for admin operations."""


class BaseAdminView(ModelView):
    """
    Base admin view with common error handling and permission checking.

    Features:
    - Catches IntegrityErrors during create/update/delete operations
      and converts them to user-friendly error messages.
    - Enforces role-based permissions:
      - Superadmin: Full access (create, edit, delete)
      - Admin: View-only access

    The permission checking uses the AdminAuthBackend from the request's
    app state when available.

    Note: UI button visibility is controlled via custom templates that check
    request.session['admin_role']. This is thread-safe because SQLAdmin
    ModelView instances are singletons shared across requests.
    """

    def _get_auth_backend(self, request: Request) -> Any | None:
        """Get the authentication backend from request."""
        # SQLAdmin mounts as a sub-application, so request.app is the Admin's app,
        # not the FastAPI app. We need to get the auth backend from the Admin instance.
        # The Admin stores authentication_backend as an attribute.
        if hasattr(request, "app"):
            # Try to get from Admin's authentication_backend (preferred)
            admin_auth = getattr(request.app, "authentication_backend", None)
            if admin_auth:
                return admin_auth
            # Fallback: try app.state (for backwards compatibility)
            if hasattr(request.app, "state"):
                admin_auth = getattr(request.app.state, "_admin_auth_backend", None)
                if admin_auth:
                    return admin_auth
        return None

    def _is_superadmin(self, request: Request) -> bool:
        """Check if current user is superadmin."""
        auth_backend = self._get_auth_backend(request)
        if auth_backend and hasattr(auth_backend, "is_superadmin"):
            result = auth_backend.is_superadmin(request)
            logger.debug(
                "_is_superadmin_check",
                auth_backend_found=True,
                is_superadmin=result,
                admin_role=request.session.get("admin_role"),
            )
            return result
        # If no auth backend, allow all (backwards compatibility)
        logger.warning(
            "_is_superadmin_no_auth_backend",
            message="No auth backend found, allowing access (backwards compatibility)",
        )
        return True

    def is_accessible(self, request: Request) -> bool:
        """
        Check if user can access this view based on role and action.

        - Superadmin: Full access (list, details, create, edit, delete)
        - Admin: View-only access (list, details only)
        """
        # Get the current path to determine the action
        path = request.url.path

        # Check if this is a modifying action (edit, create, delete)
        is_modifying_action = any(
            action in path for action in ["/edit/", "/create", "/delete"]
        )

        logger.debug(
            "is_accessible_check",
            path=path,
            is_modifying_action=is_modifying_action,
            is_superadmin=self._is_superadmin(request),
        )

        if is_modifying_action:
            # Only superadmin can access modifying actions
            result = self._is_superadmin(request)
            logger.info(
                "is_accessible_modifying_action",
                path=path,
                allowed=result,
            )
            return result

        # Allow all authenticated admins to view list and details
        return True

    async def on_model_change(
        self, data: dict[str, Any], model: Any, is_created: bool, request: Request
    ) -> None:
        """Called before model is saved. Override for custom validation."""

    async def insert_model(self, request: Request, data: dict[str, Any]) -> Any:
        """Insert a new model instance with error handling and permission check."""
        if not self._is_superadmin(request):
            raise AdminValidationError("Permission denied: Only superadmin can create records.")
        try:
            return await super().insert_model(request, data)
        except IntegrityError as exc:
            raise AdminValidationError(_parse_integrity_error(exc)) from exc

    async def update_model(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        """Update an existing model instance with error handling and permission check."""
        if not self._is_superadmin(request):
            raise AdminValidationError("Permission denied: Only superadmin can edit records.")
        try:
            return await super().update_model(request, pk, data)
        except IntegrityError as exc:
            raise AdminValidationError(_parse_integrity_error(exc)) from exc

    async def delete_model(self, request: Request, pk: Any) -> None:
        """Delete a model instance with error handling and permission check."""
        if not self._is_superadmin(request):
            raise AdminValidationError("Permission denied: Only superadmin can delete records.")
        try:
            return await super().delete_model(request, pk)
        except IntegrityError as exc:
            raise AdminValidationError(_parse_integrity_error(exc)) from exc


# =============================================================================
# AUTH ADMIN VIEWS
# =============================================================================


class UserAdmin(BaseAdminView, model=UserModel):
    """Admin view for User management."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    category = "Authentication"

    # List view configuration
    column_list = [
        UserModel.id,
        UserModel.email,
        UserModel.role,
        UserModel.is_active,
        UserModel.is_verified,
        UserModel.created_at,
    ]
    column_searchable_list = [UserModel.email]
    column_sortable_list = [
        UserModel.email,
        UserModel.is_active,
        UserModel.is_verified,
        UserModel.created_at,
    ]
    column_default_sort = [(UserModel.created_at, True)]

    # Detail view configuration
    column_details_list = [
        UserModel.id,
        UserModel.email,
        UserModel.role,
        UserModel.is_active,
        UserModel.is_verified,
        UserModel.created_at,
        UserModel.updated_at,
        UserModel.providers,
    ]

    # Form configuration - use relationship for dropdown selection
    form_columns = [
        UserModel.email,
        UserModel.role,  # Use relationship for proper dropdown
        UserModel.is_active,
        UserModel.is_verified,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "role": {
            "fields": ("code", "name"),
            "order_by": "name",
        }
    }

    # Form validation
    form_args = {
        "email": {"validators": [validators.DataRequired(), validators.Email()]},
        "role": {"validators": [validators.DataRequired()]},
    }

    # Export configuration
    column_export_list = [
        UserModel.id,
        UserModel.email,
        UserModel.role_id,
        UserModel.is_active,
        UserModel.is_verified,
        UserModel.created_at,
    ]
    can_export = True

    # Formatting
    column_formatters = {
        UserModel.is_active: lambda m, a: "Active" if m.is_active else "Inactive",
        UserModel.is_verified: lambda m, a: "Verified" if m.is_verified else "Unverified",
    }


class UserProviderAdmin(BaseAdminView, model=UserProviderModel):
    """Admin view for OAuth Provider links."""

    name = "OAuth Provider"
    name_plural = "OAuth Providers"
    icon = "fa-solid fa-link"
    category = "Authentication"

    column_list = [
        UserProviderModel.id,
        UserProviderModel.user,
        UserProviderModel.code,
        UserProviderModel.external_user_id,
    ]
    column_searchable_list = [UserProviderModel.external_user_id]
    column_sortable_list = [UserProviderModel.code]

    column_details_list = [
        UserProviderModel.id,
        UserProviderModel.user,
        UserProviderModel.code,
        UserProviderModel.external_user_id,
    ]

    # Form configuration - use relationship for proper dropdown
    form_columns = [
        UserProviderModel.user,  # Use relationship for proper dropdown
        UserProviderModel.code,
        UserProviderModel.external_user_id,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "user": {
            "fields": ("email",),
            "order_by": "email",
        }
    }

    # Form validation
    form_args = {
        "user": {"validators": [validators.DataRequired()]},
        "code": {"validators": [validators.DataRequired()]},
        "external_user_id": {"validators": [validators.DataRequired()]},
    }

    # Provider code choices
    form_choices = {
        "code": [
            ("google", "Google"),
            ("github", "GitHub"),
            ("microsoft", "Microsoft"),
            ("apple", "Apple"),
        ]
    }


class RefreshTokenAdmin(BaseAdminView, model=RefreshTokenModel):
    """Admin view for Refresh Token management."""

    name = "Refresh Token"
    name_plural = "Refresh Tokens"
    icon = "fa-solid fa-key"
    category = "Authentication"

    column_list = [
        RefreshTokenModel.id,
        RefreshTokenModel.user,
        RefreshTokenModel.expires_at,
        RefreshTokenModel.revoked_at,
        RefreshTokenModel.created_at,
        RefreshTokenModel.ip_address,
    ]
    column_sortable_list = [
        RefreshTokenModel.expires_at,
        RefreshTokenModel.created_at,
    ]
    column_default_sort = [(RefreshTokenModel.created_at, True)]

    column_details_list = [
        RefreshTokenModel.id,
        RefreshTokenModel.user,
        RefreshTokenModel.token_hash,
        RefreshTokenModel.expires_at,
        RefreshTokenModel.created_at,
        RefreshTokenModel.revoked_at,
        RefreshTokenModel.user_agent,
        RefreshTokenModel.ip_address,
    ]

    # Form configuration
    form_columns = [
        RefreshTokenModel.user,
        RefreshTokenModel.token_hash,
        RefreshTokenModel.expires_at,
        RefreshTokenModel.revoked_at,
        RefreshTokenModel.user_agent,
        RefreshTokenModel.ip_address,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "user": {
            "fields": ("email",),
            "order_by": "email",
        }
    }

    # Form validation
    form_args = {
        "user": {"validators": [validators.DataRequired()]},
        "token_hash": {"validators": [validators.DataRequired()]},
        "expires_at": {"validators": [validators.DataRequired()]},
    }


# =============================================================================
# RBAC ADMIN VIEWS
# =============================================================================


class RoleAdmin(BaseAdminView, model=RoleModel):
    """Admin view for Role management."""

    name = "Role"
    name_plural = "Roles"
    icon = "fa-solid fa-user-shield"
    category = "RBAC"

    column_list = [
        RoleModel.id,
        RoleModel.code,
        RoleModel.name,
    ]
    column_searchable_list = [RoleModel.code, RoleModel.name]
    column_sortable_list = [RoleModel.code, RoleModel.name]

    column_details_list = [
        RoleModel.id,
        RoleModel.code,
        RoleModel.name,
        RoleModel.permissions,
    ]

    form_columns = [
        RoleModel.code,
        RoleModel.name,
    ]

    # Form validation
    form_args = {
        "code": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
        "name": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
    }


class PermissionAdmin(BaseAdminView, model=PermissionModel):
    """Admin view for Permission management."""

    name = "Permission"
    name_plural = "Permissions"
    icon = "fa-solid fa-lock"
    category = "RBAC"

    column_list = [
        PermissionModel.id,
        PermissionModel.code,
        PermissionModel.type,
    ]
    column_searchable_list = [PermissionModel.code]
    column_sortable_list = [PermissionModel.code, PermissionModel.type]

    column_details_list = [
        PermissionModel.id,
        PermissionModel.code,
        PermissionModel.type,
    ]

    form_columns = [
        PermissionModel.code,
        PermissionModel.type,
    ]

    form_choices = {
        "type": [
            ("role", "Role Permission"),
            ("plan", "Plan Permission"),
        ]
    }

    # Form validation
    form_args = {
        "code": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
        "type": {"validators": [validators.DataRequired()]},
    }


class RolePermissionAdmin(BaseAdminView, model=RolePermissionModel):
    """Admin view for Role-Permission assignments."""

    name = "Role Permission"
    name_plural = "Role Permissions"
    icon = "fa-solid fa-user-lock"
    category = "RBAC"

    column_list = [
        RolePermissionModel.id,
        RolePermissionModel.role,
        RolePermissionModel.permission,
    ]
    column_sortable_list = [RolePermissionModel.role_id, RolePermissionModel.permission_id]

    column_details_list = [
        RolePermissionModel.id,
        RolePermissionModel.role,
        RolePermissionModel.permission,
    ]

    # Form configuration - use relationships for proper dropdowns
    form_columns = [
        RolePermissionModel.role,
        RolePermissionModel.permission,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "role": {
            "fields": ("code", "name"),
            "order_by": "name",
        },
        "permission": {
            "fields": ("code",),
            "order_by": "code",
        },
    }

    # Form validation
    form_args = {
        "role": {"validators": [validators.DataRequired()]},
        "permission": {"validators": [validators.DataRequired()]},
    }


# =============================================================================
# PLAN ADMIN VIEWS
# =============================================================================


class PlanAdmin(BaseAdminView, model=PlanModel):
    """Admin view for Subscription Plan management."""

    name = "Plan"
    name_plural = "Plans"
    icon = "fa-solid fa-credit-card"
    category = "Plans"

    column_list = [
        PlanModel.id,
        PlanModel.code,
        PlanModel.name,
    ]
    column_searchable_list = [PlanModel.code, PlanModel.name]
    column_sortable_list = [PlanModel.code, PlanModel.name]

    column_details_list = [
        PlanModel.id,
        PlanModel.code,
        PlanModel.name,
        PlanModel.permissions,
        PlanModel.limits,
    ]

    form_columns = [
        PlanModel.code,
        PlanModel.name,
    ]

    # Form validation
    form_args = {
        "code": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
        "name": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
    }


class FeatureAdmin(BaseAdminView, model=FeatureModel):
    """Admin view for Feature management."""

    name = "Feature"
    name_plural = "Features"
    icon = "fa-solid fa-puzzle-piece"
    category = "Plans"

    column_list = [
        FeatureModel.id,
        FeatureModel.code,
        FeatureModel.name,
    ]
    column_searchable_list = [FeatureModel.code, FeatureModel.name]
    column_sortable_list = [FeatureModel.code, FeatureModel.name]

    column_details_list = [
        FeatureModel.id,
        FeatureModel.code,
        FeatureModel.name,
    ]

    form_columns = [
        FeatureModel.code,
        FeatureModel.name,
    ]

    # Form validation
    form_args = {
        "code": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
        "name": {"validators": [validators.DataRequired(), validators.Length(max=255)]},
    }


class PlanLimitAdmin(BaseAdminView, model=PlanLimitModel):
    """Admin view for Plan Limit management."""

    name = "Plan Limit"
    name_plural = "Plan Limits"
    icon = "fa-solid fa-gauge-high"
    category = "Plans"

    column_list = [
        PlanLimitModel.id,
        PlanLimitModel.plan,
        PlanLimitModel.feature,
        PlanLimitModel.feature_limit,
        PlanLimitModel.period,
    ]
    column_sortable_list = [
        PlanLimitModel.plan_id,
        PlanLimitModel.feature_id,
        PlanLimitModel.feature_limit,
    ]

    column_details_list = [
        PlanLimitModel.id,
        PlanLimitModel.plan,
        PlanLimitModel.feature,
        PlanLimitModel.feature_limit,
        PlanLimitModel.period,
    ]

    # Form configuration - use relationships for proper dropdowns
    form_columns = [
        PlanLimitModel.plan,
        PlanLimitModel.feature,
        PlanLimitModel.feature_limit,
        PlanLimitModel.period,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "plan": {
            "fields": ("code", "name"),
            "order_by": "name",
        },
        "feature": {
            "fields": ("code", "name"),
            "order_by": "name",
        },
    }

    form_choices = {
        "period": [
            ("daily", "Daily"),
            ("monthly", "Monthly"),
            ("lifetime", "Lifetime"),
        ]
    }

    # Form validation
    form_args = {
        "plan": {"validators": [validators.DataRequired()]},
        "feature": {"validators": [validators.DataRequired()]},
        "feature_limit": {"validators": [validators.DataRequired()]},
    }

    column_formatters = {
        PlanLimitModel.feature_limit: lambda m, a: "Unlimited" if m.feature_limit == -1 else str(m.feature_limit),
    }


class PlanPermissionAdmin(BaseAdminView, model=PlanPermissionModel):
    """Admin view for Plan-Permission assignments."""

    name = "Plan Permission"
    name_plural = "Plan Permissions"
    icon = "fa-solid fa-handshake"
    category = "Plans"

    column_list = [
        PlanPermissionModel.id,
        PlanPermissionModel.plan,
        PlanPermissionModel.permission,
    ]
    column_sortable_list = [PlanPermissionModel.plan_id, PlanPermissionModel.permission_id]

    column_details_list = [
        PlanPermissionModel.id,
        PlanPermissionModel.plan,
        PlanPermissionModel.permission,
    ]

    # Form configuration - use relationships for proper dropdowns
    form_columns = [
        PlanPermissionModel.plan,
        PlanPermissionModel.permission,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "plan": {
            "fields": ("code", "name"),
            "order_by": "name",
        },
        "permission": {
            "fields": ("code",),
            "order_by": "code",
        },
    }

    # Form validation
    form_args = {
        "plan": {"validators": [validators.DataRequired()]},
        "permission": {"validators": [validators.DataRequired()]},
    }


class UserPlanAdmin(BaseAdminView, model=UserPlanModel):
    """Admin view for User Plan subscriptions."""

    name = "User Plan"
    name_plural = "User Plans"
    icon = "fa-solid fa-user-tag"
    category = "Plans"

    column_list = [
        UserPlanModel.id,
        UserPlanModel.user_id,
        UserPlanModel.plan,
        UserPlanModel.started_at,
        UserPlanModel.ends_at,
    ]
    column_sortable_list = [
        UserPlanModel.started_at,
        UserPlanModel.ends_at,
    ]
    column_default_sort = [(UserPlanModel.started_at, True)]

    column_details_list = [
        UserPlanModel.id,
        UserPlanModel.user_id,
        UserPlanModel.plan,
        UserPlanModel.started_at,
        UserPlanModel.ends_at,
        UserPlanModel.custom_limits,
    ]

    # Form configuration - use relationship for plan dropdown
    # Note: user_id stays as UUID input since users are looked up by ID
    form_columns = [
        UserPlanModel.user_id,
        UserPlanModel.plan,
        UserPlanModel.started_at,
        UserPlanModel.ends_at,
        UserPlanModel.custom_limits,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "plan": {
            "fields": ("code", "name"),
            "order_by": "name",
        },
    }

    # Form validation
    form_args = {
        "user_id": {"validators": [validators.DataRequired()]},
        "plan": {"validators": [validators.DataRequired()]},
        "started_at": {"validators": [validators.DataRequired()]},
        "ends_at": {"validators": [validators.DataRequired()]},
    }


class FeatureUsageAdmin(BaseAdminView, model=FeatureUsageModel):
    """Admin view for Feature Usage tracking."""

    name = "Feature Usage"
    name_plural = "Feature Usage"
    icon = "fa-solid fa-chart-line"
    category = "Plans"

    column_list = [
        FeatureUsageModel.id,
        FeatureUsageModel.user_plan_id,
        FeatureUsageModel.feature,
        FeatureUsageModel.feature_usage,
        FeatureUsageModel.start_period,
        FeatureUsageModel.end_period,
    ]
    column_sortable_list = [
        FeatureUsageModel.feature_usage,
        FeatureUsageModel.start_period,
        FeatureUsageModel.end_period,
    ]
    column_default_sort = [(FeatureUsageModel.start_period, True)]

    column_details_list = [
        FeatureUsageModel.id,
        FeatureUsageModel.user_plan_id,
        FeatureUsageModel.feature,
        FeatureUsageModel.feature_usage,
        FeatureUsageModel.start_period,
        FeatureUsageModel.end_period,
    ]

    # Form configuration
    form_columns = [
        FeatureUsageModel.user_plan_id,
        FeatureUsageModel.feature,
        FeatureUsageModel.feature_usage,
        FeatureUsageModel.start_period,
        FeatureUsageModel.end_period,
    ]

    # AJAX refs for searchable dropdowns
    form_ajax_refs = {
        "feature": {
            "fields": ("code", "name"),
            "order_by": "name",
        },
    }

    # Form validation
    form_args = {
        "user_plan_id": {"validators": [validators.DataRequired()]},
        "feature": {"validators": [validators.DataRequired()]},
        "feature_usage": {"validators": [validators.DataRequired()]},
        "start_period": {"validators": [validators.DataRequired()]},
        "end_period": {"validators": [validators.DataRequired()]},
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_all_admin_views() -> list[type[ModelView]]:
    """
    Get all admin views in the recommended order.

    Returns a list of ModelView classes organized by category.
    """
    return [
        # Auth
        UserAdmin,
        UserProviderAdmin,
        RefreshTokenAdmin,
        # RBAC
        RoleAdmin,
        PermissionAdmin,
        RolePermissionAdmin,
        # Plans
        PlanAdmin,
        FeatureAdmin,
        PlanLimitAdmin,
        PlanPermissionAdmin,
        UserPlanAdmin,
        FeatureUsageAdmin,
    ]


def setup_admin(
    app: FastAPI,
    engine: AsyncEngine,
    *,
    title: str = "IdentityPlanKit Admin",
    base_url: str = "/admin",
    authentication_backend: Any | None = None,
    templates_dir: str | None = None,
) -> Admin:
    """
    Set up SQLAdmin with all IdentityPlanKit models.

    Args:
        app: FastAPI application instance
        engine: SQLAlchemy async engine
        title: Admin panel title
        base_url: Base URL for admin panel
        authentication_backend: Optional authentication backend for admin access.
            Use AdminAuthBackend for role-based permissions (superadmin/admin).
        templates_dir: Optional custom templates directory

    Returns:
        Configured Admin instance

    Example:
        from identity_plan_kit.admin import setup_admin, AdminAuthBackend

        # With role-based authentication (recommended):
        auth_backend = AdminAuthBackend(
            secret_key=config.secret_key.get_secret_value(),
            admin_email=config.admin_email,
            admin_password=config.admin_password.get_secret_value(),
            session_factory=kit.db_manager.async_session_factory,
        )
        admin = setup_admin(
            app,
            kit.db_manager.engine,
            authentication_backend=auth_backend,
        )

        # Without authentication (development only):
        admin = setup_admin(app, kit.db_manager.engine)
    """
    # SECURITY: Warn if no authentication backend is provided
    if authentication_backend is None:
        environment = os.getenv("IPK_ENVIRONMENT", "production")
        warning_msg = (
            "Admin panel is being set up WITHOUT authentication. "
            "This exposes sensitive user data, tokens, and configuration. "
            "Always provide an authentication_backend in production."
        )
        if environment == "production":
            logger.critical(
                "admin_no_authentication",
                message=warning_msg,
                base_url=base_url,
            )
            warnings.warn(
                f"SECURITY WARNING: {warning_msg}",
                UserWarning,
                stacklevel=2,
            )
        else:
            logger.warning(
                "admin_no_authentication",
                message=warning_msg,
                base_url=base_url,
            )

    # Store auth backend in app state for permission checking in views
    # Note: We'll also store it on the Admin's internal Starlette app after creation
    if authentication_backend is not None:
        app.state._admin_auth_backend = authentication_backend

    # Use bundled templates for role-based permission UI if no custom templates_dir provided.
    # These templates check is_superadmin_user(request) to hide edit/delete buttons for non-superadmin.
    if templates_dir is None:
        templates_dir = str(Path(__file__).parent / "templates")

    # Build kwargs
    admin_kwargs: dict[str, Any] = {
        "app": app,
        "engine": engine,
        "title": title,
        "base_url": base_url,
        "templates_dir": templates_dir,
    }
    if authentication_backend is not None:
        admin_kwargs["authentication_backend"] = authentication_backend

    admin = Admin(**admin_kwargs)

    # Store auth backend on the Admin's internal Starlette app for permission checking.
    # SQLAdmin creates an internal Starlette app (admin.admin) that handles /admin/* requests.
    # When views call request.app, they get this internal app, not the FastAPI app.
    if authentication_backend is not None:
        admin.admin.state._admin_auth_backend = authentication_backend

    # Add Jinja2 global function for role-based permission checking in templates.
    # This is thread-safe because it checks request.session on each call,
    # unlike modifying ModelView instance attributes which are shared.
    def is_superadmin_user(request: Request) -> bool:
        """Check if current user is superadmin (for use in templates)."""
        if authentication_backend and hasattr(authentication_backend, "is_superadmin"):
            return authentication_backend.is_superadmin(request)
        # If no auth backend, allow all (backwards compatibility)
        return True

    admin.templates.env.globals["is_superadmin_user"] = is_superadmin_user

    for view in get_all_admin_views():
        admin.add_view(view)

    return admin
