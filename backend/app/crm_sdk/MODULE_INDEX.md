# CRM SDK — Business Module Index

A single, authoritative map of the CRM SDK package. It documents the foundation
(infrastructure) layer, the business-entity modules, the established extraction
pattern, and the migration status so the SDK stays consistent as the remaining
modules are added.

> Architecture: `React → FastAPI → CRMService → CRM SDK → Twenty CRM`.
> The SDK owns **entity CRUD + single-entity domain convenience methods only**.
> Workflows, orchestration, notifications, AI, and OpenClaw live in higher layers.

---

## Package layout

```
crm_sdk/
│
├── __init__.py        # Public exports (foundation + business modules)
├── MODULE_INDEX.md    # This file
│
├── ── Foundation (infrastructure) ──────────────────────────
├── client.py          # CRMClient — shared HTTP transport (URL, exec, parse, errors, retry)
├── config.py          # CRMConfig — connection settings (base_url, api_key, timeout)
├── auth.py            # build_headers() — bearer auth headers
├── exceptions.py      # CRMError hierarchy (+ error_for_status mapper)
├── models.py          # Shared models: APIResponse, Pagination, ErrorResponse, RequestContext
├── validators.py      # UUID / required-fields / object-name / pagination validation
├── metadata.py        # MetadataProvider + object/field/relationship registries
├── utility.py         # unwrap_data + Twenty field-shape builders (email/phone/blocknote)
├── router.py          # CRMRouter — action dispatch skeleton (namespaces only)
├── _subresources.py   # INTERNAL: SubResourceClient (notes/attachments/timeline), not public
│
├── ── Business entity modules ──────────────────────────────
├── requisition.py     # RequisitionModule   ✅ implemented (Phase 2.1)
├── candidate.py       # CandidateModule      ✅ implemented (Phase 2.2)
├── application.py     # ApplicationModule    ✅ implemented (Phase 2.3)
├── interview.py       # InterviewModule      ✅ implemented (Phase 2.4)
├── evaluation.py      # EvaluationModule     ✅ implemented (Phase 2.5)
├── offer.py           # OfferModule          ✅ implemented (Phase 2.6)
├── search.py          # SearchModule         ⏳ planned  (Phase 2.7)
└── workflow.py        # WorkflowModule       ⏳ planned  (Phase 2.8)
```

---

## Foundation modules

| Module | Public symbol(s) | Responsibility |
| ------ | ---------------- | -------------- |
| `client.py` | `CRMClient` | The **only** transport layer. URL generation, header injection, request execution (httpx), response parsing, status handling, error handling + logging, opt-in retry. |
| `config.py` | `CRMConfig` | Immutable connection settings; `CRMConfig.from_settings()` reads `app.settings`. |
| `auth.py` | `build_headers` | Bearer + content-type headers. |
| `exceptions.py` | `CRMError`, `AuthenticationError`, `ValidationError`, `RequestError`, `CRMRequestError`, `RateLimitError`, `NotFoundError`, `ConflictError`, `error_for_status` | Structured error surface. |
| `models.py` | `APIResponse`, `Pagination`, `ErrorResponse`, `RequestContext` | Shared infrastructure models (no business models). |
| `validators.py` | `validate_uuid`, `require_fields`, `validate_object_name`, `validate_pagination` | Non-business input validation. |
| `metadata.py` | `MetadataProvider`, `MetadataRegistry`, `ObjectEntry`, `FieldEntry`, `RelationshipEntry` | Read-only metadata registries (no live sync yet). |
| `utility.py` | `unwrap_data`, `build_email_field`, `build_phone_field`, `build_blocknote_body` | Generic, reusable helpers. |
| `router.py` | `CRMRouter` | Action-dispatch skeleton (`object.verb`), no handlers yet. |
| `_subresources.py` | `SubResourceClient` *(internal)* | Shared notes/attachments/timeline transport for aggregates, parameterized by target FK field. **Not** publicly exported. |

---

## Business entity modules

Each business module encapsulates exactly **one** CRM entity, takes a shared
`CRMClient` in its constructor, and exposes a domain API. `TwentyService`
delegates to these modules (thin delegation layer).

| Module | Class | Entity | REST collection | Status | Notes |
| ------ | ----- | ------ | --------------- | ------ | ----- |
| `requisition.py` | `RequisitionModule` | Requisition | `requistions` *(legacy spelling preserved)* | ✅ | CRUD + `approve`/`publish`/`close` convenience wrappers (single-field status PATCH). |
| `candidate.py` | `CandidateModule` | **Candidate aggregate** | `candidates` (+ `notes`, `noteTargets`, `attachments`, `timelineActivities` internally) | ✅ | Aggregate root: CRUD + notes (`add_note`/`link_note`) + `add_attachment` + `add_timeline_activity`. Hides multi-entity transport behind one domain API. No lifecycle wrappers. |
| `application.py` | `ApplicationModule` | **Application aggregate** | `applications` (+ notes/attachments/timeline) | ✅ | Central object. Net-new (no prior TwentyService code); built on established pattern + Schema V2 names. CRUD + `advance_stage`/`reject`/`hire`/`assign_recruiter` + sub-resources. Not delegated from TwentyService (nothing pre-existed). |
| `interview.py` | `InterviewModule` | **Interview aggregate** | `interviews` | ✅ | CRUD (list/get/create/delete verbatim; `update` additive) + `schedule`/`reschedule`/`cancel`/`complete` (single-field `interviewStatus` PATCH). Data-only — no calendar/email. |
| `evaluation.py` | `EvaluationModule` | **Evaluation aggregate** | `evaluations` (+ notes/attachments/timeline) | ✅ | Native (Schema V2). CRUD + `approve`(status=FINAL)/`recommend`/`hold`/`reject`(recommendation) + sub-resources via shared helper (`targetEvaluationId`). |
| `offer.py` | `OfferModule` | **Offer aggregate** | `offers` (+ notes/attachments/timeline) | ✅ | Native (Schema V2). CRUD + `approve`/`send`/`accept`/`decline`/`withdraw` (offerStatus; withdraw→DRAFT, no WITHDRAWN in schema) + sub-resources (`targetOfferId`). Data-only. |
| `search.py` | `SearchModule` | (cross-entity read) | n/a | ⏳ | Query/filter helpers. |
| `workflow.py` | `WorkflowModule` | Workflow | `workflows` | ⏳ | Trigger only; no orchestration in SDK. |

---

## Established module pattern (for new modules)

Every business module MUST follow the shape set by `requisition.py` and
`candidate.py`:

```python
"""CRM SDK — <Entity> module.

<Purpose. Responsibilities (DOES). Non-responsibilities (does NOT).>
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.crm_sdk.client import CRMClient

logger = logging.getLogger(__name__)

_COLLECTION = "<rest_collection_name>"   # preserve legacy spelling if present


class <Entity>Module:
    """Business operations for the <Entity> entity, over the CRM SDK client."""

    def __init__(self, client: CRMClient) -> None:
        self._client = client

    async def list(self) -> List[Dict[str, Any]]: ...
    async def get(self, entity_id: str) -> Dict[str, Any]: ...
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    async def update(self, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]: ...
    async def delete(self, entity_id: str) -> None: ...
    # Optional: single-field convenience wrappers over update() ONLY if they
    # already exist or naturally wrap one update. Never invent workflows.
```

**Rules (per Milestone 2):**
1. Extraction, not rewrite — preserve endpoints, payloads, response keys, and fallbacks **exactly**.
2. Use the shared `CRMClient`; never duplicate transport code.
3. One entity per module; no cross-entity orchestration.
4. Convenience wrappers only if they wrap a single `update`; document them as such.
5. `TwentyService` delegates; no duplicated business logic remains.
6. Register the class in `__init__.py` exports and add a row to this index.

---

## `TwentyService` delegation status

| Area | Delegated to SDK? |
| ---- | ----------------- |
| Requisition CRUD | ✅ `RequisitionModule` |
| Candidate CRUD | ✅ `CandidateModule` |
| Candidate notes / attachments / timeline | ✅ `CandidateModule` (aggregate root) |
| Generic `create_note` (Note entity) | ❌ still in `TwentyService` (non-candidate consumers) |
| Interview CRUD | ✅ `InterviewModule` |
| Application | ✅ `ApplicationModule` (native; nothing to delegate from `TwentyService`) |
| Evaluation | ✅ `EvaluationModule` (native SDK module) |
| Offer | ✅ `OfferModule` (native SDK module) |
| Search / Workflow | ❌ future phases |

---

## Migration order (Milestone 2)

```
2.1 Requisition ✅ → 2.2 Candidate ✅ → 2.3 Application ✅ → 2.4 Interview ✅
→ 2.5 Evaluation ✅ → 2.6 Offer ✅ → 2.7 Search → 2.8 Workflow
```

*Update this index whenever a module is added or its status changes.*
