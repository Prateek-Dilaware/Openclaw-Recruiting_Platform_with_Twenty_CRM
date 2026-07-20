// Unit tests for the recruiting-specific typed tools. The load-bearing
// guarantee: the MODEL passes flat scalars; the TOOL builds Twenty's wire
// format, validates enums/UUIDs BEFORE any network call, and forwards a
// populated body.

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";

import { resolveConfig } from "../../src/config.js";
import { buildRecruitingTools } from "../../src/tools/recruiting.js";
import { TwentyClient } from "../../src/twenty-client.js";

interface Capture {
  url: string;
  method: string;
  body: unknown;
}

function fakeFetch(
  responder: (method: string, url: string, body: unknown) => unknown,
  capture: Capture[],
): typeof fetch {
  return (async (input: RequestInfo | URL, init?: RequestInit) => {
    const method = String(init?.method ?? "GET");
    const url = String(input);
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    capture.push({ url, method, body });
    return new Response(JSON.stringify(responder(method, url, body)), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
}

const silent = {
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
};

const CID = "12517aff-9de7-4d42-bd0a-f7d3dfb881eb";
const RID = "22517aff-9de7-4d42-bd0a-f7d3dfb881eb";
const AID = "32517aff-9de7-4d42-bd0a-f7d3dfb881eb";
const IID = "42517aff-9de7-4d42-bd0a-f7d3dfb881eb";
const EID = "52517aff-9de7-4d42-bd0a-f7d3dfb881eb";
const OID = "62517aff-9de7-4d42-bd0a-f7d3dfb881eb";

// Echo the write body back under a single-keyed envelope; NOTE creation
// returns an id so the note-link flow can proceed.
function responder(method: string, url: string, body: unknown): unknown {
  const b = (body ?? {}) as Record<string, unknown>;
  if (url.includes("/rest/notes")) {
    return { data: { createNote: { id: "note-1", ...b } } };
  }
  if (url.includes("/rest/noteTargets")) {
    return { data: { createNoteTarget: { id: "nt-1", ...b } } };
  }
  return { data: { result: { id: "rec-1", ...b } } };
}

interface ToolHandle {
  name: string;
  execute: (
    id: string,
    params: unknown,
  ) => Promise<{ details?: { status: string; data?: unknown; error?: string } }>;
}

function tools(calls: Capture[]): Record<string, ToolHandle> {
  const config = resolveConfig({
    apiKey: "k",
    serverUrl: "https://crm.test.local",
    allowedWorkspaceIds: ["ws-1"],
    defaultWorkspaceId: "ws-1",
  });
  const client = new TwentyClient(config, silent, {
    fetchImpl: fakeFetch(responder, calls),
  });
  return Object.fromEntries(
    buildRecruitingTools(client).map((t) => [
      (t as unknown as ToolHandle).name,
      t as unknown as ToolHandle,
    ]),
  );
}

function lastBody(calls: Capture[]): Record<string, unknown> {
  return calls[calls.length - 1].body as Record<string, unknown>;
}

describe("candidate_create", () => {
  it("assembles emails/phones composites from flat inputs", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).candidate_create.execute("c", {
      name: "Ada Lovelace",
      email: "ada@example.test",
      phone: "9303678077",
      phoneCountryCode: "in",
      phoneCallingCode: "+91",
      skillsTags: "math",
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.name, "Ada Lovelace");
    assert.deepEqual(body.emails, {
      primaryEmail: "ada@example.test",
      additionalEmails: [],
    });
    assert.equal(
      (body.phones as Record<string, unknown>).primaryPhoneCountryCode,
      "IN",
    );
    assert.equal(body.skillsTags, "math");
  });

  it("rejects missing name before any HTTP call", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).candidate_create.execute("c", { name: "" });
    assert.equal(calls.length, 0);
    assert.equal(r.details?.status, "failed");
    assert.match(r.details?.error ?? "", /name.*required/i);
  });
});

describe("recruiting_add_note", () => {
  it("creates a note then links via the correct MORPH target field", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).recruiting_add_note.execute("n", {
      targetType: "candidate",
      targetId: CID,
      markdown: "good communicator",
      title: "Screen note",
    });
    assert.equal(r.details?.status, "ok");
    // two calls: POST notes, POST noteTargets
    assert.equal(calls.length, 2);
    assert.ok(calls[0].url.endsWith("/rest/notes"));
    assert.ok(calls[1].url.endsWith("/rest/noteTargets"));
    assert.deepEqual(calls[1].body, {
      noteId: "note-1",
      targetCandidateId: CID,
    });
  });

  it("rejects an unknown targetType before any HTTP call", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).recruiting_add_note.execute("n", {
      targetType: "company",
      targetId: CID,
      markdown: "x",
    });
    assert.equal(calls.length, 0);
    assert.match(r.details?.error ?? "", /targetType must be one of/i);
  });
});

describe("requisition_create + set_status", () => {
  it("validates employmentType enum and forwards fields", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).requisition_create.execute("r", {
      name: "Backend Eng",
      jobTitle: "Engineer",
      employmentType: "full_time",
      headcount: 2,
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.employmentType, "FULL_TIME");
    assert.equal(body.headcount, 2);
  });

  it("rejects an invalid employmentType before any HTTP call", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).requisition_create.execute("r", {
      name: "X",
      employmentType: "FREELANCE",
    });
    assert.equal(calls.length, 0);
    assert.match(r.details?.error ?? "", /employmentType.* must be one of/i);
  });

  it("set_status validates enum and PATCHes requisitionStatus", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).requisition_set_status.execute("r", {
      requisitionId: RID,
      status: "posted",
    });
    assert.equal(r.details?.status, "ok");
    assert.equal(calls[0].method, "PATCH");
    assert.deepEqual(lastBody(calls), { requisitionStatus: "POSTED" });
  });
});

describe("application_create + set_stage", () => {
  it("requires both FK ids and defaults stage to APPLIED", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).application_create.execute("a", {
      candidateId: CID,
      requisitionId: RID,
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.candidateId, CID);
    assert.equal(body.requisitionId, RID);
    assert.equal(body.stage, "APPLIED");
  });

  it("rejects an invalid candidateId before any HTTP call", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).application_create.execute("a", {
      candidateId: "nope",
      requisitionId: RID,
    });
    assert.equal(calls.length, 0);
    assert.match(r.details?.error ?? "", /candidateId.* must be a valid UUID/i);
  });

  it("set_stage validates the stage enum", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).application_set_stage.execute("a", {
      applicationId: AID,
      stage: "screening",
    });
    assert.equal(r.details?.status, "ok");
    assert.deepEqual(lastBody(calls), { stage: "SCREENING" });
  });
});

describe("interview_schedule + set_status", () => {
  it("creates an interview linked via applicationId with SCHEDULED", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).interview_schedule.execute("i", {
      applicationId: AID,
      scheduledAt: "2026-08-01T10:00:00.000Z",
      interviewType: "technical",
      durationMinutes: 45,
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.applicationId, AID);
    assert.equal(body.interviewStatus, "SCHEDULED");
    assert.equal(body.interviewType, "TECHNICAL");
    assert.equal(body.durationMinutes, 45);
  });

  it("requires scheduledAt", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).interview_schedule.execute("i", {
      applicationId: AID,
      scheduledAt: "",
    });
    assert.equal(calls.length, 0);
    assert.match(r.details?.error ?? "", /scheduledAt.*required/i);
  });

  it("set_status validates and can set endedAt", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).interview_set_status.execute("i", {
      interviewId: IID,
      status: "completed",
      endedAt: "2026-08-01T11:00:00.000Z",
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.interviewStatus, "COMPLETED");
    assert.equal(body.endedAt, "2026-08-01T11:00:00.000Z");
  });
});

describe("evaluation_create + finalize", () => {
  it("creates DRAFT with validated type/recommendation", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).evaluation_create.execute("e", {
      interviewId: IID,
      evaluationType: "interview",
      recommendation: "proceed",
      overallScore: 8,
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.interviewId, IID);
    assert.equal(body.evaluationType, "INTERVIEW");
    assert.equal(body.recommendation, "PROCEED");
    assert.equal(body.evaluationStatus, "DRAFT");
    assert.equal(body.authorType, "AGENT");
  });

  it("finalize sets evaluationStatus FINAL", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).evaluation_finalize.execute("e", {
      evaluationId: EID,
      recommendation: "hold",
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.evaluationStatus, "FINAL");
    assert.equal(body.recommendation, "HOLD");
  });
});

describe("offer_create + set_status", () => {
  it("drafts an offer linked to an application", async () => {
    const calls: Capture[] = [];
    const r = await tools(calls).offer_create.execute("o", {
      applicationId: AID,
      salary: 120000,
      offerCurrency: "INR",
    });
    assert.equal(r.details?.status, "ok");
    const body = lastBody(calls);
    assert.equal(body.applicationId, AID);
    assert.equal(body.offerStatus, "DRAFT");
    assert.equal(body.salary, 120000);
  });

  it("set_status SENT stamps sentAt; DECLINED stamps respondedAt+reason", async () => {
    const calls: Capture[] = [];
    const t = tools(calls);
    const sent = await t.offer_set_status.execute("o", {
      offerId: OID,
      status: "sent",
    });
    assert.equal(sent.details?.status, "ok");
    let body = lastBody(calls);
    assert.equal(body.offerStatus, "SENT");
    assert.ok(typeof body.sentAt === "string");

    const dec = await t.offer_set_status.execute("o", {
      offerId: OID,
      status: "declined",
      declineReason: "comp",
    });
    assert.equal(dec.details?.status, "ok");
    body = lastBody(calls);
    assert.equal(body.offerStatus, "DECLINED");
    assert.ok(typeof body.respondedAt === "string");
    assert.equal(body.declineReason, "comp");
  });
});
