"""
IdentityPlanKit - Modern FastAPI library for authentication, RBAC, and subscription plans.

Features:
- OAuth authentication (Google)
- Role-Based Access Control (RBAC)
- Subscription plan management
- Feature usage tracking with quotas
- Audit logging for security events
- Account lockout protection
- Prometheus metrics (optional, requires metrics extra)

Configuration:
    The library supports flexible configuration:

    1. Direct instantiation:
        config = IdentityPlanKitConfig(database_url=..., secret_key=...)

    2. Custom env prefix:
        config = IdentityPlanKitConfig.from_env(prefix="MYAPP_")

    3. From existing settings:
        config = IdentityPlanKitConfig.from_settings(settings, mapping={...})

External Session Factory (for existing apps):
    Share your app's database connection pool with IPK:

    from identity_plan_kit import IdentityPlanKit, IdentityPlanKitConfig
    from your_app.database import session_factory

    kit = IdentityPlanKit(config, session_factory=session_factory)

Direct Repository Access (for transaction participation):
    Use repositories directly within your app's transactions:

    from identity_plan_kit.auth import UserRepository, AuthUnitOfWork
    from identity_plan_kit.plans import PlanRepository, PlansUnitOfWork

    async with your_session.begin():
        async with AuthUnitOfWork(session_factory, session=your_session) as uow:
            user = await uow.users.get_by_email(email)
            # Your other operations in same transaction

Migration Integration:
    For integrating with your Alembic setup, see identity_plan_kit.migrations:

    from identity_plan_kit.migrations import (
        Base,           # SQLAlchemy declarative base
        BaseModel,      # Base model with UUID7 + timestamps
        configure_alembic_for_ipk,  # Helper for env.py
    )
"""

from identity_plan_kit.auth.dependencies import CurrentUser, OptionalUser
from identity_plan_kit.config import Environment, IdentityPlanKitConfig
from identity_plan_kit.kit import (
    IdentityPlanKit,
    __version__,
)
from identity_plan_kit.migrations import (
    Base,
    BaseIntModel,
    BaseModel,
    IntPrimaryKeyMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    configure_alembic_for_ipk,
    get_ipk_metadata,
    import_all_models,
)
from identity_plan_kit.plans.dto.usage import UsageInfo
from identity_plan_kit.shared.audit import AuditAction, AuditEvent, log_audit_event
from identity_plan_kit.shared.database import DatabaseManager
from identity_plan_kit.shared.error_formatter import (
    DefaultErrorFormatter,
    ErrorFormatter,
    RFC7807ErrorFormatter,
)
from identity_plan_kit.shared.schemas import ResponseModel
from identity_plan_kit.shared.exception_handlers import register_exception_handlers
from identity_plan_kit.shared.lockout import AccountLockedError, LockoutConfig
from identity_plan_kit.shared.metrics import (
    MetricsManager,
    get_metrics_manager,
    is_prometheus_available,
)
from identity_plan_kit.shared.state_store import StateStoreManager
from identity_plan_kit.shared.uow import BaseUnitOfWork

__all__ = [
    # Account lockout
    "AccountLockedError",
    # Audit logging
    "AuditAction",
    "AuditEvent",
    # Migration/Model base classes
    "Base",
    "BaseIntModel",
    "BaseModel",
    # Base Unit of Work
    "BaseUnitOfWork",
    # Auth dependencies
    "CurrentUser",
    # Manager classes
    "DatabaseManager",
    # Error formatters
    "DefaultErrorFormatter",
    "Environment",
    "ErrorFormatter",
    # Core
    "IdentityPlanKit",
    "IdentityPlanKitConfig",
    # Mixins for custom models
    "IntPrimaryKeyMixin",
    "LockoutConfig",
    # Metrics (optional - requires prometheus-client)
    "MetricsManager",
    "OptionalUser",
    # RFC 7807 error formatter
    "RFC7807ErrorFormatter",
    # Response model
    "ResponseModel",
    "StateStoreManager",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # DTOs
    "UsageInfo",
    # Version
    "__version__",
    # Migration helpers
    "configure_alembic_for_ipk",
    "get_ipk_metadata",
    "get_metrics_manager",
    "import_all_models",
    "is_prometheus_available",
    "log_audit_event",
    # Exception handlers
    "register_exception_handlers",
]
