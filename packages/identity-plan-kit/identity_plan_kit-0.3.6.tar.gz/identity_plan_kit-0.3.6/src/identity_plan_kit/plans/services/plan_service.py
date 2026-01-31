"""Plan service for subscription and usage management."""

from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.plans.cache.plan_cache import PlanCache
from identity_plan_kit.plans.cache.user_plan_cache import UserPlanCache
from identity_plan_kit.plans.domain.entities import Feature, Plan, UserPlan
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    FeatureNotFoundError,
    InvalidCustomLimitsError,
    InvalidPlanDatesError,
    PlanAuthorizationError,
    PlanExpiredError,
    PlanNotFoundError,
    QuotaExceededError,
    UserPlanNotFoundError,
)
from identity_plan_kit.plans.dto.usage import UsageInfo
from identity_plan_kit.plans.repositories.usage_repo import QuotaExceededInRepoError
from identity_plan_kit.plans.uow import PlansUnitOfWork
from identity_plan_kit.shared.logging import get_logger
from identity_plan_kit.shared.state_store import StateStoreManager

logger = get_logger(__name__)

# Type for authorization callback: (operation, target_user_id, caller_context) -> bool
AuthorizationCallback = Callable[[str, UUID, dict[str, Any] | None], Awaitable[bool]]

# Prefix for quota idempotency keys in state store
QUOTA_IDEMPOTENCY_PREFIX = "quota_idem:"

# Default plan cache TTL (5 minutes)
DEFAULT_PLAN_CACHE_TTL_SECONDS = 300


class PlanService:
    """Service for plan and usage operations.

    Plan management methods (assign_plan, cancel_plan, extend_plan, update_plan_limits,
    reset_usage) are **privileged operations** that modify user subscriptions.

    **SECURITY: Authorization Responsibility**

    This library does NOT enforce authorization by default. The calling application
    MUST verify that the caller is authorized before invoking plan management methods:

    - **Webhook handlers**: Verify webhook signatures (e.g., Stripe signature verification)
    - **Admin endpoints**: Verify the caller has admin role/permissions
    - **User endpoints**: Verify the target user_id matches the authenticated user

    You can optionally configure an ``authorization_callback`` to enforce authorization
    at the library level::

        async def check_authorization(
            operation: str,
            target_user_id: UUID,
            context: dict | None
        ) -> bool:
            # operation: "assign_plan", "cancel_plan", etc.
            # target_user_id: the user being modified
            # context: optional dict with caller info
            caller = context.get("caller_user_id") if context else None
            if caller == target_user_id:
                return True  # Users can modify their own plans
            if context.get("is_admin"):
                return True  # Admins can modify any plan
            if context.get("is_webhook"):
                return True  # Verified webhooks are authorized
            return False

        kit = IdentityPlanKit(
            config,
            authorization_callback=check_authorization
        )

    When a callback is configured, plan management methods will raise
    ``PlanAuthorizationError`` if the callback returns False.
    """

    def __init__(
        self,
        config: IdentityPlanKitConfig,
        session_factory: async_sessionmaker[AsyncSession],
        plan_cache_ttl_seconds: int = DEFAULT_PLAN_CACHE_TTL_SECONDS,
        user_plan_cache_ttl_seconds: int = DEFAULT_PLAN_CACHE_TTL_SECONDS,
        redis_url: str | None = None,
        require_redis: bool = False,
        state_store_manager: StateStoreManager | None = None,
        authorization_callback: AuthorizationCallback | None = None,
    ) -> None:
        self._config = config
        self._session_factory = session_factory
        self._plan_cache = PlanCache(
            ttl_seconds=plan_cache_ttl_seconds,
            redis_url=redis_url,
            require_redis=require_redis,
        )
        self._user_plan_cache = UserPlanCache(
            ttl_seconds=user_plan_cache_ttl_seconds,
            redis_url=redis_url,
            require_redis=require_redis,
        )
        self._state_store_manager = state_store_manager
        self._authorization_callback = authorization_callback

    async def startup(self) -> None:
        """
        Start the plan service.

        Connects to Redis if configured for distributed caching.
        Call this during application startup.
        """
        await self._plan_cache.connect()
        await self._user_plan_cache.connect()
        logger.info("plan_service_started")

    async def shutdown(self) -> None:
        """
        Shutdown the plan service.

        Disconnects from Redis if configured.
        Call this during application shutdown.
        """
        await self._plan_cache.disconnect()
        await self._user_plan_cache.disconnect()
        logger.info("plan_service_stopped")

    def _create_uow(
        self,
        session: AsyncSession | None = None,
    ) -> PlansUnitOfWork:
        """
        Create a new Unit of Work instance.

        Args:
            session: Optional external session for transaction participation.
        """
        return PlansUnitOfWork(self._session_factory, session=session)

    async def _check_authorization(
        self,
        operation: str,
        target_user_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Check if the operation is authorized.

        Args:
            operation: Name of the operation (e.g., "assign_plan")
            target_user_id: User ID being modified
            context: Optional context dict with caller info

        Raises:
            PlanAuthorizationError: If authorization callback returns False
        """
        if self._authorization_callback is None:
            # No callback configured - authorization is caller's responsibility
            return

        is_authorized = await self._authorization_callback(
            operation, target_user_id, context
        )

        if not is_authorized:
            caller_id = context.get("caller_user_id") if context else None
            caller_id_str = str(caller_id) if caller_id else None
            logger.warning(
                "plan_operation_unauthorized",
                operation=operation,
                target_user_id=str(target_user_id),
                caller_user_id=caller_id_str,
            )
            raise PlanAuthorizationError(
                message=f"Not authorized to perform '{operation}' on user {target_user_id}",
                operation=operation,
                target_user_id=str(target_user_id),
                caller_user_id=caller_id_str,
            )

    async def get_user_plan(
        self,
        user_id: UUID,
        session: AsyncSession | None = None,
    ) -> UserPlan:
        """
        Get user's active plan.

        Args:
            user_id: User UUID
            session: Optional external session for transaction participation

        Returns:
            UserPlan entity

        Raises:
            UserPlanNotFoundError: If user has no active plan
        """
        async with self._create_uow(session=session) as uow:
            user_plan = await uow.plans.get_user_active_plan(user_id)

            if user_plan is None:
                raise UserPlanNotFoundError()

            return user_plan

    async def get_plan(self, plan_code: str) -> Plan:
        """
        Get plan by code.

        Results are cached to reduce database queries.

        Args:
            plan_code: Plan code

        Returns:
            Plan entity
        """
        # Check cache first
        cached = await self._plan_cache.get(plan_code)
        if cached is not None:
            return cached

        # Get fetch timestamp BEFORE DB query for stale write prevention
        fetch_ts = self._plan_cache.get_fetch_timestamp()

        async with self._create_uow() as uow:
            plan = await uow.plans.get_plan_by_code(plan_code)

            if plan is None:
                raise PlanNotFoundError(plan_code)

            # Cache result with fetch timestamp to prevent stale writes
            await self._plan_cache.set(plan_code, plan, fetched_at=fetch_ts)

            logger.debug(
                "plan_loaded",
                plan_code=plan_code,
            )

            return plan

    async def check_feature_access(
        self,
        user_id: UUID,
        feature_code: str,
        session: AsyncSession | None = None,
    ) -> bool:
        """
        Check if user has access to a feature.

        Args:
            user_id: User UUID
            feature_code: Feature code to check
            session: Optional external session for transaction participation

        Returns:
            True if user has access, False otherwise

        Note:
            This method does NOT swallow unexpected exceptions.
            Database errors and other infrastructure failures will propagate.
        """
        try:
            # Check user plan cache first
            cached_user_plan = await self._user_plan_cache.get(user_id)
            if cached_user_plan is not None:
                _user_plan, plan = cached_user_plan
                limit = plan.get_feature_limit(feature_code)
                return limit is not None

            async with self._create_uow(session=session) as uow:
                # Fetch from database and cache
                fetch_ts = self._user_plan_cache.get_fetch_timestamp()
                result = await uow.plans.get_user_active_plan_with_details(user_id)
                if result is None:
                    return False

                user_plan, plan = result

                # Cache the result
                await self._user_plan_cache.set(
                    user_id, user_plan, plan, fetched_at=fetch_ts
                )

                # Extract limit from already-loaded plan (no extra query needed)
                limit = plan.get_feature_limit(feature_code)
                return limit is not None

        except (UserPlanNotFoundError, FeatureNotAvailableError):
            # Expected business exceptions - user doesn't have access
            return False
        # Other exceptions (DB errors, etc.) propagate to caller

    async def check_and_consume_quota(
        self,
        user_id: UUID,
        feature_code: str,
        amount: int = 1,
        session: AsyncSession | None = None,
        idempotency_key: str | None = None,
    ) -> UsageInfo:
        """
        Check if user has quota and consume it atomically.

        P0 FIX: Uses atomic check-and-consume to prevent TOCTOU race conditions.
        Two concurrent requests cannot both pass the quota check anymore.

        **Idempotency Support:**

        When ``idempotency_key`` is provided and a state store is configured,
        this method caches successful results for the configured TTL
        (``quota_idempotency_ttl_seconds``). Duplicate requests with the same
        key within the TTL window return the cached result without consuming
        additional quota.

        This prevents double-deduction when:

        - Network timeouts cause client retries
        - Load balancers retry failed requests
        - Users accidentally double-click submit buttons

        Example::

            # Generate a unique key per logical operation
            idempotency_key = f"{user_id}:{request_id}:generate_image"

            result = await kit.plan_service.check_and_consume_quota(
                user_id=user_id,
                feature_code="ai_generation",
                amount=1,
                idempotency_key=idempotency_key,
            )

        .. note::

            The idempotency key should be unique per logical operation but
            consistent across retries. Common patterns:

            - ``{user_id}:{request_id}:{operation}`` - ties to HTTP request
            - ``{user_id}:{transaction_id}`` - ties to business transaction
            - ``{user_id}:{resource_id}:{action}`` - ties to specific action

        Args:
            user_id: User UUID
            feature_code: Feature code
            amount: Amount to consume
            session: Optional external session for transaction participation
            idempotency_key: Optional key for idempotent consumption. If provided
                and state store is configured, duplicate requests return cached
                result instead of consuming quota again.

        Returns:
            UsageInfo with updated usage

        Raises:
            UserPlanNotFoundError: If user has no active plan
            PlanExpiredError: If plan has expired
            FeatureNotAvailableError: If feature not in plan
            QuotaExceededError: If quota would be exceeded
        """
        # Check idempotency cache if key provided and state store available
        cache_key: str | None = None
        if (
            idempotency_key
            and self._state_store_manager
            and self._state_store_manager.is_initialized
            and self._config.quota_idempotency_ttl_seconds > 0
        ):
            cache_key = f"{QUOTA_IDEMPOTENCY_PREFIX}{idempotency_key}"
            try:
                cached = await self._state_store_manager.store.get(cache_key)
                if cached is not None and isinstance(cached, dict):
                    logger.debug(
                        "quota_idempotency_cache_hit",
                        idempotency_key=idempotency_key,
                        user_id=str(user_id),
                        feature=feature_code,
                    )
                    return UsageInfo(
                        feature_code=cached.get("feature_code", feature_code),
                        used=cached.get("used", 0),
                        limit=cached.get("limit", 0),
                        period=cached.get("period"),
                        remaining=cached.get("remaining", 0),
                    )
            except Exception:
                # State store errors should not block quota consumption
                logger.warning(
                    "quota_idempotency_cache_read_error",
                    idempotency_key=idempotency_key,
                    exc_info=True,
                )

        # Check user plan cache first
        cached_user_plan = await self._user_plan_cache.get(user_id)
        user_plan: UserPlan | None = None
        plan: Plan | None = None

        if cached_user_plan is not None:
            user_plan, plan = cached_user_plan
            logger.debug(
                "user_plan_cache_hit",
                user_id=str(user_id),
                plan_code=user_plan.plan_code,
            )

        async with self._create_uow(session=session) as uow:
            # If not in cache, fetch from database
            if user_plan is None or plan is None:
                fetch_ts = self._user_plan_cache.get_fetch_timestamp()
                result = await uow.plans.get_user_active_plan_with_details(user_id)
                if result is None:
                    raise UserPlanNotFoundError()

                user_plan, plan = result

                # Cache the result
                await self._user_plan_cache.set(
                    user_id, user_plan, plan, fetched_at=fetch_ts
                )

            if user_plan.is_expired:
                # Invalidate cache for expired plans
                await self._user_plan_cache.invalidate(user_id)
                raise PlanExpiredError()

            # Extract limit from already-loaded plan (no extra query needed)
            limit = plan.get_feature_limit(feature_code)
            if limit is None:
                raise FeatureNotAvailableError(feature_code, user_plan.plan_code)

            # Check for custom limit override
            custom_limit = user_plan.get_custom_limit(feature_code)
            effective_limit = custom_limit if custom_limit is not None else limit.limit

            # Atomic check-and-consume (fixes TOCTOU race condition)
            try:
                new_usage = await uow.usage.atomic_check_and_consume(
                    user_plan_id=user_plan.id,
                    feature_id=limit.feature_id,
                    amount=amount,
                    limit=effective_limit,
                    period=limit.period,
                )
            except QuotaExceededInRepoError as e:
                logger.warning(
                    "quota_exceeded",
                    user_id=str(user_id),
                    feature=feature_code,
                    used=e.current_usage,
                    limit=e.limit,
                    requested=e.requested,
                )
                raise QuotaExceededError(
                    feature_code=feature_code,
                    limit=e.limit,
                    used=e.current_usage,
                    period=limit.period.value if limit.period else None,
                ) from e

            # UoW commits automatically
            if effective_limit == -1:
                logger.debug(
                    "quota_consumed_unlimited",
                    user_id=str(user_id),
                    feature=feature_code,
                    amount=amount,
                )
                remaining = -1
            else:
                logger.info(
                    "quota_consumed",
                    user_id=str(user_id),
                    feature=feature_code,
                    amount=amount,
                    used=new_usage,
                    limit=effective_limit,
                )
                remaining = effective_limit - new_usage

            result = UsageInfo(
                feature_code=feature_code,
                used=new_usage,
                limit=effective_limit,
                period=limit.period.value if limit.period else None,
                remaining=remaining,
            )

            # Cache result for idempotency
            if cache_key:
                try:
                    await self._state_store_manager.store.set(
                        cache_key,
                        {
                            "feature_code": result.feature_code,
                            "used": result.used,
                            "limit": result.limit,
                            "period": result.period,
                            "remaining": result.remaining,
                        },
                        ttl_seconds=self._config.quota_idempotency_ttl_seconds,
                    )
                    logger.debug(
                        "quota_idempotency_cached",
                        idempotency_key=idempotency_key,
                        user_id=str(user_id),
                        feature=feature_code,
                        ttl=self._config.quota_idempotency_ttl_seconds,
                    )
                except Exception:
                    # State store errors should not fail the operation
                    logger.warning(
                        "quota_idempotency_cache_write_error",
                        idempotency_key=idempotency_key,
                        exc_info=True,
                    )

            return result

    async def get_usage_info(
        self,
        user_id: UUID,
        feature_code: str,
    ) -> UsageInfo:
        """
        Get current usage info for a feature.

        Args:
            user_id: User UUID
            feature_code: Feature code

        Returns:
            UsageInfo with current usage
        """
        # Check user plan cache first
        cached_user_plan = await self._user_plan_cache.get(user_id)
        user_plan: UserPlan | None = None
        plan: Plan | None = None

        if cached_user_plan is not None:
            user_plan, plan = cached_user_plan

        async with self._create_uow() as uow:
            # If not in cache, fetch from database
            if user_plan is None or plan is None:
                fetch_ts = self._user_plan_cache.get_fetch_timestamp()
                result = await uow.plans.get_user_active_plan_with_details(user_id)
                if result is None:
                    raise UserPlanNotFoundError()

                user_plan, plan = result

                # Cache the result
                await self._user_plan_cache.set(
                    user_id, user_plan, plan, fetched_at=fetch_ts
                )

            # Extract limit from already-loaded plan (no extra query needed)
            limit = plan.get_feature_limit(feature_code)
            if limit is None:
                raise FeatureNotAvailableError(feature_code, user_plan.plan_code)

            current_usage = await uow.usage.get_current_usage(
                user_plan.id,
                limit.feature_id,
                limit.period,
            )

            effective_limit = user_plan.get_custom_limit(feature_code) or limit.limit

            remaining = -1 if effective_limit == -1 else effective_limit - current_usage

            return UsageInfo(
                feature_code=feature_code,
                used=current_usage,
                limit=effective_limit,
                period=limit.period.value if limit.period else None,
                remaining=remaining,
            )

    # =========================================================================
    # Plan Management Methods (for webhook/payment integration)
    # =========================================================================

    def _validate_plan_dates(
        self,
        started_at: date | None,
        ends_at: date | None,
    ) -> None:
        """
        Validate plan date range.

        Args:
            started_at: Plan start date
            ends_at: Plan end date

        Raises:
            InvalidPlanDatesError: If dates are invalid
        """
        if started_at is not None and ends_at is not None:
            if ends_at < started_at:
                raise InvalidPlanDatesError(
                    message=f"ends_at ({ends_at}) must be after started_at ({started_at})",
                    started_at=started_at,
                    ends_at=ends_at,
                )

    def _validate_custom_limits(
        self,
        custom_limits: dict[str, Any] | None,
    ) -> None:
        """
        Validate custom limits values.

        Args:
            custom_limits: Custom limits to validate

        Raises:
            InvalidCustomLimitsError: If any limit value is invalid
        """
        if custom_limits is None:
            return

        invalid_keys: list[str] = []
        for key, value in custom_limits.items():
            if not isinstance(value, int):
                invalid_keys.append(key)
            elif value < -1:  # -1 is valid (unlimited)
                invalid_keys.append(key)

        if invalid_keys:
            raise InvalidCustomLimitsError(
                message=f"Custom limits must be integers >= -1. Invalid keys: {invalid_keys}",
                invalid_keys=invalid_keys,
            )

    async def assign_plan(
        self,
        user_id: UUID,
        plan_code: str,
        started_at: date | None = None,
        ends_at: date | None = None,
        custom_limits: dict[str, Any] | None = None,
        expire_current: bool = True,
        session: AsyncSession | None = None,
        auth_context: dict[str, Any] | None = None,
    ) -> UserPlan:
        """
        Assign a user to a plan.

        Use this when a payment webhook indicates a new subscription or upgrade.
        Optionally expires the current plan to prevent overlap.

        .. warning:: **SECURITY: Privileged Operation**

            This method modifies a user's subscription. **You MUST verify authorization**
            before calling:

            - **Webhooks**: Verify webhook signature (e.g., ``stripe.Webhook.construct_event()``)
            - **Admin API**: Verify caller has admin role
            - **User API**: Verify ``user_id`` matches the authenticated user

            If you configured an ``authorization_callback``, pass caller info via
            ``auth_context`` to enable automatic authorization checks::

                await kit.plan_service.assign_plan(
                    user_id=user.id,
                    plan_code="pro",
                    auth_context={
                        "caller_user_id": current_user.id,
                        "is_admin": current_user.is_admin,
                        "is_webhook": True,  # for webhook handlers
                    }
                )

        .. warning:: **Idempotency Not Handled**

            This method does NOT handle idempotency internally. If your webhook
            provider retries requests (e.g., Stripe retries on timeout), duplicate
            calls will create duplicate plan assignments.

            **You must implement idempotency yourself** by:

            1. Storing processed webhook event IDs in your database
            2. Checking if an event was already processed before calling this method

            Example::

                # In your webhook handler:
                if await is_event_processed(event.id):
                    return  # Already processed, skip

                await kit.plan_service.assign_plan(...)
                await mark_event_processed(event.id)

        Args:
            user_id: User UUID
            plan_code: Plan code to assign (e.g., "pro", "enterprise")
            started_at: Plan start date (defaults to today)
            ends_at: Plan end date (defaults to 100 years for "lifetime")
            custom_limits: Optional custom limits override (e.g., {"api_calls": 5000})
            expire_current: If True, expires any current plan before assigning new one
            session: Optional external session for transaction participation
            auth_context: Optional dict with caller info for authorization callback.
                Common keys: ``caller_user_id``, ``is_admin``, ``is_webhook``

        Returns:
            Created UserPlan entity

        Raises:
            PlanNotFoundError: If plan_code doesn't exist
            InvalidPlanDatesError: If date range is invalid
            InvalidCustomLimitsError: If custom_limits values are invalid
            PlanAuthorizationError: If authorization callback returns False

        Example:
            # Stripe webhook: subscription created
            user_plan = await kit.plan_service.assign_plan(
                user_id=user.id,
                plan_code="pro",
                ends_at=datetime.fromisoformat(event.current_period_end).date(),
            )
        """
        # Check authorization if callback is configured
        await self._check_authorization("assign_plan", user_id, auth_context)
        # Validate inputs before hitting database
        self._validate_plan_dates(started_at, ends_at)
        self._validate_custom_limits(custom_limits)

        async with self._create_uow(session=session) as uow:
            # Verify plan exists
            plan = await uow.plans.get_plan_by_code(plan_code)
            if plan is None:
                raise PlanNotFoundError(plan_code)

            # Optionally expire current plan
            if expire_current:
                current_plan = await uow.plans.get_user_active_plan(user_id)
                if current_plan is not None:
                    await uow.plans.expire_user_plan(current_plan.id)
                    logger.info(
                        "previous_plan_expired",
                        user_id=str(user_id),
                        previous_plan_id=str(current_plan.id),
                    )

            # Create new plan assignment
            user_plan = await uow.plans.create_user_plan(
                user_id=user_id,
                plan_id=plan.id,
                started_at=started_at,
                ends_at=ends_at,
                custom_limits=custom_limits,
            )

            # Invalidate user plan cache
            await self._user_plan_cache.invalidate(user_id)

            logger.info(
                "plan_assigned",
                user_id=str(user_id),
                plan_code=plan_code,
                ends_at=str(ends_at) if ends_at else "lifetime",
            )

            return user_plan

    async def cancel_plan(
        self,
        user_id: UUID,
        immediate: bool = False,
        session: AsyncSession | None = None,
        auth_context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Cancel user's current plan.

        Use this when a payment webhook indicates a subscription cancellation.

        .. warning:: **SECURITY: Privileged Operation**

            This method modifies a user's subscription. See :meth:`assign_plan`
            for authorization requirements and ``auth_context`` usage.

        .. warning:: **Idempotency Not Handled**

            This method does NOT handle idempotency internally. Duplicate webhook
            calls are safe (cancelling an already-cancelled plan returns False),
            but you should still deduplicate webhook events for consistency.

            See :meth:`assign_plan` for idempotency implementation guidance.

        Args:
            user_id: User UUID
            immediate: If True, plan becomes inactive immediately.
                      If False, plan remains active until its current ends_at.
            session: Optional external session for transaction participation
            auth_context: Optional dict with caller info for authorization callback

        Returns:
            True if a plan was cancelled, False if no active plan found

        Raises:
            PlanAuthorizationError: If authorization callback returns False

        Example:
            # Stripe webhook: subscription deleted (immediate cancellation)
            await kit.plan_service.cancel_plan(user_id, immediate=True)

            # Stripe webhook: subscription scheduled for cancellation
            await kit.plan_service.cancel_plan(user_id, immediate=False)
        """
        # Check authorization if callback is configured
        await self._check_authorization("cancel_plan", user_id, auth_context)
        async with self._create_uow(session=session) as uow:
            result = await uow.plans.cancel_user_plan(user_id, immediate=immediate)

            if result:
                # Invalidate user plan cache
                await self._user_plan_cache.invalidate(user_id)

                logger.info(
                    "plan_cancelled",
                    user_id=str(user_id),
                    immediate=immediate,
                )

            return result

    async def extend_plan(
        self,
        user_id: UUID,
        new_ends_at: date,
        session: AsyncSession | None = None,
        auth_context: dict[str, Any] | None = None,
    ) -> UserPlan:
        """
        Extend user's current plan end date.

        Use this when a payment webhook indicates subscription renewal.

        .. warning:: **SECURITY: Privileged Operation**

            This method modifies a user's subscription. See :meth:`assign_plan`
            for authorization requirements and ``auth_context`` usage.

        .. warning:: **Idempotency Not Handled**

            This method does NOT handle idempotency internally. Duplicate webhook
            calls with the same ``new_ends_at`` are idempotent (setting same date
            twice has no effect), but calls with different dates will override.

            **You must deduplicate webhook events** to prevent issues where a retry
            carries stale data. See :meth:`assign_plan` for implementation guidance.

        Args:
            user_id: User UUID
            new_ends_at: New plan end date
            session: Optional external session for transaction participation
            auth_context: Optional dict with caller info for authorization callback

        Returns:
            Updated UserPlan entity

        Raises:
            UserPlanNotFoundError: If user has no active plan
            PlanAuthorizationError: If authorization callback returns False

        Example:
            # Stripe webhook: invoice paid (renewal)
            await kit.plan_service.extend_plan(
                user_id=user.id,
                new_ends_at=datetime.fromisoformat(event.current_period_end).date(),
            )
        """
        # Check authorization if callback is configured
        await self._check_authorization("extend_plan", user_id, auth_context)
        async with self._create_uow(session=session) as uow:
            user_plan = await uow.plans.get_user_active_plan(user_id)
            if user_plan is None:
                raise UserPlanNotFoundError()

            updated_plan = await uow.plans.update_user_plan(
                user_plan_id=user_plan.id,
                ends_at=new_ends_at,
            )

            if updated_plan is None:
                raise UserPlanNotFoundError()

            # Invalidate user plan cache
            await self._user_plan_cache.invalidate(user_id)

            logger.info(
                "plan_extended",
                user_id=str(user_id),
                user_plan_id=str(user_plan.id),
                new_ends_at=str(new_ends_at),
            )

            return updated_plan

    async def update_plan_limits(
        self,
        user_id: UUID,
        custom_limits: dict[str, int],
        session: AsyncSession | None = None,
        auth_context: dict[str, Any] | None = None,
    ) -> UserPlan:
        """
        Update custom limits for user's current plan.

        Use this when you need to override plan limits for specific users
        (e.g., promotional offers, enterprise contracts).

        .. warning:: **SECURITY: Privileged Operation**

            This method modifies a user's quota limits, which can grant additional
            resources. This should typically be restricted to admin users only.
            See :meth:`assign_plan` for authorization requirements.

        .. warning:: **Idempotency Not Handled**

            This method does NOT handle idempotency internally. Duplicate calls
            with the same ``custom_limits`` are idempotent, but you should still
            deduplicate requests to avoid unnecessary database writes.

            See :meth:`assign_plan` for idempotency implementation guidance.

        Args:
            user_id: User UUID
            custom_limits: Custom limits override (e.g., {"api_calls": 10000})
            session: Optional external session for transaction participation
            auth_context: Optional dict with caller info for authorization callback

        Returns:
            Updated UserPlan entity

        Raises:
            UserPlanNotFoundError: If user has no active plan
            InvalidCustomLimitsError: If custom_limits values are invalid
            PlanAuthorizationError: If authorization callback returns False

        Example:
            # Give a user extra API calls
            await kit.plan_service.update_plan_limits(
                user_id=user.id,
                custom_limits={"api_calls": 10000, "ai_generation": 500},
            )
        """
        # Check authorization if callback is configured
        await self._check_authorization("update_plan_limits", user_id, auth_context)
        # Validate inputs
        self._validate_custom_limits(custom_limits)

        async with self._create_uow(session=session) as uow:
            # Use FOR UPDATE lock to prevent lost update in concurrent merges
            # Without this, two concurrent requests could each read the same
            # custom_limits, merge their own changes, and the second write
            # would overwrite the first's changes (lost update problem)
            user_plan = await uow.plans.get_user_active_plan(user_id, for_update=True)
            if user_plan is None:
                raise UserPlanNotFoundError()

            # Merge with existing custom limits (safe now due to row lock)
            merged_limits = {**user_plan.custom_limits, **custom_limits}

            updated_plan = await uow.plans.update_user_plan(
                user_plan_id=user_plan.id,
                custom_limits=merged_limits,
            )

            if updated_plan is None:
                raise UserPlanNotFoundError()

            # Invalidate user plan cache
            await self._user_plan_cache.invalidate(user_id)

            logger.info(
                "plan_limits_updated",
                user_id=str(user_id),
                user_plan_id=str(user_plan.id),
                custom_limits=custom_limits,
            )

            return updated_plan

    async def reset_usage(
        self,
        user_id: UUID,
        feature_code: str | None = None,
        session: AsyncSession | None = None,
        auth_context: dict[str, Any] | None = None,
    ) -> None:
        """
        Reset usage counters for a user.

        Use this when:
        - A new billing period starts
        - Manually resetting usage (e.g., customer support)
        - Testing

        .. warning:: **SECURITY: Privileged Operation**

            This method resets a user's usage counters, which effectively grants
            additional quota. This should typically be restricted to admin users
            or automated billing systems. See :meth:`assign_plan` for authorization
            requirements.

        .. warning:: **Idempotency Not Handled**

            This method does NOT handle idempotency internally. Duplicate calls
            will reset usage multiple times, which may cause incorrect billing
            if usage occurred between resets.

            **You must deduplicate requests** when calling from webhooks.
            See :meth:`assign_plan` for implementation guidance.

        Args:
            user_id: User UUID
            feature_code: Specific feature to reset (None = reset all features)
            session: Optional external session for transaction participation
            auth_context: Optional dict with caller info for authorization callback

        Raises:
            UserPlanNotFoundError: If user has no active plan
            FeatureNotFoundError: If feature_code doesn't exist
            PlanAuthorizationError: If authorization callback returns False

        Example:
            # Reset all usage for a user
            await kit.plan_service.reset_usage(user_id)

            # Reset specific feature usage
            await kit.plan_service.reset_usage(user_id, "api_calls")
        """
        # Check authorization if callback is configured
        await self._check_authorization("reset_usage", user_id, auth_context)
        async with self._create_uow(session=session) as uow:
            user_plan = await uow.plans.get_user_active_plan(user_id)
            if user_plan is None:
                raise UserPlanNotFoundError()

            if feature_code is not None:
                # Reset specific feature
                feature = await uow.plans.get_feature_by_code(feature_code)
                if feature is None:
                    raise FeatureNotFoundError(feature_code)

                await uow.usage.reset_usage(user_plan.id, feature.id)

                logger.info(
                    "usage_reset",
                    user_id=str(user_id),
                    feature_code=feature_code,
                )
            else:
                # Reset all usage for this user plan in a single query
                reset_count = await uow.usage.reset_all_usage(user_plan.id)

                logger.info(
                    "all_usage_reset",
                    user_id=str(user_id),
                    features_reset=reset_count,
                )

    async def get_user_plan_or_none(
        self,
        user_id: UUID,
        session: AsyncSession | None = None,
    ) -> UserPlan | None:
        """
        Get user's active plan without raising an exception.

        Unlike get_user_plan(), returns None instead of raising
        UserPlanNotFoundError if the user has no active plan.

        Args:
            user_id: User UUID
            session: Optional external session for transaction participation

        Returns:
            UserPlan entity or None
        """
        async with self._create_uow(session=session) as uow:
            return await uow.plans.get_user_active_plan(user_id)

    async def get_user_plan_with_details(
        self,
        user_id: UUID,
        session: AsyncSession | None = None,
    ) -> tuple[UserPlan, Plan] | None:
        """
        Get user's active plan with full plan details.

        This is an optimized method that returns both the UserPlan and full Plan
        (with permissions and limits). Results are cached for performance.

        Use this when you need both the user's subscription info AND the plan
        details (e.g., for profile responses).

        Args:
            user_id: User UUID
            session: Optional external session for transaction participation

        Returns:
            Tuple of (UserPlan, Plan) or None if no active plan

        Example:
            result = await kit.plan_service.get_user_plan_with_details(user.id)
            if result:
                user_plan, plan = result
                # Access user_plan.started_at, user_plan.ends_at, etc.
                # Access plan.permissions, plan.limits, etc.
        """
        # Check cache first
        cached = await self._user_plan_cache.get(user_id)
        if cached is not None:
            user_plan, plan = cached
            # Check if plan has expired since caching
            if user_plan.is_expired:
                await self._user_plan_cache.invalidate(user_id)
                return None
            logger.debug("user_plan_cache_hit", user_id=str(user_id))
            return cached

        # Cache miss - fetch from DB
        fetch_ts = self._user_plan_cache.get_fetch_timestamp()

        async with self._create_uow(session=session) as uow:
            result = await uow.plans.get_user_active_plan_with_details(user_id)

            if result is not None:
                user_plan, plan = result
                # Cache the result
                await self._user_plan_cache.set(
                    user_id, user_plan, plan, fetched_at=fetch_ts
                )
                logger.debug("user_plan_cached", user_id=str(user_id))

            return result

    # =========================================================================
    # Cache Management
    # =========================================================================

    async def invalidate_plan_cache(self, plan_code: str) -> None:
        """
        Invalidate cached plan by code.

        Call this when a plan's permissions or limits change.

        Args:
            plan_code: Plan code to invalidate
        """
        await self._plan_cache.invalidate(plan_code)
        logger.debug("plan_cache_invalidated", plan_code=plan_code)

    async def invalidate_all_plan_cache(self) -> None:
        """
        Invalidate all cached plans.

        Call this when plans are modified globally.
        """
        await self._plan_cache.invalidate_all()

    async def invalidate_user_plan_cache(self, user_id: UUID) -> None:
        """
        Invalidate cached user plan by user ID.

        Call this when a user's plan assignment changes.

        Args:
            user_id: User UUID to invalidate
        """
        await self._user_plan_cache.invalidate(user_id)
        logger.debug("user_plan_cache_invalidated", user_id=str(user_id))

    async def invalidate_all_user_plan_cache(self) -> None:
        """
        Invalidate all cached user plans.

        Call this when plans are modified globally (e.g., plan limits change).
        """
        await self._user_plan_cache.invalidate_all()

    # =========================================================================
    # Plan Listing Methods (for public display)
    # =========================================================================

    async def get_all_plans(
        self,
        session: AsyncSession | None = None,
    ) -> list[Plan]:
        """
        Get all plans with their features and limits.

        This is an optimized method that loads all plans with their
        nested relationships in a minimal number of queries.

        Plans are cached as a complete list and individually for subsequent
        single-plan lookups.

        Args:
            session: Optional external session for transaction participation

        Returns:
            List of all Plan entities with permissions and limits
        """
        # Check cache first
        cached_plans = await self._plan_cache.get_all()
        if cached_plans is not None:
            return cached_plans

        # Get fetch timestamp BEFORE DB query for stale write prevention
        fetch_ts = self._plan_cache.get_fetch_timestamp()

        async with self._create_uow(session=session) as uow:
            plans = await uow.plans.get_all_plans()

            # Cache the complete list and individual plans
            await self._plan_cache.set_all(plans, fetched_at=fetch_ts)

            logger.debug(
                "all_plans_loaded",
                count=len(plans),
            )

            return plans

    async def get_all_features(
        self,
        session: AsyncSession | None = None,
    ) -> list[Feature]:
        """
        Get all features.

        Args:
            session: Optional external session for transaction participation

        Returns:
            List of all Feature entities
        """
        async with self._create_uow(session=session) as uow:
            features = await uow.plans.get_all_features()

            logger.debug(
                "all_features_loaded",
                count=len(features),
            )

            return features
