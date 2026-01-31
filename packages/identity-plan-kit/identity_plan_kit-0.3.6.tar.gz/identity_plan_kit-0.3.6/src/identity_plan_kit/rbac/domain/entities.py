"""RBAC domain entities."""

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID


class PermissionType(str, Enum):
    """Permission type - role or plan based."""

    ROLE = "role"
    PLAN = "plan"


@dataclass
class Permission:
    """
    Permission domain entity.

    Represents a single permission that can be granted via roles or plans.
    """

    id: UUID
    code: str
    type: PermissionType

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.code:
            raise ValueError("Permission code cannot be empty")
        if ":" not in self.code:
            raise ValueError("Permission code should follow 'resource:action' format")


@dataclass
class Role:
    """
    Role domain entity.

    Represents a user role with associated permissions.
    """

    id: UUID
    code: str
    name: str
    permissions: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.code:
            raise ValueError("Role code cannot be empty")

    def has_permission(self, permission_code: str) -> bool:
        """Check if role has a specific permission."""
        return permission_code in self.permissions

    def add_permission(self, permission_code: str) -> None:
        """Add a permission to the role."""
        self.permissions.add(permission_code)

    def remove_permission(self, permission_code: str) -> None:
        """Remove a permission from the role."""
        self.permissions.discard(permission_code)
