"""Shared, non-business SDK models.

These are infrastructure models only (envelopes, pagination, request context,
error payloads). No recruiting/business object models live here — those stay in
the application layer and are added in future phases.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    """Context describing a single outbound CRM request (for logging/tracing)."""

    method: str
    path: str
    url: str
    has_body: bool = False


class Pagination(BaseModel):
    """Cursor/limit pagination envelope (Twenty uses opaque cursors)."""

    limit: Optional[int] = None
    starting_after: Optional[str] = None
    ending_before: Optional[str] = None
    has_next_page: Optional[bool] = None
    end_cursor: Optional[str] = None


class APIResponse(BaseModel):
    """Generic wrapper around a parsed CRM response body.

    `data` holds the raw parsed JSON exactly as returned by the CRM. This is a
    thin, optional convenience — the SDK client still returns raw dicts by
    default to preserve current behavior.
    """

    status_code: int
    data: Dict[str, Any] = Field(default_factory=dict)
    pagination: Optional[Pagination] = None


class ErrorResponse(BaseModel):
    """Structured representation of a CRM error payload."""

    status_code: Optional[int] = None
    message: str
    detail: Optional[str] = None
