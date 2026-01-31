"""
Example: Custom Error Response Formats

This example demonstrates how to customize error response formats in identity-plan-kit.
You can use the built-in formatters or create your own.

Use cases:
- Conform to your organization's API standards
- Use RFC 7807 Problem Details format
- Add custom fields to error responses
- Integrate with existing error tracking systems
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig
from identity_plan_kit.shared.error_formatter import (
    DefaultErrorFormatter,
    ErrorFormatter,
    RFC7807ErrorFormatter,
)


# =============================================================================
# Example 1: Using the Default Error Formatter
# =============================================================================
# This is what you get by default - no configuration needed

def example_default_formatter():
    """
    Default error responses look like:
    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Field 'email' is required",
            "details": { ... }
        }
    }
    """
    config = IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://user:pass@localhost/db",
        secret_key="your-secret-key",
        google_client_id="...",
        google_client_secret="...",
        google_redirect_uri="...",
    )

    kit = IdentityPlanKit(config)
    app = FastAPI(lifespan=kit.lifespan)

    # Default formatter is used automatically
    kit.setup(app)

    return app


# =============================================================================
# Example 2: Using RFC 7807 Problem Details Format
# =============================================================================
# Standard format recommended by IETF for HTTP API errors

def example_rfc7807_formatter():
    """
    RFC 7807 error responses look like:
    {
        "type": "https://api.example.com/errors/validation-error",
        "title": "Validation Error",
        "status": 422,
        "detail": "Field 'email' is required",
        "instance": "/api/users"
    }

    Content-Type: application/problem+json
    """
    config = IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://user:pass@localhost/db",
        secret_key="your-secret-key",
        google_client_id="...",
        google_client_secret="...",
        google_redirect_uri="...",
    )

    kit = IdentityPlanKit(config)
    app = FastAPI(lifespan=kit.lifespan)

    # Use RFC 7807 formatter
    kit.setup(
        app,
        error_formatter=RFC7807ErrorFormatter(
            base_uri="https://api.example.com/errors",
            include_instance=True,
        ),
    )

    return app


# =============================================================================
# Example 3: Creating a Custom Error Formatter
# =============================================================================
# Implement your own format to match your organization's standards

class EnterpriseErrorFormatter(ErrorFormatter):
    """
    Custom formatter that matches enterprise API standards.

    Produces responses like:
    {
        "success": false,
        "error_code": "VALIDATION_ERROR",
        "error_message": "Field 'email' is required",
        "request_path": "/api/users",
        "timestamp": "2024-01-15T10:30:00Z",
        "trace_id": "abc123",
        "metadata": { ... }
    }
    """

    def __init__(self, include_timestamp: bool = True):
        self.include_timestamp = include_timestamp

    def format_error(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format error in enterprise format."""
        import datetime

        content: dict[str, Any] = {
            "success": False,
            "error_code": code,
            "error_message": message,
            "http_status": status_code,
            "request_path": str(request.url.path),
        }

        if self.include_timestamp:
            content["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()

        # Add trace ID if available (from RequestIDMiddleware)
        trace_id = getattr(request.state, "request_id", None)
        if trace_id:
            content["trace_id"] = trace_id

        if details:
            content["metadata"] = details

        return content

    def create_response(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Create a JSONResponse with enterprise format."""
        content = self.format_error(request, status_code, code, message, details)
        return JSONResponse(
            status_code=status_code,
            content=content,
            headers={
                "X-Error-Code": code,
            },
        )


def example_enterprise_formatter():
    """Use the custom enterprise formatter."""
    config = IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://user:pass@localhost/db",
        secret_key="your-secret-key",
        google_client_id="...",
        google_client_secret="...",
        google_redirect_uri="...",
    )

    kit = IdentityPlanKit(config)
    app = FastAPI(lifespan=kit.lifespan)

    # Use custom enterprise formatter
    kit.setup(
        app,
        error_formatter=EnterpriseErrorFormatter(include_timestamp=True),
    )

    return app


# =============================================================================
# Example 4: Formatter with Error Tracking Integration
# =============================================================================
# Send errors to external tracking services like Sentry

class SentryIntegratedFormatter(ErrorFormatter):
    """
    Formatter that reports errors to Sentry while returning standard responses.

    This example shows how to integrate error tracking without changing
    the response format.
    """

    def __init__(self, sentry_dsn: str | None = None):
        self.sentry_dsn = sentry_dsn
        self._default_formatter = DefaultErrorFormatter()

        # Initialize Sentry if configured
        if sentry_dsn:
            try:
                import sentry_sdk

                sentry_sdk.init(dsn=sentry_dsn)
                self._sentry_available = True
            except ImportError:
                self._sentry_available = False
        else:
            self._sentry_available = False

    def _report_to_sentry(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Report error to Sentry with context."""
        if not self._sentry_available:
            return

        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_code", code)
            scope.set_tag("http_status", str(status_code))
            scope.set_extra("request_path", str(request.url.path))
            scope.set_extra("request_method", request.method)
            if details:
                scope.set_extra("error_details", details)

            # Only capture server errors (5xx) as exceptions
            if status_code >= 500:
                sentry_sdk.capture_message(
                    f"[{code}] {message}",
                    level="error",
                )

    def format_error(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format error and report to Sentry."""
        # Report to Sentry
        self._report_to_sentry(request, status_code, code, message, details)

        # Use default format for response
        return self._default_formatter.format_error(
            request, status_code, code, message, details
        )

    def create_response(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Create response and report to Sentry."""
        # Report to Sentry
        self._report_to_sentry(request, status_code, code, message, details)

        # Use default format for response
        return self._default_formatter.create_response(
            request, status_code, code, message, details
        )


def example_sentry_integration():
    """Use formatter with Sentry integration."""
    config = IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://user:pass@localhost/db",
        secret_key="your-secret-key",
        google_client_id="...",
        google_client_secret="...",
        google_redirect_uri="...",
    )

    kit = IdentityPlanKit(config)
    app = FastAPI(lifespan=kit.lifespan)

    # Use Sentry-integrated formatter
    kit.setup(
        app,
        error_formatter=SentryIntegratedFormatter(
            sentry_dsn="https://...@sentry.io/..."
        ),
    )

    return app


# =============================================================================
# Example 5: Localized Error Messages
# =============================================================================
# Support multiple languages in error responses

class LocalizedErrorFormatter(ErrorFormatter):
    """
    Formatter that returns localized error messages based on Accept-Language header.

    Supports multiple languages for error messages.
    """

    def __init__(self) -> None:
        # Error message translations
        self.translations: dict[str, dict[str, str]] = {
            "en": {
                "VALIDATION_ERROR": "Validation failed",
                "NOT_FOUND": "Resource not found",
                "AUTHENTICATION_ERROR": "Authentication failed",
                "AUTHORIZATION_ERROR": "Access denied",
                "RATE_LIMIT_EXCEEDED": "Too many requests",
                "INTERNAL_ERROR": "An unexpected error occurred",
            },
            "es": {
                "VALIDATION_ERROR": "Error de validacion",
                "NOT_FOUND": "Recurso no encontrado",
                "AUTHENTICATION_ERROR": "Error de autenticacion",
                "AUTHORIZATION_ERROR": "Acceso denegado",
                "RATE_LIMIT_EXCEEDED": "Demasiadas solicitudes",
                "INTERNAL_ERROR": "Ocurrio un error inesperado",
            },
            "fr": {
                "VALIDATION_ERROR": "Erreur de validation",
                "NOT_FOUND": "Ressource non trouvee",
                "AUTHENTICATION_ERROR": "Echec de l'authentification",
                "AUTHORIZATION_ERROR": "Acces refuse",
                "RATE_LIMIT_EXCEEDED": "Trop de requetes",
                "INTERNAL_ERROR": "Une erreur inattendue s'est produite",
            },
        }

    def _get_language(self, request: Request) -> str:
        """Extract language from Accept-Language header."""
        accept_language = request.headers.get("Accept-Language", "en")
        # Simple parsing - just get the first language code
        lang = accept_language.split(",")[0].split("-")[0].lower()
        return lang if lang in self.translations else "en"

    def _get_localized_title(self, code: str, lang: str) -> str:
        """Get localized title for error code."""
        return self.translations.get(lang, {}).get(code, code.replace("_", " ").title())

    def format_error(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format error with localized title."""
        lang = self._get_language(request)
        localized_title = self._get_localized_title(code, lang)

        content: dict[str, Any] = {
            "error": {
                "code": code,
                "title": localized_title,
                "message": message,  # Keep original message for debugging
                "language": lang,
            }
        }

        if details:
            content["error"]["details"] = details

        return content

    def create_response(
        self,
        request: Request,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """Create a JSONResponse with localized error."""
        lang = self._get_language(request)
        content = self.format_error(request, status_code, code, message, details)
        return JSONResponse(
            status_code=status_code,
            content=content,
            headers={
                "Content-Language": lang,
            },
        )


def example_localized_formatter():
    """Use formatter with localized messages."""
    config = IdentityPlanKitConfig(
        database_url="postgresql+asyncpg://user:pass@localhost/db",
        secret_key="your-secret-key",
        google_client_id="...",
        google_client_secret="...",
        google_redirect_uri="...",
    )

    kit = IdentityPlanKit(config)
    app = FastAPI(lifespan=kit.lifespan)

    # Use localized formatter
    kit.setup(
        app,
        error_formatter=LocalizedErrorFormatter(),
    )

    return app


# =============================================================================
# Running the examples
# =============================================================================

if __name__ == "__main__":
    print("Custom Error Format Examples")
    print("============================")
    print()
    print("1. Default format:     example_default_formatter()")
    print("2. RFC 7807 format:    example_rfc7807_formatter()")
    print("3. Enterprise format:  example_enterprise_formatter()")
    print("4. Sentry integration: example_sentry_integration()")
    print("5. Localized errors:   example_localized_formatter()")
    print()
    print("To use in your app, import and configure:")
    print()
    print("  from identity_plan_kit import IdentityPlanKit, RFC7807ErrorFormatter")
    print()
    print("  kit.setup(")
    print("      app,")
    print("      error_formatter=RFC7807ErrorFormatter(")
    print('          base_uri="https://api.example.com/errors"')
    print("      ),")
    print("  )")
