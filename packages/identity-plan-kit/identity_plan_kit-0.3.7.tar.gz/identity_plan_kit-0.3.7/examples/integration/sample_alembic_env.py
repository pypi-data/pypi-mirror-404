"""
How to Integrate IdentityPlanKit with Your Existing Alembic Setup.

This file shows the CHANGES needed to your existing alembic/env.py,
NOT a full replacement. Your backend already has an env.py - you just
need to add a few lines to include IPK models in your migrations.

=============================================================================
STEP 1: Add these imports at the TOP of your existing env.py
=============================================================================

Add AFTER your existing imports, BEFORE target_metadata assignment:

```python
# -----------------------------------------------------------------------------
# IdentityPlanKit Integration
# -----------------------------------------------------------------------------
# Import your custom models that reference IPK's User (if any)
# from backend.features.profiles.models import ProfileModel

# Import and register all IPK models with your metadata
from identity_plan_kit.migrations import import_all_models
import_all_models()  # Registers: users, roles, plans, permissions, etc.
```

=============================================================================
STEP 2: Update your target_metadata
=============================================================================

You have two options depending on your setup:

OPTION A: If you're using IPK's Base for all models (RECOMMENDED)
---------------------------------------------------------------------
```python
# Change this:
from backend.core.database import Base
target_metadata = Base.metadata

# To this:
from identity_plan_kit import Base  # Use IPK's Base
target_metadata = Base.metadata
```

OPTION B: If you want to keep your own Base (more complex)
---------------------------------------------------------------------
```python
from backend.core.database import Base as YourBase
from identity_plan_kit.migrations import get_ipk_metadata

# Combine both metadata objects
from sqlalchemy import MetaData
target_metadata = MetaData()

# Copy IPK tables
for table in get_ipk_metadata().tables.values():
    table.to_metadata(target_metadata)

# Copy your tables
for table in YourBase.metadata.tables.values():
    if table.name not in target_metadata.tables:
        table.to_metadata(target_metadata)
```

=============================================================================
FULL EXAMPLE: Minimal changes to a typical production env.py
=============================================================================
"""

# =============================================================================
# BEFORE (typical production env.py)
# =============================================================================

BEFORE_EXAMPLE = '''
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Your existing base and models
from backend.core.infrastructure.database.models.base import Base
from backend.core.conf.settings import SETTINGS

# Import your models to register them
from backend.features.profiles.models import *  # noqa
from backend.features.organizations.models import *  # noqa

config = context.config
target_metadata = Base.metadata

# ... rest of your env.py (get_url, run_migrations_offline, etc.)
'''

# =============================================================================
# AFTER (with IPK integration)
# =============================================================================

AFTER_EXAMPLE = '''
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ============== CHANGE 1: Use IPK's Base instead of your own ==============
from identity_plan_kit import Base  # IPK's Base with naming conventions

from backend.core.conf.settings import SETTINGS

# ============== CHANGE 2: Import IPK models ==============
from identity_plan_kit.migrations import import_all_models
import_all_models()  # Registers all IPK tables

# Your existing model imports (these should now inherit from IPK's Base)
from backend.features.profiles.models import *  # noqa
from backend.features.organizations.models import *  # noqa

config = context.config
target_metadata = Base.metadata  # Now includes both IPK and your models

# ... rest of your env.py stays THE SAME
'''

# =============================================================================
# WHAT CHANGES IN YOUR MODELS
# =============================================================================

MODEL_CHANGES = '''
# BEFORE: Your models use your own Base
from backend.core.infrastructure.database.models.base import Base

class ProfileModel(Base):
    __tablename__ = "profiles"
    ...

# AFTER: Your models use IPK's BaseModel (includes UUID7 + timestamps)
from identity_plan_kit import BaseModel
from identity_plan_kit.auth.models.user import UserModel

class ProfileModel(BaseModel):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship("UserModel")
    ...
'''

# =============================================================================
# ACTUAL WORKING ENV.PY FOR COPY-PASTE
# =============================================================================
# Below is a complete, working env.py that you can adapt

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

# -----------------------------------------------------------------------------
# IPK Integration: Use IPK's Base and import all models
# -----------------------------------------------------------------------------
from identity_plan_kit import Base
from identity_plan_kit.migrations import import_all_models

# Register all IPK models (users, roles, plans, etc.)
import_all_models()

# Import YOUR models here (they should inherit from identity_plan_kit.BaseModel)
# from backend.features.profiles.models import ProfileModel
# from backend.features.organizations.models import OrganizationModel

# -----------------------------------------------------------------------------
# Alembic configuration
# -----------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Combined metadata (IPK models + your models)
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment."""
    # Adapt this to your settings structure:
    # return SETTINGS.DATABASE.DATABASE_URL

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = os.environ.get("IPK_DATABASE_URL", "")
    if not url:
        url = config.get_main_option("sqlalchemy.url", "")

    # Convert async to sync for Alembic
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")

    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with an active connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import create_engine

    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
