"""PlanLimit SQLAlchemy model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.plans.models.feature import FeatureModel
    from identity_plan_kit.plans.models.plan import PlanModel


class PlanLimitModel(Base, UUIDPrimaryKeyMixin):
    """
    Plan limit database model.

    Defines usage limits per feature per plan.
    """

    __tablename__ = "plan_limits"
    __table_args__ = (UniqueConstraint("plan_id", "feature_id", name="uq_plan_feature_limit"),)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_id: Mapped[UUID] = mapped_column(
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_limit: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        # -1 means unlimited
    )
    period: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        # 'daily' or 'monthly', NULL means no reset
    )

    # Relationships
    plan: Mapped["PlanModel"] = relationship(
        "PlanModel",
        back_populates="limits",
    )
    feature: Mapped["FeatureModel"] = relationship(
        "FeatureModel",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<PlanLimit plan={self.plan_id} feature={self.feature_id} limit={self.feature_limit}>"
        )
