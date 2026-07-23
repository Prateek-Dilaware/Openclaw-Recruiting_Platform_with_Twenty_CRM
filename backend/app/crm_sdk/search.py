"""CRM SDK — Search query service.

``SearchModule`` is **not a business aggregate** — it is a read-only query
service. It retrieves CRM records across the recruiting collections using the
shared :class:`CRMClient`. It owns no state and performs only reads.

Purpose
-------
Provide one consistent, query-oriented API for listing/filtering CRM records,
clearly distinct from the CRUD-oriented aggregate modules. The explicit
``search_*`` method names make it obvious these are QUERY operations (compare
``sdk.application.get(id)`` vs ``sdk.search.search_applications(filters=...)``).

Responsibilities (what this module DOES)
----------------------------------------
* Query each recruiting collection with consistent ``filters`` / ``limit`` /
  ``offset`` / ``sort_by`` / ``sort_order`` parameters.
* Deterministic CRM query construction (filter, pagination, sorting), request
  execution via :class:`CRMClient`, and response parsing.

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
* No writes: it never creates, updates, or deletes records.
* No semantic search, AI ranking, embeddings, vector search, recommendations,
  "best match"/"similar" logic. Those belong to OpenClaw / higher layers::

      OpenClaw → Workflow Layer → CRM SDK (this module — deterministic queries)

* It does not invent response formats. Results are returned in the same
  raw-list style the aggregate ``list``/``get`` methods use.

Query construction (Twenty REST conventions)
--------------------------------------------
* ``filters={"field": value}`` → ``filter=field[eq]:value`` (multiple joined by
  ``,``). Values are URL-encoded.
* ``sort_by`` + ``sort_order`` → ``orderBy=field[AscNullsLast|DescNullsLast]``.
* ``limit`` → ``limit=<n>``; ``offset`` → ``offset=<n>``.
Only deterministic CRM filtering is exposed — no ranking or scoring.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from app.crm_sdk.client import CRMClient

logger = logging.getLogger(__name__)

# Default pagination.
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0

# Map sort order to Twenty orderBy direction tokens.
_ORDER_TOKENS = {
    "asc": "AscNullsLast",
    "desc": "DescNullsLast",
}

# (collection, response_key) per aggregate. Requisition preserves the legacy
# misspelled collection/key to match the live schema (see requisition.py).
_CANDIDATES = ("candidates", "candidates")
_REQUISITIONS = ("requistions", "requistions")
_APPLICATIONS = ("applications", "applications")
_INTERVIEWS = ("interviews", "interviews")
_EVALUATIONS = ("evaluations", "evaluations")
_OFFERS = ("offers", "offers")


class SearchModule:
    """Read-only query service over the CRM collections."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client

    # -- Public query API (one per aggregate) -------------------------------
    async def search_candidates(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Query candidates."""
        return await self._search_collection(_CANDIDATES, filters, limit, offset, sort_by, sort_order)

    async def search_requisitions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Query requisitions."""
        return await self._search_collection(_REQUISITIONS, filters, limit, offset, sort_by, sort_order)

    async def search_applications(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Query applications."""
        return await self._search_collection(_APPLICATIONS, filters, limit, offset, sort_by, sort_order)

    async def search_interviews(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Query interviews."""
        return await self._search_collection(_INTERVIEWS, filters, limit, offset, sort_by, sort_order)

    async def search_evaluations(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Query evaluations."""
        return await self._search_collection(_EVALUATIONS, filters, limit, offset, sort_by, sort_order)

    async def search_offers(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """Query offers."""
        return await self._search_collection(_OFFERS, filters, limit, offset, sort_by, sort_order)

    # -- Internal query builder/executor ------------------------------------
    async def _search_collection(
        self,
        collection: tuple[str, str],
        filters: Optional[Dict[str, Any]],
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_order: str,
    ) -> List[Dict[str, Any]]:
        """Build a deterministic CRM query, execute it, and parse the results.

        Encapsulates filter construction, pagination, sorting, request execution,
        and response parsing so the public methods stay one-liners.
        """
        collection_name, response_key = collection
        query = self._build_query(filters, limit, offset, sort_by, sort_order)
        path = f"{collection_name}?{query}" if query else collection_name
        response = await self._client.request("GET", path)
        return response.get("data", {}).get(response_key, [])

    @staticmethod
    def _build_query(
        filters: Optional[Dict[str, Any]],
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_order: str,
    ) -> str:
        """Construct the URL query string from search parameters (deterministic)."""
        params: List[str] = []

        # Filters: {field: value} -> filter=field[eq]:value,... (Twenty convention)
        if filters:
            clauses = [f"{field}[eq]:{value}" for field, value in filters.items()]
            joined = ",".join(clauses)
            params.append(f"filter={quote(joined, safe='[]:,')}")

        # Sorting: orderBy=field[AscNullsLast|DescNullsLast]
        if sort_by:
            token = _ORDER_TOKENS.get(sort_order.lower(), _ORDER_TOKENS["asc"])
            params.append(f"orderBy={quote(sort_by, safe='')}[{token}]")

        # Pagination.
        params.append(f"limit={int(limit)}")
        params.append(f"offset={int(offset)}")

        return "&".join(params)
