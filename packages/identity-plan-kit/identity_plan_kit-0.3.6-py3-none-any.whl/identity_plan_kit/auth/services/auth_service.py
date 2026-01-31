"""Authentication service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.auth.domain.exceptions import (
    PasswordValidationError,
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)
from identity_plan_kit.auth.repositories.token_repo import RefreshTokenRepository
from identity_plan_kit.auth.services.oauth_service import GoogleOAuthService
from identity_plan_kit.auth.uow import AuthUnitOfWork
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.shared.audit import (
    audit_token_refreshed,
    audit_token_reuse_detected,
    audit_user_authenticated,
    audit_user_deactivated,
    audit_user_logout,
    audit_user_registered,
)
from identity_plan_kit.shared.constants import (
    USER_DISPLAY_NAME_MAX_LENGTH,
    USER_PICTURE_URL_MAX_LENGTH,
)
from identity_plan_kit.shared.lockout import AccountLockedError, LockoutConfig, LockoutManager
from identity_plan_kit.shared.logging import get_logger
from identity_plan_kit.shared.security import (
    TokenExpiredError as SecurityTokenExpiredError,
)
from identity_plan_kit.shared.security import (
    TokenInvalidError as SecurityTokenInvalidError,
)
from identity_plan_kit.shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_from_cache,
    encrypt_for_cache,
    hash_password,
    hash_token,
    verify_password,
)
from identity_plan_kit.shared.state_store import get_state_store

if TYPE_CHECKING:
    from identity_plan_kit.shared.registry import ExtensionConfig

logger = get_logger(__name__)

# Key prefix for refresh idempotency tracking
REFRESH_IDEMPOTENCY_PREFIX = "token_refresh:"

# Re-export for convenience
__all__ = ["AccountLockedError", "AuthService"]


class AuthService:
    """Service for authentication operations."""

    def __init__(
        self,
        config: IdentityPlanKitConfig,
        session_factory: async_sessionmaker[AsyncSession],
        lockout_config: LockoutConfig | None = None,
        extension_config: ExtensionConfig | None = None,
    ) -> None:
        """
        Initialize AuthService.

        Args:
            config: Library configuration
            session_factory: SQLAlchemy async session factory
            lockout_config: Optional lockout configuration for brute-force protection
            extension_config: Optional extension configuration for custom model/entity classes
        """
        self._config = config
        self._session_factory = session_factory
        self._google_oauth = GoogleOAuthService(config)
        self._secret_key = config.secret_key.get_secret_value()
        self._algorithm = config.algorithm
        self._lockout_config = lockout_config or LockoutConfig()
        self._lockout_manager: LockoutManager | None = None
        self._extension_config = extension_config

    def _create_uow(
        self,
        session: AsyncSession | None = None,
    ) -> AuthUnitOfWork:
        """
        Create a new Unit of Work instance.

        Args:
            session: Optional external session for transaction participation.
                If provided, the UoW will use this session instead of creating a new one.
        """
        return AuthUnitOfWork(
            self._session_factory,
            session=session,
            extension_config=self._extension_config,
        )

    def _get_lockout_manager(self) -> LockoutManager:
        """Get or create lockout manager (lazy initialization)."""
        if self._lockout_manager is None:
            self._lockout_manager = LockoutManager(
                get_state_store(),
                self._lockout_config,
            )
        return self._lockout_manager

    @property
    def google_oauth(self) -> GoogleOAuthService:
        """Get Google OAuth service."""
        return self._google_oauth

    async def get_user_from_token(
        self,
        token: str,
        include_role: bool = True,
    ) -> User:
        """
        Get user from access token.

        Args:
            token: JWT access token
            include_role: If True, eagerly load the user's role (default: True).
                Set to False to skip the role query when role info is not needed,
                reducing database queries for better performance.

        Returns:
            User entity

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
            UserNotFoundError: If user doesn't exist
            UserInactiveError: If user is inactive
        """
        try:
            payload = decode_token(
                token,
                self._secret_key,
                self._algorithm,
            )
        except SecurityTokenExpiredError as e:
            raise TokenExpiredError() from e
        except SecurityTokenInvalidError as e:
            raise TokenInvalidError() from e

        # Verify token type
        if payload.get("type") != "access":
            raise TokenInvalidError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalidError("Missing user ID in token")

        async with self._create_uow() as uow:
            user = await uow.users.get_by_id(UUID(user_id), include_role=include_role)

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise UserInactiveError()

            return user

    async def authenticate_google(
        self,
        code: str,
        default_role_code: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, str, str]:
        """
        Authenticate user via Google OAuth.

        Creates new user if not exists, or links Google account if email exists.
        Includes lockout protection against brute-force attacks.

        Args:
            code: Authorization code from Google
            default_role_code: Role code for new users (uses config default if None)
            user_agent: Client user agent
            ip_address: Client IP address

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            AccountLockedError: If too many failed attempts
            UserInactiveError: If user account is deactivated
        """
        # Use config default if not specified
        role_code = default_role_code or self._config.default_role_code
        plan_code = self._config.default_plan_code
        lockout = self._get_lockout_manager()

        # Get user info from Google (this validates the OAuth code)
        # We don't know email yet, so we check lockout by IP first
        if ip_address:
            await lockout.check_lockout(f"ip:{ip_address}", ip_address)

        try:
            google_user = await self._google_oauth.authenticate(code)
        except Exception as e:
            # Log the OAuth failure for debugging (without exposing code)
            logger.warning(
                "google_oauth_authentication_failed",
                error_type=type(e).__name__,
                ip_address=ip_address,
            )
            # Record failed attempt (OAuth code was invalid/expired)
            if ip_address:
                await lockout.record_failure(
                    f"ip:{ip_address}",
                    ip_address,
                    reason="oauth_code_invalid",
                    user_agent=user_agent,
                )
            raise

        # Now we have the email, check lockout for this specific user
        await lockout.check_lockout(google_user.email, ip_address)

        async with self._create_uow() as uow:
            # Look up role and plan by code
            role = await uow.rbac.get_role_by_code(role_code)
            if role is None:
                raise ValueError(f"Default role '{role_code}' not found")

            plan = await uow.plans.get_plan_by_code(plan_code)
            if plan is None:
                raise ValueError(f"Default plan '{plan_code}' not found")

            # Determine display_name: use Google's name, fallback to email prefix
            # Handle edge cases: empty string, None, or too long
            display_name = google_user.name
            if not display_name or not display_name.strip():
                # Fallback to email prefix if name is empty/whitespace
                display_name = google_user.email.split("@")[0]
            else:
                display_name = display_name.strip()

            # Truncate if too long (max USER_DISPLAY_NAME_MAX_LENGTH chars for database column)
            if len(display_name) > USER_DISPLAY_NAME_MAX_LENGTH:
                display_name = display_name[:USER_DISPLAY_NAME_MAX_LENGTH]

            # Handle picture_url: truncate if too long (max USER_PICTURE_URL_MAX_LENGTH chars)
            picture_url = google_user.picture
            if picture_url and len(picture_url) > USER_PICTURE_URL_MAX_LENGTH:
                # URL is too long, skip it rather than truncate (would be invalid)
                picture_url = None

            # Race-condition safe: get existing user or create new one
            # Note: display_name and picture_url only used for NEW users
            # Existing users keep their current profile (don't overwrite on re-login)
            user, created = await uow.users.get_or_create_with_provider(
                email=google_user.email,
                role_id=role.id,
                provider_code="google",
                external_user_id=google_user.id,
                display_name=display_name,
                picture_url=picture_url,
                is_verified=google_user.email_verified,
            )

            if created:
                # Create default plan for new user (atomic with user creation)
                await uow.plans.create_user_plan(
                    user_id=user.id,
                    plan_id=plan.id,
                )
                logger.info(
                    "user_registered",
                    user_id=str(user.id),
                    provider="google",
                    default_plan=plan_code,
                )
                # Audit: User registration
                audit_user_registered(
                    user_id=user.id,
                    email=user.email,
                    provider="google",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            else:
                logger.info(
                    "user_authenticated_existing",
                    user_id=str(user.id),
                    provider="google",
                )

            if not user.is_active:
                raise UserInactiveError()

            # Generate tokens
            access_token, refresh_token = await self._create_and_store_tokens(
                user=user,
                token_repo=uow.tokens,
                user_agent=user_agent,
                ip_address=ip_address,
            )

            # UoW commits automatically on successful exit
            logger.info(
                "user_authenticated",
                user_id=str(user.id),
                provider="google",
            )

            # Audit: Successful authentication
            audit_user_authenticated(
                user_id=user.id,
                email=user.email,
                provider="google",
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Clear any failed attempts on successful auth
            await lockout.clear_failures(google_user.email, ip_address)
            if ip_address:
                await lockout.clear_failures(f"ip:{ip_address}", ip_address)

            return user, access_token, refresh_token

    async def refresh_tokens(
        self,
        refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, str, str]:
        """
        Refresh access token using refresh token.

        Implements token rotation for security with idempotency support.

        P2 FIX: Added idempotency to handle network retries gracefully.
        If the same refresh token is used twice within 30 seconds, the second
        request returns the cached tokens instead of failing with "Token revoked".

        Args:
            refresh_token: Current refresh token
            user_agent: Client user agent
            ip_address: Client IP address

        Returns:
            Tuple of (user, new_access_token, new_refresh_token)

        Raises:
            TokenExpiredError: If refresh token has expired
            TokenInvalidError: If refresh token is invalid
        """
        # Decode token (without expiry check - we check manually)
        try:
            payload = decode_token(
                refresh_token,
                self._secret_key,
                self._algorithm,
                verify_exp=False,
            )
        except SecurityTokenInvalidError as e:
            raise TokenInvalidError() from e

        if payload.get("type") != "refresh":
            raise TokenInvalidError("Invalid token type")

        # P2 FIX: Check idempotency cache for recent refresh of this token
        # SECURITY FIX: Don't store full tokens in cache - only store reference
        token_hash = hash_token(refresh_token)
        idempotency_key = f"{REFRESH_IDEMPOTENCY_PREFIX}{token_hash}"
        state_store = get_state_store()

        cached_result = await state_store.get(idempotency_key)
        if cached_result is not None and isinstance(cached_result, dict):
            # This token was recently refreshed - return the SAME tokens from cache
            # to ensure idempotent behavior (client gets identical response on retry)
            cached_data: dict[str, str] = cached_result  # type: ignore[assignment]
            logger.debug(
                "token_refresh_idempotency_hit",
                user_id=cached_data.get("user_id"),
            )

            # Verify user is still valid
            async with self._create_uow() as uow:
                user = await uow.users.get_by_id(UUID(cached_data["user_id"]))
                if user is None:
                    raise UserNotFoundError()
                if not user.is_active:
                    raise UserInactiveError()

                # Return the EXACT same tokens that were generated on first request
                # This ensures true idempotency - client gets identical response
                # SECURITY: Tokens are encrypted in cache - decrypt them
                encrypted_access = cached_data.get("access_token_enc")
                encrypted_refresh = cached_data.get("refresh_token_enc")

                if encrypted_access and encrypted_refresh:
                    cached_access = decrypt_from_cache(encrypted_access, self._secret_key)
                    cached_refresh = decrypt_from_cache(encrypted_refresh, self._secret_key)

                    if cached_access and cached_refresh:
                        return user, cached_access, cached_refresh

                    # Decryption failed - possible key rotation or tampering
                    logger.warning(
                        "token_refresh_idempotency_decryption_failed",
                        user_id=str(user.id),
                    )
                else:
                    # Fallback: cache entry malformed, proceed with normal flow
                    logger.warning(
                        "token_refresh_idempotency_cache_malformed",
                        user_id=str(user.id),
                    )

        async with self._create_uow() as uow:
            # Find token by hash with row lock (prevents race condition)
            stored_token = await uow.tokens.get_by_hash(token_hash, for_update=True)

            if stored_token is None:
                logger.warning("refresh_token_not_found")
                raise TokenInvalidError("Token not found")

            if stored_token.is_expired:
                logger.warning(
                    "refresh_token_expired",
                    user_id=str(stored_token.user_id),
                )
                raise TokenExpiredError()

            if stored_token.is_revoked:
                # SECURITY: Token reuse detected - potential token theft!
                # This happens when:
                # 1. Attacker stole a refresh token
                # 2. Either attacker or legitimate user used it first
                # 3. The other party is now trying to use the already-revoked token
                #
                # Response: Revoke ALL tokens and deactivate user for safety
                logger.critical(
                    "refresh_token_reuse_detected",
                    user_id=str(stored_token.user_id),
                    original_ip=stored_token.ip_address,
                    original_user_agent=stored_token.user_agent,
                    current_ip=ip_address,
                    current_user_agent=user_agent,
                )

                # Audit: Critical security event
                audit_token_reuse_detected(
                    user_id=stored_token.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    original_ip=stored_token.ip_address,
                    original_user_agent=stored_token.user_agent,
                )

                # Revoke all tokens for this user
                await uow.tokens.revoke_all_for_user(stored_token.user_id)

                # P1 SECURITY FIX: Deactivate user to prevent further access
                # User must contact support to reactivate
                # Use FOR UPDATE to prevent race condition with concurrent requests
                user = await uow.users.get_by_id(stored_token.user_id, for_update=True)
                if user and user.is_active:
                    await uow.users.deactivate(
                        stored_token.user_id,
                        reason="token_theft_suspected",
                    )
                    audit_user_deactivated(
                        user_id=stored_token.user_id,
                        reason="Automatic deactivation due to refresh token reuse (potential theft)",
                    )

                raise TokenInvalidError("Token has been revoked - account secured")

            # Get user with FOR UPDATE lock to prevent race condition
            # where user is deactivated between this check and token creation
            # Without this, a deactivated user could get new tokens if the
            # deactivation happens after this read but before the commit
            user = await uow.users.get_by_id(stored_token.user_id, for_update=True)
            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise UserInactiveError()

            # Revoke old token (rotation)
            await uow.tokens.revoke(stored_token.id)

            # Generate new tokens
            access_token, new_refresh_token = await self._create_and_store_tokens(
                user=user,
                token_repo=uow.tokens,
                user_agent=user_agent,
                ip_address=ip_address,
            )

            # UoW commits automatically on successful exit
            logger.info(
                "tokens_refreshed",
                user_id=str(user.id),
            )

            # Audit: Token refresh
            audit_token_refreshed(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            # Cache the actual tokens for idempotency
            # This ensures retries get the EXACT same tokens (true idempotency)
            # SECURITY: Encrypt tokens before storing in cache to prevent
            # exposure if cache (Redis) is compromised. Uses Fernet encryption
            # with key derived from secret_key.
            await state_store.set(
                idempotency_key,
                {
                    "user_id": str(user.id),
                    "access_token_enc": encrypt_for_cache(access_token, self._secret_key),
                    "refresh_token_enc": encrypt_for_cache(new_refresh_token, self._secret_key),
                },
                ttl_seconds=self._config.token_refresh_idempotency_ttl_seconds,
            )

            return user, access_token, new_refresh_token

    async def logout(
        self,
        user_id: UUID,
        refresh_token: str | None = None,
        everywhere: bool = False,
        ip_address: str | None = None,
    ) -> None:
        """
        Logout user by revoking tokens.

        Args:
            user_id: User UUID
            refresh_token: Current refresh token to revoke
            everywhere: If True, revoke all sessions
            ip_address: Client IP address (for audit logging)
        """
        tokens_revoked = 0
        state_store = get_state_store()

        async with self._create_uow() as uow:
            if everywhere:
                tokens_revoked = await uow.tokens.revoke_all_for_user(user_id)
                logger.info(
                    "user_logged_out_everywhere",
                    user_id=str(user_id),
                    tokens_revoked=tokens_revoked,
                )
            elif refresh_token:
                token_hash = hash_token(refresh_token)
                stored_token = await uow.tokens.get_by_hash(token_hash)
                if stored_token:
                    await uow.tokens.revoke(stored_token.id)
                    tokens_revoked = 1
                    logger.info(
                        "user_logged_out",
                        user_id=str(user_id),
                    )

                    # P1 FIX: Clear idempotency cache for this token to prevent
                    # false token theft detection if a stale refresh request arrives
                    # after logout. Without this, a network retry could see the
                    # revoked token and incorrectly trigger theft detection.
                    idempotency_key = f"{REFRESH_IDEMPOTENCY_PREFIX}{token_hash}"
                    await state_store.delete(idempotency_key)

            # UoW commits automatically on successful exit

        # Audit: Logout event
        audit_user_logout(
            user_id=user_id,
            everywhere=everywhere,
            tokens_revoked=tokens_revoked,
            ip_address=ip_address,
        )

    async def _create_and_store_tokens(
        self,
        user: User,
        token_repo: RefreshTokenRepository,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, str]:
        """
        Create access and refresh tokens for user.

        Args:
            user: User entity
            token_repo: Token repository (from UoW)
            user_agent: Client user agent
            ip_address: Client IP address

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expires_delta=timedelta(minutes=self._config.access_token_expire_minutes),
        )

        # Refresh token
        refresh_token, token_hash = create_refresh_token(
            data={"sub": str(user.id)},
            secret_key=self._secret_key,
            algorithm=self._algorithm,
            expires_delta=timedelta(days=self._config.refresh_token_expire_days),
        )

        # Store refresh token hash
        expires_at = datetime.now(UTC) + timedelta(days=self._config.refresh_token_expire_days)
        await token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return access_token, refresh_token

    # =========================================================================
    # PROFILE MANAGEMENT
    # =========================================================================

    async def update_profile(
        self,
        user_id: UUID,
        display_name: str | None = None,
        picture_url: str | None = ...,  # Use ... as sentinel
    ) -> User:
        """
        Update user profile (display_name, picture_url).

        Args:
            user_id: User UUID
            display_name: New display name (1-100 chars)
            picture_url: New picture URL (max 500 chars, or None to clear)

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        async with self._create_uow() as uow:
            user = await uow.users.update_profile(
                user_id=user_id,
                display_name=display_name,
                picture_url=picture_url,
            )

            if user is None:
                raise UserNotFoundError()

            return user

    # =========================================================================
    # PASSWORD MANAGEMENT
    # =========================================================================

    # Minimum password length for security
    MIN_PASSWORD_LENGTH = 8

    async def set_user_password(
        self,
        user_id: UUID,
        password: str,
        *,
        require_admin_role: bool = True,
    ) -> bool:
        """
        Set password for a user (for admin panel access).

        SECURITY NOTES:
        - Validates password meets minimum requirements
        - Hashes password using bcrypt before storage
        - Uses database-level locking to prevent race conditions
        - Never logs or stores plain passwords
        - By default, only allows setting password for admin users

        Args:
            user_id: User UUID
            password: Plain text password (will be hashed)
            require_admin_role: If True, only set password for users with 'admin' role

        Returns:
            True if password was set successfully

        Raises:
            UserNotFoundError: If user does not exist
            UserInactiveError: If user is inactive
            PasswordValidationError: If password doesn't meet requirements
            AuthorizationError: If require_admin_role=True and user is not admin
        """
        # Validate password strength (don't log the actual password!)
        self._validate_password(password)

        async with self._create_uow() as uow:
            # Get user with FOR UPDATE lock to prevent race conditions
            # This ensures user isn't deactivated between this check and password set
            user = await uow.users.get_by_id(user_id, for_update=True)

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise UserInactiveError()

            # Security: Only allow password for admin users by default
            if require_admin_role and user.role_code != "admin":
                raise PasswordValidationError(
                    "Password can only be set for users with admin role"
                )

            # Hash password using bcrypt (via passlib)
            # SECURITY: Password is hashed here, never stored in plain text
            hashed = hash_password(password)

            # Set password hash with race condition protection
            success = await uow.users.set_password_hash(user_id, hashed)

            if success:
                logger.info(
                    "user_password_set",
                    user_id=str(user_id),
                    role=user.role_code,
                )

            # UoW commits automatically on successful exit
            return success

    async def verify_user_password(
        self,
        user_id: UUID,
        password: str,
    ) -> bool:
        """
        Verify a user's password.

        SECURITY NOTES:
        - Uses constant-time comparison to prevent timing attacks
        - Returns False for users without passwords (OAuth-only)
        - Never logs password attempts

        Args:
            user_id: User UUID
            password: Plain text password to verify

        Returns:
            True if password is correct, False otherwise

        Raises:
            UserNotFoundError: If user does not exist
        """
        async with self._create_uow() as uow:
            # Get the model directly to access password_hash
            # (not exposed in domain entity for security)
            from identity_plan_kit.auth.models.user import UserModel
            from sqlalchemy import select

            stmt = select(UserModel).where(UserModel.id == user_id)
            result = await uow.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise UserNotFoundError()

            if not model.password_hash:
                # User has no password (OAuth-only)
                return False

            # Verify using bcrypt (constant-time comparison)
            return verify_password(password, model.password_hash)

    async def clear_user_password(
        self,
        user_id: UUID,
    ) -> bool:
        """
        Remove password from user (revert to OAuth-only).

        Args:
            user_id: User UUID

        Returns:
            True if password was cleared

        Raises:
            UserNotFoundError: If user does not exist
        """
        async with self._create_uow() as uow:
            user = await uow.users.get_by_id(user_id)

            if user is None:
                raise UserNotFoundError()

            success = await uow.users.clear_password_hash(user_id)

            if success:
                logger.info(
                    "user_password_cleared",
                    user_id=str(user_id),
                )

            return success

    def _validate_password(self, password: str) -> None:
        """
        Validate password meets security requirements.

        Current requirements:
        - Minimum 8 characters

        Args:
            password: Plain text password to validate

        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise PasswordValidationError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
            )
