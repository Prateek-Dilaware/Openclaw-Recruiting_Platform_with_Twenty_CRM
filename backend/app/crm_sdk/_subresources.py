"""Internal helper for aggregate-owned sub-resources (notes / attachments / timeline).

This module is **internal** to the CRM SDK (leading underscore). It is NOT part
of the public SDK API and must not be imported by application code — only by
aggregate modules (``candidate.py``, ``application.py``, and future aggregates).

Why this exists
---------------
Several aggregates own the same kinds of sub-resources — notes, attachments, and
timeline activities — and the Twenty transport for each differs only by the
"target" foreign-key field (``targetCandidateId`` vs ``targetApplicationId`` …).
Rather than copy the identical create/link/attach/timeline transport into every
aggregate, this helper centralizes it, parameterized by that one target field.

It hides CRM transport complexity only. It contains NO business/workflow logic,
performs no cross-aggregate coordination, and preserves the exact payloads,
endpoints, response keys, and fallbacks the aggregates used before.
"""

from __future__ import annotations

from typing import Any, Dict

from app.crm_sdk.client import CRMClient
from app.crm_sdk.utility import build_blocknote_body


class SubResourceClient:
    """Transport for an aggregate's owned notes/attachments/timeline.

    Parameterized by ``target_field`` (the Twenty foreign-key used to link a
    sub-resource to the owning record, e.g. ``"targetCandidateId"``).
    """

    def __init__(self, client: CRMClient, target_field: str) -> None:
        self._client = client
        self._target_field = target_field

    # -- Notes --------------------------------------------------------------
    async def create_note(self, title: str, content: str) -> Dict[str, Any]:
        """Create a Note record (BlockNote ``bodyV2`` body). POST ``notes``."""
        payload = {"title": title, "bodyV2": build_blocknote_body(content)}
        response = await self._client.request("POST", "notes", payload)
        return response.get("data", {}).get("createNote", {})

    async def link_note(self, note_id: str, record_id: str) -> Dict[str, Any]:
        """Link an existing note to the owning record. POST ``noteTargets``."""
        payload = {"noteId": note_id, self._target_field: record_id}
        response = await self._client.request("POST", "noteTargets", payload)
        return response.get("data", {}).get("createNoteTarget", {})

    async def add_note(self, record_id: str, title: str, content: str) -> Dict[str, Any]:
        """Create a note then link it to the owning record (transport composition)."""
        note = await self.create_note(title, content)
        note_id = note.get("id")
        await self.link_note(note_id, record_id)
        return note

    # -- Attachments --------------------------------------------------------
    async def add_attachment(self, record_id: str, name: str, url: str) -> Dict[str, Any]:
        """Attach a file to the owning record. POST ``attachments``."""
        payload = {
            "name": name,
            "fullPath": url,
            "file": {"url": url, "name": name},
            self._target_field: record_id,
            "fileCategory": "OTHER",
        }
        response = await self._client.request("POST", "attachments", payload)
        return response.get("data", {}).get("createAttachment", {})

    # -- Timeline -----------------------------------------------------------
    async def add_timeline_activity(self, record_id: str, title: str, content: str) -> Dict[str, Any]:
        """Add a timeline activity to the owning record. POST ``timelineActivities``."""
        payload = {
            "name": title,
            "properties": {"details": content},
            self._target_field: record_id,
        }
        response = await self._client.request("POST", "timelineActivities", payload)
        return response.get("data", {}).get("createTimelineActivity", {})
