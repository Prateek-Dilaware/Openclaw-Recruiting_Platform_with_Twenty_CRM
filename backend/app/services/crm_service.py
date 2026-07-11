"""
Fallback CRM Service that supports both direct Twenty CRM connection and OpenClaw execution.
"""

import logging
from app.settings import settings
from app.services.twenty_skill import TwentySkill
from app.services.twenty_service import TwentyService

logger = logging.getLogger(__name__)

class CRMService:
    def __init__(self):
        self.use_openclaw = getattr(settings, 'USE_OPENCLAW', False)
        self.twenty_service = TwentyService()
        
        if self.use_openclaw:
            from app.services.openclaw_client import OpenclawClient
            self.openclaw_client = OpenclawClient()
            logger.info("CRMService initialized with OpenClaw")
        else:
            self.twenty_skill = TwentySkill()
            logger.info("CRMService initialized with TwentySkill (direct fallback)")
    
    async def write_field(self, object_name: str, record_id: str, field_name: str, value: any) -> dict:
        """Write field using either OpenClaw or fallback direct connection"""
        if self.use_openclaw:
            return await self.openclaw_client.execute_skill("twenty_skill", {
                "action": "write_field",
                "object": object_name,
                "record_id": record_id,
                "field": field_name,
                "value": value
            })
        else:
            return await self.twenty_skill.write_field(object_name, record_id, field_name, value)
    
    async def trigger_workflow(self, workflow_name_or_id: str, record_id: str, target_status: str, object_name: str = "candidate") -> dict:
        """Trigger workflow transition using either OpenClaw or fallback direct connection"""
        if self.use_openclaw:
            return await self.openclaw_client.execute_skill("twenty_skill", {
                "action": "trigger_workflow",
                "workflow": workflow_name_or_id,
                "record_id": record_id,
                "target_status": target_status,
                "object": object_name
            })
        else:
            return await self.twenty_skill.trigger_workflow(workflow_name_or_id, record_id, target_status, object_name)
