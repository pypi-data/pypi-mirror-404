"""Auth domain exceptions with error codes."""

from identity_plan_kit.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)


class AuthError(AuthenticationError):
    """Base exception for authentication errors."""

    code = "AUTH_ERROR"
    message = "Authentication error"


class InvalidCredentialsError(AuthError):
    """Invalid credentials provided."""

    code = "INVALID_CREDENTIALS"
    message = "Invalid credentials"


class TokenExpiredError(AuthError):
    """Token has expired."""

    code = "TOKEN_EXPIRED"
    message = "Token has expired"


class TokenInvalidError(AuthError):
    """Token is invalid or malformed."""

    code = "TOKEN_INVALID"
    message = "Invalid token"


class RefreshTokenMissingError(AuthError):
    """Refresh token not provided."""

    code = "REFRESH_TOKEN_MISSING"
    message = "Refresh token not provided"


class RefreshTokenInvalidError(AuthError):
    """Refresh token is invalid."""

    code = "REFRESH_TOKEN_INVALID"
    message = "Invalid refresh token"


class RefreshTokenExpiredError(AuthError):
    """Refresh token has expired."""

    code = "REFRESH_TOKEN_EXPIRED"
    message = "Refresh token has expired"


class UserNotFoundError(NotFoundError):
    """User not found."""

    code = "USER_NOT_FOUND"
    message = "User not found"


class UserInactiveError(AuthorizationError):
    """User account is inactive."""

    code = "USER_INACTIVE"
    message = "User account is inactive"


class OAuthError(AuthError):
    """OAuth provider error."""

    code = "OAUTH_ERROR"
    message = "OAuth error"

    def __init__(
        self,
        message: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.provider = provider
        super().__init__(message=message, details={"provider": provider} if provider else None)


class ProviderNotConfiguredError(OAuthError):
    """OAuth provider is not configured."""

    code = "PROVIDER_NOT_CONFIGURED"
    message = "OAuth provider is not configured"

    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"OAuth provider '{provider}' is not configured",
            provider=provider,
        )


class PasswordValidationError(AuthError):
    """Password does not meet security requirements."""

    code = "PASSWORD_VALIDATION_FAILED"
    message = "Password does not meet security requirements"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message=message)
