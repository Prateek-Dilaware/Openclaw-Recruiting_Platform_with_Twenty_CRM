# Recruiter Agent — Tool Allow-List Recommendation (Audit)

**Date:** 2026-07-20
**Status:** Recommendation only — NOT implemented.
**Scope:** whether the Recruiter Agent should be given a restricted tool set
instead of all 166 registered plugin tools, and what that set should be.

## 1. Can OpenClaw restrict an agent's tools? — Yes

Evidence from the running gateway (`tool-policy-*.js`, current `openclaw.json`):

- Tool exposure is governed by a **tool policy** with `allow` / `deny` lists
  plus a `profile`. Entries may be:
  - an individual tool name (`candidate_create`),
  - a **group token** (`group:plugins`, core groups via `CORE_TOOL_GROUPS`),
  - a **plugin token** (`plugin:twenty-openclaw`),
  - aliases and prefix matches.
- The runtime explicitly models a **restrictive allow policy**
  (`hasRestrictiveAllowPolicy`, `DEFAULT_PLUGIN_TOOLS_ALLOWLIST_ENTRY`), i.e. an
  allow-list narrower than "all plugin tools" is a first-class, supported case.
- **Current config is permissive:** `tools.profile = "coding"` +
  `tools.alsoAllow = ["group:plugins"]`. `group:plugins` pulls in **every**
  registered plugin tool → all 166 Twenty tools reach the planner.

**Conclusion:** a recruiter-scoped allow-list is fully supported. Instead of
`group:plugins`, we can enumerate an explicit recruiting tool list (± minimal
core groups), which the policy pipeline enforces before the model sees tools.

## 2. Why restrict (planner impact)

- 166 tools is a large decision surface. Most (~99 admin: Views, Page-layouts,
  Roles, Companies/Opportunities CRUD) are irrelevant to recruiting and only
  add planner noise + token cost + misfire risk.
- Removing the irrelevant surface also removes most of the overlap flagged in
  the inventory audit (e.g. generic `twenty_record_*` write shadowing typed
  tools) — without deleting any tool from the plugin.
- This is **reversible and non-destructive**: tools stay registered; the agent
  just isn't offered the ones outside its allow-list.

## 3. Proposed Recruiter Agent tool set

Target: typed recruiting tools + generic **reads** + essential supporting
tools. ~30 tools instead of 166.

### A. Typed recruiting WRITE tools (17) — primary surface
```
candidate_create
candidate_update_contact
candidate_update_profile
recruiting_add_note
requisition_create
requisition_update
requisition_set_status
application_create
application_set_stage
application_set_decision
application_set_consent
application_set_resume_summary
interview_schedule
interview_set_status
evaluation_create
evaluation_finalize
offer_create
offer_set_status
```

### B. Generic READS (3) — the sanctioned read path for custom objects
```
twenty_record_list
twenty_record_get
```
(There are no typed recruiting reads; these are reliable and required.)

### C. Metadata discovery (3) — schema validation before writes
```
twenty_metadata_objects_list
twenty_metadata_object_get
twenty_metadata_fields_list
```

### D. Workflow execution (5) — approved lifecycle path + verification
```
twenty_workflows_list
twenty_workflow_version_get_current
twenty_workflow_run
twenty_workflow_runs_list
twenty_workflow_run_get
```

### E. Workspace context (1)
```
twenty_workspace_info
```

### Deliberately EXCLUDED from the recruiter set
- Generic **writes**: `twenty_record_create` / `_update` / `_delete` — the
  overlap that causes the `data:{}` misfire. Excluding them from the recruiter
  agent forces the typed tools (the whole point). *(Kept registered for other
  agents / escape-hatch use.)*
- All per-entity People/Companies/Opportunities/Tasks CRUD (24).
- Views (32), List columns (5), Page layouts/dashboards (19), Roles (13),
  Field-config setters (5), metadata *object/field* create/update/delete (7),
  dedup/bulk/export (7), logic functions (3), workspace migration.

## 4. Two ways to apply it (when we implement)

1. **Global tools policy (simplest):** replace `tools.alsoAllow: ["group:plugins"]`
   with an explicit `tools.allow` list of the ~30 entries above (+ whatever core
   `coding`-profile tools the agent legitimately needs: `exec`, `read`, memory,
   `update_plan`, etc.). Applies to the single `main` agent this deployment runs.
2. **Dedicated recruiter agent (cleaner long-term):** define a `recruiter`
   agent under `agents.*` with its own `tools.allow`, leaving other agents
   unrestricted. Preferred once we run more than one agent persona.

Either way: **no plugin code changes** — pure config. Reversible.

## 5. Open questions to resolve before implementing

- Exact core-tool needs of the recruiter agent (does it need `exec`, web
  fetch/search, memory, subagents?). Must be enumerated so the allow-list
  doesn't accidentally strip required non-CRM tools.
- Whether lifecycle `*_set_*` typed setters stay in the recruiter set or are
  replaced by the workflow path (`twenty_workflow_run`) — depends on the
  workflow-routing decision deferred to the optimization phase.
- Notes overlap: recruiter set includes `recruiting_add_note` and excludes
  `twenty_notes_*`, resolving that ambiguity by construction.

## 6. Recommendation

**Adopt an explicit recruiter allow-list (~30 tools) via the tools policy**,
replacing the blanket `group:plugins`. Start with option (1) global policy for
the current single-agent deployment; migrate to a dedicated `recruiter` agent
(option 2) when multiple personas exist. Implement only after manual agent
testing confirms the core-tool needs and the workflow-vs-typed-setter decision.
