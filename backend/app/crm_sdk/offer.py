"""CRM SDK — Offer aggregate module.

An Offer is the hiring offer produced from a successful Application:

    Application ─▶ Offer

This module is the aggregate root for the Offer domain and communicates with
Twenty CRM exclusively through the shared :class:`CRMClient`.

Purpose
-------
Present one clean, domain-oriented API for offers (salary, currency, dates,
terms, status) over the CRM transport.

Responsibilities (what this module DOES)
----------------------------------------
* Offer CRUD (``list`` / ``get`` / ``create`` / ``update`` / ``delete``).
* Single-field status wrappers over ``update`` (``approve`` / ``send`` /
  ``accept`` / ``decline`` / ``withdraw``).
* Offer-owned sub-resources (``add_note`` / ``add_attachment`` /
  ``add_timeline_activity``) via the shared internal :class:`SubResourceClient`.
* Transport delegation and response parsing.

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
The status wrappers are **data operations only**. This module does NOT send
emails, generate PDFs/documents, notify candidates, execute workflows, or invoke
OpenClaw. Those belong to higher layers::

    OpenClaw → Workflow Layer → CRM SDK (this module — the Offer aggregate)

Aggregate ownership
-------------------
The Offer aggregate owns the offer record — salary, currency, start/expiry dates,
terms, status — and its own notes/attachments (e.g. offer documents) and
timeline. Applications, Interviews, and Evaluations are separate aggregates and
are not coordinated here.

Field names follow Schema V2 (``scripts/schema_v2/schema_utils.py``): collection
``offers``; select field ``offerStatus`` (DRAFT/APPROVED/SENT/ACCEPTED/DECLINED).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient
from app.crm_sdk._subresources import SubResourceClient

logger = logging.getLogger(__name__)

# REST collection name (Schema V2).
_COLLECTION = "offers"

# Schema V2 offer.offerStatus values.
STATUS_DRAFT = "DRAFT"
STATUS_APPROVED = "APPROVED"
STATUS_SENT = "SENT"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_DECLINED = "DECLINED"


class OfferModule:
    """Business operations for the Offer aggregate, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client
        # Offer-owned sub-resources linked via ``targetOfferId``.
        self._sub = SubResourceClient(client, "targetOfferId")

    # -- Core CRUD ----------------------------------------------------------
    async def list(self) -> List[Dict[str, Any]]:
        """List offers."""
        response = await self._client.request("GET", _COLLECTION)
        return response.get("data", {}).get("offers", [])

    async def get(self, offer_id: str) -> Dict[str, Any]:
        """Get a single offer."""
        response = await self._client.request("GET", f"{_COLLECTION}/{offer_id}")
        return response.get("data", {}).get("offer", {})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an offer."""
        response = await self._client.request("POST", _COLLECTION, data)
        return response.get("data", {}).get("createOffer", {})

    async def update(self, offer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an offer."""
        response = await self._client.request("PATCH", f"{_COLLECTION}/{offer_id}", data)
        return response.get("data", {}).get("updateOffer", {})

    async def delete(self, offer_id: str) -> None:
        """Delete an offer."""
        await self._client.request("DELETE", f"{_COLLECTION}/{offer_id}")

    # -- Single-field status wrappers over update() -------------------------
    async def approve(self, offer_id: str) -> Dict[str, Any]:
        """Set offerStatus = APPROVED. Single-field PATCH — data only, no workflow."""
        return await self.update(offer_id, {"offerStatus": STATUS_APPROVED})

    async def send(self, offer_id: str) -> Dict[str, Any]:
        """Set offerStatus = SENT. Single-field PATCH — data only.

        Does NOT send emails, generate PDFs, or notify the candidate.
        """
        return await self.update(offer_id, {"offerStatus": STATUS_SENT})

    async def accept(self, offer_id: str) -> Dict[str, Any]:
        """Set offerStatus = ACCEPTED. Single-field PATCH — data only, no workflow."""
        return await self.update(offer_id, {"offerStatus": STATUS_ACCEPTED})

    async def decline(self, offer_id: str) -> Dict[str, Any]:
        """Set offerStatus = DECLINED. Single-field PATCH — data only, no notifications."""
        return await self.update(offer_id, {"offerStatus": STATUS_DECLINED})

    async def withdraw(self, offer_id: str) -> Dict[str, Any]:
        """Withdraw an offer by reverting offerStatus to DRAFT. Single-field PATCH.

        NOTE: Schema V2 has no dedicated ``WITHDRAWN`` value for ``offerStatus``
        (allowed: DRAFT/APPROVED/SENT/ACCEPTED/DECLINED). This wrapper therefore
        reverts the status to ``DRAFT``. If a ``WITHDRAWN`` state is added to the
        schema later, update this single line. No orchestration/notifications.
        """
        return await self.update(offer_id, {"offerStatus": STATUS_DRAFT})

    # -- Offer-owned sub-resources (shared internal helper) -----------------
    async def add_note(self, offer_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a note to an offer (create note, then link). Transport composition only."""
        return await self._sub.add_note(offer_id, title, content)

    async def link_note(self, note_id: str, offer_id: str) -> Dict[str, Any]:
        """Link an existing note to an offer."""
        return await self._sub.link_note(note_id, offer_id)

    async def add_attachment(self, offer_id: str, name: str, url: str) -> Dict[str, Any]:
        """Add an attachment (e.g. offer document) to an offer."""
        return await self._sub.add_attachment(offer_id, name, url)

    async def add_timeline_activity(self, offer_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a timeline activity to an offer."""
        return await self._sub.add_timeline_activity(offer_id, title, content)
