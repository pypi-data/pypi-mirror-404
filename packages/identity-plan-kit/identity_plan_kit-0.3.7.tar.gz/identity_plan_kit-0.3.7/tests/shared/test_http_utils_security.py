"""Security tests for HTTP utilities.

Tests cover:
- IPv6 address handling
- Malformed IP addresses
- Header injection attempts
- IP spoofing scenarios
- Edge cases and boundary conditions

CRITICAL: These tests ensure IP extraction cannot be
exploited for rate limiting bypass or audit log pollution.
"""

from unittest.mock import MagicMock

import pytest

from identity_plan_kit.shared.http_utils import get_client_ip, get_user_agent


def create_mock_request(
    headers: dict[str, str] | None = None,
    client_host: str | None = "127.0.0.1",
) -> MagicMock:
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


class TestIPv6Addresses:
    """Test IPv6 address handling."""

    def test_ipv6_direct_connection(self):
        """IPv6 direct connection is handled correctly."""
        request = create_mock_request(client_host="2001:db8::1")

        ip = get_client_ip(request, trust_proxy=False)

        assert ip == "2001:db8::1"

    def test_ipv6_in_x_forwarded_for(self):
        """IPv6 address in X-Forwarded-For is extracted."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "2001:db8::1"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "2001:db8::1"

    def test_ipv6_loopback(self):
        """IPv6 loopback address is handled."""
        request = create_mock_request(client_host="::1")

        ip = get_client_ip(request, trust_proxy=False)

        assert ip == "::1"

    def test_ipv6_full_format(self):
        """Full IPv6 format is preserved."""
        full_ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        request = create_mock_request(
            headers={"X-Forwarded-For": full_ipv6},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == full_ipv6

    def test_ipv6_with_zone_id(self):
        """IPv6 with zone ID is handled."""
        # Zone IDs are used for link-local addresses
        ipv6_with_zone = "fe80::1%eth0"
        request = create_mock_request(
            headers={"X-Forwarded-For": ipv6_with_zone},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == ipv6_with_zone

    def test_ipv6_compressed(self):
        """Compressed IPv6 format is handled."""
        request = create_mock_request(client_host="::ffff:192.0.2.1")

        ip = get_client_ip(request, trust_proxy=False)

        assert ip == "::ffff:192.0.2.1"

    def test_ipv6_mixed_chain(self):
        """Chain of mixed IPv4 and IPv6 addresses."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "2001:db8::1, 192.168.1.1, 10.0.0.1"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Should return first IP (IPv6)
        assert ip == "2001:db8::1"


class TestMalformedIPAddresses:
    """Test handling of malformed IP addresses."""

    def test_empty_header_value(self):
        """Empty header value falls back to client IP."""
        request = create_mock_request(
            headers={"X-Forwarded-For": ""},
            client_host="192.168.1.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Empty string is falsy, so it falls back
        assert ip == "192.168.1.1"

    def test_whitespace_only_header(self):
        """Whitespace-only header falls back to client IP."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "   "},
            client_host="192.168.1.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Stripped whitespace is empty, falls back
        assert ip == "192.168.1.1"

    def test_comma_only_header(self):
        """Comma-only header returns empty string before comma."""
        request = create_mock_request(
            headers={"X-Forwarded-For": ", , ,"},
            client_host="192.168.1.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # First element before comma is empty after strip
        # Should fall back to client IP
        assert ip == "192.168.1.1"

    def test_invalid_ip_format_still_returned(self):
        """Invalid IP format is still returned (validation is caller's job)."""
        # The http_utils module extracts IPs, doesn't validate them
        invalid_ip = "not.an.ip.address"
        request = create_mock_request(
            headers={"X-Forwarded-For": invalid_ip},
            client_host="192.168.1.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Invalid format still returned - validation is separate concern
        assert ip == invalid_ip

    def test_extra_colons_in_header(self):
        """IP with extra colons (malformed) is still extracted."""
        malformed = "192.168.1.1:8080:extra"
        request = create_mock_request(
            headers={"X-Forwarded-For": malformed},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == malformed

    def test_very_long_header_value(self):
        """Very long header value is handled without crash."""
        long_value = "192.168.1.1, " * 1000 + "10.0.0.1"
        request = create_mock_request(
            headers={"X-Forwarded-For": long_value},
            client_host="127.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Should extract first IP
        assert ip == "192.168.1.1"


class TestIPSpoofingScenarios:
    """Test IP spoofing attack scenarios."""

    def test_trust_proxy_false_ignores_spoofed_headers(self):
        """With trust_proxy=False, spoofed headers are ignored."""
        # Attacker sends fake X-Forwarded-For
        request = create_mock_request(
            headers={
                "X-Forwarded-For": "1.2.3.4",  # Attacker's fake IP
                "X-Real-IP": "5.6.7.8",
            },
            client_host="203.0.113.50",  # Real attacker IP
        )

        ip = get_client_ip(request, trust_proxy=False)

        # Should return real client IP, not spoofed
        assert ip == "203.0.113.50"

    def test_localhost_spoofing_blocked(self):
        """Attacker cannot spoof localhost via headers (with trust_proxy=False)."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "127.0.0.1"},
            client_host="203.0.113.50",
        )

        ip = get_client_ip(request, trust_proxy=False)

        # Should not be spoofable to localhost
        assert ip == "203.0.113.50"

    def test_internal_ip_spoofing_blocked(self):
        """Attacker cannot spoof internal IP (with trust_proxy=False)."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "10.0.0.1"},  # Internal IP
            client_host="203.0.113.50",
        )

        ip = get_client_ip(request, trust_proxy=False)

        # Should return real external IP
        assert ip == "203.0.113.50"

    def test_multiple_headers_first_wins(self):
        """When multiple proxy headers exist, priority order is maintained."""
        request = create_mock_request(
            headers={
                "X-Forwarded-For": "first.ip.1.1",
                "X-Real-IP": "second.ip.2.2",
                "CF-Connecting-IP": "third.ip.3.3",
            },
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # X-Forwarded-For has highest priority
        assert ip == "first.ip.1.1"


class TestHeaderInjectionAttempts:
    """Test resistance to header injection attacks."""

    def test_newline_in_header_value(self):
        """Newline characters in header value don't cause issues."""
        # Some header injection attacks use newlines
        request = create_mock_request(
            headers={"X-Forwarded-For": "192.168.1.1\n192.168.2.2"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Should handle newlines (they become part of the IP string)
        # Actual validation happens elsewhere
        assert ip is not None

    def test_null_byte_in_header(self):
        """Null byte in header value doesn't cause crash."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "192.168.1.1\x00malicious"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Should handle null bytes
        assert ip is not None

    def test_unicode_in_header(self):
        """Unicode characters in header are handled."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "192.168.1.1\u200b"},  # Zero-width space
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Should handle unicode
        assert ip is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_no_client_no_headers(self):
        """No client and no headers returns None."""
        request = create_mock_request(client_host=None)

        ip = get_client_ip(request, trust_proxy=False)

        assert ip is None

    def test_no_client_with_headers_trusted(self):
        """No client but valid headers returns header IP when trusted."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "192.168.1.1"},
            client_host=None,
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "192.168.1.1"

    def test_single_ip_with_trailing_comma(self):
        """Single IP with trailing comma is handled."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "192.168.1.1,"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "192.168.1.1"

    def test_ip_with_port(self):
        """IP:port format is returned as-is (caller can parse)."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "192.168.1.1:8080"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        # Port included - caller's responsibility to parse
        assert ip == "192.168.1.1:8080"

    def test_ipv6_with_port_brackets(self):
        """IPv6 with port in brackets is handled."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "[2001:db8::1]:8080"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "[2001:db8::1]:8080"


class TestUserAgentSecurity:
    """Test user agent extraction security."""

    def test_very_long_user_agent(self):
        """Very long user agent is handled without crash."""
        long_ua = "Mozilla/5.0 " + "a" * 10000
        request = MagicMock()
        request.headers.get = lambda key: long_ua if key == "user-agent" else None

        ua = get_user_agent(request)

        # Should return full value (truncation is caller's job)
        assert ua == long_ua

    def test_unicode_user_agent(self):
        """Unicode in user agent is handled."""
        unicode_ua = "Mozilla/5.0 (🔥 Firefox)"
        request = MagicMock()
        request.headers.get = lambda key: unicode_ua if key == "user-agent" else None

        ua = get_user_agent(request)

        assert ua == unicode_ua

    def test_null_byte_in_user_agent(self):
        """Null byte in user agent doesn't cause crash."""
        request = MagicMock()
        request.headers.get = lambda key: "Mozilla\x005.0" if key == "user-agent" else None

        ua = get_user_agent(request)

        assert ua is not None


class TestCloudflareHeaders:
    """Test Cloudflare-specific header handling."""

    def test_cf_connecting_ip_preferred(self):
        """CF-Connecting-IP is used when X-Forwarded-For absent."""
        request = create_mock_request(
            headers={"CF-Connecting-IP": "203.0.113.50"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"

    def test_x_forwarded_for_takes_priority_over_cf(self):
        """X-Forwarded-For has priority over CF-Connecting-IP."""
        request = create_mock_request(
            headers={
                "X-Forwarded-For": "1.1.1.1",
                "CF-Connecting-IP": "2.2.2.2",
            },
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "1.1.1.1"


class TestAkamaiHeaders:
    """Test Akamai-specific header handling."""

    def test_true_client_ip_header(self):
        """True-Client-IP (Akamai) is supported."""
        request = create_mock_request(
            headers={"True-Client-IP": "203.0.113.50"},
            client_host="10.0.0.1",
        )

        ip = get_client_ip(request, trust_proxy=True)

        assert ip == "203.0.113.50"


class TestSecurityBestPractices:
    """Tests demonstrating security best practices."""

    def test_default_is_not_trust_proxy(self):
        """Default behavior should not trust proxy headers."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "spoofed.ip"},
            client_host="real.client.ip",
        )

        # Default trust_proxy=False
        ip = get_client_ip(request)

        assert ip == "real.client.ip"

    def test_explicit_trust_required(self):
        """Proxy headers only used when explicitly trusted."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "proxy.ip"},
            client_host="direct.ip",
        )

        ip_untrusted = get_client_ip(request, trust_proxy=False)
        ip_trusted = get_client_ip(request, trust_proxy=True)

        assert ip_untrusted == "direct.ip"
        assert ip_trusted == "proxy.ip"
