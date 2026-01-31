"""Integration tests for RefreshTokenRepository with real PostgreSQL.

Tests cover:
- Token CRUD operations
- Token revocation
- FOR UPDATE locking
- Bulk revoke operations
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from identity_plan_kit.auth.repositories.token_repo import RefreshTokenRepository


# Skip if testcontainers not available
pytest.importorskip("testcontainers")


class TestTokenRepositoryIntegration:
    """Integration tests for RefreshTokenRepository."""

    async def test_create_token(
        self,
        db_session: AsyncSession,
        create_test_user,
    ):
        """Token can be created in database."""
        user_id = await create_test_user("tokenuser@example.com")
        repo = RefreshTokenRepository(db_session)

        expires_at = datetime.now(UTC) + timedelta(days=30)
        token = await repo.create(
            user_id=user_id,
            token_hash="unique_hash_123",
            expires_at=expires_at,
            user_agent="Test Browser",
            ip_address="1.2.3.4",
        )

        assert token is not None
        assert token.user_id == user_id
        assert token.token_hash == "unique_hash_123"

    async def test_get_by_hash(
        self,
        db_session: AsyncSession,
        create_test_user,
        create_test_refresh_token,
    ):
        """Token can be retrieved by hash."""
        user_id = await create_test_user("hashuser@example.com")
        await create_test_refresh_token(user_id, token_hash="findme_hash")
        repo = RefreshTokenRepository(db_session)

        token = await repo.get_by_hash("findme_hash")

        assert token is not None
        assert token.token_hash == "findme_hash"

    async def test_get_by_hash_with_lock(
        self,
        db_session: AsyncSession,
        create_test_user,
        create_test_refresh_token,
    ):
        """Token can be retrieved with FOR UPDATE lock."""
        user_id = await create_test_user("lockuser@example.com")
        await create_test_refresh_token(user_id, token_hash="lock_hash")
        repo = RefreshTokenRepository(db_session)

        # This tests that the FOR UPDATE clause is valid SQL
        token = await repo.get_by_hash("lock_hash", for_update=True)

        assert token is not None
        assert token.token_hash == "lock_hash"

    async def test_revoke_token(
        self,
        db_session: AsyncSession,
        create_test_user,
        create_test_refresh_token,
    ):
        """Token can be revoked."""
        user_id = await create_test_user("revokeuser@example.com")
        token_id = await create_test_refresh_token(user_id, token_hash="revoke_hash")
        repo = RefreshTokenRepository(db_session)

        # Verify token exists before revoke
        token_before = await repo.get_by_hash("revoke_hash")
        assert token_before is not None

        await repo.revoke(token_id)

        # Verify token is no longer retrievable after revoke
        # (get_by_hash filters out revoked tokens for security)
        token_after = await repo.get_by_hash("revoke_hash")
        assert token_after is None

    async def test_revoke_all_for_user(
        self,
        db_session: AsyncSession,
        create_test_user,
        create_test_refresh_token,
    ):
        """All user tokens can be revoked at once."""
        user_id = await create_test_user("bulkrevokeuser@example.com")

        # Create multiple tokens
        await create_test_refresh_token(user_id, token_hash="bulk_hash_1")
        await create_test_refresh_token(user_id, token_hash="bulk_hash_2")
        await create_test_refresh_token(user_id, token_hash="bulk_hash_3")

        repo = RefreshTokenRepository(db_session)
        count = await repo.revoke_all_for_user(user_id)

        assert count == 3

        # Verify all tokens are no longer retrievable
        # (get_by_hash filters out revoked tokens for security)
        token1 = await repo.get_by_hash("bulk_hash_1")
        token2 = await repo.get_by_hash("bulk_hash_2")
        token3 = await repo.get_by_hash("bulk_hash_3")

        assert token1 is None
        assert token2 is None
        assert token3 is None

    async def test_get_by_hash_not_found(
        self,
        db_session: AsyncSession,
    ):
        """Returns None for non-existent hash."""
        repo = RefreshTokenRepository(db_session)

        token = await repo.get_by_hash("nonexistent_hash")

        assert token is None


class TestTokenExpiration:
    """Test token expiration scenarios."""

    async def test_expired_token_properties(
        self,
        db_session: AsyncSession,
        create_test_user,
        create_test_refresh_token,
    ):
        """Expired token is correctly identified."""
        user_id = await create_test_user("expireduser@example.com")
        await create_test_refresh_token(
            user_id,
            token_hash="expired_hash",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        repo = RefreshTokenRepository(db_session)

        token = await repo.get_by_hash("expired_hash")

        assert token is not None
        assert token.is_expired is True
        assert token.is_valid is False

    async def test_revoked_token_not_retrievable(
        self,
        db_session: AsyncSession,
        create_test_user,
        create_test_refresh_token,
    ):
        """Revoked token is not retrievable via get_by_hash (security feature)."""
        user_id = await create_test_user("revokeduser@example.com")
        await create_test_refresh_token(
            user_id,
            token_hash="revoked_hash",
            revoked=True,
        )
        repo = RefreshTokenRepository(db_session)

        # get_by_hash should return None for revoked tokens
        # This is correct behavior - revoked tokens should not be usable
        token = await repo.get_by_hash("revoked_hash")

        assert token is None
