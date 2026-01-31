"""Tests for plans domain entities - Unit test layer.

Tests cover:
- Plan entity and feature limits
- UserPlan entity and expiration
- PlanLimit entity properties
- Feature entity validation
"""

from datetime import date, timedelta
from uuid import UUID

import pytest

from identity_plan_kit.plans.domain.entities import (
    Feature,
    FeatureUsage,
    PeriodType,
    Plan,
    PlanLimit,
    UserPlan,
)


class TestPlanEntity:
    """Test suite for Plan domain entity."""

    def test_plan_creation(self):
        """Plan can be created with required fields."""
        plan = Plan(
            id=1,
            code="free",
            name="Free Plan",
        )

        assert plan.code == "free"
        assert plan.name == "Free Plan"
        assert plan.permissions == set()
        assert plan.limits == {}

    def test_plan_with_permissions(self):
        """Plan can have permissions."""
        plan = Plan(
            id=1,
            code="pro",
            name="Pro Plan",
            permissions={"read:data", "write:data", "export:data"},
        )

        assert "read:data" in plan.permissions
        assert len(plan.permissions) == 3

    def test_has_permission_true(self):
        """has_permission returns True for existing permission."""
        plan = Plan(
            id=1,
            code="pro",
            name="Pro Plan",
            permissions={"admin:access"},
        )

        assert plan.has_permission("admin:access") is True

    def test_has_permission_false(self):
        """has_permission returns False for missing permission."""
        plan = Plan(
            id=1,
            code="free",
            name="Free Plan",
            permissions={"read:data"},
        )

        assert plan.has_permission("admin:access") is False

    def test_get_feature_limit_exists(self):
        """get_feature_limit returns limit when exists."""
        limit = PlanLimit(
            id=1,
            plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            limit=100,
            period=PeriodType.DAILY,
        )
        plan = Plan(
            id=1,
            code="free",
            name="Free Plan",
            limits={"api_calls": limit},
        )

        result = plan.get_feature_limit("api_calls")

        assert result == limit
        assert result.limit == 100

    def test_get_feature_limit_not_exists(self):
        """get_feature_limit returns None when not exists."""
        plan = Plan(
            id=1,
            code="free",
            name="Free Plan",
            limits={},
        )

        assert plan.get_feature_limit("nonexistent") is None

    def test_empty_plan_code_raises(self):
        """Empty plan code raises ValueError."""
        with pytest.raises(ValueError, match="code cannot be empty"):
            Plan(id=1, code="", name="Invalid Plan")


class TestPlanLimitEntity:
    """Test suite for PlanLimit domain entity."""

    def test_plan_limit_creation(self):
        """PlanLimit can be created with required fields."""
        limit = PlanLimit(
            id=1,
            plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            limit=100,
            period=PeriodType.DAILY,
        )

        assert limit.limit == 100
        assert limit.period == PeriodType.DAILY

    def test_is_unlimited_false_for_limited(self):
        """is_unlimited is False for limited feature."""
        limit = PlanLimit(
            id=1,
            plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            limit=100,
            period=PeriodType.DAILY,
        )

        assert limit.is_unlimited is False

    def test_is_unlimited_true_for_unlimited(self):
        """is_unlimited is True when limit is -1."""
        limit = PlanLimit(
            id=1,
            plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            limit=-1,
            period=PeriodType.DAILY,
        )

        assert limit.is_unlimited is True

    def test_lifetime_period_is_none(self):
        """Lifetime limit has period=None."""
        limit = PlanLimit(
            id=1,
            plan_id=1,
            feature_id=1,
            feature_code="total_storage",
            limit=1000,
            period=None,
        )

        assert limit.period is None


class TestUserPlanEntity:
    """Test suite for UserPlan domain entity."""

    def test_user_plan_creation(self):
        """UserPlan can be created with required fields."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today(),
            ends_at=date.today() + timedelta(days=30),
        )

        assert user_plan.plan_code == "free"

    def test_is_active_true_for_current_plan(self):
        """is_active is True for plan within date range."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today() - timedelta(days=10),
            ends_at=date.today() + timedelta(days=20),
        )

        assert user_plan.is_active is True

    def test_is_active_false_for_future_plan(self):
        """is_active is False for plan starting in future."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today() + timedelta(days=10),
            ends_at=date.today() + timedelta(days=40),
        )

        assert user_plan.is_active is False

    def test_is_active_false_for_past_plan(self):
        """is_active is False for expired plan."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today() - timedelta(days=60),
            ends_at=date.today() - timedelta(days=30),
        )

        assert user_plan.is_active is False

    def test_is_expired_true_for_past_plan(self):
        """is_expired is True when ends_at is in past."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today() - timedelta(days=60),
            ends_at=date.today() - timedelta(days=1),
        )

        assert user_plan.is_expired is True

    def test_is_expired_false_for_current_plan(self):
        """is_expired is False when ends_at is in future."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today() - timedelta(days=10),
            ends_at=date.today() + timedelta(days=20),
        )

        assert user_plan.is_expired is False

    def test_get_custom_limit_exists(self):
        """get_custom_limit returns value when exists."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today(),
            ends_at=date.today() + timedelta(days=30),
            custom_limits={"api_calls": 500},
        )

        assert user_plan.get_custom_limit("api_calls") == 500

    def test_get_custom_limit_not_exists(self):
        """get_custom_limit returns None when not exists."""
        user_plan = UserPlan(
            id=1,
            user_id=UUID("12345678-1234-1234-1234-123456789012"),
            plan_id=1,
            plan_code="free",
            started_at=date.today(),
            ends_at=date.today() + timedelta(days=30),
            custom_limits={},
        )

        assert user_plan.get_custom_limit("api_calls") is None


class TestFeatureEntity:
    """Test suite for Feature domain entity."""

    def test_feature_creation(self):
        """Feature can be created with required fields."""
        feature = Feature(
            id=1,
            code="api_calls",
            name="API Calls",
        )

        assert feature.code == "api_calls"
        assert feature.name == "API Calls"

    def test_empty_feature_code_raises(self):
        """Empty feature code raises ValueError."""
        with pytest.raises(ValueError, match="code cannot be empty"):
            Feature(id=1, code="", name="Invalid Feature")


class TestFeatureUsageEntity:
    """Test suite for FeatureUsage domain entity."""

    def test_feature_usage_creation(self):
        """FeatureUsage can be created with required fields."""
        usage = FeatureUsage(
            id=1,
            user_plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            usage=42,
            start_period=date.today(),
            end_period=date.today(),
        )

        assert usage.usage == 42
        assert usage.feature_code == "api_calls"

    def test_is_current_period_true(self):
        """is_current_period is True for today's period."""
        usage = FeatureUsage(
            id=1,
            user_plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            usage=42,
            start_period=date.today(),
            end_period=date.today(),
        )

        assert usage.is_current_period is True

    def test_is_current_period_false_for_past(self):
        """is_current_period is False for past period."""
        usage = FeatureUsage(
            id=1,
            user_plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            usage=42,
            start_period=date.today() - timedelta(days=30),
            end_period=date.today() - timedelta(days=1),
        )

        assert usage.is_current_period is False

    def test_is_current_period_false_for_future(self):
        """is_current_period is False for future period."""
        usage = FeatureUsage(
            id=1,
            user_plan_id=1,
            feature_id=1,
            feature_code="api_calls",
            usage=0,
            start_period=date.today() + timedelta(days=1),
            end_period=date.today() + timedelta(days=30),
        )

        assert usage.is_current_period is False


class TestPeriodType:
    """Test suite for PeriodType enum."""

    def test_daily_period(self):
        """DAILY period has correct value."""
        assert PeriodType.DAILY.value == "daily"

    def test_monthly_period(self):
        """MONTHLY period has correct value."""
        assert PeriodType.MONTHLY.value == "monthly"
