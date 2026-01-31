"""Tests for plan dependencies (requires_plan, requires_feature).

These tests verify that domain exceptions propagate correctly through
the dependency layer with proper error codes and context, not generic
HTTPException codes.

The key bug this tests for: dependencies were catching domain exceptions
and re-raising them as HTTPException, which lost the specific error codes.
"""

from datetime import date
from typing import Annotated
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI, Response
from starlette.testclient import TestClient

from identity_plan_kit.auth.dependencies import get_current_user
from identity_plan_kit.auth.domain.entities import User
from identity_plan_kit.plans.dependencies import (
    FeatureUsage,
    requires_feature,
    requires_plan,
)
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    PlanExpiredError,
    QuotaExceededError,
    UserPlanNotFoundError,
)
from identity_plan_kit.plans.dto.usage import UsageInfo
from identity_plan_kit.shared.exception_handlers import register_exception_handlers


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        role_id=uuid4(),
        display_name="Test User",
        is_active=True,
        created_at=date.today(),
    )


@pytest.fixture
def mock_plan_service():
    """Create a mock plan service."""
    return AsyncMock()


@pytest.fixture
def app_with_mocked_auth(mock_plan_service, mock_user):
    """Create a FastAPI app with properly mocked dependencies."""
    app = FastAPI()

    # Mock the kit on app state
    mock_kit = MagicMock()
    mock_kit.plan_service = mock_plan_service
    app.state.identity_plan_kit = mock_kit

    # Register exception handlers
    register_exception_handlers(app)

    # Override the auth dependency to return our mock user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    return app


class TestRequiresFeatureQuotaExceeded:
    """Test that QuotaExceededError propagates with correct error code."""

    def test_quota_exceeded_returns_quota_exceeded_code(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """
        QUOTA_EXCEEDED code should be returned, not RATE_LIMIT_EXCEEDED.

        This was the bug: the dependency was converting QuotaExceededError
        to HTTPException(429), which then got the generic RATE_LIMIT_EXCEEDED
        code from http_exception_handler's status code mapping.
        """
        app = app_with_mocked_auth

        # Configure mock to raise QuotaExceededError
        mock_plan_service.check_and_consume_quota.side_effect = QuotaExceededError(
            feature_code="ai_generation",
            limit=10,
            used=10,
            period="daily",
        )

        @app.post("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)],
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.post("/test")

        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        # THIS IS THE KEY ASSERTION - must be QUOTA_EXCEEDED, not RATE_LIMIT_EXCEEDED
        assert data["error"]["code"] == "QUOTA_EXCEEDED"
        assert data["error"]["context"]["feature"] == "ai_generation"
        assert data["error"]["context"]["limit"] == 10
        assert data["error"]["context"]["used"] == 10
        assert data["error"]["context"]["period"] == "daily"

    def test_quota_exceeded_includes_headers(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """X-Quota-* headers should be set on quota exceeded."""
        app = app_with_mocked_auth

        mock_plan_service.check_and_consume_quota.side_effect = QuotaExceededError(
            feature_code="api_calls",
            limit=100,
            used=100,
            period="monthly",
        )

        @app.post("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("api_calls", consume=1)],
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.post("/test")

        assert response.status_code == 429
        assert response.headers.get("X-Quota-Limit") == "100"
        assert response.headers.get("X-Quota-Used") == "100"
        assert response.headers.get("X-Quota-Remaining") == "0"


class TestRequiresFeatureUserPlanNotFound:
    """Test that UserPlanNotFoundError propagates with correct error code."""

    def test_user_plan_not_found_returns_proper_error_code(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """USER_PLAN_NOT_FOUND code should be returned, not generic codes."""
        app = app_with_mocked_auth

        mock_plan_service.check_and_consume_quota.side_effect = UserPlanNotFoundError()

        @app.post("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)],
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.post("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_PLAN_NOT_FOUND"


class TestRequiresFeaturePlanExpired:
    """Test that PlanExpiredError propagates with correct error code."""

    def test_plan_expired_returns_proper_error_code(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """PLAN_EXPIRED code should be returned."""
        app = app_with_mocked_auth

        mock_plan_service.check_and_consume_quota.side_effect = PlanExpiredError()

        @app.post("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)],
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.post("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PLAN_EXPIRED"


class TestRequiresFeatureNotAvailable:
    """Test that FeatureNotAvailableError propagates with correct error code."""

    def test_feature_not_available_returns_proper_error_code(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """FEATURE_NOT_AVAILABLE code should be returned with context."""
        app = app_with_mocked_auth

        mock_plan_service.check_and_consume_quota.side_effect = FeatureNotAvailableError(
            feature_code="premium_export",
            plan_code="free",
        )

        @app.post("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("premium_export", consume=1)],
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.post("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FEATURE_NOT_AVAILABLE"
        assert data["error"]["context"]["feature"] == "premium_export"
        assert data["error"]["context"]["plan"] == "free"


class TestRequiresPlanErrors:
    """Test that requires_plan dependency propagates errors correctly."""

    def test_user_plan_not_found_returns_proper_code(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """USER_PLAN_NOT_FOUND from requires_plan should have correct code."""
        app = app_with_mocked_auth

        mock_plan_service.get_user_plan.side_effect = UserPlanNotFoundError()

        @app.get("/test")
        async def test_endpoint(
            _: None = requires_plan(),
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_PLAN_NOT_FOUND"

    def test_plan_expired_returns_proper_code(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """PLAN_EXPIRED from requires_plan should have correct code."""
        app = app_with_mocked_auth

        mock_plan_service.get_user_plan.side_effect = PlanExpiredError()

        @app.get("/test")
        async def test_endpoint(
            _: None = requires_plan(),
        ):
            return {"success": True}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PLAN_EXPIRED"


class TestSuccessfulFeatureAccess:
    """Test successful feature access returns usage info."""

    def test_successful_quota_consumption(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """Successful quota consumption should return usage info and headers."""
        app = app_with_mocked_auth

        mock_plan_service.check_and_consume_quota.return_value = UsageInfo(
            feature_code="ai_generation",
            used=5,
            limit=10,
            remaining=5,
            period="daily",
        )

        @app.post("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("ai_generation", consume=1)],
        ):
            return {
                "success": True,
                "remaining": usage.remaining,
            }

        client = TestClient(app)
        response = client.post("/test")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["remaining"] == 5

        # Check headers
        assert response.headers.get("X-Quota-Limit") == "10"
        assert response.headers.get("X-Quota-Used") == "5"
        assert response.headers.get("X-Quota-Remaining") == "5"
        assert response.headers.get("X-Quota-Period") == "daily"

    def test_get_usage_info_only(
        self, app_with_mocked_auth, mock_plan_service
    ):
        """consume=0 should just check access without consuming."""
        app = app_with_mocked_auth

        mock_plan_service.get_usage_info.return_value = UsageInfo(
            feature_code="exports",
            used=2,
            limit=5,
            remaining=3,
            period="monthly",
        )

        @app.get("/test")
        async def test_endpoint(
            usage: Annotated[UsageInfo, requires_feature("exports", consume=0)],
        ):
            return {
                "success": True,
                "remaining": usage.remaining,
            }

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        # Verify get_usage_info was called, not check_and_consume_quota
        mock_plan_service.get_usage_info.assert_called_once()
        mock_plan_service.check_and_consume_quota.assert_not_called()
