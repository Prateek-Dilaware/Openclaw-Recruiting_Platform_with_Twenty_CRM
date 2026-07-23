---
name: crm
description: "Use for verified Twenty CRM reads, recruiting record mutations, and recruiting workflow transitions. Enforces Twenty plugin-only access and separates safe field writes from workflow changes."
---

# CRM Operations

## Purpose

Provide the infrastructure procedure for recruiting skills that need Twenty CRM. Twenty CRM is the system of record and the `twenty-openclaw` plugin is the only CRM interface.

## Scope

- Discover objects and fields through `twenty_metadata_objects_list` and `twenty_metadata_fields_list` when schema details are unknown.
- Read custom recruiting records through `twenty_record_list` and `twenty_record_get`.
- Create/update non-state data through `twenty_record_create` and `twenty_record_update`.
- Inspect and execute approved workflows through `twenty_workflows_list`, `twenty_workflow_get`, `twenty_workflow_version_get_current`, `twenty_workflow_run`, and workflow-run status tools.

## Non-negotiable write boundary

### `write_field()` — safe informational writes

Treat `write_field()` as this procedure: validate the object, record id, and field through plugin metadata, then call `twenty_record_update` with only non-state-changing data.

Allowed examples: recruiter notes, resume summaries, interview transcripts, evaluation scores, evidence, generated drafts, and AI summaries.

### `trigger_workflow()` — state or lifecycle changes

Treat `trigger_workflow()` as this procedure: resolve the approved workflow/version, preview its scope, obtain the required OpenClaw approval, call `twenty_workflow_run`, and inspect the returned run.

Required examples: application stage movement, interview schedule/confirm/complete/cancel, rejection, offer approval/send/outcome, requisition approval/post/close.

Never use `twenty_record_update` to change `application.stage`, `interview.interviewStatus`, `offer.offerStatus`, or `requisition.requisitionStatus`. Never use a raw field update as a fallback when a workflow is unavailable or fails.

## Preconditions

1. Confirm `twenty-openclaw` is available and the user/workspace is authorized.
2. Use metadata discovery if the custom object, field, or relation is not verified for the current Twenty workspace.
3. Resolve the actual record; do not infer ids or schema from a prior environment.
4. For writes, state the intended object, fields or workflow, and user-visible effect before calling a mutation.

## Process

1. **Read** the required records and direct relations.
2. **Validate** identifiers, required fields, current lifecycle state, and duplication risk.
3. **Plan** either a safe `write_field()` or `trigger_workflow()` operation.
4. **Execute** only the matching plugin tool.
5. **Verify** the returned record or workflow run.
6. **Report** ids, changed fields/run id, current status, and any remaining approval or failure.

## Failure handling

- Missing object/field: stop and inspect metadata; do not guess field names.
- Duplicate/ambiguous candidate: return candidates and require a merge decision; never auto-merge.
- Permission/read-only/approval denial: report the exact blocked action and leave state unchanged.
- Workflow unavailable, inactive, or failed: report the run/result and escalate to a workflow owner. Do **not** patch status directly.
- Transport/plugin failure: do not replay a mutation blindly. Re-read the record/run first to determine whether it completed.

## Related skills

`candidate`, `resume`, `jd`, `interview`, `evaluation`, `scheduling`, `communication`, `research`, and `retrospective` use this boundary for CRM context.

## References and validation

Read `references/operation-contract.md`. Follow `examples/README.md` and `tests/README.md` before enabling a new mutation path.