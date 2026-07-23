"""CRM SDK — Requisition module.

This module encapsulates **Requisition business operations** for the CRM SDK. It
provides standard CRUD operations plus a few lightweight, domain-oriented
convenience methods, and communicates with Twenty CRM exclusively through the
shared :class:`CRMClient` transport layer.

Purpose
-------
Provide a clean, domain-oriented API over the CRM transport layer — nothing more.

Responsibilities (what this module DOES)
----------------------------------------
* Requisition entity CRUD (``list`` / ``get`` / ``create`` / ``update`` / ``delete``).
* Domain-oriented convenience methods (``approve`` / ``publish`` / ``close``) that
  simply set a status field.
* Transport delegation to :class:`CRMClient`.
* Response parsing (unwrapping the CRM data envelope).

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
This module deliberately contains **no workflow orchestration**. Approval
routing, notifications, scheduling, email, AI reasoning, OpenClaw execution,
automation, and any multi-step business workflow belong to **higher
architectural layers**::

    OpenClaw
          ↓
    Workflow Layer
          ↓
    CRM SDK  (this module)

Behavior-preservation notes
---------------------------
The five core operations reproduce the original ``TwentyService`` methods
EXACTLY, including:
  * the misspelled REST collection name ``requistions`` (live V1 wire format),
  * the misspelled response keys ``requistion`` / ``createRequistion`` /
    ``updateRequistion``,
  * the same default fallbacks (``[]`` / ``{}`` / ``None``).

The spelling is intentionally left untouched here — renaming it is a separate,
explicitly-scoped future task (see TWENTY_SKILL_V2_AUDIT.md), not part of this
module.

The ``approve`` / ``publish`` / ``close`` helpers are thin wrappers over
``update`` that PATCH the Schema V2 ``requisitionStatus`` field only. They are
convenience shortcuts, **not** workflow implementations (see each method's
docstring for the explicit list of things they do NOT do). All HTTP transport
goes through the shared :class:`CRMClient`; no transport code is duplicated.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient

logger = logging.getLogger(__name__)

# REST collection name. Preserved misspelling to match the live Twenty schema.
_COLLECTION = "requistions"

# Schema V2 requisitionStatus values (see scripts/schema_v2/schema_utils.py).
STATUS_APPROVED = "APPROVED"
STATUS_POSTED = "POSTED"
STATUS_CLOSED = "CLOSED"


class RequisitionModule:
    """Business operations for the Requisition entity, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client

    # -- Core CRUD (extracted verbatim) -------------------------------------
    async def list(self) -> List[Dict[str, Any]]:
        """List requisitions. (was TwentyService.get_requisitions)"""
        response = await self._client.request("GET", _COLLECTION)
        return response.get("data", {}).get("requistions", [])

    async def get(self, requisition_id: str) -> Dict[str, Any]:
        """Get a single requisition. (was TwentyService.get_requisition)"""
        response = await self._client.request("GET", f"{_COLLECTION}/{requisition_id}")
        return response.get("data", {}).get("requistion", {})

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a requisition. (was TwentyService.create_requisition)"""
        response = await self._client.request("POST", _COLLECTION, data)
        return response.get("data", {}).get("createRequistion", {})

    async def update(self, requisition_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a requisition. (was TwentyService.update_requisition)"""
        response = await self._client.request("PATCH", f"{_COLLECTION}/{requisition_id}", data)
        return response.get("data", {}).get("updateRequistion", {})

    async def delete(self, requisition_id: str) -> None:
        """Delete a requisition. (was TwentyService.delete_requisition)"""
        await self._client.request("DELETE", f"{_COLLECTION}/{requisition_id}")

    # -- Lifecycle status helpers (thin wrappers over update) ---------------
    async def approve(self, requisition_id: str) -> Dict[str, Any]:
        """Convenience wrapper that marks a requisition as approved.

        This is ONLY a convenience wrapper. It:
          * internally delegates to :meth:`update`,
          * patches the ``requisitionStatus`` field to ``APPROVED``.

        It explicitly does NOT:
          * execute approval workflows,
          * perform authorization,
          * trigger automation,
          * send notifications,
          * invoke OpenClaw,
          * perform any business orchestration.

        Those responsibilities belong to higher architectural layers.
        """
        return await self.update(requisition_id, {"requisitionStatus": STATUS_APPROVED})

    async def publish(self, requisition_id: str) -> Dict[str, Any]:
        """Convenience wrapper that marks a requisition as published (POSTED).

        This is ONLY a convenience wrapper. It:
          * internally delegates to :meth:`update`,
          * updates the ``requisitionStatus`` field to ``POSTED``.

        It explicitly does NOT:
          * publish to external job boards,
          * send notifications,
          * execute workflow logic,
          * invoke AI,
          * perform any orchestration.

        Those responsibilities belong to higher architectural layers.
        """
        return await self.update(requisition_id, {"requisitionStatus": STATUS_POSTED})

    async def close(self, requisition_id: str) -> Dict[str, Any]:
        """Convenience wrapper that marks a requisition as closed.

        This is ONLY a convenience wrapper. It:
          * internally delegates to :meth:`update`,
          * updates the ``requisitionStatus`` field to ``CLOSED``.

        It explicitly does NOT:
          * reject candidates,
          * cancel interviews,
          * archive data,
          * trigger workflow automation,
          * invoke OpenClaw.

        Those responsibilities belong to higher architectural layers.
        """
        return await self.update(requisition_id, {"requisitionStatus": STATUS_CLOSED})
