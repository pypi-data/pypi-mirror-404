"""Tests for PlanService - P0 priority (quota atomicity).

Tests cover:
- Quota check and consume atomicity (TOCTOU fix)
- Plan access and expiration
- Feature availability checks
- Unlimited quota handling
- Custom limit overrides
- Idempotency for quota consumption
"""

import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.config import IdentityPlanKitConfig
from identity_plan_kit.plans.domain.entities import PeriodType, Plan, PlanLimit, UserPlan
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    PlanAuthorizationError,
    PlanExpiredError,
    QuotaExceededError,
    UserPlanNotFoundError,
)
from identity_plan_kit.plans.dto.usage import UsageInfo
from identity_plan_kit.plans.repositories.usage_repo import QuotaExceededInRepoError
from identity_plan_kit.plans.services.plan_service import PlanService
from identity_plan_kit.shared.state_store import InMemoryStateStore, StateStoreManager

pytestmark = pytest.mark.anyio


class TestGetUserPlan:
    """Test suite for get_user_plan method."""

    async def test_returns_active_plan(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
    ):
        """Active plan is returned for user."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan = AsyncMock(return_value=mock_user_plan)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.get_user_plan(mock_user.id)

        assert result == mock_user_plan
        assert result.plan_code == "free"
        assert not result.is_expired

    async def test_raises_error_when_no_plan(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """UserPlanNotFoundError raised when user has no plan."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(UserPlanNotFoundError):
                await service.get_user_plan(mock_user.id)


class TestCheckFeatureAccess:
    """Test suite for check_feature_access method."""

    async def test_returns_true_for_available_feature(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Returns True when feature is available in plan."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_feature_access(mock_user.id, "api_calls")

        assert result is True

    async def test_returns_false_for_unavailable_feature(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Returns False when feature is not in plan."""
        # Create a plan without the premium_feature
        plan_without_feature = Plan(
            id=mock_plan.id,
            code=mock_plan.code,
            name=mock_plan.name,
            permissions=mock_plan.permissions,
            limits={},  # No limits = no features
        )
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, plan_without_feature)
        )

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_feature_access(mock_user.id, "premium_feature")

        assert result is False

    async def test_returns_false_when_no_plan(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Returns False when user has no plan."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(return_value=None)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_feature_access(mock_user.id, "api_calls")

        assert result is False


class TestCheckAndConsumeQuota:
    """Test suite for check_and_consume_quota - CRITICAL for TOCTOU fix validation."""

    async def test_successful_quota_consumption(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Successful consumption returns updated usage info."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=50)  # New usage

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1
            )

        assert isinstance(result, UsageInfo)
        assert result.feature_code == "api_calls"
        assert result.used == 50
        assert result.limit == 100
        assert result.remaining == 50

    async def test_quota_exceeded_raises_error(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """QuotaExceededError raised when limit would be exceeded."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(
            side_effect=QuotaExceededInRepoError(current_usage=99, limit=100, requested=2)
        )

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(QuotaExceededError) as exc_info:
                await service.check_and_consume_quota(
                    mock_user.id, "api_calls", amount=2
                )

        assert exc_info.value.limit == 100
        assert exc_info.value.used == 99
        assert exc_info.value.feature_code == "api_calls"

    async def test_unlimited_quota_always_succeeds(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_unlimited_plan_limit: PlanLimit,
    ):
        """Unlimited quota (-1) always allows consumption."""
        # Create a plan with unlimited limit
        unlimited_plan = Plan(
            id=2,
            code="unlimited",
            name="Unlimited Plan",
            permissions=set(),
            limits={
                "api_calls": mock_unlimited_plan_limit,
            },
        )
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, unlimited_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=1000000)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1000
            )

        assert result.limit == -1
        assert result.remaining == -1  # Unlimited

    async def test_expired_plan_raises_error(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_expired_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Expired plan raises PlanExpiredError."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_expired_user_plan, mock_plan)
        )

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(PlanExpiredError):
                await service.check_and_consume_quota(
                    mock_user.id, "api_calls", amount=1
                )

    async def test_feature_not_in_plan_raises_error(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Feature not in plan raises FeatureNotAvailableError."""
        # Create a plan without the premium_exports feature
        plan_without_feature = Plan(
            id=mock_plan.id,
            code=mock_plan.code,
            name=mock_plan.name,
            permissions=mock_plan.permissions,
            limits=mock_plan.limits,  # Only has api_calls, not premium_exports
        )
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, plan_without_feature)
        )

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            with pytest.raises(FeatureNotAvailableError) as exc_info:
                await service.check_and_consume_quota(
                    mock_user.id, "premium_exports", amount=1
                )

        assert exc_info.value.feature_code == "premium_exports"

    async def test_custom_limit_override(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_plan: Plan,
    ):
        """Custom limit overrides plan default limit."""
        # User plan with custom limit
        user_plan_with_custom = UserPlan(
            id=1,
            user_id=mock_user.id,
            plan_id=1,
            plan_code="free",
            started_at=date.today() - timedelta(days=10),
            ends_at=date.today() + timedelta(days=20),
            custom_limits={"api_calls": 500},  # Custom limit
        )

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(user_plan_with_custom, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=200)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1
            )

        # Should use custom limit of 500, not plan default of 100
        assert result.limit == 500
        assert result.remaining == 300  # 500 - 200


class TestQuotaAtomicity:
    """Test suite for atomic quota operations - validates TOCTOU fix."""

    async def test_atomic_check_called_with_correct_params(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
        mock_plan_limit: PlanLimit,
    ):
        """Atomic check receives correct parameters from service."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=10)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            await service.check_and_consume_quota(mock_user.id, "api_calls", amount=5)

        # Verify atomic operation was called with correct params
        mock_uow.usage.atomic_check_and_consume.assert_called_once_with(
            user_plan_id=mock_user_plan.id,
            feature_id=mock_plan_limit.feature_id,
            amount=5,
            limit=100,
            period=PeriodType.DAILY,
        )

    async def test_service_uses_atomic_operation(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Verifies that the service uses atomic_check_and_consume for TOCTOU protection."""
        # This test verifies the service calls the atomic operation
        # which is critical for preventing race conditions at the DB level

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=50)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1
            )

        # Key assertion: atomic_check_and_consume was called (not separate check + consume)
        mock_uow.usage.atomic_check_and_consume.assert_called_once()
        # And the result reflects the atomic operation's return value
        assert result.used == 50


class TestGetUsageInfo:
    """Test suite for get_usage_info method."""

    async def test_returns_current_usage(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Returns current usage info without consuming."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.get_current_usage = AsyncMock(return_value=42)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.get_usage_info(mock_user.id, "api_calls")

        assert result.used == 42
        assert result.limit == 100
        assert result.remaining == 58
        assert result.period == "daily"

    async def test_unlimited_shows_negative_one_remaining(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_unlimited_plan_limit: PlanLimit,
    ):
        """Unlimited plan shows -1 for remaining."""
        # Create a plan with unlimited limit
        unlimited_plan = Plan(
            id=2,
            code="unlimited",
            name="Unlimited Plan",
            permissions=set(),
            limits={
                "api_calls": mock_unlimited_plan_limit,
            },
        )
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, unlimited_plan)
        )
        mock_uow.usage.get_current_usage = AsyncMock(return_value=999999)

        mock_session_factory = MagicMock()
        service = PlanService(mock_config, mock_session_factory)

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.get_usage_info(mock_user.id, "api_calls")

        assert result.limit == -1
        assert result.remaining == -1


class TestQuotaIdempotency:
    """Test suite for quota consumption idempotency - prevents double-deduction on retries."""

    async def test_idempotency_key_returns_cached_result(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Same idempotency key returns cached result without consuming quota again."""
        # Setup state store manager
        state_manager = StateStoreManager()
        await state_manager.init()

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=50)

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config, mock_session_factory, state_store_manager=state_manager
        )

        idempotency_key = f"{mock_user.id}:test-request-1:api_call"

        with patch.object(service, "_create_uow", return_value=mock_uow):
            # First call - should consume quota
            result1 = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1, idempotency_key=idempotency_key
            )

            # Second call with same key - should return cached result
            result2 = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1, idempotency_key=idempotency_key
            )

        # Both results should be identical
        assert result1.used == result2.used
        assert result1.limit == result2.limit
        assert result1.remaining == result2.remaining

        # atomic_check_and_consume should only be called ONCE (not twice)
        assert mock_uow.usage.atomic_check_and_consume.call_count == 1

        await state_manager.close()

    async def test_different_idempotency_keys_consume_separately(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Different idempotency keys result in separate quota consumption."""
        state_manager = StateStoreManager()
        await state_manager.init()

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        # Each call returns incrementing usage
        mock_uow.usage.atomic_check_and_consume = AsyncMock(side_effect=[50, 51])

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config, mock_session_factory, state_store_manager=state_manager
        )

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result1 = await service.check_and_consume_quota(
                mock_user.id,
                "api_calls",
                amount=1,
                idempotency_key=f"{mock_user.id}:request-1",
            )
            result2 = await service.check_and_consume_quota(
                mock_user.id,
                "api_calls",
                amount=1,
                idempotency_key=f"{mock_user.id}:request-2",
            )

        # Both calls should have consumed quota
        assert mock_uow.usage.atomic_check_and_consume.call_count == 2
        assert result1.used == 50
        assert result2.used == 51

        await state_manager.close()

    async def test_no_idempotency_key_always_consumes(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Without idempotency key, quota is consumed each time."""
        state_manager = StateStoreManager()
        await state_manager.init()

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(side_effect=[50, 51, 52])

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config, mock_session_factory, state_store_manager=state_manager
        )

        with patch.object(service, "_create_uow", return_value=mock_uow):
            # Multiple calls without idempotency key
            await service.check_and_consume_quota(mock_user.id, "api_calls", amount=1)
            await service.check_and_consume_quota(mock_user.id, "api_calls", amount=1)
            await service.check_and_consume_quota(mock_user.id, "api_calls", amount=1)

        # All calls should consume quota
        assert mock_uow.usage.atomic_check_and_consume.call_count == 3

        await state_manager.close()

    async def test_works_without_state_store(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Idempotency key is ignored when state store is not available."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(side_effect=[50, 51])

        mock_session_factory = MagicMock()
        # No state store manager provided
        service = PlanService(mock_config, mock_session_factory)

        idempotency_key = f"{mock_user.id}:test-request"

        with patch.object(service, "_create_uow", return_value=mock_uow):
            # Both calls should work without errors
            result1 = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1, idempotency_key=idempotency_key
            )
            result2 = await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1, idempotency_key=idempotency_key
            )

        # Both calls consume quota (no caching without state store)
        assert mock_uow.usage.atomic_check_and_consume.call_count == 2
        assert result1.used == 50
        assert result2.used == 51

    async def test_state_store_error_does_not_block_consumption(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """State store errors are logged but don't block quota consumption."""
        state_manager = StateStoreManager()
        await state_manager.init()

        # Make state store raise errors
        state_manager.store.get = AsyncMock(side_effect=Exception("Redis down"))
        state_manager.store.set = AsyncMock(side_effect=Exception("Redis down"))

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(return_value=50)

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config, mock_session_factory, state_store_manager=state_manager
        )

        with patch.object(service, "_create_uow", return_value=mock_uow):
            # Should not raise despite state store errors
            result = await service.check_and_consume_quota(
                mock_user.id,
                "api_calls",
                amount=1,
                idempotency_key="test-key",
            )

        # Quota was still consumed
        assert result.used == 50
        mock_uow.usage.atomic_check_and_consume.assert_called_once()

        await state_manager.close()

    async def test_idempotency_disabled_when_ttl_is_zero(
        self,
        mock_user: User,
        mock_user_plan: UserPlan,
        mock_plan: Plan,
    ):
        """Idempotency is disabled when quota_idempotency_ttl_seconds is 0."""
        # Config with TTL = 0
        config = IdentityPlanKitConfig(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="x" * 32,
            google_client_id="test",
            google_client_secret="test",
            google_redirect_uri="http://localhost/callback",
            quota_idempotency_ttl_seconds=0,
        )

        state_manager = StateStoreManager()
        await state_manager.init()

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan_with_details = AsyncMock(
            return_value=(mock_user_plan, mock_plan)
        )
        mock_uow.usage.atomic_check_and_consume = AsyncMock(side_effect=[50, 51])

        mock_session_factory = MagicMock()
        service = PlanService(
            config, mock_session_factory, state_store_manager=state_manager
        )

        idempotency_key = f"{mock_user.id}:test-request"

        with patch.object(service, "_create_uow", return_value=mock_uow):
            await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1, idempotency_key=idempotency_key
            )
            await service.check_and_consume_quota(
                mock_user.id, "api_calls", amount=1, idempotency_key=idempotency_key
            )

        # Both calls consume quota (idempotency disabled)
        assert mock_uow.usage.atomic_check_and_consume.call_count == 2

        await state_manager.close()


class TestAuthorizationCallback:
    """Test suite for authorization callback functionality (IDOR prevention)."""

    async def test_authorization_callback_blocks_unauthorized_operation(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Authorization callback returning False blocks the operation."""
        # Callback that always denies
        async def deny_all(
            operation: str, target_user_id: UUID, context: dict | None
        ) -> bool:
            return False

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config,
            mock_session_factory,
            authorization_callback=deny_all,
        )

        with pytest.raises(PlanAuthorizationError) as exc_info:
            await service.assign_plan(
                mock_user.id,
                "pro",
                auth_context={"caller_user_id": UUID("00000000-0000-0000-0000-000000000001")},
            )

        assert exc_info.value.operation == "assign_plan"
        assert exc_info.value.target_user_id == str(mock_user.id)

    async def test_authorization_callback_allows_authorized_operation(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
    ):
        """Authorization callback returning True allows the operation."""
        # Callback that always allows
        async def allow_all(
            operation: str, target_user_id: UUID, context: dict | None
        ) -> bool:
            return True

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan = AsyncMock(return_value=mock_user_plan)
        mock_uow.plans.cancel_user_plan = AsyncMock(return_value=True)

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config,
            mock_session_factory,
            authorization_callback=allow_all,
        )

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.cancel_plan(mock_user.id, auth_context={"is_admin": True})

        assert result is True

    async def test_no_authorization_callback_allows_operation(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
    ):
        """Without authorization callback, operations are allowed (caller's responsibility)."""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan = AsyncMock(return_value=mock_user_plan)
        mock_uow.plans.cancel_user_plan = AsyncMock(return_value=True)

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config,
            mock_session_factory,
            authorization_callback=None,  # No callback
        )

        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.cancel_plan(mock_user.id)

        assert result is True

    async def test_authorization_callback_receives_correct_parameters(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """Authorization callback receives operation, target_user_id, and context."""
        received_params: dict = {}

        async def capture_params(
            operation: str, target_user_id: UUID, context: dict | None
        ) -> bool:
            received_params["operation"] = operation
            received_params["target_user_id"] = target_user_id
            received_params["context"] = context
            return False  # Deny to stop execution early

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config,
            mock_session_factory,
            authorization_callback=capture_params,
        )

        auth_context = {
            "caller_user_id": UUID("00000000-0000-0000-0000-000000000001"),
            "is_admin": True,
        }

        with pytest.raises(PlanAuthorizationError):
            await service.reset_usage(mock_user.id, auth_context=auth_context)

        assert received_params["operation"] == "reset_usage"
        assert received_params["target_user_id"] == mock_user.id
        assert received_params["context"] == auth_context

    async def test_authorization_callback_called_for_all_privileged_methods(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
    ):
        """All privileged methods call the authorization callback."""
        called_operations: list[str] = []

        async def track_calls(
            operation: str, target_user_id: UUID, context: dict | None
        ) -> bool:
            called_operations.append(operation)
            return False

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config,
            mock_session_factory,
            authorization_callback=track_calls,
        )

        # Call all privileged methods
        privileged_methods = [
            ("assign_plan", {"plan_code": "pro"}),
            ("cancel_plan", {}),
            ("extend_plan", {"new_ends_at": date.today() + timedelta(days=30)}),
            ("update_plan_limits", {"custom_limits": {"api_calls": 100}}),
            ("reset_usage", {}),
        ]

        for method_name, kwargs in privileged_methods:
            with pytest.raises(PlanAuthorizationError):
                method = getattr(service, method_name)
                await method(mock_user.id, **kwargs)

        assert called_operations == [
            "assign_plan",
            "cancel_plan",
            "extend_plan",
            "update_plan_limits",
            "reset_usage",
        ]

    async def test_authorization_context_with_admin_role(
        self,
        mock_config: IdentityPlanKitConfig,
        mock_user: User,
        mock_user_plan: UserPlan,
    ):
        """Admin role in context grants access to any user's plan."""

        async def admin_only_callback(
            operation: str, target_user_id: UUID, context: dict | None
        ) -> bool:
            if context and context.get("is_admin"):
                return True
            return False

        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.plans.get_user_active_plan = AsyncMock(return_value=mock_user_plan)
        mock_uow.plans.cancel_user_plan = AsyncMock(return_value=True)

        mock_session_factory = MagicMock()
        service = PlanService(
            mock_config,
            mock_session_factory,
            authorization_callback=admin_only_callback,
        )

        # Non-admin is denied
        with pytest.raises(PlanAuthorizationError):
            with patch.object(service, "_create_uow", return_value=mock_uow):
                await service.cancel_plan(
                    mock_user.id,
                    auth_context={"caller_user_id": UUID("00000000-0000-0000-0000-000000000001")},
                )

        # Admin is allowed
        with patch.object(service, "_create_uow", return_value=mock_uow):
            result = await service.cancel_plan(mock_user.id, auth_context={"is_admin": True})

        assert result is True
