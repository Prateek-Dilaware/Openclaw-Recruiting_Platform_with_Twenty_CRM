"""Centralized, non-business input validation for the CRM SDK.

Only infrastructure-level validation lives here (UUIDs, required fields,
pagination bounds, object-name shape). No recruiting/business rules.

These helpers are provided for use by future router handlers. They are NOT wired
into `TwentyService` in Phase 1.2, so no existing behavior changes.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Optional
from uuid import UUID

from app.crm_sdk.exceptions import ValidationError

# Twenty object names are lowerCamel/plural identifiers, e.g. "candidates".
_OBJECT_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*$")


def validate_uuid(value: str, *, field: str = "id") -> str:
    """Ensure `value` is a valid UUID string; return it unchanged."""
    try:
        UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValidationError(f"{field} must be a valid UUID, got: {value!r}") from exc
    return value


def require_fields(data: Mapping[str, Any], fields: Iterable[str]) -> None:
    """Raise if any required field is missing or None in `data`."""
    missing = [f for f in fields if data.get(f) is None]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}")


def validate_object_name(name: str) -> str:
    """Ensure a CRM object/collection name has a safe identifier shape."""
    if not name or not _OBJECT_NAME_RE.match(name):
        raise ValidationError(f"Invalid object name: {name!r}")
    return name


def validate_pagination(limit: Optional[int]) -> Optional[int]:
    """Validate a pagination limit (positive, <= 1000 per Twenty's cap)."""
    if limit is None:
        return None
    if not isinstance(limit, int) or limit <= 0 or limit > 1000:
        raise ValidationError(f"limit must be an integer in 1..1000, got: {limit!r}")
    return limit
