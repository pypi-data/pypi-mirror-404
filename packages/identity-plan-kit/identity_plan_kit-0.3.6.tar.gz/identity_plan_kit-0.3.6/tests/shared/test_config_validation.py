"""Tests for configuration validation.

Tests cover:
- Secret key length validation
- JWT algorithm validation
- Token expiration bounds
- Database pool size limits
- Environment-specific defaults

CRITICAL: These tests ensure security-critical config
values are validated before the application starts.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from identity_plan_kit.config import Environment, IdentityPlanKitConfig


def create_minimal_config(**overrides):
    """Create config with minimal required fields."""
    defaults = {
        "database_url": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "secret_key": "a" * 32,  # Minimum 32 chars
        "google_client_id": "test-client-id",
        "google_client_secret": "test-client-secret",
        "google_redirect_uri": "https://example.com/callback",
    }
    defaults.update(overrides)
    return IdentityPlanKitConfig(**defaults)


class TestSecretKeyValidation:
    """Test secret key validation."""

    def test_secret_key_minimum_length(self):
        """Secret key must be at least 32 characters."""
        # Exactly 32 chars - should work
        config = create_minimal_config(secret_key="a" * 32)
        assert len(config.secret_key.get_secret_value()) == 32

    def test_secret_key_too_short_rejected(self):
        """Secret key shorter than 32 chars is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            create_minimal_config(secret_key="short")

        errors = exc_info.value.errors()
        assert any("secret_key" in str(e) for e in errors)
        assert any("32" in str(e) or "min_length" in str(e) for e in errors)

    def test_secret_key_31_chars_rejected(self):
        """Secret key with 31 chars (boundary) is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(secret_key="a" * 31)

    def test_secret_key_stored_as_secret(self):
        """Secret key is stored as SecretStr."""
        config = create_minimal_config(secret_key="a" * 32)

        # Should be SecretStr type
        assert isinstance(config.secret_key, SecretStr)

        # String representation should be masked
        assert config.secret_key.get_secret_value() not in str(config.secret_key)

    def test_long_secret_key_accepted(self):
        """Longer secret keys are accepted."""
        config = create_minimal_config(secret_key="a" * 256)
        assert len(config.secret_key.get_secret_value()) == 256


class TestJWTAlgorithmValidation:
    """Test JWT algorithm validation."""

    @pytest.mark.parametrize("algorithm", ["HS256", "HS384", "HS512"])
    def test_valid_algorithms_accepted(self, algorithm):
        """Valid HMAC algorithms are accepted."""
        config = create_minimal_config(algorithm=algorithm)
        assert config.algorithm == algorithm

    def test_invalid_algorithm_rejected(self):
        """Invalid algorithm is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            create_minimal_config(algorithm="RS256")

        errors = exc_info.value.errors()
        assert any("algorithm" in str(e) for e in errors)

    def test_lowercase_algorithm_rejected(self):
        """Lowercase algorithm is rejected (must be exact)."""
        with pytest.raises(ValidationError):
            create_minimal_config(algorithm="hs256")

    def test_default_algorithm(self):
        """Default algorithm is HS256."""
        config = create_minimal_config()
        assert config.algorithm == "HS256"


class TestTokenExpirationValidation:
    """Test token expiration validation."""

    def test_access_token_expire_range(self):
        """Access token expiration must be 1-1440 minutes."""
        # Minimum
        config_min = create_minimal_config(access_token_expire_minutes=1)
        assert config_min.access_token_expire_minutes == 1

        # Maximum
        config_max = create_minimal_config(access_token_expire_minutes=1440)
        assert config_max.access_token_expire_minutes == 1440

    def test_access_token_expire_zero_rejected(self):
        """Access token expiration of 0 is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(access_token_expire_minutes=0)

    def test_access_token_expire_too_high_rejected(self):
        """Access token expiration over 1440 minutes is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(access_token_expire_minutes=1441)

    def test_refresh_token_expire_range(self):
        """Refresh token expiration must be 1-365 days."""
        # Minimum
        config_min = create_minimal_config(refresh_token_expire_days=1)
        assert config_min.refresh_token_expire_days == 1

        # Maximum
        config_max = create_minimal_config(refresh_token_expire_days=365)
        assert config_max.refresh_token_expire_days == 365

    def test_refresh_token_expire_too_high_rejected(self):
        """Refresh token expiration over 365 days is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(refresh_token_expire_days=366)

    def test_default_token_expirations(self):
        """Default token expirations are reasonable."""
        config = create_minimal_config()

        # Access token: 15 minutes
        assert config.access_token_expire_minutes == 15

        # Refresh token: 30 days
        assert config.refresh_token_expire_days == 30


class TestDatabasePoolValidation:
    """Test database pool configuration validation."""

    def test_pool_size_range(self):
        """Database pool size must be 1-100."""
        # Minimum
        config_min = create_minimal_config(database_pool_size=1)
        assert config_min.database_pool_size == 1

        # Maximum
        config_max = create_minimal_config(database_pool_size=100)
        assert config_max.database_pool_size == 100

    def test_pool_size_zero_rejected(self):
        """Pool size of 0 is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(database_pool_size=0)

    def test_pool_size_too_high_rejected(self):
        """Pool size over 100 is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(database_pool_size=101)

    def test_statement_timeout_range(self):
        """Statement timeout must be 1000-300000ms."""
        # Minimum (1 second)
        config_min = create_minimal_config(database_statement_timeout_ms=1000)
        assert config_min.database_statement_timeout_ms == 1000

        # Maximum (5 minutes)
        config_max = create_minimal_config(database_statement_timeout_ms=300000)
        assert config_max.database_statement_timeout_ms == 300000

    def test_statement_timeout_too_low_rejected(self):
        """Statement timeout under 1000ms is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(database_statement_timeout_ms=999)


class TestCookieValidation:
    """Test cookie configuration validation."""

    @pytest.mark.parametrize("samesite", ["lax", "strict", "none"])
    def test_valid_samesite_values(self, samesite):
        """Valid SameSite values are accepted."""
        config = create_minimal_config(cookie_samesite=samesite)
        assert config.cookie_samesite == samesite

    def test_invalid_samesite_rejected(self):
        """Invalid SameSite value is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(cookie_samesite="invalid")

    def test_default_cookie_settings(self):
        """Default cookie settings are secure."""
        config = create_minimal_config()

        # Secure cookies by default
        assert config.cookie_secure is True

        # Lax SameSite by default
        assert config.cookie_samesite == "lax"


class TestEnvironmentSettings:
    """Test environment-specific settings."""

    def test_environment_enum_values(self):
        """Environment enum has expected values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

    def test_default_environment_is_development(self):
        """Default environment is development."""
        config = create_minimal_config()
        assert config.environment == Environment.DEVELOPMENT

    def test_is_development_property(self):
        """is_development property works correctly."""
        dev_config = create_minimal_config(environment=Environment.DEVELOPMENT)
        assert dev_config.is_development is True
        assert dev_config.is_production is False

        prod_config = create_minimal_config(environment=Environment.PRODUCTION)
        assert prod_config.is_development is False
        assert prod_config.is_production is True

    def test_require_redis_default_in_production(self):
        """require_redis defaults to True in production with redis_url."""
        config = create_minimal_config(
            environment=Environment.PRODUCTION,
            redis_url="redis://localhost:6379",
        )

        assert config.require_redis is True

    def test_require_redis_default_in_development(self):
        """require_redis defaults to False in development."""
        config = create_minimal_config(
            environment=Environment.DEVELOPMENT,
            redis_url="redis://localhost:6379",
        )

        assert config.require_redis is False


class TestOAuthStateValidation:
    """Test OAuth state configuration validation."""

    def test_oauth_state_ttl_range(self):
        """OAuth state TTL must be 60-600 seconds."""
        # Minimum (1 minute)
        config_min = create_minimal_config(oauth_state_ttl_seconds=60)
        assert config_min.oauth_state_ttl_seconds == 60

        # Maximum (10 minutes)
        config_max = create_minimal_config(oauth_state_ttl_seconds=600)
        assert config_max.oauth_state_ttl_seconds == 600

    def test_oauth_state_ttl_too_low_rejected(self):
        """OAuth state TTL under 60 seconds is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(oauth_state_ttl_seconds=59)

    def test_oauth_state_ttl_too_high_rejected(self):
        """OAuth state TTL over 600 seconds is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(oauth_state_ttl_seconds=601)


class TestPermissionCacheValidation:
    """Test permission cache configuration validation."""

    def test_cache_ttl_range(self):
        """Permission cache TTL must be 0-3600 seconds."""
        # Disabled (0)
        config_disabled = create_minimal_config(permission_cache_ttl_seconds=0)
        assert config_disabled.permission_cache_ttl_seconds == 0

        # Maximum (1 hour)
        config_max = create_minimal_config(permission_cache_ttl_seconds=3600)
        assert config_max.permission_cache_ttl_seconds == 3600

    def test_cache_ttl_negative_rejected(self):
        """Negative cache TTL is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(permission_cache_ttl_seconds=-1)

    def test_cache_ttl_too_high_rejected(self):
        """Cache TTL over 3600 seconds is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(permission_cache_ttl_seconds=3601)


class TestRateLimitValidation:
    """Test rate limit configuration."""

    def test_default_rate_limits(self):
        """Default rate limits are set."""
        config = create_minimal_config()

        assert config.rate_limit_login == "20/minute"
        assert config.rate_limit_callback == "10/minute"
        assert config.rate_limit_refresh == "30/minute"
        assert config.rate_limit_logout == "10/minute"

    def test_custom_rate_limits(self):
        """Custom rate limits are accepted."""
        config = create_minimal_config(
            rate_limit_login="100/minute",
            rate_limit_callback="50/minute",
        )

        assert config.rate_limit_login == "100/minute"
        assert config.rate_limit_callback == "50/minute"


class TestProxyTrustSettings:
    """Test proxy trust configuration."""

    def test_default_proxy_trust_is_false(self):
        """Proxy headers are not trusted by default."""
        config = create_minimal_config()
        assert config.trust_proxy_headers is False

    def test_can_enable_proxy_trust(self):
        """Proxy trust can be enabled."""
        config = create_minimal_config(trust_proxy_headers=True)
        assert config.trust_proxy_headers is True


class TestConfigFromEnv:
    """Test config initialization from environment."""

    def test_from_env_with_custom_prefix(self):
        """Config can be loaded from env with custom prefix."""
        env_vars = {
            "MYAPP_DATABASE_URL": "postgresql+asyncpg://env:pass@localhost/db",
            "MYAPP_SECRET_KEY": "a" * 32,
            "MYAPP_GOOGLE_CLIENT_ID": "env-client-id",
            "MYAPP_GOOGLE_CLIENT_SECRET": "env-secret",
            "MYAPP_GOOGLE_REDIRECT_URI": "https://env.example.com/callback",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = IdentityPlanKitConfig.from_env(prefix="MYAPP_")

            assert config.google_client_id == "env-client-id"


class TestConfigFromSettings:
    """Test config initialization from other settings object."""

    def test_from_settings_with_mapping(self):
        """Config can be loaded from another settings object."""
        class OtherSettings:
            pg_url = "postgresql+asyncpg://other:pass@localhost/db"
            jwt_secret = "a" * 32
            oauth_google_id = "other-client-id"
            oauth_google_secret = "other-secret"
            oauth_redirect = "https://other.example.com/callback"

        other = OtherSettings()

        config = IdentityPlanKitConfig.from_settings(
            other,
            mapping={
                "database_url": "pg_url",
                "secret_key": "jwt_secret",
                "google_client_id": "oauth_google_id",
                "google_client_secret": "oauth_google_secret",
                "google_redirect_uri": "oauth_redirect",
            },
        )

        assert config.google_client_id == "other-client-id"


class TestGracefulShutdownValidation:
    """Test graceful shutdown configuration."""

    def test_shutdown_grace_period_range(self):
        """Shutdown grace period must be 0-60 seconds."""
        # Minimum (immediate)
        config_min = create_minimal_config(shutdown_grace_period_seconds=0.0)
        assert config_min.shutdown_grace_period_seconds == 0.0

        # Maximum (1 minute)
        config_max = create_minimal_config(shutdown_grace_period_seconds=60.0)
        assert config_max.shutdown_grace_period_seconds == 60.0

    def test_shutdown_grace_period_too_high_rejected(self):
        """Shutdown grace period over 60 seconds is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(shutdown_grace_period_seconds=61.0)


class TestIdempotencyValidation:
    """Test token refresh idempotency configuration."""

    def test_idempotency_ttl_range(self):
        """Idempotency TTL must be 5-120 seconds."""
        # Minimum
        config_min = create_minimal_config(token_refresh_idempotency_ttl_seconds=5)
        assert config_min.token_refresh_idempotency_ttl_seconds == 5

        # Maximum
        config_max = create_minimal_config(token_refresh_idempotency_ttl_seconds=120)
        assert config_max.token_refresh_idempotency_ttl_seconds == 120

    def test_idempotency_ttl_too_low_rejected(self):
        """Idempotency TTL under 5 seconds is rejected."""
        with pytest.raises(ValidationError):
            create_minimal_config(token_refresh_idempotency_ttl_seconds=4)
