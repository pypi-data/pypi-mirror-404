from __future__ import annotations


class XSMeteoError(Exception):
    """Base exception for all xsmeteo errors."""


class RequestError(XSMeteoError):
    """Base exception for request-related errors."""


class HTTPError(RequestError):
    """Exception raised when an HTTP request fails (non-2xx status)."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code


class RateLimitError(RequestError):
    """Exception raised when the rate limit is exceeded."""


class DecodeError(XSMeteoError):
    """Exception raised when response decoding fails."""
