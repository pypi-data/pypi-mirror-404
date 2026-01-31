"""
Example: Extending identity-plan-kit models with custom fields.

This example demonstrates how to extend the library's models, entities, and DTOs
with custom fields (e.g., organization support) without modifying library code.

The extensibility pattern uses:
1. ModelRegistry - for custom SQLAlchemy model classes
2. EntityRegistry - for custom domain entity classes
3. DTORegistry - for custom Pydantic response classes
4. ExtensionConfig - combines all registries

Usage:
    # Run database migration first to add new columns
    alembic revision --autogenerate -m "add_organization_fields"
    alembic upgrade head

    # Then run your FastAPI app with extended models
    python examples/extending_models.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.auth.dto.responses import UserResponse
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.shared.registry import (
    DTORegistry,
    EntityRegistry,
    ExtensionConfig,
    ModelRegistry,
)


# =============================================================================
# Step 1: Define Extended Model
# =============================================================================


class OrganizationUserModel(UserModel):
    """
    Extended UserModel with organization support.

    This model adds organization-related fields to the base UserModel.
    The new columns will be added to the 'users' table.

    Note: You need to create a migration to add these columns:
        alembic revision --autogenerate -m "add_organization_fields"
    """

    # Organization the user belongs to (nullable for users without org)
    organization_id: Mapped[UUID | None] = mapped_column(
        # ForeignKey("organizations.id") - uncomment if you have organizations table
        nullable=True,
        default=None,
    )

    # Department within the organization
    department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    # Employee identifier (for enterprise SSO integrations)
    employee_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    # Custom metadata JSON field (if you need flexible storage)
    # custom_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


# =============================================================================
# Step 2: Define Extended Entity
# =============================================================================


@dataclass
class OrganizationUser(User):
    """
    Extended User entity with organization support.

    This entity adds organization fields to the base User dataclass.
    All business logic methods from User are inherited.
    """

    # Organization fields (must have defaults for dataclass inheritance)
    organization_id: UUID | None = None
    department: str | None = None
    employee_id: str | None = None

    # You can add custom business logic methods
    def is_in_organization(self) -> bool:
        """Check if user belongs to an organization."""
        return self.organization_id is not None

    def get_display_department(self) -> str:
        """Get display-friendly department name."""
        return self.department or "Unassigned"


# =============================================================================
# Step 3: Define Extended DTO (Optional)
# =============================================================================


class OrganizationUserResponse(UserResponse):
    """
    Extended UserResponse with organization fields.

    This DTO includes organization fields in API responses.
    """

    organization_id: UUID | None = Field(
        default=None,
        description="ID of the organization the user belongs to",
    )
    department: str | None = Field(
        default=None,
        description="User's department within the organization",
    )
    employee_id: str | None = Field(
        default=None,
        description="Employee identifier for enterprise SSO",
    )


# =============================================================================
# Step 4: Configure the Extension
# =============================================================================


def create_organization_extension_config() -> ExtensionConfig:
    """
    Create extension config with organization support.

    Returns:
        ExtensionConfig ready to use with IdentityPlanKit
    """
    return ExtensionConfig(
        models=ModelRegistry(
            user_model=OrganizationUserModel,
        ),
        entities=EntityRegistry(
            user_entity=OrganizationUser,
        ),
        dtos=DTORegistry(
            user_response=OrganizationUserResponse,
        ),
    )


# =============================================================================
# Step 5: Use with IdentityPlanKit
# =============================================================================


def example_usage():
    """
    Example of using the extension with IdentityPlanKit.

    This shows how to configure IPK with custom models.
    """
    from fastapi import FastAPI

    from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig

    # Create extension config
    extension_config = create_organization_extension_config()

    # Create IPK config
    config = IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/myapp",
        secret_key="your-secret-key-at-least-32-characters-long",
        google_client_id="your-google-client-id",
        google_client_secret="your-google-client-secret",
        google_redirect_uri="http://localhost:8000/auth/google/callback",
    )

    # Set extension config (this enables custom models)
    config.set_extension_config(extension_config)

    # Create Kit instance
    kit = IdentityPlanKit(config)

    # Create FastAPI app
    app = FastAPI(
        title="My App with Extended User",
        lifespan=kit.lifespan,
    )

    # Setup IPK routes
    kit.setup(app)

    return app


# =============================================================================
# Example: Creating Users with Custom Fields
# =============================================================================


async def example_create_user_with_organization(kit):
    """
    Example of creating a user with organization fields.

    Note: This is illustrative - actual usage would be through
    the OAuth flow which creates users automatically.
    """
    from identity_plan_kit.auth.uow import AuthUnitOfWork
    from identity_plan_kit.shared.registry import ExtensionConfig, ModelRegistry, EntityRegistry

    # When using extension config, the UoW will use extended models
    extension_config = create_organization_extension_config()

    async with AuthUnitOfWork(
        kit.session_factory,
        extension_config=extension_config,
    ) as uow:
        # Create user with custom fields
        user = await uow.users.create(
            email="employee@company.com",
            role_id=...,  # Your role ID
            display_name="John Doe",
            # Extended fields passed via **extra_fields
            organization_id=...,  # Your organization ID
            department="Engineering",
            employee_id="EMP001",
        )

        # user is now an OrganizationUser instance
        print(f"Created user: {user.email}")
        print(f"Department: {user.department}")
        print(f"Employee ID: {user.employee_id}")

        # Business logic methods work
        if user.is_in_organization():
            print(f"User is in organization: {user.organization_id}")


# =============================================================================
# Migration Example
# =============================================================================

MIGRATION_EXAMPLE = """
# Example Alembic migration for adding organization fields

'''add organization fields to users

Revision ID: abc123
Revises: previous_revision
Create Date: 2024-01-01 00:00:00.000000

'''
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'abc123'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add organization_id column (nullable for existing users)
    op.add_column(
        'users',
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add department column
    op.add_column(
        'users',
        sa.Column('department', sa.String(100), nullable=True)
    )

    # Add employee_id column
    op.add_column(
        'users',
        sa.Column('employee_id', sa.String(50), nullable=True)
    )

    # Optional: Add index for organization lookups
    op.create_index(
        'ix_users_organization_id',
        'users',
        ['organization_id']
    )


def downgrade() -> None:
    op.drop_index('ix_users_organization_id', table_name='users')
    op.drop_column('users', 'employee_id')
    op.drop_column('users', 'department')
    op.drop_column('users', 'organization_id')
"""


if __name__ == "__main__":
    print("Extension Example: Organization User Support")
    print("=" * 50)
    print()
    print("This example shows how to extend identity-plan-kit with custom fields.")
    print()
    print("Key concepts:")
    print("1. OrganizationUserModel - extends UserModel with new columns")
    print("2. OrganizationUser - extends User entity with new fields")
    print("3. OrganizationUserResponse - extends UserResponse DTO")
    print("4. ExtensionConfig - wires everything together")
    print()
    print("To use in your app:")
    print("  1. Copy the model/entity/DTO classes to your project")
    print("  2. Create an Alembic migration to add the new columns")
    print("  3. Configure IPK with extension_config.set_extension_config()")
    print()
    print("See MIGRATION_EXAMPLE variable for migration template.")
