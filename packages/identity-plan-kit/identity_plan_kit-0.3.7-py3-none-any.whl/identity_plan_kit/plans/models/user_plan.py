"""UserPlan SQLAlchemy model."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.plans.models.plan import PlanModel


class UserPlanModel(Base, UUIDPrimaryKeyMixin):
    """
    User plan database model.

    Links users to their subscription plans.
    """

    __tablename__ = "user_plans"
    __table_args__ = (
        # Composite index for active plan lookups (user_id + date range)
        Index("ix_user_plans_active_lookup", "user_id", "started_at", "ends_at"),
        # Partial index for finding active (non-cancelled) plans
        Index(
            "ix_user_plans_active_not_cancelled",
            "user_id",
            "started_at",
            "ends_at",
            postgresql_where="is_cancelled = false",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    ends_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    custom_limits: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    plan: Mapped["PlanModel"] = relationship(
        "PlanModel",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Check if plan is currently active (not expired and not cancelled)."""
        today = date.today()
        return self.started_at <= today <= self.ends_at and not self.is_cancelled

    def __repr__(self) -> str:
        return f"<UserPlan user={self.user_id} plan={self.plan_id}>"
