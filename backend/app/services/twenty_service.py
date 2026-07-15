import logging
from typing import Dict, Any, List, Optional
from app.crm_sdk import CRMClient
from app.crm_sdk.requisition import RequisitionModule
from app.crm_sdk.candidate import CandidateModule
from app.crm_sdk.application import ApplicationModule
from app.crm_sdk.interview import InterviewModule

logger = logging.getLogger(__name__)

class TwentyService:
    def __init__(self):
        # Phase 1.2: transport is delegated to the CRM SDK client. The client
        # reproduces the previous base-url/auth/timeout/parse/error behavior
        # exactly, so business methods below are unchanged.
        self._client = CRMClient()
        # Phase 2.1: requisition operations are delegated to the SDK module.
        self._requisitions = RequisitionModule(self._client)
        # Phase 2.2: candidate operations are delegated to the SDK module.
        self._candidates = CandidateModule(self._client)
        # Phase 2.3: application aggregate (net-new; no prior TwentyService code).
        self._applications = ApplicationModule(self._client)
        # Phase 2.4: interview operations are delegated to the SDK module.
        self._interviews = InterviewModule(self._client)
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
    # Phase 2.2: delegated to app.crm_sdk.candidate.CandidateModule.
    # Signatures and return values are unchanged; behavior is identical.
    async def get_candidates(self) -> List[Dict[str, Any]]:
        return await self._candidates.list()

    async def get_candidate(self, candidate_id: str) -> Dict[str, Any]:
        return await self._candidates.get(candidate_id)

    async def create_candidate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._candidates.create(data)

    async def update_candidate(self, candidate_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._candidates.update(candidate_id, data)

    async def delete_candidate(self, candidate_id: str) -> None:
        await self._candidates.delete(candidate_id)

    # ==========================================================
    # Requisitions API
    # ==========================================================
    # Phase 2.1: delegated to app.crm_sdk.requisition.RequisitionModule.
    # Signatures and return values are unchanged; behavior is identical.
    async def get_requisitions(self) -> List[Dict[str, Any]]:
        return await self._requisitions.list()

    async def get_requisition(self, requisition_id: str) -> Dict[str, Any]:
        return await self._requisitions.get(requisition_id)

    async def create_requisition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._requisitions.create(data)

    async def update_requisition(self, requisition_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._requisitions.update(requisition_id, data)

    async def delete_requisition(self, requisition_id: str) -> None:
        await self._requisitions.delete(requisition_id)

    # ==========================================================
    # Interviews API
    # ==========================================================
    # Phase 2.4: delegated to app.crm_sdk.interview.InterviewModule.
    # Signatures and return values are unchanged; behavior is identical.
    async def get_interviews(self) -> List[Dict[str, Any]]:
        return await self._interviews.list()

    async def get_interview(self, interview_id: str) -> Dict[str, Any]:
        return await self._interviews.get(interview_id)

    async def create_interview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._interviews.create(data)

    async def delete_interview(self, interview_id: str) -> None:
        await self._interviews.delete(interview_id)

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

    # Phase 2.2 (refinement): candidate-owned sub-resources delegated to the
    # Candidate aggregate module. Signatures/behavior unchanged.
    async def link_note_to_candidate(self, note_id: str, candidate_id: str) -> Dict[str, Any]:
        return await self._candidates.link_note(note_id, candidate_id)

    async def add_note_to_candidate(self, candidate_id: str, title: str, content: str) -> Dict[str, Any]:
        return await self._candidates.add_note(candidate_id, title, content)

    async def add_attachment_to_candidate(self, candidate_id: str, name: str, url: str) -> Dict[str, Any]:
        return await self._candidates.add_attachment(candidate_id, name, url)

    async def add_timeline_activity_to_candidate(self, candidate_id: str, title: str, content: str) -> Dict[str, Any]:
        return await self._candidates.add_timeline_activity(candidate_id, title, content)
