"""Permission SQLAlchemy model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin


class PermissionModel(Base, UUIDPrimaryKeyMixin):
    """
    Permission database model.

    Stores individual permissions that can be assigned to roles or plans.
    Permission codes follow 'resource:action' format (e.g., 'users:read', 'movies:delete').
    """

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        # CHECK constraint: type IN ('role', 'plan')
        # Added via migration or raw SQL
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"
