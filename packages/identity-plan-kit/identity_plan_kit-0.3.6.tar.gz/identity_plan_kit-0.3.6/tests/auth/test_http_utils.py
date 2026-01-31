"""Tests for HTTP utilities (P2 IP extraction fix)."""

from unittest.mock import MagicMock

import pytest

from identity_plan_kit.shared.http_utils import get_client_ip, get_user_agent


class TestGetClientIP:
    """Test suite for client IP extraction."""

    def _create_mock_request(
        self,
        headers: dict[str, str] | None = None,
        client_host: str | None = "127.0.0.1",
    ):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.headers = MagicMock()
        request.headers.get = lambda key: (headers or {}).get(key)

        if client_host:
            request.client = MagicMock()
            request.client.host = client_host
        else:
            request.client = None

        return request

    def test_direct_connection(self):
        """Test IP extraction for direct connection (no proxy)."""
        request = self._create_mock_request(client_host="192.168.1.100")

        ip = get_client_ip(request, trust_proxy=False)

        assert ip == "192.168.1.100"

    def test_x_forwarded_for_single_ip(self):
        """Test X-Forwarded-For with single IP."""
        request = self._create_mock_request(
            headers={"X-Forwarded-For": "203.0.113.50"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"

    def test_x_forwarded_for_chain(self):
        """Test X-Forwarded-For with multiple IPs (proxy chain)."""
        request = self._create_mock_request(
            headers={"X-Forwarded-For": "203.0.113.50, 70.41.3.18, 150.172.238.178"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Should return the first (original client) IP
        assert ip == "203.0.113.50"

    def test_x_real_ip(self):
        """Test X-Real-IP header (nginx)."""
        request = self._create_mock_request(
            headers={"X-Real-IP": "203.0.113.50"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"

    def test_cf_connecting_ip(self):
        """Test CF-Connecting-IP header (Cloudflare)."""
        request = self._create_mock_request(
            headers={"CF-Connecting-IP": "203.0.113.50"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"

    def test_header_priority(self):
        """Test that X-Forwarded-For takes priority over other headers."""
        request = self._create_mock_request(
            headers={
                "X-Forwarded-For": "203.0.113.50",
                "X-Real-IP": "192.168.1.1",
                "CF-Connecting-IP": "10.10.10.10",
            },
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"

    def test_no_trust_proxy_ignores_headers(self):
        """Test that headers are ignored when trust_proxy=False."""
        request = self._create_mock_request(
            headers={"X-Forwarded-For": "203.0.113.50"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=False)

        # Should return direct client IP, ignoring header
        assert ip == "10.0.0.1"

    def test_no_client_returns_none(self):
        """Test that None is returned when no client info available."""
        request = self._create_mock_request(client_host=None)

        ip = get_client_ip(request, trust_proxy=False)

        assert ip is None

    def test_whitespace_handling(self):
        """Test that whitespace in headers is handled correctly."""
        request = self._create_mock_request(
            headers={"X-Forwarded-For": "  203.0.113.50  ,  10.0.0.1  "},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"


class TestGetUserAgent:
    """Test suite for user agent extraction."""

    def test_user_agent_extraction(self):
        """Test user agent is extracted from headers."""
        request = MagicMock()
        request.headers.get = lambda key: (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" if key == "user-agent" else None
        )

        ua = get_user_agent(request)

        assert ua == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

    def test_missing_user_agent(self):
        """Test None is returned when user agent is missing."""
        request = MagicMock()
        request.headers.get = lambda key: None

        ua = get_user_agent(request)

        assert ua is None
