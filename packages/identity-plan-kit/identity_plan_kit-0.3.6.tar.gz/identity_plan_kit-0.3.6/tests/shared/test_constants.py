"""Tests for shared constants module.

Tests verify:
- Constants are properly defined with correct types
- Constants are used consistently across the codebase
- Default values are sensible
"""

import pytest

from identity_plan_kit.shared.constants import (
    # Cache
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_MAX_CACHE_ENTRIES,
    # Redis
    REDIS_SOCKET_TIMEOUT,
    REDIS_SOCKET_CONNECT_TIMEOUT,
    REDIS_RETRY_ATTEMPTS,
    REDIS_RETRY_BASE_DELAY,
    REDIS_CIRCUIT_FAILURE_THRESHOLD,
    REDIS_CIRCUIT_RECOVERY_TIMEOUT,
    REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS,
    # State store
    STATE_STORE_MAX_KEY_LENGTH,
    STATE_STORE_MAX_CONSECUTIVE_ERRORS,
    # User profile
    USER_DISPLAY_NAME_MAX_LENGTH,
    USER_DISPLAY_NAME_MIN_LENGTH,
    USER_PICTURE_URL_MAX_LENGTH,
    # OAuth
    OAUTH_MAX_CONCURRENT_CALLS,
    OAUTH_SEMAPHORE_ACQUIRE_TIMEOUT,
    OAUTH_STATE_TTL_SECONDS,
    # Database
    DEFAULT_DATABASE_POOL_SIZE,
    DEFAULT_DATABASE_MAX_OVERFLOW,
    DEFAULT_DATABASE_STATEMENT_TIMEOUT_MS,
    DATABASE_POOL_RECYCLE_SECONDS,
    # Retry
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_MIN_WAIT,
    DEFAULT_RETRY_MAX_WAIT,
    DEFAULT_STARTUP_TIMEOUT,
    DEFAULT_CONNECTION_RETRY_ATTEMPTS,
    DEFAULT_CONNECTION_RETRY_MAX_WAIT,
    # Lockout
    DEFAULT_LOCKOUT_MAX_ATTEMPTS,
    DEFAULT_LOCKOUT_DURATION_MINUTES,
    DEFAULT_LOCKOUT_WINDOW_MINUTES,
    # Token
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS,
    DEFAULT_TOKEN_REFRESH_IDEMPOTENCY_TTL_SECONDS,
    DEFAULT_QUOTA_IDEMPOTENCY_TTL_SECONDS,
    # Error formatting
    MAX_CONSTRAINT_ERROR_MESSAGE_LENGTH,
    MAX_KEY_DISPLAY_LENGTH,
)


class TestCacheConstants:
    """Tests for cache-related constants."""

    def test_cache_ttl_is_positive(self):
        """Cache TTL should be positive."""
        assert DEFAULT_CACHE_TTL_SECONDS > 0

    def test_cache_ttl_is_reasonable(self):
        """Cache TTL should not be excessively long."""
        assert DEFAULT_CACHE_TTL_SECONDS <= 3600  # Max 1 hour

    def test_max_cache_entries_is_positive(self):
        """Max cache entries should be positive."""
        assert DEFAULT_MAX_CACHE_ENTRIES > 0

    def test_max_cache_entries_is_reasonable(self):
        """Max cache entries should be reasonable for memory."""
        assert DEFAULT_MAX_CACHE_ENTRIES <= 100000


class TestRedisConstants:
    """Tests for Redis-related constants."""

    def test_socket_timeout_is_positive(self):
        """Socket timeout should be positive."""
        assert REDIS_SOCKET_TIMEOUT > 0

    def test_socket_connect_timeout_is_positive(self):
        """Socket connect timeout should be positive."""
        assert REDIS_SOCKET_CONNECT_TIMEOUT > 0

    def test_retry_attempts_is_positive(self):
        """Retry attempts should be at least 1."""
        assert REDIS_RETRY_ATTEMPTS >= 1

    def test_retry_base_delay_is_positive(self):
        """Retry base delay should be positive."""
        assert REDIS_RETRY_BASE_DELAY > 0

    def test_circuit_failure_threshold_is_positive(self):
        """Circuit failure threshold should be positive."""
        assert REDIS_CIRCUIT_FAILURE_THRESHOLD >= 1

    def test_circuit_recovery_timeout_is_positive(self):
        """Circuit recovery timeout should be positive."""
        assert REDIS_CIRCUIT_RECOVERY_TIMEOUT > 0

    def test_circuit_half_open_max_calls_is_positive(self):
        """Half-open max calls should be at least 1."""
        assert REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS >= 1


class TestStateStoreConstants:
    """Tests for state store constants."""

    def test_max_key_length_is_positive(self):
        """Max key length should be positive."""
        assert STATE_STORE_MAX_KEY_LENGTH > 0

    def test_max_key_length_is_reasonable(self):
        """Max key length should be reasonable."""
        assert STATE_STORE_MAX_KEY_LENGTH <= 1024

    def test_max_consecutive_errors_is_positive(self):
        """Max consecutive errors should be positive."""
        assert STATE_STORE_MAX_CONSECUTIVE_ERRORS >= 1


class TestUserProfileConstants:
    """Tests for user profile constraints."""

    def test_display_name_length_constraints(self):
        """Display name constraints should be valid."""
        assert USER_DISPLAY_NAME_MIN_LENGTH >= 0
        assert USER_DISPLAY_NAME_MAX_LENGTH > USER_DISPLAY_NAME_MIN_LENGTH

    def test_picture_url_max_length_is_reasonable(self):
        """Picture URL max length should allow typical URLs."""
        assert USER_PICTURE_URL_MAX_LENGTH >= 100
        assert USER_PICTURE_URL_MAX_LENGTH <= 2048


class TestOAuthConstants:
    """Tests for OAuth constants."""

    def test_max_concurrent_calls_is_positive(self):
        """Max concurrent calls should be positive."""
        assert OAUTH_MAX_CONCURRENT_CALLS >= 1

    def test_semaphore_timeout_is_positive(self):
        """Semaphore timeout should be positive."""
        assert OAUTH_SEMAPHORE_ACQUIRE_TIMEOUT > 0

    def test_state_ttl_is_positive(self):
        """OAuth state TTL should be positive."""
        assert OAUTH_STATE_TTL_SECONDS > 0


class TestDatabaseConstants:
    """Tests for database constants."""

    def test_pool_size_is_positive(self):
        """Pool size should be positive."""
        assert DEFAULT_DATABASE_POOL_SIZE >= 1

    def test_max_overflow_is_non_negative(self):
        """Max overflow can be 0 or positive."""
        assert DEFAULT_DATABASE_MAX_OVERFLOW >= 0

    def test_statement_timeout_is_positive(self):
        """Statement timeout should be positive."""
        assert DEFAULT_DATABASE_STATEMENT_TIMEOUT_MS > 0

    def test_pool_recycle_is_positive(self):
        """Pool recycle time should be positive."""
        assert DATABASE_POOL_RECYCLE_SECONDS > 0


class TestRetryConstants:
    """Tests for retry configuration constants."""

    def test_retry_attempts_is_positive(self):
        """Default retry attempts should be positive."""
        assert DEFAULT_RETRY_ATTEMPTS >= 1

    def test_retry_wait_times_are_positive(self):
        """Retry wait times should be positive."""
        assert DEFAULT_RETRY_MIN_WAIT > 0
        assert DEFAULT_RETRY_MAX_WAIT > 0

    def test_retry_min_wait_less_than_max(self):
        """Min wait should be less than or equal to max wait."""
        assert DEFAULT_RETRY_MIN_WAIT <= DEFAULT_RETRY_MAX_WAIT

    def test_startup_timeout_is_positive(self):
        """Startup timeout should be positive."""
        assert DEFAULT_STARTUP_TIMEOUT > 0

    def test_connection_retry_attempts_is_positive(self):
        """Connection retry attempts should be positive."""
        assert DEFAULT_CONNECTION_RETRY_ATTEMPTS >= 1


class TestLockoutConstants:
    """Tests for lockout configuration constants."""

    def test_max_attempts_is_positive(self):
        """Max attempts should be positive."""
        assert DEFAULT_LOCKOUT_MAX_ATTEMPTS >= 1

    def test_lockout_duration_is_positive(self):
        """Lockout duration should be positive."""
        assert DEFAULT_LOCKOUT_DURATION_MINUTES > 0

    def test_lockout_window_is_positive(self):
        """Lockout window should be positive."""
        assert DEFAULT_LOCKOUT_WINDOW_MINUTES > 0


class TestTokenConstants:
    """Tests for token configuration constants."""

    def test_access_token_expire_is_positive(self):
        """Access token expiration should be positive."""
        assert DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_refresh_token_expire_is_positive(self):
        """Refresh token expiration should be positive."""
        assert DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS > 0

    def test_refresh_token_longer_than_access(self):
        """Refresh token should expire after access token."""
        refresh_minutes = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        assert refresh_minutes > DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES

    def test_idempotency_ttls_are_positive(self):
        """Idempotency TTLs should be positive."""
        assert DEFAULT_TOKEN_REFRESH_IDEMPOTENCY_TTL_SECONDS > 0
        assert DEFAULT_QUOTA_IDEMPOTENCY_TTL_SECONDS > 0


class TestConstantsUsedInOAuthService:
    """Tests that constants are used in OAuth service."""

    def test_oauth_service_uses_constants(self):
        """OAuth service should use constants for defaults."""
        from identity_plan_kit.auth.services.oauth_service import (
            DEFAULT_MAX_CONCURRENT_CALLS,
            SEMAPHORE_ACQUIRE_TIMEOUT,
        )

        assert DEFAULT_MAX_CONCURRENT_CALLS == OAUTH_MAX_CONCURRENT_CALLS
        assert SEMAPHORE_ACQUIRE_TIMEOUT == OAUTH_SEMAPHORE_ACQUIRE_TIMEOUT


class TestConstantsUsedInStateStore:
    """Tests that constants are used in state store."""

    def test_state_store_uses_constants(self):
        """State store should use constants."""
        from identity_plan_kit.shared.state_store import InMemoryStateStore

        store = InMemoryStateStore()
        assert store.MAX_ENTRIES == DEFAULT_MAX_CACHE_ENTRIES
        assert store.MAX_CONSECUTIVE_ERRORS == STATE_STORE_MAX_CONSECUTIVE_ERRORS
