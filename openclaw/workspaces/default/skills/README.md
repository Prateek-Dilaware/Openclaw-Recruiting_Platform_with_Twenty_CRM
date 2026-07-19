# Recruiting Skills

Workspace-local OpenClaw recruiting skills. Each directory is a valid OpenClaw skill package because it contains a `SKILL.md` with required YAML frontmatter and description.

## Package map

| Skill | Recruiter activity | CRM mutation boundary |
|---|---|---|
| `candidate` | Find, create, update, merge-review, summarize, timeline | Safe profile writes only; merge is review-only |
| `resume` | Parse, screen, match, compare, rank resumes | Safe summaries/evaluation drafts only |
| `jd` | Generate/improve JD and extract requirements | Safe requisition-content writes only |
| `crm` | Twenty plugin operation contract | Safe writes vs workflow runs |
| `interview` | Prepare/interpret interview artifacts | Safe transcript/evaluation writes only |
| `evaluation` | Compare, rank, shortlist, recommend | Safe evaluation artifacts only |
| `scheduling` | Availability, schedule/reschedule/cancel | Interview Lifecycle workflow only |
| `communication` | Email/offer/rejection/feedback drafts | Draft storage only; never sends |
| `research` | Company/profile/GitHub research | Read-only unless explicitly approved safe write |
| `retrospective` | Override/failure analysis and recommendations | Read-only; never auto-applies changes |

## Shared operating contract

1. Twenty CRM is the system of record.
2. The `twenty-openclaw` plugin is the only CRM interface. No direct REST, CRM SDK, database, or custom HTTP client is permitted in these skills.
3. `twenty_record_update` is used only for non-state information after validation.
4. Lifecycle state changes use a verified and approved Twenty workflow through `twenty_workflow_run`; no direct-update fallback is allowed.
5. Skills are instruction packages, not executable services. FastAPI remains the deterministic business-API boundary; OpenClaw performs reasoning and chooses approved operations.

## References reused

- **OpenClaw official skills:** `SKILL.md` directory package, YAML frontmatter, workspace-local loading, and task-specific instruction model.
- **WeCom CRM skill:** workflow-oriented, reference-backed skill layout.
- **Odoo skill:** separation between high-level reasoning/workflow orchestration and deterministic, validated service actions with structured outcomes.
- **Browser Act skill forge:** explicit validation, recovery, and reusable example/script-package discipline; applied here as `references/`, `examples/`, and `tests/` documentation without adding browser automation implementation.
- **Twenty plugin 0.8.4:** metadata discovery, generic custom-object records, and approval-gated workflow execution.
- **Schema V2 scripts:** six recruiting objects, application as stage owner, and the four approved workflow names.

## Runtime test prerequisites

The Markdown package structure can be validated statically. Tool execution must be validated only in a non-production Twenty workspace after confirming:

- the `twenty-openclaw` plugin is installed/enabled and allowed by policy;
- Schema V2 custom objects/relations exist and metadata names match;
- the named recruiting workflows have reviewed active versions and defined input payload contracts;
- test records are synthetic or approved; and
- any Calendar/browser/mail MCP is configured and permissioned.