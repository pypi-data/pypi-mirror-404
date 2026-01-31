"""Plan cache for fast plan lookups with Redis support."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import UUID

from identity_plan_kit.plans.domain.entities import Plan, PlanLimit, PeriodType
from identity_plan_kit.shared.constants import (
    DEFAULT_CACHE_TTL_SECONDS,
    REDIS_CIRCUIT_FAILURE_THRESHOLD,
    REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS,
    REDIS_CIRCUIT_RECOVERY_TIMEOUT,
    REDIS_RETRY_ATTEMPTS,
    REDIS_RETRY_BASE_DELAY,
    REDIS_SOCKET_CONNECT_TIMEOUT,
    REDIS_SOCKET_TIMEOUT,
)
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Optional Redis support
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False


# Keys for Redis
ALL_PLANS_KEY = "_all_plans"


class CacheCircuitState(Enum):
    """Circuit breaker states for cache."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def _plan_to_dict(plan: Plan) -> dict:
    """Convert Plan entity to JSON-serializable dict."""
    return {
        "id": str(plan.id),
        "code": plan.code,
        "name": plan.name,
        "permissions": list(plan.permissions),
        "limits": {
            code: {
                "id": str(limit.id),
                "plan_id": str(limit.plan_id),
                "feature_id": str(limit.feature_id),
                "feature_code": limit.feature_code,
                "limit": limit.limit,
                "period": limit.period.value if limit.period else None,
            }
            for code, limit in plan.limits.items()
        },
    }


def _dict_to_plan(data: dict) -> Plan:
    """Convert dict back to Plan entity."""
    limits = {}
    for code, limit_data in data.get("limits", {}).items():
        limits[code] = PlanLimit(
            id=UUID(limit_data["id"]),
            plan_id=UUID(limit_data["plan_id"]),
            feature_id=UUID(limit_data["feature_id"]),
            feature_code=limit_data["feature_code"],
            limit=limit_data["limit"],
            period=PeriodType(limit_data["period"]) if limit_data["period"] else None,
        )
    return Plan(
        id=UUID(data["id"]),
        code=data["code"],
        name=data["name"],
        permissions=set(data.get("permissions", [])),
        limits=limits,
    )


class AbstractPlanCache(ABC):
    """Abstract base class for plan caching."""

    @abstractmethod
    async def get(self, plan_code: str) -> Plan | None:
        """Get cached plan by code."""
        pass

    @abstractmethod
    async def set(
        self,
        plan_code: str,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """Cache plan by code."""
        pass

    @abstractmethod
    async def get_all(self) -> list[Plan] | None:
        """Get cached list of all plans."""
        pass

    @abstractmethod
    async def set_all(
        self,
        plans: list[Plan],
        fetched_at: float | None = None,
    ) -> bool:
        """Cache the complete list of all plans."""
        pass

    @abstractmethod
    async def invalidate(self, plan_code: str) -> None:
        """Invalidate cached plan by code."""
        pass

    @abstractmethod
    async def invalidate_all(self) -> None:
        """Invalidate all cached plans."""
        pass

    def get_fetch_timestamp(self) -> float:
        """Get a monotonic timestamp for stale write prevention."""
        return time.monotonic()


@dataclass
class PlanCacheEntry:
    """Cache entry with expiration and fetch timestamp for race condition prevention."""

    plan: Plan
    expires_at: datetime
    fetched_at: float = field(default_factory=time.monotonic)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now(UTC) > self.expires_at


@dataclass
class AllPlansCacheEntry:
    """Cache entry for the complete list of all plans."""

    plans: list[Plan]
    expires_at: datetime
    fetched_at: float = field(default_factory=time.monotonic)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now(UTC) > self.expires_at


class InMemoryPlanCache(AbstractPlanCache):
    """
    In-memory plan cache.

    Caches plan data (by code) to reduce database queries.
    Plans are static reference data that rarely change, so a simple
    in-memory cache with TTL is sufficient.

    For cache invalidation on plan updates, call invalidate() or invalidate_all().

    **Race Condition Prevention:**

    This cache prevents stale writes after invalidation using a timestamp-based
    approach. When invalidate() is called, it records the invalidation time.
    Subsequent set() calls only succeed if their fetch timestamp is newer than
    the last invalidation.

    Warning:
        For multi-instance deployments, use RedisPlanCache instead.
        In-memory cache invalidation only affects the local instance.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> None:
        """
        Initialize plan cache.

        Args:
            ttl_seconds: Cache TTL in seconds (default: 5 minutes, 0 to disable)
        """
        self._ttl = timedelta(seconds=ttl_seconds)
        self._ttl_seconds = ttl_seconds
        self._cache: dict[str, PlanCacheEntry] = {}
        self._write_lock = asyncio.Lock()
        self._enabled = ttl_seconds > 0
        self._invalidated_at: dict[str, float] = {}
        self._global_invalidated_at: float = 0.0
        self._all_plans_cache: AllPlansCacheEntry | None = None

    async def get(self, plan_code: str) -> Plan | None:
        """
        Get cached plan by code.

        Args:
            plan_code: Plan code (e.g., "free", "pro")

        Returns:
            Plan entity or None if not cached/expired
        """
        if not self._enabled:
            return None

        entry = self._cache.get(plan_code)

        if entry is None:
            return None

        if entry.is_expired:
            return None

        return entry.plan

    async def set(
        self,
        plan_code: str,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """
        Cache plan by code.

        Args:
            plan_code: Plan code
            plan: Plan entity to cache
            fetched_at: Monotonic timestamp when the plan was fetched from DB.

        Returns:
            True if the entry was cached, False if rejected as stale
        """
        if not self._enabled:
            return False

        if fetched_at is not None:
            if fetched_at < self._global_invalidated_at:
                logger.debug(
                    "plan_cache_stale_write_rejected",
                    plan_code=plan_code,
                    reason="global_invalidation",
                )
                return False

            key_invalidated_at = self._invalidated_at.get(plan_code, 0.0)
            if fetched_at < key_invalidated_at:
                logger.debug(
                    "plan_cache_stale_write_rejected",
                    plan_code=plan_code,
                    reason="key_invalidation",
                )
                return False

        entry = PlanCacheEntry(
            plan=plan,
            expires_at=datetime.now(UTC) + self._ttl,
            fetched_at=fetched_at or time.monotonic(),
        )
        self._cache[plan_code] = entry
        return True

    async def get_all(self) -> list[Plan] | None:
        """Get cached list of all plans."""
        if not self._enabled:
            return None

        entry = self._all_plans_cache
        if entry is None:
            return None

        if entry.is_expired:
            return None

        logger.debug("all_plans_cache_hit", count=len(entry.plans))
        return entry.plans

    async def set_all(
        self,
        plans: list[Plan],
        fetched_at: float | None = None,
    ) -> bool:
        """Cache the complete list of all plans."""
        if not self._enabled:
            return False

        if fetched_at is not None and fetched_at < self._global_invalidated_at:
            logger.debug(
                "all_plans_cache_stale_write_rejected",
                reason="global_invalidation",
            )
            return False

        self._all_plans_cache = AllPlansCacheEntry(
            plans=plans,
            expires_at=datetime.now(UTC) + self._ttl,
            fetched_at=fetched_at or time.monotonic(),
        )

        for plan in plans:
            await self.set(plan.code, plan, fetched_at=fetched_at)

        logger.debug("all_plans_cached", count=len(plans))
        return True

    async def invalidate(self, plan_code: str) -> None:
        """Invalidate cached plan by code."""
        self._invalidated_at[plan_code] = time.monotonic()
        self._cache.pop(plan_code, None)
        self._all_plans_cache = None
        logger.debug("plan_cache_invalidated", plan_code=plan_code)

    async def invalidate_all(self) -> None:
        """Invalidate all cached plans."""
        async with self._write_lock:
            self._global_invalidated_at = time.monotonic()
            self._cache.clear()
            self._all_plans_cache = None
            self._invalidated_at.clear()
            logger.info("plan_cache_cleared")

    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        async with self._write_lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug("plan_cache_cleanup", removed_count=len(expired_keys))

            return len(expired_keys)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class RedisPlanCache(AbstractPlanCache):
    """
    Redis-backed plan cache for distributed deployments.

    Use this when running multiple application instances behind a load balancer.
    Ensures cache invalidation propagates to all instances.

    Features:
    - Circuit breaker: Fails fast when Redis is unavailable
    - Retry with exponential backoff: Handles transient failures
    - Configurable timeouts: Prevents hanging connections

    Requires: pip install redis
    """

    # Circuit breaker configuration (from constants)
    CIRCUIT_FAILURE_THRESHOLD = REDIS_CIRCUIT_FAILURE_THRESHOLD
    CIRCUIT_RECOVERY_TIMEOUT = REDIS_CIRCUIT_RECOVERY_TIMEOUT
    CIRCUIT_HALF_OPEN_MAX_CALLS = REDIS_CIRCUIT_HALF_OPEN_MAX_CALLS

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        key_prefix: str = "ipk:plan:",
        socket_timeout: float = REDIS_SOCKET_TIMEOUT,
        socket_connect_timeout: float = REDIS_SOCKET_CONNECT_TIMEOUT,
    ) -> None:
        """
        Initialize Redis plan cache.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: Cache TTL in seconds (0 to disable)
            key_prefix: Prefix for cache keys
            socket_timeout: Timeout for socket operations (default: 5s)
            socket_connect_timeout: Timeout for connection (default: 5s)
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. Install with: pip install redis"
            )

        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix
        self._socket_timeout = socket_timeout
        self._socket_connect_timeout = socket_connect_timeout
        self._enabled = ttl_seconds > 0
        self._client: redis.Redis[bytes] | None = None

        # Circuit breaker state
        self._circuit_state = CacheCircuitState.CLOSED
        self._circuit_failures = 0
        self._circuit_successes = 0
        self._circuit_opened_at: datetime | None = None
        self._circuit_half_open_calls = 0
        self._circuit_lock = asyncio.Lock()

    def _make_key(self, plan_code: str) -> str:
        """Create cache key for plan."""
        return f"{self._key_prefix}{plan_code}"

    async def _check_circuit(self) -> bool:
        """Check if circuit allows request."""
        async with self._circuit_lock:
            if self._circuit_state == CacheCircuitState.CLOSED:
                return True

            if self._circuit_state == CacheCircuitState.OPEN:
                if self._circuit_opened_at is not None:
                    elapsed = (datetime.now(UTC) - self._circuit_opened_at).total_seconds()
                    if elapsed >= self.CIRCUIT_RECOVERY_TIMEOUT:
                        self._circuit_state = CacheCircuitState.HALF_OPEN
                        self._circuit_half_open_calls = 0
                        self._circuit_successes = 0
                        logger.info("plan_cache_circuit_half_open")
                        return True
                return False

            if self._circuit_state == CacheCircuitState.HALF_OPEN:
                if self._circuit_half_open_calls < self.CIRCUIT_HALF_OPEN_MAX_CALLS:
                    self._circuit_half_open_calls += 1
                    return True
                return False

            return False

    async def _record_success(self) -> None:
        """Record successful operation."""
        async with self._circuit_lock:
            self._circuit_successes += 1
            if self._circuit_state == CacheCircuitState.HALF_OPEN:
                if self._circuit_successes >= 2:
                    self._circuit_state = CacheCircuitState.CLOSED
                    self._circuit_failures = 0
                    logger.info("plan_cache_circuit_closed")

    async def _record_failure(self) -> None:
        """Record failed operation."""
        async with self._circuit_lock:
            self._circuit_failures += 1
            if self._circuit_state == CacheCircuitState.CLOSED:
                if self._circuit_failures >= self.CIRCUIT_FAILURE_THRESHOLD:
                    self._circuit_state = CacheCircuitState.OPEN
                    self._circuit_opened_at = datetime.now(UTC)
                    logger.warning("plan_cache_circuit_open", failures=self._circuit_failures)
            elif self._circuit_state == CacheCircuitState.HALF_OPEN:
                self._circuit_state = CacheCircuitState.OPEN
                self._circuit_opened_at = datetime.now(UTC)
                logger.warning("plan_cache_circuit_reopened")

    async def _execute_with_retry(
        self,
        operation: str,
        func: callable,
        *args: object,
        **kwargs: object,
    ) -> object:
        """Execute Redis operation with retry and circuit breaker."""
        if not await self._check_circuit():
            logger.debug("plan_cache_circuit_rejected", operation=operation)
            return None

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
                        "plan_cache_retry",
                        operation=operation,
                        attempt=attempt + 1,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)

        logger.warning("plan_cache_operation_failed", operation=operation, error=str(last_error))
        return None

    async def connect(
        self,
        max_retries: int = 3,
        base_delay: float = 0.5,
    ) -> None:
        """Connect to Redis with exponential backoff retry and timeouts."""
        self._client = redis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=False,
            socket_timeout=self._socket_timeout,
            socket_connect_timeout=self._socket_connect_timeout,
        )

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                await self._client.ping()
                logger.info(
                    "redis_plan_cache_connected",
                    url=self._redis_url.split("@")[-1],
                )
                return
            except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "redis_plan_cache_connection_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)

        await self._client.aclose()
        self._client = None
        raise ConnectionError(
            f"Failed to connect to Redis after {max_retries} attempts: {last_error}"
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, plan_code: str) -> Plan | None:
        """Get cached plan by code with retry and circuit breaker."""
        if not self._enabled or not self._client:
            return None

        key = self._make_key(plan_code)
        value = await self._execute_with_retry("get", self._client.get, key)
        if value is None:
            return None

        try:
            data = json.loads(value)
            return _dict_to_plan(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(
                "plan_cache_json_decode_error",
                plan_code=plan_code,
                error=str(e),
            )
            await self.invalidate(plan_code)
            return None

    async def set(
        self,
        plan_code: str,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """Cache plan by code with retry and circuit breaker."""
        if not self._enabled or not self._client:
            return False

        key = self._make_key(plan_code)
        try:
            value = json.dumps(_plan_to_dict(plan))
        except (TypeError, ValueError) as e:
            logger.warning(
                "plan_cache_json_encode_error",
                plan_code=plan_code,
                error=str(e),
            )
            return False

        result = await self._execute_with_retry("setex", self._client.setex, key, self._ttl_seconds, value)
        return result is not None

    async def get_all(self) -> list[Plan] | None:
        """Get cached list of all plans with retry and circuit breaker."""
        if not self._enabled or not self._client:
            return None

        key = self._make_key(ALL_PLANS_KEY)
        value = await self._execute_with_retry("get", self._client.get, key)
        if value is None:
            return None

        try:
            data = json.loads(value)
            plans = [_dict_to_plan(p) for p in data]
            logger.debug("all_plans_cache_hit", count=len(plans))
            return plans
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(
                "all_plans_cache_json_decode_error",
                error=str(e),
            )
            await self._execute_with_retry("delete", self._client.delete, key)
            return None

    async def set_all(
        self,
        plans: list[Plan],
        fetched_at: float | None = None,
    ) -> bool:
        """Cache the complete list of all plans with retry and circuit breaker."""
        if not self._enabled or not self._client:
            return False

        key = self._make_key(ALL_PLANS_KEY)
        try:
            value = json.dumps([_plan_to_dict(p) for p in plans])
        except (TypeError, ValueError) as e:
            logger.warning(
                "all_plans_cache_json_encode_error",
                error=str(e),
            )
            return False

        result = await self._execute_with_retry("setex", self._client.setex, key, self._ttl_seconds, value)
        if result is None:
            return False

        # Also cache individual plans
        for plan in plans:
            await self.set(plan.code, plan, fetched_at=fetched_at)

        logger.debug("all_plans_cached", count=len(plans))
        return True

    async def invalidate(self, plan_code: str) -> None:
        """Invalidate cached plan by code with retry."""
        if not self._client:
            return

        key = self._make_key(plan_code)
        all_key = self._make_key(ALL_PLANS_KEY)
        await self._execute_with_retry("delete", self._client.delete, key, all_key)
        logger.debug("plan_cache_invalidated", plan_code=plan_code)

    async def invalidate_all(self) -> None:
        """Invalidate all cached plans with retry."""
        if not self._client:
            return

        pattern = f"{self._key_prefix}*"
        cursor = 0
        deleted = 0

        while True:
            result = await self._execute_with_retry("scan", self._client.scan, cursor, match=pattern, count=100)
            if result is None:
                break
            cursor, keys = result
            if keys:
                del_result = await self._execute_with_retry("delete", self._client.delete, *keys)
                if del_result is not None:
                    deleted += del_result
            if cursor == 0:
                break

        logger.info("plan_cache_cleared", deleted=deleted)


class RedisRequiredError(Exception):
    """Raised when Redis is required but not available for plan cache."""

    pass


class PlanCache(AbstractPlanCache):
    """
    Plan cache with automatic backend selection.

    Uses Redis if redis_url is provided, otherwise falls back to in-memory.
    This is the recommended class to use for plan caching.

    Example:
        ```python
        # In-memory (single instance)
        cache = PlanCache(ttl_seconds=300)

        # Redis (multi-instance, fail if unavailable)
        cache = PlanCache(
            ttl_seconds=300,
            redis_url="redis://localhost:6379/0",
            require_redis=True,
        )
        await cache.connect()  # Required for Redis
        ```
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        redis_url: str | None = None,
        key_prefix: str = "ipk:plan:",
        require_redis: bool = False,
    ) -> None:
        """
        Initialize plan cache.

        Args:
            ttl_seconds: Cache TTL in seconds (0 to disable)
            redis_url: Redis URL for distributed caching (optional)
            key_prefix: Prefix for Redis keys
            require_redis: If True, fail if Redis is not available.

        Raises:
            RedisRequiredError: If require_redis=True and Redis is not available.
        """
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

        if require_redis:
            if not redis_url:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) for plan cache but "
                    "redis_url is not configured."
                )
            if not REDIS_AVAILABLE:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) for plan cache but "
                    "the redis package is not installed. Install with: pip install redis"
                )

        if redis_url and REDIS_AVAILABLE:
            self._backend: AbstractPlanCache = RedisPlanCache(
                redis_url=redis_url,
                ttl_seconds=ttl_seconds,
                key_prefix=key_prefix,
            )
            self._is_redis = True
        else:
            if redis_url and not REDIS_AVAILABLE:
                logger.warning(
                    "redis_not_available_for_plan_cache",
                    message="Redis URL provided but redis package not installed. "
                    "Using in-memory cache.",
                )
            self._backend = InMemoryPlanCache(ttl_seconds=ttl_seconds)
            self._is_redis = False

    async def connect(self) -> None:
        """Connect to Redis (if using Redis backend)."""
        if self._is_redis and isinstance(self._backend, RedisPlanCache):
            await self._backend.connect()

    async def disconnect(self) -> None:
        """Disconnect from Redis (if using Redis backend)."""
        if self._is_redis and isinstance(self._backend, RedisPlanCache):
            await self._backend.disconnect()

    async def get(self, plan_code: str) -> Plan | None:
        """Get cached plan by code."""
        return await self._backend.get(plan_code)

    async def set(
        self,
        plan_code: str,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """Cache plan by code."""
        return await self._backend.set(plan_code, plan, fetched_at=fetched_at)

    async def get_all(self) -> list[Plan] | None:
        """Get cached list of all plans."""
        return await self._backend.get_all()

    async def set_all(
        self,
        plans: list[Plan],
        fetched_at: float | None = None,
    ) -> bool:
        """Cache the complete list of all plans."""
        return await self._backend.set_all(plans, fetched_at=fetched_at)

    async def invalidate(self, plan_code: str) -> None:
        """Invalidate cached plan by code."""
        await self._backend.invalidate(plan_code)

    async def invalidate_all(self) -> None:
        """Invalidate all cached plans."""
        await self._backend.invalidate_all()

    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache (in-memory only)."""
        if isinstance(self._backend, InMemoryPlanCache):
            return await self._backend.cleanup_expired()
        return 0

    @property
    def size(self) -> int:
        """Get current cache size (in-memory only)."""
        if isinstance(self._backend, InMemoryPlanCache):
            return self._backend.size
        return -1

    @property
    def is_redis(self) -> bool:
        """Check if using Redis backend."""
        return self._is_redis
