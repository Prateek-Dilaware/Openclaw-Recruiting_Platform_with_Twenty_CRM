// LIVE end-to-end recruiting flow against the running Twenty instance, using
// the DEPLOYED plugin artifact. Exercises EVERY recruiting tool, verifies via
// read-back, and cleans up all created records. Exits non-zero on any failure.
//
// Flow: create candidate -> update contact -> update profile -> create
// requisition -> update -> set status -> create application -> set stage ->
// set decision -> set consent -> set resume summary -> add notes -> schedule
// interview -> set interview status -> create evaluation -> finalize ->
// create offer -> set offer status. Then cleanup (soft-delete).

import { readFileSync } from "node:fs";

const pluginRoot = "/home/node/.openclaw/extensions/twenty-openclaw/dist";
const cfg = JSON.parse(
  readFileSync("/home/node/.openclaw/openclaw.json", "utf8"),
).plugins.entries["twenty-openclaw"].config;

const { TwentyClient } = await import(`${pluginRoot}/twenty-client.js`);
const { resolveConfig } = await import(`${pluginRoot}/config.js`);
const { buildRecruitingTools } = await import(`${pluginRoot}/tools/recruiting.js`);
const { buildRecordTools } = await import(`${pluginRoot}/tools/records.js`);

const silent = { debug() {}, info() {}, warn() {}, error() {} };
const client = new TwentyClient(
  resolveConfig({
    apiKey: cfg.apiKey,
    serverUrl: cfg.serverUrl,
    allowedWorkspaceIds: [cfg.defaultWorkspaceId],
    defaultWorkspaceId: cfg.defaultWorkspaceId,
  }),
  silent,
);
const R = Object.fromEntries(buildRecruitingTools(client).map((t) => [t.name, t]));
const REC = Object.fromEntries(buildRecordTools(client).map((t) => [t.name, t]));

let pass = 0;
let fail = 0;
const ok = (m) => { pass++; console.log(`  \u2713 ${m}`); };
const bad = (m) => { fail++; console.log(`  \u2717 ${m}`); };

async function read(entity, id) {
  const r = await REC.twenty_record_get.execute("r", { entity, id, depth: 0 });
  return r.details?.data ?? null;
}
function okStatus(r, label) {
  if (r.details?.status === "ok") return true;
  bad(`${label}: ${r.details?.error ?? JSON.stringify(r.details)}`);
  return false;
}

const created = { candidates: [], requisitions: [], applications: [], interviews: [], evaluations: [], offers: [], notes: [] };

try {
  // 1. candidate_create
  console.log("[1] candidate_create");
  let r = await R.candidate_create.execute("t", {
    name: "ZZ Flow Candidate", email: "zz.flow@example.test",
    phone: "9303678077", phoneCountryCode: "IN", phoneCallingCode: "+91",
    skillsTags: "typescript,node",
  });
  const candId = r.details?.data?.candidate?.id;
  if (okStatus(r, "candidate_create") && candId) { created.candidates.push(candId); ok(`candidate ${candId}`); }

  // 2. candidate_update_contact
  console.log("[2] candidate_update_contact");
  r = await R.candidate_update_contact.execute("t", { candidateId: candId, email: "zz.flow2@example.test" });
  { const a = await read("candidates", candId); a?.emails?.primaryEmail === "zz.flow2@example.test" ? ok("email updated") : bad(`email got ${a?.emails?.primaryEmail}`); }

  // 3. candidate_update_profile
  console.log("[3] candidate_update_profile");
  r = await R.candidate_update_profile.execute("t", { candidateId: candId, source: "referral" });
  { const a = await read("candidates", candId); a?.source === "referral" ? ok("source updated") : bad(`source got ${a?.source}`); }

  // 4. requisition_create
  console.log("[4] requisition_create");
  r = await R.requisition_create.execute("t", { name: "ZZ Flow Req", jobTitle: "Engineer", employmentType: "FULL_TIME", headcount: 1 });
  const reqId = r.details?.data?.requisition?.id;
  if (okStatus(r, "requisition_create") && reqId) { created.requisitions.push(reqId); ok(`requisition ${reqId}`); }

  // 5. requisition_update
  console.log("[5] requisition_update");
  r = await R.requisition_update.execute("t", { requisitionId: reqId, department: "Engineering" });
  { const a = await read("requisitions", reqId); a?.department === "Engineering" ? ok("department updated") : bad(`department got ${a?.department}`); }

  // 6. requisition_set_status
  console.log("[6] requisition_set_status");
  r = await R.requisition_set_status.execute("t", { requisitionId: reqId, status: "APPROVED" });
  { const a = await read("requisitions", reqId); a?.requisitionStatus === "APPROVED" ? ok("status APPROVED") : bad(`status got ${a?.requisitionStatus}`); }

  // 7. application_create
  console.log("[7] application_create");
  r = await R.application_create.execute("t", { candidateId: candId, requisitionId: reqId, stage: "APPLIED", consentStatus: "GRANTED" });
  const appId = r.details?.data?.application?.id;
  if (okStatus(r, "application_create") && appId) { created.applications.push(appId); ok(`application ${appId}`); }

  // 8. application_set_stage
  console.log("[8] application_set_stage");
  r = await R.application_set_stage.execute("t", { applicationId: appId, stage: "SCREENING" });
  { const a = await read("applications", appId); a?.stage === "SCREENING" ? ok("stage SCREENING") : bad(`stage got ${a?.stage}`); }

  // 9. application_set_decision
  console.log("[9] application_set_decision");
  r = await R.application_set_decision.execute("t", { applicationId: appId, recommendation: "PROCEED", reason: "strong fit" });
  { const a = await read("applications", appId); a?.decisionRecommendation === "PROCEED" ? ok("decision PROCEED") : bad(`decision got ${a?.decisionRecommendation}`); }

  // 10. application_set_consent
  console.log("[10] application_set_consent");
  r = await R.application_set_consent.execute("t", { applicationId: appId, consentStatus: "WITHDRAWN" });
  { const a = await read("applications", appId); a?.consentStatus === "WITHDRAWN" ? ok("consent WITHDRAWN") : bad(`consent got ${a?.consentStatus}`); }

  // 11. application_set_resume_summary
  console.log("[11] application_set_resume_summary");
  r = await R.application_set_resume_summary.execute("t", { applicationId: appId, summary: "5y TS/Node." });
  { const a = await read("applications", appId); a?.parsedResumeSummary === "5y TS/Node." ? ok("resume summary set") : bad(`summary got ${a?.parsedResumeSummary}`); }

  // 12. recruiting_add_note (on candidate)
  console.log("[12] recruiting_add_note");
  r = await R.recruiting_add_note.execute("t", { targetType: "candidate", targetId: candId, markdown: "Great comms", title: "Screen" });
  if (okStatus(r, "recruiting_add_note") && r.details?.data?.noteId) {
    created.notes.push(r.details.data.noteId);
    r.details.data.verification?.linked?.ok ? ok("note linked to candidate") : bad("note link not verified");
  }

  // 13. interview_schedule
  console.log("[13] interview_schedule");
  r = await R.interview_schedule.execute("t", { applicationId: appId, scheduledAt: "2026-08-01T10:00:00.000Z", interviewType: "TECHNICAL", durationMinutes: 45, timezone: "Asia/Kolkata" });
  const intId = r.details?.data?.interview?.id;
  if (okStatus(r, "interview_schedule") && intId) { created.interviews.push(intId); const a = await read("interviews", intId); a?.interviewStatus === "SCHEDULED" ? ok(`interview ${intId} SCHEDULED`) : bad(`interview status ${a?.interviewStatus}`); }

  // 14. interview_set_status
  console.log("[14] interview_set_status");
  r = await R.interview_set_status.execute("t", { interviewId: intId, status: "COMPLETED", endedAt: "2026-08-01T10:45:00.000Z" });
  { const a = await read("interviews", intId); a?.interviewStatus === "COMPLETED" ? ok("interview COMPLETED") : bad(`interview status ${a?.interviewStatus}`); }

  // 15. evaluation_create
  console.log("[15] evaluation_create");
  r = await R.evaluation_create.execute("t", { interviewId: intId, evaluationType: "INTERVIEW", recommendation: "PROCEED", overallScore: 8, sentiment: "POSITIVE", summary: "solid" });
  const evalId = r.details?.data?.evaluation?.id;
  if (okStatus(r, "evaluation_create") && evalId) { created.evaluations.push(evalId); const a = await read("evaluations", evalId); a?.evaluationStatus === "DRAFT" ? ok(`evaluation ${evalId} DRAFT`) : bad(`eval status ${a?.evaluationStatus}`); }

  // 16. evaluation_finalize
  console.log("[16] evaluation_finalize");
  r = await R.evaluation_finalize.execute("t", { evaluationId: evalId, recommendation: "PROCEED" });
  { const a = await read("evaluations", evalId); a?.evaluationStatus === "FINAL" ? ok("evaluation FINAL") : bad(`eval status ${a?.evaluationStatus}`); }

  // 17. offer_create
  console.log("[17] offer_create");
  r = await R.offer_create.execute("t", { applicationId: appId, salary: 1500000, offerCurrency: "INR", termsSummary: "Annual", startDate: "2026-09-01" });
  const offerId = r.details?.data?.offer?.id;
  if (okStatus(r, "offer_create") && offerId) { created.offers.push(offerId); const a = await read("offers", offerId); a?.offerStatus === "DRAFT" ? ok(`offer ${offerId} DRAFT`) : bad(`offer status ${a?.offerStatus}`); }

  // 18. offer_set_status
  console.log("[18] offer_set_status");
  r = await R.offer_set_status.execute("t", { offerId, status: "SENT" });
  { const a = await read("offers", offerId); a?.offerStatus === "SENT" && a?.sentAt ? ok("offer SENT + sentAt stamped") : bad(`offer status ${a?.offerStatus} sentAt ${a?.sentAt}`); }

  // Negative checks
  console.log("[neg] enum + uuid + empty guards");
  r = await R.application_set_stage.execute("t", { applicationId: appId, stage: "BOGUS" });
  (r.details?.status === "failed" && /must be one of/i.test(r.details?.error ?? "")) ? ok("bad enum rejected") : bad("bad enum not rejected");
  r = await R.candidate_create.execute("t", { name: "" });
  (r.details?.status === "failed") ? ok("empty candidate name rejected") : bad("empty name not rejected");
} finally {
  console.log("[cleanup] soft-deleting created records");
  const order = ["offers", "evaluations", "interviews", "notes", "applications", "requisitions", "candidates"];
  for (const entity of order) {
    for (const id of created[entity]) {
      await REC.twenty_record_delete.execute("d", { entity, id }).catch(() => {});
    }
  }
  console.log("  cleanup done");
}

console.log("");
console.log(`RESULT: ${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
