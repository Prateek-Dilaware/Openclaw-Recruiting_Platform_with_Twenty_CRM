"""CRM SDK — Evaluation aggregate module.

An Evaluation captures interviewer (or agent) feedback for an Application,
anchored to a specific Interview:

    Application ─▶ Interview ─▶ Evaluation

This module is the aggregate root for the Evaluation domain and communicates
with Twenty CRM exclusively through the shared :class:`CRMClient`.

Purpose
-------
Present one clean, domain-oriented API for evaluations (score, recommendation,
sentiment, strengths/weaknesses, summary, status) over the CRM transport.

Responsibilities (what this module DOES)
----------------------------------------
* Evaluation CRUD (``list`` / ``get`` / ``create`` / ``update`` / ``delete``).
* Single-field convenience wrappers over ``update`` (``approve`` / ``recommend``
  / ``hold`` / ``reject``).
* Evaluation-owned sub-resources (``add_note`` / ``add_attachment`` /
  ``add_timeline_activity``) via the shared internal :class:`SubResourceClient`.
* Transport delegation and response parsing.

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
No cross-aggregate coordination, workflow execution, application stage changes,
notifications, emails, AI, or OpenClaw. Those belong to higher layers::

    OpenClaw → Workflow Layer → CRM SDK (this module — the Evaluation aggregate)

Aggregate ownership
-------------------
The Evaluation aggregate owns the evaluation record — score, recommendation,
sentiment, summary, strengths, weaknesses, status — and its own
notes/attachments/timeline. Interviews, Applications, and Offers are separate
aggregates and are not coordinated here.

Field names follow Schema V2 (``scripts/schema_v2/schema_utils.py``): collection
``evaluations``; select fields ``recommendation`` (PROCEED/HOLD/REJECT) and
``evaluationStatus`` (DRAFT/FINAL).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient
from app.crm_sdk._subresources import SubResourceClient

logger = logging.getLogger(__name__)

# REST collection name (Schema V2).
_COLLECTION = "evaluations"

# Schema V2 evaluation.recommendation values.
RECOMMENDATION_PROCEED = "PROCEED"
RECOMMENDATION_HOLD = "HOLD"
RECOMMENDATION_REJECT = "REJECT"

# Schema V2 evaluation.evaluationStatus values.
STATUS_DRAFT = "DRAFT"
STATUS_FINAL = "FINAL"


class EvaluationModule:
    """Business operations for the Evaluation aggregate, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client
        # Evaluation-owned sub-resources linked via ``targetEvaluationId``.
        self._sub = SubResourceClient(client, "targetEvaluationId")

    # -- Core CRUD ----------------------------------------------------------
    async def list(self) -> List[Dict[str, Any]]:
        """List evaluations."""
        response = await self._client.request("GET", _COLLECTION)
        return response.get("data", {}).get("evaluations", [])

    async def get(self, evaluation_id: str) -> Dict[str, Any]:
        """Get a single evaluation."""
        response = await self._client.request("GET", f"{_COLLECTION}/{evaluation_id}")
        return response.get("data", {}).get("evaluation", {})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an evaluation."""
        response = await self._client.request("POST", _COLLECTION, data)
        return response.get("data", {}).get("createEvaluation", {})

    async def update(self, evaluation_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an evaluation."""
        response = await self._client.request("PATCH", f"{_COLLECTION}/{evaluation_id}", data)
        return response.get("data", {}).get("updateEvaluation", {})

    async def delete(self, evaluation_id: str) -> None:
        """Delete an evaluation."""
        await self._client.request("DELETE", f"{_COLLECTION}/{evaluation_id}")

    # -- Single-field convenience wrappers over update() --------------------
    async def approve(self, evaluation_id: str) -> Dict[str, Any]:
        """Finalize the evaluation (evaluationStatus = FINAL). Single-field PATCH, no workflow."""
        return await self.update(evaluation_id, {"evaluationStatus": STATUS_FINAL})

    async def recommend(self, evaluation_id: str) -> Dict[str, Any]:
        """Set recommendation = PROCEED. Single-field PATCH, no workflow."""
        return await self.update(evaluation_id, {"recommendation": RECOMMENDATION_PROCEED})

    async def hold(self, evaluation_id: str) -> Dict[str, Any]:
        """Set recommendation = HOLD. Single-field PATCH, no workflow."""
        return await self.update(evaluation_id, {"recommendation": RECOMMENDATION_HOLD})

    async def reject(self, evaluation_id: str) -> Dict[str, Any]:
        """Set recommendation = REJECT. Single-field PATCH, no workflow."""
        return await self.update(evaluation_id, {"recommendation": RECOMMENDATION_REJECT})

    # -- Evaluation-owned sub-resources (shared internal helper) ------------
    async def add_note(self, evaluation_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a note to an evaluation (create note, then link). Transport composition only."""
        return await self._sub.add_note(evaluation_id, title, content)

    async def link_note(self, note_id: str, evaluation_id: str) -> Dict[str, Any]:
        """Link an existing note to an evaluation."""
        return await self._sub.link_note(note_id, evaluation_id)

    async def add_attachment(self, evaluation_id: str, name: str, url: str) -> Dict[str, Any]:
        """Add an attachment to an evaluation."""
        return await self._sub.add_attachment(evaluation_id, name, url)

    async def add_timeline_activity(self, evaluation_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a timeline activity to an evaluation."""
        return await self._sub.add_timeline_activity(evaluation_id, title, content)
