// LIVE end-to-end test of `candidate_update_contact` against the running
// Twenty instance, using the DEPLOYED plugin artifact.
//
// Creates a throwaway candidate, exercises the 5 cases, verifies each result
// by RE-READING from Twenty, then soft-deletes the candidate. Exits non-zero
// on any failure.
//
// Cases:
//   1. Update email       -> verify CRM
//   2. Update phone       -> verify CRM
//   3. Update email+phone -> verify CRM
//   4. Invalid candidate id -> proper error, no mutation
//   5. Empty update       -> validation error, NO HTTP request

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
const recruiting = Object.fromEntries(
  buildRecruitingTools(client).map((t) => [t.name, t]),
);
const records = Object.fromEntries(
  buildRecordTools(client).map((t) => [t.name, t]),
);

let pass = 0;
let fail = 0;
const ok = (m) => {
  pass++;
  console.log(`  \u2713 ${m}`);
};
const bad = (m) => {
  fail++;
  console.log(`  \u2717 ${m}`);
};

async function readCandidate(id) {
  const r = await records.twenty_record_get.execute("r", {
    entity: "candidates",
    id,
    depth: 0,
  });
  return r.details?.data ?? null;
}

// --- Setup: create a throwaway candidate -----------------------------------
console.log("[setup] creating throwaway candidate");
const created = await records.twenty_record_create.execute("c", {
  entity: "candidates",
  data: { name: "ZZ Live Test Candidate" },
});
const cid = created.details?.data?.id;
if (!cid) {
  console.log("FATAL: could not create test candidate", JSON.stringify(created.details));
  process.exit(2);
}
console.log(`  created candidate id=${cid}`);

try {
  // --- Case 1: email ---
  console.log("[1] update email");
  {
    const email = `zz.livetest.${Date.now()}@example.test`;
    const r = await recruiting.candidate_update_contact.execute("e", {
      candidateId: cid,
      email,
    });
    const after = await readCandidate(cid);
    if (r.details?.status === "ok" && after?.emails?.primaryEmail === email) {
      ok(`email persisted in CRM: ${after.emails.primaryEmail}`);
    } else {
      bad(`email not persisted. status=${r.details?.status} got=${after?.emails?.primaryEmail}`);
    }
  }

  // --- Case 2: phone ---
  console.log("[2] update phone");
  {
    const phone = "9303678077";
    const r = await recruiting.candidate_update_contact.execute("p", {
      candidateId: cid,
      phone,
      phoneCountryCode: "IN",
      phoneCallingCode: "+91",
    });
    const after = await readCandidate(cid);
    if (
      r.details?.status === "ok" &&
      after?.phones?.primaryPhoneNumber === phone &&
      after?.phones?.primaryPhoneCountryCode === "IN"
    ) {
      ok(`phone persisted: ${after.phones.primaryPhoneNumber} (${after.phones.primaryPhoneCountryCode})`);
    } else {
      bad(`phone not persisted. status=${r.details?.status} got=${JSON.stringify(after?.phones)}`);
    }
  }

  // --- Case 3: email + phone together ---
  // NOTE: Twenty validates phone numbers server-side (INVALID_PHONE_NUMBER),
  // so a realistic number + calling code is required. This also demonstrates
  // the tool faithfully surfaces Twenty's validation instead of silently
  // no-op'ing.
  console.log("[3] update email + phone together");
  {
    const email = `zz.both.${Date.now()}@example.test`;
    const phone = "9303678078";
    const r = await recruiting.candidate_update_contact.execute("b", {
      candidateId: cid,
      email,
      phone,
      phoneCountryCode: "IN",
      phoneCallingCode: "+91",
    });
    const after = await readCandidate(cid);
    if (
      r.details?.status === "ok" &&
      after?.emails?.primaryEmail === email &&
      after?.phones?.primaryPhoneNumber === phone
    ) {
      ok(`both persisted: email=${after.emails.primaryEmail} phone=${after.phones.primaryPhoneNumber}`);
    } else {
      bad(`both not persisted. status=${r.details?.status} email=${after?.emails?.primaryEmail} phone=${after?.phones?.primaryPhoneNumber}`);
    }
  }

  // --- Case 4: invalid candidate id ---
  console.log("[4] invalid candidate id");
  {
    const r = await recruiting.candidate_update_contact.execute("i", {
      candidateId: "not-a-uuid",
      email: "x@y.test",
    });
    if (
      r.details?.status === "failed" &&
      /must be a valid UUID/i.test(r.details?.error ?? "")
    ) {
      ok(`invalid id rejected: ${r.details.error}`);
    } else {
      bad(`invalid id not rejected properly. status=${r.details?.status} error=${r.details?.error}`);
    }
  }

  // --- Case 5: empty update ---
  console.log("[5] empty update (no email/phone)");
  {
    const r = await recruiting.candidate_update_contact.execute("z", {
      candidateId: cid,
    });
    if (
      r.details?.status === "failed" &&
      /at least one of/i.test(r.details?.error ?? "") &&
      /No HTTP request was made/i.test(r.details?.error ?? "")
    ) {
      ok(`empty update rejected with no HTTP: ${r.details.error}`);
    } else {
      bad(`empty update not rejected properly. status=${r.details?.status} error=${r.details?.error}`);
    }
  }
} finally {
  // --- Cleanup: soft-delete the throwaway candidate ---
  console.log("[cleanup] soft-deleting test candidate");
  const del = await records.twenty_record_delete.execute("d", {
    entity: "candidates",
    id: cid,
  });
  console.log(`  delete status=${del.details?.status}`);
}

console.log("");
console.log(`RESULT: ${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
