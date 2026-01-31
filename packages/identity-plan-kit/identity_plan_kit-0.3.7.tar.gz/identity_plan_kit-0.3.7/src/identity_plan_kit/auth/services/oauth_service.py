"""Google OAuth service with resilience patterns."""

import asyncio
import secrets
from dataclasses import dataclass
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from identity_plan_kit.auth.domain.exceptions import OAuthError
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.circuit_breaker import CircuitBreaker, CircuitBreakerError
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# HTTP timeout configuration
HTTP_TIMEOUT = httpx.Timeout(
    connect=5.0,  # Connection timeout
    read=10.0,  # Read timeout
    write=10.0,  # Write timeout
    pool=5.0,  # Pool timeout
)

# Retry configuration for transient network errors
# Only retry on network errors, NOT on HTTP 4xx errors (those indicate bad requests)
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    OSError,
    ConnectionError,
)

MAX_RETRY_ATTEMPTS = 3

# HTTP status code ranges for error handling
HTTP_CLIENT_ERROR_MIN = 400
HTTP_CLIENT_ERROR_MAX = 500
RETRY_MIN_WAIT = 0.5  # seconds
RETRY_MAX_WAIT = 5.0  # seconds

# P2 FIX: Bulkhead - maximum concurrent calls to Google OAuth
DEFAULT_MAX_CONCURRENT_CALLS = 10
# Timeout for semaphore acquisition (prevents indefinite waiting)
SEMAPHORE_ACQUIRE_TIMEOUT = 30.0  # seconds


@dataclass
class GoogleUserInfo:
    """
    Google user information from OAuth.

    Fields map to Google's userinfo endpoint response:
    https://www.googleapis.com/oauth2/v3/userinfo

    Example response:
    {
        "sub": "110248495921238986420",
        "email": "user@gmail.com",
        "email_verified": true,
        "name": "Иван Иванов",
        "given_name": "Иван",
        "family_name": "Иванов",
        "picture": "https://lh3.googleusercontent.com/...",
        "locale": "ru"
    }
    """

    id: str  # Google's 'sub' field - unique user identifier
    email: str
    email_verified: bool
    name: str | None  # Full display name
    given_name: str | None  # First name
    family_name: str | None  # Last name
    picture: str | None  # Profile picture URL


class SemaphoreTimeoutError(Exception):
    """Raised when semaphore acquisition times out."""

    pass


class GoogleOAuthService:
    """
    Service for Google OAuth2 authentication.

    Features:
    - Instance-scoped circuit breaker (P2 FIX: doesn't leak state between instances)
    - Bulkhead pattern with semaphore (P2 FIX: prevents connection pool exhaustion)
    - Semaphore acquisition timeout (prevents indefinite waiting)
    - Retry with exponential backoff for transient errors
    - Configurable timeouts
    """

    def __init__(
        self,
        config: IdentityPlanKitConfig,
        max_concurrent_calls: int = DEFAULT_MAX_CONCURRENT_CALLS,
        semaphore_timeout: float = SEMAPHORE_ACQUIRE_TIMEOUT,
    ) -> None:
        self._config = config
        self._client_id = config.google_client_id
        self._client_secret = config.google_client_secret.get_secret_value()
        self._redirect_uri = config.google_redirect_uri
        self._semaphore_timeout = semaphore_timeout

        # P2 FIX: Instance-scoped circuit breaker (doesn't leak between test runs)
        self._circuit_breaker = CircuitBreaker(
            name=f"google_oauth_{id(self)}",
            failure_threshold=5,
            recovery_timeout=60.0,
            half_open_max_calls=3,
            success_threshold=2,
            # Don't count client errors (4xx) as circuit breaker failures
            exclude_exceptions=(OAuthError,),
        )

        # P2 FIX: Bulkhead - limits concurrent calls to prevent overwhelming Google
        self._semaphore = asyncio.Semaphore(max_concurrent_calls)

        logger.debug(
            "google_oauth_service_initialized",
            max_concurrent_calls=max_concurrent_calls,
            semaphore_timeout=semaphore_timeout,
        )

    async def _acquire_semaphore(self) -> None:
        """
        Acquire semaphore with timeout.

        Raises:
            SemaphoreTimeoutError: If semaphore cannot be acquired within timeout
        """
        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self._semaphore_timeout,
            )
            if not acquired:
                raise SemaphoreTimeoutError(
                    f"Failed to acquire OAuth semaphore within {self._semaphore_timeout}s"
                )
        except TimeoutError as e:
            logger.warning(
                "oauth_semaphore_timeout",
                provider="google",
                timeout=self._semaphore_timeout,
            )
            raise SemaphoreTimeoutError(
                f"OAuth semaphore acquisition timed out after {self._semaphore_timeout}s"
            ) from e

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """
        Get Google OAuth authorization URL.

        Args:
            state: Optional state for CSRF protection (generated if not provided)

        Returns:
            Tuple of (authorization_url, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        client = AsyncOAuth2Client(
            client_id=self._client_id,
            redirect_uri=self._redirect_uri,
        )

        url, _ = client.create_authorization_url(
            GOOGLE_AUTHORIZE_URL,
            state=state,
            scope="openid email profile",
            access_type="offline",
            prompt="consent",
        )

        logger.debug("oauth_authorization_url_created", provider="google")

        return url, state

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback

        Returns:
            Token response containing access_token, refresh_token, etc.

        Raises:
            OAuthError: If code exchange fails or circuit breaker is open
        """
        try:
            return await self._exchange_code_internal(code)
        except CircuitBreakerError as e:
            logger.warning(
                "oauth_circuit_breaker_open",
                provider="google",
                retry_after=e.retry_after,
            )
            raise OAuthError(
                message="Google OAuth service temporarily unavailable",
                provider="google",
            ) from e
        except SemaphoreTimeoutError as e:
            logger.warning(
                "oauth_semaphore_timeout",
                provider="google",
            )
            raise OAuthError(
                message="Google OAuth service is overloaded, please try again later",
                provider="google",
            ) from e

    async def _exchange_code_internal(self, code: str) -> dict[str, Any]:
        """Internal method for code exchange with retry, circuit breaker, and bulkhead."""

        @self._circuit_breaker.call
        @retry(
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
            before_sleep=before_sleep_log(logger, log_level=20),
            reraise=True,
        )
        async def _do_exchange() -> dict[str, Any]:
            # P2 FIX: Bulkhead with timeout - limit concurrent calls to Google
            await self._acquire_semaphore()
            try:
                async with AsyncOAuth2Client(
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    redirect_uri=self._redirect_uri,
                    timeout=HTTP_TIMEOUT,
                ) as client:
                    try:
                        token = await client.fetch_token(
                            GOOGLE_TOKEN_URL,
                            code=code,
                        )
                        logger.debug("oauth_code_exchanged", provider="google")
                        return dict(token)
                    except httpx.TimeoutException:
                        logger.warning(
                            "oauth_code_exchange_timeout",
                            provider="google",
                        )
                        # Re-raise as retryable if it's a timeout
                        raise
                    except httpx.HTTPStatusError as e:
                        # HTTP errors (4xx, 5xx) - don't retry 4xx
                        if HTTP_CLIENT_ERROR_MIN <= e.response.status_code < HTTP_CLIENT_ERROR_MAX:
                            logger.exception(
                                "oauth_code_exchange_client_error",
                                provider="google",
                                status=e.response.status_code,
                            )
                            raise OAuthError(
                                message=f"Failed to exchange code: {e}",
                                provider="google",
                            ) from e
                        # 5xx errors are transient, will be retried
                        logger.warning(
                            "oauth_code_exchange_server_error",
                            provider="google",
                            status=e.response.status_code,
                        )
                        raise
                    except Exception as e:
                        logger.exception(
                            "oauth_code_exchange_failed",
                            provider="google",
                            error=str(e),
                        )
                        raise OAuthError(
                            message=f"Failed to exchange code: {e}",
                            provider="google",
                        ) from e
            finally:
                self._semaphore.release()

        return await _do_exchange()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Get user information from Google.

        Args:
            access_token: Google access token

        Returns:
            GoogleUserInfo with user details

        Raises:
            OAuthError: If fetching user info fails or circuit breaker is open
        """
        try:
            return await self._get_user_info_internal(access_token)
        except CircuitBreakerError as e:
            logger.warning(
                "oauth_circuit_breaker_open",
                provider="google",
                retry_after=e.retry_after,
            )
            raise OAuthError(
                message="Google OAuth service temporarily unavailable",
                provider="google",
            ) from e
        except SemaphoreTimeoutError as e:
            logger.warning(
                "oauth_semaphore_timeout",
                provider="google",
            )
            raise OAuthError(
                message="Google OAuth service is overloaded, please try again later",
                provider="google",
            ) from e

    async def _get_user_info_internal(self, access_token: str) -> GoogleUserInfo:
        """Internal method for user info fetch with retry, circuit breaker, and bulkhead."""

        @self._circuit_breaker.call
        @retry(
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
            wait=wait_exponential(multiplier=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
            before_sleep=before_sleep_log(logger, log_level=20),
            reraise=True,
        )
        async def _do_fetch() -> GoogleUserInfo:
            # P2 FIX: Bulkhead with timeout - limit concurrent calls to Google
            await self._acquire_semaphore()
            try:
                async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                    try:
                        response = await client.get(
                            GOOGLE_USERINFO_URL,
                            headers={"Authorization": f"Bearer {access_token}"},
                        )
                        response.raise_for_status()
                        data = response.json()

                        logger.debug(
                            "oauth_user_info_fetched",
                            provider="google",
                            email=data.get("email"),
                        )

                        return GoogleUserInfo(
                            id=data["sub"],
                            email=data["email"],
                            email_verified=data.get("email_verified", False),
                            name=data.get("name"),
                            given_name=data.get("given_name"),
                            family_name=data.get("family_name"),
                            picture=data.get("picture"),
                        )
                    except httpx.TimeoutException:
                        logger.warning(
                            "oauth_user_info_timeout",
                            provider="google",
                        )
                        # Re-raise for retry
                        raise
                    except httpx.HTTPStatusError as e:
                        # HTTP errors - don't retry 4xx
                        if HTTP_CLIENT_ERROR_MIN <= e.response.status_code < HTTP_CLIENT_ERROR_MAX:
                            logger.exception(
                                "oauth_user_info_client_error",
                                provider="google",
                                status=e.response.status_code,
                            )
                            raise OAuthError(
                                message=f"Failed to get user info: {e}",
                                provider="google",
                            ) from e
                        # 5xx errors are transient, will be retried
                        logger.warning(
                            "oauth_user_info_server_error",
                            provider="google",
                            status=e.response.status_code,
                        )
                        raise
                    except Exception as e:
                        logger.exception(
                            "oauth_user_info_failed",
                            provider="google",
                            error=str(e),
                        )
                        raise OAuthError(
                            message=f"Failed to get user info: {e}",
                            provider="google",
                        ) from e
            finally:
                self._semaphore.release()

        return await _do_fetch()

    async def authenticate(self, code: str) -> GoogleUserInfo:
        """
        Complete OAuth flow: exchange code and get user info.

        Args:
            code: Authorization code from callback

        Returns:
            GoogleUserInfo with user details

        Raises:
            OAuthError: If authentication fails
        """
        tokens = await self.exchange_code(code)
        access_token = tokens.get("access_token")

        if not access_token:
            raise OAuthError(
                message="No access token in response",
                provider="google",
            )

        return await self.get_user_info(access_token)
