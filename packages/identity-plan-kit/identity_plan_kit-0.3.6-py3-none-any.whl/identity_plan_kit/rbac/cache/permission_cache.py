"""Permission cache for fast permission checks."""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Optional Redis support
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False


class AbstractPermissionCache(ABC):
    """Abstract base class for permission caching."""

    @abstractmethod
    async def get(self, user_id: UUID) -> set[str] | None:
        """Get cached permissions for user."""
        pass

    @abstractmethod
    async def set(self, user_id: UUID, permissions: set[str]) -> None:
        """Cache permissions for user."""
        pass

    @abstractmethod
    async def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached permissions for user."""
        pass

    @abstractmethod
    async def invalidate_all(self) -> None:
        """Invalidate all cached permissions."""
        pass


@dataclass
class CacheEntry:
    """Cache entry with expiration."""

    permissions: set[str]
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now(UTC) > self.expires_at


class InMemoryPermissionCache(AbstractPermissionCache):
    """
    In-memory permission cache.

    Caches user permissions with configurable TTL to reduce database queries.
    Thread-safe using asyncio locks.

    Warning:
        For multi-instance deployments, use RedisPermissionCache instead.
        In-memory cache invalidation only affects the local instance.
    """

    def __init__(self, ttl_seconds: int = 60) -> None:
        """
        Initialize permission cache.

        Args:
            ttl_seconds: Cache TTL in seconds (0 to disable caching)
        """
        self._ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict[UUID, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._enabled = ttl_seconds > 0

    async def get(self, user_id: UUID) -> set[str] | None:
        """
        Get cached permissions for user.

        Args:
            user_id: User UUID

        Returns:
            Set of permission codes or None if not cached/expired
        """
        if not self._enabled:
            return None

        async with self._lock:
            entry = self._cache.get(user_id)

            if entry is None:
                return None

            if entry.is_expired:
                del self._cache[user_id]
                return None

            return entry.permissions

    async def set(self, user_id: UUID, permissions: set[str]) -> None:
        """
        Cache permissions for user.

        Args:
            user_id: User UUID
            permissions: Set of permission codes
        """
        if not self._enabled:
            return

        async with self._lock:
            self._cache[user_id] = CacheEntry(
                permissions=permissions.copy(),
                expires_at=datetime.now(UTC) + self._ttl,
            )

    async def invalidate(self, user_id: UUID) -> None:
        """
        Invalidate cached permissions for user.

        Args:
            user_id: User UUID
        """
        async with self._lock:
            self._cache.pop(user_id, None)

    async def invalidate_all(self) -> None:
        """Invalidate all cached permissions."""
        async with self._lock:
            self._cache.clear()
            logger.info("permission_cache_cleared")

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            now = datetime.now(UTC)
            expired = [uid for uid, entry in self._cache.items() if entry.expires_at < now]
            for uid in expired:
                del self._cache[uid]

            if expired:
                logger.debug("cache_cleanup", removed=len(expired))

            return len(expired)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class RedisPermissionCache(AbstractPermissionCache):
    """
    Redis-backed permission cache for distributed deployments.

    Use this when running multiple application instances behind a load balancer.
    Ensures cache invalidation propagates to all instances.

    Requires: pip install redis
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 60,
        key_prefix: str = "ipk:perms:",
    ) -> None:
        """
        Initialize Redis permission cache.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: Cache TTL in seconds (0 to disable)
            key_prefix: Prefix for cache keys
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. Install it with: pip install redis"
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
        """
        Connect to Redis with exponential backoff retry.

        Args:
            max_retries: Maximum number of connection attempts
            base_delay: Base delay in seconds (doubles each retry)
        """
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
                    "redis_permission_cache_connected",
                    url=self._redis_url.split("@")[-1],
                )
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "redis_connection_retry",
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

    async def get(self, user_id: UUID) -> set[str] | None:
        """Get cached permissions for user."""
        if not self._enabled or not self._client:
            return None

        key = self._make_key(user_id)
        value = await self._client.get(key)
        if value is None:
            return None

        try:
            return set(json.loads(value))
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(
                "cache_json_decode_error",
                user_id=str(user_id),
                error=str(e),
            )
            await self.invalidate(user_id)
            return None

    async def set(self, user_id: UUID, permissions: set[str]) -> None:
        """Cache permissions for user."""
        if not self._enabled or not self._client:
            return

        key = self._make_key(user_id)
        try:
            value = json.dumps(list(permissions))
        except (TypeError, ValueError) as e:
            logger.warning(
                "cache_json_encode_error",
                user_id=str(user_id),
                error=str(e),
            )
            return
        await self._client.setex(key, self._ttl_seconds, value)

    async def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached permissions for user."""
        if not self._client:
            return

        key = self._make_key(user_id)
        await self._client.delete(key)

    async def invalidate_all(self) -> None:
        """
        Invalidate all cached permissions.

        Warning: This scans all keys with the prefix and may be slow on large caches.
        """
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

        logger.info("permission_cache_cleared", deleted=deleted)


class RedisRequiredError(Exception):
    """Raised when Redis is required but not available for permission cache."""

    pass


class PermissionCache(AbstractPermissionCache):
    """
    Permission cache with automatic backend selection.

    Uses Redis if redis_url is provided, otherwise falls back to in-memory.
    This is the recommended class to use for permission caching.

    Example:
        ```python
        # In-memory (single instance)
        cache = PermissionCache(ttl_seconds=60)

        # Redis (multi-instance, fail if unavailable)
        cache = PermissionCache(
            ttl_seconds=60,
            redis_url="redis://localhost:6379/0",
            require_redis=True,
        )
        await cache.connect()  # Required for Redis
        ```
    """

    def __init__(
        self,
        ttl_seconds: int = 60,
        redis_url: str | None = None,
        key_prefix: str = "ipk:perms:",
        require_redis: bool = False,
    ) -> None:
        """
        Initialize permission cache.

        Args:
            ttl_seconds: Cache TTL in seconds (0 to disable)
            redis_url: Redis URL for distributed caching (optional)
            key_prefix: Prefix for Redis keys
            require_redis: If True, fail if Redis is not available. Use this in
                          production multi-instance deployments to prevent silent
                          fallback to in-memory storage.

        Raises:
            RedisRequiredError: If require_redis=True and Redis is not available.
        """
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

        # P2 FIX: Fail-fast if Redis is required but not available
        if require_redis:
            if not redis_url:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) for permission cache but "
                    "redis_url is not configured. Set IPK_REDIS_URL environment variable "
                    "or disable require_redis for single-instance deployments."
                )
            if not REDIS_AVAILABLE:
                raise RedisRequiredError(
                    "Redis is required (require_redis=True) for permission cache but "
                    "the redis package is not installed. Install with: pip install redis"
                )

        if redis_url and REDIS_AVAILABLE:
            self._backend: AbstractPermissionCache = RedisPermissionCache(
                redis_url=redis_url,
                ttl_seconds=ttl_seconds,
                key_prefix=key_prefix,
            )
            self._is_redis = True
        else:
            if redis_url and not REDIS_AVAILABLE:
                logger.warning(
                    "redis_not_available_for_cache",
                    message="Redis URL provided but redis package not installed. "
                    "Using in-memory cache. Install with: pip install redis",
                )
            self._backend = InMemoryPermissionCache(ttl_seconds=ttl_seconds)
            self._is_redis = False

    async def connect(self) -> None:
        """Connect to Redis (if using Redis backend)."""
        if self._is_redis and isinstance(self._backend, RedisPermissionCache):
            await self._backend.connect()

    async def disconnect(self) -> None:
        """Disconnect from Redis (if using Redis backend)."""
        if self._is_redis and isinstance(self._backend, RedisPermissionCache):
            await self._backend.disconnect()

    async def get(self, user_id: UUID) -> set[str] | None:
        """Get cached permissions for user."""
        return await self._backend.get(user_id)

    async def set(self, user_id: UUID, permissions: set[str]) -> None:
        """Cache permissions for user."""
        await self._backend.set(user_id, permissions)

    async def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached permissions for user."""
        await self._backend.invalidate(user_id)

    async def invalidate_all(self) -> None:
        """Invalidate all cached permissions."""
        await self._backend.invalidate_all()

    @property
    def size(self) -> int:
        """Get current cache size (in-memory only)."""
        if isinstance(self._backend, InMemoryPermissionCache):
            return self._backend.size
        return -1  # Unknown for Redis
