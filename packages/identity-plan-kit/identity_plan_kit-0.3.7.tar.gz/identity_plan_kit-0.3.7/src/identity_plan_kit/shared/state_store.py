"""State store for CSRF tokens and short-lived data."""

import asyncio
import contextlib
import json
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from identity_plan_kit.shared.constants import (
    MAX_KEY_DISPLAY_LENGTH,
    REDIS_CIRCUIT_FAILURE_THRESHOLD,
    REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS,
    REDIS_CIRCUIT_RECOVERY_TIMEOUT,
    REDIS_RETRY_ATTEMPTS,
    REDIS_RETRY_BASE_DELAY,
    REDIS_SOCKET_CONNECT_TIMEOUT,
    REDIS_SOCKET_TIMEOUT,
    STATE_STORE_MAX_CONSECUTIVE_ERRORS,
    STATE_STORE_MAX_KEY_LENGTH,
)
from identity_plan_kit.shared.logging import get_logger

if TYPE_CHECKING:
    from identity_plan_kit.shared.health import ComponentHealth

# Type alias for JSON-serializable values stored in the state store
JsonValue = dict[str, object] | list[object] | str | int | float | bool | None

logger = get_logger(__name__)


class RedisCircuitState(Enum):
    """Circuit breaker states for Redis."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

# Key validation: alphanumeric, underscores, hyphens, colons, and dots only
# Max length STATE_STORE_MAX_KEY_LENGTH chars to prevent memory issues
_KEY_PATTERN = re.compile(rf"^[a-zA-Z0-9_\-:.]{{1,{STATE_STORE_MAX_KEY_LENGTH}}}$")


class InvalidKeyError(ValueError):
    """Raised when a state store key is invalid."""

    pass


def _validate_key(key: str) -> None:
    """
    Validate state store key format.

    Keys must be 1-STATE_STORE_MAX_KEY_LENGTH characters and contain only:
    - Alphanumeric characters (a-z, A-Z, 0-9)
    - Underscores (_), hyphens (-), colons (:), dots (.)

    Args:
        key: The key to validate

    Raises:
        InvalidKeyError: If key format is invalid
    """
    if not key:
        raise InvalidKeyError("State store key cannot be empty")
    if not _KEY_PATTERN.match(key):
        truncated = key[:MAX_KEY_DISPLAY_LENGTH]
        ellipsis = "..." if len(key) > MAX_KEY_DISPLAY_LENGTH else ""
        raise InvalidKeyError(
            f"Invalid state store key format: '{truncated}{ellipsis}'. "
            f"Keys must be 1-{STATE_STORE_MAX_KEY_LENGTH} characters containing only alphanumeric, "
            "underscore, hyphen, colon, or dot characters."
        )

# Optional Redis support - gracefully degrade if not installed
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False


class StateStore(ABC):
    """Abstract base class for state storage."""

    @abstractmethod
    async def set(self, key: str, value: JsonValue, ttl_seconds: int = 300) -> None:
        """Store a value with TTL."""
        pass

    @abstractmethod
    async def get(self, key: str) -> JsonValue | None:
        """Get a value by key. Returns None if not found or expired."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass


class InMemoryStateStore(StateStore):
    """
    In-memory state store with TTL support.

    Suitable for single-instance deployments.
    For multi-instance deployments, use Redis-backed store.
    """

    # Import constants - using module-level imports
    from identity_plan_kit.shared.constants import (
        DEFAULT_MAX_CACHE_ENTRIES as MAX_ENTRIES,
    )

    # Maximum consecutive errors before logging critical warning
    MAX_CONSECUTIVE_ERRORS = STATE_STORE_MAX_CONSECUTIVE_ERRORS

    def __init__(self) -> None:
        self._store: dict[str, tuple[JsonValue, datetime]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task[None] | None = None
        self._consecutive_errors = 0

    async def start(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.debug("state_store_started")

    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            self._cleanup_task = None
            logger.debug("state_store_stopped")

    async def _cleanup_loop(self) -> None:
        """Periodically clean up expired entries with error supervision."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self._cleanup_expired()
                self._consecutive_errors = 0  # Reset on success
            except asyncio.CancelledError:
                break
            except Exception:
                self._consecutive_errors += 1
                logger.exception(
                    "state_store_cleanup_error",
                    consecutive_errors=self._consecutive_errors,
                )
                if self._consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    logger.critical(
                        "state_store_cleanup_failing_repeatedly",
                        consecutive_errors=self._consecutive_errors,
                        message="State store cleanup has failed multiple times. "
                        "Memory may grow unbounded.",
                    )

    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = datetime.now(UTC)
        async with self._lock:
            expired_keys = [key for key, (_, expires_at) in self._store.items() if expires_at < now]
            for key in expired_keys:
                del self._store[key]
            if expired_keys:
                logger.debug("state_store_cleanup", removed=len(expired_keys))

    async def set(self, key: str, value: JsonValue, ttl_seconds: int = 300) -> None:
        """Store a value with TTL."""
        _validate_key(key)
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

        # P2 FIX: Minimize lock contention by checking outside lock first
        # This is a hint - we may still need to cleanup after acquiring lock
        needs_cleanup = len(self._store) >= self.MAX_ENTRIES

        if needs_cleanup:
            # Run expensive cleanup outside the main lock acquisition
            await self._enforce_size_limit()

        async with self._lock:
            self._store[key] = (value, expires_at)

    async def _enforce_size_limit(self) -> None:
        """
        Enforce size limit by removing expired and oldest entries.

        P2 FIX: Restructured to minimize lock hold time:
        - Take a snapshot of keys and expiration times
        - Release lock, do sorting (O(n log n))
        - Re-acquire lock to delete
        """
        now = datetime.now(UTC)
        expired_keys: list[str] = []
        keys_to_evict: list[str] = []

        # Phase 1: Take snapshot while holding lock (fast)
        async with self._lock:
            current_size = len(self._store)
            if current_size < self.MAX_ENTRIES:
                return  # Another coroutine cleaned up

            # Collect expired keys and make a snapshot for sorting
            snapshot: list[tuple[str, datetime]] = []
            for k, (_, exp) in self._store.items():
                if exp < now:
                    expired_keys.append(k)
                else:
                    snapshot.append((k, exp))

            # Delete expired keys immediately (they're definitely invalid)
            for key in expired_keys:
                del self._store[key]

        # Phase 2: Do expensive sorting OUTSIDE the lock
        if len(snapshot) >= self.MAX_ENTRIES - len(expired_keys):
            # Sort by expiration time (oldest first)
            snapshot.sort(key=lambda x: x[1])
            to_remove_count = max(1, len(snapshot) // 10)
            keys_to_evict = [k for k, _ in snapshot[:to_remove_count]]

        # Phase 3: Re-acquire lock to delete oldest entries
        if keys_to_evict:
            async with self._lock:
                removed_count = 0
                for key in keys_to_evict:
                    # Check key still exists (may have been deleted by another coroutine)
                    if key in self._store:
                        del self._store[key]
                        removed_count += 1

                logger.warning(
                    "state_store_size_limit_enforced",
                    removed_expired=len(expired_keys),
                    removed_oldest=removed_count,
                    remaining=len(self._store),
                )

    async def get(self, key: str) -> JsonValue | None:
        """Get a value by key. Returns None if expired or not found."""
        _validate_key(key)
        async with self._lock:
            if key not in self._store:
                return None
            value, expires_at = self._store[key]
            if datetime.now(UTC) > expires_at:
                del self._store[key]
                return None
            return value

    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        _validate_key(key)
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        _validate_key(key)
        return await self.get(key) is not None

    async def get_and_delete(self, key: str) -> JsonValue | None:
        """Get a value and delete it atomically (for one-time use tokens)."""
        _validate_key(key)
        async with self._lock:
            if key not in self._store:
                return None
            value, expires_at = self._store[key]
            del self._store[key]
            if datetime.now(UTC) > expires_at:
                return None
            return value


class RedisStateStore(StateStore):
    """
    Redis-backed state store for distributed deployments.

    Use this when running multiple application instances behind a load balancer.
    Ensures OAuth state tokens are validated correctly across all instances.

    Features:
    - Circuit breaker pattern: Fails fast when Redis is unavailable
    - Retry with exponential backoff: Handles transient failures
    - Configurable timeouts: Prevents hanging connections

    Requires: pip install redis

    Example:
        ```python
        store = RedisStateStore("redis://localhost:6379/0")
        await store.start()

        # Use in oauth routes
        await store.set("oauth_state:abc123", {"ip": "1.2.3.4"}, ttl_seconds=300)
        data = await store.get_and_delete("oauth_state:abc123")
        ```
    """

    # Circuit breaker configuration (from constants)
    CIRCUIT_FAILURE_THRESHOLD = REDIS_CIRCUIT_FAILURE_THRESHOLD
    CIRCUIT_RECOVERY_TIMEOUT = REDIS_CIRCUIT_RECOVERY_TIMEOUT
    CIRCUIT_HALF_OPEN_MAX_CALLS = REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "ipk:",
        socket_timeout: float = REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout: float = REDIS_SOCKET_CONNECT_TIMEOUT,
    ) -> None:
        """
        Initialize Redis state store.

        Args:
            redis_url: Redis connection URL (redis://host:port/db)
            key_prefix: Prefix for all keys (default: "ipk:")
            socket_timeout: Timeout for socket operations (default: 5s)
            socket_connect_timeout: Timeout for connection establishment (default: 5s)
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. Install it with: pip install redis"
            )

        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._socket_timeout = socket_timeout
        self._socket_connect_timeout = socket_connect_timeout
        self._client: redis.Redis[bytes] | None = None

        # Circuit breaker state
        self._circuit_state = RedisCircuitState.CLOSED
        self._circuit_failures = 0
        self._circuit_successes = 0
        self._circuit_opened_at: datetime | None = None
        self._circuit_half_open_calls = 0
        self._circuit_lock = asyncio.Lock()

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self._key_prefix}{key}"

    async def _check_circuit(self) -> bool:
        """
        Check if circuit allows request.

        Returns:
            True if request should proceed, False if circuit is open
        """
        async with self._circuit_lock:
            if self._circuit_state == RedisCircuitState.CLOSED:
                return True

            if self._circuit_state == RedisCircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._circuit_opened_at is not None:
                    elapsed = (datetime.now(UTC) - self._circuit_opened_at).total_seconds()
                    if elapsed >= self.CIRCUIT_RECOVERY_TIMEOUT:
                        self._circuit_state = RedisCircuitState.HALF_OPEN
                        self._circuit_half_open_calls = 0
                        self._circuit_successes = 0
                        logger.info("redis_circuit_half_open", store="state_store")
                        return True
                return False

            if self._circuit_state == RedisCircuitState.HALF_OPEN:
                if self._circuit_half_open_calls < self.CIRCUIT_HALF_OPEN_MAX_CALLS:
                    self._circuit_half_open_calls += 1
                    return True
                return False

            return False

    async def _record_success(self) -> None:
        """Record a successful Redis operation."""
        async with self._circuit_lock:
            self._circuit_successes += 1
            if self._circuit_state == RedisCircuitState.HALF_OPEN:
                if self._circuit_successes >= 2:  # 2 successes to close
                    self._circuit_state = RedisCircuitState.CLOSED
                    self._circuit_failures = 0
                    logger.info("redis_circuit_closed", store="state_store")

    async def _record_failure(self) -> None:
        """Record a failed Redis operation."""
        async with self._circuit_lock:
            self._circuit_failures += 1
            if self._circuit_state == RedisCircuitState.CLOSED:
                if self._circuit_failures >= self.CIRCUIT_FAILURE_THRESHOLD:
                    self._circuit_state = RedisCircuitState.OPEN
                    self._circuit_opened_at = datetime.now(UTC)
                    logger.warning(
                        "redis_circuit_open",
                        store="state_store",
                        failures=self._circuit_failures,
                    )
            elif self._circuit_state == RedisCircuitState.HALF_OPEN:
                # Any failure in half-open reopens circuit
                self._circuit_state = RedisCircuitState.OPEN
                self._circuit_opened_at = datetime.now(UTC)
                logger.warning("redis_circuit_reopened", store="state_store")

    async def _execute_with_retry(
        self,
        operation: str,
        func: callable,
        *args: object,
        **kwargs: object,
    ) -> object:
        """
        Execute a Redis operation with retry and circuit breaker.

        Args:
            operation: Name of the operation for logging
            func: Async function to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result of the operation

        Raises:
            RuntimeError: If circuit is open
            Exception: If all retries fail
        """
        # Check circuit breaker
        if not await self._check_circuit():
            logger.warning(
                "redis_circuit_rejected",
                store="state_store",
                operation=operation,
            )
            raise RuntimeError("Redis state store circuit breaker is open")

        last_error: Exception | None = None
        for attempt in range(REDIS_RETRY_ATTEMPTS):
            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
                last_error = e
                await self._record_failure()
                if attempt < REDIS_RETRY_ATTEMPTS - 1:
                    delay = REDIS_RETRY_BASE_DELAY * (2**attempt)
                    logger.warning(
                        "redis_operation_retry",
                        store="state_store",
                        operation=operation,
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                # Non-retryable errors
                logger.exception(
                    "redis_operation_error",
                    store="state_store",
                    operation=operation,
                    error=str(e),
                )
                raise

        # All retries exhausted
        logger.error(
            "redis_operation_failed",
            store="state_store",
            operation=operation,
            attempts=REDIS_RETRY_ATTEMPTS,
            error=str(last_error),
        )
        raise last_error  # type: ignore[misc]

    async def start(self) -> None:
        """Connect to Redis with configurable timeouts."""
        self._client = redis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=False,
            socket_timeout=self._socket_timeout,
            socket_connect_timeout=self._socket_connect_timeout,
        )
        # Test connection with retry
        await self._execute_with_retry("ping", self._client.ping)
        logger.info("redis_state_store_connected", url=self._redis_url.split("@")[-1])

    async def stop(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("redis_state_store_disconnected")

    async def set(self, key: str, value: JsonValue, ttl_seconds: int = 300) -> None:
        """Store a value with TTL, with retry and circuit breaker."""
        _validate_key(key)
        if not self._client:
            raise RuntimeError("Redis client not connected. Call start() first.")

        full_key = self._make_key(key)
        serialized = json.dumps(value)
        await self._execute_with_retry(
            "setex",
            self._client.setex,
            full_key,
            ttl_seconds,
            serialized,
        )

    async def get(self, key: str) -> JsonValue | None:
        """Get a value by key with retry and circuit breaker."""
        _validate_key(key)
        if not self._client:
            raise RuntimeError("Redis client not connected. Call start() first.")

        full_key = self._make_key(key)
        try:
            value = await self._execute_with_retry("get", self._client.get, full_key)
        except RuntimeError:
            # Circuit breaker open - return None (graceful degradation)
            logger.warning("redis_get_circuit_open", key=key[:50])
            return None
        if value is None:
            return None
        return json.loads(value)

    async def delete(self, key: str) -> bool:
        """Delete a key with retry and circuit breaker."""
        _validate_key(key)
        if not self._client:
            raise RuntimeError("Redis client not connected. Call start() first.")

        full_key = self._make_key(key)
        try:
            result = await self._execute_with_retry("delete", self._client.delete, full_key)
            return result > 0
        except RuntimeError:
            # Circuit breaker open - return False (graceful degradation)
            logger.warning("redis_delete_circuit_open", key=key[:50])
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists with retry and circuit breaker."""
        _validate_key(key)
        if not self._client:
            raise RuntimeError("Redis client not connected. Call start() first.")

        full_key = self._make_key(key)
        try:
            result = await self._execute_with_retry("exists", self._client.exists, full_key)
            return result > 0
        except RuntimeError:
            # Circuit breaker open - return False (graceful degradation)
            logger.warning("redis_exists_circuit_open", key=key[:50])
            return False

    async def get_and_delete(self, key: str) -> JsonValue | None:
        """
        Get a value and delete it atomically with retry and circuit breaker.

        Uses Redis GETDEL command for atomic operation.
        """
        _validate_key(key)
        if not self._client:
            raise RuntimeError("Redis client not connected. Call start() first.")

        full_key = self._make_key(key)
        try:
            value = await self._execute_with_retry("getdel", self._client.getdel, full_key)
        except RuntimeError:
            # Circuit breaker open - return None (graceful degradation)
            logger.warning("redis_getdel_circuit_open", key=key[:50])
            return None
        if value is None:
            return None
        return json.loads(value)


class RedisRequiredError(Exception):
    """Raised when Redis is required but not available."""

    pass


class StateStoreManager:
    """
    Manages state store lifecycle.

    P1 FIX: Replaces global state with an injectable, testable class.
    Each IdentityPlanKit instance owns its own StateStoreManager.

    Example:
        ```python
        manager = StateStoreManager()
        await manager.init(redis_url="redis://localhost:6379/0")

        store = manager.store
        await store.set("key", "value", ttl_seconds=300)

        await manager.close()
        ```
    """

    def __init__(self) -> None:
        self._store: StateStore | None = None
        self._startup_task: asyncio.Task[None] | None = None

    @property
    def store(self) -> StateStore:
        """Get the state store instance."""
        if self._store is None:
            raise RuntimeError("State store not initialized. Call init() first.")
        return self._store

    @property
    def is_initialized(self) -> bool:
        """Check if state store has been initialized."""
        return self._store is not None

    @property
    def backend_type(self) -> str:
        """Get the backend type (memory or redis)."""
        if self._store is None:
            return "none"
        return "redis" if isinstance(self._store, RedisStateStore) else "memory"

    async def init(
        self,
        redis_url: str | None = None,
        key_prefix: str = "ipk:",
        require_redis: bool = False,
    ) -> StateStore:
        """
        Initialize and start the state store.

        Args:
            redis_url: If provided, use Redis backend for distributed deployments.
            key_prefix: Prefix for Redis keys (default: "ipk:")
            require_redis: If True, fail if Redis is not available.

        Returns:
            Configured and connected state store.

        Raises:
            RedisRequiredError: If require_redis=True and Redis is not available.
        """
        if require_redis:
            if not redis_url:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) but redis_url is not configured. "
                    "Set IPK_REDIS_URL environment variable or disable require_redis for "
                    "single-instance deployments."
                )
            if not REDIS_AVAILABLE:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) but the redis package is not installed. "
                    "Install with: pip install redis"
                )

        if redis_url:
            if not REDIS_AVAILABLE:
                logger.warning(
                    "redis_not_available",
                    message="Redis URL provided but redis package not installed. "
                    "Falling back to in-memory store. "
                    "Install with: pip install redis",
                )
                self._store = InMemoryStateStore()
            else:
                self._store = RedisStateStore(redis_url=redis_url, key_prefix=key_prefix)
        else:
            self._store = InMemoryStateStore()

        await self._store.start()
        return self._store

    async def close(self) -> None:
        """Stop the state store."""
        if self._store is not None:
            await self._store.stop()
            self._store = None

    async def check_health(self) -> "ComponentHealth":
        """
        Health check function for HealthChecker integration.

        Returns:
            ComponentHealth with state store status
        """
        # Import here to avoid circular imports
        from identity_plan_kit.shared.health import ComponentHealth, HealthStatus  # noqa: PLC0415

        start = datetime.now(UTC)

        if self._store is None:
            return ComponentHealth(
                name="state_store",
                status=HealthStatus.UNHEALTHY,
                error="State store not initialized",
            )

        try:
            # Test write and read
            test_key = "_health_check_test"
            await self._store.set(test_key, {"test": True}, ttl_seconds=10)
            result = await self._store.get(test_key)
            await self._store.delete(test_key)

            if result is None:
                return ComponentHealth(
                    name="state_store",
                    status=HealthStatus.UNHEALTHY,
                    error="State store read/write test failed",
                )

            latency = (datetime.now(UTC) - start).total_seconds() * 1000

            return ComponentHealth(
                name="state_store",
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                details={"backend": self.backend_type},
            )
        except Exception as e:
            return ComponentHealth(
                name="state_store",
                status=HealthStatus.UNHEALTHY,
                error=str(e),
            )


# =============================================================================
# BACKWARD COMPATIBILITY LAYER
# =============================================================================
# The following maintains backward compatibility with existing code that uses
# the global functions. New code should use StateStoreManager directly.

import threading

_default_manager: StateStoreManager | None = None
_default_manager_lock = threading.Lock()


def _get_default_manager() -> StateStoreManager:
    """Get or create the default state store manager (thread-safe)."""
    global _default_manager  # noqa: PLW0603
    if _default_manager is None:
        with _default_manager_lock:
            if _default_manager is None:  # Double-check after acquiring lock
                _default_manager = StateStoreManager()
    return _default_manager


def get_state_store_manager() -> StateStoreManager:
    """
    Get the default state store manager instance.

    Returns the singleton StateStoreManager, creating it if necessary.
    Useful for checking initialization status and backend type.
    """
    return _get_default_manager()


def get_state_store() -> StateStore:
    """
    Get the default state store instance.

    DEPRECATED: Use StateStoreManager.store for new code.
    """
    manager = _get_default_manager()
    if not manager.is_initialized:
        # Auto-initialize with in-memory store for backward compatibility
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context but can't await here
            # Initialize synchronously with InMemoryStateStore
            manager._store = InMemoryStateStore()
            # Start the cleanup task - store reference to prevent GC
            manager._startup_task = asyncio.create_task(manager._store.start())
        else:
            loop.run_until_complete(manager.init())
    return manager.store


async def init_state_store(
    redis_url: str | None = None,
    key_prefix: str = "ipk:",
    require_redis: bool = False,
) -> StateStore:
    """
    Initialize and start the state store.

    DEPRECATED: Use StateStoreManager.init() for new code.
    """
    manager = _get_default_manager()
    return await manager.init(redis_url, key_prefix, require_redis)


async def close_state_store() -> None:
    """
    Stop the default state store.

    DEPRECATED: Use StateStoreManager.close() for new code.
    """
    global _default_manager  # noqa: PLW0603
    with _default_manager_lock:
        if _default_manager is not None:
            await _default_manager.close()
            _default_manager = None


async def check_state_store_health() -> "ComponentHealth":
    """
    Health check function for HealthChecker integration.

    DEPRECATED: Use StateStoreManager.check_health() for new code.
    """
    return await _get_default_manager().check_health()
