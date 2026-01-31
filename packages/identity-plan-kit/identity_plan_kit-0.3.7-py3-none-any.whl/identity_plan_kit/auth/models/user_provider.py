"""UserProvider SQLAlchemy model."""

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin


class UserProviderModel(Base, UUIDPrimaryKeyMixin):
    """
    OAuth provider link model.

    Links users to external OAuth providers (e.g., Google).
    """

    __tablename__ = "user_providers"
    __table_args__ = (
        # Unique composite index for provider + external user id
        Index("ix_user_providers_unique", "code", "external_user_id", unique=True),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        # CHECK constraint: code IN ('google', ...)
        # Added via migration or raw SQL
    )
    external_user_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="providers",
    )

    def __repr__(self) -> str:
        return f"<UserProvider {self.code}:{self.external_user_id}>"


# Import for type hints
from identity_plan_kit.auth.models.user import UserModel  # noqa: E402
