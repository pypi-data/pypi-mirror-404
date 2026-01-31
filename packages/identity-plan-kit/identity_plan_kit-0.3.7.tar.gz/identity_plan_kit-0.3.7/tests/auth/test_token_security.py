"""Tests for token security (P1 fixes)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from identity_plan_kit.shared.security import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_token_hash,
)


class TestTokenCreation:
    """Test suite for token creation functions."""

    def test_create_access_token(self):
        """Test access token creation with required claims."""
        data = {"sub": "user-123"}
        token = create_access_token(
            data=data,
            secret_key="test-secret-key-32-characters-long",
            algorithm="HS256",
            expires_delta=timedelta(minutes=15),
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify claims
        payload = decode_token(
            token,
            secret_key="test-secret-key-32-characters-long",
            algorithm="HS256",
        )
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_returns_token_and_hash(self):
        """Test refresh token creation returns both token and hash."""
        data = {"sub": "user-123"}
        token, token_hash = create_refresh_token(
            data=data,
            secret_key="test-secret-key-32-characters-long",
            algorithm="HS256",
            expires_delta=timedelta(days=30),
        )

        assert isinstance(token, str)
        assert isinstance(token_hash, str)
        assert len(token_hash) == 64  # SHA-256 hex digest

        # Verify hash matches token
        assert verify_token_hash(token, token_hash)

    def test_refresh_token_has_jti(self):
        """Test refresh token includes unique JWT ID."""
        data = {"sub": "user-123"}
        token, _ = create_refresh_token(
            data=data,
            secret_key="test-secret-key-32-characters-long",
        )

        payload = decode_token(
            token,
            secret_key="test-secret-key-32-characters-long",
            verify_exp=False,
        )
        assert "jti" in payload
        assert payload["type"] == "refresh"


class TestTokenDecoding:
    """Test suite for token decoding and validation."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        secret = "test-secret-key-32-characters-long"
        token = create_access_token(
            data={"sub": "user-123"},
            secret_key=secret,
            expires_delta=timedelta(minutes=15),
        )

        payload = decode_token(token, secret_key=secret)

        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_decode_expired_token_raises(self):
        """Test that expired token raises TokenExpiredError."""
        secret = "test-secret-key-32-characters-long"
        token = create_access_token(
            data={"sub": "user-123"},
            secret_key=secret,
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(TokenExpiredError):
            decode_token(token, secret_key=secret)

    def test_decode_expired_token_with_verify_false(self):
        """Test expired token can be decoded when verify_exp=False."""
        secret = "test-secret-key-32-characters-long"
        token = create_access_token(
            data={"sub": "user-123"},
            secret_key=secret,
            expires_delta=timedelta(seconds=-1),
        )

        # Should not raise with verify_exp=False
        payload = decode_token(token, secret_key=secret, verify_exp=False)
        assert payload["sub"] == "user-123"

    def test_decode_invalid_token_raises(self):
        """Test that invalid token raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            decode_token(
                "invalid.token.here",
                secret_key="test-secret-key-32-characters-long",
            )

    def test_decode_wrong_secret_raises(self):
        """Test that wrong secret raises TokenInvalidError."""
        token = create_access_token(
            data={"sub": "user-123"},
            secret_key="correct-secret-key-32-characters",
            expires_delta=timedelta(minutes=15),
        )

        with pytest.raises(TokenInvalidError):
            decode_token(
                token,
                secret_key="wrong-secret-key-32-characters-!",
            )


class TestTokenHashing:
    """Test suite for token hashing functions."""

    def test_hash_token_deterministic(self):
        """Test that same token always produces same hash."""
        token = "test-token-value"

        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2

    def test_different_tokens_different_hashes(self):
        """Test that different tokens produce different hashes."""
        token1 = "test-token-1"
        token2 = "test-token-2"

        hash1 = hash_token(token1)
        hash2 = hash_token(token2)

        assert hash1 != hash2

    def test_verify_token_hash_correct(self):
        """Test hash verification with correct token."""
        token = "test-token-value"
        token_hash = hash_token(token)

        assert verify_token_hash(token, token_hash) is True

    def test_verify_token_hash_incorrect(self):
        """Test hash verification with incorrect token."""
        token = "test-token-value"
        token_hash = hash_token(token)

        assert verify_token_hash("wrong-token", token_hash) is False

    def test_hash_is_sha256(self):
        """Test that hash is SHA-256 (64 hex chars)."""
        token = "test-token-value"
        token_hash = hash_token(token)

        assert len(token_hash) == 64
        assert all(c in "0123456789abcdef" for c in token_hash)
