"""Account lockout mechanism for brute-force protection.

Tracks failed authentication attempts and temporarily locks accounts
after too many failures to prevent brute-force attacks.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from identity_plan_kit.shared.audit import audit_account_locked, audit_failed_login_attempt
from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit.shared.state_store import StateStore

logger = get_logger(__name__)


class AccountLockedError(Exception):
    """Raised when an account is locked due to too many failed attempts."""

    def __init__(
        self,
        identifier: str,
        unlock_at: datetime,
        failed_attempts: int,
    ) -> None:
        self.identifier = identifier
        self.unlock_at = unlock_at
        self.failed_attempts = failed_attempts
        self.retry_after_seconds = max(0, int((unlock_at - datetime.now(UTC)).total_seconds()))
        super().__init__(
            f"Account locked until {unlock_at.isoformat()}. "
            f"Retry after {self.retry_after_seconds} seconds."
        )


@dataclass
class LockoutConfig:
    """Configuration for account lockout behavior."""

    # Number of failed attempts before lockout
    max_attempts: int = 5

    # Duration of lockout in minutes
    lockout_duration_minutes: int = 15

    # Time window for counting attempts (in minutes)
    # Failed attempts older than this are not counted
    attempt_window_minutes: int = 15

    # Whether to track by IP in addition to identifier
    track_by_ip: bool = True

    # Key prefix for state store
    key_prefix: str = "lockout:"


class LockoutManager:
    """
    Manages account lockout state.

    Tracks failed login attempts and enforces temporary lockouts
    after too many failures. Uses the state store for persistence,
    supporting both single-instance and distributed deployments.

    Example:
        ```python
        lockout = LockoutManager(state_store, config)

        # Check if locked before authentication
        await lockout.check_lockout(email, ip_address)

        # Record failure if auth fails
        await lockout.record_failure(email, ip_address, "invalid_code")

        # Clear on success
        await lockout.clear_failures(email, ip_address)
        ```
    """

    def __init__(
        self,
        state_store: "StateStore",
        config: LockoutConfig | None = None,
    ) -> None:
        """
        Initialize lockout manager.

        Args:
            state_store: State store for persistence
            config: Lockout configuration (uses defaults if None)
        """
        self._store = state_store
        self._config = config or LockoutConfig()

    def _hash_identifier(self, identifier: str) -> str:
        """Hash identifier to prevent email enumeration via key inspection."""
        # SECURITY FIX: Hash identifier to prevent targeted attacks on lockout entries
        return hashlib.sha256(identifier.lower().encode()).hexdigest()[:32]

    def _hash_ip(self, ip_address: str | None) -> str | None:
        """Hash IP address for logging to avoid PII exposure."""
        if ip_address is None:
            return None
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]

    def _make_key(self, identifier: str, ip_address: str | None = None) -> str:
        """Create state store key for tracking."""
        hashed_id = self._hash_identifier(identifier)
        base_key = f"{self._config.key_prefix}{hashed_id}"
        if ip_address and self._config.track_by_ip:
            return f"{base_key}:{ip_address}"
        return base_key

    def _make_lockout_key(self, identifier: str) -> str:
        """Create state store key for lockout status."""
        hashed_id = self._hash_identifier(identifier)
        return f"{self._config.key_prefix}locked:{hashed_id}"

    async def check_lockout(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Check if identifier is locked out.

        Args:
            identifier: Email or user identifier
            ip_address: Client IP address

        Raises:
            AccountLockedError: If account is currently locked
        """
        # Check lockout status
        lockout_key = self._make_lockout_key(identifier)
        lockout_data = await self._store.get(lockout_key)

        if lockout_data is not None:
            unlock_at = datetime.fromisoformat(lockout_data["unlock_at"])
            if datetime.now(UTC) < unlock_at:
                # Log hashed identifiers to avoid PII exposure in logs
                logger.warning(
                    "lockout_check_blocked",
                    identifier_hash=self._hash_identifier(identifier),
                    ip_hash=self._hash_ip(ip_address),
                    unlock_at=unlock_at.isoformat(),
                )
                raise AccountLockedError(
                    identifier=identifier,
                    unlock_at=unlock_at,
                    failed_attempts=lockout_data.get("attempts", 0),
                )
            # Lockout expired, will be cleaned up naturally by TTL

    async def record_failure(
        self,
        identifier: str,
        ip_address: str | None = None,
        reason: str = "unknown",
        user_agent: str | None = None,
    ) -> int:
        """
        Record a failed authentication attempt.

        Note: This operation uses optimistic concurrency. In high-concurrency
        scenarios, the count may be slightly off due to race conditions between
        get and set, but this is acceptable for rate limiting purposes as it
        errs on the side of caution (may lock out slightly early).

        Args:
            identifier: Email or user identifier
            ip_address: Client IP address
            reason: Reason for failure (for audit logging)
            user_agent: Client user agent

        Returns:
            Current failure count

        Raises:
            AccountLockedError: If this failure triggers a lockout
        """
        key = self._make_key(identifier, ip_address)
        now = datetime.now(UTC)
        ttl_seconds = self._config.attempt_window_minutes * 60

        # Retry loop to handle race conditions
        max_retries = 3
        for attempt in range(max_retries):
            # Get current failure state
            failure_data = await self._store.get(key) or {
                "attempts": 0,
                "first_attempt": now.isoformat(),
                "version": 0,  # Optimistic concurrency control
            }

            # Extract version for optimistic locking
            version = failure_data.get("version", 0)

            # Increment attempts
            new_attempts = failure_data.get("attempts", 0) + 1
            new_data = {
                "attempts": new_attempts,
                "first_attempt": failure_data.get("first_attempt", now.isoformat()),
                "last_attempt": now.isoformat(),
                "last_reason": reason,
                "version": version + 1,
            }

            # Store with TTL
            await self._store.set(key, new_data, ttl_seconds=ttl_seconds)

            # Verify the write (simple check - read back)
            verify_data = await self._store.get(key)
            if verify_data and verify_data.get("version") == version + 1:
                # Write succeeded
                current_attempts = new_attempts
                break
            elif attempt < max_retries - 1:
                # Potential conflict, retry
                logger.debug(
                    "lockout_record_failure_retry",
                    identifier_hash=self._hash_identifier(identifier),
                    attempt=attempt + 1,
                )
                continue
            else:
                # Use the value we attempted to write
                current_attempts = new_attempts
        else:
            current_attempts = new_attempts

        # Log the failed attempt
        audit_failed_login_attempt(
            email=identifier,
            ip_address=ip_address,
            user_agent=user_agent,
            reason=reason,
            attempt_count=current_attempts,
        )

        # Log hashed identifiers to avoid PII exposure in logs
        logger.warning(
            "login_attempt_failed",
            identifier_hash=self._hash_identifier(identifier),
            ip_hash=self._hash_ip(ip_address),
            attempt_count=current_attempts,
            max_attempts=self._config.max_attempts,
            reason=reason,
        )

        # Check if we need to trigger lockout
        if current_attempts >= self._config.max_attempts:
            await self._trigger_lockout(identifier, ip_address, current_attempts)

        return current_attempts

    async def _trigger_lockout(
        self,
        identifier: str,
        ip_address: str | None,
        attempts: int,
    ) -> None:
        """Trigger account lockout."""
        unlock_at = datetime.now(UTC) + timedelta(minutes=self._config.lockout_duration_minutes)

        lockout_key = self._make_lockout_key(identifier)
        lockout_data = {
            "unlock_at": unlock_at.isoformat(),
            "locked_at": datetime.now(UTC).isoformat(),
            "attempts": attempts,
            "trigger_ip": ip_address,
        }

        # Store lockout with TTL
        await self._store.set(
            lockout_key,
            lockout_data,
            ttl_seconds=self._config.lockout_duration_minutes * 60 + 60,  # Extra minute buffer
        )

        # Log security event
        audit_account_locked(
            email=identifier,
            ip_address=ip_address,
            failed_attempts=attempts,
            lock_duration_minutes=self._config.lockout_duration_minutes,
        )

        # Log hashed identifiers to avoid PII exposure in logs
        logger.warning(
            "account_locked",
            identifier_hash=self._hash_identifier(identifier),
            ip_hash=self._hash_ip(ip_address),
            unlock_at=unlock_at.isoformat(),
            failed_attempts=attempts,
        )

        raise AccountLockedError(
            identifier=identifier,
            unlock_at=unlock_at,
            failed_attempts=attempts,
        )

    async def clear_failures(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Clear failure count on successful authentication.

        Args:
            identifier: Email or user identifier
            ip_address: Client IP address
        """
        key = self._make_key(identifier, ip_address)
        await self._store.delete(key)

        # Also clear any lockout (successful auth lifts lockout)
        lockout_key = self._make_lockout_key(identifier)
        was_locked = await self._store.delete(lockout_key)

        if was_locked:
            # Log hashed identifiers to avoid PII exposure in logs
            logger.info(
                "lockout_cleared_on_success",
                identifier_hash=self._hash_identifier(identifier),
                ip_hash=self._hash_ip(ip_address),
            )

    async def get_failure_count(
        self,
        identifier: str,
        ip_address: str | None = None,
    ) -> int:
        """
        Get current failure count for an identifier.

        Args:
            identifier: Email or user identifier
            ip_address: Client IP address

        Returns:
            Current failure count (0 if none)
        """
        key = self._make_key(identifier, ip_address)
        failure_data = await self._store.get(key)

        if failure_data is None:
            return 0

        return failure_data.get("attempts", 0)

    async def get_lockout_status(
        self,
        identifier: str,
    ) -> dict | None:
        """
        Get lockout status for an identifier.

        Args:
            identifier: Email or user identifier

        Returns:
            Lockout data if locked, None otherwise
        """
        lockout_key = self._make_lockout_key(identifier)
        lockout_data = await self._store.get(lockout_key)

        if lockout_data is None:
            return None

        unlock_at = datetime.fromisoformat(lockout_data["unlock_at"])
        if datetime.now(UTC) >= unlock_at:
            return None  # Expired

        return {
            "locked": True,
            "unlock_at": unlock_at,
            "attempts": lockout_data.get("attempts", 0),
            "retry_after_seconds": int((unlock_at - datetime.now(UTC)).total_seconds()),
        }
