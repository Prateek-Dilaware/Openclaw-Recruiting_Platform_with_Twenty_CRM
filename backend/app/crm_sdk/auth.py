"""CRM SDK authentication helpers.

Extracted from `TwentyService.__init__`, which constructed a static bearer-token
header dict. `build_headers` reproduces that exact header shape so requests are
identical to before.
"""

from __future__ import annotations

from typing import Dict


def build_headers(api_key: str) -> Dict[str, str]:
    """Return the standard Twenty CRM auth headers.

    Matches the original TwentyService header dict exactly:
        Authorization: Bearer <api_key>
        Content-Type: application/json
    """
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
