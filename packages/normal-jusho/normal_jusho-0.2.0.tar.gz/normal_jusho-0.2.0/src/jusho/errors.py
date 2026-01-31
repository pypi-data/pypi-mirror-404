"""Custom exception hierarchy for the Jusho SDK.

All exceptions inherit from :class:`JushoError` so callers can catch a
single base class if they prefer broad error handling.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class JushoError(Exception):
    """Base exception for all Jusho SDK errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code if the error originated from an API
            response, otherwise ``None``.
        body: Parsed response body (dict) if available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.body = body

    def __repr__(self) -> str:
        parts = [f"JushoError({self.message!r}"]
        if self.status_code is not None:
            parts.append(f", status_code={self.status_code}")
        parts.append(")")
        return "".join(parts)


class NetworkError(JushoError):
    """Raised when an HTTP request fails due to a network-level issue.

    This covers DNS failures, connection timeouts, socket errors, and
    similar transport-level problems.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TimeoutError(JushoError):
    """Raised when an HTTP request exceeds the configured timeout."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)


class APIError(JushoError):
    """Raised for unexpected API error responses (5xx, etc.).

    Attributes:
        status_code: The HTTP status code.
        body: Parsed response body if JSON was returned.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)


class NotFoundError(JushoError):
    """Raised when the requested address or resource is not found (404)."""

    def __init__(
        self,
        message: str = "Address not found",
        *,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=404, body=body)


class ValidationError(JushoError):
    """Raised when the request is invalid (422 Unprocessable Entity)."""

    def __init__(
        self,
        message: str = "Validation error",
        *,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=422, body=body)


class RateLimitError(JushoError):
    """Raised when the API rate limit is exceeded (429).

    Attributes:
        retry_after: Number of seconds to wait before retrying, if the
            server provided a ``Retry-After`` header.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=429, body=body)
        self.retry_after = retry_after
