"""Integration tests for UserRepository with real PostgreSQL.

Tests cover:
- User CRUD operations
- Unique email constraint
- User deactivation
- Provider linking
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.repositories.user_repo import UserRepository


# Skip if testcontainers not available
pytest.importorskip("testcontainers")


class TestUserRepositoryIntegration:
    """Integration tests for UserRepository with real database."""

    async def test_create_user(
        self,
        db_session: AsyncSession,
        create_test_role,
    ):
        """User can be created in database."""
        role_id = await create_test_role("user", "User")
        repo = UserRepository(db_session)

        user = await repo.create(
            email="newuser@example.com",
            role_id=role_id,
        )

        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.is_active is True

    async def test_get_user_by_email(
        self,
        db_session: AsyncSession,
        create_test_user,
    ):
        """User can be retrieved by email."""
        await create_test_user("findme@example.com")
        repo = UserRepository(db_session)

        user = await repo.get_by_email("findme@example.com")

        assert user is not None
        assert user.email == "findme@example.com"

    async def test_get_user_by_email_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Returns None for non-existent email."""
        repo = UserRepository(db_session)

        user = await repo.get_by_email("nonexistent@example.com")

        assert user is None

    async def test_unique_email_constraint(
        self,
        db_session: AsyncSession,
        create_test_role,
    ):
        """Duplicate email raises IntegrityError."""
        role_id = await create_test_role("user", "User")
        repo = UserRepository(db_session)

        # Create first user
        await repo.create(email="duplicate@example.com", role_id=role_id)

        # Attempt duplicate
        with pytest.raises(IntegrityError):
            await repo.create(email="duplicate@example.com", role_id=role_id)

    async def test_get_or_create_creates_new(
        self,
        db_session: AsyncSession,
        create_test_role,
    ):
        """get_or_create creates new user when not exists."""
        role_id = await create_test_role("user", "User")
        repo = UserRepository(db_session)

        user, created = await repo.get_or_create_with_provider(
            email="newprovider@example.com",
            role_id=role_id,
            provider_code="google",
            external_user_id="google_12345",
            is_verified=True,
        )

        assert created is True
        assert user.email == "newprovider@example.com"

    async def test_get_or_create_returns_existing(
        self,
        db_session: AsyncSession,
        create_test_user,
    ):
        """get_or_create returns existing user."""
        user_id = await create_test_user("existing@example.com")
        repo = UserRepository(db_session)

        user, created = await repo.get_or_create_with_provider(
            email="existing@example.com",
            role_id=2,  # Doesn't matter for existing
            provider_code="google",
            external_user_id="google_99999",
            is_verified=True,
        )

        assert created is False
        # Compare as strings to handle potential UUID type differences
        assert str(user.id) == str(user_id)

    async def test_deactivate_user(
        self,
        db_session: AsyncSession,
        create_test_user,
    ):
        """User can be deactivated."""
        user_id = await create_test_user("tobedeactivated@example.com")
        repo = UserRepository(db_session)

        await repo.deactivate(user_id, reason="test")

        # Verify deactivated
        user = await repo.get_by_id(user_id)
        assert user is not None
        assert user.is_active is False


class TestUserRepositoryConcurrency:
    """Test concurrent operations on UserRepository."""

    async def test_concurrent_get_or_create(
        self,
        db_session: AsyncSession,
        create_test_role,
    ):
        """Concurrent get_or_create for same email doesn't create duplicates."""
        # This test verifies the race-condition handling
        # Note: This is a simplified test; real concurrent testing
        # would require separate database sessions

        role_id = await create_test_role("user", "User")
        repo = UserRepository(db_session)

        # First call creates
        user1, created1 = await repo.get_or_create_with_provider(
            email="concurrent@example.com",
            role_id=role_id,
            provider_code="google",
            external_user_id="google_1",
            is_verified=True,
        )

        # Second call finds existing
        user2, created2 = await repo.get_or_create_with_provider(
            email="concurrent@example.com",
            role_id=role_id,
            provider_code="google",
            external_user_id="google_2",  # Different provider ID
            is_verified=True,
        )

        assert created1 is True
        assert created2 is False
        assert user1.id == user2.id  # Same user
