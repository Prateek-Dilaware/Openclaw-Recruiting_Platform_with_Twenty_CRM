# Dedicated `recruiter` Agent — Design (Not Yet Applied)

**Date:** 2026-07-20
**Status:** DESIGN ONLY. No config written, no runtime change. For review.
**Depends on:** `docs/RECRUITER_AGENT_TOOL_ALLOWLIST.md` (the tool set).

## Goals

- Add a dedicated `recruiter` agent with a **restrictive tool allow-list**
  (recruiting tools + minimal core tools).
- **Keep `main` unchanged** as the fallback (its global tool policy —
  `profile: coding` + `alsoAllow: group:plugins` — stays as is).
- Explain how requests route between `main` and `recruiter`.

## How OpenClaw agents + routing work (verified via `openclaw agents` CLI)

- Agents are **isolated**: each has its own workspace, state dir, model, and
  (optionally) its own tool policy. Config lives under `agents.<id>`, mirroring
  the existing `agents.defaults` block.
- **Routing is by channel binding.** `openclaw agents bind --agent <id>
  --bind <channel[:accountId]>` maps an inbound channel (or channel+account) to
  an agent. `openclaw agents bindings` lists them. Currently: **"No routing
  bindings"** → everything falls to the default agent (`main`).
- With no binding matched, the **default agent handles the request** — so
  `main` remains the catch-all fallback automatically.

## Proposed config (add to `openclaw.json` — DO NOT APPLY YET)

Add a `recruiter` entry under `agents`. `agents.defaults` continues to supply
workspace/model defaults; the `recruiter` block overrides only what it needs
and adds a restrictive `tools` policy.

```jsonc
{
  "agents": {
    "defaults": {
      "workspace": "/home/node/.openclaw/workspace",
      "models": { "openrouter/auto": { "alias": "OpenRouter" } },
      "model": { "primary": "openrouter/auto" }
    },

    // NEW — dedicated recruiter agent. `main` is untouched (it is the
    // implicit default agent and keeps the global permissive policy).
    "recruiter": {
      "workspace": "/home/node/.openclaw/workspace",
      "model": { "primary": "openrouter/auto" },

      // Restrictive allow-list. Only these tools are offered to the planner
      // for this agent. Everything else stays REGISTERED but hidden here.
      "tools": {
        // Minimal OpenClaw core profile (planning/read/edit/exec/etc.).
        // `assistant` is the lighter core profile; if unavailable use
        // `coding`. Confirm the exact profile id during review.
        "profile": "assistant",

        // Core tools the recruiter genuinely needs beyond the profile.
        // These are OpenClaw built-ins (not plugin tools).
        "alsoAllow": [
          "update_plan",        // planning
          "memory_search",      // memory recall
          "web_fetch",          // pull JDs / public pages
          "web_search"          // research
        ],

        // Explicit plugin allow-list (recruiting surface only). Because we
        // enumerate here, we DO NOT add `group:plugins` (which would expose
        // all 166).
        "allow": [
          // Typed recruiting writes (17)
          "candidate_create",
          "candidate_update_contact",
          "candidate_update_profile",
          "recruiting_add_note",
          "requisition_create",
          "requisition_update",
          "requisition_set_status",
          "application_create",
          "application_set_stage",
          "application_set_decision",
          "application_set_consent",
          "application_set_resume_summary",
          "interview_schedule",
          "interview_set_status",
          "evaluation_create",
          "evaluation_finalize",
          "offer_create",
          "offer_set_status",

          // Generic reads (sanctioned read path for custom objects)
          "twenty_record_list",
          "twenty_record_get",

          // Metadata discovery (validate schema before writes)
          "twenty_metadata_objects_list",
          "twenty_metadata_object_get",
          "twenty_metadata_fields_list",

          // Workflow execution (approved lifecycle path + verification)
          "twenty_workflows_list",
          "twenty_workflow_version_get_current",
          "twenty_workflow_run",
          "twenty_workflow_runs_list",
          "twenty_workflow_run_get",

          // Workspace context
          "twenty_workspace_info"
        ]
      }
    }
  }
}
```

> Notes:
> - `main` is the implicit default agent; it is **not** listed above and keeps
>   the existing global `tools` policy. Nothing about `main` changes.
> - The recruiter's `allow` deliberately **omits** generic writes
>   (`twenty_record_create/_update/_delete`) and all admin surfaces (People/
>   Companies/Views/Page-layouts/Roles/etc.) — see the allow-list audit.

## Routing between `main` and `recruiter`

Two supported models — pick during review:

### Option R1 — Channel binding (production-style)
Bind a dedicated inbound channel/account to the recruiter; everything else
falls through to `main`.

```
openclaw agents bind --agent recruiter --bind <channel>:<accountId>
```
- Requests on that channel → `recruiter` (restricted tools).
- All other requests → `main` (fallback, full tools).
- `openclaw agents bindings` shows the mapping; unbound = `main`.

### Option R2 — Explicit invocation / default stays main
Leave bindings empty (current state). `main` remains default. Invoke the
recruiter explicitly per session (e.g. via the agent selector / `--agent
recruiter` where the surface supports it). Fallback is automatic: anything not
explicitly targeting `recruiter` uses `main`.

**Recommendation:** start with **R2** (no bindings) for review/testing — zero
routing risk, `main` untouched — then move to **R1** once we dedicate a channel
to recruiting.

## Apply steps (for later, after review)

```powershell
# 1. (Option A) Hand-edit openclaw.json to add the `agents.recruiter` block
#    above, OR (Option B) scaffold then edit tools:
docker exec openclaw openclaw agents add recruiter `
  --workspace /home/node/.openclaw/workspace `
  --model openrouter/auto --non-interactive
#    then add the `tools` allow-list block to agents.recruiter in openclaw.json.

# 2. (Optional, R1) bind a channel:
# docker exec openclaw openclaw agents bind --agent recruiter --bind <channel>:<acct>

# 3. Restart gateway to load agent config:
docker restart openclaw

# 4. Verify:
docker exec openclaw openclaw agents list
docker exec openclaw openclaw agents bindings
```

## Open items to confirm during review

1. **Core profile id** — is `assistant` valid on 2026.6.11, or should the
   recruiter use `coding`? Confirm before applying (wrong id → no core tools).
2. **Exact core tools** the recruiter needs (does it need `exec`? file
   read/write? subagents?). The `alsoAllow` list above is conservative.
3. **Workspace isolation** — share `main`'s workspace (as drafted) or give the
   recruiter its own `--agent-dir` for isolated memory/state.
4. **Lifecycle setters vs workflows** — if we later route lifecycle through
   `twenty_workflow_run`, drop the `*_set_*` entries from the allow-list.
5. **Model** — same `openrouter/auto` as main, or a recruiting-tuned model.

## What this does NOT change now

- No `openclaw.json` written; no `agents add`/`bind` executed.
- Global `tools` policy and the `main` agent are untouched.
- No plugin code or tool registration change.
