# Write & Update Strategy Analysis

**Date:** 2026-07-20
**Status:** Decision analysis — no implementation performed. Every conclusion is cited to source.
**Scope:** Determine the best engineering solution for the recurring `data: {}` failure on
recruiting write/update operations through the Twenty plugin, and choose one architecture for **this**
project.

---

## 0. Executive Summary

- **Root cause (high confidence):** The generic `twenty_record_update` (and `twenty_record_create`)
  tools expose a **structurally opaque parameter schema** — `data: Type.Object({}, { additionalProperties: true })`
  with **no declared properties**. Nothing in the tool contract tells the model that fields like
  `emails` and `phones` are **nested composite objects**. When a model has to *invent* a nested wire
  shape from metadata on every call, some providers/turns drop the nested object and emit `data: {}`.
  This is confirmed by the plugin source (`records.js:151`) and by OpenClaw's own post-mortem
  (`docs/openclaw_self_given_report/updation_issues.md`): the *intent* was a correct nested
  `{ emails: { primaryEmail } }`, but the *emitted* tool call was `data: {}`.
- **The failure is not uniform — it is structural.** Flat writes with scalar/ID fields succeed
  (`noteTargets` with `noteId` + `targetCandidateId`); **nested composite writes** (`emails`, `phones`)
  collapse. This is the single most important diagnostic fact.
- **It is not** a Twenty bug, not an auth/permission problem, not an OpenClaw routing failure, and not
  the plugin's HTTP layer. The plugin forwards `params.data` unchanged (`records.js` update `run`), so an
  empty body means the model produced an empty body.
- **Recommended architecture (Option B/C hybrid):** Keep **all** read tools and keep the generic
  create/update as an escape hatch, but **add a small set of recruiting-aware, strongly-typed write
  tools** (`candidate_update_contact`, `candidate_add_note`, `application_create`, …). Put them in a
  **new, separate recruiting tool plugin** (`defineToolPlugin`) that calls the Twenty REST API — not
  inside the vendored `@lacneu/twenty-openclaw` package. This maximizes reliability and AI-friendliness
  while preserving upgrade safety.
- **Immediate stop-gap (hours, not days):** extend the existing patch
  (`tests/openclaw/patch_twenty_metadata_compatibility.mjs`) to reject an empty PATCH body on
  `twenty_record_update` (mirroring the `minProperties: 1` guard already added to create), so an empty
  update **fails loudly** instead of silently touching `updatedAt`.

---

## 1. Evidence Base

All file paths are relative to the workspace root unless prefixed with the OpenClaw repo. The installed
plugin lives under the git-ignored runtime state:
`openclaw/data/npm/projects/…/node_modules/@lacneu/twenty-openclaw/dist/`.

### 1.1 The generic update tool schema is opaque (primary evidence)

`…/dist/tools/records.js` — `RecordUpdateSchema`:

```js
const RecordUpdateSchema = Type.Object({
    entity: Type.String({ /* plural name */ }),
    id: Type.String({ description: "Record UUID to update" }),
    data: Type.Object({}, {
        additionalProperties: true,
        description: "Record fields to patch. PATCH semantics — only supplied fields " +
            "are modified. Schema depends on the entity (see `twenty_metadata_fields_list`).",
    }),
});
```

- `data` has **zero declared properties**. The model receives no structural hint that `emails` is
  `{ primaryEmail, additionalEmails }` or that `phones` is
  `{ primaryPhoneNumber, primaryPhoneCountryCode, primaryPhoneCallingCode, additionalPhones }`.
- `twenty_record_create` was already hardened by the local patch to add `minProperties: 1`
  (`patch_twenty_metadata_compatibility.mjs`), **but `twenty_record_update` has no such guard** — a PATCH
  with `data: {}` is accepted and forwarded.
- The update `run` forwards the body verbatim:

  ```js
  run: async (params, c, signal) => {
      assertValidEntity(params.entity);
      const resp = await c.request("PATCH", `/rest/${params.entity}/${encodeURIComponent(params.id)}`,
          { body: params.data, signal });
      return unwrapSingleKeyed(resp);
  },
  ```

  There is **no transformation** between the model's arguments and the HTTP body. An empty body
  therefore originates upstream, in the tool-call arguments — exactly as the investigation stated.

### 1.2 The entity-specific tools are strongly typed (the contrast)

`…/dist/tools/people.js` — `twenty_people_update` uses a **typed nested schema**:

```js
const PersonEmailsSchema = Type.Object({
    primaryEmail: Type.Optional(Type.String({ format: "email" })),
    additionalEmails: Type.Optional(Type.Array(Type.String({ format: "email" }))),
});
const PersonUpdateSchema = Type.Object({
    id: Type.String(),
    name: Type.Optional(PersonNameSchema),
    emails: Type.Optional(PersonEmailsSchema),
    jobTitle: Type.Optional(Type.String()),
    city: Type.Optional(Type.String()),
    companyId: Type.Optional(Type.String()),
});
```

This is the difference that matters: `twenty_people_update` **shows the model the nested shape**;
`twenty_record_update` hides it behind an empty object. A grep across the whole plugin for
`primaryPhoneNumber` / `PhonesSchema` returns **zero matches** — even the typed people tool never
models `phones`, and the custom recruiting objects (candidate/application/…) have **no typed tool at
all**. Every recruiting write must go through the opaque generic tool.

### 1.3 OpenClaw's own post-mortem confirms the mechanism

`docs/openclaw_self_given_report/updation_issues.md`:

- Intended call: `data: { emails: { primaryEmail: "…", additionalEmails: [] } }`.
- Actual emitted calls: `data: {}` (repeatedly).
- The **note write succeeded** because it was modeled as *separate flat records*:
  `notes` (create) then `noteTargets` with flat scalar IDs `{ noteId, targetCandidateId }`.
- The model's own conclusion: "the email/phone failures were … caused by me sending empty update
  bodies … For the note operation, I inspected the relationship model first, sent complete arguments."

This is decisive: the **same model, same session, same plugin** succeeded on flat writes and failed on
nested composite writes. The variable that changed is **payload structure**, which is governed by the
**tool schema**.

### 1.4 The runtime validates against the schema — an opaque schema validates nothing

`OPENCLAW_TOOL_RUNTIME_ANALYSIS.md` §2 documents the dispatch path:
`prepareToolCall` → `validateToolArguments` (against the TypeBox `parameters`) → `tool.execute`.

Because `data` is `Type.Object({}, { additionalProperties: true })`, **`{}` is a fully valid value**.
Validation cannot catch the mistake, and (pre-patch) neither can the tool body. The runtime is behaving
correctly; the contract is simply too loose to protect the operation.

### 1.5 Existing local infrastructure (reused by the recommendation)

- `tests/openclaw/patch_twenty_metadata_compatibility.mjs` — monkey-patches the installed plugin
  (metadata envelope fix, create empty-body guard, POST no-retry, debug logging of `fieldCount`).
- `tests/openclaw/validate_twenty_plugin.ps1` — applies the patch, then runs the contract tests.
- `tests/openclaw/test_twenty_write_contract.mjs` — asserts create rejects `{}` without a network call,
  forwards a populated body once, and does not retry POST.
- `docs/twenty_metadata_compatibility.md` — records that the package sits under git-ignored
  `openclaw/data/`, so **manual edits are not durable across a plugin reinstall**; the patch script is
  re-run after each reinstall.

**Implication:** we already own a supported, tested seam for changing the plugin's behavior without
forking it, and a separate plugin is the clean home for new tools.

---

## 2. Root Cause Analysis

**What is the actual root cause?** A combination, ranked by contribution:

| Rank | Factor | Verdict | Evidence |
| ---- | ------ | ------- | -------- |
| 1 | **Tool schema design** (opaque `data` with no nested structure) | **Primary cause** | `records.js:151`; contrast `people.js` typed schema; grep: no `phones` schema anywhere |
| 2 | **Generic-CRUD design** (model must reconstruct Twenty's nested wire format per call) | **Major contributing** | `updation_issues.md`: nested intent → empty emission; flat `noteTargets` succeeded |
| 3 | **Model/planner behavior** (LLMs drop nested objects under a permissive schema) | **Trigger, not cause** | Same model succeeded on flat writes; failure correlates with nesting, not the model |
| 4 | **Missing update guard** (empty PATCH silently accepted) | **Aggravator** (turns a bug into a *silent* bug) | create has `minProperties:1`; update does not; Twenty accepts empty PATCH, bumps `updatedAt` |
| 5 | OpenClaw runtime routing | **Not a cause** | Validates + dispatches correctly; opaque schema means `{}` is valid input |
| 6 | Plugin HTTP implementation | **Not a cause** | Update `run` forwards `params.data` unchanged |
| 7 | Twenty CRM / auth | **Not a cause** | Twenty accepted the request; email stayed blank because body was empty |

**Conclusion:** The root cause is **tool-contract design**, specifically an opaque generic write schema
that forces the model to hand-serialize nested composite fields (`emails`, `phones`) with no structural
guidance and no failure signal. The model/provider is the *trigger* that exposes the weak contract, but
the *fixable* defect is the schema and the generic-CRUD strategy for writes.

---

## 3. Option Evaluation

### Option A — Fix the existing generic Twenty plugin tools

Keep `twenty_record_create` / `twenty_record_update`; make the model reliably produce correct payloads
via schema/prompt changes.

- **Realistically fixable?** Partially. Adding `minProperties: 1` + an explicit empty-body reject to
  *update* (mirroring create) makes the failure **loud** instead of silent — that is cheap and worth
  doing regardless. But making a **generic** tool reliably emit nested composites is fundamentally hard:
  a single tool serves *every* entity, so its `data` cannot be strongly typed without becoming an
  enormous union.
- **Caused by schema design?** Yes (see §2).
- **Would richer/entity-aware schemas solve it?** Entity-aware schemas would — but that is no longer
  "the generic tool." A truly generic tool that is also strongly typed per entity is a contradiction.
- **Reliable across providers?** No. A permissive `additionalProperties: true` object is exactly the
  shape most prone to nested-object dropping across different LLM providers. Prompt-only mitigations are
  provider-sensitive and regress silently.
- **Verdict:** Do the cheap safety guard, but A alone does **not** solve reliability for nested writes.

### Option B — Replace only write/update tools with recruiting-aware tools

Keep all read tools; replace create/update/delete with `candidate_update`, `candidate_add_note`,
`application_create`, `schedule_interview`, etc.

- **Advantages:** Strong typing gives the model an unambiguous, flat, recruiting-shaped contract
  (e.g. `candidate_update_contact({ id, email, phone })`) — the tool internally builds Twenty's nested
  `emails`/`phones` objects. This is the exact fix for the root cause: the model never hand-serializes
  nested wire format. High reliability, high AI-friendliness, testable in isolation, easy to debug
  (each tool has one job).
- **Disadvantages:** More tools to author/maintain; must encode Twenty's nested shapes once (low risk,
  centralized). Read/write asymmetry (generic reads, typed writes) is a minor conceptual seam.
- **Compatibility with existing plugin:** Excellent — reads continue via the existing plugin unchanged.
- **Maintenance cost:** Low-moderate; the write surface for recruiting is small and stable
  (contact info, notes, application create, interview scheduling via workflow).
- **Verdict:** Strong. This directly removes the failure mode.

### Option C — Extend the plugin with recruiting-specific tools alongside generic CRUD

Keep generic CRUD; add `twenty_candidate_update_email`, `twenty_schedule_interview`, etc.

- **Evaluation:** The tool *design* is right (typed, task-specific) and is essentially Option B's tools
  living **inside** the vendored plugin. The problem is **location**: the plugin is installed under
  git-ignored `openclaw/data/` and is overwritten on reinstall (`twenty_metadata_compatibility.md`).
  Adding tools there means forking or patch-injecting into a third-party package — fragile and an
  upgrade hazard.
- **Verdict:** The hybrid *tool set* is correct; putting it *inside* the Twenty plugin is not. Prefer B
  packaged as its own plugin (see §4 recommendation).

### Option D — Build an independent Recruiting Plugin (Recruiting Plugin → Twenty REST)

- **Complexity:** Moderate. `openclaw plugins init recruiting --type tool` scaffolds it; it needs a thin
  Twenty REST client (retry/backoff already exists in `scripts/schema_v2/schema_utils.py` and the
  plugin's `twenty-client.js` as reference) plus typed tools.
- **Long-term maintainability:** High. Versioned separately, own tests, own manifest `contracts.tools`,
  survives Twenty-plugin reinstalls untouched.
- **Code duplication:** Some — a second Twenty HTTP client. Bounded and acceptable (the recruiting write
  surface is small); reads still delegate to the existing plugin.
- **Future scalability:** Best of all options — new recruiting tools slot in without touching Twenty's
  generic surface.
- **Verdict:** This is the right **home** for Option B's tools.

### Option E — Direct REST from Recruiting *skill* tools (no plugin for writes)

Skills shell out (`exec curl`) or call REST directly for writes.

- **Evaluation:** `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md` §4/§7 shows skills are prose that must call a
  **tool** to execute; a `SKILL.md` cannot run code. "Direct REST from tools" therefore still needs a
  tool — which is Option D. If it means `exec curl`, it loses typing, validation, policy gating, and
  testability (the very things that fix the root cause) and reintroduces hand-built JSON — the exact
  problem we are trying to eliminate.
- **Verdict:** Rejected. It trades a schema problem for a worse, unvalidated shell-string problem.

---

## 4. Required Comparison

Scores: ✅ strong / 🟡 acceptable / ❌ weak. "Time" is relative implementation effort.

| Criterion | A: Fix generic | B: Typed write tools | C: Extend plugin | D: New plugin (home for B) | E: Direct REST/exec |
| --------- | :---: | :---: | :---: | :---: | :---: |
| Reliability (nested writes) | ❌ | ✅ | ✅ | ✅ | 🟡 |
| Complexity | ✅ low | 🟡 | 🟡 | 🟡 | 🟡 |
| Maintainability | 🟡 | ✅ | ❌ (fork risk) | ✅ | ❌ |
| Testability | 🟡 | ✅ | 🟡 | ✅ | ❌ |
| AI friendliness | ❌ | ✅ | ✅ | ✅ | ❌ |
| Debuggability | 🟡 | ✅ | 🟡 | ✅ | ❌ |
| Future extensibility | ❌ | ✅ | 🟡 | ✅ | 🟡 |
| Upgrade risk (Twenty plugin reinstall) | ✅ | ✅ | ❌ | ✅ | ✅ |
| Compat. w/ future Twenty releases | 🟡 | ✅ | 🟡 | ✅ | ❌ |
| Time to implement | ✅ hours | 🟡 days | 🟡 days | 🟡 days | 🟡 |

**Reading of the matrix:** B's *tools* + D's *packaging* dominate. A is the correct *immediate safety
fix* but not a reliability solution. C is B misplaced. E is a regression.

---

## 5. Final Recommendation (for THIS project)

Adopt a **two-part, hybrid architecture**. Optimize for a working platform quickly, minimal future
maintenance, and preserved OpenClaw/Twenty compatibility.

```
Agent turn
  ├─ READS  ─────────────► @lacneu/twenty-openclaw (unchanged): twenty_record_list/get, metadata, views, workflows
  └─ WRITES ─────────────► recruiting-tools plugin (NEW, defineToolPlugin)
                               candidate_update_contact / candidate_add_note /
                               application_create / schedule_interview / ...
                                     └─ typed args → builds Twenty nested wire shape → Twenty REST /rest/*
```

### Part 1 — Immediate stop-gap (hours): make the silent failure loud

- Extend `tests/openclaw/patch_twenty_metadata_compatibility.mjs` to guard **update** the same way
  create is guarded: reject `data: {}` on `twenty_record_update` **before** the network call, with a
  message like *"Refused to update `<entity>`: data must contain at least one field. No HTTP request was
  made."*
- Add the mirror assertion to `tests/openclaw/test_twenty_write_contract.mjs`.
- **Why:** This does not fix reliability, but it converts a silent no-op (that bumps `updatedAt` and
  wastes minutes) into an actionable error the agent can react to. Low risk, uses infrastructure we
  already run.

### Part 2 — The real fix: a dedicated recruiting write plugin (Option B tools, Option D home)

**What to build:** a new OpenClaw tool plugin — proposed id `recruiting-tools` — scaffolded with
`openclaw plugins init recruiting-tools --type tool` and registered via `defineToolPlugin`
(pattern documented in `OPENCLAW_TOOL_RUNTIME_ANALYSIS.md` §6 and the official `stock-quotes` example).

**Tools (small, task-shaped, strongly typed — flat inputs, nested serialization hidden):**

| Tool | Typed input (flat) | Internally builds |
| ---- | ------------------ | ----------------- |
| `candidate_update_contact` | `{ id, email?, phone?, phoneCountry? }` | Twenty `emails` / `phones` nested objects |
| `candidate_update_notes_field` | `{ id, field, text }` (informational only) | validated `twenty_record_update`-equivalent PATCH |
| `candidate_add_note` | `{ candidateId, title, markdown }` | `notes` create + `noteTargets` link (the flow proven to work) |
| `application_create` | `{ candidateId, requisitionId, stage? }` | `applications` POST with FKs |
| `schedule_interview` | `{ applicationId, when, … }` | approved-workflow run (`twenty_workflow_run`), **not** raw status PATCH |

Each tool: validates required IDs, builds the exact nested Twenty payload once (server-verified shapes),
returns the updated record, and is unit-testable with a mocked client (same style as
`test_twenty_write_contract.mjs`).

**Where the tools live and why:** in the **new `recruiting-tools` plugin**, **not** inside
`@lacneu/twenty-openclaw`. Reason: the Twenty package is installed under git-ignored `openclaw/data/`
and is **overwritten on reinstall** (`docs/twenty_metadata_compatibility.md`). A separate plugin is
versioned in the repo, survives Twenty-plugin upgrades, carries its own `contracts.tools` manifest and
tests, and keeps a clean read/write separation (generic reads from the vendor plugin; typed recruiting
writes from ours).

**What explicitly should NOT change:**

- Do **not** fork or hand-edit the vendored Twenty plugin to add recruiting tools (Option C).
- Do **not** remove the generic create/update — keep them as a metadata-gated escape hatch for
  one-off/unmodeled writes, now with the empty-body guard.
- Do **not** route lifecycle/state changes (`application.stage`, `interview.interviewStatus`,
  `offer.offerStatus`, `requisition.requisitionStatus`) through any raw PATCH tool — those remain
  workflow-run operations per `openclaw/workspaces/default/skills/crm/SKILL.md`.

**Skill layer:** update the `crm` skill (and downstream recruiting skills) to prefer the new typed
recruiting tools for writes, using the generic tools only for reads and unmodeled fields. This matches
the OpenClaw execution model (skill = instructions, tool = execution).

### Why this is the best engineering solution (not just the quickest)

1. It removes the **actual** root cause: the model no longer hand-serializes nested composites — it
   passes flat, typed arguments that the tool converts. Flat scalar inputs are exactly the shape that
   already succeeds today (`noteTargets`).
2. It is **provider-robust**: strong TypeBox schemas + server-side validation + a loud empty-body guard
   protect against the failure across any LLM.
3. It is **upgrade-safe**: no fork of the vendored plugin; reads stay on the maintained upstream.
4. It **reuses proven infrastructure**: the patch/validate/test harness already exists; the new plugin
   follows the documented `defineToolPlugin` pattern.
5. It **avoids a rewrite**: existing read paths, metadata compatibility patch, and workflow boundaries
   are untouched.

---

## 6. Source Reference Index

| Claim | Source |
| ----- | ------ |
| Opaque generic update schema (`data` empty object) | `…/@lacneu/twenty-openclaw/dist/tools/records.js` `RecordUpdateSchema` |
| Create guarded with `minProperties:1`; update not | `records.js` + `tests/openclaw/patch_twenty_metadata_compatibility.mjs` |
| Update `run` forwards `params.data` unchanged | `records.js` `twenty_record_update` `run` |
| Typed nested schema on people update; no `phones` schema anywhere | `…/dist/tools/people.js`; grep `primaryPhoneNumber` = 0 matches |
| Intended nested payload vs emitted `data:{}`; flat note write succeeded | `docs/openclaw_self_given_report/updation_issues.md` |
| Runtime validates args against TypeBox schema, then dispatches | `docs/openclaw_skill_reports/OPENCLAW_TOOL_RUNTIME_ANALYSIS.md` §2 |
| `defineToolPlugin` is the supported custom-tool path; skills call tools | same, §6–§7 |
| Package under git-ignored `openclaw/data/`, overwritten on reinstall | `docs/twenty_metadata_compatibility.md` |
| Write boundary: lifecycle changes via workflow, not raw PATCH | `openclaw/workspaces/default/skills/crm/SKILL.md` |
| Existing write-contract test style to mirror | `tests/openclaw/test_twenty_write_contract.mjs` |
