"""Tests for OAuth service resilience patterns.

Tests cover:
- Circuit breaker integration with OAuth
- Semaphore (bulkhead) pattern for concurrent requests
- Instance isolation
- Error handling and error classification

CRITICAL: These tests ensure OAuth service handles:
- Network failures gracefully
- Prevents cascading failures
- Doesn't overwhelm external services
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from identity_plan_kit.auth.domain.exceptions import OAuthError
from identity_plan_kit.auth.services.oauth_service import (
    DEFAULT_MAX_CONCURRENT_CALLS,
    GoogleOAuthService,
    GoogleUserInfo,
    RETRYABLE_EXCEPTIONS,
)
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.circuit_breaker import CircuitState

pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_config():
    """Create mock config for OAuth service."""
    config = MagicMock(spec=IdentityPlanKitConfig)
    config.google_client_id = "test-client-id"
    config.google_client_secret = MagicMock()
    config.google_client_secret.get_secret_value.return_value = "test-client-secret"
    config.google_redirect_uri = "https://example.com/callback"
    return config


class TestGoogleOAuthServiceInit:
    """Test OAuth service initialization."""

    def test_creates_instance_scoped_circuit_breaker(self, mock_config):
        """Each service instance has its own circuit breaker."""
        service1 = GoogleOAuthService(mock_config)
        service2 = GoogleOAuthService(mock_config)

        # Different instances have different circuit breakers
        assert service1._circuit_breaker is not service2._circuit_breaker
        assert service1._circuit_breaker.name != service2._circuit_breaker.name

    def test_creates_semaphore_with_default_limit(self, mock_config):
        """Semaphore is created with default concurrent call limit."""
        service = GoogleOAuthService(mock_config)

        # Default is 10 concurrent calls
        assert service._semaphore._value == DEFAULT_MAX_CONCURRENT_CALLS

    def test_creates_semaphore_with_custom_limit(self, mock_config):
        """Semaphore can be configured with custom concurrent call limit."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=5)

        assert service._semaphore._value == 5

    def test_circuit_breaker_has_correct_settings(self, mock_config):
        """Circuit breaker is configured with appropriate defaults."""
        service = GoogleOAuthService(mock_config)

        # Check default configuration
        assert service._circuit_breaker.failure_threshold == 5
        assert service._circuit_breaker.recovery_timeout.total_seconds() == 60.0
        assert service._circuit_breaker.half_open_max_calls == 3
        assert service._circuit_breaker.success_threshold == 2

    def test_circuit_breaker_excludes_oauth_errors(self, mock_config):
        """Circuit breaker is configured to exclude OAuthError."""
        service = GoogleOAuthService(mock_config)

        # OAuthError should not count as circuit breaker failure
        assert OAuthError in service._circuit_breaker.exclude_exceptions


class TestAuthorizationUrl:
    """Test authorization URL generation."""

    def test_generates_state_if_not_provided(self, mock_config):
        """State is auto-generated if not provided."""
        service = GoogleOAuthService(mock_config)

        url1, state1 = service.get_authorization_url()
        url2, state2 = service.get_authorization_url()

        # Different calls generate different states
        assert state1 != state2
        assert len(state1) > 20  # Secure random state

    def test_uses_provided_state(self, mock_config):
        """Provided state is used in URL."""
        service = GoogleOAuthService(mock_config)
        custom_state = "my-custom-state"

        url, state = service.get_authorization_url(state=custom_state)

        assert state == custom_state
        assert custom_state in url

    def test_authorization_url_contains_required_params(self, mock_config):
        """Authorization URL contains all required OAuth parameters."""
        service = GoogleOAuthService(mock_config)

        url, _ = service.get_authorization_url()

        assert "client_id=test-client-id" in url
        assert "redirect_uri=" in url
        assert "scope=" in url
        assert "state=" in url


class TestCircuitBreakerState:
    """Test circuit breaker state management."""

    def test_initial_state_is_closed(self, mock_config):
        """Circuit breaker starts in closed state."""
        service = GoogleOAuthService(mock_config)

        assert service._circuit_breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_state_isolated_between_instances(self, mock_config):
        """Circuit breaker state is isolated between service instances."""
        service1 = GoogleOAuthService(mock_config)
        service2 = GoogleOAuthService(mock_config)

        # Manually change state on service1
        service1._circuit_breaker._state = CircuitState.OPEN

        # service2 should be unaffected
        assert service1._circuit_breaker.state == CircuitState.OPEN
        assert service2._circuit_breaker.state == CircuitState.CLOSED


class TestSemaphoreBulkhead:
    """Test semaphore (bulkhead) pattern."""

    async def test_semaphore_limits_concurrent_operations(self, mock_config):
        """Semaphore limits concurrent operations."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=2)

        # Initially all permits available
        assert service._semaphore._value == 2

        # Acquire permits
        async with service._semaphore:
            assert service._semaphore._value == 1
            async with service._semaphore:
                assert service._semaphore._value == 0

        # Permits released
        assert service._semaphore._value == 2

    async def test_semaphore_prevents_over_acquisition(self, mock_config):
        """Semaphore blocks when all permits are taken."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=1)

        acquired = False

        async def try_acquire():
            nonlocal acquired
            async with service._semaphore:
                acquired = True
                await asyncio.sleep(0.2)

        async def try_acquire_blocked():
            await asyncio.sleep(0.05)  # Let first acquire start
            start = asyncio.get_event_loop().time()
            async with service._semaphore:
                elapsed = asyncio.get_event_loop().time() - start
                return elapsed

        # First task holds the semaphore
        task1 = asyncio.create_task(try_acquire())
        # Second task should be blocked
        elapsed = await try_acquire_blocked()

        await task1

        # Second task should have waited
        assert elapsed >= 0.1


class TestRetryableExceptions:
    """Test that correct exceptions are retryable."""

    def test_network_errors_are_retryable(self):
        """Network-related exceptions should be retryable."""
        import httpx

        expected_retryable = {
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            OSError,
            ConnectionError,
        }

        for exc_type in expected_retryable:
            assert exc_type in RETRYABLE_EXCEPTIONS


class TestAuthenticate:
    """Test full authentication flow."""

    async def test_authenticate_exchanges_code_and_gets_user_info(self, mock_config):
        """authenticate() chains exchange_code and get_user_info."""
        service = GoogleOAuthService(mock_config)

        mock_tokens = {"access_token": "test-access-token"}
        mock_user_info = GoogleUserInfo(
            id="google-user-id",
            email="test@example.com",
            email_verified=True,
            name="Test User",
            given_name="Test",
            family_name="User",
            picture=None,
        )

        with patch.object(
            service, "exchange_code", return_value=mock_tokens
        ) as mock_exchange:
            with patch.object(
                service, "get_user_info", return_value=mock_user_info
            ) as mock_get_user:
                result = await service.authenticate("auth-code")

        mock_exchange.assert_called_once_with("auth-code")
        mock_get_user.assert_called_once_with("test-access-token")
        assert result.email == "test@example.com"

    async def test_authenticate_raises_if_no_access_token(self, mock_config):
        """authenticate() raises OAuthError if no access token in response."""
        service = GoogleOAuthService(mock_config)

        with patch.object(service, "exchange_code", return_value={}):
            with pytest.raises(OAuthError) as exc_info:
                await service.authenticate("auth-code")

            assert "No access token" in str(exc_info.value.message)


class TestConcurrentOAuthRequests:
    """Test concurrent OAuth requests behavior."""

    async def test_multiple_services_dont_share_state(self, mock_config):
        """Multiple service instances don't share circuit breaker state."""
        services = [GoogleOAuthService(mock_config) for _ in range(5)]

        # Each has its own circuit breaker
        breaker_ids = {id(s._circuit_breaker) for s in services}
        assert len(breaker_ids) == 5

        # Modifying one doesn't affect others
        services[0]._circuit_breaker._state = CircuitState.OPEN

        for service in services[1:]:
            assert service._circuit_breaker.state == CircuitState.CLOSED

    async def test_concurrent_authorization_url_generation(self, mock_config):
        """Concurrent authorization URL generation produces unique states."""
        service = GoogleOAuthService(mock_config)

        async def get_state():
            _, state = service.get_authorization_url()
            return state

        tasks = [get_state() for _ in range(100)]
        states = await asyncio.gather(*tasks)

        # All states should be unique
        assert len(set(states)) == 100


class TestErrorHandling:
    """Test error handling in OAuth service."""

    async def test_exchange_code_returns_oauth_error_when_circuit_open(self, mock_config):
        """exchange_code returns OAuthError when circuit breaker is open."""
        service = GoogleOAuthService(mock_config)

        # Force circuit open
        service._circuit_breaker._state = CircuitState.OPEN
        from datetime import UTC, datetime
        service._circuit_breaker._stats.state_changed_at = datetime.now(UTC)

        with pytest.raises(OAuthError) as exc_info:
            await service.exchange_code("test-code")

        assert "temporarily unavailable" in str(exc_info.value.message)
        assert exc_info.value.provider == "google"

    async def test_get_user_info_returns_oauth_error_when_circuit_open(self, mock_config):
        """get_user_info returns OAuthError when circuit breaker is open."""
        service = GoogleOAuthService(mock_config)

        # Force circuit open
        service._circuit_breaker._state = CircuitState.OPEN
        from datetime import UTC, datetime
        service._circuit_breaker._stats.state_changed_at = datetime.now(UTC)

        with pytest.raises(OAuthError) as exc_info:
            await service.get_user_info("test-token")

        assert "temporarily unavailable" in str(exc_info.value.message)


class TestInstanceIsolation:
    """Test that service instances are properly isolated."""

    async def test_circuit_breaker_name_includes_instance_id(self, mock_config):
        """Circuit breaker name includes instance ID for isolation."""
        service = GoogleOAuthService(mock_config)

        # Name should include instance ID
        assert f"google_oauth_{id(service)}" == service._circuit_breaker.name

    async def test_multiple_instances_have_separate_semaphores(self, mock_config):
        """Each service instance has its own semaphore."""
        service1 = GoogleOAuthService(mock_config, max_concurrent_calls=5)
        service2 = GoogleOAuthService(mock_config, max_concurrent_calls=10)

        # Different semaphores with different limits
        assert service1._semaphore._value == 5
        assert service2._semaphore._value == 10
        assert service1._semaphore is not service2._semaphore
