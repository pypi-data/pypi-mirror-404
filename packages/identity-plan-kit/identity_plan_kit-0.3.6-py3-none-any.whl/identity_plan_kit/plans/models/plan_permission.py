"""PlanPermission junction model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.rbac.models.permission import PermissionModel


class PlanPermissionModel(Base, UUIDPrimaryKeyMixin):
    """
    Plan-Permission junction table.

    Links plans to their permissions.
    """

    __tablename__ = "plan_permissions"
    __table_args__ = (UniqueConstraint("plan_id", "permission_id", name="uq_plan_permission"),)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    plan: Mapped["PlanModel"] = relationship(
        "PlanModel",
        back_populates="permissions",
    )
    permission: Mapped["PermissionModel"] = relationship(
        "PermissionModel",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PlanPermission plan={self.plan_id} permission={self.permission_id}>"
