"""Migration helpers for integrating IdentityPlanKit with host applications.

This module provides utilities for integrating IPK's database models with
your existing Alembic setup. You DON'T need to replace your env.py - just
add a few lines to include IPK models.

## Quick Start: Modify Your Existing env.py

Add these 2 changes to your existing alembic/env.py:

```python
# CHANGE 1: Add these imports (after your existing imports)
from identity_plan_kit import Base  # Use IPK's Base
from identity_plan_kit.migrations import import_all_models
import_all_models()  # Registers all IPK tables

# CHANGE 2: Update target_metadata to use IPK's Base
target_metadata = Base.metadata

# The rest of your env.py stays the same!
```

## Update Your Models

Your models should inherit from IPK's BaseModel:

```python
# BEFORE
from your_app.database import Base

class Profile(Base):
    __tablename__ = "profiles"

# AFTER
from identity_plan_kit import BaseModel
from identity_plan_kit.auth.models.user import UserModel

class Profile(BaseModel):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship("UserModel")
```

## Alternative: Keep Your Own Base (Advanced)

If you can't switch to IPK's Base, combine metadata manually:

```python
from your_app.database import Base as YourBase
from identity_plan_kit.migrations import get_ipk_metadata
from sqlalchemy import MetaData

target_metadata = MetaData()

# Copy IPK tables first
for table in get_ipk_metadata().tables.values():
    table.to_metadata(target_metadata)

# Then copy your tables
for table in YourBase.metadata.tables.values():
    if table.name not in target_metadata.tables:
        table.to_metadata(target_metadata)
```

## Generate Migration

After updating env.py, generate migration as usual:

```bash
alembic revision --autogenerate -m "Add IPK models"
alembic upgrade head
```
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import MetaData


def get_package_dir() -> Path:
    """Get the identity_plan_kit package directory."""
    return Path(__file__).parent


def get_alembic_migrations_dir() -> Path:
    """
    Get the path to IPK's Alembic migrations directory.

    Useful if you want to run IPK migrations standalone or
    include them in a multi-location Alembic setup.

    Returns:
        Path to the alembic/versions directory
    """
    return get_package_dir().parent.parent / "alembic" / "versions"


def get_alembic_ini_path() -> Path:
    """
    Get the path to IPK's alembic.ini file.

    Returns:
        Path to alembic.ini
    """
    return get_package_dir().parent.parent / "alembic.ini"


def import_all_models() -> list[type]:
    """
    Import all IPK SQLAlchemy models.

    This ensures all models are registered with the Base metadata,
    which is necessary for Alembic autogenerate to detect them.

    Returns:
        List of all model classes

    Example:
        ```python
        # In your alembic/env.py
        from identity_plan_kit.migrations import import_all_models

        # This registers all IPK models with the metadata
        models = import_all_models()
        ```
    """
    # Import all model modules to register them with Base.metadata
    from identity_plan_kit.auth.models.user import UserModel
    from identity_plan_kit.auth.models.user_provider import UserProviderModel
    from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
    from identity_plan_kit.rbac.models.role import RoleModel
    from identity_plan_kit.rbac.models.permission import PermissionModel
    from identity_plan_kit.rbac.models.role_permission import RolePermissionModel
    from identity_plan_kit.plans.models.plan import PlanModel
    from identity_plan_kit.plans.models.feature import FeatureModel
    from identity_plan_kit.plans.models.plan_limit import PlanLimitModel
    from identity_plan_kit.plans.models.plan_permission import PlanPermissionModel
    from identity_plan_kit.plans.models.user_plan import UserPlanModel
    from identity_plan_kit.plans.models.feature_usage import FeatureUsageModel

    return [
        # Auth models
        UserModel,
        UserProviderModel,
        RefreshTokenModel,
        # RBAC models
        RoleModel,
        PermissionModel,
        RolePermissionModel,
        # Plan models
        PlanModel,
        FeatureModel,
        PlanLimitModel,
        PlanPermissionModel,
        UserPlanModel,
        FeatureUsageModel,
    ]


def get_ipk_metadata() -> "MetaData":
    """
    Get IPK's SQLAlchemy metadata with all models registered.

    This ensures all models are imported and returns the metadata
    object that can be used for migrations.

    Returns:
        SQLAlchemy MetaData object

    Example:
        ```python
        from identity_plan_kit.migrations import get_ipk_metadata

        metadata = get_ipk_metadata()
        print(metadata.tables.keys())
        # dict_keys(['users', 'user_providers', 'refresh_tokens', ...])
        ```
    """
    # Import models to register them
    import_all_models()

    # Return the Base metadata
    from identity_plan_kit.shared.database import Base
    return Base.metadata


def configure_alembic_for_ipk() -> "MetaData":
    """
    Configure Alembic to include all IPK models.

    Call this in your alembic/env.py to get the metadata for migrations.
    Make sure to import your own models BEFORE calling this function
    so they are included in the metadata.

    Returns:
        SQLAlchemy MetaData object with all models

    Example:
        ```python
        # your_app/alembic/env.py
        from logging.config import fileConfig
        from alembic import context

        # Import your models first
        from your_app.models import *  # noqa

        # Then configure IPK
        from identity_plan_kit.migrations import configure_alembic_for_ipk

        target_metadata = configure_alembic_for_ipk()

        # ... rest of env.py
        ```
    """
    return get_ipk_metadata()


# Re-export commonly used items for convenience
from identity_plan_kit.shared.database import Base
from identity_plan_kit.shared.models import (
    BaseModel,
    BaseIntModel,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    IntPrimaryKeyMixin,
)

__all__ = [
    # Base classes for models
    "Base",
    "BaseModel",
    "BaseIntModel",
    # Mixins
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "IntPrimaryKeyMixin",
    # Functions
    "get_package_dir",
    "get_alembic_migrations_dir",
    "get_alembic_ini_path",
    "import_all_models",
    "get_ipk_metadata",
    "configure_alembic_for_ipk",
]
