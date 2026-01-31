"""Utility functions for load tests."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from jose import jwt

from loadtests.config import config


@dataclass
class TestUser:
    """Represents a test user for load testing."""

    id: UUID
    email: str
    role_id: UUID
    role_code: str
    access_token: str
    refresh_token: str
    plan_code: str | None = None

    def auth_headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def auth_cookies(self) -> dict[str, str]:
        """Get authentication cookies."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }


class TestUserPool:
    """Pool of pre-generated test users for load testing."""

    # Default role IDs (should match your test database)
    DEFAULT_USER_ROLE_ID = UUID("00000000-0000-0000-0000-000000000002")
    DEFAULT_ADMIN_ROLE_ID = UUID("00000000-0000-0000-0000-000000000001")

    def __init__(
        self,
        count: int = 100,
        secret_key: str | None = None,
        algorithm: str = "HS256",
    ) -> None:
        """
        Initialize test user pool.

        Args:
            count: Number of test users to generate
            secret_key: JWT secret key
            algorithm: JWT algorithm
        """
        self._secret_key = secret_key or config.secret_key
        self._algorithm = algorithm
        self._users: list[TestUser] = []
        self._admin_users: list[TestUser] = []
        self._index = 0
        self._admin_index = 0

        self._generate_users(count)

    def _generate_users(self, count: int) -> None:
        """Generate test users."""
        admin_count = max(1, count // 10)  # 10% admins
        user_count = count - admin_count

        # Generate regular users
        for i in range(user_count):
            user = self._create_user(
                email=f"loadtest_user_{i}@example.com",
                role_id=self.DEFAULT_USER_ROLE_ID,
                role_code="user",
                plan_code=config.plan_codes[i % len(config.plan_codes)],
            )
            self._users.append(user)

        # Generate admin users
        for i in range(admin_count):
            user = self._create_user(
                email=f"loadtest_admin_{i}@example.com",
                role_id=self.DEFAULT_ADMIN_ROLE_ID,
                role_code="admin",
                plan_code="enterprise",
            )
            self._admin_users.append(user)

    def _create_user(
        self,
        email: str,
        role_id: UUID,
        role_code: str,
        plan_code: str | None = None,
    ) -> TestUser:
        """Create a test user with valid tokens."""
        user_id = uuid4()

        # Create access token
        access_token = self._create_access_token(user_id)

        # Create refresh token
        refresh_token = self._create_refresh_token(user_id)

        return TestUser(
            id=user_id,
            email=email,
            role_id=role_id,
            role_code=role_code,
            access_token=access_token,
            refresh_token=refresh_token,
            plan_code=plan_code,
        )

    def _create_access_token(self, user_id: UUID) -> str:
        """Create a JWT access token."""
        expires = datetime.now(UTC) + timedelta(minutes=config.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "exp": expires,
            "iat": datetime.now(UTC),
            "type": "access",
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def _create_refresh_token(self, user_id: UUID) -> str:
        """Create a refresh token."""
        expires = datetime.now(UTC) + timedelta(days=30)
        payload = {
            "sub": str(user_id),
            "exp": expires,
            "iat": datetime.now(UTC),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def get_user(self) -> TestUser:
        """Get next user from pool (round-robin)."""
        user = self._users[self._index % len(self._users)]
        self._index += 1
        return user

    def get_admin_user(self) -> TestUser:
        """Get next admin user from pool (round-robin)."""
        user = self._admin_users[self._admin_index % len(self._admin_users)]
        self._admin_index += 1
        return user

    def get_random_user(self) -> TestUser:
        """Get a random user from pool."""
        import random

        return random.choice(self._users)

    @property
    def users(self) -> list[TestUser]:
        """Get all regular users."""
        return self._users

    @property
    def admin_users(self) -> list[TestUser]:
        """Get all admin users."""
        return self._admin_users

    @property
    def all_users(self) -> list[TestUser]:
        """Get all users."""
        return self._users + self._admin_users


def generate_oauth_state() -> str:
    """Generate a mock OAuth state parameter."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for comparison."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_mock_oauth_code() -> str:
    """Generate a mock OAuth authorization code."""
    return secrets.token_urlsafe(32)


class MetricsCollector:
    """Collect custom metrics during load tests."""

    def __init__(self) -> None:
        self.cache_hits = 0
        self.cache_misses = 0
        self.quota_exceeded = 0
        self.db_errors = 0
        self.auth_failures = 0

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1

    def record_quota_exceeded(self) -> None:
        """Record quota exceeded error."""
        self.quota_exceeded += 1

    def record_db_error(self) -> None:
        """Record database error."""
        self.db_errors += 1

    def record_auth_failure(self) -> None:
        """Record authentication failure."""
        self.auth_failures += 1

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def to_dict(self) -> dict[str, Any]:
        """Export metrics as dictionary."""
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": self.cache_hit_ratio,
            "quota_exceeded": self.quota_exceeded,
            "db_errors": self.db_errors,
            "auth_failures": self.auth_failures,
        }


# Global metrics collector
metrics = MetricsCollector()

# Global user pool (initialized lazily)
_user_pool: TestUserPool | None = None


def get_user_pool() -> TestUserPool:
    """Get or create the global user pool."""
    global _user_pool
    if _user_pool is None:
        _user_pool = TestUserPool(count=config.test_user_count)
    return _user_pool
