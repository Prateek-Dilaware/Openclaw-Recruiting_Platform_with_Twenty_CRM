"""CRM SDK — Candidate aggregate module.

This module is the **aggregate root for the Candidate domain**. CRM SDK modules
are organized around domain aggregates, not around individual database tables.

The Candidate aggregate owns:
  * the candidate record,
  * candidate notes,
  * candidate attachments,
  * candidate timeline activities,
  * candidate resume (an attachment).

Internally these require several Twenty REST entities (``candidates``, ``notes``,
``noteTargets``, ``attachments``, ``timelineActivities``). That transport
complexity is **hidden** behind a single, domain-oriented API — the whole point
of the SDK. All communication goes through the shared :class:`CRMClient`; no
transport code is duplicated.

Purpose
-------
Present one clean domain API for everything that belongs to a candidate, while
abstracting away which CRM entities/endpoints are used under the hood.

Responsibilities (what this module DOES)
----------------------------------------
* Candidate CRUD (``list`` / ``get`` / ``create`` / ``update`` / ``delete``).
* Entity-local payload normalization (raw ``email`` / ``phone`` string → Twenty
  structured field shape on create/update).
* Candidate-owned sub-resources: notes (``add_note`` / ``link_note``),
  attachments (``add_attachment``), timeline (``add_timeline_activity``).
* Transport delegation to :class:`CRMClient` and response parsing.

Acceptable internal composition
--------------------------------
Hiding CRM transport complexity is allowed and encouraged. For example,
``add_note`` internally performs ``create_note`` (POST ``notes``) followed by
``link_note`` (POST ``noteTargets``). This is transport composition within a
single aggregate — **not** business-workflow orchestration.

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
This module never coordinates across *other* aggregates. It does NOT schedule
interviews, create applications, generate offers, execute workflows, send
notifications/emails, perform AI reasoning, or invoke OpenClaw. Those cross-
aggregate concerns belong to higher layers::

    OpenClaw
          ↓
    Workflow Layer
          ↓
    CRM SDK  (this module — the Candidate aggregate)

Behavior-preservation notes
---------------------------
Every operation reproduces the original ``TwentyService`` methods EXACTLY:
  * candidate CRUD: collection ``candidates``; keys ``candidate`` / ``candidates``
    / ``createCandidate`` / ``updateCandidate``; inline email/phone shaping;
    fallbacks ``[]`` / ``{}`` / ``None``.
  * notes: POST ``notes`` (BlockNote ``bodyV2`` body), key ``createNote``; link via
    POST ``noteTargets`` with ``{noteId, targetCandidateId}``, key ``createNoteTarget``.
  * attachments: POST ``attachments`` with ``{name, fullPath, file, targetCandidateId,
    fileCategory: "OTHER"}``, key ``createAttachment``.
  * timeline: POST ``timelineActivities`` with ``{name, properties.details,
    targetCandidateId}``, key ``createTimelineActivity``.

No convenience *lifecycle* wrappers (archive/restore/etc.) were added — the
Candidate entity has no single-field status to wrap, and none were invented.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient
from app.crm_sdk._subresources import SubResourceClient

logger = logging.getLogger(__name__)

# REST collection name.
_COLLECTION = "candidates"


class CandidateModule:
    """Business operations for the Candidate entity, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client
        # Candidate-owned sub-resources (notes/attachments/timeline) linked via
        # the ``targetCandidateId`` field. Internal helper hides transport.
        self._sub = SubResourceClient(client, "targetCandidateId")

    # -- Core CRUD (extracted verbatim) -------------------------------------
    async def list(self) -> List[Dict[str, Any]]:
        """List candidates. (was TwentyService.get_candidates)"""
        response = await self._client.request("GET", _COLLECTION)
        return response.get("data", {}).get("candidates", [])

    async def get(self, candidate_id: str) -> Dict[str, Any]:
        """Get a single candidate. (was TwentyService.get_candidate)"""
        response = await self._client.request("GET", f"{_COLLECTION}/{candidate_id}")
        return response.get("data", {}).get("candidate", {})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a candidate. (was TwentyService.create_candidate)

        Preserves the original inline shaping that converts a raw ``email`` /
        ``phone`` string into Twenty's structured field format.
        """
        # Formulate phone/email if raw strings are provided
        payload = data.copy()
        if "email" in payload and isinstance(payload["email"], str):
            payload["email"] = {
                "primaryEmail": payload["email"],
                "additionalEmails": []
            }
        if "phone" in payload and isinstance(payload["phone"], str):
            payload["phone"] = {
                "primaryPhoneNumber": payload["phone"],
                "primaryPhoneCountryCode": "",
                "primaryPhoneCallingCode": "",
                "additionalPhones": []
            }
        response = await self._client.request("POST", _COLLECTION, payload)
        return response.get("data", {}).get("createCandidate", {})

    async def update(self, candidate_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a candidate. (was TwentyService.update_candidate)

        Preserves the original inline shaping that converts a raw ``email`` /
        ``phone`` string into Twenty's structured field format.
        """
        payload = data.copy()
        if "email" in payload and isinstance(payload["email"], str):
            payload["email"] = {
                "primaryEmail": payload["email"],
                "additionalEmails": []
            }
        if "phone" in payload and isinstance(payload["phone"], str):
            payload["phone"] = {
                "primaryPhoneNumber": payload["phone"],
                "primaryPhoneCountryCode": "",
                "primaryPhoneCallingCode": "",
                "additionalPhones": []
            }
        response = await self._client.request("PATCH", f"{_COLLECTION}/{candidate_id}", payload)
        return response.get("data", {}).get("updateCandidate", {})

    async def delete(self, candidate_id: str) -> None:
        """Delete a candidate. (was TwentyService.delete_candidate)"""
        await self._client.request("DELETE", f"{_COLLECTION}/{candidate_id}")

    # -- Candidate-owned sub-resources (delegated to internal helper) -------
    # These hide CRM transport complexity (notes/attachments/timeline) behind the
    # aggregate. Behavior is identical to the previous inline implementation.
    async def link_note(self, note_id: str, candidate_id: str) -> Dict[str, Any]:
        """Link an existing note to a candidate. (was TwentyService.link_note_to_candidate)"""
        return await self._sub.link_note(note_id, candidate_id)

    async def add_note(self, candidate_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a note to a candidate (create note, then link). Transport composition only."""
        return await self._sub.add_note(candidate_id, title, content)

    async def add_attachment(self, candidate_id: str, name: str, url: str) -> Dict[str, Any]:
        """Add an attachment (e.g. resume) to a candidate."""
        return await self._sub.add_attachment(candidate_id, name, url)

    async def add_timeline_activity(self, candidate_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a timeline activity to a candidate."""
        return await self._sub.add_timeline_activity(candidate_id, title, content)
