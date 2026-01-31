"""Shared infrastructure modules."""

from identity_plan_kit.shared.audit import (
    AuditAction,
    AuditEvent,
    AuditSeverity,
    log_audit_event,
)
from identity_plan_kit.shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
)
from identity_plan_kit.shared.cleanup_scheduler import (
    CleanupConfig,
    CleanupScheduler,
    create_cleanup_scheduler_for_kit,
)
from identity_plan_kit.shared.database import (
    Base,
    DatabaseManager,
    with_db_retry,
)
from identity_plan_kit.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from identity_plan_kit.shared.http_utils import get_client_ip, get_user_agent
from identity_plan_kit.shared.lockout import (
    AccountLockedError,
    LockoutConfig,
    LockoutManager,
)
from identity_plan_kit.shared.logging import configure_logging, get_logger
from identity_plan_kit.shared.models import (
    BaseIntModel,
    BaseModel,
    IntPrimaryKeyMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from identity_plan_kit.shared.rate_limiter import (
    create_limiter,
    get_rate_limiter,
    init_rate_limiter,
)
from identity_plan_kit.shared.schemas import (
    BaseRequest,
    BaseResponse,
    BaseSchema,
    ErrorDetail,
    ErrorResponse,
    ResponseWithTimestamps,
)
from identity_plan_kit.shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_token_hash,
)
from identity_plan_kit.shared.state_store import (
    InMemoryStateStore,
    InvalidKeyError,
    RedisStateStore,
    StateStore,
    StateStoreManager,
    close_state_store,
    get_state_store,
    init_state_store,
)
from identity_plan_kit.shared.uow import AbstractUnitOfWork, BaseUnitOfWork
from identity_plan_kit.shared.uuid7 import uuid7, uuid7_str

# Note: register_exception_handlers moved to avoid circular import
# Import it directly: from identity_plan_kit.shared.exception_handlers import register_exception_handlers

__all__ = [
    # Unit of Work
    "AbstractUnitOfWork",
    # Lockout (P1 fix)
    "AccountLockedError",
    # Audit logging (P1 fix)
    "AuditAction",
    "AuditEvent",
    "AuditSeverity",
    "AuthenticationError",
    "AuthorizationError",
    # Database
    "Base",
    # Exceptions
    "BaseError",
    "BaseIntModel",
    # Models
    "BaseModel",
    "BaseRequest",
    "BaseResponse",
    # Schemas
    "BaseSchema",
    "BaseUnitOfWork",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitState",
    # Cleanup scheduler (P1 fix)
    "CleanupConfig",
    "CleanupScheduler",
    "ConflictError",
    "DatabaseManager",
    "ErrorDetail",
    "ErrorResponse",
    "InMemoryStateStore",
    "IntPrimaryKeyMixin",
    "InvalidKeyError",
    "LockoutConfig",
    "LockoutManager",
    "NotFoundError",
    "RateLimitError",
    "RedisStateStore",
    "ResponseWithTimestamps",
    # State Store
    "StateStore",
    "StateStoreManager",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "ValidationError",
    "close_state_store",
    # Logging
    "configure_logging",
    # Security
    "create_access_token",
    "create_cleanup_scheduler_for_kit",
    # Rate Limiter
    "create_limiter",
    "create_refresh_token",
    "decode_token",
    # HTTP Utils
    "get_client_ip",
    "get_logger",
    "get_rate_limiter",
    "get_state_store",
    "get_user_agent",
    "hash_token",
    "init_rate_limiter",
    "init_state_store",
    "log_audit_event",
    # UUID
    "uuid7",
    "uuid7_str",
    "verify_token_hash",
    "with_db_retry",
    # Note: register_exception_handlers not exported here to avoid circular import
    # Import it directly: from identity_plan_kit.shared.exception_handlers import register_exception_handlers
]
