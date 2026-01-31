"""Tests for OAuth semaphore timeout feature.

Tests cover:
- Semaphore acquisition with timeout
- SemaphoreTimeoutError handling
- OAuthError propagation from semaphore timeout
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from identity_plan_kit.auth.domain.exceptions import OAuthError
from identity_plan_kit.auth.services.oauth_service import (
    DEFAULT_MAX_CONCURRENT_CALLS,
    SEMAPHORE_ACQUIRE_TIMEOUT,
    GoogleOAuthService,
    SemaphoreTimeoutError,
)
from identity_plan_kit.config import IdentityPlanKitConfig


@pytest.fixture
def mock_config():
    """Create a mock config for OAuth service."""
    config = MagicMock(spec=IdentityPlanKitConfig)
    config.google_client_id = "test-client-id"
    config.google_client_secret = MagicMock()
    config.google_client_secret.get_secret_value.return_value = "test-client-secret"
    config.google_redirect_uri = "http://localhost:8000/callback"
    return config


class TestSemaphoreTimeoutConfiguration:
    """Tests for semaphore timeout configuration."""

    def test_default_semaphore_timeout(self, mock_config):
        """Should use default semaphore timeout."""
        service = GoogleOAuthService(mock_config)
        assert service._semaphore_timeout == SEMAPHORE_ACQUIRE_TIMEOUT

    def test_custom_semaphore_timeout(self, mock_config):
        """Should accept custom semaphore timeout."""
        service = GoogleOAuthService(mock_config, semaphore_timeout=60.0)
        assert service._semaphore_timeout == 60.0

    def test_default_max_concurrent_calls(self, mock_config):
        """Should use default max concurrent calls."""
        service = GoogleOAuthService(mock_config)
        # Semaphore internal value is the initial count
        assert service._semaphore._value == DEFAULT_MAX_CONCURRENT_CALLS

    def test_custom_max_concurrent_calls(self, mock_config):
        """Should accept custom max concurrent calls."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=5)
        assert service._semaphore._value == 5


class TestSemaphoreAcquisition:
    """Tests for semaphore acquisition with timeout."""

    async def test_acquire_semaphore_success(self, mock_config):
        """Should successfully acquire semaphore when available."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=1)

        # Should not raise
        await service._acquire_semaphore()

        # Semaphore should be acquired (count decreased)
        assert service._semaphore._value == 0

        # Release for cleanup
        service._semaphore.release()

    async def test_acquire_semaphore_timeout(self, mock_config):
        """Should raise SemaphoreTimeoutError when timeout expires."""
        service = GoogleOAuthService(
            mock_config,
            max_concurrent_calls=1,
            semaphore_timeout=0.1,  # Very short timeout
        )

        # Acquire the only available slot
        await service._semaphore.acquire()

        # Should timeout trying to acquire
        with pytest.raises(SemaphoreTimeoutError):
            await service._acquire_semaphore()

        # Release for cleanup
        service._semaphore.release()

    async def test_semaphore_timeout_error_message(self, mock_config):
        """SemaphoreTimeoutError should have descriptive message."""
        service = GoogleOAuthService(
            mock_config,
            max_concurrent_calls=1,
            semaphore_timeout=0.1,
        )

        await service._semaphore.acquire()

        try:
            await service._acquire_semaphore()
            pytest.fail("Should have raised SemaphoreTimeoutError")
        except SemaphoreTimeoutError as e:
            assert "0.1s" in str(e)
            assert "timed out" in str(e).lower()

        service._semaphore.release()


class TestOAuthErrorOnSemaphoreTimeout:
    """Tests for OAuthError propagation from semaphore timeout."""

    async def test_exchange_code_raises_oauth_error_on_timeout(self, mock_config):
        """exchange_code should raise OAuthError when semaphore times out."""
        service = GoogleOAuthService(
            mock_config,
            max_concurrent_calls=1,
            semaphore_timeout=0.1,
        )

        # Acquire the only slot
        await service._semaphore.acquire()

        try:
            with pytest.raises(OAuthError) as exc_info:
                await service.exchange_code("test-code")

            assert "overloaded" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "google"
        finally:
            service._semaphore.release()

    async def test_get_user_info_raises_oauth_error_on_timeout(self, mock_config):
        """get_user_info should raise OAuthError when semaphore times out."""
        service = GoogleOAuthService(
            mock_config,
            max_concurrent_calls=1,
            semaphore_timeout=0.1,
        )

        await service._semaphore.acquire()

        try:
            with pytest.raises(OAuthError) as exc_info:
                await service.get_user_info("test-access-token")

            assert "overloaded" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "google"
        finally:
            service._semaphore.release()


class TestSemaphoreRelease:
    """Tests for proper semaphore release."""

    async def test_semaphore_released_on_success(self, mock_config):
        """Semaphore should be released after successful operation."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=1)

        initial_value = service._semaphore._value

        # Mock the internal exchange to succeed
        with patch.object(service, "_exchange_code_internal", new_callable=AsyncMock) as mock:
            mock.return_value = {"access_token": "test-token"}
            await service.exchange_code("test-code")

        # Semaphore should be back to initial value
        assert service._semaphore._value == initial_value

    async def test_semaphore_released_on_error(self, mock_config):
        """Semaphore should be released even when operation fails."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=1)

        initial_value = service._semaphore._value

        # Mock the internal exchange to fail
        with patch.object(service, "_exchange_code_internal", new_callable=AsyncMock) as mock:
            mock.side_effect = OAuthError(message="Test error", provider="google")
            with pytest.raises(OAuthError):
                await service.exchange_code("test-code")

        # Semaphore should still be back to initial value
        assert service._semaphore._value == initial_value


class TestConcurrentOAuthWithTimeout:
    """Tests for concurrent OAuth operations with semaphore timeout."""

    async def test_concurrent_calls_within_limit(self, mock_config):
        """Should allow concurrent calls up to the limit."""
        service = GoogleOAuthService(mock_config, max_concurrent_calls=3)

        acquired_count = 0
        timeout_count = 0

        async def try_acquire():
            nonlocal acquired_count, timeout_count
            try:
                await service._acquire_semaphore()
                acquired_count += 1
                await asyncio.sleep(0.05)  # Simulate work
                service._semaphore.release()
            except SemaphoreTimeoutError:
                timeout_count += 1

        # Start 3 concurrent acquires (should all succeed)
        service._semaphore_timeout = 1.0
        await asyncio.gather(*[try_acquire() for _ in range(3)])

        assert acquired_count == 3
        assert timeout_count == 0

    async def test_excess_concurrent_calls_timeout(self, mock_config):
        """Calls exceeding the limit should timeout if semaphore not released."""
        service = GoogleOAuthService(
            mock_config,
            max_concurrent_calls=2,
            semaphore_timeout=0.1,
        )

        acquired_count = 0
        timeout_count = 0
        release_event = asyncio.Event()

        async def hold_semaphore():
            nonlocal acquired_count
            await service._semaphore.acquire()
            acquired_count += 1
            await release_event.wait()  # Hold until released
            service._semaphore.release()

        async def try_acquire_and_timeout():
            nonlocal timeout_count
            try:
                await service._acquire_semaphore()
                service._semaphore.release()
            except SemaphoreTimeoutError:
                timeout_count += 1

        # Start 2 tasks that hold the semaphore
        hold_tasks = [asyncio.create_task(hold_semaphore()) for _ in range(2)]
        await asyncio.sleep(0.01)  # Let them acquire

        # Try to acquire (should timeout)
        await try_acquire_and_timeout()

        # Cleanup
        release_event.set()
        await asyncio.gather(*hold_tasks)

        assert acquired_count == 2
        assert timeout_count == 1


class TestSemaphoreTimeoutError:
    """Tests for SemaphoreTimeoutError exception."""

    def test_error_is_exception(self):
        """SemaphoreTimeoutError should be an Exception."""
        error = SemaphoreTimeoutError("Test timeout")
        assert isinstance(error, Exception)

    def test_error_message(self):
        """Should store the error message."""
        error = SemaphoreTimeoutError("Custom timeout message")
        assert "Custom timeout message" in str(error)
