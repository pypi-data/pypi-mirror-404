"""
SQLAdmin Authentication Backend with role-based permissions.

Provides authentication for the SQLAdmin panel with two roles:
- Superadmin: Full permissions (create, edit, delete) - configured via env vars
- Admin: View-only permissions - created by superadmin in the database

Usage:
    from identity_plan_kit.admin import AdminAuthBackend, setup_admin

    # Create authentication backend
    auth_backend = AdminAuthBackend(
        secret_key=config.secret_key.get_secret_value(),
        admin_email=config.admin_email,
        admin_password=config.admin_password.get_secret_value(),
        session_factory=kit.db_manager.async_session_factory,
    )

    # Setup admin with authentication
    admin = setup_admin(
        app,
        kit.db_manager.engine,
        authentication_backend=auth_backend,
    )
"""

from __future__ import annotations

import secrets
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

logger = get_logger(__name__)


class AdminRole(str, Enum):
    """Admin panel roles with different permission levels."""

    SUPERADMIN = "superadmin"  # Full permissions (env var admin)
    ADMIN = "admin"  # View-only permissions (DB admins created by superadmin)


class AdminAuthBackend(AuthenticationBackend):
    """
    Authentication backend for SQLAdmin with role-based permissions.

    Supports two types of admin users:
    1. Superadmin (from environment variables):
       - Has full permissions: can create, edit, delete all records
       - Credentials set via IPK_ADMIN_EMAIL and IPK_ADMIN_PASSWORD

    2. Admin (from database):
       - Has view-only permissions: can only view records
       - Created by superadmin via the admin panel
       - Must have 'admin' role in the database

    Session data stored:
        - admin_authenticated: bool
        - admin_email: str
        - admin_role: AdminRole value
    """

    def __init__(
        self,
        secret_key: str,
        admin_email: str | None = None,
        admin_password: str | None = None,
        session_factory: async_sessionmaker | None = None,
    ) -> None:
        """
        Initialize the admin authentication backend.

        Args:
            secret_key: Secret key for session signing
            admin_email: Superadmin email (from env vars)
            admin_password: Superadmin password (from env vars)
            session_factory: SQLAlchemy async session factory for DB admin lookup
        """
        super().__init__(secret_key)
        self._admin_email = admin_email
        self._admin_password = admin_password
        self._session_factory = session_factory

    async def login(self, request: Request) -> bool:
        """
        Handle login form submission.

        Authenticates against:
        1. Superadmin credentials (from env vars) - gets full permissions
        2. Database users with 'admin' role - gets view-only permissions

        Returns:
            True if login successful, False otherwise
        """
        form = await request.form()
        email = form.get("username", "")
        password = form.get("password", "")

        if not email or not password:
            return False

        # Check superadmin credentials first (from env vars)
        if await self._authenticate_superadmin(str(email), str(password)):
            request.session["admin_authenticated"] = True
            request.session["admin_email"] = str(email)
            request.session["admin_role"] = AdminRole.SUPERADMIN.value
            logger.info(
                "admin_login_success",
                email=email,
                role=AdminRole.SUPERADMIN.value,
            )
            return True

        # Check database admin users
        if await self._authenticate_db_admin(str(email), str(password)):
            request.session["admin_authenticated"] = True
            request.session["admin_email"] = str(email)
            request.session["admin_role"] = AdminRole.ADMIN.value
            logger.info(
                "admin_login_success",
                email=email,
                role=AdminRole.ADMIN.value,
            )
            return True

        logger.warning(
            "admin_login_failed",
            email=email,
        )
        return False

    async def logout(self, request: Request) -> bool:
        """Handle logout - clear session data."""
        email = request.session.get("admin_email", "unknown")
        request.session.clear()
        logger.info("admin_logout", email=email)
        return True

    async def authenticate(self, request: Request) -> RedirectResponse | bool:
        """
        Check if user is authenticated.

        Returns:
            True if authenticated, RedirectResponse to login page otherwise
        """
        if request.session.get("admin_authenticated"):
            return True
        return RedirectResponse(request.url_for("admin:login"), status_code=302)

    async def _authenticate_superadmin(self, email: str, password: str) -> bool:
        """
        Authenticate against superadmin credentials from environment.

        Uses constant-time comparison to prevent timing attacks.
        """
        if not self._admin_email or not self._admin_password:
            return False

        # Use constant-time comparison for security
        # Encode to bytes to handle non-ASCII characters
        email_match = secrets.compare_digest(
            email.lower().encode("utf-8"), self._admin_email.lower().encode("utf-8")
        )
        password_match = secrets.compare_digest(
            password.encode("utf-8"), self._admin_password.encode("utf-8")
        )

        return email_match and password_match

    async def _authenticate_db_admin(self, email: str, password: str) -> bool:
        """
        Authenticate against database admin users.

        Looks up users with 'admin' role and verifies password hash.

        Note: This requires users to have a password_hash field and
        the 'admin' role assigned. For OAuth-only setups, superadmin
        is the only way to access the admin panel.
        """
        if not self._session_factory:
            return False

        try:
            # Import here to avoid circular imports
            from sqlalchemy import select

            from identity_plan_kit.auth.models.user import UserModel
            from identity_plan_kit.rbac.models.role import RoleModel

            async with self._session_factory() as session:
                # Query user with admin role
                stmt = (
                    select(UserModel)
                    .join(RoleModel, UserModel.role_id == RoleModel.id)
                    .where(
                        UserModel.email == email.lower(),
                        RoleModel.code == "admin",
                        UserModel.is_active == True,  # noqa: E712
                    )
                )
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    return False

                # Check if user has password_hash (for password-based auth)
                if not user.password_hash:
                    logger.debug(
                        "admin_auth_no_password",
                        email=email,
                        message="User has no password hash, cannot authenticate via password",
                    )
                    return False

                # Verify password using shared security utilities (bcrypt via passlib)
                from identity_plan_kit.shared.security import verify_password

                return verify_password(password, user.password_hash)

        except Exception as e:
            logger.error(
                "admin_auth_error",
                error=str(e),
                email=email,
            )
            return False

    def get_admin_role(self, request: Request) -> AdminRole | None:
        """
        Get the admin role from the current session.

        Returns:
            AdminRole if authenticated, None otherwise
        """
        if not request.session.get("admin_authenticated"):
            return None

        role_value = request.session.get("admin_role")
        if role_value:
            try:
                return AdminRole(role_value)
            except ValueError:
                return None
        return None

    def is_superadmin(self, request: Request) -> bool:
        """Check if current user is superadmin."""
        return self.get_admin_role(request) == AdminRole.SUPERADMIN

    def is_admin(self, request: Request) -> bool:
        """Check if current user is admin (view-only)."""
        return self.get_admin_role(request) == AdminRole.ADMIN

    def can_create(self, request: Request) -> bool:
        """Check if current user can create records."""
        return self.is_superadmin(request)

    def can_edit(self, request: Request) -> bool:
        """Check if current user can edit records."""
        return self.is_superadmin(request)

    def can_delete(self, request: Request) -> bool:
        """Check if current user can delete records."""
        return self.is_superadmin(request)
