"""OAuth authentication routes."""

import hashlib
import re
import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from identity_plan_kit.auth.dependencies import CurrentUser
from identity_plan_kit.auth.domain.exceptions import (
    OAuthError,
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
)
from identity_plan_kit.auth.dto.requests import UpdateProfileRequest
from identity_plan_kit.auth.dto.responses import (
    AuthURLResponse,
    PlanInfoResponse,
    ProfileResponse,
    TokenResponse,
    UserResponse,
)
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.http_utils import get_client_ip, get_user_agent
from identity_plan_kit.shared.logging import get_logger
from identity_plan_kit.shared.rate_limiter import get_rate_limiter
from identity_plan_kit.shared.schemas import ResponseModel
from identity_plan_kit.shared.state_store import get_state_store

logger = get_logger(__name__)

# OAuth authorization code format validation
# Codes are typically alphanumeric with some special characters, 20-200 chars
OAUTH_CODE_PATTERN = re.compile(r"^[a-zA-Z0-9/_\-\.]{20,200}$")


def create_auth_router(config: IdentityPlanKitConfig) -> APIRouter:  # noqa: PLR0915
    """
    Create authentication router with all OAuth endpoints.

    Args:
        config: IdentityPlanKit configuration

    Returns:
        FastAPI router with auth endpoints
    """
    router = APIRouter(tags=["auth"])

    rate_limiter = get_rate_limiter()
    # NOTE: Don't capture state_store here - get it lazily inside each endpoint
    # This ensures Redis is connected before the store is used
    # (setup() runs before startup() which connects to Redis)

    @router.get(
        "/google/login",
        response_model=ResponseModel[AuthURLResponse],
        summary="Get Google OAuth URL",
        description="Get URL to redirect user for Google authentication",
    )
    @rate_limiter.limit(config.rate_limit_login, methods=["GET"])
    async def google_login(
        request: Request,
        redirect_url: Annotated[
            str | None,
            Query(description="URL to redirect to after successful authentication"),
        ] = None,
    ) -> ResponseModel[AuthURLResponse]:
        """Get Google OAuth authorization URL."""
        # Validate redirect URL if provided (prevent open redirect)
        validated_redirect_url = None
        if redirect_url:
            validated_redirect_url = _validate_redirect_url(redirect_url, config)
            if validated_redirect_url is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid redirect URL",
                )

        kit = request.app.state.identity_plan_kit
        oauth = kit.auth_service.google_oauth

        url, state = oauth.get_authorization_url()

        # SECURITY FIX: Store state with additional entropy for defense-in-depth
        # Include IP, user agent hash, and nonce to prevent state reuse attacks
        user_agent = get_user_agent(request) or ""
        user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
        nonce = secrets.token_urlsafe(8)

        # Get state store lazily to ensure Redis is connected after startup()
        state_store = get_state_store()
        await state_store.set(
            f"oauth_state:{state}",
            {
                "ip": get_client_ip(request, trust_proxy=config.trust_proxy_headers),
                "ua_hash": user_agent_hash,
                "nonce": nonce,
                "redirect_url": validated_redirect_url,
            },
            ttl_seconds=config.oauth_state_ttl_seconds,
        )

        logger.debug("oauth_state_stored")

        return ResponseModel.ok(data=AuthURLResponse(url=url, state=state))

    @router.get(
        "/google/callback",
        response_model=ResponseModel[TokenResponse],
        summary="Google OAuth callback",
        description="Handle Google OAuth callback and authenticate user",
    )
    @rate_limiter.limit(config.rate_limit_callback)
    async def google_callback(
        request: Request,
        response: Response,
        code: Annotated[str, Query(description="Authorization code")],
        state: Annotated[str | None, Query(description="State parameter")] = None,
        error: Annotated[str | None, Query(description="Error code")] = None,
    ) -> ResponseModel[TokenResponse] | RedirectResponse:
        """Handle Google OAuth callback."""
        if error:
            logger.warning("google_oauth_error", error=error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {error}",
            )

        # Validate authorization code format (defense in depth)
        if not OAUTH_CODE_PATTERN.match(code):
            logger.warning(
                "oauth_callback_invalid_code_format",
                code_length=len(code),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code format",
            )

        # Validate CSRF state (P0 security fix)
        if not state:
            logger.warning("oauth_callback_missing_state")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter",
            )

        # Atomically get and delete state (one-time use)
        # Get state store lazily to ensure Redis is connected after startup()
        state_store = get_state_store()
        stored_state = await state_store.get_and_delete(f"oauth_state:{state}")
        if stored_state is None:
            # SECURITY FIX: Add diagnostic info for multi-instance deployments
            from identity_plan_kit.shared.state_store import get_state_store_manager  # noqa: PLC0415, I001

            manager = get_state_store_manager()
            backend_type = manager.backend_type if manager.is_initialized else "unknown"
            logger.warning(
                "oauth_callback_invalid_state",
                backend_type=backend_type,
                hint="If running multiple instances, ensure Redis is configured (IPK_REDIS_URL)"
                if backend_type == "memory"
                else None,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter",
            )

        # SECURITY FIX: Validate additional entropy (defense-in-depth)
        # Verify user agent matches to detect potential state theft
        current_user_agent = get_user_agent(request) or ""
        current_ua_hash = hashlib.sha256(current_user_agent.encode()).hexdigest()[:16]
        stored_ua_hash = stored_state.get("ua_hash")

        if stored_ua_hash and stored_ua_hash != current_ua_hash:
            # SECURITY FIX: Configurable user-agent mismatch handling
            logger.warning(
                "oauth_callback_user_agent_mismatch",
                stored_ua_hash=stored_ua_hash,
                current_ua_hash=current_ua_hash,
                strict_mode=config.oauth_strict_ua_verification,
            )
            if config.oauth_strict_ua_verification:
                # In strict mode, block the request for high-security environments
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security verification failed. Please try logging in again.",
                )

        kit = request.app.state.identity_plan_kit
        auth_service = kit.auth_service

        try:
            _user, access_token, refresh_token = await auth_service.authenticate_google(
                code=code,
                user_agent=get_user_agent(request),
                ip_address=get_client_ip(request, trust_proxy=config.trust_proxy_headers),
            )
        except OAuthError as e:
            logger.exception("google_oauth_failed", error=str(e), provider="google")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. Please try again.",
            ) from None
        except UserInactiveError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            ) from None

        # Check if we need to redirect to frontend
        redirect_url = stored_state.get("redirect_url")
        if redirect_url:
            # Create redirect response and set cookies on it
            redirect_response = RedirectResponse(
                url=redirect_url,
                status_code=status.HTTP_302_FOUND,
            )
            _set_auth_cookies(redirect_response, access_token, refresh_token, config)
            return redirect_response

        # Set tokens in cookies
        _set_auth_cookies(response, access_token, refresh_token, config)

        return ResponseModel.ok(
            data=TokenResponse(
                access_token=access_token,
                token_type="bearer",  # noqa: S106
                expires_in=config.access_token_expire_minutes * 60,
            )
        )

    @router.post(
        "/refresh",
        response_model=ResponseModel[TokenResponse],
        summary="Refresh tokens",
        description="Get new access token using refresh token",
    )
    @rate_limiter.limit(config.rate_limit_refresh)
    async def refresh_tokens(
        request: Request,
        response: Response,
        refresh_token: Annotated[
            str | None,
            Cookie(alias="refresh_token", description="Refresh token"),
        ] = None,
    ) -> ResponseModel[TokenResponse]:
        """Refresh access token."""
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not provided",
            )

        kit = request.app.state.identity_plan_kit
        auth_service = kit.auth_service

        try:
            _user, access_token, new_refresh_token = await auth_service.refresh_tokens(
                refresh_token=refresh_token,
                user_agent=get_user_agent(request),
                ip_address=get_client_ip(request, trust_proxy=config.trust_proxy_headers),
            )
        except TokenExpiredError:
            _clear_auth_cookies(response, config)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            ) from None
        except TokenInvalidError:
            _clear_auth_cookies(response, config)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from None
        except UserInactiveError:
            _clear_auth_cookies(response, config)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            ) from None

        # Update cookies with new tokens
        _set_auth_cookies(response, access_token, new_refresh_token, config)

        return ResponseModel.ok(
            data=TokenResponse(
                access_token=access_token,
                token_type="bearer",  # noqa: S106
                expires_in=config.access_token_expire_minutes * 60,
            )
        )

    @router.post(
        "/logout",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Logout",
        description="Logout current session or all sessions",
    )
    @rate_limiter.limit(config.rate_limit_logout)
    async def logout(
        request: Request,
        response: Response,
        user: CurrentUser,
        everywhere: bool = False,
        refresh_token: Annotated[
            str | None,
            Cookie(alias="refresh_token"),
        ] = None,
    ) -> None:
        """Logout user."""
        kit = request.app.state.identity_plan_kit
        auth_service = kit.auth_service

        await auth_service.logout(
            user_id=user.id,
            refresh_token=refresh_token,
            everywhere=everywhere,
        )

        _clear_auth_cookies(response, config)

    @router.get(
        "/me",
        response_model=ResponseModel[UserResponse],
        summary="Get current user",
        description="Get information about the authenticated user",
    )
    @rate_limiter.limit(config.rate_limit_profile)
    async def get_me(request: Request, user: CurrentUser) -> ResponseModel[UserResponse]:
        """Get current authenticated user."""
        return ResponseModel.ok(
            data=UserResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                picture_url=user.picture_url,
                role_code=user.role_code,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
            )
        )

    @router.get(
        "/profile",
        response_model=ResponseModel[ProfileResponse],
        summary="Get user profile",
        description="Get complete user profile including role, permissions, and current plan",
    )
    @rate_limiter.limit(config.rate_limit_profile)
    async def get_profile(request: Request, user: CurrentUser) -> ResponseModel[ProfileResponse]:
        """Get complete user profile with permissions and plan."""
        kit = request.app.state.identity_plan_kit

        # Get user role-based permissions
        user_permissions = await kit.rbac_service.get_user_permissions(
            user_id=user.id,
            role_id=user.role_id,
        )

        # Get user plan with full details in a single optimized query
        plan_info = None
        result = await kit.plan_service.get_user_plan_with_details(user.id)
        if result:
            user_plan, plan = result
            plan_info = PlanInfoResponse(
                code=plan.code,
                name=plan.name,
                started_at=user_plan.started_at,
                ends_at=user_plan.ends_at,
                is_active=user_plan.is_active,
                permissions=sorted(plan.permissions),
            )

        return ResponseModel.ok(
            data=ProfileResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                picture_url=user.picture_url,
                role_code=user.role_code,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                user_permissions=sorted(user_permissions),
                plan=plan_info,
            )
        )

    @router.patch(
        "/profile",
        response_model=ResponseModel[UserResponse],
        summary="Update user profile",
        description="Update current user's display name and/or profile picture",
    )
    @rate_limiter.limit(config.rate_limit_profile)
    async def update_profile(
        request: Request,  # Required for rate limiter
        user: CurrentUser,
        body: UpdateProfileRequest,
    ) -> ResponseModel[UserResponse]:
        """Update user profile (display_name, picture_url)."""
        # Check if at least one field is being updated
        if body.display_name is None and body.picture_url is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field (display_name or picture_url) must be provided",
            )

        kit = request.app.state.identity_plan_kit
        auth_service = kit.auth_service

        # Handle picture_url: empty string means clear, None means don't update
        # Use ellipsis (...) as sentinel to indicate "not provided"
        picture_url_arg = ...  # type: ignore[assignment]
        if body.picture_url is not None:
            # Empty string means clear the picture
            picture_url_arg = body.picture_url if body.picture_url else None

        updated_user = await auth_service.update_profile(
            user_id=user.id,
            display_name=body.display_name,
            picture_url=picture_url_arg,
        )

        return ResponseModel.ok(
            data=UserResponse(
                id=updated_user.id,
                email=updated_user.email,
                display_name=updated_user.display_name,
                picture_url=updated_user.picture_url,
                role_code=updated_user.role_code,
                is_active=updated_user.is_active,
                is_verified=updated_user.is_verified,
                created_at=updated_user.created_at,
            )
        )

    return router


def _validate_redirect_url(
    redirect_url: str,
    config: IdentityPlanKitConfig,
) -> str | None:
    """
    Validate redirect URL against allowed prefixes to prevent open redirect attacks.

    Args:
        redirect_url: The URL to validate
        config: Configuration with allowed redirect URL prefixes

    Returns:
        The validated URL if allowed, None otherwise
    """
    if not config.oauth_allowed_redirect_urls:
        # No allowed URLs configured - reject all redirects
        logger.warning(
            "oauth_redirect_url_rejected",
            reason="no_allowed_urls_configured",
            redirect_url=redirect_url[:100],  # Truncate for logging
        )
        return None

    # Check if the redirect URL starts with any allowed prefix
    for allowed_prefix in config.oauth_allowed_redirect_urls:
        if redirect_url.startswith(allowed_prefix):
            return redirect_url

    logger.warning(
        "oauth_redirect_url_rejected",
        reason="not_in_allowed_list",
        redirect_url=redirect_url[:100],
    )
    return None


def _set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    config: IdentityPlanKitConfig,
) -> None:
    """Set authentication cookies."""
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=config.access_token_expire_minutes * 60,
        httponly=True,
        secure=config.cookie_secure,
        samesite=config.cookie_samesite,
        domain=config.cookie_domain,
    )

    # Refresh token cookie (longer lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=config.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=config.cookie_secure,
        samesite=config.cookie_samesite,
        domain=config.cookie_domain,
        path=f"{config.auth_prefix}/refresh",  # Only sent to refresh endpoint
    )


def _clear_auth_cookies(
    response: Response,
    config: IdentityPlanKitConfig,
) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(
        key="access_token",
        domain=config.cookie_domain,
    )
    response.delete_cookie(
        key="refresh_token",
        domain=config.cookie_domain,
        path=f"{config.auth_prefix}/refresh",
    )
