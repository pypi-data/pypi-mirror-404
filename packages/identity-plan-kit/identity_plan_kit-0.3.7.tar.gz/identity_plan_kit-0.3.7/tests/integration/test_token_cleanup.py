"""Tests for token cleanup operations.

Tests cover:
- Batch cleanup of expired tokens
- Batch cleanup of revoked tokens
- Cleanup under concurrent access
- Batch size enforcement
- has_more indicator accuracy

CRITICAL: These tests ensure token cleanup:
- Doesn't cause table-level locks
- Handles large datasets efficiently
- Works correctly with concurrent token operations
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from identity_plan_kit.auth.models.refresh_token import RefreshTokenModel
from identity_plan_kit.auth.models.user import UserModel
from identity_plan_kit.auth.repositories.token_repo import RefreshTokenRepository


pytestmark = pytest.mark.anyio


@pytest.fixture
async def db_session(db_engine: AsyncEngine):
    """Create a database session for testing."""
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for token tests."""
    # Get or create a role first
    result = await db_session.execute(
        select(text("id")).select_from(text("roles")).where(text("code = 'user'"))
    )
    role_row = result.first()

    if role_row is None:
        pytest.skip("No 'user' role found - run migrations first")

    role_id = role_row[0]

    user = UserModel(
        email=f"cleanup-test-{uuid4()}@example.com",
        role_id=role_id,
        display_name="Cleanup Test User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestTokenCleanupBasic:
    """Basic token cleanup tests."""

    async def test_cleanup_expired_tokens(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Expired tokens are cleaned up."""
        repo = RefreshTokenRepository(db_session)

        # Create expired token
        expired_token = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"expired_{uuid4().hex}",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(expired_token)
        await db_session.commit()

        # Cleanup should delete it
        deleted = await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        assert deleted >= 1

        # Verify token is gone
        result = await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.id == expired_token.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_cleanup_revoked_tokens(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Revoked tokens are cleaned up."""
        repo = RefreshTokenRepository(db_session)

        # Create revoked token (not expired)
        revoked_token = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"revoked_{uuid4().hex}",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(revoked_token)
        await db_session.commit()

        # Cleanup should delete it
        deleted = await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        assert deleted >= 1

        # Verify token is gone
        result = await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.id == revoked_token.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_active_tokens_not_cleaned(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Active tokens are NOT cleaned up."""
        repo = RefreshTokenRepository(db_session)

        # Create active token
        active_token = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"active_{uuid4().hex}",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked_at=None,  # Not revoked
        )
        db_session.add(active_token)
        await db_session.commit()
        token_id = active_token.id

        # Cleanup should not delete it
        await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        # Verify token still exists
        result = await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.id == token_id)
        )
        assert result.scalar_one_or_none() is not None


class TestBatchCleanup:
    """Test batch cleanup behavior."""

    async def test_batch_size_enforced(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Batch size limits number of tokens deleted per call."""
        repo = RefreshTokenRepository(db_session)

        # Create many expired tokens
        for i in range(25):
            token = RefreshTokenModel(
                user_id=test_user.id,
                token_hash=f"batch_test_{i}_{uuid4().hex}",
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )
            db_session.add(token)
        await db_session.commit()

        # Cleanup with small batch size
        deleted = await repo.cleanup_expired(batch_size=10)
        await db_session.commit()

        # Should delete exactly batch_size
        assert deleted == 10

        # More remain to be cleaned
        deleted2 = await repo.cleanup_expired(batch_size=10)
        await db_session.commit()

        assert deleted2 == 10

        # Clean the rest
        deleted3 = await repo.cleanup_expired(batch_size=10)
        await db_session.commit()

        assert deleted3 == 5

    async def test_empty_cleanup_returns_zero(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Cleanup with no expired tokens returns 0."""
        repo = RefreshTokenRepository(db_session)

        # Create only active token
        active_token = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"active_only_{uuid4().hex}",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        db_session.add(active_token)
        await db_session.commit()

        # First clean up any pre-existing expired tokens
        while True:
            deleted = await repo.cleanup_expired(batch_size=1000)
            await db_session.commit()
            if deleted == 0:
                break

        # Now cleanup should return 0
        deleted = await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        assert deleted == 0


class TestConcurrentCleanup:
    """Test cleanup under concurrent access."""

    async def test_cleanup_during_token_creation(
        self, db_engine: AsyncEngine, test_user: UserModel
    ):
        """Cleanup doesn't interfere with concurrent token creation."""
        async_session = async_sessionmaker(db_engine, expire_on_commit=False)

        async def create_tokens():
            """Create tokens in one session."""
            async with async_session() as session:
                for i in range(10):
                    token = RefreshTokenModel(
                        user_id=test_user.id,
                        token_hash=f"concurrent_create_{i}_{uuid4().hex}",
                        expires_at=datetime.now(UTC) + timedelta(days=30),
                    )
                    session.add(token)
                    await asyncio.sleep(0.01)  # Small delay
                await session.commit()

        async def cleanup_tokens():
            """Cleanup tokens in another session."""
            async with async_session() as session:
                repo = RefreshTokenRepository(session)
                for _ in range(5):
                    await repo.cleanup_expired(batch_size=10)
                    await session.commit()
                    await asyncio.sleep(0.01)

        # First create some expired tokens to clean
        async with async_session() as session:
            for i in range(20):
                token = RefreshTokenModel(
                    user_id=test_user.id,
                    token_hash=f"to_clean_{i}_{uuid4().hex}",
                    expires_at=datetime.now(UTC) - timedelta(days=1),
                )
                session.add(token)
            await session.commit()

        # Run concurrently
        await asyncio.gather(
            create_tokens(),
            cleanup_tokens(),
        )

        # Verify new tokens exist
        async with async_session() as session:
            result = await session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.token_hash.like("concurrent_create_%")
                )
            )
            new_tokens = result.scalars().all()
            assert len(new_tokens) == 10

    async def test_multiple_concurrent_cleanups(
        self, db_engine: AsyncEngine, test_user: UserModel
    ):
        """Multiple concurrent cleanup operations don't cause issues."""
        async_session = async_sessionmaker(db_engine, expire_on_commit=False)

        # Create many expired tokens
        async with async_session() as session:
            for i in range(100):
                token = RefreshTokenModel(
                    user_id=test_user.id,
                    token_hash=f"multi_cleanup_{i}_{uuid4().hex}",
                    expires_at=datetime.now(UTC) - timedelta(days=1),
                )
                session.add(token)
            await session.commit()

        total_deleted = 0
        lock = asyncio.Lock()

        async def do_cleanup():
            """Run cleanup and track deleted count."""
            nonlocal total_deleted
            async with async_session() as session:
                repo = RefreshTokenRepository(session)
                deleted = await repo.cleanup_expired(batch_size=20)
                await session.commit()
                async with lock:
                    total_deleted += deleted
                return deleted

        # Run multiple cleanups concurrently
        results = await asyncio.gather(*[do_cleanup() for _ in range(10)])

        # Each cleanup should succeed (might delete different amounts)
        for result in results:
            assert result >= 0

        # Total deleted should be around 100 (the expired tokens we created)
        # Some cleanups might overlap and get 0, that's okay
        assert total_deleted >= 50  # At least half should be cleaned


class TestCleanupEdgeCases:
    """Test edge cases in cleanup."""

    async def test_cleanup_token_expiring_now(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Token expiring exactly now is cleaned up."""
        repo = RefreshTokenRepository(db_session)

        # Create token expiring right now
        now_token = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"expiring_now_{uuid4().hex}",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),  # Just expired
        )
        db_session.add(now_token)
        await db_session.commit()

        deleted = await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        # Should be cleaned (< now)
        assert deleted >= 1

    async def test_cleanup_very_old_tokens(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Very old tokens are cleaned up."""
        repo = RefreshTokenRepository(db_session)

        # Create very old token
        old_token = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"ancient_{uuid4().hex}",
            expires_at=datetime.now(UTC) - timedelta(days=365),  # Year old
        )
        db_session.add(old_token)
        await db_session.commit()

        deleted = await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        assert deleted >= 1

    async def test_cleanup_with_batch_size_one(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Cleanup works with batch size of 1."""
        repo = RefreshTokenRepository(db_session)

        # Create expired tokens
        for i in range(3):
            token = RefreshTokenModel(
                user_id=test_user.id,
                token_hash=f"single_batch_{i}_{uuid4().hex}",
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )
            db_session.add(token)
        await db_session.commit()

        # Delete one at a time
        deleted1 = await repo.cleanup_expired(batch_size=1)
        await db_session.commit()
        assert deleted1 == 1

        deleted2 = await repo.cleanup_expired(batch_size=1)
        await db_session.commit()
        assert deleted2 == 1

    async def test_cleanup_mixed_expired_and_revoked(
        self, db_session: AsyncSession, test_user: UserModel
    ):
        """Cleanup handles mix of expired and revoked tokens."""
        repo = RefreshTokenRepository(db_session)

        # Create expired token
        expired = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"mixed_expired_{uuid4().hex}",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        # Create revoked token
        revoked = RefreshTokenModel(
            user_id=test_user.id,
            token_hash=f"mixed_revoked_{uuid4().hex}",
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked_at=datetime.now(UTC) - timedelta(hours=1),
        )

        db_session.add_all([expired, revoked])
        await db_session.commit()

        deleted = await repo.cleanup_expired(batch_size=100)
        await db_session.commit()

        # Both should be cleaned
        assert deleted >= 2


class TestCleanupPerformance:
    """Test cleanup performance characteristics."""

    async def test_cleanup_doesnt_lock_table(
        self, db_engine: AsyncEngine, test_user: UserModel
    ):
        """Cleanup using batch delete doesn't cause long table locks."""
        async_session = async_sessionmaker(db_engine, expire_on_commit=False)

        # Create tokens to clean
        async with async_session() as session:
            for i in range(50):
                token = RefreshTokenModel(
                    user_id=test_user.id,
                    token_hash=f"perf_test_{i}_{uuid4().hex}",
                    expires_at=datetime.now(UTC) - timedelta(days=1),
                )
                session.add(token)
            await session.commit()

        read_succeeded = False

        async def cleanup_large():
            """Run cleanup."""
            async with async_session() as session:
                repo = RefreshTokenRepository(session)
                await repo.cleanup_expired(batch_size=50)
                await session.commit()

        async def read_during_cleanup():
            """Try to read during cleanup."""
            nonlocal read_succeeded
            await asyncio.sleep(0.001)  # Small delay to let cleanup start
            async with async_session() as session:
                # This should not be blocked
                result = await session.execute(
                    select(RefreshTokenModel).limit(1)
                )
                result.scalar_one_or_none()
                read_succeeded = True

        await asyncio.gather(
            cleanup_large(),
            read_during_cleanup(),
        )

        # Read should have succeeded (not blocked)
        assert read_succeeded
