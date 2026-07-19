---
name: communication
description: "Use for recruiter-facing and candidate-facing communication drafts: email drafts, rejection letters, offer letters, recruiter summaries, and candidate feedback. Drafts only; never sends messages."
---

# Recruiting Communication Drafts

## Purpose

Prepare accurate, respectful communication drafts without sending messages or changing recruiting state.

## Responsibilities

- Draft recruiter summaries and candidate feedback.
- Draft email, rejection, and offer communications from approved facts.
- Identify missing approvals, terms, recipients, or delivery channels.

## Scope

This skill owns message drafting only. It does not send messages, schedule events, or change candidate, application, interview, requisition, or offer state.

## Scope and approvals

This skill creates drafts only. It does not send email, create messaging actions, schedule invitations, or update lifecycle fields. Store an approved draft/note only through `crm.write_field()`. Offer approval, sending, acceptance, decline, or rejection remains a workflow action through `crm.trigger_workflow()` and future approved MCP delivery capability.

## Process

1. Read `references/communication-standard.md`.
2. Confirm audience, purpose, authorized facts, tone, locale, and whether the message is internal or external.
3. For rejection/offer content, verify the relevant human approval and CRM workflow status; never imply a decision that has not been approved.
4. Draft concise content with placeholders for unresolved facts.
5. Include a fact/approval checklist for the requester.
6. If asked to save the draft, use the CRM safe-write procedure after confirming the target record.

## Failure handling

- Missing approved decision or offer terms: provide a template with clear placeholders; do not invent facts.
- Request to send: state that delivery requires a configured future MCP integration and the required approval.
- Sensitive feedback: use factual, respectful language and recommend legal/HR review where policy requires it.

## Related skills

`evaluation` supplies evidence-based rationale; `scheduling` handles scheduling lifecycle; `crm` handles approved persistence/workflows.

## Examples and validation

See `examples/README.md` and `tests/README.md`.