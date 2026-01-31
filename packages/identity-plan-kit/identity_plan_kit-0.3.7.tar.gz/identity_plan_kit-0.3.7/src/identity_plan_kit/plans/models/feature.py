"""Feature SQLAlchemy model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import UUIDPrimaryKeyMixin


class FeatureModel(Base, UUIDPrimaryKeyMixin):
    """
    Feature database model.

    Stores trackable features (e.g., ai_generation, exports).
    """

    __tablename__ = "features"

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

    def __repr__(self) -> str:
        return f"<Feature {self.code}>"
