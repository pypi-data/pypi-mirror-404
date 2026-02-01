"""
Tests for Pamela Python SDK.

Includes unit tests (no network) and integration tests (require env vars).
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pamela import (
    PamelaClient,
    verify_webhook_signature,
    create_tool_handler,
    parse_tool_webhook,
    PamelaError,
    AuthenticationError,
    SubscriptionError,
    RateLimitError,
    ValidationError,
    CallError,
)

TEST_API_URL = os.getenv("PAMELA_API_URL", "https://pamela-dev.up.railway.app")
TEST_API_KEY = os.getenv("PAMELA_TEST_API_KEY")


# =============================================================================
# Unit Tests (No Network Required)
# =============================================================================


class TestWebhookVerification:
    """Unit tests for webhook signature verification."""

    def test_verify_valid_signature(self):
        """Test valid signature verification."""
        secret = "test_secret_123"
        payload = {"event": "call.completed", "call_id": "call_123"}
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        import hmac
        import hashlib

        signature = hmac.new(
            secret.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        assert verify_webhook_signature(payload, signature, secret) is True

    def test_verify_invalid_signature(self):
        """Test invalid signature is rejected."""
        secret = "test_secret_123"
        payload = {"event": "call.completed", "call_id": "call_123"}

        assert verify_webhook_signature(payload, "invalid_signature", secret) is False

    def test_verify_none_signature(self):
        """Test None signature is rejected."""
        secret = "test_secret_123"
        payload = {"event": "call.completed"}

        assert verify_webhook_signature(payload, None, secret) is False

    def test_verify_empty_secret_raises(self):
        """Test empty secret raises ValueError."""
        with pytest.raises(ValueError, match="secret cannot be empty"):
            verify_webhook_signature({"test": "payload"}, "sig", "")

    def test_verify_string_payload(self):
        """Test string payload is handled."""
        secret = "test_secret"
        payload_str = '{"test":"value"}'

        import hmac
        import hashlib

        signature = hmac.new(
            secret.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        assert verify_webhook_signature(payload_str, signature, secret) is True


class TestToolWebhookParsing:
    """Unit tests for tool webhook payload parsing."""

    def test_parse_valid_payload(self):
        """Test parsing valid tool webhook payload."""
        payload = {
            "tool_name": "check_order",
            "arguments": {"order_id": "123"},
            "call_id": "call_abc",
            "correlation_id": "corr_xyz",
            "call_session_id": "sess_123",
        }
        result = parse_tool_webhook(payload)

        assert result["tool_name"] == "check_order"
        assert result["arguments"] == {"order_id": "123"}
        assert result["call_id"] == "call_abc"
        assert result["correlation_id"] == "corr_xyz"

    def test_parse_missing_fields_raises(self):
        """Test missing required fields raises ValueError."""
        payload = {"tool_name": "check_order"}

        with pytest.raises(ValueError, match="Missing required fields"):
            parse_tool_webhook(payload)

    def test_parse_empty_arguments(self):
        """Test empty arguments is handled."""
        payload = {
            "tool_name": "no_args_tool",
            "arguments": {},
            "call_id": "call_abc",
            "correlation_id": "corr_xyz",
        }
        result = parse_tool_webhook(payload)

        assert result["arguments"] == {}


class TestExceptionClasses:
    """Unit tests for SDK exception classes."""

    def test_pamela_error_attributes(self):
        """Test PamelaError has correct attributes."""
        error = PamelaError(
            message="Test error",
            error_code=1001,
            details={"key": "value"},
            status_code=403,
        )

        assert error.message == "Test error"
        assert error.error_code == 1001
        assert error.details == {"key": "value"}
        assert error.status_code == 403
        assert str(error) == "Test error"

    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        assert issubclass(AuthenticationError, PamelaError)
        assert issubclass(SubscriptionError, PamelaError)
        assert issubclass(RateLimitError, PamelaError)
        assert issubclass(ValidationError, PamelaError)
        assert issubclass(CallError, PamelaError)

    def test_exceptions_with_minimal_args(self):
        """Test exceptions can be created with minimal arguments."""
        error = AuthenticationError("Invalid API key")
        assert error.message == "Invalid API key"
        assert error.error_code is None
        assert error.details == {}


class TestClientErrorMapping:
    """Unit tests for error mapping in client."""

    def test_401_raises_authentication_error(self):
        """Test 401 response raises AuthenticationError."""
        client = PamelaClient(api_key="pk_live_test", base_url="http://test")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid API key"}

        with pytest.raises(AuthenticationError):
            client._raise_for_error(mock_response, "/calls")

    def test_403_raises_subscription_error(self):
        """Test 403 response raises SubscriptionError."""
        client = PamelaClient(api_key="pk_live_test", base_url="http://test")

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "detail": {
                "error_code": 7008,
                "message": "Subscription expired",
            }
        }

        with pytest.raises(SubscriptionError) as exc_info:
            client._raise_for_error(mock_response, "/calls")

        assert exc_info.value.error_code == 7008

    def test_429_raises_rate_limit_error(self):
        """Test 429 response raises RateLimitError."""
        client = PamelaClient(api_key="pk_live_test", base_url="http://test")

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"detail": "Rate limit exceeded"}

        with pytest.raises(RateLimitError):
            client._raise_for_error(mock_response, "/usage")

    def test_400_raises_validation_error(self):
        """Test 400 response raises ValidationError."""
        client = PamelaClient(api_key="pk_live_test", base_url="http://test")

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid phone number"}

        with pytest.raises(ValidationError):
            client._raise_for_error(mock_response, "/calls")

    def test_call_endpoint_errors_raise_call_error(self):
        """Test errors on /calls endpoints raise CallError."""
        client = PamelaClient(api_key="pk_live_test", base_url="http://test")

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal error"}

        with pytest.raises(CallError):
            client._raise_for_error(mock_response, "/calls/call_123")


class TestClientInitialization:
    """Unit tests for client initialization."""

    def test_default_base_url(self):
        """Test default base URL is set."""
        client = PamelaClient(api_key="pk_live_test")
        assert client.base_url == "https://api.thisispamela.com"

    def test_custom_base_url(self):
        """Test custom base URL is used."""
        client = PamelaClient(api_key="pk_live_test", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"

    def test_usage_client_initialized(self):
        """Test UsageClient is initialized."""
        client = PamelaClient(api_key="pk_live_test")
        assert client.usage is not None


# =============================================================================
# Integration Tests (Require PAMELA_TEST_API_KEY)
# =============================================================================


@pytest.fixture
def sdk():
    """Create SDK instance for testing."""
    if not TEST_API_KEY:
        pytest.skip("PAMELA_TEST_API_KEY not set")
    return PamelaClient(api_key=TEST_API_KEY, base_url=TEST_API_URL)


class TestIntegrationInitialization:
    """Integration tests for SDK initialization."""

    def test_initialize_with_api_key(self, sdk):
        """Test SDK initializes with API key."""
        assert sdk is not None


class TestIntegrationCalls:
    """Integration tests for calls."""

    def test_list_calls(self, sdk):
        """Test listing calls."""
        result = sdk.list_calls(limit=1)
        assert "items" in result

    def test_get_call_status_if_available(self, sdk):
        """Test fetching status for the newest call if present."""
        result = sdk.list_calls(limit=1)
        items = result.get("items", [])
        if not items:
            pytest.skip("No calls available to test get_call")
        call_id = items[0].get("id")
        status = sdk.get_call(call_id)
        assert status.get("id") == call_id


class TestIntegrationUsage:
    """Integration tests for usage queries."""

    def test_get_usage(self, sdk):
        """Test gets usage statistics."""
        usage = sdk.usage.get()
        assert "call_count" in usage


