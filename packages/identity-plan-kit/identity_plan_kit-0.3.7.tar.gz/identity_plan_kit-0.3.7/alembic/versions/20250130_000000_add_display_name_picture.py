"""Add display_name and picture_url columns to users table.

Revision ID: 003_add_display_name_picture
Revises: 002_add_password_hash
Create Date: 2025-01-30 00:00:00.000000

This migration adds profile fields to support OAuth profile data:
- display_name: User's display name (from OAuth provider's 'name' field)
- picture_url: Profile picture URL (from OAuth provider)

For existing users:
- display_name is populated from email prefix (part before @)
- picture_url is set to NULL (we don't have historical data)
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_display_name_picture"
down_revision: str | None = "002_add_password_hash"
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    """Add display_name and picture_url columns to users table."""
    op.add_column(
        "users",
        sa.Column(
            "picture_url",
            sa.String(500),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "display_name",
            sa.String(100),
            nullable=False,
            server_default="",
        ),
    )

    # Populate display_name from email prefix for existing users
    op.execute(
        """
        UPDATE users
        SET display_name = SPLIT_PART(email, '@', 1)
        WHERE display_name = ''
        """
    )

    op.alter_column(
        "users",
        "display_name",
        server_default=None,
    )


def downgrade() -> None:
    """Remove display_name and picture_url columns from users table."""
    op.drop_column("users", "display_name")
    op.drop_column("users", "picture_url")
