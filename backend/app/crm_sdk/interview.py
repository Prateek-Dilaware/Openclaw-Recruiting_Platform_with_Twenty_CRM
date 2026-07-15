"""CRM SDK — Interview aggregate module.

This module is the aggregate root for the Interview domain. An Interview belongs
to an Application (see the Application aggregate) and is the anchor for its
Evaluation (a separate aggregate). It communicates with Twenty CRM exclusively
through the shared :class:`CRMClient`.

Purpose
-------
Present one clean domain API for the Interview aggregate over the CRM transport.

Responsibilities (what this module DOES)
----------------------------------------
* Interview CRUD (``list`` / ``get`` / ``create`` / ``update`` / ``delete``).
* Single-field status convenience wrappers over ``update``:
  ``schedule`` / ``reschedule`` / ``cancel`` / ``complete``.
* Transport delegation to :class:`CRMClient` and response parsing.

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
Interview scheduling here is a **data operation only**. It does NOT send emails,
invoke calendars, notify candidates, execute workflows, or invoke OpenClaw — all
cross-aggregate/process concerns belong to higher layers::

    OpenClaw → Workflow Layer → CRM SDK (this module — the Interview aggregate)

Aggregate ownership
-------------------
The Interview aggregate owns the interview record and its status/scheduling
fields. Applications, Evaluations, and Offers are separate aggregates and are not
coordinated here.

Behavior-preservation notes
---------------------------
``list`` / ``get`` / ``create`` / ``delete`` reproduce the original
``TwentyService`` interview methods EXACTLY (collection ``interviews``; keys
``interview`` / ``interviews`` / ``createInterview``; fallbacks ``[]`` / ``{}`` /
``None``).

``update`` and the status wrappers are additive: the original ``TwentyService``
had no ``update_interview``. ``update`` follows the exact same PATCH shape used by
the other modules (``PATCH interviews/{id}`` → key ``updateInterview``). The
status wrappers set the Schema V2 ``interviewStatus`` field only.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient

logger = logging.getLogger(__name__)

# REST collection name.
_COLLECTION = "interviews"

# Schema V2 interview.interviewStatus values (see scripts/schema_v2/schema_utils.py).
STATUS_DRAFT = "DRAFT"
STATUS_SCHEDULED = "SCHEDULED"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_COMPLETED = "COMPLETED"
STATUS_CANCELLED = "CANCELLED"


class InterviewModule:
    """Business operations for the Interview aggregate, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client

    # -- Core CRUD (list/get/create/delete extracted verbatim) --------------
    async def list(self) -> List[Dict[str, Any]]:
        """List interviews. (was TwentyService.get_interviews)"""
        response = await self._client.request("GET", _COLLECTION)
        return response.get("data", {}).get("interviews", [])

    async def get(self, interview_id: str) -> Dict[str, Any]:
        """Get a single interview. (was TwentyService.get_interview)"""
        response = await self._client.request("GET", f"{_COLLECTION}/{interview_id}")
        return response.get("data", {}).get("interview", {})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an interview. (was TwentyService.create_interview)"""
        response = await self._client.request("POST", _COLLECTION, data)
        return response.get("data", {}).get("createInterview", {})

    async def update(self, interview_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an interview.

        Additive (no ``update_interview`` existed in TwentyService). Follows the
        same PATCH shape as the other modules.
        """
        response = await self._client.request("PATCH", f"{_COLLECTION}/{interview_id}", data)
        return response.get("data", {}).get("updateInterview", {})

    async def delete(self, interview_id: str) -> None:
        """Delete an interview. (was TwentyService.delete_interview)"""
        await self._client.request("DELETE", f"{_COLLECTION}/{interview_id}")

    # -- Single-field status wrappers over update() -------------------------
    async def schedule(self, interview_id: str) -> Dict[str, Any]:
        """Set interviewStatus = SCHEDULED. Single-field PATCH — data only.

        Does NOT send emails, invoke calendars, notify anyone, or run workflows.
        """
        return await self.update(interview_id, {"interviewStatus": STATUS_SCHEDULED})

    async def reschedule(self, interview_id: str, scheduled_at: str) -> Dict[str, Any]:
        """Update ``scheduledAt`` and set status = SCHEDULED. Single PATCH — data only.

        Does NOT send emails, invoke calendars, or notify anyone.
        """
        return await self.update(
            interview_id,
            {"scheduledAt": scheduled_at, "interviewStatus": STATUS_SCHEDULED},
        )

    async def cancel(self, interview_id: str) -> Dict[str, Any]:
        """Set interviewStatus = CANCELLED. Single-field PATCH — data only, no notifications."""
        return await self.update(interview_id, {"interviewStatus": STATUS_CANCELLED})

    async def complete(self, interview_id: str) -> Dict[str, Any]:
        """Set interviewStatus = COMPLETED. Single-field PATCH — data only."""
        return await self.update(interview_id, {"interviewStatus": STATUS_COMPLETED})
