import logging
import httpx
from typing import Dict, Any, Optional
from app.settings import settings
from app.services.twenty_service import TwentyService

logger = logging.getLogger(__name__)

class TwentySkill:
    def __init__(self):
        self.twenty_service = TwentyService()
        self.base_url = settings.TWENTY_API_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.TWENTY_API_KEY}",
            "Content-Type": "application/json"
        }
        logger.info("TwentySkill initialized.")

    def _normalize_object_name(self, object_name: str) -> str:
        """Helper to ensure pluralized object endpoints are correct."""
        name = object_name.lower().strip()
        if name == "candidate":
            return "candidates"
        elif name == "requistion" or name == "requisition":
            return "requistions"  # CRM uses requistions spelling
        elif name == "interview":
            return "interviews"
        elif name == "note":
            return "notes"
        elif name == "attachment":
            return "attachments"
        elif name == "timelineactivity" or name == "timeline_activity":
            return "timelineActivities"
        return name

    async def write_field(self, object_name: str, record_id: str, field_name: str, value: Any) -> Dict[str, Any]:
        """
        Direct writes for non-state-changing data (notes, transcripts, scores, etc.).
        If field_name is 'note', it creates a note record linked to the record.
        """
        plural_obj = self._normalize_object_name(object_name)
        logger.info(f"TwentySkill.write_field: writing to {plural_obj}/{record_id}, field={field_name}")

        # Handle notes separately as they are distinct objects in Twenty CRM
        if field_name.lower() in ("note", "notes"):
            title = "Agent Update Note"
            content = str(value)
            if isinstance(value, dict):
                title = value.get("title", title)
                content = value.get("content", content)

            if plural_obj == "candidates":
                return await self.twenty_service.add_note_to_candidate(record_id, title, content)
            else:
                # General note creation and linking
                note = await self.twenty_service.create_note(title, content)
                note_id = note.get("id")
                # Link note to target object
                payload = {
                    "noteId": note_id,
                    f"target{object_name.capitalize()}Id": record_id
                }
                async with httpx.AsyncClient() as client:
                    res = await client.post(f"{self.base_url}/rest/noteTargets", headers=self.headers, json=payload)
                    res.raise_for_status()
                return note

        # Format phone/email structures if raw string is provided
        payload = {}
        if field_name == "email" and isinstance(value, str):
            payload["email"] = {
                "primaryEmail": value,
                "additionalEmails": []
            }
        elif field_name == "phone" and isinstance(value, str):
            payload["phone"] = {
                "primaryPhoneNumber": value,
                "primaryPhoneCountryCode": "",
                "primaryPhoneCallingCode": "",
                "additionalPhones": []
            }
        else:
            payload[field_name] = value

        # Send PATCH request for direct mutation
        url = f"{self.base_url}/rest/{plural_obj}/{record_id}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method="PATCH",
                    url=url,
                    headers=self.headers,
                    json=payload,
                    timeout=15.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully mutated field '{field_name}' on {plural_obj}/{record_id}.")
                return result.get("data", {}).get(f"update{object_name.capitalize()}", result)
            except Exception as e:
                logger.error(f"Failed to write field to CRM: {e}")
                raise Exception(f"Twenty Skill write_field error: {e}")

    async def trigger_workflow(self, workflow_name_or_id: str, record_id: str, target_status: str, object_name: str = "candidate") -> Dict[str, Any]:
        """
        Transition status/stage through a Twenty workflow.
        If workflow execution fails or is not found, falls back to direct mutation and logs a warning.
        """
        logger.info(f"TwentySkill.trigger_workflow: workflow={workflow_name_or_id}, record={record_id}, target_status={target_status}")

        plural_obj = self._normalize_object_name(object_name)
        workflow_id = None
        version_id = None

        # 1. Search for matching workflow
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/rest/workflows", headers=self.headers)
                res.raise_for_status()
                workflows = res.json().get("data", {}).get("workflows", [])
                
                # Check by name or ID
                for wf in workflows:
                    if wf.get("id") == workflow_name_or_id or wf.get("name") == workflow_name_or_id:
                        workflow_id = wf.get("id")
                        version_id = wf.get("lastPublishedVersionId")
                        break
        except Exception as e:
            logger.warning(f"Error querying workflows in Twenty: {e}")

        # 2. Trigger workflow if found
        if workflow_id and version_id:
            try:
                payload = {
                    "workflowId": workflow_id,
                    "workflowVersionId": version_id,
                    "name": f"Workflow run triggered by agent for candidate {record_id}",
                    "state": {
                        "recordId": record_id,
                        "targetStatus": target_status,
                        "objectName": object_name
                    }
                }
                async with httpx.AsyncClient() as client:
                    run_res = await client.post(f"{self.base_url}/rest/workflowRuns", headers=self.headers, json=payload)
                    run_res.raise_for_status()
                    run_data = run_res.json()
                    logger.info(f"Successfully triggered workflow run: {run_data.get('id') or 'ID unknown'}")
                    
                    # Check if there is an error in execution (like logic function transpilation error)
                    if run_data.get("workflowRunError"):
                        logger.warning(f"Workflow ran but reported error: {run_data.get('workflowRunError')}. Bypassing to direct mutation.")
                        raise Exception("Workflow runner internal error")
                        
                    return run_data
            except Exception as wf_err:
                logger.error(f"Triggering workflow via CRM runner failed: {wf_err}. Falling back to direct mutation.")

        # 3. Direct mutation fallback (if workflow runner is disabled or missing)
        logger.warning(f"Workflow '{workflow_name_or_id}' bypassed. Mutating status directly to '{target_status}'.")
        
        # Decide field name based on object_name
        status_field = "interviewStatus" if object_name.lower() == "candidate" else "status"
        
        # Run direct PATCH update
        direct_update = await self.write_field(object_name, record_id, status_field, target_status)
        
        # Log to timeline activity for accountability and audit trailing
        activity_title = f"Status Transition to {target_status}"
        activity_desc = f"Transitioned candidate stage to {target_status} (Agent Workflow Simulation)."
        await self.twenty_service.add_timeline_activity_to_candidate(
            candidate_id=record_id,
            title=activity_title,
            content=activity_desc
        )
        
        return {
            "status": "success",
            "message": f"Direct mutation performed for stage transition.",
            "workflow_bypassed": True,
            "data": direct_update
        }
