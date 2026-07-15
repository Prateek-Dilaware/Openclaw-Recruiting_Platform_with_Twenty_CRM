# `twenty-skill` V2 — Technical Audit & Refactoring Blueprint

**Date:** 2026-07-15
**Status:** Audit only — **no CRUD implementation performed.** This is a pre-implementation blueprint.
**Author:** Architecture audit of the current codebase (every conclusion is cited to a source file).

> **Goal:** Understand the current `twenty-skill` implementation, compare it against the CRM
> Schema V2 architecture, and produce a detailed refactoring plan before writing significant new code.

---

## 0. Scope of Inspection

Files read and analyzed for this audit:

| Area | Files inspected |
| ---- | --------------- |
| OpenClaw skill | `CRM/openclaw/skills/twenty-skill/SKILL.md`, `skill.py`, `__init__.py` |
| Backend CRM layer | `backend/app/services/twenty_skill.py`, `twenty_service.py`, `crm_service.py`, `openclaw_client.py` |
| OpenClaw bridge | `backend/app/agents/openclaw_service.py` |
| Agents (consumers) | `backend/app/agents/scheduling_agent.py` (+ referenced `jd_agent`, `interview_agent`, `retrospective_agent`) |
| API routers | `backend/app/api/candidate.py`, `requistion.py`, `main.py` |
| Config | `backend/app/settings.py` |
| Schema V2 (target) | `scripts/schema_v2/schema_utils.py`, `02_create_objects.py`, `05_create_workflows.py` |

---

## 1. Current Architecture

### 1.1 Stated target architecture

```
React → FastAPI → OpenClaw → twenty-skill → Twenty CRM → PostgreSQL
```

### 1.2 Actual architecture as implemented (from source)

```
React → FastAPI ─┬─► TwentyService ───────────────► Twenty CRM REST  (PRIMARY, live path)
                 ├─► TwentySkill (backend copy) ───► Twenty CRM REST  (notes/workflow helper)
                 └─► CRMService ──(USE_OPENCLAW?)──► TwentySkill (default)  ─► Twenty CRM REST
                                                 └─► OpenclawClient ─► OpenClaw gateway (NEVER taken; flag=False)

OpenClaw runtime ─► twenty-skill/SKILL.md (metadata only; NO tool definitions) ─► (does nothing)
```

**Key structural finding:** The intended chain (`OpenClaw → twenty-skill → Twenty CRM`) is **not
wired up**. Today FastAPI talks to Twenty CRM **directly**, and the OpenClaw skill is inert.

- `CRMService.__init__` reads `self.use_openclaw = getattr(settings, 'USE_OPENCLAW', False)`
  (`backend/app/services/crm_service.py:13`), and `settings.USE_OPENCLAW` defaults to **`False`**
  (`backend/app/settings.py:34`). So the OpenClaw branch is never executed.
- The OpenClaw-side skill (`CRM/openclaw/skills/twenty-skill/skill.py`) is a **near-verbatim copy**
  of the backend `TwentySkill`, but its `SKILL.md` contains only a title and no instructions or tool
  definitions (`CRM/openclaw/skills/twenty-skill/SKILL.md` — 6 lines total). OpenClaw therefore loads
  it as a discoverable skill but has no behavior to invoke.

### 1.3 The three overlapping CRM abstractions (redundancy)

| Class | File | Role today |
| ----- | ---- | ---------- |
| `TwentyService` | `backend/app/services/twenty_service.py` | Direct Twenty REST CRUD (candidates, requisitions, interviews, notes, attachments, timeline). **Primary live path.** |
| `TwentySkill` (backend) | `backend/app/services/twenty_skill.py` | `write_field` + `trigger_workflow`; wraps `TwentyService`. Used by `candidate.py` and `CRMService`. |
| `TwentySkill` (skill) | `CRM/openclaw/skills/twenty-skill/skill.py` | Standalone copy for OpenClaw. **Orphaned / never invoked.** |
| `CRMService` | `backend/app/services/crm_service.py` | Router that *would* switch between `TwentySkill` and `OpenclawClient`. Used by agents. |
| `OpenclawClient` | `backend/app/services/openclaw_client.py` | HTTP client to OpenClaw. **Dead code** (flag off + wrong endpoint). |
| `OpenClawService` | `backend/app/agents/openclaw_service.py` | In-process agent registry. Not connected to real OpenClaw. |

---

## 2. Current Execution Flow

### 2.1 Direct CRUD (e.g. create candidate)

```
POST /api/v1/candidates
 └─ candidate.py: create_candidate()          (backend/app/api/candidate.py:55)
     └─ TwentyService.create_candidate()        (twenty_service.py:57)
         └─ TwentyService._request("POST","candidates")  (twenty_service.py:16)
             └─ httpx → {TWENTY_API_URL}/rest/candidates
```

### 2.2 Agent flow (e.g. schedule interview)

```
POST /api/v1/candidates/{id}/schedule
 └─ candidate.py: schedule_candidate_interview()   (candidate.py:78)
     └─ SchedulingAgent.schedule_interview()        (scheduling_agent.py:22)
         ├─ CRMService.twenty_service.get_candidate()
         ├─ CRMService.twenty_service.create_interview({... "candidateId": ...})
         ├─ CRMService.write_field(object_name="candidate", field="note", ...)
         │    └─ (USE_OPENCLAW=False) → TwentySkill.write_field()   (twenty_skill.py:35)
         └─ CRMService.trigger_workflow("Candidate Status Change", target="INTERVIEW_SCHEDULED")
              └─ (USE_OPENCLAW=False) → TwentySkill.trigger_workflow()  (twenty_skill.py:104)
                   └─ query /rest/workflows → fallback direct PATCH interviewStatus
```

### 2.3 Registered routers (live surface)

From `backend/app/main.py:34–39`: `candidates`, `requisitions`, `interviews`, `voice`, `webhooks`,
`health` — all under `/api/v1`. **No `application`, `evaluation`, or `offer` routers exist.**

---

## 3. Current Entry Point & OpenClaw Invocation

### 3.1 Skill entry point

- **OpenClaw skill:** `CRM/openclaw/skills/twenty-skill/` — the runtime discovers it via `SKILL.md`
  (verified previously: source `openclaw-managed`, `✓ ready`). Per the OpenClaw loading model, only
  `SKILL.md` is read by the runtime; `skill.py`/`__init__.py` are **not** auto-executed by OpenClaw.
- **`SKILL.md` is effectively empty** (title only). There are **no tool definitions, no frontmatter
  beyond `name`/`description`, no invocation instructions**. → OpenClaw cannot currently *do* anything
  with this skill.

### 3.2 How OpenClaw "invokes" the skill today

**It does not.** Two disconnected mechanisms exist, neither active:

1. `OpenclawClient.execute_skill()` (`openclaw_client.py:18`) POSTs to
   `{OPENCLAW_API_URL}/skills/{skill_name}/execute` with `{"action": ...}`. This endpoint shape does
   **not** match OpenClaw's real gateway API, and the caller path is gated behind `USE_OPENCLAW=False`.
   It also references the old name `"twenty_skill"` (`crm_service.py:27,40`), not `twenty-skill`.
2. `OpenClawService` (`openclaw_service.py`) is an **in-process** Python registry of agents — unrelated
   to the actual OpenClaw gateway container.

**Conclusion:** The current design predates the confirmed OpenClaw skill-loading model. `twenty-skill`
is a placeholder, not a functioning SDK.

---

## 4. Backend Communication, Endpoints, Request/Response

### 4.1 How the skill communicates with the backend

- Backend `TwentySkill`/`TwentyService` talk to **Twenty CRM REST** directly via `httpx`
  (`twenty_service.py:16`, `twenty_skill.py:88`). They do **not** talk to a backend "skill endpoint".
- The intended reverse direction (OpenClaw → backend, or backend → OpenClaw) exists only as the dead
  `OpenclawClient`.

### 4.2 Current backend endpoints (FastAPI, `main.py`)

| Prefix | Router file | Objects |
| ------ | ----------- | ------- |
| `/api/v1/candidates` | `api/candidate.py` | candidate CRUD + `/schedule`, `/evaluate-screening` |
| `/api/v1/requisitions` | `api/requistion.py` *(filename misspelled)* | requisition CRUD + `/parse-jd`, `/generate-jd` |
| `/api/v1/interviews` | `api/interview.py` | interview CRUD |
| `/api/v1/voice` | `api/voice.py` | ElevenLabs voice |
| `/api/v1/webhooks` | `api/webhook.py` | inbound webhooks |
| `/api/v1/health` | `api/health.py` | health |

### 4.3 Current request format (to Twenty CRM)

- REST calls to `{base}/rest/{plural}` and `{base}/rest/{plural}/{id}` (`twenty_service.py:18`).
- Structured fields hand-built inline: e.g. `email → {primaryEmail, additionalEmails}`,
  `phone → {primaryPhoneNumber,...}` (`twenty_service.py:60`, `twenty_skill.py:72`).
- Notes built as BlockNote JSON inline (`twenty_service.py:139`).

### 4.4 Current response format

- Raw Twenty envelope unwrapped ad-hoc: `response.get("data", {}).get("candidates", [])`,
  `.get("createCandidate", {})`, etc. (`twenty_service.py:49–116`). Inconsistent and duplicated per method.
- Errors: `TwentyService._request` raises generic `Exception(f"Twenty CRM Error: ...")`
  (`twenty_service.py:40`); routers convert to `HTTPException` with the raw string
  (`candidate.py:60`).

---

## 5. Assumptions About CRM Schema (Current vs Schema V2)

| Aspect | Current backend code | Schema V2 (target, `schema_utils.py`) |
| ------ | -------------------- | -------------------------------------- |
| Objects | candidate, requisition (as `requistion`), interview | candidate, requisition, application, interview, evaluation, offer |
| Central object | **candidate** (candidate-centric) | **application** (`"Candidate participation in a specific requisition"`) |
| Requisition plural | **`requistions`** (misspelled) | `requisitions` (correct) |
| Status field | `interviewStatus` on **candidate** (`twenty_skill.py:180`) | `requisitionStatus`, `application.stage`, `interviewStatus`, `offerStatus`, `evaluationStatus` on their own objects |
| Relationships | implicit `candidateId` on interview; requisitions linked by `listingId`/`candidateId` guesswork (`candidate.py:29`) | explicit FKs: application→candidate, application→requisition, interview→application, evaluation→interview, offer→application (`RELATIONSHIP_DEFINITIONS`) |
| Stages | none formalized | `application.stage`: APPLIED→SCREENING→…→HIRED/REJECTED (`schema_utils.py`) |
| Workflows | `"Candidate Status Change"` (invented name) | `"Recruiting V2 - Requisition Approval"`, `"… Application Stage Transition"`, `"… Interview Lifecycle"`, `"… Offer Lifecycle"` (`05_create_workflows.py`) |

---

## 6. Hardcoded Object Names & Legacy References (to remove)

| Legacy artifact | Location | Problem |
| --------------- | -------- | ------- |
| `"requistions"`, `"requistion"`, `createRequistion`, `updateRequistion` | `twenty_service.py:99–114`; `twenty_skill.py:22` (`"CRM uses requistions spelling"`) | Misspelled V1 name; V2 uses `requisitions`. |
| `api/requistion.py` (filename) | `backend/app/api/` | Misspelled router filename. |
| `_normalize_object_name` maps only candidate/requisition/interview/note/attachment/timeline | `twenty_skill.py:18`, `skill.py:21` | Missing application/evaluation/offer; hardcoded pluralization. |
| `interviewStatus` chosen when `object_name == "candidate"` | `twenty_skill.py:180`; `skill.py:213` | V2 has no candidate status; status belongs to application/interview/offer. |
| Workflow name `"Candidate Status Change"` | `scheduling_agent.py` | Not a V2 workflow name. |
| `target{Object}Id` note-link built by string concat | `twenty_skill.py:59`; `skill.py:120` | Fragile; assumes V1 note-target field names. |
| Requisition↔candidate join via `listingId`/`candidateId` | `candidate.py:29,47` | V2 joins are through `application`, not candidate↔requisition. |
| Duplicate `TwentySkill` in skill folder | `openclaw/skills/twenty-skill/skill.py` | Orphaned copy; drift risk. |
| `OpenclawClient` endpoint `/skills/{name}/execute` + name `"twenty_skill"` | `openclaw_client.py:19`; `crm_service.py:27,40` | Non-existent endpoint shape; stale skill name. |

---

## 7. Dependency Analysis

| Dependency | Used? | Evidence |
| ---------- | ----- | -------- |
| **FastAPI** | Yes (backend API host) | `main.py`, all routers. **Not** a dependency the *skill* itself should need. |
| **Twenty REST API** | **Yes — the only CRM transport** | `twenty_service.py:18` (`/rest/...`); `twenty_skill.py:88`; `schema_utils.py` (`/rest/metadata/...`). |
| **Twenty GraphQL** | No (record ops) | All record/metadata ops are REST. Note: `05_create_workflows.py` documents that workflow *authoring* is GraphQL-only, but the code does not call GraphQL. |
| **OpenClaw SDK** | No | No OpenClaw SDK import anywhere; only a bespoke `OpenclawClient` HTTP shim (dead). |
| **Local Python execution** | Skill folder ships `skill.py`/`__init__.py`, but OpenClaw does **not** execute them (loads `SKILL.md` only). | OpenClaw loading model (prior analysis). |
| **External libraries** | `httpx` (HTTP), `pydantic`/`pydantic-settings` (models/config), `python-dotenv`; agents also use `llm_service`, ElevenLabs. | `import httpx` across services; `settings.py`. |

---

## 8. Architecture Review

### 8.1 What should remain
- **REST-over-`httpx` transport to Twenty** — correct and sufficient; keep, but centralize.
- **Retry/backoff pattern** already in `schema_utils.TwentyClient` (`RETRYABLE_STATUS_CODES`, 3 attempts) — promote this into the skill client.
- **Schema V2 declarative definitions** (`schema_utils.py`) — reuse as the single source of truth for object/field/enum names in the skill (`metadata` module).
- **Structured-field builders** (email/phone/BlockNote note) — keep the logic, relocate into dedicated helpers.

### 8.2 What should be refactored
- Collapse `TwentyService` + backend `TwentySkill` + `CRMService` into **one** layered client inside `twenty-skill`.
- Replace ad-hoc response unwrapping with a **single response normalizer**.
- Replace inline object-name maps with a **metadata module derived from Schema V2**.
- Redefine status transitions around **`application.stage`** (central object), not `candidate.interviewStatus`.

### 8.3 What should be deleted
- `openclaw/skills/twenty-skill/skill.py` and `__init__.py` **as duplicated logic** (skill logic will be re-established properly; nothing in OpenClaw executes them today).
- `OpenclawClient` (`openclaw_client.py`) in its current form (wrong endpoint, dead path) — or rewrite against the real gateway later.
- All `requistion(s)` misspellings and the candidate-centric requisition join.

### 8.4 What should be modularized
- Per-object modules (candidate, requisition, application, interview, evaluation, offer).
- Cross-cutting: `client`, `config`, `auth`, `router`, `metadata`, `validators`, `exceptions`, `models`, `search`.

---

## 9. Proposed V2 Architecture

**Principle:** `twenty-skill` becomes a self-contained **CRM SDK** with one HTTP client, one config,
one error model, a Schema-V2-derived metadata layer, and thin per-object modules exposing a stable
public action API. Application is the hub object.

```
                        ┌─────────────────────────────┐
   caller (agent) ────► │ router.py  (action dispatch) │
                        └──────────────┬──────────────┘
              ┌────────────────────────┼─────────────────────────┐
        object modules            search.py                 metadata.py
   candidate/requisition/…            │                          │
              └──────────┬────────────┘                          │
                     validators.py ──► models.py                 │
                         │                                        │
                     client.py (httpx + retry + normalize) ◄──────┘
                         │            ▲
                     auth.py      exceptions.py
                         │
                     config.py (env)
                         │
                   Twenty CRM REST
```

---

## 10. Proposed Directory Layout (V2)

> **Only create files that are required for the refactor**, phase by phase (see §12). This is the
> *target* layout, not an instruction to scaffold everything now.

```
twenty-skill/
├── SKILL.md            # Real frontmatter + tool/action documentation for OpenClaw
├── skill.py            # Thin public entrypoint → delegates to router
├── config.py           # Env loading (TWENTY_API_URL/KEY), constants, timeouts
├── client.py           # Single httpx client: request(), retry, response normalize
├── auth.py             # Header/token construction (Bearer)
├── router.py           # Maps action strings ("candidate.create") → handlers
├── exceptions.py       # TwentySkillError hierarchy (NotFound, Validation, Transport…)
├── validators.py       # Input validation; enum/stage checks vs metadata
├── models.py           # Pydantic request/response models per object
├── metadata.py         # Schema-V2 object/field/enum registry (single source of truth)
├── search.py           # Cross-object query/filter helpers
├── utility.py          # Field builders (email/phone/BlockNote), pagination
├── candidate.py        # candidate.* actions
├── requisition.py      # requisition.* actions
├── application.py      # application.* actions (central object)
├── interview.py        # interview.* actions
├── evaluation.py       # evaluation.* actions
└── offer.py            # offer.* actions
```

**Note on OpenClaw execution model:** because OpenClaw reads `SKILL.md` (not Python) at load time, the
`SKILL.md` must be authored to describe the action surface (how the agent calls each action). Whether
these Python modules are executed *in-process by the backend* or *invoked via a gateway tool* is a
Phase-1 decision (see §13 Risks) — the module layout supports either.

---

## 11. Public API Design (naming convention)

**Convention:** `object.verb[_qualifier]`, lowercase, dot-namespaced, verbs from a fixed vocabulary
(`create`, `get`, `list`, `update`, `delete`, plus domain verbs). No underscores in the object segment
(matches OpenClaw skill-name rules and keeps parity with the renamed `twenty-skill`).

| Domain | Actions (design only — not implemented) |
| ------ | --------------------------------------- |
| metadata | `metadata.health`, `metadata.objects`, `metadata.fields`, `metadata.schema_version` |
| search | `search.candidates`, `search.applications`, `search.requisitions`, `search.by_stage` |
| candidate | `candidate.create`, `candidate.get`, `candidate.list`, `candidate.update`, `candidate.delete`, `candidate.add_note` |
| requisition | `requisition.create`, `requisition.get`, `requisition.list`, `requisition.update`, `requisition.approve`, `requisition.post`, `requisition.close` |
| application | `application.create`, `application.get`, `application.list`, `application.advance_stage`, `application.reject`, `application.set_decision` |
| interview | `interview.schedule`, `interview.get`, `interview.list`, `interview.confirm`, `interview.complete`, `interview.cancel` |
| evaluation | `evaluation.create`, `evaluation.get`, `evaluation.list`, `evaluation.finalize` |
| offer | `offer.create`, `offer.approve`, `offer.send`, `offer.mark_accepted`, `offer.mark_declined` |
| workflow | `workflow.list`, `workflow.trigger` (thin wrapper; no silent direct-PATCH fallback — see §13) |

**Stage/enum values** must be sourced from `metadata.py` (derived from `schema_utils.py`), e.g.
`application.advance_stage(stage="INTERVIEW_SCHEDULED")` validated against
`REQUIRED_SELECT_VALUES[("application","stage")]`.

---

## 12. Migration Plan (phased roadmap)

> Each phase is independently shippable and testable. Do **not** start Phase 3+ CRUD until Phase 1–2
> foundation is reviewed.

| Phase | Name | Deliverables | Depends on |
| ----- | ---- | ------------ | ---------- |
| **1** | Foundation | `config.py`, `client.py` (retry + normalize), `auth.py`, `exceptions.py`, `router.py` skeleton, real `SKILL.md` | — |
| **2** | Utility / Metadata / Health / Discovery | `metadata.py` (from Schema V2), `utility.py` (field builders), `metadata.health/objects/fields` actions | 1 |
| **3** | Candidate | `candidate.py` + `models` + validators; `candidate.*` actions | 1,2 |
| **4** | Requisition | `requisition.py`; `requisition.*` incl. approve/post/close | 1,2 |
| **5** | Application (central) | `application.py`; `application.*` incl. `advance_stage` using V2 stage enum | 1,2,3,4 |
| **6** | Interview | `interview.py`; `interview.schedule/confirm/complete/cancel` linked to application | 5 |
| **7** | Evaluation | `evaluation.py`; `evaluation.*` linked to interview | 6 |
| **8** | Offer | `offer.py`; `offer.*` linked to application | 5 |
| **9** | Search | `search.py`; cross-object queries/filters, stage-based search | 3–8 |
| **10** | Workflow | `workflow.trigger` mapped to the four V2 workflows; remove legacy silent PATCH fallback | 5,9 |

**Decommission (parallel, after parity reached):** delete backend `twenty_skill.py`, fold
`twenty_service.py` into the skill client, replace `CRMService` calls, remove `OpenclawClient`/rename
skill references, fix `requistion` spellings, add `application/evaluation/offer` routers.

---

## 13. Risks

1. **OpenClaw execution model gap (highest).** OpenClaw loads `SKILL.md`, not Python. The current
   `skill.py` is never executed by OpenClaw. **Before Phase 3**, decide the invocation contract:
   (a) backend imports the `twenty-skill` package in-process, or (b) OpenClaw invokes it via a defined
   gateway tool/command described in `SKILL.md`. Everything downstream depends on this.
2. **Central-object inversion.** Moving from candidate-centric to application-centric changes every
   status transition and join. Existing agents (`scheduling_agent` writes `candidate.interviewStatus`)
   must be re-pointed to `application.stage`.
3. **Legacy spelling in live data.** If any Twenty objects were actually created as `requistions`,
   renaming to `requisitions` requires a data/metadata migration, not just code edits. **Verify against
   the running Twenty instance before changing plurals.**
4. **Workflow authoring is GraphQL-only** (`05_create_workflows.py`): V2 workflows are draft records
   without steps. `workflow.trigger` cannot rely on published transitions yet; the old silent
   direct-PATCH fallback (`twenty_skill.py:180`) must **not** be carried over (Schema V2 script
   explicitly forbids it).
5. **Duplication drift.** Three CRM abstractions today; partial migration could create a fourth. Enforce
   a single client from Phase 1.
6. **Response-shape coupling.** Ad-hoc `.get("createX")` unwrapping is brittle across Twenty versions;
   centralize in `client.py` normalizer.

---

## 14. Implementation Order (summary)

```
Phase 1  Foundation        → config, client(retry+normalize), auth, exceptions, router, SKILL.md
Phase 2  Metadata/Health   → metadata (from Schema V2), utility builders, discovery actions
Phase 3  Candidate         → candidate.* CRUD
Phase 4  Requisition       → requisition.* (+approve/post/close)
Phase 5  Application       → application.* (advance_stage — central hub)
Phase 6  Interview         → interview.* (linked to application)
Phase 7  Evaluation        → evaluation.* (linked to interview)
Phase 8  Offer             → offer.* (linked to application)
Phase 9  Search            → cross-object queries
Phase 10 Workflow          → workflow.trigger (V2 workflows; no legacy PATCH fallback)
Decommission (parallel)    → remove backend TwentySkill/CRMService/OpenclawClient, fix `requistion`
```

---

## 15. Conclusion

The current `twenty-skill` is **not yet a functioning CRM SDK**: it is an inert OpenClaw skill
(`SKILL.md` metadata only) plus a duplicated backend class, layered over a **candidate-centric,
Schema-V1** data model that uses the misspelled `requistions` name and lacks the `application`,
`evaluation`, and `offer` objects central to Schema V2. FastAPI currently bypasses OpenClaw entirely
(`USE_OPENCLAW=False`).

The V2 refactor should establish a single, layered SDK inside `twenty-skill`, derive all object/field/
enum names from the Schema V2 definitions, re-center transitions on `application.stage`, and expose a
clean `object.verb` action API — delivered in the ten phases above, with the OpenClaw invocation
contract resolved in Phase 1 before any CRUD is written.

**No CRUD operations were implemented in this task, as instructed.**

---

### Appendix A — Source reference index

| Claim | File | Symbol / line |
| ----- | ---- | ------------- |
| Skill `SKILL.md` is metadata-only | `openclaw/skills/twenty-skill/SKILL.md` | 6 lines, `name`/`description` only |
| Orphaned skill copy | `openclaw/skills/twenty-skill/skill.py` | `class TwentySkill` |
| Backend duplicate | `backend/app/services/twenty_skill.py` | `class TwentySkill` |
| `requistions` spelling | `backend/app/services/twenty_service.py` | `get_requisitions` L99–114 |
| Legacy normalize map | `backend/app/services/twenty_skill.py` | `_normalize_object_name` L18 |
| Candidate-status assumption | `backend/app/services/twenty_skill.py` | `status_field = "interviewStatus"` L180 |
| CRM switch flag | `backend/app/services/crm_service.py` | `use_openclaw` L13 |
| Flag default False | `backend/app/settings.py` | `USE_OPENCLAW: bool = False` L34 |
| Dead OpenClaw client | `backend/app/services/openclaw_client.py` | `execute_skill` L18 |
| In-process agent bridge | `backend/app/agents/openclaw_service.py` | `OpenClawService` |
| Live routers | `backend/app/main.py` | L34–39 |
| Schema V2 objects | `scripts/schema_v2/schema_utils.py` | `V2_OBJECTS`, `OBJECT_DEFINITIONS` |
| Application = central | `scripts/schema_v2/schema_utils.py` | application `description` |
| V2 relationships | `scripts/schema_v2/schema_utils.py` | `RELATIONSHIP_DEFINITIONS` |
| V2 workflows (draft, GraphQL-only) | `scripts/schema_v2/05_create_workflows.py` | `WORKFLOW_NAMES`, warning |
```
