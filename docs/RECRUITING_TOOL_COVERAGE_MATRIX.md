# Recruiting Tool Coverage Matrix

**Date:** 2026-07-20
**Plugin:** `@crm/twenty-plugin` (`plugins/twenty-plugin`).
**Basis:** live schema discovery against the running Twenty instance.
**Phase:** Recruiting Tool Completion (completeness over optimization).

## Legend
- **Typed tool** = recruiting-specific, flat-input, builds Twenty wire format
  internally (`src/tools/recruiting.ts`).
- **Generic** = falls back to `twenty_record_*` (kept as escape hatch).
- **Lifecycle** = SELECT status/stage field. Per the `crm` skill these are
  ideally workflow-driven; typed setters here are explicit + approval-gated so
  they are auditable, pending the later workflow-routing decision.

## Live schema (recruiting objects)

| Object | Key writable fields | Lifecycle SELECT | Relations (FK on write) |
| --- | --- | --- | --- |
| candidate | name, emails, phones, source, skillsTags, resumeUrl | — | applications(1:M) |
| requisition | name, jobTitle, department, location, employmentType, experienceRequirements, requiredSkills, jobDescription, headcount, postingUrl | requisitionStatus | applications(1:M) |
| application | name, source, appliedAt, parsedResumeSummary, decisionReason | stage, consentStatus, decisionRecommendation | candidateId, requisitionId |
| interview | name, round, scheduledAt, endedAt, timezone, durationMinutes | interviewType, interviewStatus | applicationId |
| evaluation | name, summary, strengths, weaknesses, overallScore, promptVersionTag | evaluationType, recommendation, evaluationStatus, authorType, sentiment | interviewId |
| offer | name, sentAt, termsSummary, salary, offerCurrency, startDate, expiryDate, respondedAt, declineReason | offerStatus | applicationId |
| note / noteTarget | title, bodyV2.markdown | — | noteId + target<Object>Id (MORPH) |

Enums (live):
- application.stage: APPLIED, SCREENING, RECRUITER_REVIEW, INTERVIEW_SCHEDULING, INTERVIEW_SCHEDULED, INTERVIEW_COMPLETED, DECISION_PENDING, OFFER, HIRED, REJECTED
- application.consentStatus: PENDING, GRANTED, WITHDRAWN
- application.decisionRecommendation: PENDING, PROCEED, HOLD, REJECT
- requisition.requisitionStatus: DRAFT, JD_PENDING_APPROVAL, APPROVED, POSTED, CLOSED
- requisition.employmentType: FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP
- interview.interviewType: PHONE, VIDEO, TECHNICAL, HIRING_MANAGER, ONSITE
- interview.interviewStatus: DRAFT, SCHEDULED, CONFIRMED, COMPLETED, CANCELLED
- evaluation.evaluationType: RESUME, INTERVIEW; recommendation: PROCEED, HOLD, REJECT; evaluationStatus: DRAFT, FINAL; authorType: AGENT, HUMAN; sentiment: POSITIVE, NEUTRAL, NEGATIVE
- offer.offerStatus: DRAFT, APPROVED, SENT, ACCEPTED, DECLINED

## Coverage matrix (recruiter agent operations → tools)

| # | Business operation | Tool | Status |
| --- | --- | --- | --- |
| 1 | Update candidate contact (email/phone) | `candidate_update_contact` | ✅ done |
| 2 | Create candidate | `candidate_create` | ✅ this phase |
| 3 | Update candidate profile (source/skills/resume/name) | `candidate_update_profile` | ✅ this phase |
| 4 | Add a note to any recruiting record | `recruiting_add_note` | ✅ this phase |
| 5 | Create requisition | `requisition_create` | ✅ this phase |
| 6 | Update requisition details / JD | `requisition_update` | ✅ this phase |
| 7 | Set requisition status (lifecycle) | `requisition_set_status` | ✅ this phase (gated) |
| 8 | Create application (link candidate↔requisition) | `application_create` | ✅ this phase |
| 9 | Set application stage (lifecycle) | `application_set_stage` | ✅ this phase (gated) |
| 10 | Record application decision (recommendation+reason) | `application_set_decision` | ✅ this phase |
| 11 | Set application consent | `application_set_consent` | ✅ this phase |
| 12 | Store parsed resume summary | `application_set_resume_summary` | ✅ this phase |
| 13 | Schedule an interview | `interview_schedule` | ✅ this phase |
| 14 | Set interview status (lifecycle) | `interview_set_status` | ✅ this phase (gated) |
| 15 | Record an evaluation | `evaluation_create` | ✅ this phase |
| 16 | Finalize an evaluation | `evaluation_finalize` | ✅ this phase |
| 17 | Draft an offer | `offer_create` | ✅ this phase |
| 18 | Set offer status (lifecycle) | `offer_set_status` | ✅ this phase (gated) |

Reads (candidate/application/etc.) continue via generic `twenty_record_list` /
`twenty_record_get` — reliable and the only read path for custom objects.

## Notes on lifecycle tools
`*_set_stage` / `*_set_status` perform a typed, validated PATCH of the SELECT
field and are **approval-gated by default**. This gives the recruiter agent a
working, auditable lifecycle surface now. Whether to reroute these through
`twenty_workflow_run` is deferred to the post-completion optimization phase
(as directed).
