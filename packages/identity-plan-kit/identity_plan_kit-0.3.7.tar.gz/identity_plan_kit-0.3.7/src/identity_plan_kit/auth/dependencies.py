"""Auth FastAPI dependencies."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.auth.domain.exceptions import (
    AuthError,
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=False)


def current_user(
    include_role: bool = True,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """
    Create a parameterized current user dependency.

    Use this when you need to control whether role is loaded:

    Example::

        # Skip role loading for better performance
        @router.get("/generate")
        async def generate(
            user: Annotated[User, Depends(current_user(include_role=False))],
        ):
            ...

    Args:
        include_role: If True, eagerly load the user's role (default: True).
            Set to False to skip the role query when role info is not needed.

    Returns:
        FastAPI dependency function
    """

    async def _get_user(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(bearer_scheme),
        ] = None,
        access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
    ) -> User:
        token: str | None = None
        if credentials:
            token = credentials.credentials
        elif access_token:
            token = access_token

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        kit = request.app.state.identity_plan_kit
        auth_service = kit.auth_service

        try:
            return await auth_service.get_user_from_token(token, include_role=include_role)
        except TokenExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        except (TokenInvalidError, AuthError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        except UserInactiveError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            ) from None

    return _get_user


async def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> User:
    """
    Get the current authenticated user.

    Checks for JWT token in:
    1. Authorization header (Bearer token)
    2. access_token cookie

    Args:
        request: FastAPI request
        credentials: Bearer token from header
        access_token: Token from cookie

    Returns:
        Authenticated User entity

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    # Get token from header or cookie
    token: str | None = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get auth service from app state
    kit = request.app.state.identity_plan_kit
    auth_service = kit.auth_service

    try:
        return await auth_service.get_user_from_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except (TokenInvalidError, AuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except UserInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        ) from None


async def get_optional_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> User | None:
    """
    Get the current user if authenticated, None otherwise.

    Useful for endpoints that work for both authenticated and anonymous users.

    Returns:
        User entity or None
    """
    token: str | None = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        return None

    try:
        kit = request.app.state.identity_plan_kit
        auth_service = kit.auth_service
        return await auth_service.get_user_from_token(token)
    except AuthError:
        # Expected auth errors (expired, invalid token, etc.) - return None
        return None
    except Exception:
        # Unexpected errors (DB failures, config issues) - log and re-raise
        # This ensures we don't silently mask infrastructure failures
        logger.exception(
            "unexpected_error_in_optional_auth",
            has_token=bool(token),
        )
        raise


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]

# Optimized variant that skips role loading (saves 1 DB query)
# Use when role info is not needed for the endpoint
CurrentUserNoRole = Annotated[User, Depends(current_user(include_role=False))]
