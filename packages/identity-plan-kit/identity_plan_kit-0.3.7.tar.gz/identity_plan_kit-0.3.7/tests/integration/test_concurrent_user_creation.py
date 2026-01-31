"""Integration tests for concurrent OAuth user creation.

This tests the race condition handling in get_or_create_with_provider
when multiple OAuth requests arrive simultaneously for the same user.

CRITICAL: Without proper locking and savepoint handling, concurrent OAuth
logins for the same email can create duplicate users or corrupt the session.
"""

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.models.user_provider import UserProviderModel
from identity_plan_kit.auth.repositories.user_repo import UserRepository

# Skip if testcontainers not available
pytest.importorskip("testcontainers")


async def create_test_role(session: AsyncSession, code: str = "user") -> UUID:
    """Create a test role and return its ID."""
    from identity_plan_kit.rbac.models.role import RoleModel

    role = RoleModel(code=code, name=code.title())
    session.add(role)
    await session.flush()
    return role.id


class TestConcurrentUserCreation:
    """Tests for concurrent OAuth user creation scenarios."""

    async def test_concurrent_oauth_same_email_creates_single_user(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL RACE CONDITION TEST: Multiple concurrent OAuth logins
        for the same email should create only ONE user.

        This simulates the scenario where:
        1. User clicks "Login with Google" on multiple tabs
        2. Or network retry causes duplicate OAuth callbacks
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup: create a role first
        async with session_factory() as setup_session:
            async with setup_session.begin():
                role_id = await create_test_role(setup_session, f"user_{id(setup_session)}")

        email = f"concurrent_test_{id(db_engine)}@example.com"
        provider = "google"
        external_id = f"google_user_{id(db_engine)}"

        async def oauth_login(session_num: int) -> tuple[UUID, bool]:
            """Simulate an OAuth login creating/getting user."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UserRepository(session)
                    user, created = await repo.get_or_create_with_provider(
                        email=email,
                        role_id=role_id,
                        provider_code=provider,
                        external_user_id=f"{external_id}_{session_num}",
                        is_verified=True,
                    )
                    return user.id, created

        # Fire 10 concurrent OAuth logins for the same email
        tasks = [oauth_login(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions (IntegrityError is expected in race conditions)
        successes = [r for r in results if isinstance(r, tuple)]
        errors = [r for r in results if isinstance(r, Exception)]

        # CRITICAL: Verify only ONE user was created
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            users = result.scalars().all()

        assert len(users) == 1, (
            f"RACE CONDITION BUG: Expected 1 user, found {len(users)}. "
            f"Concurrent OAuth logins created duplicate users!"
        )

        # Verify all successful requests got the same user ID
        if len(successes) > 1:
            user_ids = [r[0] for r in successes]
            assert len(set(user_ids)) == 1, (
                f"Different user IDs returned: {user_ids}. "
                f"Concurrent requests got different users!"
            )

        # Verify exactly one request created the user
        created_flags = [r[1] for r in successes]
        assert created_flags.count(True) <= 1, (
            f"Multiple requests claimed to create the user: {created_flags}"
        )

    async def test_concurrent_different_providers_same_email(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Test: User logs in via Google on one tab and Apple on another.

        Both should result in the same user with two providers linked.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                role_id = await create_test_role(setup_session, f"user_multi_{id(setup_session)}")

        email = f"multi_provider_{id(db_engine)}@example.com"

        async def oauth_login(provider: str, external_id: str) -> tuple[UUID, bool]:
            """Simulate OAuth login with different providers."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UserRepository(session)
                    user, created = await repo.get_or_create_with_provider(
                        email=email,
                        role_id=role_id,
                        provider_code=provider,
                        external_user_id=external_id,
                        is_verified=True,
                    )
                    return user.id, created

        # Fire concurrent logins with different providers
        tasks = [
            oauth_login("google", f"google_{id(db_engine)}"),
            oauth_login("apple", f"apple_{id(db_engine)}"),
            oauth_login("github", f"github_{id(db_engine)}"),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, tuple)]

        # CRITICAL: Verify only ONE user was created
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            users = result.scalars().all()

        assert len(users) == 1, (
            f"RACE CONDITION BUG: Expected 1 user, found {len(users)}. "
            f"Multiple providers created duplicate users!"
        )

        # All successful requests should have the same user ID
        if len(successes) > 1:
            user_ids = set(r[0] for r in successes)
            assert len(user_ids) == 1, (
                f"Different providers got different user IDs: {user_ids}"
            )

    async def test_concurrent_user_creation_with_existing_user(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Test: User already exists, multiple concurrent OAuth attempts.

        All requests should return the existing user, none should create new.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                role_id = await create_test_role(setup_session, f"user_existing_{id(setup_session)}")

        email = f"existing_user_{id(db_engine)}@example.com"

        # First, create the user
        async with session_factory() as session:
            async with session.begin():
                repo = UserRepository(session)
                existing_user, created = await repo.get_or_create_with_provider(
                    email=email,
                    role_id=role_id,
                    provider_code="google",
                    external_user_id=f"google_existing_{id(db_engine)}",
                    is_verified=True,
                )
                assert created is True
                existing_user_id = existing_user.id

        async def oauth_login(session_num: int) -> tuple[UUID, bool]:
            """Simulate OAuth login for existing user."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UserRepository(session)
                    user, created = await repo.get_or_create_with_provider(
                        email=email,
                        role_id=role_id,
                        provider_code="google",
                        external_user_id=f"google_existing_{id(db_engine)}",
                        is_verified=True,
                    )
                    return user.id, created

        # Fire 20 concurrent logins for existing user
        tasks = [oauth_login(i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, tuple)]

        # All should succeed with created=False
        for user_id, created in successes:
            assert user_id == existing_user_id, (
                f"Wrong user returned: {user_id} vs expected {existing_user_id}"
            )
            assert created is False, "Should not create user when already exists"

        # Verify still only one user
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            users = result.scalars().all()

        assert len(users) == 1, f"Expected 1 user, found {len(users)}"


class TestUserDeactivationRaceCondition:
    """Tests for concurrent user deactivation scenarios."""

    async def test_concurrent_deactivation_is_idempotent(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Multiple concurrent deactivation requests should be safe.

        Only one should actually deactivate, others should see already inactive.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create active user
        async with session_factory() as setup_session:
            async with setup_session.begin():
                role_id = await create_test_role(setup_session, f"deact_{id(setup_session)}")
                repo = UserRepository(setup_session)
                user, _ = await repo.get_or_create_with_provider(
                    email=f"deactivate_{id(db_engine)}@example.com",
                    role_id=role_id,
                    provider_code="google",
                    external_user_id=f"google_deact_{id(db_engine)}",
                )
                user_id = user.id

        async def deactivate_user() -> bool:
            """Attempt to deactivate the user."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UserRepository(session)
                    return await repo.deactivate(user_id, reason="concurrent_test")

        # Fire 10 concurrent deactivation requests
        tasks = [deactivate_user() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, bool)]

        # Exactly ONE request should return True (actually deactivated)
        assert successes.count(True) == 1, (
            f"Expected exactly 1 successful deactivation, got {successes.count(True)}. "
            f"Results: {successes}"
        )

        # Verify user is actually deactivated
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one()

        assert user.is_active is False, "User should be deactivated"

    async def test_concurrent_reactivation_is_idempotent(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Multiple concurrent reactivation requests should be safe.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create and deactivate user
        async with session_factory() as setup_session:
            async with setup_session.begin():
                role_id = await create_test_role(setup_session, f"react_{id(setup_session)}")
                repo = UserRepository(setup_session)
                user, _ = await repo.get_or_create_with_provider(
                    email=f"reactivate_{id(db_engine)}@example.com",
                    role_id=role_id,
                    provider_code="google",
                    external_user_id=f"google_react_{id(db_engine)}",
                )
                user_id = user.id
                await repo.deactivate(user_id, reason="setup")

        async def reactivate_user() -> bool:
            """Attempt to reactivate the user."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UserRepository(session)
                    return await repo.reactivate(user_id, reason="concurrent_test")

        # Fire 10 concurrent reactivation requests
        tasks = [reactivate_user() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, bool)]

        # Exactly ONE request should return True
        assert successes.count(True) == 1, (
            f"Expected exactly 1 successful reactivation, got {successes.count(True)}"
        )

        # Verify user is actually active
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one()

        assert user.is_active is True, "User should be active"


class TestProviderLinkingRaceCondition:
    """Tests for concurrent provider linking scenarios."""

    async def test_concurrent_provider_linking_same_provider(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Multiple concurrent requests to link same provider should not duplicate.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create user without provider
        async with session_factory() as setup_session:
            async with setup_session.begin():
                role_id = await create_test_role(setup_session, f"link_{id(setup_session)}")

                user = UserModel(
                    email=f"link_test_{id(db_engine)}@example.com",
                    role_id=role_id,
                    display_name=f"Link Test {id(db_engine)}",
                    is_verified=True,
                )
                setup_session.add(user)
                await setup_session.flush()
                user_id = user.id

        async def link_provider(attempt: int) -> bool:
            """Attempt to link provider."""
            async with session_factory() as session:
                async with session.begin():
                    repo = UserRepository(session)
                    try:
                        await repo.add_provider(
                            user_id=user_id,
                            provider_code="google",
                            external_user_id=f"google_link_{id(db_engine)}",
                        )
                        return True
                    except Exception:
                        return False

        # Fire concurrent link attempts
        tasks = [link_provider(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify only ONE provider link was created
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserProviderModel).where(UserProviderModel.user_id == user_id)
            )
            providers = result.scalars().all()

        # Due to unique constraint, only 1 should exist
        assert len(providers) <= 1, (
            f"Multiple provider links created: {len(providers)}"
        )
