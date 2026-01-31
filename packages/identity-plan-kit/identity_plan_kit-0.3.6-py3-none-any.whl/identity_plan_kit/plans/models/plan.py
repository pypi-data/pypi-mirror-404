"""Plan SQLAlchemy model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
    from identity_plan_kit.plans.models.plan_permission import PlanPermissionModel


class PlanModel(Base, UUIDPrimaryKeyMixin):
    """
    Plan database model.

    Stores subscription plans (e.g., free, pro).
    """

    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Relationships
    permissions: Mapped[list["PlanPermissionModel"]] = relationship(
        "PlanPermissionModel",
        back_populates="plan",
        lazy="selectin",
    )
    limits: Mapped[list["PlanLimitModel"]] = relationship(
        "PlanLimitModel",
        back_populates="plan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Plan {self.code}>"
