"""
OpenClaw Twenty CRM Skill
Provides standardized interface for Twenty CRM operations
"""
 
import httpx
from typing import Dict, Any, Optional
import logging
 
logger = logging.getLogger(__name__)
 
class TwentySkill:
    def __init__(self, twenty_api_url: str, twenty_api_key: str):
        self.base_url = twenty_api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {twenty_api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"TwentySkill initialized with base URL: {self.base_url}")
 
    def _normalize_object_name(self, object_name: str) -> str:
        """Normalize object names to Twenty CRM API format"""
        name = object_name.lower().strip()
        mappings = {
            "candidate": "candidates",
            "requistion": "requistions",
            "requisition": "requistions",
            "interview": "interviews",
            "note": "notes",
            "attachment": "attachments",
            "timelineactivity": "timelineActivities",
            "timeline_activity": "timelineActivities"
        }
        return mappings.get(name, name)
 
    async def write_field(self, object_name: str, record_id: str, field_name: str, value: Any) -> Dict[str, Any]:
        """
        Direct writes for non-state-changing data (notes, transcripts, scores).
        If field_name is 'note', it creates a note record linked to the record.
        """
        plural_obj = self._normalize_object_name(object_name)
        logger.info(f"write_field: {plural_obj}/{record_id}, field={field_name}")
 
        # Handle notes separately
        if field_name.lower() in ("note", "notes"):
            return await self._create_note(plural_obj, record_id, value)
 
        # Format phone/email structures if needed
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
 
        # Send PATCH request
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
                logger.info(f"Successfully wrote field '{field_name}' on {plural_obj}/{record_id}")
                return result.get("data", {}).get(f"update{object_name.capitalize()}", result)
            except Exception as e:
                logger.error(f"Failed to write field: {e}")
                raise Exception(f"TwentySkill write_field error: {e}")
 
    async def _create_note(self, plural_obj: str, record_id: str, value: Any) -> Dict[str, Any]:
        """Create and link a note to a record"""
        title = "Agent Update Note"
        content = str(value)
        if isinstance(value, dict):
            title = value.get("title", title)
            content = value.get("content", content)
 
        # Create note
        import json
        blocks = []
        for p in content.split('\n'):
            blocks.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": p}]
            })
        
        note_payload = {
            "title": title,
            "bodyV2": {
                "blocknote": json.dumps(blocks),
                "markdown": content
            }
        }
 
        async with httpx.AsyncClient() as client:
            # Create note
            note_res = await client.post(
                f"{self.base_url}/rest/notes",
                headers=self.headers,
                json=note_payload
            )
            note_res.raise_for_status()
            note = note_res.json().get("data", {}).get("createNote", {})
            note_id = note.get("id")
 
            # Link note to target object
            target_field = f"target{plural_obj.rstrip('s').capitalize()}Id"
            link_payload = {
                "noteId": note_id,
                target_field: record_id
            }
            
            link_res = await client.post(
                f"{self.base_url}/rest/noteTargets",
                headers=self.headers,
                json=link_payload
            )
            link_res.raise_for_status()
            
            return note
 
    async def trigger_workflow(self, workflow_name_or_id: str, record_id: str, target_status: str, object_name: str = "candidate") -> Dict[str, Any]:
        """
        Transition status/stage through a Twenty workflow.
        If workflow execution fails, falls back to direct mutation.
        """
        logger.info(f"trigger_workflow: workflow={workflow_name_or_id}, record={record_id}, status={target_status}")
 
        plural_obj = self._normalize_object_name(object_name)
        workflow_id = None
        version_id = None
 
        # Search for workflow
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/rest/workflows", headers=self.headers)
                res.raise_for_status()
                workflows = res.json().get("data", {}).get("workflows", [])
                
                for wf in workflows:
                    if wf.get("id") == workflow_name_or_id or wf.get("name") == workflow_name_or_id:
                        workflow_id = wf.get("id")
                        version_id = wf.get("lastPublishedVersionId")
                        break
        except Exception as e:
            logger.warning(f"Error querying workflows: {e}")
 
        # Trigger workflow if found
        if workflow_id and version_id:
            try:
                payload = {
                    "workflowId": workflow_id,
                    "workflowVersionId": version_id,
                    "name": f"Workflow run for {object_name} {record_id}",
                    "state": {
                        "recordId": record_id,
                        "targetStatus": target_status,
                        "objectName": object_name
                    }
                }
                async with httpx.AsyncClient() as client:
                    run_res = await client.post(
                        f"{self.base_url}/rest/workflowRuns",
                        headers=self.headers,
                        json=payload
                    )
                    run_res.raise_for_status()
                    run_data = run_res.json()
                    
                    if run_data.get("workflowRunError"):
                        logger.warning(f"Workflow error: {run_data.get('workflowRunError')}. Using direct mutation.")
                        raise Exception("Workflow runner error")
                    
                    logger.info(f"Successfully triggered workflow: {run_data.get('id')}")
                    return run_data
            except Exception as wf_err:
                logger.error(f"Workflow trigger failed: {wf_err}. Using direct mutation.")
 
        # Direct mutation fallback
        logger.warning(f"Using direct mutation for status transition to '{target_status}'")
        status_field = "interviewStatus" if object_name.lower() == "candidate" else "status"
        return await self.write_field(object_name, record_id, status_field, target_status)
