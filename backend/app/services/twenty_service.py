import logging
from typing import Dict, Any, List, Optional
from app.crm_sdk import CRMClient

logger = logging.getLogger(__name__)

class TwentyService:
    def __init__(self):
        # Phase 1.2: transport is delegated to the CRM SDK client. The client
        # reproduces the previous base-url/auth/timeout/parse/error behavior
        # exactly, so business methods below are unchanged.
        self._client = CRMClient()
        # Kept for backwards compatibility with any code that reads these.
        self.base_url = self._client.base_url
        self.headers = self._client.headers
        logger.info(f"Initialized TwentyService with base URL: {self.base_url}")

    async def _request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send an HTTP request to the Twenty CRM REST API via the CRM SDK client.

        Behavior (URL, headers, timeout, 204 handling, JSON parsing, and error
        message text) is identical to the previous inline implementation.
        """
        return await self._client.request(method, path, json_data)

    # ==========================================================
    # Candidates API
    # ==========================================================
    async def get_candidates(self) -> List[Dict[str, Any]]:
        response = await self._request("GET", "candidates")
        return response.get("data", {}).get("candidates", [])

    async def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        response = await self._request("GET", f"candidates/{candidate_id}")
        return response.get("data", {}).get("candidate", {})

    async def create_candidate(self, data: Dict[str, Any]) -> Dict[str, Any]:
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
        response = await self._request("POST", "candidates", payload)
        return response.get("data", {}).get("createCandidate", {})

    async def update_candidate(self, candidate_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
        response = await self._request("PATCH", f"candidates/{candidate_id}", payload)
        return response.get("data", {}).get("updateCandidate", {})

    async def delete_candidate(self, candidate_id: str) -> None:
        await self._request("DELETE", f"candidates/{candidate_id}")

    # ==========================================================
    # Requisitions API
    # ==========================================================
    async def get_requisitions(self) -> List[Dict[str, Any]]:
        response = await self._request("GET", "requistions")
        return response.get("data", {}).get("requistions", [])

    async def get_requisition(self, requisition_id: str) -> Dict[str, Any]:
        response = await self._request("GET", f"requistions/{requisition_id}")
        return response.get("data", {}).get("requistion", {})

    async def create_requisition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._request("POST", "requistions", data)
        return response.get("data", {}).get("createRequistion", {})

    async def update_requisition(self, requisition_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._request("PATCH", f"requistions/{requisition_id}", data)
        return response.get("data", {}).get("updateRequistion", {})

    async def delete_requisition(self, requisition_id: str) -> None:
        await self._request("DELETE", f"requistions/{requisition_id}")

    # ==========================================================
    # Interviews API
    # ==========================================================
    async def get_interviews(self) -> List[Dict[str, Any]]:
        response = await self._request("GET", "interviews")
        return response.get("data", {}).get("interviews", [])

    async def get_interview(self, interview_id: str) -> Dict[str, Any]:
        response = await self._request("GET", f"interviews/{interview_id}")
        return response.get("data", {}).get("interview", {})

    async def create_interview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._request("POST", "interviews", data)
        return response.get("data", {}).get("createInterview", {})

    async def delete_interview(self, interview_id: str) -> None:
        await self._request("DELETE", f"interviews/{interview_id}")

    # ==========================================================
    # Custom Notes, Attachments, and Activities
    # ==========================================================
    async def create_note(self, title: str, content: str) -> Dict[str, Any]:
        import json
        blocks = []
        for p in content.split('\n'):
            blocks.append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": p
                    }
                ]
            })
        body_v2_obj = {
            "blocknote": json.dumps(blocks),
            "markdown": content
        }
        payload = {
            "title": title,
            "bodyV2": body_v2_obj,
        }
        response = await self._request("POST", "notes", payload)
        return response.get("data", {}).get("createNote", {})

    async def link_note_to_candidate(self, note_id: str, candidate_id: str) -> Dict[str, Any]:
        payload = {
            "noteId": note_id,
            "targetCandidateId": candidate_id
        }
        response = await self._request("POST", "noteTargets", payload)
        return response.get("data", {}).get("createNoteTarget", {})

    async def add_note_to_candidate(self, candidate_id: str, title: str, content: str) -> Dict[str, Any]:
        note = await self.create_note(title, content)
        note_id = note.get("id")
        await self.link_note_to_candidate(note_id, candidate_id)
        return note

    async def add_attachment_to_candidate(self, candidate_id: str, name: str, url: str) -> Dict[str, Any]:
        payload = {
            "name": name,
            "fullPath": url,
            "file": {"url": url, "name": name},
            "targetCandidateId": candidate_id,
            "fileCategory": "OTHER"
        }
        response = await self._request("POST", "attachments", payload)
        return response.get("data", {}).get("createAttachment", {})

    async def add_timeline_activity_to_candidate(self, candidate_id: str, title: str, content: str) -> Dict[str, Any]:
        payload = {
            "name": title,
            "properties": {"details": content},
            "targetCandidateId": candidate_id
        }
        response = await self._request("POST", "timelineActivities", payload)
        return response.get("data", {}).get("createTimelineActivity", {})
