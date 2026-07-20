"""CRM SDK exception hierarchy.

These exceptions provide a structured error surface for the SDK client so that
callers can distinguish auth, validation, transport, and HTTP-status failures.

NOTE (Phase 1.2): The current `TwentyService` raises plain `Exception` objects.
To preserve *exactly* the existing runtime behavior, the SDK client raises
`CRMRequestError` (a subclass of `Exception`) with the same message format that
`TwentyService._request` used. Nothing catches these by a more specific type yet,
so behavior is unchanged. Future phases can start catching the richer types.
"""

from __future__ import annotations

from typing import Any, Optional


class CRMError(Exception):
    """Base class for all CRM SDK errors."""


class AuthenticationError(CRMError):
    """Raised when credentials are missing or rejected (HTTP 401/403)."""


class ValidationError(CRMError):
    """Raised when client-side validation fails before a request is sent."""


class RequestError(CRMError):
    """Base class for errors that occur while performing a request."""


class CRMRequestError(RequestError):
    """Transport/HTTP failure while communicating with the CRM.

    Carries optional HTTP context so future callers can branch on it without
    parsing the message string.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.cause = cause


class RateLimitError(CRMRequestError):
    """Raised when the CRM returns HTTP 429."""


class NotFoundError(CRMRequestError):
    """Raised when the CRM returns HTTP 404."""


class ConflictError(CRMRequestError):
    """Raised when the CRM returns HTTP 409."""


def error_for_status(
    status_code: int,
    message: str,
    *,
    response_text: Optional[str] = None,
    cause: Optional[BaseException] = None,
) -> CRMRequestError:
    """Map an HTTP status code to the most specific SDK request error.

    Returns (does not raise) so callers control the raise site.
    """
    kwargs: dict[str, Any] = {
        "status_code": status_code,
        "response_text": response_text,
        "cause": cause,
    }
    if status_code == 404:
        return NotFoundError(message, **kwargs)
    if status_code == 409:
        return ConflictError(message, **kwargs)
    if status_code == 429:
        return RateLimitError(message, **kwargs)
    return CRMRequestError(message, **kwargs)
