"""Tests for exception handlers and error format compliance.

These tests verify that all error responses match the documented format in README.md:
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "context": { ... }  // Optional
    }
}
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr

from identity_plan_kit.auth.domain.exceptions import (
    AuthError,
    InvalidCredentialsError,
    OAuthError,
    RefreshTokenExpiredError,
    RefreshTokenInvalidError,
    RefreshTokenMissingError,
    TokenExpiredError,
    TokenInvalidError,
    UserInactiveError,
    UserNotFoundError,
)
from identity_plan_kit.plans.domain.exceptions import (
    FeatureNotAvailableError,
    PlanAuthorizationError,
    PlanExpiredError,
    PlanNotFoundError,
    QuotaExceededError,
    UserPlanNotFoundError,
)
from identity_plan_kit.rbac.domain.exceptions import (
    PermissionDeniedError,
    RoleNotFoundError,
)
from identity_plan_kit.shared.error_formatter import (
    DefaultErrorFormatter,
    get_error_formatter,
    reset_error_formatter,
)
from identity_plan_kit.shared.exception_handlers import register_exception_handlers
from identity_plan_kit.shared.exceptions import BaseError


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app with exception handlers registered."""
    app = FastAPI()
    reset_error_formatter()  # Ensure default formatter
    register_exception_handlers(app)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


# =============================================================================
# Error Format Structure Tests
# =============================================================================


class TestErrorFormatStructure:
    """Test that error responses have the correct structure."""

    def test_default_formatter_produces_correct_structure(self):
        """DefaultErrorFormatter should produce success: false format."""
        from unittest.mock import MagicMock

        formatter = DefaultErrorFormatter()
        mock_request = MagicMock()

        result = formatter.format_error(
            request=mock_request,
            status_code=400,
            code="TEST_ERROR",
            message="Test message",
            details={"key": "value"},
        )

        assert result == {
            "success": False,
            "error": {
                "code": "TEST_ERROR",
                "message": "Test message",
                "context": {"key": "value"},
            },
        }

    def test_default_formatter_without_details(self):
        """DefaultErrorFormatter should omit context when no details."""
        from unittest.mock import MagicMock

        formatter = DefaultErrorFormatter()
        mock_request = MagicMock()

        result = formatter.format_error(
            request=mock_request,
            status_code=400,
            code="TEST_ERROR",
            message="Test message",
            details=None,
        )

        assert result == {
            "success": False,
            "error": {
                "code": "TEST_ERROR",
                "message": "Test message",
            },
        }
        assert "context" not in result["error"]

    def test_base_error_to_dict_format(self):
        """BaseError.to_dict() should produce correct format."""
        error = BaseError(message="Test error", details={"key": "value"})
        result = error.to_dict()

        assert result == {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Test error",
                "context": {"key": "value"},
            },
        }

    def test_base_error_to_dict_without_details(self):
        """BaseError.to_dict() should omit context when no details."""
        error = BaseError(message="Test error")
        result = error.to_dict()

        assert result == {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Test error",
            },
        }
        assert "context" not in result["error"]

    def test_base_error_context_property(self):
        """BaseError should have context property as alias for details."""
        error = BaseError(message="Test", details={"key": "value"})
        assert error.context == {"key": "value"}
        assert error.context == error.details


# =============================================================================
# Authentication Error Tests (401)
# =============================================================================


class TestAuthenticationErrors:
    """Test authentication error responses match README documentation."""

    def test_token_expired_error(self, app: FastAPI, client: TestClient):
        """TOKEN_EXPIRED should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise TokenExpiredError()

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "TOKEN_EXPIRED"
        assert "expired" in data["error"]["message"].lower()

    def test_token_invalid_error(self, app: FastAPI, client: TestClient):
        """TOKEN_INVALID should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise TokenInvalidError()

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "TOKEN_INVALID"
        assert "invalid" in data["error"]["message"].lower()

    def test_auth_error(self, app: FastAPI, client: TestClient):
        """AUTH_ERROR should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise AuthError(message="Custom auth error")

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_ERROR"
        assert data["error"]["message"] == "Custom auth error"

    def test_invalid_credentials_error(self, app: FastAPI, client: TestClient):
        """INVALID_CREDENTIALS should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise InvalidCredentialsError()

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_user_not_found_error(self, app: FastAPI, client: TestClient):
        """USER_NOT_FOUND should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise UserNotFoundError()

        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_NOT_FOUND"


# =============================================================================
# Refresh Token Error Tests (401)
# =============================================================================


class TestRefreshTokenErrors:
    """Test refresh token error responses match README documentation."""

    def test_refresh_token_missing_error(self, app: FastAPI, client: TestClient):
        """REFRESH_TOKEN_MISSING should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise RefreshTokenMissingError()

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "REFRESH_TOKEN_MISSING"
        assert "not provided" in data["error"]["message"].lower()

    def test_refresh_token_invalid_error(self, app: FastAPI, client: TestClient):
        """REFRESH_TOKEN_INVALID should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise RefreshTokenInvalidError()

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "REFRESH_TOKEN_INVALID"
        assert "invalid" in data["error"]["message"].lower()

    def test_refresh_token_expired_error(self, app: FastAPI, client: TestClient):
        """REFRESH_TOKEN_EXPIRED should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise RefreshTokenExpiredError()

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "REFRESH_TOKEN_EXPIRED"
        assert "expired" in data["error"]["message"].lower()


# =============================================================================
# OAuth Error Tests (400/401)
# =============================================================================


class TestOAuthErrors:
    """Test OAuth error responses match README documentation."""

    def test_oauth_error(self, app: FastAPI, client: TestClient):
        """OAUTH_ERROR should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise OAuthError(message="OAuth failed", provider="google")

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "OAUTH_ERROR"
        assert data["error"]["context"]["provider"] == "google"

    def test_oauth_error_without_provider(self, app: FastAPI, client: TestClient):
        """OAUTH_ERROR without provider should omit context."""

        @app.get("/test")
        async def test_endpoint():
            raise OAuthError(message="OAuth failed")

        response = client.get("/test")

        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "OAUTH_ERROR"
        assert "context" not in data["error"]


# =============================================================================
# Authorization Error Tests (403)
# =============================================================================


class TestAuthorizationErrors:
    """Test authorization error responses match README documentation."""

    def test_user_inactive_error(self, app: FastAPI, client: TestClient):
        """USER_INACTIVE should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise UserInactiveError()

        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_INACTIVE"
        assert "deactivated" in data["error"]["message"].lower()

    def test_permission_denied_error(self, app: FastAPI, client: TestClient):
        """PERMISSION_DENIED should return correct format with context."""

        @app.get("/test")
        async def test_endpoint():
            raise PermissionDeniedError(permission="admin.write")

        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_DENIED"
        assert data["error"]["context"]["permission"] == "admin.write"

    def test_permission_denied_error_without_permission(
        self, app: FastAPI, client: TestClient
    ):
        """PERMISSION_DENIED without permission should omit context."""

        @app.get("/test")
        async def test_endpoint():
            raise PermissionDeniedError()

        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PERMISSION_DENIED"
        assert "context" not in data["error"]

    def test_permission_denied_error_permission_code_property(self):
        """PermissionDeniedError should have permission_code property."""
        error = PermissionDeniedError(permission="admin.write")
        assert error.permission == "admin.write"
        assert error.permission_code == "admin.write"

    def test_feature_not_available_error(self, app: FastAPI, client: TestClient):
        """FEATURE_NOT_AVAILABLE should return correct format with context."""

        @app.get("/test")
        async def test_endpoint():
            raise FeatureNotAvailableError(feature_code="premium_export", plan_code="free")

        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FEATURE_NOT_AVAILABLE"
        assert data["error"]["context"]["feature"] == "premium_export"
        assert data["error"]["context"]["plan"] == "free"

    def test_plan_authorization_error(self, app: FastAPI, client: TestClient):
        """PLAN_AUTHORIZATION_ERROR should return correct format with context."""

        @app.get("/test")
        async def test_endpoint():
            raise PlanAuthorizationError(
                message="Not authorized to assign plan",
                operation="assign_plan",
                target_user_id="user-123",
                caller_user_id="admin-456",
            )

        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PLAN_AUTHORIZATION_ERROR"
        assert data["error"]["context"]["operation"] == "assign_plan"
        assert data["error"]["context"]["target_user_id"] == "user-123"


# =============================================================================
# Plan/Subscription Error Tests
# =============================================================================


class TestPlanErrors:
    """Test plan/subscription error responses match README documentation."""

    def test_plan_expired_error(self, app: FastAPI, client: TestClient):
        """PLAN_EXPIRED should return 402 with correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise PlanExpiredError()

        response = client.get("/test")

        assert response.status_code == 403  # Handler returns 403
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PLAN_EXPIRED"
        assert "expired" in data["error"]["message"].lower()

    def test_user_plan_not_found_error(self, app: FastAPI, client: TestClient):
        """USER_PLAN_NOT_FOUND should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise UserPlanNotFoundError()

        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "USER_PLAN_NOT_FOUND"

    def test_plan_not_found_error(self, app: FastAPI, client: TestClient):
        """PLAN_NOT_FOUND should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise PlanNotFoundError(plan_code="enterprise")

        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PLAN_NOT_FOUND"
        assert "enterprise" in data["error"]["message"]

    def test_quota_exceeded_error(self, app: FastAPI, client: TestClient):
        """QUOTA_EXCEEDED should return 429 with correct format and context."""

        @app.get("/test")
        async def test_endpoint():
            raise QuotaExceededError(
                feature_code="ai_generation",
                limit=100,
                used=150,
                period="monthly",
            )

        response = client.get("/test")

        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "QUOTA_EXCEEDED"
        assert data["error"]["context"]["feature"] == "ai_generation"
        assert data["error"]["context"]["limit"] == 100
        assert data["error"]["context"]["used"] == 150
        assert data["error"]["context"]["period"] == "monthly"


# =============================================================================
# Resource Error Tests (404)
# =============================================================================


class TestResourceErrors:
    """Test resource error responses match README documentation."""

    def test_role_not_found_error(self, app: FastAPI, client: TestClient):
        """ROLE_NOT_FOUND should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise RoleNotFoundError(role_code="super_admin")

        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "ROLE_NOT_FOUND"
        assert "super_admin" in data["error"]["message"]


# =============================================================================
# HTTP Exception Tests
# =============================================================================


class TestHTTPExceptions:
    """Test HTTP exception responses match README documentation."""

    def test_http_404_not_found(self, app: FastAPI, client: TestClient):
        """404 NOT_FOUND should return correct format with context."""

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=404, detail="Not found")

        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_http_405_method_not_allowed(self, app: FastAPI, client: TestClient):
        """405 METHOD_NOT_ALLOWED raised explicitly should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=405, detail="Method not allowed")

        response = client.get("/test")

        assert response.status_code == 405
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_http_400_bad_request(self, app: FastAPI, client: TestClient):
        """400 BAD_REQUEST should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise HTTPException(status_code=400, detail="Bad request")

        response = client.get("/test")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "BAD_REQUEST"


# =============================================================================
# Validation Error Tests (422)
# =============================================================================


class TestValidationErrors:
    """Test validation error responses match README documentation."""

    def test_validation_error_missing_field(self, app: FastAPI, client: TestClient):
        """VALIDATION_ERROR for missing field should return correct format."""

        class UserRequest(BaseModel):
            email: EmailStr
            password: str

        @app.post("/test")
        async def test_endpoint(data: UserRequest):
            return {"ok": True}

        response = client.post("/test", json={})

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "context" in data["error"]
        assert "errors" in data["error"]["context"]

    def test_validation_error_invalid_email(self, app: FastAPI, client: TestClient):
        """VALIDATION_ERROR for invalid email should return correct format."""

        class UserRequest(BaseModel):
            email: EmailStr

        @app.post("/test")
        async def test_endpoint(data: UserRequest):
            return {"ok": True}

        response = client.post("/test", json={"email": "invalid"})

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        errors = data["error"]["context"]["errors"]
        assert any(e["field"] == "email" for e in errors)


# =============================================================================
# Server Error Tests (5xx)
# =============================================================================


class TestServerErrors:
    """Test server error responses match README documentation."""

    def test_internal_server_error(self, app: FastAPI, client: TestClient):
        """500 INTERNAL_SERVER_ERROR should return correct format."""

        @app.get("/test")
        async def test_endpoint():
            raise RuntimeError("Something went wrong")

        response = client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "unexpected" in data["error"]["message"].lower()


# =============================================================================
# Error Code Completeness Tests
# =============================================================================


class TestErrorCodeCompleteness:
    """Test that all documented error codes are properly defined."""

    def test_auth_error_codes(self):
        """Verify authentication error codes match documentation."""
        assert TokenExpiredError.code == "TOKEN_EXPIRED"
        assert TokenInvalidError.code == "TOKEN_INVALID"
        assert AuthError.code == "AUTH_ERROR"
        assert InvalidCredentialsError.code == "INVALID_CREDENTIALS"

    def test_refresh_token_error_codes(self):
        """Verify refresh token error codes match documentation."""
        assert RefreshTokenMissingError.code == "REFRESH_TOKEN_MISSING"
        assert RefreshTokenInvalidError.code == "REFRESH_TOKEN_INVALID"
        assert RefreshTokenExpiredError.code == "REFRESH_TOKEN_EXPIRED"

    def test_oauth_error_codes(self):
        """Verify OAuth error codes match documentation."""
        assert OAuthError.code == "OAUTH_ERROR"

    def test_authorization_error_codes(self):
        """Verify authorization error codes match documentation."""
        assert UserInactiveError.code == "USER_INACTIVE"
        assert PermissionDeniedError.code == "PERMISSION_DENIED"
        assert FeatureNotAvailableError.code == "FEATURE_NOT_AVAILABLE"
        assert PlanAuthorizationError.code == "PLAN_AUTHORIZATION_ERROR"

    def test_plan_error_codes(self):
        """Verify plan error codes match documentation."""
        assert PlanExpiredError.code == "PLAN_EXPIRED"
        assert UserPlanNotFoundError.code == "USER_PLAN_NOT_FOUND"
        assert PlanNotFoundError.code == "PLAN_NOT_FOUND"
        assert QuotaExceededError.code == "QUOTA_EXCEEDED"

    def test_rbac_error_codes(self):
        """Verify RBAC error codes match documentation."""
        assert RoleNotFoundError.code == "ROLE_NOT_FOUND"

    def test_user_error_codes(self):
        """Verify user error codes match documentation."""
        assert UserNotFoundError.code == "USER_NOT_FOUND"


# =============================================================================
# Status Code Tests
# =============================================================================


class TestStatusCodes:
    """Test that exceptions return correct HTTP status codes."""

    def test_auth_errors_return_401(self):
        """Auth errors should return 401 status code."""
        assert TokenExpiredError.status_code == 401
        assert TokenInvalidError.status_code == 401
        assert AuthError.status_code == 401
        assert RefreshTokenMissingError.status_code == 401
        assert RefreshTokenInvalidError.status_code == 401
        assert RefreshTokenExpiredError.status_code == 401

    def test_authorization_errors_return_403(self):
        """Authorization errors should return 403 status code."""
        assert UserInactiveError.status_code == 403
        assert PermissionDeniedError.status_code == 403
        assert FeatureNotAvailableError.status_code == 403
        assert PlanAuthorizationError.status_code == 403

    def test_not_found_errors_return_404(self):
        """Not found errors should return 404 status code."""
        assert UserNotFoundError.status_code == 404
        assert RoleNotFoundError.status_code == 404
        assert PlanNotFoundError.status_code == 404

    def test_plan_expired_returns_402(self):
        """Plan expired should return 402 Payment Required."""
        assert PlanExpiredError.status_code == 402
        assert UserPlanNotFoundError.status_code == 402

    def test_quota_exceeded_returns_429(self):
        """Quota exceeded should return 429 Too Many Requests."""
        assert QuotaExceededError.status_code == 429
