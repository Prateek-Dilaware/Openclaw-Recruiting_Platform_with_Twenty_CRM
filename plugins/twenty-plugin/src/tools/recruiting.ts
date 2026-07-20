// Recruiting-aware typed business tools — CRM Recruiting Platform.
//
// WHY: the generic `twenty_record_*` tools expose an opaque `data` object;
// for nested COMPOSITE fields (EMAILS/PHONES) and for correct enum/relation
// handling the model must hand-build Twenty's wire format, which it does
// unreliably (dropped nested objects -> data:{}). These tools take FLAT,
// strongly-typed inputs and build Twenty's wire format INTERNALLY, validate
// before any HTTP call, perform the op, and verify by reading back the fields
// they set.
//
// Schema is live-verified (see docs/RECRUITING_TOOL_COVERAGE_MATRIX.md).
// FK writes use `<relation>Id` (candidateId, requisitionId, applicationId,
// interviewId, noteId, target<Object>Id).
//
// Lifecycle SELECT setters (*_set_stage / *_set_status) are typed + validated
// + approval-gated. Whether to reroute them through workflows is a later
// decision (per the completion-phase directive).

import { Type } from "@sinclair/typebox";
import type { TSchema } from "@sinclair/typebox";

import { defineTwentyTool } from "./_factory.js";
import type { TwentyClient } from "../twenty-client.js";

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

type Rec = Record<string, unknown>;

function assertUuid(value: unknown, field: string, tool: string): string {
  if (typeof value !== "string" || !UUID_REGEX.test(value)) {
    throw new Error(
      `${tool}: \`${field}\` must be a valid UUID (got: ${JSON.stringify(
        value,
      )}). No HTTP request was made.`,
    );
  }
  return value;
}

function assertEnum(
  value: string,
  allowed: readonly string[],
  field: string,
  tool: string,
): string {
  const up = value.toUpperCase();
  if (!allowed.includes(up)) {
    throw new Error(
      `${tool}: \`${field}\` must be one of [${allowed.join(", ")}] ` +
        `(got: ${JSON.stringify(value)}). No HTTP request was made.`,
    );
  }
  return up;
}

/** Unwrap Twenty's single-keyed write/get envelope into the bare record. */
function unwrap(resp: { data?: Rec } | null): Rec | null {
  const wrap = resp?.data;
  if (!wrap || typeof wrap !== "object") return null;
  const keys = Object.keys(wrap);
  if (keys.length === 0) return null;
  return (wrap[keys[0]] as Rec) ?? null;
}

/** Trim a string param; return "" for non-strings. */
function s(v: unknown): string {
  return typeof v === "string" ? v.trim() : "";
}

async function post(
  c: TwentyClient,
  entity: string,
  body: Rec,
  signal?: AbortSignal,
): Promise<Rec | null> {
  const resp = await c.request<{ data?: Rec }>("POST", `/rest/${entity}`, {
    body,
    signal,
  });
  return unwrap(resp);
}

async function patch(
  c: TwentyClient,
  entity: string,
  id: string,
  body: Rec,
  signal?: AbortSignal,
): Promise<Rec | null> {
  const resp = await c.request<{ data?: Rec }>(
    "PATCH",
    `/rest/${entity}/${encodeURIComponent(id)}`,
    { body, signal },
  );
  return unwrap(resp);
}

/** Build a { field: {expected, actual, ok} } verification entry. */
function verifyField(
  record: Rec | null,
  path: string,
  expected: unknown,
): { expected: unknown; actual: unknown; ok: boolean } {
  const actual = path
    .split(".")
    .reduce<unknown>(
      (acc, k) => (acc && typeof acc === "object" ? (acc as Rec)[k] : undefined),
      record ?? undefined,
    );
  return { expected, actual, ok: actual === expected };
}

// Enum sources (live-verified).
const REQ_STATUS = [
  "DRAFT",
  "JD_PENDING_APPROVAL",
  "APPROVED",
  "POSTED",
  "CLOSED",
] as const;
const EMPLOYMENT_TYPE = [
  "FULL_TIME",
  "PART_TIME",
  "CONTRACT",
  "INTERNSHIP",
] as const;
const APP_STAGE = [
  "APPLIED",
  "SCREENING",
  "RECRUITER_REVIEW",
  "INTERVIEW_SCHEDULING",
  "INTERVIEW_SCHEDULED",
  "INTERVIEW_COMPLETED",
  "DECISION_PENDING",
  "OFFER",
  "HIRED",
  "REJECTED",
] as const;
const CONSENT_STATUS = ["PENDING", "GRANTED", "WITHDRAWN"] as const;
const DECISION_REC = ["PENDING", "PROCEED", "HOLD", "REJECT"] as const;
const INTERVIEW_TYPE = [
  "PHONE",
  "VIDEO",
  "TECHNICAL",
  "HIRING_MANAGER",
  "ONSITE",
] as const;
const INTERVIEW_STATUS = [
  "DRAFT",
  "SCHEDULED",
  "CONFIRMED",
  "COMPLETED",
  "CANCELLED",
] as const;
const EVAL_TYPE = ["RESUME", "INTERVIEW"] as const;
const EVAL_REC = ["PROCEED", "HOLD", "REJECT"] as const;
const AUTHOR_TYPE = ["AGENT", "HUMAN"] as const;
const SENTIMENT = ["POSITIVE", "NEUTRAL", "NEGATIVE"] as const;
const OFFER_STATUS = [
  "DRAFT",
  "APPROVED",
  "SENT",
  "ACCEPTED",
  "DECLINED",
] as const;

// The MORPH target field on noteTargets per recruiting object.
const NOTE_TARGET_FIELD: Record<string, string> = {
  candidate: "targetCandidateId",
  requisition: "targetRequisitionId",
  application: "targetApplicationId",
  interview: "targetInterviewId",
  evaluation: "targetEvaluationId",
  offer: "targetOfferId",
};

// ---------------------------------------------------------------------------
// Tool builder
// ---------------------------------------------------------------------------

export function buildRecruitingTools(client: TwentyClient) {
  const tools: unknown[] = [];

  const optStr = (desc: string) =>
    Type.Optional(Type.String({ description: desc }));

  // ---- CANDIDATE ----------------------------------------------------------

  const CandidateUpdateContactSchema = Type.Object({
    candidateId: Type.String({ description: "UUID of the candidate." }),
    email: optStr("Primary email. Sets emails.primaryEmail."),
    phone: optStr(
      "Primary phone number (national digits, e.g. '9303678077').",
    ),
    phoneCountryCode: optStr("ISO alpha-2 country code (e.g. 'IN')."),
    phoneCallingCode: optStr("Calling code incl. '+' (e.g. '+91')."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "candidate_update_contact",
        description:
          "Update a candidate's email and/or phone using FLAT inputs. Builds " +
          "Twenty's nested emails/phones internally. At least one of `email` " +
          "or `phone` required. Returns the updated candidate + verification.",
        mutates: true,
        parameters: CandidateUpdateContactSchema,
        run: async (p, c, signal, toolCallId) => {
          const id = assertUuid(
            p.candidateId,
            "candidateId",
            "candidate_update_contact",
          );
          const email = s(p.email);
          const phone = s(p.phone);
          if (!email && !phone) {
            throw new Error(
              "candidate_update_contact: supply at least one of `email` or " +
                "`phone`. No HTTP request was made.",
            );
          }
          const data: Rec = {};
          if (email) {
            data.emails = { primaryEmail: email, additionalEmails: [] };
          }
          if (phone) {
            const phones: Rec = {
              primaryPhoneNumber: phone,
              additionalPhones: [],
            };
            if (s(p.phoneCountryCode)) {
              phones.primaryPhoneCountryCode = s(p.phoneCountryCode).toUpperCase();
            }
            if (s(p.phoneCallingCode)) {
              phones.primaryPhoneCallingCode = s(p.phoneCallingCode);
            }
            data.phones = phones;
          }
          c.logger?.debug?.(
            `candidate_update_contact callId=${toolCallId} id=${id} ` +
              `fields=[${Object.keys(data).join(",")}]`,
          );
          const updated = await patch(c, "candidates", id, data, signal);
          const verification: Rec = {};
          if (data.emails) {
            verification.email = verifyField(updated, "emails.primaryEmail", email);
          }
          if (data.phones) {
            verification.phone = verifyField(
              updated,
              "phones.primaryPhoneNumber",
              phone,
            );
          }
          return { candidate: updated, verification };
        },
      },
      client,
    ),
  );

  const CandidateCreateSchema = Type.Object({
    name: Type.String({ description: "Candidate full name (TEXT field)." }),
    email: optStr("Primary email."),
    phone: optStr("Primary phone number (national digits)."),
    phoneCountryCode: optStr("ISO alpha-2 country code (e.g. 'IN')."),
    phoneCallingCode: optStr("Calling code incl. '+' (e.g. '+91')."),
    source: optStr("Sourcing channel (free text)."),
    skillsTags: optStr("Comma/space separated skills (free text)."),
    resumeUrl: optStr("URL to the candidate's resume."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "candidate_create",
        description:
          "Create a candidate from FLAT inputs. `name` required. Optional " +
          "email/phone are assembled into Twenty's emails/phones composites. " +
          "Returns the created candidate.",
        mutates: true,
        parameters: CandidateCreateSchema,
        run: async (p, c, signal) => {
          const name = s(p.name);
          if (!name) {
            throw new Error(
              "candidate_create: `name` is required. No HTTP request was made.",
            );
          }
          const data: Rec = { name };
          if (s(p.source)) data.source = s(p.source);
          if (s(p.skillsTags)) data.skillsTags = s(p.skillsTags);
          if (s(p.resumeUrl)) data.resumeUrl = s(p.resumeUrl);
          if (s(p.email)) {
            data.emails = { primaryEmail: s(p.email), additionalEmails: [] };
          }
          if (s(p.phone)) {
            const phones: Rec = {
              primaryPhoneNumber: s(p.phone),
              additionalPhones: [],
            };
            if (s(p.phoneCountryCode)) {
              phones.primaryPhoneCountryCode = s(p.phoneCountryCode).toUpperCase();
            }
            if (s(p.phoneCallingCode)) {
              phones.primaryPhoneCallingCode = s(p.phoneCallingCode);
            }
            data.phones = phones;
          }
          const created = await post(c, "candidates", data, signal);
          return { candidate: created };
        },
      },
      client,
    ),
  );

  const CandidateUpdateProfileSchema = Type.Object({
    candidateId: Type.String({ description: "UUID of the candidate." }),
    name: optStr("New candidate name."),
    source: optStr("Sourcing channel."),
    skillsTags: optStr("Skills (free text)."),
    resumeUrl: optStr("Resume URL."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "candidate_update_profile",
        description:
          "Update candidate non-contact profile fields (name, source, " +
          "skillsTags, resumeUrl). At least one field required. For email/" +
          "phone use `candidate_update_contact`.",
        mutates: true,
        parameters: CandidateUpdateProfileSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.candidateId,
            "candidateId",
            "candidate_update_profile",
          );
          const data: Rec = {};
          if (s(p.name)) data.name = s(p.name);
          if (s(p.source)) data.source = s(p.source);
          if (s(p.skillsTags)) data.skillsTags = s(p.skillsTags);
          if (s(p.resumeUrl)) data.resumeUrl = s(p.resumeUrl);
          if (Object.keys(data).length === 0) {
            throw new Error(
              "candidate_update_profile: supply at least one field. No HTTP " +
                "request was made.",
            );
          }
          const updated = await patch(c, "candidates", id, data, signal);
          return { candidate: updated };
        },
      },
      client,
    ),
  );

  // ---- NOTES (works for any recruiting record) ----------------------------

  const AddNoteSchema = Type.Object({
    targetType: Type.String({
      description:
        "Which record the note attaches to: one of candidate, requisition, " +
        "application, interview, evaluation, offer.",
    }),
    targetId: Type.String({ description: "UUID of the target record." }),
    title: optStr("Optional note title."),
    markdown: Type.String({
      description: "Note body as markdown. Stored in bodyV2.markdown.",
    }),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "recruiting_add_note",
        description:
          "Attach a note to a recruiting record. Creates the note, then links " +
          "it via a noteTarget (the two-record flow Twenty requires). Returns " +
          "the note id, noteTarget id, and verification.",
        mutates: true,
        parameters: AddNoteSchema,
        run: async (p, c, signal) => {
          const targetType = s(p.targetType).toLowerCase();
          const targetField = NOTE_TARGET_FIELD[targetType];
          if (!targetField) {
            throw new Error(
              `recruiting_add_note: targetType must be one of ` +
                `[${Object.keys(NOTE_TARGET_FIELD).join(", ")}] (got: ` +
                `${JSON.stringify(p.targetType)}). No HTTP request was made.`,
            );
          }
          const targetId = assertUuid(
            p.targetId,
            "targetId",
            "recruiting_add_note",
          );
          const markdown = s(p.markdown);
          if (!markdown) {
            throw new Error(
              "recruiting_add_note: `markdown` is required. No HTTP request " +
                "was made.",
            );
          }
          // 1. create the note
          const noteBody: Rec = {
            bodyV2: { markdown, blocknote: "" },
          };
          if (s(p.title)) noteBody.title = s(p.title);
          const note = await post(c, "notes", noteBody, signal);
          const noteId = note?.id as string | undefined;
          if (!noteId) {
            throw new Error(
              "recruiting_add_note: note creation returned no id.",
            );
          }
          // 2. link via noteTarget
          const link = await post(
            c,
            "noteTargets",
            { noteId, [targetField]: targetId },
            signal,
          );
          return {
            noteId,
            noteTargetId: link?.id ?? null,
            verification: {
              linked: {
                expected: targetId,
                actual: link?.[targetField] ?? null,
                ok: link?.[targetField] === targetId,
              },
            },
          };
        },
      },
      client,
    ),
  );

  // ---- REQUISITION --------------------------------------------------------

  const RequisitionCreateSchema = Type.Object({
    name: Type.String({ description: "Requisition name/title." }),
    jobTitle: optStr("Job title."),
    department: optStr("Department."),
    location: optStr("Location."),
    employmentType: optStr(
      `Employment type. One of [${EMPLOYMENT_TYPE.join(", ")}].`,
    ),
    experienceRequirements: optStr("Experience requirements (free text)."),
    requiredSkills: optStr("Required skills (free text)."),
    jobDescription: optStr("Full job description."),
    headcount: Type.Optional(Type.Number({ description: "Open headcount." })),
    postingUrl: optStr("Public posting URL."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "requisition_create",
        description:
          "Create a requisition from FLAT inputs. `name` required. " +
          "`employmentType` (if given) is validated against the enum. New " +
          "requisitions start in DRAFT status. Returns the created requisition.",
        mutates: true,
        parameters: RequisitionCreateSchema,
        run: async (p, c, signal) => {
          const name = s(p.name);
          if (!name) {
            throw new Error(
              "requisition_create: `name` is required. No HTTP request was made.",
            );
          }
          const data: Rec = { name };
          for (const f of [
            "jobTitle",
            "department",
            "location",
            "experienceRequirements",
            "requiredSkills",
            "jobDescription",
            "postingUrl",
          ] as const) {
            if (s(p[f])) data[f] = s(p[f]);
          }
          if (s(p.employmentType)) {
            data.employmentType = assertEnum(
              s(p.employmentType),
              EMPLOYMENT_TYPE,
              "employmentType",
              "requisition_create",
            );
          }
          if (typeof p.headcount === "number") data.headcount = p.headcount;
          const created = await post(c, "requisitions", data, signal);
          return { requisition: created };
        },
      },
      client,
    ),
  );

  const RequisitionUpdateSchema = Type.Object({
    requisitionId: Type.String({ description: "UUID of the requisition." }),
    name: optStr("Name."),
    jobTitle: optStr("Job title."),
    department: optStr("Department."),
    location: optStr("Location."),
    employmentType: optStr(
      `Employment type. One of [${EMPLOYMENT_TYPE.join(", ")}].`,
    ),
    experienceRequirements: optStr("Experience requirements."),
    requiredSkills: optStr("Required skills."),
    jobDescription: optStr("Full job description."),
    headcount: Type.Optional(Type.Number({ description: "Open headcount." })),
    postingUrl: optStr("Posting URL."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "requisition_update",
        description:
          "Update requisition details / job description. At least one field " +
          "required. Does NOT change requisitionStatus (use " +
          "`requisition_set_status`).",
        mutates: true,
        parameters: RequisitionUpdateSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.requisitionId,
            "requisitionId",
            "requisition_update",
          );
          const data: Rec = {};
          for (const f of [
            "name",
            "jobTitle",
            "department",
            "location",
            "experienceRequirements",
            "requiredSkills",
            "jobDescription",
            "postingUrl",
          ] as const) {
            if (s(p[f])) data[f] = s(p[f]);
          }
          if (s(p.employmentType)) {
            data.employmentType = assertEnum(
              s(p.employmentType),
              EMPLOYMENT_TYPE,
              "employmentType",
              "requisition_update",
            );
          }
          if (typeof p.headcount === "number") data.headcount = p.headcount;
          if (Object.keys(data).length === 0) {
            throw new Error(
              "requisition_update: supply at least one field. No HTTP request " +
                "was made.",
            );
          }
          const updated = await patch(c, "requisitions", id, data, signal);
          return { requisition: updated };
        },
      },
      client,
    ),
  );

  const RequisitionSetStatusSchema = Type.Object({
    requisitionId: Type.String({ description: "UUID of the requisition." }),
    status: Type.String({
      description: `New status. One of [${REQ_STATUS.join(", ")}].`,
    }),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "requisition_set_status",
        description:
          "LIFECYCLE (approval-gated). Set requisitionStatus to one of " +
          `[${REQ_STATUS.join(", ")}]. Returns updated requisition + verification.`,
        mutates: true,
        parameters: RequisitionSetStatusSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.requisitionId,
            "requisitionId",
            "requisition_set_status",
          );
          const status = assertEnum(
            s(p.status),
            REQ_STATUS,
            "status",
            "requisition_set_status",
          );
          const updated = await patch(
            c,
            "requisitions",
            id,
            { requisitionStatus: status },
            signal,
          );
          return {
            requisition: updated,
            verification: {
              status: verifyField(updated, "requisitionStatus", status),
            },
          };
        },
      },
      client,
    ),
  );

  // ---- APPLICATION --------------------------------------------------------

  const ApplicationCreateSchema = Type.Object({
    candidateId: Type.String({ description: "UUID of the candidate." }),
    requisitionId: Type.String({ description: "UUID of the requisition." }),
    stage: optStr(`Initial stage. One of [${APP_STAGE.join(", ")}]. Default APPLIED.`),
    source: optStr("Application source (free text)."),
    consentStatus: optStr(`Consent. One of [${CONSENT_STATUS.join(", ")}].`),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "application_create",
        description:
          "Create an application linking a candidate to a requisition. Both " +
          "ids required. Optional initial stage/source/consent. Returns the " +
          "created application.",
        mutates: true,
        parameters: ApplicationCreateSchema,
        run: async (p, c, signal) => {
          const candidateId = assertUuid(
            p.candidateId,
            "candidateId",
            "application_create",
          );
          const requisitionId = assertUuid(
            p.requisitionId,
            "requisitionId",
            "application_create",
          );
          const data: Rec = { candidateId, requisitionId };
          data.stage = s(p.stage)
            ? assertEnum(s(p.stage), APP_STAGE, "stage", "application_create")
            : "APPLIED";
          if (s(p.source)) data.source = s(p.source);
          if (s(p.consentStatus)) {
            data.consentStatus = assertEnum(
              s(p.consentStatus),
              CONSENT_STATUS,
              "consentStatus",
              "application_create",
            );
          }
          const created = await post(c, "applications", data, signal);
          return { application: created };
        },
      },
      client,
    ),
  );

  const ApplicationSetStageSchema = Type.Object({
    applicationId: Type.String({ description: "UUID of the application." }),
    stage: Type.String({
      description: `New stage. One of [${APP_STAGE.join(", ")}].`,
    }),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "application_set_stage",
        description:
          "LIFECYCLE (approval-gated). Advance/set application stage to one " +
          `of [${APP_STAGE.join(", ")}]. Returns updated application + verification.`,
        mutates: true,
        parameters: ApplicationSetStageSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.applicationId,
            "applicationId",
            "application_set_stage",
          );
          const stage = assertEnum(
            s(p.stage),
            APP_STAGE,
            "stage",
            "application_set_stage",
          );
          const updated = await patch(c, "applications", id, { stage }, signal);
          return {
            application: updated,
            verification: { stage: verifyField(updated, "stage", stage) },
          };
        },
      },
      client,
    ),
  );

  const ApplicationSetDecisionSchema = Type.Object({
    applicationId: Type.String({ description: "UUID of the application." }),
    recommendation: Type.String({
      description: `Decision. One of [${DECISION_REC.join(", ")}].`,
    }),
    reason: optStr("Decision reason (free text)."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "application_set_decision",
        description:
          "Record an application's decisionRecommendation (+ optional " +
          "decisionReason). Informational; does not change stage.",
        mutates: true,
        parameters: ApplicationSetDecisionSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.applicationId,
            "applicationId",
            "application_set_decision",
          );
          const rec = assertEnum(
            s(p.recommendation),
            DECISION_REC,
            "recommendation",
            "application_set_decision",
          );
          const data: Rec = { decisionRecommendation: rec };
          if (s(p.reason)) data.decisionReason = s(p.reason);
          const updated = await patch(c, "applications", id, data, signal);
          return {
            application: updated,
            verification: {
              recommendation: verifyField(
                updated,
                "decisionRecommendation",
                rec,
              ),
            },
          };
        },
      },
      client,
    ),
  );

  const ApplicationSetConsentSchema = Type.Object({
    applicationId: Type.String({ description: "UUID of the application." }),
    consentStatus: Type.String({
      description: `Consent. One of [${CONSENT_STATUS.join(", ")}].`,
    }),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "application_set_consent",
        description:
          "Set an application's consentStatus to one of " +
          `[${CONSENT_STATUS.join(", ")}].`,
        mutates: true,
        parameters: ApplicationSetConsentSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.applicationId,
            "applicationId",
            "application_set_consent",
          );
          const consent = assertEnum(
            s(p.consentStatus),
            CONSENT_STATUS,
            "consentStatus",
            "application_set_consent",
          );
          const updated = await patch(
            c,
            "applications",
            id,
            { consentStatus: consent },
            signal,
          );
          return {
            application: updated,
            verification: {
              consentStatus: verifyField(updated, "consentStatus", consent),
            },
          };
        },
      },
      client,
    ),
  );

  const ApplicationResumeSummarySchema = Type.Object({
    applicationId: Type.String({ description: "UUID of the application." }),
    summary: Type.String({ description: "Parsed resume summary text." }),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "application_set_resume_summary",
        description:
          "Store a parsed resume summary on an application " +
          "(parsedResumeSummary). Informational write.",
        mutates: true,
        parameters: ApplicationResumeSummarySchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.applicationId,
            "applicationId",
            "application_set_resume_summary",
          );
          const summary = s(p.summary);
          if (!summary) {
            throw new Error(
              "application_set_resume_summary: `summary` is required. No HTTP " +
                "request was made.",
            );
          }
          const updated = await patch(
            c,
            "applications",
            id,
            { parsedResumeSummary: summary },
            signal,
          );
          return { application: updated };
        },
      },
      client,
    ),
  );

  // ---- INTERVIEW ----------------------------------------------------------

  const InterviewScheduleSchema = Type.Object({
    applicationId: Type.String({ description: "UUID of the application." }),
    scheduledAt: Type.String({
      description: "ISO 8601 datetime for the interview start.",
    }),
    interviewType: optStr(`Type. One of [${INTERVIEW_TYPE.join(", ")}].`),
    round: optStr("Round label (free text, e.g. 'Round 1')."),
    durationMinutes: Type.Optional(
      Type.Number({ description: "Duration in minutes." }),
    ),
    timezone: optStr("IANA timezone (e.g. 'Asia/Kolkata')."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "interview_schedule",
        description:
          "Schedule an interview for an application. Creates an interview " +
          "record linked via applicationId with interviewStatus=SCHEDULED. " +
          "`scheduledAt` (ISO datetime) required. Returns the created interview.",
        mutates: true,
        parameters: InterviewScheduleSchema,
        run: async (p, c, signal) => {
          const applicationId = assertUuid(
            p.applicationId,
            "applicationId",
            "interview_schedule",
          );
          const scheduledAt = s(p.scheduledAt);
          if (!scheduledAt) {
            throw new Error(
              "interview_schedule: `scheduledAt` (ISO datetime) is required. " +
                "No HTTP request was made.",
            );
          }
          const data: Rec = {
            applicationId,
            scheduledAt,
            interviewStatus: "SCHEDULED",
          };
          if (s(p.interviewType)) {
            data.interviewType = assertEnum(
              s(p.interviewType),
              INTERVIEW_TYPE,
              "interviewType",
              "interview_schedule",
            );
          }
          if (s(p.round)) data.round = s(p.round);
          if (s(p.timezone)) data.timezone = s(p.timezone);
          if (typeof p.durationMinutes === "number") {
            data.durationMinutes = p.durationMinutes;
          }
          const created = await post(c, "interviews", data, signal);
          return { interview: created };
        },
      },
      client,
    ),
  );

  const InterviewSetStatusSchema = Type.Object({
    interviewId: Type.String({ description: "UUID of the interview." }),
    status: Type.String({
      description: `New status. One of [${INTERVIEW_STATUS.join(", ")}].`,
    }),
    endedAt: optStr("ISO datetime when the interview ended (for COMPLETED)."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "interview_set_status",
        description:
          "LIFECYCLE (approval-gated). Set interviewStatus to one of " +
          `[${INTERVIEW_STATUS.join(", ")}]. Optionally set endedAt. Returns ` +
          "updated interview + verification.",
        mutates: true,
        parameters: InterviewSetStatusSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.interviewId,
            "interviewId",
            "interview_set_status",
          );
          const status = assertEnum(
            s(p.status),
            INTERVIEW_STATUS,
            "status",
            "interview_set_status",
          );
          const data: Rec = { interviewStatus: status };
          if (s(p.endedAt)) data.endedAt = s(p.endedAt);
          const updated = await patch(c, "interviews", id, data, signal);
          return {
            interview: updated,
            verification: {
              status: verifyField(updated, "interviewStatus", status),
            },
          };
        },
      },
      client,
    ),
  );

  // ---- EVALUATION ---------------------------------------------------------

  const EvaluationCreateSchema = Type.Object({
    interviewId: Type.String({ description: "UUID of the interview." }),
    evaluationType: Type.String({
      description: `Type. One of [${EVAL_TYPE.join(", ")}].`,
    }),
    recommendation: optStr(`Recommendation. One of [${EVAL_REC.join(", ")}].`),
    summary: optStr("Evaluation summary."),
    strengths: optStr("Strengths (free text)."),
    weaknesses: optStr("Weaknesses (free text)."),
    overallScore: Type.Optional(
      Type.Number({ description: "Overall numeric score." }),
    ),
    sentiment: optStr(`Sentiment. One of [${SENTIMENT.join(", ")}].`),
    authorType: optStr(`Author. One of [${AUTHOR_TYPE.join(", ")}]. Default AGENT.`),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "evaluation_create",
        description:
          "Record an evaluation for an interview (evaluationStatus=DRAFT). " +
          "`interviewId` + `evaluationType` required. Returns the created " +
          "evaluation.",
        mutates: true,
        parameters: EvaluationCreateSchema,
        run: async (p, c, signal) => {
          const interviewId = assertUuid(
            p.interviewId,
            "interviewId",
            "evaluation_create",
          );
          const evaluationType = assertEnum(
            s(p.evaluationType),
            EVAL_TYPE,
            "evaluationType",
            "evaluation_create",
          );
          const data: Rec = {
            interviewId,
            evaluationType,
            evaluationStatus: "DRAFT",
            authorType: s(p.authorType)
              ? assertEnum(
                  s(p.authorType),
                  AUTHOR_TYPE,
                  "authorType",
                  "evaluation_create",
                )
              : "AGENT",
          };
          if (s(p.recommendation)) {
            data.recommendation = assertEnum(
              s(p.recommendation),
              EVAL_REC,
              "recommendation",
              "evaluation_create",
            );
          }
          if (s(p.sentiment)) {
            data.sentiment = assertEnum(
              s(p.sentiment),
              SENTIMENT,
              "sentiment",
              "evaluation_create",
            );
          }
          if (s(p.summary)) data.summary = s(p.summary);
          if (s(p.strengths)) data.strengths = s(p.strengths);
          if (s(p.weaknesses)) data.weaknesses = s(p.weaknesses);
          if (typeof p.overallScore === "number") {
            data.overallScore = p.overallScore;
          }
          const created = await post(c, "evaluations", data, signal);
          return { evaluation: created };
        },
      },
      client,
    ),
  );

  const EvaluationFinalizeSchema = Type.Object({
    evaluationId: Type.String({ description: "UUID of the evaluation." }),
    recommendation: optStr(
      `Final recommendation. One of [${EVAL_REC.join(", ")}].`,
    ),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "evaluation_finalize",
        description:
          "LIFECYCLE (approval-gated). Mark an evaluation FINAL " +
          "(evaluationStatus=FINAL), optionally setting the final " +
          "recommendation. Returns updated evaluation + verification.",
        mutates: true,
        parameters: EvaluationFinalizeSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(
            p.evaluationId,
            "evaluationId",
            "evaluation_finalize",
          );
          const data: Rec = { evaluationStatus: "FINAL" };
          if (s(p.recommendation)) {
            data.recommendation = assertEnum(
              s(p.recommendation),
              EVAL_REC,
              "recommendation",
              "evaluation_finalize",
            );
          }
          const updated = await patch(c, "evaluations", id, data, signal);
          return {
            evaluation: updated,
            verification: {
              status: verifyField(updated, "evaluationStatus", "FINAL"),
            },
          };
        },
      },
      client,
    ),
  );

  // ---- OFFER --------------------------------------------------------------

  const OfferCreateSchema = Type.Object({
    applicationId: Type.String({ description: "UUID of the application." }),
    salary: Type.Optional(Type.Number({ description: "Salary amount." })),
    offerCurrency: optStr("Currency code (e.g. 'INR', 'USD')."),
    termsSummary: optStr("Summary of offer terms."),
    startDate: optStr("Start date (YYYY-MM-DD)."),
    expiryDate: optStr("Offer expiry date (YYYY-MM-DD)."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "offer_create",
        description:
          "Draft an offer for an application (offerStatus=DRAFT). " +
          "`applicationId` required. Returns the created offer.",
        mutates: true,
        parameters: OfferCreateSchema,
        run: async (p, c, signal) => {
          const applicationId = assertUuid(
            p.applicationId,
            "applicationId",
            "offer_create",
          );
          const data: Rec = { applicationId, offerStatus: "DRAFT" };
          if (typeof p.salary === "number") data.salary = p.salary;
          if (s(p.offerCurrency)) data.offerCurrency = s(p.offerCurrency);
          if (s(p.termsSummary)) data.termsSummary = s(p.termsSummary);
          if (s(p.startDate)) data.startDate = s(p.startDate);
          if (s(p.expiryDate)) data.expiryDate = s(p.expiryDate);
          const created = await post(c, "offers", data, signal);
          return { offer: created };
        },
      },
      client,
    ),
  );

  const OfferSetStatusSchema = Type.Object({
    offerId: Type.String({ description: "UUID of the offer." }),
    status: Type.String({
      description: `New status. One of [${OFFER_STATUS.join(", ")}].`,
    }),
    declineReason: optStr("Reason (when status=DECLINED)."),
  });
  tools.push(
    defineTwentyTool(
      {
        name: "offer_set_status",
        description:
          "LIFECYCLE (approval-gated). Set offerStatus to one of " +
          `[${OFFER_STATUS.join(", ")}]. Sets sentAt on SENT and respondedAt ` +
          "on ACCEPTED/DECLINED. Returns updated offer + verification.",
        mutates: true,
        parameters: OfferSetStatusSchema,
        run: async (p, c, signal) => {
          const id = assertUuid(p.offerId, "offerId", "offer_set_status");
          const status = assertEnum(
            s(p.status),
            OFFER_STATUS,
            "status",
            "offer_set_status",
          );
          const data: Rec = { offerStatus: status };
          const nowIso = new Date().toISOString();
          if (status === "SENT") data.sentAt = nowIso;
          if (status === "ACCEPTED" || status === "DECLINED") {
            data.respondedAt = nowIso;
          }
          if (status === "DECLINED" && s(p.declineReason)) {
            data.declineReason = s(p.declineReason);
          }
          const updated = await patch(c, "offers", id, data, signal);
          return {
            offer: updated,
            verification: {
              status: verifyField(updated, "offerStatus", status),
            },
          };
        },
      },
      client,
    ),
  );

  return tools as ReturnType<typeof defineTwentyTool<TSchema>>[];
}
