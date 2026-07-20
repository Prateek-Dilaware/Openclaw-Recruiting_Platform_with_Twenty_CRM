"""CRM SDK — Application aggregate module.

Application is the **central business object** of the recruiting platform: it
links a Candidate to a Requisition and is the anchor for interviews, evaluation,
and offers.

    Candidate ─▶ Application ◀─ Requisition
                     │
                     ▼  (interviews → evaluations → offers hang off it)

This module is the aggregate root for the Application domain and communicates
with Twenty CRM exclusively through the shared :class:`CRMClient`.

Provenance note
---------------
Unlike Requisition/Candidate, there were **no Application methods in
``TwentyService``** to extract — the previous code predates the Schema V2
Application object. This module is therefore built on the *established SDK
pattern* (identical in shape to ``RequisitionModule``/``CandidateModule``) using
the Schema V2 collection/field names from ``scripts/schema_v2/schema_utils.py``
(collection ``applications``; select fields ``stage`` and
``decisionRecommendation``). No business/workflow logic is introduced — only
deterministic CRUD + single-field convenience wrappers. Because nothing existed
in ``TwentyService``, nothing is delegated from it (its public API is unchanged).

Purpose
-------
Present one clean domain API for the Application aggregate over the CRM transport.

Responsibilities (what this module DOES)
----------------------------------------
* Application CRUD (``list`` / ``get`` / ``create`` / ``update`` / ``delete``).
* Single-field convenience wrappers over ``update``:
  ``advance_stage`` / ``reject`` / ``hire`` / ``assign_recruiter``.
* Application-owned sub-resources: ``add_note`` / ``link_note`` /
  ``add_attachment`` / ``add_timeline_activity`` (transport composition only).
* Transport delegation to :class:`CRMClient` and response parsing.

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
No cross-aggregate coordination, workflow execution, approval routing,
notifications, emails, AI, or OpenClaw. Those belong to higher layers::

    OpenClaw → Workflow Layer → CRM SDK (this module — the Application aggregate)

Aggregate ownership
-------------------
The Application aggregate owns the application record, its stage/decision status,
and its notes/attachments/timeline. Interviews, Evaluations, and Offers are
**separate aggregates** (their own modules) and are NOT coordinated here.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient
from app.crm_sdk._subresources import SubResourceClient

logger = logging.getLogger(__name__)

# REST collection name (Schema V2).
_COLLECTION = "applications"

# Schema V2 application.stage values (see scripts/schema_v2/schema_utils.py).
STAGE_APPLIED = "APPLIED"
STAGE_SCREENING = "SCREENING"
STAGE_RECRUITER_REVIEW = "RECRUITER_REVIEW"
STAGE_INTERVIEW_SCHEDULING = "INTERVIEW_SCHEDULING"
STAGE_INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
STAGE_INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
STAGE_DECISION_PENDING = "DECISION_PENDING"
STAGE_OFFER = "OFFER"
STAGE_HIRED = "HIRED"
STAGE_REJECTED = "REJECTED"

# Schema V2 application.decisionRecommendation values.
DECISION_REJECT = "REJECT"


class ApplicationModule:
    """Business operations for the Application aggregate, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client
        # Application-owned sub-resources (notes/attachments/timeline) linked via
        # the ``targetApplicationId`` field. Internal helper hides transport.
        self._sub = SubResourceClient(client, "targetApplicationId")

    # -- Core CRUD ----------------------------------------------------------
    async def list(self) -> List[Dict[str, Any]]:
        """List applications."""
        response = await self._client.request("GET", _COLLECTION)
        return response.get("data", {}).get("applications", [])

    async def get(self, application_id: str) -> Dict[str, Any]:
        """Get a single application."""
        response = await self._client.request("GET", f"{_COLLECTION}/{application_id}")
        return response.get("data", {}).get("application", {})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an application."""
        response = await self._client.request("POST", _COLLECTION, data)
        return response.get("data", {}).get("createApplication", {})

    async def update(self, application_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an application."""
        response = await self._client.request("PATCH", f"{_COLLECTION}/{application_id}", data)
        return response.get("data", {}).get("updateApplication", {})

    async def delete(self, application_id: str) -> None:
        """Delete an application."""
        await self._client.request("DELETE", f"{_COLLECTION}/{application_id}")

    # -- Single-field convenience wrappers over update() --------------------
    async def advance_stage(self, application_id: str, stage: str) -> Dict[str, Any]:
        """Set the application ``stage``. Single-field PATCH, no workflow.

        ``stage`` must be a Schema V2 application.stage value (e.g.
        ``SCREENING``, ``INTERVIEW_SCHEDULED``, ``OFFER``). This is a plain field
        update — it does NOT trigger automation, notifications, or orchestration.
        """
        return await self.update(application_id, {"stage": stage})

    async def reject(self, application_id: str) -> Dict[str, Any]:
        """Set stage = REJECTED (and decisionRecommendation = REJECT). Single PATCH, no workflow.

        Does NOT send notifications, cancel interviews, or invoke any process.
        """
        return await self.update(
            application_id,
            {"stage": STAGE_REJECTED, "decisionRecommendation": DECISION_REJECT},
        )

    async def hire(self, application_id: str) -> Dict[str, Any]:
        """Set stage = HIRED. Single-field PATCH, no workflow/onboarding."""
        return await self.update(application_id, {"stage": STAGE_HIRED})

    async def assign_recruiter(self, application_id: str, recruiter_id: str) -> Dict[str, Any]:
        """Assign the recruiter relation. Single-field PATCH, no workflow.

        Writes the ``recruiterId`` relation field only; no notifications.
        """
        return await self.update(application_id, {"recruiterId": recruiter_id})

    # -- Application-owned sub-resources (delegated to internal helper) -----
    # Hide CRM transport complexity (notes/attachments/timeline) behind the
    # aggregate, linked via targetApplicationId.
    async def link_note(self, note_id: str, application_id: str) -> Dict[str, Any]:
        """Link an existing note to an application."""
        return await self._sub.link_note(note_id, application_id)

    async def add_note(self, application_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a note to an application (create note, then link). Transport composition only."""
        return await self._sub.add_note(application_id, title, content)

    async def add_attachment(self, application_id: str, name: str, url: str) -> Dict[str, Any]:
        """Add an attachment to an application."""
        return await self._sub.add_attachment(application_id, name, url)

    async def add_timeline_activity(self, application_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a timeline activity to an application."""
        return await self._sub.add_timeline_activity(application_id, title, content)
