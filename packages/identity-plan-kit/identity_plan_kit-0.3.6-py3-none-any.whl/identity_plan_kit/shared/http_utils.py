"""HTTP utilities for request handling."""

from fastapi import Request

from identity_plan_kit.shared.logging import get_logger

logger = get_logger(__name__)

# Trusted proxy headers in order of preference
FORWARDED_HEADERS = [
    "X-Forwarded-For",
    "X-Real-IP",
    "CF-Connecting-IP",  # Cloudflare
    "True-Client-IP",  # Akamai
]


def get_client_ip(request: Request, trust_proxy: bool = False) -> str | None:
    """
    Extract the real client IP address from a request.

    Handles reverse proxy headers (nginx, load balancers, Cloudflare, etc.)

    Args:
        request: FastAPI request object
        trust_proxy: Whether to trust proxy headers.
                    Default is False for security.
                    Set to True only when behind a trusted reverse proxy.
                    Use config.trust_proxy_headers to configure globally.

    Returns:
        Client IP address or None if not determinable

    Security Warning:
        Only set trust_proxy=True if your application is behind a trusted proxy.
        An attacker can spoof these headers if requests reach your app directly,
        which could bypass rate limiting and pollute audit logs.
    """
    if trust_proxy:
        for header in FORWARDED_HEADERS:
            value = request.headers.get(header)
            if value:
                # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
                # The first one is the original client
                ip = value.split(",")[0].strip()
                if ip:
                    logger.debug(
                        "client_ip_from_header",
                        header=header,
                        ip=ip,
                    )
                    return ip

    # Fall back to direct connection IP
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> str | None:
    """Extract user agent from request."""
    return request.headers.get("user-agent")
