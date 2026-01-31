"""Initial schema for IdentityPlanKit.

Revision ID: 001_initial
Revises:
Create Date: 2025-01-24 00:00:00.000000

This migration creates all core tables for:
- Authentication (users, providers, refresh_tokens)
- RBAC (roles, permissions, role_permissions)
- Plans (plans, features, limits, user_plans, usage)

Rollback Plan:
- This migration drops all tables in reverse order
- WARNING: Rollback will DELETE ALL DATA
- Before rollback in production, ensure data backup exists
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from uuid_utils import uuid7

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""

    # =============================================
    # CORE TABLES
    # =============================================

    # Roles table
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("code", name=op.f("uq_roles_code")),
    )
    op.create_index(op.f("ix_roles_code"), "roles", ["code"], unique=True)

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_users_role_id_roles"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # User providers table (OAuth)
    op.create_table(
        "user_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_user_id", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_providers_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_providers")),
    )
    op.create_index(
        op.f("ix_user_providers_external_id"),
        "user_providers",
        ["external_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_providers_unique",
        "user_providers",
        ["code", "external_user_id"],
        unique=True,
    )

    # Refresh tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"),
        "refresh_tokens",
        ["token_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"),
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )
    # P2 FIX: Partial index for active token lookups (revoked_at IS NULL)
    # This optimizes the common query pattern of looking up non-revoked tokens
    # by hash, which happens on every authenticated request validation.
    op.execute(
        """
        CREATE INDEX ix_refresh_tokens_hash_active
        ON refresh_tokens (token_hash)
        WHERE revoked_at IS NULL
        """
    )
    # Index for token cleanup queries (finding expired tokens)
    op.create_index(
        "ix_refresh_tokens_expires_at",
        "refresh_tokens",
        ["expires_at"],
        unique=False,
    )
    # Composite index for cleanup queries filtering by expiry and revocation
    op.create_index(
        "ix_refresh_tokens_cleanup",
        "refresh_tokens",
        ["expires_at", "revoked_at"],
        unique=False,
    )

    # =============================================
    # RBAC TABLES
    # =============================================

    # Permissions table
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(255), nullable=False),
        sa.Column("type", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
        sa.UniqueConstraint("code", name=op.f("uq_permissions_code")),
        sa.CheckConstraint("type IN ('role', 'plan')", name="ck_permissions_type"),
    )

    # Role permissions junction table
    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_role_permissions_role_id_roles"),
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_role_permissions_permission_id_permissions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permissions")),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permissions_role_permission"
        ),
    )
    op.create_index(
        op.f("ix_role_permissions_role_id"),
        "role_permissions",
        ["role_id"],
        unique=False,
    )

    # =============================================
    # PLANS & FEATURES TABLES
    # =============================================

    # Plans table
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plans")),
        sa.UniqueConstraint("code", name=op.f("uq_plans_code")),
    )

    # Features table
    op.create_table(
        "features",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_features")),
        sa.UniqueConstraint("code", name=op.f("uq_features_code")),
    )

    # Plan limits table
    op.create_table(
        "plan_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_limit", sa.BigInteger(), nullable=False),
        sa.Column("period", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_plan_limits_plan_id_plans"),
        ),
        sa.ForeignKeyConstraint(
            ["feature_id"],
            ["features.id"],
            name=op.f("fk_plan_limits_feature_id_features"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_limits")),
        sa.CheckConstraint(
            "period IS NULL OR period IN ('daily', 'monthly', 'lifetime')",
            name="ck_plan_limits_period",
        ),
    )
    op.create_index(
        op.f("ix_plan_limits_plan_id"),
        "plan_limits",
        ["plan_id"],
        unique=False,
    )

    # Plan permissions table
    op.create_table(
        "plan_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_plan_permissions_plan_id_plans"),
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_plan_permissions_permission_id_permissions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plan_permissions")),
        sa.UniqueConstraint(
            "plan_id", "permission_id", name="uq_plan_permissions_plan_permission"
        ),
    )
    op.create_index(
        op.f("ix_plan_permissions_plan_id"),
        "plan_permissions",
        ["plan_id"],
        unique=False,
    )

    # User plans table
    op.create_table(
        "user_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.Date(), nullable=False),
        sa.Column("ends_at", sa.Date(), nullable=False),
        sa.Column("custom_limits", postgresql.JSONB(), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_plans_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_user_plans_plan_id_plans"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_plans")),
    )
    op.create_index(
        op.f("ix_user_plans_user_id"),
        "user_plans",
        ["user_id"],
        unique=False,
    )
    # P1 FIX: Composite index for active plan lookups (user_id + date range + not cancelled)
    op.create_index(
        "ix_user_plans_active_lookup",
        "user_plans",
        ["user_id", "started_at", "ends_at"],
        unique=False,
    )
    # Index for finding active (non-cancelled) plans
    op.execute(
        """
        CREATE INDEX ix_user_plans_active_not_cancelled
        ON user_plans (user_id, started_at, ends_at)
        WHERE is_cancelled = false
        """
    )

    # Feature usage table
    op.create_table(
        "feature_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_usage", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("start_period", sa.Date(), nullable=False),
        sa.Column("end_period", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_plan_id"],
            ["user_plans.id"],
            name=op.f("fk_feature_usage_user_plan_id_user_plans"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["feature_id"],
            ["features.id"],
            name=op.f("fk_feature_usage_feature_id_features"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feature_usage")),
        # P0 FIX: Unique constraint required for atomic upsert in usage tracking
        sa.UniqueConstraint(
            "user_plan_id", "feature_id", "start_period",
            name="uq_usage_plan_feature_period",
        ),
    )
    # Composite index for period-based queries
    op.create_index(
        "ix_feature_usage_period_lookup",
        "feature_usage",
        ["user_plan_id", "feature_id", "start_period", "end_period"],
        unique=False,
    )

    # =============================================
    # SEED DATA
    # =============================================

    # Generate UUID7s for seed data
    admin_role_id = str(uuid7())
    user_role_id = str(uuid7())
    free_plan_id = str(uuid7())
    pro_plan_id = str(uuid7())

    # Insert default roles
    op.execute(
        f"""
        INSERT INTO roles (id, code, name) VALUES
        ('{admin_role_id}', 'admin', 'Administrator'),
        ('{user_role_id}', 'user', 'User')
        """
    )

    # Insert default plans
    op.execute(
        f"""
        INSERT INTO plans (id, code, name) VALUES
        ('{free_plan_id}', 'free', 'Free Plan'),
        ('{pro_plan_id}', 'pro', 'Pro Plan')
        """
    )


def downgrade() -> None:
    """Drop all tables in reverse order.

    WARNING: This will DELETE ALL DATA.
    Ensure you have backups before running in production.
    """
    # Drop in reverse order of creation (respecting foreign keys)
    op.drop_table("feature_usage")
    op.drop_table("user_plans")
    op.drop_table("plan_permissions")
    op.drop_table("plan_limits")
    op.drop_table("features")
    op.drop_table("plans")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    # Drop partial index before dropping table
    op.execute("DROP INDEX IF EXISTS ix_refresh_tokens_hash_active")
    op.drop_table("refresh_tokens")
    op.drop_table("user_providers")
    op.drop_table("users")
    op.drop_table("roles")