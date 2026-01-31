"""RBAC FastAPI dependencies."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from identity_plan_kit.auth.dependencies import CurrentUser
from identity_plan_kit.rbac.domain.exceptions import PermissionDeniedError
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)


def requires_permission(permission_code: str) -> Callable[..., Any]:
    """
    Dependency that requires a specific permission.

    Usage:
        @app.get("/admin/users")
        @requires_permission("users:read")
        async def list_users(user: CurrentUser):
            ...

    Args:
        permission_code: Required permission code

    Returns:
        FastAPI dependency
    """

    async def dependency(
        request: Request,
        user: CurrentUser,
    ) -> None:
        kit = request.app.state.identity_plan_kit
        rbac_service = kit.rbac_service

        try:
            await rbac_service.require_permission(
                user_id=user.id,
                role_id=user.role_id,
                permission_code=permission_code,
            )
        except PermissionDeniedError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_code}",
            ) from None

    return Depends(dependency)


def requires_role(role_code: str) -> Callable[..., Any]:
    """
    Dependency that requires a specific role.

    Usage:
        @app.get("/admin/dashboard")
        @requires_role("admin")
        async def admin_dashboard(user: CurrentUser):
            ...

    Args:
        role_code: Required role code

    Returns:
        FastAPI dependency
    """

    async def dependency(
        request: Request,
        user: CurrentUser,
    ) -> None:
        kit = request.app.state.identity_plan_kit
        rbac_service = kit.rbac_service

        try:
            await rbac_service.require_role(
                user_role_code=user.role_code or "",
                required_role_code=role_code,
            )
        except PermissionDeniedError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {role_code}",
            ) from None

    return Depends(dependency)


def requires_any_permission(*permission_codes: str) -> Callable[..., Any]:
    """
    Dependency that requires any of the specified permissions.

    Usage:
        @app.get("/content")
        @requires_any_permission("content:read", "content:admin")
        async def get_content(user: CurrentUser):
            ...

    Args:
        permission_codes: List of acceptable permission codes

    Returns:
        FastAPI dependency
    """

    async def dependency(
        request: Request,
        user: CurrentUser,
    ) -> None:
        kit = request.app.state.identity_plan_kit
        rbac_service = kit.rbac_service

        for code in permission_codes:
            if await rbac_service.check_permission(
                user_id=user.id,
                role_id=user.role_id,
                permission_code=code,
            ):
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required one of: {', '.join(permission_codes)}",
        )

    return Depends(dependency)
