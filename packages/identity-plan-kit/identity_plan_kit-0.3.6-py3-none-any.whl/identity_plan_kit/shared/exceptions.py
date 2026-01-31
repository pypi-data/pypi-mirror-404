"""Base exceptions with error codes."""

from typing import Any


class BaseError(Exception):
    """
    Base exception class with error code support.

    All custom exceptions should inherit from this class.
    """

    code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred"
    status_code: int = 500

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.details = details
        super().__init__(self.message)

    @property
    def context(self) -> dict[str, Any] | None:
        """Alias for details to support context naming convention."""
        return self.details

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to error response dict."""
        error_content: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            error_content["context"] = self.details
        return {
            "success": False,
            "error": error_content,
        }


class NotFoundError(BaseError):
    """Resource not found."""

    code = "NOT_FOUND"
    message = "Resource not found"
    status_code = 404


class ValidationError(BaseError):
    """Validation error."""

    code = "VALIDATION_ERROR"
    message = "Validation failed"
    status_code = 422


class AuthenticationError(BaseError):
    """Authentication error."""

    code = "AUTHENTICATION_ERROR"
    message = "Authentication failed"
    status_code = 401


class AuthorizationError(BaseError):
    """Authorization error."""

    code = "AUTHORIZATION_ERROR"
    message = "Access denied"
    status_code = 403


class ConflictError(BaseError):
    """Resource conflict."""

    code = "CONFLICT"
    message = "Resource conflict"
    status_code = 409


class RateLimitError(BaseError):
    """Rate limit exceeded."""

    code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded"
    status_code = 429
