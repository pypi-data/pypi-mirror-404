"""Role SQLAlchemy model."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from identity_plan_kit.rbac.models.role_permission import RolePermissionModel


class RoleModel(Base, UUIDPrimaryKeyMixin):
    """
    Role database model.

    Stores user roles (e.g., admin, user).
    """

    __tablename__ = "roles"

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
    # Note: permissions uses lazy="noload" to avoid duplicate queries.
    # RBAC service loads permissions separately with caching.
    # Load explicitly with selectinload() when needed (e.g., rbac_repo, admin views).
    permissions: Mapped[list["RolePermissionModel"]] = relationship(
        "RolePermissionModel",
        back_populates="role",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Role {self.code}>"
