"""Integration tests for concurrent token operations.

Tests race conditions in:
- Token refresh (concurrent refresh requests with same token)
- Token revocation (concurrent logout/revoke operations)
- Token cleanup (concurrent cleanup batches)

CRITICAL: Token operations must be atomic to prevent:
1. Token reuse by concurrent refresh
2. Incomplete revocation during logout-everywhere
3. Double-spend on token theft detection
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.repositories.token_repo import RefreshTokenRepository
from identity_plan_kit.auth.repositories.user_repo import UserRepository

# Skip if testcontainers not available
pytest.importorskip("testcontainers")


async def create_test_user_with_role(session: AsyncSession, email_suffix: str) -> UUID:
    """Create a test user and return its ID."""
    from identity_plan_kit.rbac.models.role import RoleModel

    role = RoleModel(code=f"user_{email_suffix}", name="User")
    session.add(role)
    await session.flush()

    user = UserModel(
        email=f"token_test_{email_suffix}@example.com",
        role_id=role.id,
        display_name=f"Token Test {email_suffix}",
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    await session.flush()
    return user.id


class TestConcurrentTokenRefresh:
    """Tests for concurrent token refresh scenarios."""

    async def test_concurrent_token_revocation_all_for_user(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        CRITICAL: Concurrent revoke_all_for_user should be safe.

        This tests the scenario where:
        1. Token theft is detected, triggering revoke_all
        2. Meanwhile, user is logging out everywhere
        3. Both should complete without conflict
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create user with multiple tokens
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id = await create_test_user_with_role(setup_session, f"revoke_{id(db_engine)}")

                # Create 20 tokens for the user
                token_repo = RefreshTokenRepository(setup_session)
                for i in range(20):
                    await token_repo.create(
                        user_id=user_id,
                        token_hash=f"token_hash_{i}_{id(db_engine)}",
                        expires_at=datetime.now(UTC) + timedelta(days=30),
                    )

        async def revoke_all() -> int:
            """Attempt to revoke all tokens for user."""
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    return await repo.revoke_all_for_user(user_id)

        # Fire 10 concurrent revoke_all requests
        tasks = [revoke_all() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        counts = [r for r in results if isinstance(r, int)]

        # Sum of all revocations should equal original token count
        # (first request revokes all, others revoke 0)
        total_revoked = sum(counts)
        assert total_revoked == 20, (
            f"Expected 20 total revocations, got {total_revoked}. "
            f"Individual results: {counts}"
        )

        # Exactly one request should have revoked all 20
        assert 20 in counts, "One request should have revoked all 20 tokens"

        # Verify all tokens are now revoked
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(func.count(RefreshTokenModel.id)).where(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.revoked_at.is_(None),
                )
            )
            active_count = result.scalar()

        assert active_count == 0, f"Expected 0 active tokens, found {active_count}"

    async def test_concurrent_single_token_revocation(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent revocation of same single token should be idempotent.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create user with one token
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id = await create_test_user_with_role(setup_session, f"single_{id(db_engine)}")

                token_repo = RefreshTokenRepository(setup_session)
                token = await token_repo.create(
                    user_id=user_id,
                    token_hash=f"single_token_{id(db_engine)}",
                    expires_at=datetime.now(UTC) + timedelta(days=30),
                )
                token_id = token.id

        async def revoke_token() -> bool:
            """Attempt to revoke the token."""
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    await repo.revoke(token_id)
                    return True

        # Fire concurrent revocation requests
        tasks = [revoke_token() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without error (idempotent)
        successes = [r for r in results if r is True]
        assert len(successes) == 10, "All revocations should succeed (idempotent)"

        # Verify token is revoked
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(RefreshTokenModel).where(RefreshTokenModel.id == token_id)
            )
            token = result.scalar_one()

        assert token.revoked_at is not None, "Token should be revoked"

    async def test_concurrent_token_lookup_with_for_update(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Test that get_by_hash with for_update properly serializes access.

        This is critical for preventing double-refresh attacks.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create user with one token
        token_hash = f"lookup_test_{id(db_engine)}"
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id = await create_test_user_with_role(setup_session, f"lookup_{id(db_engine)}")

                token_repo = RefreshTokenRepository(setup_session)
                await token_repo.create(
                    user_id=user_id,
                    token_hash=token_hash,
                    expires_at=datetime.now(UTC) + timedelta(days=30),
                )

        access_times: list[tuple[int, float]] = []
        access_lock = asyncio.Lock()

        async def lookup_with_lock(request_num: int) -> bool:
            """Lookup token with FOR UPDATE lock."""
            start = asyncio.get_event_loop().time()
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    token = await repo.get_by_hash(token_hash, for_update=True)

                    # Simulate some processing time while holding lock
                    await asyncio.sleep(0.1)

                    end = asyncio.get_event_loop().time()
                    async with access_lock:
                        access_times.append((request_num, end - start))

                    return token is not None

        # Fire concurrent lookups
        tasks = [lookup_with_lock(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if r is True]
        assert len(successes) == 5, "All lookups should succeed"

        # With proper FOR UPDATE locking, requests should be serialized
        # Total execution time should be roughly 5 * 0.1s if properly serialized
        # (This is a timing-based heuristic, not a strict assertion)
        durations = [t[1] for t in access_times]
        avg_duration = sum(durations) / len(durations)

        # At least some requests should have waited (duration > 0.1s)
        waited_count = len([d for d in durations if d > 0.15])
        assert waited_count >= 1, (
            f"Expected at least 1 request to wait for lock. "
            f"Durations: {durations}"
        )


class TestConcurrentTokenCleanup:
    """Tests for concurrent token cleanup operations."""

    async def test_concurrent_cleanup_expired_tokens(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent cleanup operations should not conflict or miss tokens.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create user with expired tokens
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id = await create_test_user_with_role(setup_session, f"cleanup_{id(db_engine)}")

                # Create 100 expired tokens
                for i in range(100):
                    token = RefreshTokenModel(
                        user_id=user_id,
                        token_hash=f"expired_token_{i}_{id(db_engine)}",
                        expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
                    )
                    setup_session.add(token)
                await setup_session.flush()

        async def cleanup_batch() -> int:
            """Run cleanup batch."""
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    return await repo.cleanup_expired(batch_size=20)

        # Fire concurrent cleanup batches
        tasks = [cleanup_batch() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        counts = [r for r in results if isinstance(r, int)]

        # Total cleaned should be at least 100 (our test tokens)
        # May be more if there are leftover tokens from other tests
        total_cleaned = sum(counts)
        assert total_cleaned >= 100, (
            f"Expected at least 100 tokens cleaned, got {total_cleaned}. "
            f"Individual results: {counts}"
        )

        # Verify all tokens are gone
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(func.count(RefreshTokenModel.id)).where(
                    RefreshTokenModel.user_id == user_id
                )
            )
            remaining = result.scalar()

        assert remaining == 0, f"Expected 0 tokens remaining, found {remaining}"


class TestTokenCreationRaceCondition:
    """Tests for concurrent token creation scenarios."""

    async def test_concurrent_token_creation_unique_hashes(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Concurrent token creation should never produce duplicate hashes.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id = await create_test_user_with_role(setup_session, f"create_{id(db_engine)}")

        created_hashes: list[str] = []
        hash_lock = asyncio.Lock()

        async def create_token(token_num: int) -> str:
            """Create a token and return its hash."""
            # Use unique hash to avoid conflicts
            token_hash = f"unique_hash_{token_num}_{id(db_engine)}_{asyncio.get_event_loop().time()}"
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    await repo.create(
                        user_id=user_id,
                        token_hash=token_hash,
                        expires_at=datetime.now(UTC) + timedelta(days=30),
                    )
                    async with hash_lock:
                        created_hashes.append(token_hash)
                    return token_hash

        # Fire concurrent token creations
        tasks = [create_token(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = [r for r in results if isinstance(r, str)]

        # All should succeed with unique hashes
        assert len(successes) == 50, f"Expected 50 successes, got {len(successes)}"
        assert len(set(successes)) == 50, "All hashes should be unique"

        # Verify all tokens exist in DB
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(func.count(RefreshTokenModel.id)).where(
                    RefreshTokenModel.user_id == user_id
                )
            )
            count = result.scalar()

        assert count == 50, f"Expected 50 tokens in DB, found {count}"


class TestTokenRevocationAndLookupRace:
    """Tests for race between token lookup and revocation."""

    async def test_lookup_during_revoke_all(
        self,
        db_engine: AsyncEngine,
    ) -> None:
        """
        Token lookup should properly handle concurrent revocation.

        Scenario: User refreshes token while logout-everywhere is happening.
        """
        session_factory = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        token_hash = f"race_token_{id(db_engine)}"
        async with session_factory() as setup_session:
            async with setup_session.begin():
                user_id = await create_test_user_with_role(setup_session, f"race_{id(db_engine)}")

                # Create token to be looked up
                token_repo = RefreshTokenRepository(setup_session)
                await token_repo.create(
                    user_id=user_id,
                    token_hash=token_hash,
                    expires_at=datetime.now(UTC) + timedelta(days=30),
                )

                # Create other tokens to be revoked
                for i in range(10):
                    await token_repo.create(
                        user_id=user_id,
                        token_hash=f"other_{i}_{id(db_engine)}",
                        expires_at=datetime.now(UTC) + timedelta(days=30),
                    )

        lookup_results: list[bool] = []
        revoke_results: list[int] = []
        results_lock = asyncio.Lock()

        async def lookup_token() -> None:
            """Lookup the specific token."""
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    # Small delay to interleave with revocation
                    await asyncio.sleep(0.01)
                    token = await repo.get_by_hash(token_hash, for_update=True)
                    async with results_lock:
                        lookup_results.append(token is not None and token.revoked_at is None)

        async def revoke_all() -> None:
            """Revoke all tokens for user."""
            async with session_factory() as session:
                async with session.begin():
                    repo = RefreshTokenRepository(session)
                    count = await repo.revoke_all_for_user(user_id)
                    async with results_lock:
                        revoke_results.append(count)

        # Fire concurrent operations
        tasks = [
            lookup_token(),
            lookup_token(),
            revoke_all(),
            lookup_token(),
            lookup_token(),
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        # After completion, all lookups should consistently see revoked state
        # (either found as active before revocation, or found as revoked/not found after)

        # The key invariant: once revoke_all completes, no subsequent lookup
        # should find an active token
        async with session_factory() as verify_session:
            result = await verify_session.execute(
                select(func.count(RefreshTokenModel.id)).where(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.revoked_at.is_(None),
                )
            )
            active_count = result.scalar()

        assert active_count == 0, (
            f"After revoke_all, expected 0 active tokens, found {active_count}"
        )
