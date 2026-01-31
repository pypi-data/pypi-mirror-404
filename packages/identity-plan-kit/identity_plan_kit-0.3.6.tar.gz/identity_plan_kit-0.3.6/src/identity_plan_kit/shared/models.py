"""Base SQLAlchemy models with common fields."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.uuid7 import uuid7


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """
    Mixin that adds UUID7 primary key.

    Usage:
        class MyModel(Base, UUIDPrimaryKeyMixin):
            __tablename__ = "my_table"
            ...
    """

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Base model with UUID7 primary key and timestamps.

    Provides:
    - id: UUID7 primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated

    Usage:
        class User(BaseModel):
            __tablename__ = "users"
            email: Mapped[str] = mapped_column(String(255))
    """

    __abstract__ = True


class IntPrimaryKeyMixin:
    """
    Mixin that adds BigInt auto-increment primary key.

    Usage:
        class MyModel(Base, IntPrimaryKeyMixin):
            __tablename__ = "my_table"
            ...
    """

    @declared_attr
    def id(cls) -> Mapped[int]:
        # Import here to avoid potential circular imports at class definition time
        from sqlalchemy import BigInteger  # noqa: PLC0415

        return mapped_column(BigInteger, primary_key=True, autoincrement=True)


class BaseIntModel(Base, IntPrimaryKeyMixin, TimestampMixin):
    """
    Base model with integer primary key and timestamps.

    For tables that need auto-increment integer IDs instead of UUIDs.

    Provides:
    - id: BigInt auto-increment primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    """

    __abstract__ = True
