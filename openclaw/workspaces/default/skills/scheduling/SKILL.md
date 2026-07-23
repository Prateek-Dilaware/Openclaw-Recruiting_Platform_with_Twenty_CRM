---
name: scheduling
description: "Use for availability review, interview scheduling proposals, rescheduling, and cancellation through approved Twenty workflows. Uses a Calendar MCP when configured and does not implement calendar transport directly."
---

# Interview Scheduling

## Purpose

Coordinate interview timing while keeping calendar transport and recruiting lifecycle changes separate and controlled.

## Responsibilities

- Review supplied or MCP-provided availability.
- Propose suitable interview slots with timezone clarity.
- Request schedule, reschedule, or cancellation through approved lifecycle workflows.

## Scope

This skill owns availability analysis and approved interview-lifecycle requests. It does not implement calendar transport, send invitations, or directly write interview status fields.

## Scope and approval

Use an approved Calendar MCP only when it is configured; otherwise operate on availability supplied by authorized users. Do not send invitations, create calendar events, or implement calendar API logic. Interview schedule/reschedule/cancel is a workflow change and must use `crm.trigger_workflow()` with runtime approval.

## Process

1. Read `references/scheduling-contract.md`.
2. Confirm application, interview round, interviewers, duration, timezone, and consent to schedule.
3. Read availability from the approved Calendar MCP or supplied data. State the source and freshness.
4. Propose slots with timezone and conflict rationale; do not assume availability is a commitment.
5. After explicit authorization, resolve the Interview Lifecycle workflow/version and run it with approved input.
6. Verify workflow status and re-read the interview/application. Report whether external calendar action remains pending.

## Failure handling

- No Calendar MCP: request availability; do not create a custom calendar integration.
- Timezone/availability ambiguity: present alternatives and request confirmation.
- Workflow inactive/failed: do not write `scheduledAt` or `interviewStatus` directly; escalate with the workflow-run evidence.
- Calendar MCP conflict: report conflict and retain CRM state until a valid workflow outcome is confirmed.

## Related skills

`interview` prepares the round; `communication` drafts messages; `crm` owns the workflow boundary.

## Examples and validation

See `examples/README.md` and `tests/README.md`.