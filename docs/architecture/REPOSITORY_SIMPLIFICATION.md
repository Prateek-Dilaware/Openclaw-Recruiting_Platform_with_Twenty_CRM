# Repository Simplification — Phase 1.1

**Date:** 2026-07-15
**Phase:** 1.1 (pre-implementation cleanup for AI Recruiting Platform V2)
**Principle:** Delete dead code, not deprecate it. Git history is the archive. The active repository
should reflect the **future** architecture, not carry obsolete implementations.

**Reference source of truth (accepted, not re-investigated):**
`SKILL_LOADING_ANALYSIS.md`, `TWENTY_SKILL_V2_AUDIT.md`, `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md`
(in `CRM/Reports/openclaw_skill_reports/`).

---

## 1. Summary

Removed the abandoned "backend routes CRM through the OpenClaw gateway" architecture and one duplicate
skill implementation. Every deletion was preceded by a full import/reference/runtime trace. The backend
still imports, builds, and starts. **Docker, Schema V2, React, OpenClaw runtime/config, and the working
`TwentyService` REST implementation were not touched.**

| Metric | Result |
| ------ | ------ |
| Files deleted | 4 (2 backend modules + 2 duplicate skill files) |
| Files simplified | 4 (`crm_service.py`, `settings.py`, `backend/.env.example`, `docs/configuration.md`) |
| Backend import check | ✅ `import app.main` OK, 12 routes |
| Broken imports | None |
| Circular imports | None |
| CRMService live path | `TwentySkill` only (`openclaw_client` attribute gone) |

---

## 2. Deleted Files

| File | Contained | Why safe to delete |
| ---- | --------- | ------------------ |
| `backend/app/agents/openclaw_service.py` | `class OpenClawService` (in-process agent registry) | **Zero importers** (grep confirmed only its own definition). Not connected to the real OpenClaw gateway (per `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md`). Never instantiated anywhere in the runtime. |
| `backend/app/services/openclaw_client.py` | `class OpenclawClient` (`execute_skill`) | Only referenced by the dead `USE_OPENCLAW=True` branch in `CRMService`. Targeted a **non-existent** endpoint `POST /skills/{name}/execute` (`TWENTY_SKILL_V2_AUDIT.md` §3, `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md` §8). Once the branch was removed, it had zero references. |
| `openclaw/skills/twenty-skill/skill.py` | `class TwentySkill` (duplicate) | **Orphaned duplicate** of `backend/app/services/twenty_skill.py`. OpenClaw loads only `SKILL.md`, never executes skill Python (`SKILL_LOADING_ANALYSIS.md`, `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md` §4). No importers. Carries no unique logic (the backend copy is retained). |
| `openclaw/skills/twenty-skill/__init__.py` | Package marker comment only | Part of the orphaned duplicate; not read by OpenClaw. |

> `openclaw/skills/twenty-skill/SKILL.md` was **kept** — it is the live, loaded skill (source
> `openclaw-managed`, verified `✓ ready`).

---

## 3. Deleted Classes / Services

| Symbol | Location (removed) | Role in abandoned architecture |
| ------ | ------------------ | ------------------------------ |
| `OpenClawService` | `agents/openclaw_service.py` | Fake in-process "OpenClaw" agent/skill registry. |
| `OpenclawClient` | `services/openclaw_client.py` | HTTP shim to a non-existent gateway skill-execute endpoint. |
| `TwentySkill` (duplicate) | `openclaw/skills/twenty-skill/skill.py` | Copy of the backend class; never executed. |

---

## 4. Deleted / Removed Configuration

| Config | Removed from | Notes |
| ------ | ------------ | ----- |
| `USE_OPENCLAW` | `settings.py`, `crm_service.py` (routing), `backend/.env.example`, `docs/configuration.md` | Feature flag for the abandoned gateway-routing path. Defaulted `False`; the `True` branch never functioned. |
| `OPENCLAW_API_URL` | `settings.py`, `backend/.env.example`, `docs/configuration.md` | Only consumed by the deleted `OpenclawClient`. |
| `OPENCLAW_API_KEY` | `settings.py`, `backend/.env.example`, `docs/configuration.md` | Only consumed by the deleted `OpenclawClient`. |

**Kept intentionally:**
- `OPENCLAW_URL` — still used by `llm_service.py` for the OpenClaw **LLM provider** path
  (`LLM_PROVIDER=openclaw`). This is unrelated to CRM execution routing.
- `backend/.env` (real developer secrets file) — **not modified**. It may still contain the obsolete
  keys; they are now ignored (`extra = "ignore"` in `Settings.Config`). Remove them manually if desired.
- `docker/.env.example` and `docker/archive/*` — **not touched** (Docker is out of scope per the task).

---

## 5. Files Simplified (not deleted)

### `backend/app/services/crm_service.py`
- Removed the `use_openclaw` flag read, the lazy `OpenclawClient` import, and both `if self.use_openclaw:`
  branches in `write_field` / `trigger_workflow`.
- `CRMService` now always uses `TwentySkill` (the direct Twenty CRM path). Public method signatures are
  unchanged, so all callers (`interview_agent`, `scheduling_agent`, `webhook.py`) keep working.

### `backend/app/settings.py`
- Removed `USE_OPENCLAW`, `OPENCLAW_API_URL`, `OPENCLAW_API_KEY`. Kept `OPENCLAW_URL` (LLM provider).

### `backend/.env.example` and `docs/configuration.md`
- Removed the "OpenClaw Integration" env block and the corresponding documentation rows for the three
  deleted keys.

---

## 6. Kept — Still Valuable for V2

| Component | Reason |
| --------- | ------ |
| `backend/app/services/twenty_service.py` (`TwentyService`) | **Explicitly kept.** Working Twenty REST implementation that will become the basis of the CRM SDK. Not redesigned/rewritten in this phase. |
| `backend/app/services/twenty_skill.py` (`TwentySkill`) | **Kept.** Still the live path used by `CRMService`, and holds notes/workflow REST logic slated to migrate into the CRM SDK. **See §7 — deleting it now would break the backend.** |
| `backend/app/services/crm_service.py` (`CRMService`) | Kept (simplified). Live dependency of agents + webhook. |
| `backend/app/agents/*` (`jd_agent`, `interview_agent`, `scheduling_agent`, `retrospective_agent`) | **Kept.** Still wired into live API routes (`candidate.py`, `requistion.py`, `webhook.py`, `health.py`). See §7. |
| `backend/app/services/{llm_service, elevenlabs_service, retrospective_job}.py` | Live dependencies of agents/routers. |
| `backend/app/api/*`, `models/*`, `utils/*`, `main.py`, `settings.py` | Active FastAPI surface. |
| `openclaw/skills/twenty-skill/SKILL.md` | The live, loaded OpenClaw skill. |
| Schema V2 (`scripts/schema_v2/*`), Docker, React, OpenClaw runtime/config | Out of scope — untouched. |

---

## 7. Deletions Deliberately NOT Performed (with reason)

The task's example deletion list included `backend/app/services/twenty_skill.py` and implied removing
backend AI agents ("there are no backend AI agents anymore"). **These were kept**, because the task also
requires: *"If any deletion cannot be safely completed because it still has runtime dependencies, stop,
explain why, and leave that component in place rather than breaking the project"* and *"Do NOT delete
code that still contains valuable implementation logic that will be migrated into the CRM SDK."*

| Component | Why NOT deleted now | Live references (traced) |
| --------- | ------------------- | ------------------------ |
| `services/twenty_skill.py` (`TwentySkill`) | Still the **only** live CRM write/workflow path via `CRMService`; contains logic to migrate into the CRM SDK. | `crm_service.py` (import + instantiation + both methods). |
| `agents/scheduling_agent.py` | Bound to a live route. | `api/candidate.py` (`/schedule`), `api/webhook.py`. |
| `agents/interview_agent.py` | Bound to live routes. | `api/candidate.py` (`/evaluate-screening`, transcript/eval endpoints), `api/webhook.py`. |
| `agents/jd_agent.py` | Bound to live routes. | `api/requistion.py` (`/parse-jd`, `/generate-jd`), `api/webhook.py`. |
| `agents/retrospective_agent.py` | Bound to a live route. | `api/candidate.py` (`/{id}/retrospective`). |
| `services/retrospective_job.py` | Bound to a live route. | `api/health.py` (`/run-retrospective`). |

> These belong to the current (still-serving) recruiting flow. Removing them is a **later phase**
> (once the CRM SDK + OpenClaw tool plugin replace them per `TWENTY_SKILL_V2_AUDIT.md`). Deleting them
> in Phase 1.1 would break running API endpoints — outside this phase's scope and explicitly guarded
> against by the task rules.

---

## 8. Remaining Architecture (after Phase 1.1)

```
React → FastAPI → CRMService/TwentySkill + TwentyService → Twenty CRM REST → PostgreSQL
                     (agents still serve current recruiting endpoints)
OpenClaw runtime ← twenty-skill/SKILL.md (instruction pack; execution via tools — future)
LLM: llm_service (gemini/openai/openrouter/openclaw via OPENCLAW_URL)
```

**Removed from the picture:** the `USE_OPENCLAW` gateway-routing branch, `OpenclawClient`,
`OpenClawService`, and the duplicate skill `TwentySkill`.

---

## 9. What Remains to Migrate (future phases)

Per `TWENTY_SKILL_V2_AUDIT.md` and `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md`:

1. **CRM SDK**: fold `TwentyService` (+ the useful notes/workflow logic in `TwentySkill`) into a single
   layered CRM SDK, application-centric, aligned to Schema V2 (correct `requisitions` spelling, 6
   objects).
2. **OpenClaw tool plugin (Option D / hybrid)**: expose CRM actions as typed tools via `defineToolPlugin`
   + a real `SKILL.md` instruction pack.
3. **Retire backend agents** once OpenClaw becomes the sole AI runtime and the API routes are re-pointed
   at the SDK/tool surface.
4. Fix the misspelled `requistion(s)` naming and add `application`/`evaluation`/`offer` routers.

---

## 10. Verification Performed

| Check | Command | Result |
| ----- | ------- | ------ |
| Syntax of all backend files | `python -m py_compile` (recursive over `app/`) | ✅ `SYNTAX OK: all backend .py files compiled` |
| Full live import graph | `python -c "import app.main"` | ✅ `IMPORT OK: app.main loaded`, 12 routes |
| CRMService live path | `CRMService()` attributes | ✅ `has twenty_skill: True | has openclaw_client: False` |
| No leftover dead symbols in code | grep `OpenclawClient|OpenClawService|USE_OPENCLAW|...` in `backend/app` | ✅ only the explanatory docstring in `crm_service.py` |
| Docker | (not touched) | ✅ unchanged |
| Schema V2 / React / OpenClaw config | (not touched) | ✅ unchanged |

- **No broken imports.**
- **No circular imports.**
- **No missing configuration** (`OPENCLAW_URL` retained for the LLM path; obsolete keys ignored via
  `extra = "ignore"`).
- **No runtime failures** on import/startup.

---

*Every deletion in this document was made only after tracing imports, references, and runtime usage.
Components with live runtime dependencies or migratable logic were retained and are listed in §6–§7.*
```
