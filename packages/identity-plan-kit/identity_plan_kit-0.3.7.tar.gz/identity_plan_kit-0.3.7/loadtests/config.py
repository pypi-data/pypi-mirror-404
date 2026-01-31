"""Load test configuration and environment setup."""

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    # Target application
    base_url: str = field(default_factory=lambda: os.getenv("LOADTEST_BASE_URL", "http://localhost:8000"))
    api_prefix: str = field(default_factory=lambda: os.getenv("LOADTEST_API_PREFIX", ""))

    # Database (for direct service testing)
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "LOADTEST_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/identity_plan_kit_loadtest",
        )
    )

    # Redis (optional)
    redis_url: str | None = field(default_factory=lambda: os.getenv("LOADTEST_REDIS_URL"))

    # Test user pool settings
    test_user_count: int = field(
        default_factory=lambda: int(os.getenv("LOADTEST_USER_COUNT", "100"))
    )

    # JWT settings for generating test tokens
    secret_key: str = field(
        default_factory=lambda: os.getenv(
            "LOADTEST_SECRET_KEY", "loadtest-secret-key-that-is-at-least-32-chars"
        )
    )
    algorithm: str = field(default_factory=lambda: os.getenv("LOADTEST_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("LOADTEST_TOKEN_EXPIRE_MINUTES", "60"))
    )

    # Load test parameters
    spawn_rate: int = field(default_factory=lambda: int(os.getenv("LOADTEST_SPAWN_RATE", "10")))
    run_time: str = field(default_factory=lambda: os.getenv("LOADTEST_RUN_TIME", "5m"))

    # Feature flags for tests
    test_auth: bool = field(
        default_factory=lambda: os.getenv("LOADTEST_TEST_AUTH", "true").lower() == "true"
    )
    test_rbac: bool = field(
        default_factory=lambda: os.getenv("LOADTEST_TEST_RBAC", "true").lower() == "true"
    )
    test_plans: bool = field(
        default_factory=lambda: os.getenv("LOADTEST_TEST_PLANS", "true").lower() == "true"
    )
    test_quotas: bool = field(
        default_factory=lambda: os.getenv("LOADTEST_TEST_QUOTAS", "true").lower() == "true"
    )

    # Test data
    plan_codes: list[str] = field(
        default_factory=lambda: os.getenv("LOADTEST_PLAN_CODES", "free,pro,enterprise").split(",")
    )
    feature_codes: list[str] = field(
        default_factory=lambda: os.getenv("LOADTEST_FEATURE_CODES", "api_calls,ai_generation,exports").split(
            ","
        )
    )
    role_codes: list[str] = field(
        default_factory=lambda: os.getenv("LOADTEST_ROLE_CODES", "user,admin").split(",")
    )

    @property
    def auth_url(self) -> str:
        """Get the auth URL."""
        return f"{self.base_url}{self.api_prefix}/auth"

    @property
    def health_url(self) -> str:
        """Get the health URL."""
        return f"{self.base_url}{self.api_prefix}/health"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "base_url": self.base_url,
            "api_prefix": self.api_prefix,
            "test_user_count": self.test_user_count,
            "test_auth": self.test_auth,
            "test_rbac": self.test_rbac,
            "test_plans": self.test_plans,
            "test_quotas": self.test_quotas,
        }


# Global config instance
config = LoadTestConfig()
