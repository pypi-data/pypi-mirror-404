"""Base Pydantic schemas with common configuration."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class BaseSchema(BaseModel):
    """
    Base schema with common configuration.

    Features:
    - camelCase serialization for API responses
    - from_attributes=True for ORM model conversion
    - Populate by name for accepting both camelCase and snake_case
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


class BaseRequest(BaseSchema):
    """Base schema for request DTOs."""

    pass


class BaseResponse(BaseSchema):
    """Base schema for response DTOs."""

    pass


class TimestampSchemaMixin(BaseModel):
    """
    Mixin for Pydantic schemas with timestamps.

    Note: This is distinct from shared.models.TimestampMixin which is for
    SQLAlchemy ORM models. Use this mixin for Pydantic response schemas.
    """

    created_at: datetime
    updated_at: datetime


# Backward compatibility alias (deprecated - use TimestampSchemaMixin)
TimestampMixin = TimestampSchemaMixin


class ResponseWithTimestamps(BaseResponse, TimestampSchemaMixin):
    """Base response schema with timestamps."""

    pass


class ErrorDetail(BaseSchema):
    """
    Standard error detail schema.

    All error responses from the library follow this structure.

    Attributes:
        code: Machine-readable error code (e.g., "AUTH_ERROR", "VALIDATION_ERROR")
        message: Human-readable error message
        details: Additional error details (optional, can include fields, constraints, etc.)

    Examples:
        Simple error:
        {
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found"
            }
        }

        Error with details:
        {
            "error": {
                "code": "QUOTA_EXCEEDED",
                "message": "Quota exceeded for 'api_calls': 1050/1000 (monthly)",
                "details": {
                    "feature_code": "api_calls",
                    "limit": 1000,
                    "used": 1050,
                    "period": "monthly",
                    "remaining": -50
                }
            }
        }

        Validation error:
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed for 2 field(s)",
                "details": {
                    "errors": [
                        {
                            "field": "email",
                            "message": "Field 'email' is required",
                            "type": "missing"
                        },
                        {
                            "field": "age",
                            "message": "Invalid type for 'age': value is not a valid integer",
                            "type": "type_error"
                        }
                    ]
                }
            }
        }
    """

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseSchema):
    """
    Standard error response schema.

    All errors from the library are wrapped in this structure.
    """

    error: ErrorDetail


class ResponseModel(BaseModel, Generic[T]):
    """
    Standard API response envelope.

    Provides a consistent structure for all API responses:
    {
        "success": true,
        "data": { ... },
        "meta": { ... }
    }

    Usage:
        @router.get("/users/{user_id}", response_model=ResponseModel[UserResponseDto])
        async def get_user(user_id: str) -> ResponseModel[UserResponseDto]:
            user = await user_service.get(user_id)
            return ResponseModel(data=UserResponseDto.model_validate(user))

        # Or use the factory function:
        return ResponseModel.ok(data=user_dto)

    Error response:
        return ResponseModel.error(message="User not found")
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    success: bool = Field(
        default=True,
        description="Indicates whether the request was successful",
    )

    data: T | None = Field(
        default=None,
        description="Response payload",
    )

    meta: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata (pagination, timing, etc.)",
    )

    message: str | None = Field(
        default=None,
        description="Optional message (typically for errors)",
    )

    @classmethod
    def ok(
        cls,
        data: T | None = None,
        meta: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> "ResponseModel[T]":
        """
        Create a successful response.

        Args:
            data: Response payload
            meta: Optional metadata
            message: Optional success message

        Returns:
            ResponseModel with success=True
        """
        return cls(success=True, data=data, meta=meta, message=message)

    @classmethod
    def error(
        cls,
        message: str,
        data: T | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "ResponseModel[T]":
        """
        Create an error response.

        Args:
            message: Error message
            data: Optional error details
            meta: Optional metadata

        Returns:
            ResponseModel with success=False
        """
        return cls(success=False, data=data, meta=meta, message=message)
