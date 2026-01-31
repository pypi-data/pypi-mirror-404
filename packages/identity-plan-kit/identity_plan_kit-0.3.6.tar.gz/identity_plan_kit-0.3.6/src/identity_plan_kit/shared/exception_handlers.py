"""Centralized exception handlers for FastAPI."""

import os
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from identity_plan_kit.auth.domain.exceptions import (
    AuthError,
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
    ErrorFormatter,
    get_error_formatter,
    set_error_formatter,
)
from identity_plan_kit.shared.exceptions import (
    BaseError,
)
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Compiled regex patterns for sensitive data sanitization
# These patterns detect common credential/secret formats in error messages
_SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Key-value patterns (password=xxx, api_key: xxx, etc.)
    (re.compile(r"(password|passwd|pwd)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),
    (re.compile(r"(token|access_token|refresh_token|api_token)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),
    (re.compile(r"(secret|client_secret|app_secret)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),
    (re.compile(r"(api_key|apikey|api-key)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),
    (re.compile(r"(auth|authorization)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),
    (re.compile(r"(private_key|private-key)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),

    # Bearer tokens (JWT format)
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", re.IGNORECASE), "Bearer ***"),

    # Database connection strings (postgres://user:pass@host, mysql://user:pass@host, etc.)
    (re.compile(r"(postgres|postgresql|mysql|mongodb|redis|amqp|rabbitmq)://[^:]+:[^@]+@", re.IGNORECASE), r"\1://***:***@"),

    # Generic connection strings with credentials
    (re.compile(r"://([^:]+):([^@]+)@"), "://***:***@"),

    # AWS credentials
    (re.compile(r"(AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}", re.IGNORECASE), "***AWS_KEY***"),
    (re.compile(r"(aws_secret_access_key|aws_access_key_id)[=:]\s*['\"]?[^'\"\s;,}{]+", re.IGNORECASE), r"\1=***"),

    # Generic API keys (long alphanumeric strings that look like keys)
    (re.compile(r"(sk_live_|sk_test_|pk_live_|pk_test_)[A-Za-z0-9]{20,}"), "***STRIPE_KEY***"),

    # Email addresses in error context (partial masking)
    (re.compile(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"), r"\1[at]\2"),

    # IP addresses (partial masking for privacy)
    (re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b"), r"\1.\2.***.***"),

    # Base64-encoded secrets (long base64 strings in key contexts)
    (re.compile(r"(key|secret|token|credential)[=:]\s*['\"]?[A-Za-z0-9+/]{40,}={0,2}['\"]?", re.IGNORECASE), r"\1=***BASE64***"),
]


def _sanitize_sensitive_data(message: str) -> str:
    """
    Sanitize potentially sensitive data from exception messages.

    This function applies multiple regex patterns to detect and mask:
    - Passwords and secrets in key=value format
    - Bearer tokens (JWT)
    - Database connection strings with credentials
    - AWS access keys
    - Stripe API keys
    - Email addresses (partial masking)
    - IP addresses (partial masking)
    - Base64-encoded credentials

    Args:
        message: The exception message to sanitize

    Returns:
        Sanitized message with sensitive data masked
    """
    for pattern, replacement in _SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


def create_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    """
    Create an error response using the configured error formatter.

    Args:
        request: The FastAPI request object
        status_code: HTTP status code
        code: Error code (e.g., "AUTH_ERROR")
        message: Human-readable error message
        details: Additional error details

    Returns:
        JSONResponse with formatted error body
    """
    formatter = get_error_formatter()
    return formatter.create_response(
        request=request,
        status_code=status_code,
        code=code,
        message=message,
        details=details,
    )


async def base_error_handler(request: Request, exc: BaseError) -> JSONResponse:
    """Handle all BaseError exceptions."""
    logger.warning(
        "application_error",
        error_code=exc.code,
        message=exc.message,
        path=request.url.path,
    )
    return create_error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning(
        "auth_error",
        error_code=exc.code,
        path=request.url.path,
    )
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


async def token_expired_handler(request: Request, exc: TokenExpiredError) -> JSONResponse:
    """Handle expired token errors."""
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message="Your session has expired. Please log in again.",
    )


async def token_invalid_handler(request: Request, exc: TokenInvalidError) -> JSONResponse:
    """Handle invalid token errors."""
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message="Invalid authentication token.",
    )


async def refresh_token_missing_handler(
    request: Request, exc: RefreshTokenMissingError
) -> JSONResponse:
    """Handle missing refresh token errors."""
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message="Refresh token not provided. Please log in again.",
    )


async def refresh_token_invalid_handler(
    request: Request, exc: RefreshTokenInvalidError
) -> JSONResponse:
    """Handle invalid refresh token errors."""
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message="Invalid refresh token. Please log in again.",
    )


async def refresh_token_expired_handler(
    request: Request, exc: RefreshTokenExpiredError
) -> JSONResponse:
    """Handle expired refresh token errors."""
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message="Refresh token has expired. Please log in again.",
    )


async def oauth_error_handler(request: Request, exc: OAuthError) -> JSONResponse:
    """Handle OAuth errors."""
    logger.warning(
        "oauth_error",
        error_code=exc.code,
        provider=exc.provider,
        path=request.url.path,
    )
    return create_error_response(
        request=request,
        status_code=401,
        code=exc.code,
        message=exc.message,
        details={"provider": exc.provider} if exc.provider else None,
    )


async def user_inactive_handler(request: Request, exc: UserInactiveError) -> JSONResponse:
    """Handle inactive user errors."""
    return create_error_response(
        request=request,
        status_code=403,
        code=exc.code,
        message="Your account has been deactivated.",
    )


async def user_not_found_handler(request: Request, exc: UserNotFoundError) -> JSONResponse:
    """Handle user not found errors."""
    return create_error_response(
        request=request,
        status_code=404,
        code=exc.code,
        message="User not found.",
    )


async def permission_denied_handler(request: Request, exc: PermissionDeniedError) -> JSONResponse:
    """Handle permission denied errors."""
    permission = exc.permission_code
    logger.warning(
        "permission_denied",
        permission=permission,
        path=request.url.path,
    )
    return create_error_response(
        request=request,
        status_code=403,
        code=exc.code,
        message=exc.message,
        details={"permission": permission} if permission else None,
    )


async def role_not_found_handler(request: Request, exc: RoleNotFoundError) -> JSONResponse:
    """Handle role not found errors."""
    return create_error_response(
        request=request,
        status_code=404,
        code=exc.code,
        message=exc.message,
    )


async def quota_exceeded_handler(request: Request, exc: QuotaExceededError) -> JSONResponse:
    """Handle quota exceeded errors."""
    logger.info(
        "quota_exceeded",
        feature=exc.feature_code,
        path=request.url.path,
    )
    response = create_error_response(
        request=request,
        status_code=429,
        code=exc.code,
        message=exc.message,
        details={
            "feature": exc.feature_code,
            "limit": exc.limit,
            "used": exc.used,
            "period": exc.period,
        },
    )
    # Add quota headers for client visibility
    response.headers["X-Quota-Limit"] = str(exc.limit)
    response.headers["X-Quota-Used"] = str(exc.used)
    response.headers["X-Quota-Remaining"] = str(exc.remaining)
    return response


async def plan_expired_handler(request: Request, exc: PlanExpiredError) -> JSONResponse:
    """Handle plan expired errors."""
    return create_error_response(
        request=request,
        status_code=403,
        code=exc.code,
        message="Your subscription plan has expired.",
    )


async def feature_not_available_handler(
    request: Request,
    exc: FeatureNotAvailableError,
) -> JSONResponse:
    """Handle feature not available errors."""
    return create_error_response(
        request=request,
        status_code=403,
        code=exc.code,
        message=exc.message,
        details={
            "feature": exc.feature_code,
            "plan": exc.plan_code,
        },
    )


async def user_plan_not_found_handler(request: Request, exc: UserPlanNotFoundError) -> JSONResponse:
    """Handle user plan not found errors."""
    return create_error_response(
        request=request,
        status_code=404,
        code=exc.code,
        message="No active subscription plan found.",
    )


async def plan_not_found_handler(request: Request, exc: PlanNotFoundError) -> JSONResponse:
    """Handle plan not found errors."""
    return create_error_response(
        request=request,
        status_code=404,
        code=exc.code,
        message=exc.message,
    )


async def plan_authorization_error_handler(
    request: Request,
    exc: PlanAuthorizationError,
) -> JSONResponse:
    """Handle plan authorization errors.

    Raised when a plan operation is not authorized (e.g., unauthorized plan assignment).
    """
    logger.warning(
        "plan_authorization_error",
        operation=exc.operation,
        target_user_id=exc.target_user_id,
        caller_user_id=exc.caller_user_id,
        path=request.url.path,
    )
    return create_error_response(
        request=request,
        status_code=403,
        code=exc.code,
        message=exc.message,
        details={
            "operation": exc.operation,
            "target_user_id": exc.target_user_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException errors.

    Converts standard HTTPException to use the library's error structure.
    """
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )

    # Map status codes to error codes
    code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = code_mapping.get(exc.status_code, "HTTP_ERROR")

    # Extract details if the detail is a dict
    details = None
    message = str(exc.detail)
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", str(exc.detail))
        details = {k: v for k, v in exc.detail.items() if k != "message"}

    return create_error_response(
        request=request,
        status_code=exc.status_code,
        code=error_code,
        message=message,
        details=details if details else None,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Converts validation errors into a user-friendly format with clear messages.
    """
    logger.warning(
        "validation_error",
        error_count=len(exc.errors()),
        path=request.url.path,
    )

    # Format validation errors into clear messages
    errors = []
    for error in exc.errors():
        # Get the field path (e.g., ["body", "email"] -> "email")
        field_path = " -> ".join(
            str(loc) for loc in error["loc"] if loc not in ["body", "query", "path"]
        )
        field_name = field_path or "request"

        # Get the error message
        error_msg = error["msg"]
        error_type = error["type"]

        # Create user-friendly message
        if error_type == "missing":
            message = f"Field '{field_name}' is required"
        elif error_type == "value_error":
            message = f"Invalid value for '{field_name}': {error_msg}"
        elif error_type == "type_error":
            message = f"Invalid type for '{field_name}': {error_msg}"
        else:
            message = f"{field_name}: {error_msg}"

        errors.append(
            {
                "field": field_name,
                "message": message,
                "type": error_type,
            }
        )

    # Create a summary message
    if len(errors) == 1:
        summary = errors[0]["message"]
    else:
        summary = f"Validation failed for {len(errors)} field(s)"

    return create_error_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        message=summary,
        details={"errors": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions.

    This is a catch-all handler for any exceptions that don't have
    a specific handler. Logs the full error for debugging while
    returning a safe error message to the client.
    """
    logger.error(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        exc_message=str(exc),
        path=request.url.path,
        exc_info=exc,
    )

    # In development, include more details
    # In production, keep it generic for security
    environment = os.getenv("IPK_ENVIRONMENT", "production")

    if environment == "development":
        # SECURITY FIX: Sanitize exception message to avoid leaking sensitive data
        exc_message = str(exc)
        exc_message = _sanitize_sensitive_data(exc_message)

        details = {
            "type": type(exc).__name__,
            "message": exc_message,
        }
    else:
        details = None

    return create_error_response(
        request=request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
        details=details,
    )


def register_exception_handlers(
    app: FastAPI,
    error_formatter: ErrorFormatter | None = None,
) -> None:
    """
    Register all exception handlers with a FastAPI application.

    Args:
        app: FastAPI application instance
        error_formatter: Optional custom error formatter. If provided,
            all error responses will use this formatter's format.

    Usage:
        ```python
        app = FastAPI()
        register_exception_handlers(app)
        ```

    Usage with custom formatter:
        ```python
        from identity_plan_kit.shared.error_formatter import RFC7807ErrorFormatter

        app = FastAPI()
        formatter = RFC7807ErrorFormatter(base_uri="https://api.example.com/errors")
        register_exception_handlers(app, error_formatter=formatter)
        ```
    """
    # Set the global formatter if provided
    if error_formatter is not None:
        set_error_formatter(error_formatter)
    # Auth errors
    app.add_exception_handler(TokenExpiredError, token_expired_handler)
    app.add_exception_handler(TokenInvalidError, token_invalid_handler)
    app.add_exception_handler(RefreshTokenMissingError, refresh_token_missing_handler)
    app.add_exception_handler(RefreshTokenInvalidError, refresh_token_invalid_handler)
    app.add_exception_handler(RefreshTokenExpiredError, refresh_token_expired_handler)
    app.add_exception_handler(OAuthError, oauth_error_handler)
    app.add_exception_handler(UserInactiveError, user_inactive_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(AuthError, auth_error_handler)

    # RBAC errors
    app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
    app.add_exception_handler(RoleNotFoundError, role_not_found_handler)

    # Plan errors
    app.add_exception_handler(QuotaExceededError, quota_exceeded_handler)
    app.add_exception_handler(PlanExpiredError, plan_expired_handler)
    app.add_exception_handler(FeatureNotAvailableError, feature_not_available_handler)
    app.add_exception_handler(UserPlanNotFoundError, user_plan_not_found_handler)
    app.add_exception_handler(PlanNotFoundError, plan_not_found_handler)
    app.add_exception_handler(PlanAuthorizationError, plan_authorization_error_handler)

    # Base error (catch-all for domain errors)
    app.add_exception_handler(BaseError, base_error_handler)

    # FastAPI built-in exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Generic exception handler (must be last - catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.debug("exception_handlers_registered")
