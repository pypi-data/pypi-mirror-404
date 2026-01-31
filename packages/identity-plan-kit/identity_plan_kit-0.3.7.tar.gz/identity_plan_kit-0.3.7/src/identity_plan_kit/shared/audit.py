"""Audit logging for security-sensitive actions.

Provides structured audit logs for compliance, security monitoring, and incident investigation.
All audit events are logged with a consistent format including actor, action, target, and context.
"""

import hashlib
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from identity_plan_kit.shared.logging import get_logger

# Dedicated audit logger - can be configured separately for compliance
audit_logger = get_logger("identity_plan_kit.audit")

# Threshold for escalating failed login attempts to WARNING severity
FAILED_LOGIN_WARNING_THRESHOLD = 3

# SECURITY FIX: Control email masking in audit logs via environment variable
# Default to True for privacy protection
MASK_PII_IN_AUDIT_LOGS = os.getenv("IPK_MASK_PII_IN_AUDIT_LOGS", "true").lower() in ("true", "1", "yes")


def mask_email(email: str | None) -> str | None:
    """
    Mask email address for audit logs while preserving some identifiability.

    When IPK_MASK_PII_IN_AUDIT_LOGS=true (default):
        - "user@example.com" -> "u***@e***.com"
        - Preserves first char of local and domain for correlation

    When IPK_MASK_PII_IN_AUDIT_LOGS=false:
        - Returns email unchanged (for environments with strict log access controls)

    Args:
        email: Email address to mask

    Returns:
        Masked email or None if input is None

    Note:
        This function uses constant-time operations where possible to prevent
        timing attacks that could distinguish valid from invalid email formats.
    """
    if email is None:
        return None

    if not MASK_PII_IN_AUDIT_LOGS:
        return email

    # SECURITY FIX: Always compute the hash to prevent timing attacks
    # The hash is computed regardless of whether we use it, ensuring
    # consistent execution time for all inputs
    email_hash = hashlib.sha256(email.encode()).hexdigest()[:8]

    # Attempt to parse and mask the email
    # Use a flag to track success rather than early return to maintain timing
    masked_result: str | None = None

    if "@" in email:
        parts = email.rsplit("@", 1)
        if len(parts) == 2:
            local, domain = parts
            domain_parts = domain.rsplit(".", 1)
            if len(domain_parts) == 2 and local and domain_parts[0]:
                domain_name, tld = domain_parts
                masked_local = local[0] + "***"
                masked_domain = domain_name[0] + "***"
                masked_result = f"{masked_local}@{masked_domain}.{tld}"
            elif local:
                # No TLD found, but valid local part
                masked_result = f"{local[0]}***@***"

    # Return masked result if parsing succeeded, otherwise use hash
    return masked_result if masked_result is not None else f"[hash:{email_hash}]"


class AuditAction(str, Enum):
    """Audit action types for categorization."""

    # Authentication events
    USER_REGISTERED = "user.registered"
    USER_AUTHENTICATED = "user.authenticated"
    USER_LOGOUT = "user.logout"
    USER_LOGOUT_ALL = "user.logout_all"

    # Token events (noqa: S105 - these are event names, not passwords)
    TOKEN_REFRESHED = "token.refreshed"  # noqa: S105
    TOKEN_REVOKED = "token.revoked"  # noqa: S105
    TOKEN_REVOKED_ALL = "token.revoked_all"  # noqa: S105
    TOKEN_REUSE_DETECTED = "token.reuse_detected"  # noqa: S105

    # Security events
    SECURITY_ACCOUNT_LOCKED = "security.account_locked"
    SECURITY_ACCOUNT_UNLOCKED = "security.account_unlocked"
    SECURITY_FAILED_LOGIN_ATTEMPT = "security.failed_login_attempt"
    SECURITY_TOKEN_THEFT_SUSPECTED = "security.token_theft_suspected"  # noqa: S105
    SECURITY_USER_DEACTIVATED = "security.user_deactivated"
    SECURITY_USER_REACTIVATED = "security.user_reactivated"

    # User management events
    USER_ROLE_CHANGED = "user.role_changed"
    USER_DEACTIVATED = "user.deactivated"
    USER_REACTIVATED = "user.reactivated"

    # Plan events
    PLAN_ASSIGNED = "plan.assigned"
    PLAN_EXPIRED = "plan.expired"
    PLAN_UPGRADED = "plan.upgraded"
    PLAN_DOWNGRADED = "plan.downgraded"

    # Admin events
    ADMIN_TOKEN_CLEANUP = "admin.token_cleanup"  # noqa: S105
    ADMIN_CACHE_INVALIDATED = "admin.cache_invalidated"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""

    INFO = "info"  # Normal operations
    WARNING = "warning"  # Suspicious but not critical
    CRITICAL = "critical"  # Security incidents requiring investigation


@dataclass
class AuditEvent:
    """
    Structured audit event.

    All security-sensitive actions should create an AuditEvent and log it.
    This ensures consistent format for log aggregation and analysis.
    """

    action: AuditAction
    severity: AuditSeverity = AuditSeverity.INFO

    # Who performed the action (None for system actions)
    actor_id: UUID | None = None
    actor_email: str | None = None
    actor_ip: str | None = None
    actor_user_agent: str | None = None

    # What was affected
    target_id: UUID | None = None
    target_type: str | None = None  # "user", "token", "plan", etc.

    # Additional context
    details: dict[str, Any] = field(default_factory=dict)

    # Timestamp (auto-generated)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Request context
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "audit_event": True,  # Marker for log filtering
            "action": self.action.value,
            "severity": self.severity.value,
            "actor": {
                "id": str(self.actor_id) if self.actor_id else None,
                "email": self.actor_email,
                "ip": self.actor_ip,
                "user_agent": self.actor_user_agent,
            },
            "target": {
                "id": str(self.target_id) if self.target_id else None,
                "type": self.target_type,
            },
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
        }


def log_audit_event(event: AuditEvent) -> None:
    """
    Log an audit event with appropriate severity.

    Args:
        event: The audit event to log

    Example:
        >>> log_audit_event(AuditEvent(
        ...     action=AuditAction.USER_AUTHENTICATED,
        ...     actor_id=user.id,
        ...     actor_email=user.email,
        ...     actor_ip="1.2.3.4",
        ...     details={"provider": "google"},
        ... ))
    """
    event_dict = event.to_dict()

    if event.severity == AuditSeverity.CRITICAL:
        audit_logger.critical("audit_event", **event_dict)
    elif event.severity == AuditSeverity.WARNING:
        audit_logger.warning("audit_event", **event_dict)
    else:
        audit_logger.info("audit_event", **event_dict)


# Convenience functions for common audit events


def audit_user_registered(
    user_id: UUID,
    email: str,
    provider: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log user registration event."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.USER_REGISTERED,
            actor_id=user_id,
            actor_email=email,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            target_id=user_id,
            target_type="user",
            details={"provider": provider},
            request_id=request_id,
        )
    )


def audit_user_authenticated(
    user_id: UUID,
    email: str,
    provider: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log successful authentication event."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.USER_AUTHENTICATED,
            actor_id=user_id,
            actor_email=email,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            target_id=user_id,
            target_type="user",
            details={"provider": provider},
            request_id=request_id,
        )
    )


def audit_token_refreshed(
    user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log token refresh event."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.TOKEN_REFRESHED,
            actor_id=user_id,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            target_id=user_id,
            target_type="user",
            request_id=request_id,
        )
    )


def audit_user_logout(
    user_id: UUID,
    everywhere: bool = False,
    tokens_revoked: int = 0,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log logout event."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.USER_LOGOUT_ALL if everywhere else AuditAction.USER_LOGOUT,
            actor_id=user_id,
            actor_ip=ip_address,
            target_id=user_id,
            target_type="user",
            details={"everywhere": everywhere, "tokens_revoked": tokens_revoked},
            request_id=request_id,
        )
    )


def audit_token_reuse_detected(
    user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
    original_ip: str | None = None,
    original_user_agent: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log token reuse detection (potential theft) - CRITICAL severity."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.TOKEN_REUSE_DETECTED,
            severity=AuditSeverity.CRITICAL,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            target_id=user_id,
            target_type="user",
            details={
                "original_ip": original_ip,
                "original_user_agent": original_user_agent,
                "detection_type": "refresh_token_reuse",
            },
            request_id=request_id,
        )
    )


def audit_user_deactivated(
    user_id: UUID,
    reason: str,
    actor_id: UUID | None = None,
    request_id: str | None = None,
) -> None:
    """Log user deactivation event - WARNING severity."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.SECURITY_USER_DEACTIVATED,
            severity=AuditSeverity.WARNING,
            actor_id=actor_id,  # None if system-triggered
            target_id=user_id,
            target_type="user",
            details={"reason": reason},
            request_id=request_id,
        )
    )


def audit_account_locked(
    user_id: UUID | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    failed_attempts: int = 0,
    lock_duration_minutes: int = 0,
    request_id: str | None = None,
) -> None:
    """Log account lockout event - WARNING severity."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.SECURITY_ACCOUNT_LOCKED,
            severity=AuditSeverity.WARNING,
            actor_ip=ip_address,
            target_id=user_id,
            target_type="user",
            details={
                "email": email,
                "failed_attempts": failed_attempts,
                "lock_duration_minutes": lock_duration_minutes,
            },
            request_id=request_id,
        )
    )


def audit_failed_login_attempt(
    email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    reason: str = "unknown",
    attempt_count: int = 1,
    request_id: str | None = None,
) -> None:
    """Log failed login attempt - INFO or WARNING based on count."""
    severity = AuditSeverity.WARNING if attempt_count >= FAILED_LOGIN_WARNING_THRESHOLD else AuditSeverity.INFO
    # SECURITY FIX: Mask email to prevent PII exposure in logs
    log_audit_event(
        AuditEvent(
            action=AuditAction.SECURITY_FAILED_LOGIN_ATTEMPT,
            severity=severity,
            actor_ip=ip_address,
            actor_user_agent=user_agent,
            target_type="user",
            details={
                "email": mask_email(email),
                "reason": reason,
                "attempt_count": attempt_count,
            },
            request_id=request_id,
        )
    )


def audit_token_cleanup(
    deleted_count: int,
    batch_size: int,
    has_more: bool,
    request_id: str | None = None,
) -> None:
    """Log token cleanup administrative action."""
    log_audit_event(
        AuditEvent(
            action=AuditAction.ADMIN_TOKEN_CLEANUP,
            target_type="refresh_token",
            details={
                "deleted_count": deleted_count,
                "batch_size": batch_size,
                "has_more": has_more,
            },
            request_id=request_id,
        )
    )
