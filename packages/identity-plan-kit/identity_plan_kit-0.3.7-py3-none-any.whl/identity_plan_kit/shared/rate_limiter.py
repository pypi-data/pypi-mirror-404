"""Rate limiting using slowapi with configurable backends."""

import threading
from collections.abc import Callable

from fastapi import Request
from slowapi import Limiter

from identity_plan_kit.shared.http_utils import get_client_ip
from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Global state with thread-safe initialization
_limiter: Limiter | None = None
_trust_proxy: bool = False
_trust_proxy_initialized: bool = False  # Track if trust_proxy was explicitly set
_limiter_lock = threading.RLock()


def _get_client_ip_key(request: Request) -> str:
    """
    Extract client IP for rate limiting key.

    Uses the global _trust_proxy setting to determine whether
    to trust proxy headers.
    """
    ip = get_client_ip(request, trust_proxy=_trust_proxy)
    return ip or "unknown"


def create_limiter(
    storage_uri: str | None = None,
    key_func: Callable[[Request], str] | None = None,
    default_limits: list[str] | None = None,
    trust_proxy: bool | None = None,
) -> Limiter:
    """
    Create a rate limiter with configurable backend.

    Args:
        storage_uri: Redis URI for distributed rate limiting.
                    None or "memory://" for in-memory storage.
                    Example: "redis://localhost:6379"
        key_func: Function to extract rate limit key from request.
                 Defaults to client IP with proxy header support.
        default_limits: Default rate limits (e.g., ["100/minute"]).
        trust_proxy: Whether to trust X-Forwarded-For headers for client IP.
                    Only set to True when behind a trusted reverse proxy.
                    If None, keeps existing value (defaults to False on first call).

    Returns:
        Configured Limiter instance.

    Example:
        ```python
        # In-memory (single instance)
        limiter = create_limiter()

        # Redis (multi-instance) with proxy support
        limiter = create_limiter(
            storage_uri="redis://localhost:6379",
            trust_proxy=True,
        )

        @app.post("/login")
        @limiter.limit("10/minute")
        async def login(request: Request):
            ...
        ```
    """
    global _limiter, _trust_proxy, _trust_proxy_initialized  # noqa: PLW0603

    with _limiter_lock:
        # Handle trust_proxy: only update if explicitly provided or not yet initialized
        if trust_proxy is not None:
            if _trust_proxy_initialized and _trust_proxy != trust_proxy:
                logger.warning(
                    "rate_limiter_trust_proxy_changed",
                    previous=_trust_proxy,
                    new=trust_proxy,
                    message="trust_proxy setting changed after initialization. "
                    "This may cause inconsistent IP detection.",
                )
            _trust_proxy = trust_proxy
            _trust_proxy_initialized = True
        elif not _trust_proxy_initialized:
            # First initialization with no explicit value - default to False
            _trust_proxy = False
            _trust_proxy_initialized = True

        if key_func is None:
            key_func = _get_client_ip_key

        _limiter = Limiter(
            key_func=key_func,
            storage_uri=storage_uri,
            default_limits=default_limits or [],
        )

        logger.info(
            "rate_limiter_initialized",
            backend="redis" if storage_uri and storage_uri.startswith("redis") else "memory",
            trust_proxy=_trust_proxy,
        )

        return _limiter


def get_rate_limiter() -> Limiter:
    """
    Get the global rate limiter instance.

    Creates an in-memory limiter if not already initialized.
    Thread-safe with double-checked locking pattern.
    """
    global _limiter  # noqa: PLW0603
    if _limiter is None:
        with _limiter_lock:
            if _limiter is None:  # Double-check after acquiring lock
                _limiter = create_limiter()
    return _limiter


def init_rate_limiter(
    storage_uri: str | None = None,
    default_limits: list[str] | None = None,
    trust_proxy: bool | None = None,
) -> Limiter:
    """
    Initialize the global rate limiter.

    Should be called during app startup.

    Args:
        storage_uri: Redis URI or None for in-memory.
        default_limits: Default rate limits.
        trust_proxy: Whether to trust X-Forwarded-For headers.
                    If None, keeps existing value (defaults to False on first call).

    Returns:
        Configured Limiter instance.
    """
    return create_limiter(
        storage_uri=storage_uri,
        default_limits=default_limits,
        trust_proxy=trust_proxy,
    )
