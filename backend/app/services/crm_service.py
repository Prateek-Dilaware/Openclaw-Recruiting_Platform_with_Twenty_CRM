"""
CRM Service: direct Twenty CRM connection via TwentySkill.

Holds the working notes/workflow REST logic that will migrate into the CRM SDK
in a later phase. The obsolete OpenClaw-gateway routing path (USE_OPENCLAW /
OpenclawClient) was removed in Phase 1.1 — it targeted a non-existent
`/skills/{name}/execute` endpoint and never executed in production.
"""

import logging
from app.services.twenty_skill import TwentySkill
from app.services.twenty_service import TwentyService

logger = logging.getLogger(__name__)

class CRMService:
    def __init__(self):
        self.twenty_service = TwentyService()
        self.twenty_skill = TwentySkill()
        logger.info("CRMService initialized with TwentySkill (direct Twenty CRM connection)")

    async def write_field(self, object_name: str, record_id: str, field_name: str, value: any) -> dict:
        """Write a field directly to Twenty CRM."""
        return await self.twenty_skill.write_field(object_name, record_id, field_name, value)

    async def trigger_workflow(self, workflow_name_or_id: str, record_id: str, target_status: str, object_name: str = "candidate") -> dict:
        """Trigger a workflow status transition directly against Twenty CRM."""
        return await self.twenty_skill.trigger_workflow(workflow_name_or_id, record_id, target_status, object_name)
