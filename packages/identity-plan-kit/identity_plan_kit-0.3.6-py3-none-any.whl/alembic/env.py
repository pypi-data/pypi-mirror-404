"""Alembic environment configuration for async migrations."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models to ensure they're registered with Base.metadata
from identity_plan_kit.shared.database import Base

# Import all model modules to register them
from identity_plan_kit.auth.models import user, user_provider, refresh_token  # noqa: F401
from identity_plan_kit.rbac.models import role, permission, role_permission  # noqa: F401
from identity_plan_kit.plans.models import (  # noqa: F401
    plan,
    feature,
    plan_limit,
    user_plan,
    feature_usage,
    plan_permission,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from environment or config.

    For migrations, we need a sync driver (psycopg2), not async (asyncpg).
    The IPK_DATABASE_URL uses asyncpg, so we convert it.
    """
    url = os.environ.get("IPK_DATABASE_URL", "")

    if not url:
        # Fall back to alembic.ini value
        url = config.get_main_option("sqlalchemy.url", "")

    # Convert async URL to sync for migrations
    # postgresql+asyncpg://... -> postgresql://...
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")

    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
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
    """Run migrations with connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode.

    Creates an async engine and runs migrations within a connection.
    """
    # Get sync URL for alembic (it handles the connection itself)
    url = get_url()

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    # Use sync engine for migrations (Alembic doesn't fully support async)
    from sqlalchemy import create_engine

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates a connection and runs migrations.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
