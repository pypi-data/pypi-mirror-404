"""RBAC module - Role-Based Access Control."""

from identity_plan_kit.rbac.dependencies import requires_permission, requires_role
from identity_plan_kit.rbac.domain.entities import Permission, Role
from identity_plan_kit.rbac.domain.exceptions import PermissionDeniedError, RoleNotFoundError
from identity_plan_kit.rbac.repositories.rbac_repo import RBACRepository
from identity_plan_kit.rbac.uow import RBACUnitOfWork

__all__ = [
    # Entities
    "Permission",
    # Exceptions
    "PermissionDeniedError",
    # Repository (for direct use with external sessions)
    "RBACRepository",
    # Unit of Work
    "RBACUnitOfWork",
    "Role",
    "RoleNotFoundError",
    # Dependencies
    "requires_permission",
    "requires_role",
]
