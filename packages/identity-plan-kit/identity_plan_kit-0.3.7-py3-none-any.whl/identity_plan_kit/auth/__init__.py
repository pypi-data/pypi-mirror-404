"""Authentication module - OAuth, tokens, and session management."""

from identity_plan_kit.auth.dependencies import CurrentUser, OptionalUser, get_current_user
from identity_plan_kit.auth.domain.entities import RefreshToken, User, UserProvider
from identity_plan_kit.auth.domain.exceptions import (
    AuthError,
    InvalidCredentialsError,
    OAuthError,
    PasswordValidationError,
    ProviderNotConfiguredError,
    RefreshTokenExpiredError,
    RefreshTokenInvalidError,
    RefreshTokenMissingError,
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)
from identity_plan_kit.auth.repositories.token_repo import RefreshTokenRepository
from identity_plan_kit.auth.repositories.user_repo import UserRepository
from identity_plan_kit.auth.uow import AuthUnitOfWork

__all__ = [
    # Exceptions
    "AuthError",
    # Unit of Work
    "AuthUnitOfWork",
    # Dependencies
    "CurrentUser",
    "InvalidCredentialsError",
    "OAuthError",
    "OptionalUser",
    "PasswordValidationError",
    "ProviderNotConfiguredError",
    "RefreshToken",
    "RefreshTokenExpiredError",
    "RefreshTokenInvalidError",
    "RefreshTokenMissingError",
    # Repositories (for direct use with external sessions)
    "RefreshTokenRepository",
    "TokenExpiredError",
    "TokenInvalidError",
    # Entities
    "User",
    "UserInactiveError",
    "UserNotFoundError",
    "UserProvider",
    "UserRepository",
    "get_current_user",
]
