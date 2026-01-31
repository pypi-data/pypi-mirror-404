"""Security utilities for token generation and verification."""

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Password hashing context (for future password auth support)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """Base exception for token errors."""

    pass


class TokenExpiredError(TokenError):
    """Token has expired."""

    pass


class TokenInvalidError(TokenError):
    """Token is invalid or malformed."""

    pass


# Minimum secret key length for security
MIN_SECRET_KEY_LENGTH = 32


def _validate_secret_key(secret_key: str) -> None:
    """
    Validate that secret key meets minimum security requirements.

    Args:
        secret_key: The secret key to validate

    Raises:
        ValueError: If secret key is too short
    """
    if len(secret_key) < MIN_SECRET_KEY_LENGTH:
        raise ValueError(
            f"Secret key must be at least {MIN_SECRET_KEY_LENGTH} characters. "
            f"Got {len(secret_key)} characters."
        )


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Claims to encode in the token
        secret_key: Secret key for signing (minimum 32 characters)
        algorithm: JWT algorithm (default: HS256)
        expires_delta: Token expiration time

    Returns:
        Encoded JWT string

    Raises:
        ValueError: If secret key is too short

    Example:
        >>> token = create_access_token(
        ...     {"sub": "user-id", "type": "access"},
        ...     secret_key="...",
        ...     expires_delta=timedelta(minutes=15)
        ... )
    """
    _validate_secret_key(secret_key)
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=15))
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "access",
        }
    )
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Create a refresh token pair (token + hash for storage).

    The actual token is returned to the client, while only the hash
    is stored in the database for security.

    Args:
        data: Claims to encode in the token
        secret_key: Secret key for signing (minimum 32 characters)
        algorithm: JWT algorithm
        expires_delta: Token expiration time

    Returns:
        Tuple of (token, token_hash)

    Raises:
        ValueError: If secret key is too short

    Example:
        >>> token, token_hash = create_refresh_token(
        ...     {"sub": "user-id"},
        ...     secret_key="...",
        ...     expires_delta=timedelta(days=30)
        ... )
        >>> # Store token_hash in database
        >>> # Return token to client
    """
    _validate_secret_key(secret_key)
    # Generate a random token ID for uniqueness
    token_id = secrets.token_urlsafe(32)

    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=30))
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": token_id,
            "type": "refresh",
        }
    )

    token = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    token_hash = hash_token(token)

    return token, token_hash


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
    verify_exp: bool = True,
) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string
        secret_key: Secret key for verification (minimum 32 characters)
        algorithm: JWT algorithm
        verify_exp: Whether to verify expiration

    Returns:
        Decoded token claims

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
        ValueError: If secret key is too short

    Example:
        >>> claims = decode_token(token, secret_key)
        >>> user_id = claims["sub"]
    """
    _validate_secret_key(secret_key)
    try:
        options = {"verify_exp": verify_exp}
        return jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options=options,
        )
    except jwt.ExpiredSignatureError as e:
        # SECURITY FIX: Don't log any part of the token content
        logger.debug("token_expired")
        raise TokenExpiredError("Token has expired") from e
    except JWTError as e:
        logger.warning("token_invalid", error=str(e))
        raise TokenInvalidError("Token is invalid") from e


def hash_token(token: str) -> str:
    """
    Hash a token for secure storage.

    Uses SHA-256 for fast, secure hashing of tokens.

    Args:
        token: The token to hash

    Returns:
        Hex-encoded hash string
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """
    Verify a token against its stored hash.

    Args:
        token: The token to verify
        token_hash: The stored hash

    Returns:
        True if token matches hash
    """
    return secrets.compare_digest(hash_token(token), token_hash)


def hash_password(password: str) -> str:
    """
    Hash a password for storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# SYMMETRIC ENCRYPTION FOR CACHE DATA
# =============================================================================


def _derive_fernet_key(secret_key: str) -> bytes:
    """
    Derive a Fernet-compatible key from the application secret.

    Fernet requires a 32-byte base64-encoded key. We derive this from
    the secret_key using SHA-256 to ensure consistent key length.

    Args:
        secret_key: The application secret key

    Returns:
        Base64-encoded 32-byte key suitable for Fernet
    """
    # SHA-256 produces exactly 32 bytes
    key_bytes = hashlib.sha256(secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_for_cache(data: str, secret_key: str) -> str:
    """
    Encrypt data for safe storage in cache.

    Uses Fernet symmetric encryption which provides:
    - AES-128-CBC encryption
    - HMAC-SHA256 authentication
    - Timestamp for optional TTL validation

    Args:
        data: The plaintext data to encrypt
        secret_key: The application secret key (minimum 32 characters)

    Returns:
        Base64-encoded encrypted ciphertext

    Example:
        >>> encrypted = encrypt_for_cache("sensitive_token", secret_key)
        >>> # Store encrypted in cache
    """
    _validate_secret_key(secret_key)
    fernet_key = _derive_fernet_key(secret_key)
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()


def decrypt_from_cache(encrypted_data: str, secret_key: str) -> str | None:
    """
    Decrypt data retrieved from cache.

    Args:
        encrypted_data: The encrypted ciphertext
        secret_key: The application secret key

    Returns:
        Decrypted plaintext, or None if decryption fails
        (indicates tampering or wrong key)

    Example:
        >>> decrypted = decrypt_from_cache(encrypted, secret_key)
        >>> if decrypted is None:
        ...     # Data was tampered or key changed
    """
    try:
        _validate_secret_key(secret_key)
        fernet_key = _derive_fernet_key(secret_key)
        fernet = Fernet(fernet_key)
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except (InvalidToken, ValueError) as e:
        logger.warning("cache_decryption_failed", error=str(e))
        return None
