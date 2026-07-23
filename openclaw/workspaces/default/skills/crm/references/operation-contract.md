# CRM Operation Contract

## Schema V2 roles

- `candidate`: reusable person/contact profile.
- `requisition`: approved job opening.
- `application`: a candidate's participation in a requisition; this owns the recruiting stage.
- `interview`: a round linked to an application.
- `evaluation`: an AI or human assessment linked to an interview.
- `offer`: approval/delivery/outcome linked to an application.

## Approved workflow catalogue

| Lifecycle | Workflow |
|---|---|
| Requisition status | `Recruiting V2 - Requisition Approval` |
| Application stage | `Recruiting V2 - Application Stage Transition` |
| Interview status | `Recruiting V2 - Interview Lifecycle` |
| Offer status | `Recruiting V2 - Offer Lifecycle` |

The deployed workflow version and input contract must be inspected at runtime. Workflow records can exist as drafts; do not assume a draft is executable.

## Plugin facts

The installed Twenty plugin provides generic record tools for custom recruiting objects and approval-gated workflow execution. `twenty_workflow_run` can have external side effects; use its returned run id with `twenty_workflow_run_get` for verification.

## Prohibited paths

- Direct REST calls, a CRM SDK, database access, or custom HTTP clients.
- Raw status/stage updates.
- Silent fallback after a workflow error.
- Schema mutation by operational recruiting skills.