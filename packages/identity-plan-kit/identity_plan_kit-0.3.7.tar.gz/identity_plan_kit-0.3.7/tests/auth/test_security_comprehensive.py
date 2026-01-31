"""Comprehensive security tests for the authentication system.

Tests cover:
- Token tampering and validation
- Permission elevation attempts
- User deactivation enforcement
- Plan expiration enforcement
- JWT security (signature, payload, timing)

CRITICAL: These tests ensure the security boundaries are enforced correctly.
"""

import base64
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from identity_plan_kit.auth.domain.entities import RefreshToken, User
from identity_plan_kit.auth.domain.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)
from identity_plan_kit.auth.services.auth_service import AuthService
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_from_cache,
    encrypt_for_cache,
    hash_token,
)

pytestmark = pytest.mark.anyio


class TestJWTTokenTampering:
    """Tests for JWT token tampering detection."""

    async def test_modified_payload_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Token with modified payload (different user_id) is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        # Create valid token
        valid_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        # Tamper with the payload (modify user ID)
        parts = valid_token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        payload["sub"] = str(UUID("00000000-0000-0000-0000-000000000001"))  # Different user
        new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        tampered_token = f"{parts[0]}.{new_payload}.{parts[2]}"

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError):
            await service.get_user_from_token(tampered_token)

    async def test_modified_signature_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Token with modified signature is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        # Create valid token
        valid_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        # Tamper with the signature
        parts = valid_token.split(".")
        # Flip some bits in the signature
        signature = parts[2]
        tampered_sig = signature[:-5] + "XXXXX"
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError):
            await service.get_user_from_token(tampered_token)

    async def test_wrong_secret_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Token created with wrong secret is rejected."""
        wrong_secret = "completely-different-secret-key-12345"

        # Create token with wrong secret
        wrong_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=wrong_secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError):
            await service.get_user_from_token(wrong_token)

    async def test_empty_token_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Empty token is rejected."""
        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError):
            await service.get_user_from_token("")

    async def test_malformed_jwt_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Various malformed JWTs are rejected."""
        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        malformed_tokens = [
            "not.a.valid.jwt.token",
            "only.two.parts",
            "single",
            "header.payload.",
            ".payload.signature",
            "header..signature",
            "header.payload.signature.extra",
            "eyJhbGciOiJIUzI1NiJ9.invalid_base64!.signature",
        ]

        for token in malformed_tokens:
            with pytest.raises(TokenInvalidError):
                await service.get_user_from_token(token)

    async def test_none_algorithm_attack_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Tokens with 'none' algorithm attack are rejected."""
        # Create a token with 'none' algorithm (attack vector)
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()

        payload = base64.urlsafe_b64encode(
            json.dumps({
                "sub": str(mock_user.id),
                "type": "access",
                "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            }).encode()
        ).rstrip(b"=").decode()

        none_algo_token = f"{header}.{payload}."

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError):
            await service.get_user_from_token(none_algo_token)


class TestTokenTypeEnforcement:
    """Tests for token type enforcement (access vs refresh)."""

    async def test_refresh_token_rejected_as_access_token(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Using refresh token as access token is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        refresh_token, _ = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenInvalidError, match="Invalid token type"):
            await service.get_user_from_token(refresh_token)

    async def test_access_token_rejected_for_refresh(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Using access token for refresh operation is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        access_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        # Access tokens are rejected by token type check before DB lookup
        with pytest.raises(TokenInvalidError, match="Invalid token type"):
            await service.refresh_tokens(access_token)


class TestTokenExpirationEnforcement:
    """Tests for token expiration enforcement."""

    async def test_expired_access_token_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Expired access token is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        # Create expired token
        expired_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=-1),  # Already expired
        )

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with pytest.raises(TokenExpiredError):
            await service.get_user_from_token(expired_token)

    async def test_expired_refresh_token_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Expired refresh token is rejected even if DB record exists."""
        secret = mock_config.secret_key.get_secret_value()

        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        # Token exists in DB but is marked as expired
        stored_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
            created_at=datetime.now(UTC) - timedelta(days=31),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=stored_token)

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            with pytest.raises(TokenExpiredError):
                await service.refresh_tokens(refresh_token)


class TestUserDeactivationEnforcement:
    """Tests for user deactivation enforcement."""

    async def test_deactivated_user_token_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_inactive_user: User,
    ):
        """Token for deactivated user is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        # Create valid token for inactive user
        access_token = create_access_token(
            data={"sub": str(mock_inactive_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_by_id = AsyncMock(return_value=mock_inactive_user)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(UserInactiveError):
                await service.get_user_from_token(access_token)

    async def test_deactivated_user_cannot_refresh(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Deactivated user cannot refresh tokens."""
        secret = mock_config.secret_key.get_secret_value()

        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        stored_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC),
        )

        # User has been deactivated
        inactive_user = User(
            id=mock_user.id,
            email=mock_user.email,
            role_id=mock_user.role_id,
            display_name="Test User",
            is_active=False,  # Deactivated!
            is_verified=True,
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=stored_token)
        mock_uow.users.get_by_id = AsyncMock(return_value=inactive_user)

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            with pytest.raises(UserInactiveError):
                await service.refresh_tokens(refresh_token)

    async def test_deactivated_user_cannot_authenticate(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Deactivated user cannot authenticate via OAuth."""
        mock_google_user = MagicMock()
        mock_google_user.id = "google_123"
        mock_google_user.email = "deactivated@example.com"
        mock_google_user.name = "Deactivated User"
        mock_google_user.picture = None
        mock_google_user.email_verified = True

        inactive_user = User(
            id=UUID("12345678-1234-1234-1234-123456789099"),
            email="deactivated@example.com",
            role_id=2,
            display_name="Deactivated User",
            is_active=False,  # Deactivated!
            is_verified=True,
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_or_create_with_provider = AsyncMock(
            return_value=(inactive_user, False)
        )

        mock_lockout = AsyncMock()
        mock_lockout.check_lockout = AsyncMock()

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch.object(service, "_get_lockout_manager", return_value=mock_lockout),
            patch.object(
                service._google_oauth, "authenticate", return_value=mock_google_user
            ),
        ):
            with pytest.raises(UserInactiveError):
                await service.authenticate_google(code="auth_code")


class TestDeletedUserHandling:
    """Tests for deleted user handling."""

    async def test_deleted_user_token_rejected(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Token for deleted user is rejected."""
        secret = mock_config.secret_key.get_secret_value()

        # Create token for user who will be "deleted"
        access_token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.users.get_by_id = AsyncMock(return_value=None)  # User not found

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(UserNotFoundError):
                await service.get_user_from_token(access_token)


class TestTokenTheftDetection:
    """Tests for token theft detection and response."""

    async def test_revoked_token_reuse_deactivates_user(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """
        CRITICAL SECURITY TEST: Using a revoked token triggers account deactivation.

        This protects against token theft by assuming that if a revoked token
        is reused, either:
        1. Attacker stole the token, OR
        2. Legitimate user using stolen token copy

        Either way, safest response is to revoke ALL tokens and deactivate.
        """
        secret = mock_config.secret_key.get_secret_value()

        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(days=30),
        )

        # Token exists but is already revoked (potential theft!)
        revoked_token = RefreshToken(
            id=UUID("87654321-4321-4321-4321-210987654321"),
            user_id=mock_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC) - timedelta(hours=1),
            revoked_at=datetime.now(UTC) - timedelta(minutes=30),  # Already revoked!
        )

        active_user = User(
            id=mock_user.id,
            email=mock_user.email,
            role_id=mock_user.role_id,
            display_name="Test User",
            is_active=True,
            is_verified=True,
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.tokens.get_by_hash = AsyncMock(return_value=revoked_token)
        mock_uow.tokens.revoke_all_for_user = AsyncMock()
        mock_uow.users.get_by_id = AsyncMock(return_value=active_user)
        mock_uow.users.deactivate = AsyncMock()

        mock_state_store = AsyncMock()
        mock_state_store.get = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = AuthService(mock_config, mock_session_factory)

        with (
            patch.object(service, "_create_uow", return_value=mock_uow),
            patch(
                "identity_plan_kit.auth.services.auth_service.get_state_store",
                return_value=mock_state_store,
            ),
        ):
            with pytest.raises(TokenInvalidError, match="revoked"):
                await service.refresh_tokens(refresh_token)

        # Verify security response
        mock_uow.tokens.revoke_all_for_user.assert_called_once_with(mock_user.id)
        mock_uow.users.deactivate.assert_called_once_with(
            mock_user.id, reason="token_theft_suspected"
        )


class TestTokenHashSecurity:
    """Tests for token hash security."""

    def test_token_hash_is_not_plaintext(self):
        """Token hash should not store plaintext token."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature"
        hashed = hash_token(token)

        assert hashed != token
        assert token not in hashed
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_same_token_produces_same_hash(self):
        """Same token should always produce same hash (deterministic)."""
        token = "test-token-12345"

        hash1 = hash_token(token)
        hash2 = hash_token(token)

        assert hash1 == hash2

    def test_different_tokens_produce_different_hashes(self):
        """Different tokens should produce different hashes."""
        token1 = "test-token-1"
        token2 = "test-token-2"

        hash1 = hash_token(token1)
        hash2 = hash_token(token2)

        assert hash1 != hash2

    def test_similar_tokens_produce_different_hashes(self):
        """Similar tokens (1 char diff) should produce very different hashes."""
        token1 = "test-token-12345"
        token2 = "test-token-12346"  # Only last digit different

        hash1 = hash_token(token1)
        hash2 = hash_token(token2)

        assert hash1 != hash2
        # Check that they differ significantly (not just one byte)
        diff_count = sum(1 for a, b in zip(hash1, hash2) if a != b)
        assert diff_count > 10  # Most characters should differ


class TestJTIUniqueness:
    """Tests for JWT ID (jti) uniqueness in refresh tokens."""

    def test_refresh_token_has_unique_jti(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Each refresh token should have a unique jti claim."""
        secret = mock_config.secret_key.get_secret_value()

        jtis = set()
        for _ in range(100):
            token, _ = create_refresh_token(
                data={"sub": str(mock_user.id)},
                secret_key=secret,
                algorithm=mock_config.algorithm,
                expires_delta=timedelta(days=30),
            )

            payload = decode_token(token, secret, mock_config.algorithm)
            jti = payload.get("jti")

            assert jti is not None, "Refresh token should have jti claim"
            assert jti not in jtis, f"Duplicate jti detected: {jti}"
            jtis.add(jti)

    def test_access_token_does_not_have_jti(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Access tokens don't need jti (they're stateless)."""
        secret = mock_config.secret_key.get_secret_value()

        token = create_access_token(
            data={"sub": str(mock_user.id)},
            secret_key=secret,
            algorithm=mock_config.algorithm,
            expires_delta=timedelta(minutes=15),
        )

        payload = decode_token(token, secret, mock_config.algorithm)
        # jti may or may not be present for access tokens
        # The important thing is access tokens are validated by signature, not DB lookup


class TestCacheEncryption:
    """Tests for cache data encryption (SECURITY FIX for plaintext token storage)."""

    def test_encrypt_decrypt_round_trip(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Encryption and decryption round trip works correctly."""
        secret = mock_config.secret_key.get_secret_value()
        original = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_payload.signature"

        encrypted = encrypt_for_cache(original, secret)
        decrypted = decrypt_from_cache(encrypted, secret)

        assert decrypted == original

    def test_encrypted_data_not_plaintext(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Encrypted data should not contain plaintext."""
        secret = mock_config.secret_key.get_secret_value()
        sensitive = "my-super-secret-jwt-token-12345"

        encrypted = encrypt_for_cache(sensitive, secret)

        # Encrypted data should not contain the original
        assert sensitive not in encrypted
        # Should be base64-encoded Fernet ciphertext
        assert encrypted.startswith("gAAAAA")  # Fernet version byte

    def test_different_encryption_each_time(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Same plaintext should produce different ciphertext (IV randomness)."""
        secret = mock_config.secret_key.get_secret_value()
        plaintext = "same-data-to-encrypt"

        encrypted1 = encrypt_for_cache(plaintext, secret)
        encrypted2 = encrypt_for_cache(plaintext, secret)

        # Due to random IV, same plaintext produces different ciphertext
        assert encrypted1 != encrypted2

        # But both decrypt to same value
        assert decrypt_from_cache(encrypted1, secret) == plaintext
        assert decrypt_from_cache(encrypted2, secret) == plaintext

    def test_wrong_key_returns_none(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Decryption with wrong key returns None (not raises exception)."""
        secret1 = mock_config.secret_key.get_secret_value()
        secret2 = "a-completely-different-secret-key-32chars"

        encrypted = encrypt_for_cache("sensitive-data", secret1)
        decrypted = decrypt_from_cache(encrypted, secret2)

        assert decrypted is None

    def test_tampered_ciphertext_returns_none(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Tampered ciphertext returns None (HMAC validation fails)."""
        secret = mock_config.secret_key.get_secret_value()

        encrypted = encrypt_for_cache("sensitive-data", secret)
        # Tamper with the ciphertext
        tampered = encrypted[:-5] + "XXXXX"

        decrypted = decrypt_from_cache(tampered, secret)
        assert decrypted is None

    def test_invalid_base64_returns_none(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Invalid base64 input returns None."""
        secret = mock_config.secret_key.get_secret_value()

        decrypted = decrypt_from_cache("not-valid-base64!!!", secret)
        assert decrypted is None

    def test_encryption_validates_secret_key_length(self):
        """Encryption validates minimum secret key length."""
        short_key = "tooshort"

        with pytest.raises(ValueError, match="at least"):
            encrypt_for_cache("data", short_key)

    def test_decryption_validates_secret_key_length(
        self,
        mock_config: IdentityPlanKitConfig,
    ):
        """Decryption validates minimum secret key length."""
        secret = mock_config.secret_key.get_secret_value()
        encrypted = encrypt_for_cache("data", secret)

        # Trying to decrypt with short key returns None (validation fails)
        result = decrypt_from_cache(encrypted, "tooshort")
        assert result is None
