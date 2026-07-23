# Recruiting Write Tools

**Date:** 2026-07-20
**Plugin:** `@crm/twenty-plugin` (maintained in `plugins/twenty-plugin`).
**Status:** Recruiting tool layer COMPLETE — 18 typed tools, unit 105/105,
live full-flow 20/20. Plugin registers 166 tools (57 approval-gated). See
`docs/RECRUITING_TOOL_COVERAGE_MATRIX.md` for the full matrix.

## Completed tool surface (18)

candidate: `candidate_create`, `candidate_update_contact`,
`candidate_update_profile` · notes: `recruiting_add_note` · requisition:
`requisition_create`, `requisition_update`, `requisition_set_status`* ·
application: `application_create`, `application_set_stage`*,
`application_set_decision`, `application_set_consent`,
`application_set_resume_summary` · interview: `interview_schedule`,
`interview_set_status`* · evaluation: `evaluation_create`,
`evaluation_finalize`* · offer: `offer_create`, `offer_set_status`*.

`*` = lifecycle SELECT setter, approval-gated by default.

Live verification: `scripts/twenty-plugin/live_test_recruiting_flow.mjs`
(full create→lifecycle→note→interview→evaluation→offer flow, read-back
verified, records soft-deleted).

---

## Design notes (original phase 1)

## Rationale

The generic `twenty_record_update` exposes an opaque `data` object. For nested
COMPOSITE Twenty fields (EMAILS, PHONES) the model must hand-build the nested
wire shape, and providers frequently drop the nested object — emitting
`data: {}` (see `docs/openclaw_self_given_report/updation_issues.md`). Flat
scalar writes succeed; nested composite writes silently no-op.

**Fix:** recruiting-aware **typed** tools that accept FLAT scalar inputs and
build Twenty's nested wire shapes internally. The model never constructs
`emails`/`phones`.

## Where the tools live

- Module: `plugins/twenty-plugin/src/tools/recruiting.ts`
  (`buildRecruitingTools`).
- Registered in `src/index.ts` alongside the generic tools.
- Declared in `openclaw.plugin.json` → `contracts.tools`.
- Generic CRUD tools remain as a metadata-gated escape hatch. Lifecycle/state
  changes stay on approved workflows, never a raw PATCH.

## Live-verified Twenty wire shapes (candidate object)

| Field | Type | Shape |
| --- | --- | --- |
| `name` | TEXT | plain string (NOT FULL_NAME on the custom candidate object) |
| `emails` | EMAILS | `{ primaryEmail: string, additionalEmails: string[] }` |
| `phones` | PHONES | `{ primaryPhoneNumber, primaryPhoneCountryCode, primaryPhoneCallingCode, additionalPhones: [] }` |

Twenty validates phone numbers server-side (`INVALID_PHONE_NUMBER`); the tool
surfaces that 400 rather than swallowing it.

## Tool: `candidate_update_contact`

Input (flat):
- `candidateId` (required, UUID)
- `email?` — sets `emails.primaryEmail`
- `phone?` — sets `phones.primaryPhoneNumber`
- `phoneCountryCode?` — ISO alpha-2 (e.g. `IN`), uppercased
- `phoneCallingCode?` — e.g. `+91`

Behavior:
1. Validate `candidateId` is a UUID and at least one of `email`/`phone` is
   supplied — BEFORE any HTTP request.
2. Build the nested `emails`/`phones` payload internally.
3. `PATCH /rest/candidates/:id`.
4. Verify the PATCH response reflects the set fields.
5. Return `{ candidate, verification }`.

## Tests

- **Unit (mocked client):** `test/tools/recruiting.test.ts` — 5 cases
  (email-only, phone-only, both, invalid UUID rejected pre-network, empty
  rejected pre-network). Full suite: **93/93 pass**.
- **Live (real Twenty):** `scripts/twenty-plugin/live_test_candidate_contact.mjs`
  — creates a throwaway candidate, exercises all 5 cases with CRM re-read
  verification, then soft-deletes. **5/5 pass.**

  Run:
  ```powershell
  docker cp scripts\twenty-plugin\live_test_candidate_contact.mjs openclaw:/tmp/lt.mjs
  docker exec openclaw node /tmp/lt.mjs
  ```

## Evidence (2026-07-20)

- Gateway: `twenty-openclaw [CRM maintained @crm/twenty-plugin]: ready — 149
  tool(s) registered` (was 148; +1 = `candidate_update_contact`).
- Live test: 5/5 — email/phone/both persisted and re-read from CRM; invalid id
  and empty update rejected with no HTTP request.

## Next tools (same pattern)

- `candidate_add_note` — `notes` create + `noteTargets` link (the flat,
  two-record flow already proven to work).
- `application_create` — application with candidate/requisition FKs.
- `schedule_interview` — via an approved workflow run, not a raw status PATCH.
