"""
Custom exceptions for the Pamela Python SDK.
"""

from typing import Optional, Dict, Any


class PamelaError(Exception):
    """Base exception for Pamela SDK."""

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(PamelaError):
    """API key is invalid or expired."""


class SubscriptionError(PamelaError):
    """Enterprise subscription is inactive or expired."""


class RateLimitError(PamelaError):
    """Rate limit exceeded."""


class ValidationError(PamelaError):
    """Request validation failed."""


class CallError(PamelaError):
    """Call-related error."""
