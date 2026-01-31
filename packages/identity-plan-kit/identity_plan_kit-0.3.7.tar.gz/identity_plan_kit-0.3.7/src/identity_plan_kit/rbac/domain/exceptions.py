"""RBAC domain exceptions with error codes."""

from identity_plan_kit.shared.exceptions import AuthorizationError, NotFoundError


class RBACError(AuthorizationError):
    """Base exception for RBAC errors."""

    code = "RBAC_ERROR"
    message = "RBAC error"


class PermissionDeniedError(RBACError):
    """Permission denied for the requested action."""

    code = "PERMISSION_DENIED"
    message = "Permission denied"

    def __init__(
        self,
        permission: str | None = None,
        message: str | None = None,
    ) -> None:
        self._permission = permission
        msg = message or (f"Permission denied: {permission}" if permission else "Permission denied")
        super().__init__(message=msg, details={"permission": permission} if permission else None)

    @property
    def permission(self) -> str | None:
        """Get the permission code."""
        return self._permission

    @property
    def permission_code(self) -> str | None:
        """Alias for permission to support permission_code naming convention."""
        return self._permission


class RoleNotFoundError(NotFoundError):
    """Role not found."""

    code = "ROLE_NOT_FOUND"
    message = "Role not found"

    def __init__(self, role_code: str | None = None) -> None:
        self.role_code = role_code
        msg = f"Role not found: {role_code}" if role_code else "Role not found"
        super().__init__(message=msg, details={"role_code": role_code} if role_code else None)


class PermissionNotFoundError(NotFoundError):
    """Permission not found."""

    code = "PERMISSION_NOT_FOUND"
    message = "Permission not found"

    def __init__(self, permission_code: str | None = None) -> None:
        self.permission_code = permission_code
        msg = (
            f"Permission not found: {permission_code}"
            if permission_code
            else "Permission not found"
        )
        super().__init__(
            message=msg, details={"permission_code": permission_code} if permission_code else None
        )
