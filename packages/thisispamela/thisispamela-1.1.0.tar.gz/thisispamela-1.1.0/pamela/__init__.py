"""
Pamela Enterprise Voice API SDK for Python

This SDK provides a Pythonic interface to the Pamela Enterprise Voice API,
including call management, tool registration, webhook verification, and
structured error handling.

Example:
    >>> from pamela import PamelaClient
    >>> client = PamelaClient(api_key="pk_live_your_key")
    >>> call = client.create_call(to="+1234567890", task="Schedule meeting")
    >>> print(call["id"])
"""

from pamela.client import PamelaClient, UsageClient
from pamela.webhooks import (
    verify_webhook_signature,
    create_tool_handler,
    parse_tool_webhook,
)
from pamela.exceptions import (
    PamelaError,
    AuthenticationError,
    SubscriptionError,
    RateLimitError,
    ValidationError,
    CallError,
)

# Alias for backward compatibility with tests
Pamela = PamelaClient

__all__ = [
    # Client
    "PamelaClient",
    "Pamela",
    "UsageClient",
    # Webhooks
    "verify_webhook_signature",
    "create_tool_handler",
    "parse_tool_webhook",
    # Exceptions
    "PamelaError",
    "AuthenticationError",
    "SubscriptionError",
    "RateLimitError",
    "ValidationError",
    "CallError",
]
__version__ = "1.0.4"

