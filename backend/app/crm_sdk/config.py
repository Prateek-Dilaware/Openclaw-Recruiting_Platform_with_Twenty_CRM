"""CRM SDK connection configuration.

Extracted from `TwentyService.__init__`, which built its base URL + auth from
`app.settings.settings`. `CRMConfig.from_settings()` reproduces that exact logic
(``TWENTY_API_URL.rstrip("/")`` and the ``TWENTY_API_KEY`` bearer token) so the
default behavior is byte-for-byte identical.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Default request timeout (seconds). Matches the previous TwentyService._request
# timeout of 15.0 so no request behavior changes.
DEFAULT_TIMEOUT_SECONDS: float = 15.0

# REST path prefix used by the Twenty CRM records/metadata API.
REST_PREFIX: str = "rest"


@dataclass
class CRMConfig:
    """Immutable connection settings for the CRM SDK client."""

    base_url: str
    api_key: str
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    rest_prefix: str = REST_PREFIX

    @classmethod
    def from_settings(cls, settings_obj: Optional[object] = None) -> "CRMConfig":
        """Build a config from the app settings object.

        Reproduces the original TwentyService behavior exactly.
        """
        if settings_obj is None:
            from app.settings import settings as settings_obj  # local import avoids cycles

        base_url = str(getattr(settings_obj, "TWENTY_API_URL", "")).rstrip("/")
        api_key = str(getattr(settings_obj, "TWENTY_API_KEY", ""))
        return cls(base_url=base_url, api_key=api_key)
