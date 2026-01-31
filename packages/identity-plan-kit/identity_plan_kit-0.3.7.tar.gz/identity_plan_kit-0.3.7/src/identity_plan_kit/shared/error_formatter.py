"""Error formatter protocol and default implementation for customizable error responses."""

from abc import ABC, abstractmethod
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ErrorFormatter(ABC):
    """
    Abstract base class for error formatters.

    Implement this class to customize how errors are formatted in API responses.
    This allows integrating applications to use their own error standards
    (e.g., RFC 7807 Problem Details, custom enterprise formats, etc.).

    Example:
        ```python
        from identity_plan_kit.shared.error_formatter import ErrorFormatter

        class RFC7807Formatter(ErrorFormatter):
            def format_error(
                self,
                request: Request,
                status_code: int,
                code: str,
                message: str,
                details: dict | None = None,
            ) -> dict[str, Any]:
                return {
                    "type": f"https://api.example.com/errors/{code.lower()}",
                    "title": code.replace("_", " ").title(),
                    "status": status_code,
                    "detail": message,
                    "instance": str(request.url),
                    **(details or {}),
                }

            def create_response(
                self,
                request: Request,
                status_code: int,
                code: str,
                message: str,
                details: dict | None = None,
            ) -> JSONResponse:
                content = self.format_error(request, status_code, code, message, details)
                return JSONResponse(
                    status_code=status_code,
                    content=content,
                    media_type="application/problem+json",
                )
        ```
    """

    @abstractmethod
    def format_error(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Format an error into a dictionary structure.

        Args:
            request: The FastAPI request object
            status_code: HTTP status code
            code: Error code (e.g., "VALIDATION_ERROR")
            message: Human-readable error message
            details: Additional error details

        Returns:
            Dictionary representing the error response body
        """
        pass

    @abstractmethod
    def create_response(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """
        Create a JSONResponse for the error.

        This method allows customization of the response itself,
        including headers, media type, etc.

        Args:
            request: The FastAPI request object
            status_code: HTTP status code
            code: Error code (e.g., "VALIDATION_ERROR")
            message: Human-readable error message
            details: Additional error details

        Returns:
            JSONResponse with the formatted error
        """
        pass


class DefaultErrorFormatter(ErrorFormatter):
    """
    Default error formatter using the library's standard format.

    Produces responses in the format:
        ```json
        {
            "success": false,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable message",
                "context": { ... }
            }
        }
        ```
    """

    def format_error(
        self,
        request: Request,  # noqa: ARG002
        status_code: int,  # noqa: ARG002
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format error in the default library format."""
        error_content: dict[str, Any] = {
            "code": code,
            "message": message,
        }
        if details:
            error_content["context"] = details
        return {
            "success": False,
            "error": error_content,
        }

    def create_response(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Create a JSONResponse with the default format."""
        content = self.format_error(request, status_code, code, message, details)
        return JSONResponse(status_code=status_code, content=content)


class RFC7807ErrorFormatter(ErrorFormatter):
    """
    Error formatter following RFC 7807 Problem Details for HTTP APIs.

    Produces responses in the format:
        ```json
        {
            "type": "https://example.com/errors/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": "Field 'email' is required",
            "instance": "/api/users"
        }
        ```

    See: https://datatracker.ietf.org/doc/html/rfc7807

    Args:
        base_uri: Base URI for error type URLs (default: "about:blank")
        include_instance: Whether to include the request path as instance
    """

    def __init__(
        self,
        base_uri: str = "about:blank",
        include_instance: bool = True,
    ) -> None:
        self.base_uri = base_uri.rstrip("/")
        self.include_instance = include_instance

    def format_error(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format error according to RFC 7807 Problem Details."""
        # Convert error code to URI-friendly format
        error_slug = code.lower().replace("_", "-")

        # Build the type URI
        if self.base_uri == "about:blank":
            type_uri = "about:blank"
        else:
            type_uri = f"{self.base_uri}/{error_slug}"

        # Create title from code
        title = code.replace("_", " ").title()

        content: dict[str, Any] = {
            "type": type_uri,
            "title": title,
            "status": status_code,
            "detail": message,
        }

        if self.include_instance:
            content["instance"] = str(request.url.path)

        # Include additional details as extension members
        if details:
            # Flatten known fields or include as-is
            for key, value in details.items():
                # Avoid overwriting standard RFC 7807 fields
                if key not in ("type", "title", "status", "detail", "instance"):
                    content[key] = value

        return content

    def create_response(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Create a JSONResponse with RFC 7807 format and media type."""
        content = self.format_error(request, status_code, code, message, details)
        return JSONResponse(
            status_code=status_code,
            content=content,
            media_type="application/problem+json",
        )


# Global formatter instance - can be replaced at setup time
_error_formatter: ErrorFormatter = DefaultErrorFormatter()


def get_error_formatter() -> ErrorFormatter:
    """Get the current error formatter instance."""
    return _error_formatter


def set_error_formatter(formatter: ErrorFormatter) -> None:
    """
    Set the global error formatter.

    This is typically called during application setup via kit.setup().

    Args:
        formatter: The error formatter to use for all error responses
    """
    global _error_formatter
    _error_formatter = formatter


def reset_error_formatter() -> None:
    """Reset to the default error formatter."""
    global _error_formatter
    _error_formatter = DefaultErrorFormatter()
