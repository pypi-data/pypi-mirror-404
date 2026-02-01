"""
Webhook verification utilities for Pamela Enterprise.

This module provides secure webhook signature verification and helper decorators
for handling tool webhooks in FastAPI/Flask applications.
"""

import hmac
import hashlib
import json
from typing import Union, Dict, Any, Callable, Awaitable, TypeVar, Optional
from functools import wraps

# Type aliases for better readability
WebhookPayload = Dict[str, Any]
ToolResult = Dict[str, Any]
AsyncHandler = Callable[[WebhookPayload], Awaitable[ToolResult]]
F = TypeVar("F", bound=Callable[..., Any])


def verify_webhook_signature(
    payload: Union[str, Dict[str, Any]],
    signature: Optional[str],
    secret: str,
) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        payload: Webhook payload (dict or JSON string)
        signature: Signature from X-Pamela-Signature header (hex-encoded)
        secret: Webhook secret (from Partner Portal or project settings)

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> from pamela import verify_webhook_signature
        >>> is_valid = verify_webhook_signature(
        ...     payload=request.json,
        ...     signature=request.headers.get("X-Pamela-Signature"),
        ...     secret="whsec_your_secret"
        ... )
        >>> if not is_valid:
        ...     return {"error": "Invalid signature"}, 401
    """
    if not signature:
        return False

    if not secret:
        raise ValueError("Webhook secret cannot be empty")

    if isinstance(payload, dict):
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    else:
        payload_str = payload

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def create_tool_handler(secret: str) -> Callable[[F], F]:
    """
    Create a decorator for FastAPI/Flask tool webhook handlers.

    Automatically verifies the webhook signature before calling your handler.
    Returns 401 Unauthorized if signature is invalid.

    Args:
        secret: Webhook secret for signature verification

    Returns:
        Decorator function that wraps your handler

    Example (FastAPI):
        >>> from pamela import create_tool_handler
        >>> from fastapi import Request
        >>>
        >>> tool_handler = create_tool_handler("whsec_your_secret")
        >>>
        >>> @app.post("/webhooks/tools")
        >>> @tool_handler
        >>> async def handle_tool(payload: dict):
        ...     tool_name = payload["tool_name"]
        ...     arguments = payload["arguments"]
        ...     # Execute tool and return result
        ...     return {"result": "success"}

    Example (Flask):
        >>> from pamela import create_tool_handler
        >>>
        >>> tool_handler = create_tool_handler("whsec_your_secret")
        >>>
        >>> @app.route("/webhooks/tools", methods=["POST"])
        >>> @tool_handler
        >>> async def handle_tool(payload: dict):
        ...     return {"result": "success"}
    """
    if not secret:
        raise ValueError("Webhook secret cannot be empty")

    def decorator(handler: F) -> F:
        @wraps(handler)
        async def wrapper(request: Any) -> Any:
            signature = request.headers.get("X-Pamela-Signature")

            # Get payload from request (support both FastAPI and Flask)
            if hasattr(request, "json") and callable(request.json):
                payload = request.json()  # Flask
            elif hasattr(request, "json"):
                payload = request.json  # May be property
            else:
                payload = await request.json()  # FastAPI

            if not verify_webhook_signature(payload, signature, secret):
                return {"error": "Invalid signature"}, 401

            return await handler(payload)

        return wrapper  # type: ignore

    return decorator  # type: ignore


def parse_tool_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate a tool webhook payload.

    Args:
        payload: Raw webhook payload

    Returns:
        Parsed payload with validated fields

    Raises:
        ValueError: If required fields are missing

    Example:
        >>> parsed = parse_tool_webhook(request.json)
        >>> tool_name = parsed["tool_name"]
        >>> arguments = parsed["arguments"]
        >>> correlation_id = parsed["correlation_id"]
    """
    required_fields = ["tool_name", "arguments", "call_id", "correlation_id"]
    missing = [f for f in required_fields if f not in payload]

    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    return {
        "tool_name": str(payload["tool_name"]),
        "arguments": dict(payload.get("arguments", {})),
        "call_id": str(payload["call_id"]),
        "correlation_id": str(payload["correlation_id"]),
        "call_session_id": payload.get("call_session_id"),
        "partner_id": payload.get("partner_id"),
        "project_id": payload.get("project_id"),
    }

