"""Shared utilities and declarative definitions for Twenty CRM Schema V2."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / "backend" / ".env"
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}

# These are the only custom objects owned by Schema V2. The deletion script uses
# this allowlist, plus the legacy Schema V1 names, so standard Twenty objects are
# never candidates for removal.
V2_OBJECTS = (
    "candidate",
    "requisition",
    "application",
    "interview",
    "evaluation",
    "offer",
)
LEGACY_OBJECTS = ("candidate", "requistion", "interview")
PROJECT_OBJECTS = tuple(sorted(set(V2_OBJECTS + LEGACY_OBJECTS)))

OBJECT_DEFINITIONS: list[dict[str, str]] = [
    {
        "nameSingular": "candidate",
        "namePlural": "candidates",
        "labelSingular": "Candidate",
        "labelPlural": "Candidates",
        "description": "Reusable recruiting contact record.",
        "icon": "IconUser",
    },
    {
        "nameSingular": "requisition",
        "namePlural": "requisitions",
        "labelSingular": "Requisition",
        "labelPlural": "Requisitions",
        "description": "Approved job opening and posting record.",
        "icon": "IconBriefcase",
    },
    {
        "nameSingular": "application",
        "namePlural": "applications",
        "labelSingular": "Application",
        "labelPlural": "Applications",
        "description": "Candidate participation in a specific requisition.",
        "icon": "IconFileDescription",
    },
    {
        "nameSingular": "interview",
        "namePlural": "interviews",
        "labelSingular": "Interview",
        "labelPlural": "Interviews",
        "description": "Scheduled interview round for an application.",
        "icon": "IconCalendarEvent",
    },
    {
        "nameSingular": "evaluation",
        "namePlural": "evaluations",
        "labelSingular": "Evaluation",
        "labelPlural": "Evaluations",
        "description": "AI or human assessment of an interview.",
        "icon": "IconChecklist",
    },
    {
        "nameSingular": "offer",
        "namePlural": "offers",
        "labelSingular": "Offer",
        "labelPlural": "Offers",
        "description": "Recruiting offer approval, delivery, and outcome.",
        "icon": "IconFileText",
    },
]


def select_options(values: Iterable[tuple[str, str, str]]) -> list[dict[str, Any]]:
    return [
        {"label": label, "value": value, "color": color, "position": position}
        for position, (label, value, color) in enumerate(values)
    ]


REQUIRED_SELECT_VALUES: dict[tuple[str, str], set[str]] = {
    ("requisition", "requisitionStatus"): {
        "DRAFT", "JD_PENDING_APPROVAL", "APPROVED", "POSTED", "CLOSED"
    },
    ("application", "stage"): {
        "APPLIED", "SCREENING", "RECRUITER_REVIEW", "INTERVIEW_SCHEDULING",
        "INTERVIEW_SCHEDULED", "INTERVIEW_COMPLETED", "DECISION_PENDING", "OFFER",
        "HIRED", "REJECTED",
    },
    ("interview", "interviewStatus"): {
        "DRAFT", "SCHEDULED", "CONFIRMED", "COMPLETED", "CANCELLED"
    },
    ("offer", "offerStatus"): {
        "DRAFT", "APPROVED", "SENT", "ACCEPTED", "DECLINED"
    },
}

FIELD_DEFINITIONS: dict[str, list[dict[str, Any]]] = {
    "candidate": [
        {"name": "emails", "label": "Emails", "type": "EMAILS"},
        {"name": "phones", "label": "Phones", "type": "PHONES"},
        {"name": "source", "label": "Source", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "skillsTags", "label": "Skills", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "resumeUrl", "label": "Resume URL", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
    ],
    "requisition": [
        {"name": "jobTitle", "label": "Job Title", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "department", "label": "Department", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "location", "label": "Location", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "employmentType", "label": "Employment Type", "type": "SELECT", "options": select_options([
            ("Full-Time", "FULL_TIME", "green"),
            ("Part-Time", "PART_TIME", "jade"),
            ("Contract", "CONTRACT", "turquoise"),
            ("Internship", "INTERNSHIP", "sky"),
        ])},
        {"name": "experienceRequirements", "label": "Experience Requirements", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "requiredSkills", "label": "Required Skills", "type": "TEXT", "settings": {"displayedMaxRows": 4}},
        {"name": "jobDescription", "label": "Job Description", "type": "TEXT", "settings": {"displayedMaxRows": 12}},
        {"name": "headcount", "label": "Headcount", "type": "NUMBER", "settings": {"type": "number", "decimals": 0}},
        {"name": "postingUrl", "label": "Posting URL", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "postedAt", "label": "Posted At", "type": "DATE_TIME"},
        {"name": "closedAt", "label": "Closed At", "type": "DATE_TIME"},
        {"name": "requisitionStatus", "label": "Requisition Status", "type": "SELECT", "options": select_options([
            ("Draft", "DRAFT", "gray"),
            ("JD Pending Approval", "JD_PENDING_APPROVAL", "yellow"),
            ("Approved", "APPROVED", "green"),
            ("Posted", "POSTED", "blue"),
            ("Closed", "CLOSED", "red"),
        ])},
    ],
    "application": [
        {"name": "stage", "label": "Application Stage", "type": "SELECT", "options": select_options([
            ("Applied", "APPLIED", "gray"),
            ("Screening", "SCREENING", "yellow"),
            ("Recruiter Review", "RECRUITER_REVIEW", "orange"),
            ("Interview Scheduling", "INTERVIEW_SCHEDULING", "blue"),
            ("Interview Scheduled", "INTERVIEW_SCHEDULED", "cyan"),
            ("Interview Completed", "INTERVIEW_COMPLETED", "indigo"),
            ("Decision Pending", "DECISION_PENDING", "purple"),
            ("Offer", "OFFER", "green"),
            ("Hired", "HIRED", "jade"),
            ("Rejected", "REJECTED", "red"),
        ])},
        {"name": "source", "label": "Application Source", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "appliedAt", "label": "Applied At", "type": "DATE_TIME"},
        {"name": "consentStatus", "label": "Consent Status", "type": "SELECT", "options": select_options([
            ("Pending", "PENDING", "yellow"),
            ("Granted", "GRANTED", "green"),
            ("Withdrawn", "WITHDRAWN", "red"),
        ])},
        {"name": "parsedResumeSummary", "label": "Parsed Resume Summary", "type": "TEXT", "settings": {"displayedMaxRows": 10}},
        {"name": "decisionRecommendation", "label": "Decision Recommendation", "type": "SELECT", "options": select_options([
            ("Pending", "PENDING", "gray"),
            ("Proceed", "PROCEED", "green"),
            ("Hold", "HOLD", "yellow"),
            ("Reject", "REJECT", "red"),
        ])},
        {"name": "decisionReason", "label": "Decision Reason", "type": "TEXT", "settings": {"displayedMaxRows": 6}},
    ],
    "interview": [
        {"name": "round", "label": "Round", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "interviewType", "label": "Interview Type", "type": "SELECT", "options": select_options([
            ("Phone", "PHONE", "blue"),
            ("Video", "VIDEO", "cyan"),
            ("Technical", "TECHNICAL", "purple"),
            ("Hiring Manager", "HIRING_MANAGER", "orange"),
            ("Onsite", "ONSITE", "green"),
        ])},
        {"name": "interviewStatus", "label": "Interview Status", "type": "SELECT", "options": select_options([
            ("Draft", "DRAFT", "gray"),
            ("Scheduled", "SCHEDULED", "blue"),
            ("Confirmed", "CONFIRMED", "cyan"),
            ("Completed", "COMPLETED", "green"),
            ("Cancelled", "CANCELLED", "red"),
        ])},
        {"name": "scheduledAt", "label": "Scheduled At", "type": "DATE_TIME"},
        {"name": "endedAt", "label": "Ended At", "type": "DATE_TIME"},
        {"name": "timezone", "label": "Timezone", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "durationMinutes", "label": "Duration Minutes", "type": "NUMBER", "settings": {"type": "number", "decimals": 0}},
    ],
    "evaluation": [
        {"name": "evaluationType", "label": "Evaluation Type", "type": "SELECT", "options": select_options([
            ("Resume", "RESUME", "blue"),
            ("Interview", "INTERVIEW", "purple"),
        ])},
        {"name": "authorType", "label": "Author Type", "type": "SELECT", "options": select_options([
            ("Agent", "AGENT", "violet"),
            ("Human", "HUMAN", "green"),
        ])},
        {"name": "overallScore", "label": "Overall Score", "type": "NUMBER", "settings": {"type": "number", "decimals": 1}},
        {"name": "recommendation", "label": "Recommendation", "type": "SELECT", "options": select_options([
            ("Proceed", "PROCEED", "green"),
            ("Hold", "HOLD", "yellow"),
            ("Reject", "REJECT", "red"),
        ])},
        {"name": "sentiment", "label": "Sentiment", "type": "SELECT", "options": select_options([
            ("Positive", "POSITIVE", "green"),
            ("Neutral", "NEUTRAL", "gray"),
            ("Negative", "NEGATIVE", "red"),
        ])},
        {"name": "summary", "label": "Summary", "type": "TEXT", "settings": {"displayedMaxRows": 8}},
        {"name": "strengths", "label": "Strengths", "type": "TEXT", "settings": {"displayedMaxRows": 8}},
        {"name": "weaknesses", "label": "Weaknesses", "type": "TEXT", "settings": {"displayedMaxRows": 8}},
        {"name": "promptVersionTag", "label": "Prompt Version Tag", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "evaluationStatus", "label": "Evaluation Status", "type": "SELECT", "options": select_options([
            ("Draft", "DRAFT", "gray"),
            ("Final", "FINAL", "green"),
        ])},
    ],
    "offer": [
        {"name": "offerStatus", "label": "Offer Status", "type": "SELECT", "options": select_options([
            ("Draft", "DRAFT", "gray"),
            ("Approved", "APPROVED", "blue"),
            ("Sent", "SENT", "purple"),
            ("Accepted", "ACCEPTED", "green"),
            ("Declined", "DECLINED", "red"),
        ])},
        {"name": "salary", "label": "Salary", "type": "NUMBER", "settings": {"type": "number", "decimals": 2}},
        {"name": "offerCurrency", "label": "Currency", "type": "TEXT", "settings": {"displayedMaxRows": 0}},
        {"name": "startDate", "label": "Start Date", "type": "DATE"},
        {"name": "expiryDate", "label": "Expiry Date", "type": "DATE"},
        {"name": "termsSummary", "label": "Terms Summary", "type": "TEXT", "settings": {"displayedMaxRows": 8}},
        {"name": "sentAt", "label": "Sent At", "type": "DATE_TIME"},
        {"name": "respondedAt", "label": "Responded At", "type": "DATE_TIME"},
        {"name": "declineReason", "label": "Decline Reason", "type": "TEXT", "settings": {"displayedMaxRows": 4}},
    ],
}

# Source records carry the foreign key. Each creates the inverse collection field
# on its target object through Twenty's relation metadata API.
RELATIONSHIP_DEFINITIONS: list[dict[str, str]] = [
    {
        "source": "application", "field": "candidate", "label": "Candidate",
        "target": "candidate", "inverse_field": "applications", "inverse_label": "Applications",
    },
    {
        "source": "application", "field": "requisition", "label": "Requisition",
        "target": "requisition", "inverse_field": "applications", "inverse_label": "Applications",
    },
    {
        "source": "interview", "field": "application", "label": "Application",
        "target": "application", "inverse_field": "interviews", "inverse_label": "Interviews",
    },
    {
        "source": "evaluation", "field": "interview", "label": "Interview",
        "target": "interview", "inverse_field": "evaluations", "inverse_label": "Evaluations",
    },
    {
        "source": "offer", "field": "application", "label": "Application",
        "target": "application", "inverse_field": "offers", "inverse_label": "Offers",
    },
]


@dataclass
class OperationReport:
    title: str
    created: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    validated: list[str] = field(default_factory=list)

    def print(self) -> None:
        print("\n" + "=" * 72)
        print(self.title)
        print("=" * 72)
        for heading, values in (
            ("Created", self.created),
            ("Deleted", self.deleted),
            ("Skipped", self.skipped),
            ("Validated", self.validated),
            ("Warnings", self.warnings),
            ("Errors", self.errors),
        ):
            print(f"{heading}: {len(values)}")
            for value in values:
                print(f"  - {value}")


def load_twenty_env() -> tuple[str, str]:
    """Load Twenty connection details from environment or backend/.env."""
    values = {
        "TWENTY_API_URL": os.getenv("TWENTY_API_URL", ""),
        "TWENTY_API_KEY": os.getenv("TWENTY_API_KEY", ""),
    }
    if ENV_PATH.exists():
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key.strip() in values and not values[key.strip()]:
                    values[key.strip()] = value.strip().strip('"').strip("'")

    api_url = values["TWENTY_API_URL"].replace("host.docker.internal", "localhost").rstrip("/")
    api_key = values["TWENTY_API_KEY"]
    if not api_url or not api_key or "your-twenty-api-key" in api_key:
        raise RuntimeError(
            "TWENTY_API_URL and TWENTY_API_KEY must be supplied through environment variables "
            "or backend/.env."
        )
    return api_url, api_key


def get_headers(api_key: str) -> dict[str, str]:
    """Return the common authorization headers for standalone integration tests."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


class TwentyClient:
    """Small retrying client for the Twenty metadata and records REST APIs."""

    def __init__(self) -> None:
        self.base_url, api_key = load_twenty_env()
        self.headers = get_headers(api_key)
        self.client = httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, headers=self.headers)

    def close(self) -> None:
        self.client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        allow_statuses: set[int] | None = None,
    ) -> tuple[int, Any]:
        url = f"{self.base_url}{path}"
        allowed = allow_statuses or set()
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                print(f"[REQUEST] {method} {path}")
                response = self.client.request(method, url, json=json_body)
                print(f"[RESPONSE] {method} {path} -> {response.status_code}")
                if response.status_code in allowed:
                    return response.status_code, self._json_or_text(response)
                if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_ATTEMPTS:
                    print(f"[RETRY] {method} {path} returned {response.status_code}; attempt {attempt}/{MAX_ATTEMPTS}")
                    time.sleep(attempt)
                    continue
                response.raise_for_status()
                return response.status_code, self._json_or_text(response)
            except httpx.RequestError as exc:
                if attempt == MAX_ATTEMPTS:
                    raise RuntimeError(f"{method} {url} failed after {MAX_ATTEMPTS} attempts: {exc}") from exc
                print(f"[RETRY] {method} {path} failed: {exc}; attempt {attempt}/{MAX_ATTEMPTS}")
                time.sleep(attempt)
        raise RuntimeError(f"Unexpected request loop exit for {method} {url}")

    @staticmethod
    def _json_or_text(response: httpx.Response) -> Any:
        if not response.content:
            return {}
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text

    def get_objects(self) -> list[dict[str, Any]]:
        _, payload = self.request("GET", "/rest/metadata/objects")
        if isinstance(payload, dict):
            data = payload.get("data", payload)
            return data if isinstance(data, list) else data.get("objects", [])
        return []

    def get_object_map(self) -> dict[str, dict[str, Any]]:
        return {obj["nameSingular"]: obj for obj in self.get_objects()}

    def create_object(self, definition: dict[str, Any]) -> Any:
        return self.request("POST", "/rest/metadata/objects", json_body=definition)[1]

    def create_field(self, definition: dict[str, Any]) -> Any:
        return self.request("POST", "/rest/metadata/fields", json_body=definition)[1]

    def delete_field(self, field_id: str) -> tuple[int, Any]:
        return self.request("DELETE", f"/rest/metadata/fields/{field_id}", allow_statuses={404})

    def deactivate_object(self, object_id: str) -> tuple[int, Any]:
        return self.request("PATCH", f"/rest/metadata/objects/{object_id}", json_body={"isActive": False}, allow_statuses={404})

    def delete_object(self, object_id: str) -> tuple[int, Any]:
        return self.request("DELETE", f"/rest/metadata/objects/{object_id}", allow_statuses={404})

    def list_records(self, object_plural: str) -> list[dict[str, Any]]:
        _, payload = self.request("GET", f"/rest/{object_plural}")
        if not isinstance(payload, dict):
            return []
        data = payload.get("data", payload)
        if isinstance(data, list):
            return data
        records = data.get(object_plural, [])
        if isinstance(records, dict):
            records = records.get("edges", [])
        if isinstance(records, list) and records and isinstance(records[0], dict) and "node" in records[0]:
            return [edge["node"] for edge in records if edge.get("node")]
        return records if isinstance(records, list) else []

    def create_record(self, object_plural: str, payload: dict[str, Any]) -> dict[str, Any]:
        _, response = self.request("POST", f"/rest/{object_plural}", json_body=payload)
        if not isinstance(response, dict):
            return {}
        data = response.get("data", response)
        if not isinstance(data, dict):
            return {}
        singular_by_plural = {
            "candidates": "Candidate",
            "requisitions": "Requisition",
            "applications": "Application",
            "interviews": "Interview",
            "evaluations": "Evaluation",
            "offers": "Offer",
            "workflows": "Workflow",
        }
        create_key = f"create{singular_by_plural.get(object_plural, object_plural[:-1].capitalize())}"
        return data.get(create_key, data)


def get_field_map(object_metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {field["name"]: field for field in object_metadata.get("fields", [])}


def relation_payload(
    source_object_id: str,
    target_object_id: str,
    relation: dict[str, str],
) -> dict[str, Any]:
    return {
        "name": relation["field"],
        "label": relation["label"],
        "type": "RELATION",
        "objectMetadataId": source_object_id,
        "relationCreationPayload": {
            "targetObjectMetadataId": target_object_id,
            "type": "MANY_TO_ONE",
            "targetFieldLabel": relation["inverse_label"],
            "targetFieldName": relation["inverse_field"],
            "targetFieldIcon": "IconRelationOneToMany",
        },
    }


def main_error_boundary(main: Any) -> None:
    try:
        main()
    except Exception as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        sys.exit(1)
