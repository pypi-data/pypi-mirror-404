"""User plan cache for fast user plan lookups with Redis support."""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, date
from uuid import UUID

from identity_plan_kit.plans.domain.entities import Plan, PlanLimit, PeriodType, UserPlan
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Optional Redis support
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False


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


def _user_plan_to_dict(user_plan: UserPlan) -> dict:
    """Convert UserPlan entity to JSON-serializable dict."""
    return {
        "id": str(user_plan.id),
        "user_id": str(user_plan.user_id),
        "plan_id": str(user_plan.plan_id),
        "plan_code": user_plan.plan_code,
        "started_at": user_plan.started_at.isoformat(),
        "ends_at": user_plan.ends_at.isoformat(),
        "custom_limits": user_plan.custom_limits,
    }


def _dict_to_user_plan(data: dict) -> UserPlan:
    """Convert dict back to UserPlan entity."""
    return UserPlan(
        id=UUID(data["id"]),
        user_id=UUID(data["user_id"]),
        plan_id=UUID(data["plan_id"]),
        plan_code=data["plan_code"],
        started_at=date.fromisoformat(data["started_at"]),
        ends_at=date.fromisoformat(data["ends_at"]),
        custom_limits=data.get("custom_limits", {}),
    )


class AbstractUserPlanCache(ABC):
    """Abstract base class for user plan caching."""

    @abstractmethod
    async def get(self, user_id: UUID) -> tuple[UserPlan, Plan] | None:
        """Get cached user plan by user ID."""
        pass

    @abstractmethod
    async def set(
        self,
        user_id: UUID,
        user_plan: UserPlan,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """Cache user plan by user ID."""
        pass

    @abstractmethod
    async def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached user plan by user ID."""
        pass

    @abstractmethod
    async def invalidate_all(self) -> None:
        """Invalidate all cached user plans."""
        pass

    def get_fetch_timestamp(self) -> float:
        """Get a monotonic timestamp for stale write prevention."""
        return time.monotonic()


@dataclass
class UserPlanCacheEntry:
    """Cache entry for user plan with expiration."""

    user_plan: UserPlan
    plan: Plan
    expires_at: datetime
    fetched_at: float = field(default_factory=time.monotonic)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now(UTC) > self.expires_at


class InMemoryUserPlanCache(AbstractUserPlanCache):
    """
    In-memory user plan cache.

    Caches user plan assignments (by user_id) to reduce database queries.
    User plans change less frequently than usage, so caching provides
    significant benefit for quota check operations.

    Cache key: user_id (UUID)
    Cache value: (UserPlan, Plan) tuple with full plan details

    **Invalidation:**

    Call invalidate() when:
    - User's plan is assigned/changed
    - User's plan is cancelled
    - User's plan is extended
    - User's custom limits are updated

    Warning:
        For multi-instance deployments, use RedisUserPlanCache instead.
        In-memory cache invalidation only affects the local instance.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        """
        Initialize user plan cache.

        Args:
            ttl_seconds: Cache TTL in seconds (default: 5 minutes, 0 to disable)
        """
        self._ttl = timedelta(seconds=ttl_seconds)
        self._ttl_seconds = ttl_seconds
        self._cache: dict[UUID, UserPlanCacheEntry] = {}
        self._write_lock = asyncio.Lock()
        self._enabled = ttl_seconds > 0
        self._invalidated_at: dict[UUID, float] = {}
        self._global_invalidated_at: float = 0.0

    async def get(self, user_id: UUID) -> tuple[UserPlan, Plan] | None:
        """
        Get cached user plan by user ID.

        Args:
            user_id: User UUID

        Returns:
            Tuple of (UserPlan, Plan) or None if not cached/expired
        """
        if not self._enabled:
            return None

        entry = self._cache.get(user_id)

        if entry is None:
            return None

        if entry.is_expired:
            return None

        return entry.user_plan, entry.plan

    async def set(
        self,
        user_id: UUID,
        user_plan: UserPlan,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """
        Cache user plan by user ID.

        Args:
            user_id: User UUID
            user_plan: UserPlan entity to cache
            plan: Plan entity with full details (permissions, limits)
            fetched_at: Monotonic timestamp when data was fetched from DB

        Returns:
            True if the entry was cached, False if rejected as stale
        """
        if not self._enabled:
            return False

        if fetched_at is not None:
            if fetched_at < self._global_invalidated_at:
                logger.debug(
                    "user_plan_cache_stale_write_rejected",
                    user_id=str(user_id),
                    reason="global_invalidation",
                )
                return False

            key_invalidated_at = self._invalidated_at.get(user_id, 0.0)
            if fetched_at < key_invalidated_at:
                logger.debug(
                    "user_plan_cache_stale_write_rejected",
                    user_id=str(user_id),
                    reason="key_invalidation",
                )
                return False

        entry = UserPlanCacheEntry(
            user_plan=user_plan,
            plan=plan,
            expires_at=datetime.now(UTC) + self._ttl,
            fetched_at=fetched_at or time.monotonic(),
        )
        self._cache[user_id] = entry
        return True

    async def invalidate(self, user_id: UUID) -> None:
        """
        Invalidate cached user plan by user ID.

        Args:
            user_id: User UUID to invalidate
        """
        self._invalidated_at[user_id] = time.monotonic()
        self._cache.pop(user_id, None)
        logger.debug("user_plan_cache_invalidated", user_id=str(user_id))

    async def invalidate_all(self) -> None:
        """Invalidate all cached user plans."""
        async with self._write_lock:
            self._global_invalidated_at = time.monotonic()
            self._cache.clear()
            self._invalidated_at.clear()
            logger.info("user_plan_cache_cleared")

    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        async with self._write_lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(
                    "user_plan_cache_cleanup",
                    removed_count=len(expired_keys),
                )

            return len(expired_keys)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class RedisUserPlanCache(AbstractUserPlanCache):
    """
    Redis-backed user plan cache for distributed deployments.

    Use this when running multiple application instances behind a load balancer.
    Ensures cache invalidation propagates to all instances.

    Requires: pip install redis
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 300,
        key_prefix: str = "ipk:user_plan:",
    ) -> None:
        """
        Initialize Redis user plan cache.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: Cache TTL in seconds (0 to disable)
            key_prefix: Prefix for cache keys
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. Install with: pip install redis"
            )

        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix
        self._enabled = ttl_seconds > 0
        self._client: redis.Redis[bytes] | None = None

    def _make_key(self, user_id: UUID) -> str:
        """Create cache key for user."""
        return f"{self._key_prefix}{user_id}"

    async def connect(
        self,
        max_retries: int = 3,
        base_delay: float = 0.5,
    ) -> None:
        """Connect to Redis with exponential backoff retry."""
        self._client = redis.from_url(
            self._redis_url,
            encoding="utf-8",
            decode_responses=False,
        )

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                await self._client.ping()
                logger.info(
                    "redis_user_plan_cache_connected",
                    url=self._redis_url.split("@")[-1],
                )
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "redis_user_plan_cache_connection_retry",
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

    async def get(self, user_id: UUID) -> tuple[UserPlan, Plan] | None:
        """Get cached user plan by user ID."""
        if not self._enabled or not self._client:
            return None

        key = self._make_key(user_id)
        value = await self._client.get(key)
        if value is None:
            return None

        try:
            data = json.loads(value)
            user_plan = _dict_to_user_plan(data["user_plan"])
            plan = _dict_to_plan(data["plan"])
            return user_plan, plan
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(
                "user_plan_cache_json_decode_error",
                user_id=str(user_id),
                error=str(e),
            )
            await self.invalidate(user_id)
            return None

    async def set(
        self,
        user_id: UUID,
        user_plan: UserPlan,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """Cache user plan by user ID."""
        if not self._enabled or not self._client:
            return False

        key = self._make_key(user_id)
        try:
            value = json.dumps({
                "user_plan": _user_plan_to_dict(user_plan),
                "plan": _plan_to_dict(plan),
            })
        except (TypeError, ValueError) as e:
            logger.warning(
                "user_plan_cache_json_encode_error",
                user_id=str(user_id),
                error=str(e),
            )
            return False

        await self._client.setex(key, self._ttl_seconds, value)
        return True

    async def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached user plan by user ID."""
        if not self._client:
            return

        key = self._make_key(user_id)
        await self._client.delete(key)
        logger.debug("user_plan_cache_invalidated", user_id=str(user_id))

    async def invalidate_all(self) -> None:
        """Invalidate all cached user plans."""
        if not self._client:
            return

        pattern = f"{self._key_prefix}*"
        cursor = 0
        deleted = 0

        while True:
            cursor, keys = await self._client.scan(cursor, match=pattern, count=100)
            if keys:
                deleted += await self._client.delete(*keys)
            if cursor == 0:
                break

        logger.info("user_plan_cache_cleared", deleted=deleted)


class RedisRequiredError(Exception):
    """Raised when Redis is required but not available for user plan cache."""

    pass


class UserPlanCache(AbstractUserPlanCache):
    """
    User plan cache with automatic backend selection.

    Uses Redis if redis_url is provided, otherwise falls back to in-memory.
    This is the recommended class to use for user plan caching.

    Example:
        ```python
        # In-memory (single instance)
        cache = UserPlanCache(ttl_seconds=300)

        # Redis (multi-instance, fail if unavailable)
        cache = UserPlanCache(
            ttl_seconds=300,
            redis_url="redis://localhost:6379/0",
            require_redis=True,
        )
        await cache.connect()  # Required for Redis
        ```
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
        redis_url: str | None = None,
        key_prefix: str = "ipk:user_plan:",
        require_redis: bool = False,
    ) -> None:
        """
        Initialize user plan cache.

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
                    "Redis is required (require_redis=True) for user plan cache but "
                    "redis_url is not configured."
                )
            if not REDIS_AVAILABLE:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) for user plan cache but "
                    "the redis package is not installed. Install with: pip install redis"
                )

        if redis_url and REDIS_AVAILABLE:
            self._backend: AbstractUserPlanCache = RedisUserPlanCache(
                redis_url=redis_url,
                ttl_seconds=ttl_seconds,
                key_prefix=key_prefix,
            )
            self._is_redis = True
        else:
            if redis_url and not REDIS_AVAILABLE:
                logger.warning(
                    "redis_not_available_for_user_plan_cache",
                    message="Redis URL provided but redis package not installed. "
                    "Using in-memory cache.",
                )
            self._backend = InMemoryUserPlanCache(ttl_seconds=ttl_seconds)
            self._is_redis = False

    async def connect(self) -> None:
        """Connect to Redis (if using Redis backend)."""
        if self._is_redis and isinstance(self._backend, RedisUserPlanCache):
            await self._backend.connect()

    async def disconnect(self) -> None:
        """Disconnect from Redis (if using Redis backend)."""
        if self._is_redis and isinstance(self._backend, RedisUserPlanCache):
            await self._backend.disconnect()

    async def get(self, user_id: UUID) -> tuple[UserPlan, Plan] | None:
        """Get cached user plan by user ID."""
        return await self._backend.get(user_id)

    async def set(
        self,
        user_id: UUID,
        user_plan: UserPlan,
        plan: Plan,
        fetched_at: float | None = None,
    ) -> bool:
        """Cache user plan by user ID."""
        return await self._backend.set(user_id, user_plan, plan, fetched_at=fetched_at)

    async def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached user plan by user ID."""
        await self._backend.invalidate(user_id)

    async def invalidate_all(self) -> None:
        """Invalidate all cached user plans."""
        await self._backend.invalidate_all()

    @property
    def size(self) -> int:
        """Get current cache size (in-memory only)."""
        if isinstance(self._backend, InMemoryUserPlanCache):
            return self._backend.size
        return -1

    @property
    def is_redis(self) -> bool:
        """Check if using Redis backend."""
        return self._is_redis
