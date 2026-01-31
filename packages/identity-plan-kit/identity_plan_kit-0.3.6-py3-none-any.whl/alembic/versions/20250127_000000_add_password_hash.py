"""Add password_hash column to users table.

Revision ID: 002_add_password_hash
Revises: 001_initial
Create Date: 2025-01-27 00:00:00.000000

This migration adds password_hash column to support password-based
authentication for admin users (in addition to OAuth).

Security considerations:
- Column is nullable (OAuth-only users don't have passwords)
- Uses VARCHAR(255) to store bcrypt hashes (~60 chars)
- No index on password_hash (never queried directly)
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_password_hash"
down_revision: str | None = "001_initial"
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    """Add password_hash column to users table."""
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove password_hash column from users table."""
    op.drop_column("users", "password_hash")
