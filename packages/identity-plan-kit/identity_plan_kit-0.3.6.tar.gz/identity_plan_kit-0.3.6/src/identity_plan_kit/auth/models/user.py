"""User SQLAlchemy model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.models import BaseModel

if TYPE_CHECKING:
    from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
    from identity_plan_kit.auth.models.user_provider import UserProviderModel
    from identity_plan_kit.rbac.models.role import RoleModel


class UserModel(BaseModel):
    """
    User database model.

    Stores user account information and links to roles.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False,
    )
    # Password hash for optional password authentication (e.g., admin users).
    # Nullable because OAuth-only users don't have passwords.
    # Uses bcrypt via passlib - hash is ~60 chars but we use 255 for safety.
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    # Display name from OAuth provider (e.g., Google 'name' field).
    # User-editable. Defaults to email prefix on registration.
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # Profile picture URL from OAuth provider.
    # Nullable because not all users have profile pictures.
    picture_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    # Note: providers uses lazy="noload" to avoid unnecessary queries on every auth check.
    # Load explicitly with selectinload() when needed (e.g., admin views).
    providers: Mapped[list[UserProviderModel]] = relationship(
        "UserProviderModel",
        back_populates="user",
        lazy="noload",
    )
    refresh_tokens: Mapped[list[RefreshTokenModel]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        lazy="noload",
    )
    role: Mapped[RoleModel] = relationship(
        "RoleModel",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
