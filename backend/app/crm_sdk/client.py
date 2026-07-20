"""CRM SDK HTTP client.

This is the reusable transport layer extracted from `TwentyService._request`.
It centralizes: URL generation, header injection, request execution (httpx),
response parsing, status handling, and error handling + logging.

BEHAVIOR-PRESERVATION CONTRACT (Phase 1.2)
------------------------------------------
`request()` reproduces the original `TwentyService._request` semantics exactly:
  * URL built as ``{base_url}/rest/{path.lstrip('/')}``
  * bearer auth headers, ``timeout=15.0``
  * ``response.raise_for_status()``; HTTP 204 -> ``{}``; else ``response.json()``
  * on `httpx.HTTPStatusError`  -> error message ``"Twenty CRM Error: <code> - <text>"``
  * on any other exception      -> error message ``"Failed to communicate with Twenty CRM: <e>"``

The original raised plain ``Exception`` with those messages. The SDK raises
``CRMRequestError`` (a subclass of ``Exception``) with the *same message text*,
so ``except Exception`` callers behave identically.

Retry: the original TwentyService had NO retry, so retries default to disabled
(``max_attempts=1``) to keep behavior identical. Retry support is included as an
opt-in for future callers (the schema-tooling client already uses this pattern).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from app.crm_sdk.auth import build_headers
from app.crm_sdk.config import CRMConfig
from app.crm_sdk.exceptions import CRMRequestError

logger = logging.getLogger(__name__)

# Status codes worth retrying when retries are explicitly enabled.
RETRYABLE_STATUS_CODES = frozenset({408, 425, 429, 500, 502, 503, 504})


class CRMClient:
    """Async transport client for the Twenty CRM REST API."""

    def __init__(
        self,
        config: Optional[CRMConfig] = None,
        *,
        max_attempts: int = 1,
    ) -> None:
        self.config = config or CRMConfig.from_settings()
        self.base_url = self.config.base_url
        self.headers = build_headers(self.config.api_key)
        self.max_attempts = max(1, int(max_attempts))
        logger.info(f"Initialized CRMClient with base URL: {self.base_url}")

    # -- URL generation -----------------------------------------------------
    def build_url(self, path: str) -> str:
        """Build a full REST URL from a relative path."""
        return f"{self.base_url}/{self.config.rest_prefix}/{path.lstrip('/')}"

    # -- Request execution --------------------------------------------------
    async def request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a REST request and return the parsed JSON body.

        Matches the original TwentyService._request semantics exactly.
        """
        url = self.build_url(path)
        logger.info(f"Twenty CRM Request: {method} {url}")

        attempt = 0
        while True:
            attempt += 1
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=json_data,
                        timeout=self.config.timeout,
                    )
                logger.info(f"Twenty CRM Response Status: {response.status_code}")

                if (
                    self.max_attempts > 1
                    and response.status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.max_attempts
                ):
                    await asyncio.sleep(attempt)
                    continue

                response.raise_for_status()

                if response.status_code == 204:
                    return {}
                return self._parse_json(response)

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Twenty CRM HTTP Error: {e.response.status_code} - {e.response.text}"
                )
                # Preserve the exact original message text.
                raise CRMRequestError(
                    f"Twenty CRM Error: {e.response.status_code} - {e.response.text}",
                    status_code=e.response.status_code,
                    response_text=e.response.text,
                    cause=e,
                )
            except CRMRequestError:
                raise
            except Exception as e:  # noqa: BLE001 - preserve original broad behavior
                logger.error(f"Twenty CRM Request Failed: {e}")
                raise CRMRequestError(
                    f"Failed to communicate with Twenty CRM: {e}",
                    cause=e,
                )

    # -- Response parsing ---------------------------------------------------
    @staticmethod
    def _parse_json(response: httpx.Response) -> Dict[str, Any]:
        """Parse a JSON response body (matches original ``response.json()``)."""
        return response.json()
