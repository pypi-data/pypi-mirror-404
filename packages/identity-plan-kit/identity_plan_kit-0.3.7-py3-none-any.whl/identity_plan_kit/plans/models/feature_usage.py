"""FeatureUsage SQLAlchemy model."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.plans.models.feature import FeatureModel


class FeatureUsageModel(Base, UUIDPrimaryKeyMixin):
    """
    Feature usage database model.

    Tracks feature usage per user plan per period.
    """

    __tablename__ = "feature_usage"
    __table_args__ = (
        UniqueConstraint(
            "user_plan_id", "feature_id", "start_period", name="uq_usage_plan_feature_period"
        ),
        # Composite index for period-based queries
        Index(
            "ix_feature_usage_period_lookup",
            "user_plan_id",
            "feature_id",
            "start_period",
            "end_period",
        ),
    )

    user_plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_id: Mapped[UUID] = mapped_column(
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_usage: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )
    start_period: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_period: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Relationships
    feature: Mapped[FeatureModel] = relationship(
        "FeatureModel",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<FeatureUsage plan={self.user_plan_id} feature={self.feature_id} usage={self.feature_usage}>"
