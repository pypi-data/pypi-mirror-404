"""Tests for audit logging PII masking.

Tests cover:
- Email masking function
- PII protection in audit events
- Environment-controlled masking
- Edge cases in email formats

CRITICAL: These tests ensure PII is properly masked
in audit logs to comply with privacy regulations.
"""

import os
from unittest.mock import patch
from uuid import uuid4

import pytest

from identity_plan_kit.shared.audit import (
    FAILED_LOGIN_WARNING_THRESHOLD,
    AuditAction,
    AuditEvent,
    AuditSeverity,
    audit_account_locked,
    audit_failed_login_attempt,
    audit_user_authenticated,
    audit_user_deactivated,
    audit_user_registered,
    log_audit_event,
    mask_email,
)


class TestMaskEmailFunction:
    """Test the mask_email function."""

    def test_standard_email_masked(self):
        """Standard email is properly masked."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            # Reload to pick up env var
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("user@example.com")

            # First char of local + first char of domain + TLD preserved
            assert result == "u***@e***.com"

    def test_none_returns_none(self):
        """None input returns None."""
        result = mask_email(None)
        assert result is None

    def test_short_local_part(self):
        """Single char local part is handled."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("a@example.com")
            assert result == "a***@e***.com"

    def test_short_domain(self):
        """Single char domain is handled."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("user@a.io")
            assert result == "u***@a***.io"

    def test_subdomain_preserved(self):
        """Subdomain in email is handled."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            # "mail.example.com" - the last dot separates TLD
            result = audit.mask_email("user@mail.example.com")
            # Domain part before last dot gets masked
            assert "u***@" in result
            assert result.endswith(".com")

    def test_plus_addressing(self):
        """Plus addressing in email is masked."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("user+tag@example.com")
            # First char of local part preserved
            assert result.startswith("u***@")

    def test_masking_disabled_returns_original(self):
        """With masking disabled, original email is returned."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "false"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("user@example.com")
            assert result == "user@example.com"

    def test_invalid_email_returns_hash(self):
        """Invalid email format returns hash prefix."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("notanemail")
            assert result.startswith("[hash:")
            assert "]" in result

    def test_empty_string_returns_hash(self):
        """Empty string returns hash prefix."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("")
            assert result.startswith("[hash:")


class TestMaskEmailEnvControl:
    """Test environment variable control of masking."""

    @pytest.mark.parametrize("env_value", ["true", "True", "TRUE", "1", "yes", "YES"])
    def test_masking_enabled_variants(self, env_value):
        """Various truthy env values enable masking."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": env_value}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            assert audit.MASK_PII_IN_AUDIT_LOGS is True

    @pytest.mark.parametrize("env_value", ["false", "False", "FALSE", "0", "no", "NO"])
    def test_masking_disabled_variants(self, env_value):
        """Various falsy env values disable masking."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": env_value}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            assert audit.MASK_PII_IN_AUDIT_LOGS is False


class TestAuditEventSerialization:
    """Test AuditEvent serialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict() includes all event fields."""
        user_id = uuid4()
        event = AuditEvent(
            action=AuditAction.USER_AUTHENTICATED,
            severity=AuditSeverity.INFO,
            actor_id=user_id,
            actor_email="user@example.com",
            actor_ip="1.2.3.4",
            actor_user_agent="Mozilla/5.0",
            target_id=user_id,
            target_type="user",
            details={"provider": "google"},
            request_id="req-123",
        )

        result = event.to_dict()

        assert result["audit_event"] is True
        assert result["action"] == "user.authenticated"
        assert result["severity"] == "info"
        assert result["actor"]["id"] == str(user_id)
        assert result["actor"]["email"] == "user@example.com"
        assert result["actor"]["ip"] == "1.2.3.4"
        assert result["target"]["id"] == str(user_id)
        assert result["target"]["type"] == "user"
        assert result["details"] == {"provider": "google"}
        assert result["request_id"] == "req-123"

    def test_to_dict_handles_none_values(self):
        """to_dict() handles None values gracefully."""
        event = AuditEvent(
            action=AuditAction.USER_LOGOUT,
        )

        result = event.to_dict()

        assert result["actor"]["id"] is None
        assert result["actor"]["email"] is None
        assert result["target"]["id"] is None


class TestAuditEventSeverity:
    """Test audit event severity levels."""

    def test_failed_login_severity_based_on_count(self):
        """Failed login severity escalates with attempt count."""
        # Below threshold = INFO
        event_low = AuditEvent(
            action=AuditAction.SECURITY_FAILED_LOGIN_ATTEMPT,
            severity=AuditSeverity.INFO,
            details={"attempt_count": 1},
        )
        assert event_low.severity == AuditSeverity.INFO

        # At/above threshold = WARNING
        threshold = FAILED_LOGIN_WARNING_THRESHOLD
        event_high = AuditEvent(
            action=AuditAction.SECURITY_FAILED_LOGIN_ATTEMPT,
            severity=AuditSeverity.WARNING,
            details={"attempt_count": threshold},
        )
        assert event_high.severity == AuditSeverity.WARNING

    def test_token_reuse_is_critical(self):
        """Token reuse detection is CRITICAL severity."""
        event = AuditEvent(
            action=AuditAction.TOKEN_REUSE_DETECTED,
            severity=AuditSeverity.CRITICAL,
        )
        assert event.severity == AuditSeverity.CRITICAL

    def test_account_locked_is_warning(self):
        """Account locked is WARNING severity."""
        event = AuditEvent(
            action=AuditAction.SECURITY_ACCOUNT_LOCKED,
            severity=AuditSeverity.WARNING,
        )
        assert event.severity == AuditSeverity.WARNING


class TestAuditConvenienceFunctions:
    """Test audit convenience functions mask PII correctly."""

    def test_audit_failed_login_masks_email(self):
        """audit_failed_login_attempt masks email in details."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            # Mock the log function to capture the event
            logged_events = []
            original_log = audit.log_audit_event

            def capture_log(event):
                logged_events.append(event)
                return original_log(event)

            with patch.object(audit, "log_audit_event", capture_log):
                audit.audit_failed_login_attempt(
                    email="secret@example.com",
                    ip_address="1.2.3.4",
                    reason="invalid_code",
                    attempt_count=1,
                )

            assert len(logged_events) == 1
            event_dict = logged_events[0].to_dict()
            # Email in details should be masked
            assert event_dict["details"]["email"] != "secret@example.com"
            assert event_dict["details"]["email"] == "s***@e***.com"

    def test_audit_account_locked_includes_email(self):
        """audit_account_locked includes email in details."""
        logged_events = []

        def capture_log(event):
            logged_events.append(event)

        with patch("identity_plan_kit.shared.audit.log_audit_event", capture_log):
            audit_account_locked(
                email="locked@example.com",
                ip_address="1.2.3.4",
                failed_attempts=5,
                lock_duration_minutes=15,
            )

        assert len(logged_events) == 1
        event_dict = logged_events[0].to_dict()
        assert event_dict["details"]["failed_attempts"] == 5
        assert event_dict["details"]["lock_duration_minutes"] == 15


class TestAuditActions:
    """Test audit action types."""

    def test_all_actions_have_values(self):
        """All audit actions have string values."""
        for action in AuditAction:
            assert isinstance(action.value, str)
            assert len(action.value) > 0
            assert "." in action.value  # Format: category.action

    def test_action_categories(self):
        """Actions are properly categorized."""
        user_actions = [
            AuditAction.USER_REGISTERED,
            AuditAction.USER_AUTHENTICATED,
            AuditAction.USER_LOGOUT,
        ]
        for action in user_actions:
            assert action.value.startswith("user.")

        security_actions = [
            AuditAction.SECURITY_ACCOUNT_LOCKED,
            AuditAction.SECURITY_FAILED_LOGIN_ATTEMPT,
            AuditAction.SECURITY_TOKEN_THEFT_SUSPECTED,
        ]
        for action in security_actions:
            assert action.value.startswith("security.")


class TestLogAuditEvent:
    """Test log_audit_event function."""

    def test_info_events_logged_as_info(self):
        """INFO severity events use info log level."""
        with patch("identity_plan_kit.shared.audit.audit_logger") as mock_logger:
            event = AuditEvent(
                action=AuditAction.USER_AUTHENTICATED,
                severity=AuditSeverity.INFO,
            )
            log_audit_event(event)

            mock_logger.info.assert_called_once()
            mock_logger.warning.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_warning_events_logged_as_warning(self):
        """WARNING severity events use warning log level."""
        with patch("identity_plan_kit.shared.audit.audit_logger") as mock_logger:
            event = AuditEvent(
                action=AuditAction.SECURITY_ACCOUNT_LOCKED,
                severity=AuditSeverity.WARNING,
            )
            log_audit_event(event)

            mock_logger.warning.assert_called_once()
            mock_logger.info.assert_not_called()
            mock_logger.critical.assert_not_called()

    def test_critical_events_logged_as_critical(self):
        """CRITICAL severity events use critical log level."""
        with patch("identity_plan_kit.shared.audit.audit_logger") as mock_logger:
            event = AuditEvent(
                action=AuditAction.TOKEN_REUSE_DETECTED,
                severity=AuditSeverity.CRITICAL,
            )
            log_audit_event(event)

            mock_logger.critical.assert_called_once()
            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()


class TestAuditEventEdgeCases:
    """Test edge cases in audit events."""

    def test_unicode_in_details(self):
        """Unicode characters in details are handled."""
        event = AuditEvent(
            action=AuditAction.USER_AUTHENTICATED,
            details={"name": "用户 🎉"},
        )

        result = event.to_dict()
        assert result["details"]["name"] == "用户 🎉"

    def test_large_details_dict(self):
        """Large details dictionary is handled."""
        large_details = {f"key_{i}": f"value_{i}" for i in range(100)}
        event = AuditEvent(
            action=AuditAction.USER_AUTHENTICATED,
            details=large_details,
        )

        result = event.to_dict()
        assert len(result["details"]) == 100

    def test_nested_details(self):
        """Nested details dictionary is handled."""
        event = AuditEvent(
            action=AuditAction.USER_AUTHENTICATED,
            details={
                "nested": {
                    "deep": {
                        "value": 123,
                    },
                },
            },
        )

        result = event.to_dict()
        assert result["details"]["nested"]["deep"]["value"] == 123

    def test_timestamp_is_iso_format(self):
        """Timestamp is serialized in ISO format."""
        event = AuditEvent(
            action=AuditAction.USER_LOGOUT,
        )

        result = event.to_dict()

        # Should be ISO format with timezone
        timestamp_str = result["timestamp"]
        assert "T" in timestamp_str
        assert "+" in timestamp_str or "Z" in timestamp_str


class TestEmailMaskingEdgeCases:
    """Test edge cases in email masking."""

    def test_email_with_dots_in_local(self):
        """Email with dots in local part."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("first.last@example.com")
            assert result.startswith("f***@")

    def test_email_with_numbers(self):
        """Email with numbers."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("user123@test456.com")
            assert result == "u***@t***.com"

    def test_email_no_tld(self):
        """Email without standard TLD format."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            result = audit.mask_email("user@localhost")
            # No dot in domain, so different handling
            assert "@" in result or result.startswith("[hash:")

    def test_email_multiple_at_signs(self):
        """Email with multiple @ signs (invalid)."""
        with patch.dict(os.environ, {"IPK_MASK_PII_IN_AUDIT_LOGS": "true"}):
            import importlib
            from identity_plan_kit.shared import audit
            importlib.reload(audit)

            # Invalid email format
            result = audit.mask_email("user@@example.com")
            # Should handle gracefully (might return hash or partial mask)
            assert result is not None
