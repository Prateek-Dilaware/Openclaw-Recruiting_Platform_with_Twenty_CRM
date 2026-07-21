# Planner Alignment Audit — `main` Agent vs. Recruiting-Typed Tools

**Date:** 2026-07-20
**Status:** ANALYSIS ONLY — no code, prompt, config, or doc was modified.
**Question:** Does the current `main` agent's planning surface naturally prefer
the new typed recruiting tools, or does it still steer toward generic CRUD?

---

## 0. TL;DR

**The planner is currently mis-aligned.** Every recruiting skill instructs the
model to write through two abstractions — `crm.write_field()` (→
`twenty_record_update`) and `crm.trigger_workflow()` (→ `twenty_workflow_run`).
**None of the skills, examples, or workspace docs mention the 18 typed
recruiting tools.** So the planner will keep choosing generic
`twenty_record_update` for informational writes — the exact opaque-`data` path
that motivated the typed tools. The typed tools are live and correct, but the
*instructions the planner reads* have not caught up.

SOUL.md / AGENTS.md / TOOLS.md are essentially neutral (no misalignment); the
work is concentrated in the `crm` skill + the per-domain recruiting skills +
their examples.

---

## 1. Current planner flow (how `main` selects tools today)

1. **Startup context** injects `AGENTS.md`, `SOUL.md`, `USER.md`, recent
   `memory/*.md`, and (main session) `MEMORY.md`. None reference specific CRM
   tools — they set posture/guardrails.
2. **Skill selection.** For a recruiting request the model loads the relevant
   skill (`candidate`, `resume`, `jd`, `interview`, `evaluation`, `scheduling`,
   `communication`, `research`, `retrospective`) which all delegate CRM writes
   to the **`crm` skill**.
3. **`crm` skill defines the write boundary** as exactly two procedures:
   - `write_field()` → "call `twenty_record_update` with only non-state data"
   - `trigger_workflow()` → "call `twenty_workflow_run`"
4. **Tool selection.** With that instruction in context, the planner emits
   `twenty_record_update` (generic) for any informational write and
   `twenty_workflow_run` for lifecycle. It has **no signal** that
   `candidate_update_contact`, `application_create`, etc. exist or are
   preferred.
5. **Tool descriptions** (the plugin-level text the planner also sees) DO
   describe the typed tools well, but the **skill instructions override intent**
   — the model follows the explicit procedure it was told to use.

Net: two competing signals — good typed-tool descriptions vs. explicit
skill instructions naming the generic tool. **The explicit instruction wins.**

---

## 2. Misalignment findings by severity

### 🔴 Critical

- **C1 — `crm/SKILL.md` names the generic tools as the write path.**
  Lines: "Create/update non-state data through `twenty_record_create` and
  `twenty_record_update`." and "Treat `write_field()` as … call
  `twenty_record_update` with only non-state-changing data." This directly
  steers the planner to the opaque generic tool over the typed tools.
- **C2 — No recruiting skill mentions any typed recruiting tool.** Grep across
  `openclaw/workspaces/default/**` finds **zero** references to
  `candidate_*`, `application_*`, `interview_*`, `evaluation_*`, `offer_*`,
  `requisition_*`, or `recruiting_add_note`. The planner cannot prefer tools it
  is never told about.

### 🟠 High

- **H1 — `crm/examples/README.md` demonstrates the generic path.** "Call
  `twenty_record_update` with only `{ parsedResumeSummary: … }`." A few-shot
  example is a strong planner signal; it actively teaches the wrong tool
  (`application_set_resume_summary` now exists).
- **H2 — `crm/references/operation-contract.md` "Plugin facts" only mentions
  "generic record tools + workflow execution."** It omits the typed recruiting
  surface, reinforcing generic-CRUD as the sanctioned path.
- **H3 — Note attachment guidance is generic.** `candidate` skill + memory
  reference building `noteTarget` via generic create; `recruiting_add_note`
  (the reliable two-step tool) is not referenced.

### 🟡 Medium

- **M1 — Lifecycle ambiguity is now three-way.** Skills say lifecycle →
  `twenty_workflow_run`. The plugin also exposes typed `*_set_stage` /
  `*_set_status` setters (approval-gated) AND generic `twenty_record_update`.
  The skill text doesn't acknowledge the typed setters, so their role is
  undefined for the planner (should it use them, or always workflows?).
- **M2 — Per-domain skills route everything through `crm.write_field()`.**
  `resume`, `evaluation`, `interview`, `jd`, `communication` all say "store via
  `crm.write_field()`." Each has a natural typed target now
  (`application_set_resume_summary`, `evaluation_create/finalize`,
  `interview_schedule`, `requisition_update`, `recruiting_add_note`).
- **M3 — Stale memory fragment.** `memory/2026-07-19-1319.md` reasons about
  using generic `twenty_record_create` for a `noteTarget`. Memory is planner
  context in main sessions; it can reinforce the generic pattern.

### 🟢 Low

- **L1 — `TOOLS.md` references `twenty-skill`** (an older skill name) and
  "twenty-openclaw plugin … only" — accurate but doesn't point at the typed
  recruiting surface. Minor.
- **L2 — SOUL.md / AGENTS.md** are tool-agnostic and correct; no change needed
  beyond optionally noting the typed-tool preference in AGENTS "lessons."
- **L3 — `skills/README.md`** repeats "twenty_record_update is used only for
  non-state information" — consistent with C1; low on its own.

---

## 3. Exact files requiring updates (no edits applied)

| File | Finding(s) | Priority |
|---|---|---|
| `openclaw/workspaces/default/skills/crm/SKILL.md` | C1, M1 | Critical |
| `openclaw/workspaces/default/skills/crm/examples/README.md` | H1 | High |
| `openclaw/workspaces/default/skills/crm/references/operation-contract.md` | H2, M1 | High |
| `openclaw/workspaces/default/skills/candidate/SKILL.md` (+ examples) | C2, H3 | High |
| `openclaw/workspaces/default/skills/resume/SKILL.md` | M2 | Medium |
| `openclaw/workspaces/default/skills/evaluation/SKILL.md` | M2 | Medium |
| `openclaw/workspaces/default/skills/interview/SKILL.md` | M2 | Medium |
| `openclaw/workspaces/default/skills/jd/SKILL.md` | M2 | Medium |
| `openclaw/workspaces/default/skills/communication/SKILL.md` | M2 | Medium |
| `openclaw/workspaces/default/skills/scheduling/SKILL.md` | M1/M2 | Medium |
| `openclaw/workspaces/default/skills/README.md` | L3 | Low |
| `openclaw/workspaces/default/TOOLS.md` | L1 | Low |
| `openclaw/workspaces/default/AGENTS.md` | L2 (optional lesson) | Low |

(Do NOT edit `memory/*.md` retroactively — treat M3 as informational; memory is
a log.)

---

## 4. Recommended edits (proposals — not applied)

### `crm/SKILL.md` (C1, M1)
- Replace "Create/update non-state data through `twenty_record_create` and
  `twenty_record_update`" with: *"For recruiting records, prefer the typed
  recruiting tools (`candidate_*`, `requisition_*`, `application_*`,
  `interview_*`, `evaluation_*`, `offer_*`, `recruiting_add_note`). Use generic
  `twenty_record_*` only for objects with no typed tool, after metadata
  validation."*
- Reframe `write_field()` as: "prefer the matching typed tool; fall back to
  `twenty_record_update` only when no typed tool covers the field."
- Add a short **decision rule** (see §6) at the top of the write boundary.
- Clarify M1: lifecycle SELECT changes → `twenty_workflow_run` when an approved
  workflow exists; the typed `*_set_*` setters are the **approval-gated
  fallback** when no workflow is wired. State one order explicitly.

### `crm/examples/README.md` (H1)
- Replace the `twenty_record_update({parsedResumeSummary})` example with
  `application_set_resume_summary({ applicationId, summary })`.

### `crm/references/operation-contract.md` (H2)
- Expand "Plugin facts" to list the typed recruiting tools and state they are
  the preferred write surface; generic record tools are the escape hatch.

### Per-domain skills (C2, H3, M2)
- `candidate`: point create/update at `candidate_create`,
  `candidate_update_contact`, `candidate_update_profile`; notes at
  `recruiting_add_note`.
- `resume`: `application_set_resume_summary`.
- `evaluation`: `evaluation_create` + `evaluation_finalize`.
- `interview`: `interview_schedule` + `interview_set_status`.
- `jd`: `requisition_create` / `requisition_update`.
- `communication`: `recruiting_add_note` for stored notes/drafts.
- `scheduling`: `interview_schedule` (create) / workflow for reschedule/cancel.

### `TOOLS.md` (L1)
- Update the CRM note to reference the maintained plugin + typed recruiting
  tools; drop the stale `twenty-skill` name.

---

## 5. Suggested few-shot examples (for the skills — proposals)

Add compact, correct examples so the planner has demonstrations:

**Update candidate email**
> 1. Resolve the candidate id.
> 2. Call `candidate_update_contact({ candidateId, email })`.
> 3. Report the verification block returned by the tool.

**Store a parsed resume summary**
> 1. Resolve the application id.
> 2. Call `application_set_resume_summary({ applicationId, summary })`.
> 3. Re-read and report.

**Attach a note to a candidate**
> 1. Resolve the candidate id.
> 2. Call `recruiting_add_note({ targetType: "candidate", targetId, markdown })`.
> 3. Confirm `verification.linked.ok`.

**Create an application**
> 1. Resolve candidate + requisition ids.
> 2. Call `application_create({ candidateId, requisitionId, stage: "APPLIED" })`.

**Advance a stage (lifecycle)**
> 1. Prefer the approved workflow: inspect + `twenty_workflow_run`.
> 2. If no workflow is wired and policy permits, `application_set_stage(
>    { applicationId, stage })` (approval-gated).

**Record + finalize an evaluation**
> 1. `evaluation_create({ interviewId, evaluationType: "INTERVIEW", … })`.
> 2. After human decision: `evaluation_finalize({ evaluationId, recommendation })`.

---

## 6. Prompt change to make the planner prefer typed tools

Add a single **decision rule** near the top of the `crm` skill (and echo one
line in `AGENTS.md` lessons):

> **CRM write decision rule:**
> 1. Is it a **lifecycle** SELECT change (stage/status)? → approved
>    **workflow** (`twenty_workflow_run`); typed `*_set_*` setter only as the
>    approval-gated fallback.
> 2. Is there a **typed recruiting tool** for this object/field
>    (`candidate_*`, `application_*`, `interview_*`, `evaluation_*`, `offer_*`,
>    `requisition_*`, `recruiting_add_note`)? → **use it**.
> 3. Otherwise → generic `twenty_record_update` after metadata validation.
> Never hand-build `emails`/`phones`/`noteTarget` payloads — the typed tools do
> that.

A crisp 3-step rule collapses the decision and removes the "which tool?"
ambiguity that currently causes over-reasoning.

---

## 7. Latency / reasoning-depth optimizations

- **L-Opt 1 — Fewer choices = shorter planning.** The typed tools + the 3-step
  rule let the planner pick in one hop instead of reasoning about generic
  `data` shape + metadata. (Pairs with the future recruiter allow-list, which
  removes ~136 irrelevant tools from context.)
- **L-Opt 2 — Kill the metadata pre-flight for known writes.** Skills currently
  say "discover metadata when fields are not verified." For the typed tools the
  schema is baked in, so metadata discovery is unnecessary — remove that step
  from the typed-write path to cut a round trip.
- **L-Opt 3 — Trim per-skill duplication.** All nine skills repeat the same
  `write_field()`/`trigger_workflow()` boilerplate. Centralize the write rule in
  `crm` and have others reference it, reducing repeated prompt tokens.
- **L-Opt 4 — Prune stale memory.** Large `memory/*.md` files (esp. the
  2026-07-19 one reasoning about generic `noteTarget`) add tokens and a
  wrong-pattern signal in main sessions; curate them.

---

## 8. Readiness checklist for a dedicated `recruiter` agent

| # | Gate | Status |
|---|---|---|
| 1 | Typed recruiting tools implemented + live-verified | ✅ done (18 tools, 20/20) |
| 2 | `crm` skill prefers typed tools over generic CRUD | ❌ not yet (C1) |
| 3 | Recruiting skills reference their typed tools | ❌ not yet (C2/M2) |
| 4 | Examples demonstrate typed tools | ❌ not yet (H1) |
| 5 | Operation contract lists typed surface | ❌ not yet (H2) |
| 6 | Single documented CRM write decision rule | ❌ not yet (§6) |
| 7 | Lifecycle path (workflow vs typed setter) disambiguated | ❌ not yet (M1) |
| 8 | Tool allow-list for recruiter designed | ✅ done (allow-list audit) |
| 9 | Recruiter agent config designed | ✅ done (agent design) |
| 10 | Latency optimizations identified | ✅ done (§7) |

**Verdict:** The **tooling** is ready; the **planner instruction layer is
not**. Recommend completing gates 2–7 (skill/example/contract edits + the
decision rule) BEFORE standing up the dedicated `recruiter` agent — otherwise
the recruiter would inherit the same generic-CRUD bias, just with fewer tools.

---

## 9. What was NOT changed

No skill, prompt, SOUL/AGENTS/TOOLS, example, operation contract, workspace
config, memory, or plugin file was modified. This document is analysis only.
