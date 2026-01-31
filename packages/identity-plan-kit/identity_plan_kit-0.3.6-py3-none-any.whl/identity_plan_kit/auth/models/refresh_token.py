"""RefreshToken SQLAlchemy model."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin


class RefreshTokenModel(Base, UUIDPrimaryKeyMixin):
    """
    Refresh token model for persistent sessions.

    Stores hashed tokens for "Remember Me" functionality.
    Tokens are rotated on each refresh for security.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        # Partial index for active token lookups (revoked_at IS NULL)
        Index(
            "ix_refresh_tokens_hash_active",
            "token_hash",
            postgresql_where="revoked_at IS NULL",
        ),
        # Index for token cleanup queries (finding expired tokens)
        Index("ix_refresh_tokens_expires_at", "expires_at"),
        # Composite index for cleanup queries filtering by expiry and revocation
        Index("ix_refresh_tokens_cleanup", "expires_at", "revoked_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="refresh_tokens",
    )

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.is_expired and not self.is_revoked

    def __repr__(self) -> str:
        return f"<RefreshToken {self.id} user={self.user_id}>"


# Import for type hints
from identity_plan_kit.auth.models.user import UserModel  # noqa: E402
