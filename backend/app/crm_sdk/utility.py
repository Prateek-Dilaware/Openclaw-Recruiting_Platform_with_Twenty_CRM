"""Common, non-business SDK utilities.

Only generic, reusable helpers live here. Recruiting/business logic does not.

Phase 1.2 note: these helpers are provided for future router/SDK use. They are
NOT wired into `TwentyService` yet, so no existing behavior changes. The Twenty
field-shape builders below mirror the structured-field format Twenty expects
(EMAILS/PHONES) and the BlockNote body format — these are CRM-generic data
shapes, not recruiting rules.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def unwrap_data(payload: Dict[str, Any], key: Optional[str] = None) -> Any:
    """Return ``payload['data'][key]`` when present, else sensible fallbacks.

    Mirrors the ``response.get("data", {}).get(<key>, ...)`` unwrapping pattern
    used throughout the current TwentyService, centralized for reuse.
    """
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if key is None:
        return data
    if isinstance(data, dict):
        return data.get(key)
    return None


def build_email_field(value: str) -> Dict[str, Any]:
    """Build Twenty's EMAILS structured field from a plain string."""
    return {"primaryEmail": value, "additionalEmails": []}


def build_phone_field(value: str) -> Dict[str, Any]:
    """Build Twenty's PHONES structured field from a plain string."""
    return {
        "primaryPhoneNumber": value,
        "primaryPhoneCountryCode": "",
        "primaryPhoneCallingCode": "",
        "additionalPhones": [],
    }


def build_blocknote_body(content: str) -> Dict[str, Any]:
    """Build Twenty's ``bodyV2`` BlockNote structure from markdown text."""
    blocks: List[Dict[str, Any]] = [
        {"type": "paragraph", "content": [{"type": "text", "text": paragraph}]}
        for paragraph in content.split("\n")
    ]
    return {"blocknote": json.dumps(blocks), "markdown": content}
