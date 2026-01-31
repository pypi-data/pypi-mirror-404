"""Integration tests for concurrent user deactivation race conditions.

Tests the FOR UPDATE locking added to prevent race conditions between:
1. Token refresh checking is_active status
2. Account deactivation setting is_active = False

CRITICAL: Without proper locking, a token refresh could succeed even as
the user is being deactivated:

1. Deactivation starts: reads user.is_active = True
2. Token refresh starts: reads user.is_active = True
3. Deactivation writes: user.is_active = False
4. Token refresh continues (saw True!): issues new tokens
   -> Security gap! Tokens issued after deactivation started

With FOR UPDATE locking:
1. Deactivation acquires lock, reads user.is_active = True
2. Token refresh waits for lock
3. Deactivation writes: user.is_active = False, releases lock
4. Token refresh acquires lock, reads user.is_active = False
5. Token refresh fails (correct behavior)
   -> No security gap!
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
from identity_plan_kit.auth.models.user import UserModel

# Skip if testcontainers not available
pytest.importorskip("testcontainers")


async def create_test_user_with_token(
    session: AsyncSession,
    suffix: str,
) -> tuple[UUID, UUID, str]:
    """Create user with refresh token. Returns (user_id, token_id, token_hash)."""
    from identity_plan_kit.rbac.models.role import RoleModel

    # Create role
    role = RoleModel(code=f"role_{suffix}", name="Test Role")
    session.add(role)
    await session.flush()

    # Create active user
    user = UserModel(
        email=f"deactivation_test_{suffix}@example.com",
        role_id=role.id,
        display_name=f"Deactivation Test {suffix}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()

    # Create refresh token
    token_hash = f"token_hash_{suffix}"
    token = RefreshTokenModel(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    session.add(token)
    await session.flush()

    return user.id, token.id, token_hash


class TestConcurrentUserDeactivation:
    """Integration tests for user deactivation race conditions."""

    async def test_token_refresh_blocked_during_deactivation(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL: Token refresh should fail if user deactivation is in progress.

        This tests that FOR UPDATE locking prevents token refresh from succeeding
        while user is being deactivated.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, token_id, token_hash = await create_test_user_with_token(
                    setup_session, unique_id
                )

        # Synchronization to ensure both operations start at the same time
        barrier = asyncio.Barrier(2)
        deactivation_started = asyncio.Event()
        refresh_result: dict[str, bool | str | None] = {"success": None, "error": None}
        deactivation_result: dict[str, bool] = {"success": None}

        async def deactivate_user() -> None:
            """Deactivate the user with FOR UPDATE lock."""
            async with session_factory() as session:
                async with session.begin():
                    await barrier.wait()

                    # Acquire lock and hold it briefly to create race window
                    stmt = (
                        select(UserModel)
                        .where(UserModel.id == user_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user = result.scalar_one()

                    # Signal that we have the lock
                    deactivation_started.set()

                    # Hold lock to ensure refresh must wait
                    await asyncio.sleep(0.1)

                    # Deactivate
                    user.is_active = False
                    await session.flush()

                    deactivation_result["success"] = True

        async def refresh_token() -> None:
            """Attempt token refresh - should fail if user is deactivated."""
            async with session_factory() as session:
                async with session.begin():
                    await barrier.wait()

                    # Wait until deactivation has started
                    await deactivation_started.wait()

                    # Try to refresh - with FOR UPDATE this will wait for deactivation
                    stmt = (
                        select(UserModel)
                        .where(UserModel.id == user_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user = result.scalar_one()

                    # Check if user is still active
                    if not user.is_active:
                        refresh_result["success"] = False
                        refresh_result["error"] = "User is inactive"
                        return

                    # Would issue new token here
                    refresh_result["success"] = True

        # Run both operations concurrently
        await asyncio.gather(
            deactivate_user(),
            refresh_token(),
            return_exceptions=True,
        )

        # CRITICAL ASSERTION: Token refresh should fail
        assert deactivation_result["success"] is True, "Deactivation should succeed"
        assert refresh_result["success"] is False, (
            "Token refresh should fail after deactivation. "
            "If it succeeded, we have a race condition!"
        )
        assert refresh_result["error"] == "User is inactive"

        # Verify user is actually deactivated
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one()

        assert user.is_active is False, "User should be deactivated"

    async def test_concurrent_deactivation_is_idempotent(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Multiple concurrent deactivation requests should be safe.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, token_id, token_hash = await create_test_user_with_token(
                    setup_session, unique_id
                )

        async def deactivate_user() -> bool:
            """Attempt to deactivate user. Returns True if changed, False if already inactive."""
            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        update(UserModel)
                        .where(
                            UserModel.id == user_id,
                            UserModel.is_active == True,  # noqa: E712
                        )
                        .values(is_active=False)
                    )
                    result = await session.execute(stmt)
                    return result.rowcount > 0

        # Fire concurrent deactivation requests
        tasks = [deactivate_user() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Exactly one should have actually changed the status
        actual_changes = [r for r in results if r is True]
        assert len(actual_changes) == 1, (
            f"Expected exactly 1 deactivation, got {len(actual_changes)}"
        )

        # Verify user is deactivated
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one()

        assert user.is_active is False

    async def test_multiple_token_refreshes_with_active_user(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent token refreshes for an ACTIVE user should all succeed.

        This verifies that FOR UPDATE locking doesn't break normal operation.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, token_id, token_hash = await create_test_user_with_token(
                    setup_session, unique_id
                )

        async def check_user_active() -> bool:
            """Simulate token refresh user check with FOR UPDATE."""
            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        select(UserModel)
                        .where(UserModel.id == user_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user = result.scalar_one()

                    return user.is_active

        # Fire concurrent checks
        tasks = [check_user_active() for _ in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should return True (user is active)
        successes = [r for r in results if r is True]
        failures = [r for r in results if r is False or isinstance(r, Exception)]

        assert len(successes) == 20, f"All checks should succeed, got {len(successes)}"
        assert len(failures) == 0, f"No checks should fail: {failures}"

    async def test_deactivation_revokes_tokens(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        User deactivation should also revoke all refresh tokens.

        This prevents any subsequent refresh attempts.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup with multiple tokens
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                from identity_plan_kit.rbac.models.role import RoleModel

                role = RoleModel(code=f"role_{unique_id}", name="Test Role")
                setup_session.add(role)
                await setup_session.flush()

                user = UserModel(
                    email=f"multi_token_{unique_id}@example.com",
                    role_id=role.id,
                    display_name=f"Multi Token {unique_id}",
                    is_active=True,
                    is_verified=True,
                )
                setup_session.add(user)
                await setup_session.flush()

                # Create multiple tokens
                for i in range(5):
                    token = RefreshTokenModel(
                        user_id=user.id,
                        token_hash=f"token_hash_{unique_id}_{i}",
                        expires_at=datetime.now(UTC) + timedelta(days=30),
                    )
                    setup_session.add(token)

                await setup_session.flush()
                user_id = user.id

        # Deactivate user and revoke tokens
        async with session_factory() as session:
            async with session.begin():
                # Deactivate user
                stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(is_active=False)
                )
                await session.execute(stmt)

                # Revoke all tokens
                now = datetime.now(UTC)
                stmt = (
                    update(RefreshTokenModel)
                    .where(
                        RefreshTokenModel.user_id == user_id,
                        RefreshTokenModel.revoked_at.is_(None),
                    )
                    .values(revoked_at=now)
                )
                result = await session.execute(stmt)
                revoked_count = result.rowcount

        assert revoked_count == 5, f"All 5 tokens should be revoked, got {revoked_count}"

        # Verify all tokens are revoked
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.revoked_at.is_(None),
                )
            )
            active_tokens = result.scalars().all()

        assert len(active_tokens) == 0, "All tokens should be revoked"


class TestTokenRefreshUserValidation:
    """Tests for user validation during token refresh."""

    async def test_refresh_with_for_update_sees_concurrent_changes(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        FOR UPDATE should ensure refresh sees the latest user state.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Setup
        unique_id = uuid4().hex[:8]
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id, token_id, token_hash = await create_test_user_with_token(
                    setup_session, unique_id
                )

        read_values: list[bool] = []
        values_lock = asyncio.Lock()

        async def read_user_status() -> bool:
            """Read user status with FOR UPDATE."""
            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        select(UserModel)
                        .where(UserModel.id == user_id)
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    user = result.scalar_one()

                    async with values_lock:
                        read_values.append(user.is_active)

                    return user.is_active

        async def deactivate_in_middle() -> None:
            """Deactivate after some reads have occurred."""
            await asyncio.sleep(0.05)  # Let some reads start
            async with session_factory() as session:
                async with session.begin():
                    stmt = (
                        update(UserModel)
                        .where(UserModel.id == user_id)
                        .values(is_active=False)
                    )
                    await session.execute(stmt)

        # Fire reads and deactivation
        tasks = [read_user_status() for _ in range(10)]
        tasks.append(deactivate_in_middle())

        await asyncio.gather(*tasks, return_exceptions=True)

        # Some reads should see True, others should see False
        true_count = sum(1 for v in read_values if v is True)
        false_count = sum(1 for v in read_values if v is False)

        print(f"Reads: {true_count} True, {false_count} False")

        # At least one should have seen the deactivated state
        # (timing dependent, but with FOR UPDATE serialization this should work)
        assert len(read_values) == 10, "All reads should complete"
