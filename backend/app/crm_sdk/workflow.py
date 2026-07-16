"""CRM SDK — Workflow module (thin transport wrapper).

This module is **not** a business aggregate and **not** a workflow engine. It is a
thin transport wrapper over the Workflow APIs that Twenty CRM actually exposes
via its REST record interface. It reads workflow definitions and workflow runs,
and triggers a run by creating a ``workflowRuns`` record. It performs no
orchestration and no business logic.

Three distinct workflow layers (important for future contributors)
------------------------------------------------------------------
1. **Twenty CRM Workflows** — workflow *definitions* stored in Twenty, seeded as
   draft records by ``scripts/schema_v2/05_create_workflows.py`` (the four
   "Recruiting V2 - …" workflows). Authoring/steps are GraphQL-only and are
   configured/published inside Twenty, not here.
2. **CRM SDK Workflow Module (THIS FILE)** — a transport abstraction over
   Twenty's workflow REST endpoints. It lists/gets definitions, triggers runs,
   and reads run status/history. Nothing more.
3. **OpenClaw Recruiting Workflow** — AI orchestration across multiple SDK
   aggregates. That lives in a higher layer, not here.

Purpose
-------
Expose exactly the workflow operations Twenty CRM supports over REST, using the
shared :class:`CRMClient`.

Responsibilities (what this module DOES)
----------------------------------------
* ``list`` / ``get`` workflow definitions (``workflows`` collection).
* ``trigger`` a workflow run (creates a ``workflowRuns`` record).
* ``status`` of a single run and ``history`` of runs (``workflowRuns`` collection).

NOT responsibilities (what this module intentionally does NOT do)
-----------------------------------------------------------------
No hiring/interview/offer/recruiter workflow logic, no business orchestration,
multi-step processes, AI, notifications, email, calendar, or OpenClaw. Those
belong to higher layers::

    OpenClaw → Workflow Layer → CRM SDK (this module — Twenty workflow transport)

Supported-operations note
--------------------------
Only operations evidenced by the codebase/Twenty REST are implemented:
``list`` / ``get`` (workflows), ``trigger`` (POST ``workflowRuns`` with
``workflowId`` / ``workflowVersionId`` / ``name`` / ``state``), and
``status`` / ``history`` (``workflowRuns`` record reads). A **``cancel``**
operation is intentionally **omitted**: Twenty exposes no run-cancel REST
endpoint in this codebase, and inventing one is out of scope.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.crm_sdk.client import CRMClient

logger = logging.getLogger(__name__)

# REST collections.
_WORKFLOWS = "workflows"
_WORKFLOW_RUNS = "workflowRuns"


class WorkflowModule:
    """Thin transport wrapper over Twenty CRM workflow REST APIs."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client

    # -- Workflow definitions -----------------------------------------------
    async def list(self) -> List[Dict[str, Any]]:
        """List workflow definitions. GET ``workflows`` → ``data.workflows``."""
        response = await self._client.request("GET", _WORKFLOWS)
        return response.get("data", {}).get("workflows", [])

    async def get(self, workflow_id: str) -> Dict[str, Any]:
        """Get a single workflow definition. GET ``workflows/{id}`` → ``data.workflow``."""
        response = await self._client.request("GET", f"{_WORKFLOWS}/{workflow_id}")
        return response.get("data", {}).get("workflow", {})

    # -- Workflow runs ------------------------------------------------------
    async def trigger(
        self,
        workflow_id: str,
        workflow_version_id: str,
        name: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Trigger a workflow run by creating a ``workflowRuns`` record.

        Mirrors the payload shape Twenty expects (``workflowId`` /
        ``workflowVersionId`` / ``name`` / ``state``). This starts a run; it does
        NOT orchestrate business steps — Twenty executes the configured workflow.
        """
        payload: Dict[str, Any] = {
            "workflowId": workflow_id,
            "workflowVersionId": workflow_version_id,
            "name": name,
            "state": state or {},
        }
        response = await self._client.request("POST", _WORKFLOW_RUNS, payload)
        return response.get("data", {}).get("createWorkflowRun", response)

    async def status(self, run_id: str) -> Dict[str, Any]:
        """Get a single workflow run (its status/error). GET ``workflowRuns/{id}``."""
        response = await self._client.request("GET", f"{_WORKFLOW_RUNS}/{run_id}")
        return response.get("data", {}).get("workflowRun", {})

    async def history(self) -> List[Dict[str, Any]]:
        """List workflow runs. GET ``workflowRuns`` → ``data.workflowRuns``."""
        response = await self._client.request("GET", _WORKFLOW_RUNS)
        return response.get("data", {}).get("workflowRuns", [])
