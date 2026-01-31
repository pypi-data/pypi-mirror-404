"""RolePermission junction model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.rbac.models.permission import PermissionModel
    from identity_plan_kit.rbac.models.role import RoleModel


class RolePermissionModel(Base, UUIDPrimaryKeyMixin):
    """
    Role-Permission junction table.

    Links roles to their permissions.
    """

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    role: Mapped["RoleModel"] = relationship(
        "RoleModel",
        back_populates="permissions",
    )
    permission: Mapped["PermissionModel"] = relationship(
        "PermissionModel",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<RolePermission role={self.role_id} permission={self.permission_id}>"
