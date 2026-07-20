// Live verification of the maintained Twenty plugin against a running
// Twenty instance. Proves — from the DEPLOYED plugin artifact — that:
//
//   1. Metadata envelope compatibility works (direct-array format):
//        twenty_metadata_objects_list returns a non-empty catalog.
//   2. Object discovery + field listing works (metadataItem path).
//   3. A read works (twenty_record_list on a discovered entity).
//   4. The Phase D empty-update guard rejects data:{} BEFORE any HTTP call.
//   5. workspace_info reports a non-zero object count consistent with (1).
//
// It is intentionally NON-MUTATING: it never creates/updates/deletes a
// real record. The empty-update guard is proven with a fetch spy that
// asserts the network was never touched.
//
// Usage (inside the openclaw container):
//   node verify_twenty_plugin.mjs --plugin-root <dist-dir>
// Config (serverUrl + apiKey) is read from the plugin entry in
// openclaw.json, or from TWENTY_SERVER_URL / TWENTY_API_KEY /
// TWENTY_WORKSPACE_ID env vars as a fallback.

import { readFileSync, existsSync } from "node:fs";

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const pluginRoot = arg("--plugin-root", process.env.TWENTY_PLUGIN_ROOT);
if (!pluginRoot) {
  console.error(
    "FATAL: pass --plugin-root <dist-dir> or set TWENTY_PLUGIN_ROOT.",
  );
  process.exit(2);
}

const configPath = arg(
  "--config",
  process.env.OPENCLAW_CONFIG_PATH ?? "/home/node/.openclaw/openclaw.json",
);

function resolveConfigFromOpenClaw() {
  try {
    if (!existsSync(configPath)) return {};
    const json = JSON.parse(readFileSync(configPath, "utf8"));
    const cfg = json?.plugins?.entries?.["twenty-openclaw"]?.config ?? {};
    return {
      serverUrl: cfg.serverUrl,
      apiKey: cfg.apiKey,
      workspaceId: cfg.defaultWorkspaceId,
    };
  } catch {
    return {};
  }
}

const fromConfig = resolveConfigFromOpenClaw();
const serverUrl = fromConfig.serverUrl ?? process.env.TWENTY_SERVER_URL;
const apiKey = fromConfig.apiKey ?? process.env.TWENTY_API_KEY;
const workspaceId =
  fromConfig.workspaceId ?? process.env.TWENTY_WORKSPACE_ID ?? "";

if (!serverUrl || !apiKey) {
  console.error(
    "FATAL: could not resolve serverUrl/apiKey from openclaw.json or env.",
  );
  process.exit(2);
}

const { TwentyClient } = await import(`${pluginRoot}/twenty-client.js`);
const { resolveConfig } = await import(`${pluginRoot}/config.js`);
const { buildMetadataTools } = await import(`${pluginRoot}/tools/metadata.js`);
const { buildWorkspaceTools } = await import(`${pluginRoot}/tools/workspace.js`);
const { buildRecordTools } = await import(`${pluginRoot}/tools/records.js`);

const silent = { debug() {}, info() {}, warn() {}, error() {} };

let pass = 0;
let fail = 0;
function ok(m) {
  pass++;
  console.log(`  \u2713 ${m}`);
}
function bad(m) {
  fail++;
  console.log(`  \u2717 ${m}`);
}

function toolsByName(builder, client) {
  return Object.fromEntries(builder(client).map((t) => [t.name, t]));
}

// -- Live client (real network) for read/metadata checks --------------------
const liveConfig = resolveConfig({
  apiKey,
  serverUrl,
  allowedWorkspaceIds: workspaceId ? [workspaceId] : [],
  defaultWorkspaceId: workspaceId || undefined,
  readOnly: false,
});
const liveClient = new TwentyClient(liveConfig, silent);
const meta = toolsByName(buildMetadataTools, liveClient);
const ws = toolsByName(buildWorkspaceTools, liveClient);
const rec = toolsByName(buildRecordTools, liveClient);

console.log("Twenty plugin live verification");
console.log(`  serverUrl=${serverUrl}`);
console.log(`  pluginRoot=${pluginRoot}`);
console.log("");

// 1. Metadata objects list — compatibility (direct-array) ---------------------
console.log("[1] twenty_metadata_objects_list (metadata compat)");
let objectCount = 0;
let candidateObjectId = null;
try {
  const r = await meta.twenty_metadata_objects_list.execute("v-1", {});
  if (r.details?.status !== "ok") {
    bad(`status=${r.details?.status} error=${r.details?.error}`);
  } else {
    const list = r.details.data?.data ?? [];
    objectCount = list.length;
    if (objectCount > 0) {
      ok(`discovered ${objectCount} metadata objects (not an empty workspace)`);
      const cand = list.find(
        (o) => o.nameSingular === "candidate" || o.namePlural === "candidates",
      );
      const anyObj = cand ?? list.find((o) => o.id);
      candidateObjectId = anyObj?.id ?? null;
    } else {
      bad("metadata list returned 0 objects (compat regression?)");
    }
  }
} catch (e) {
  bad(`threw: ${e.message}`);
}

// 2. Field listing for a discovered object -----------------------------------
console.log("[2] twenty_metadata_fields_list (metadataItem path)");
if (candidateObjectId) {
  try {
    const r = await meta.twenty_metadata_fields_list.execute("v-2", {
      objectMetadataId: candidateObjectId,
    });
    if (r.details?.status !== "ok") {
      bad(`status=${r.details?.status} error=${r.details?.error}`);
    } else if ((r.details.data?.data?.length ?? 0) > 0) {
      ok(
        `object ${candidateObjectId} exposed ${r.details.data.data.length} fields`,
      );
    } else {
      bad("field list empty for a known object (compat regression?)");
    }
  } catch (e) {
    bad(`threw: ${e.message}`);
  }
} else {
  bad("no object id available to list fields");
}

// 3. A read ------------------------------------------------------------------
console.log("[3] twenty_record_list (read path)");
try {
  const r = await rec.twenty_record_list.execute("v-3", {
    entity: "people",
    limit: 1,
  });
  if (r.details?.status === "ok") {
    ok("record list read returned ok");
  } else {
    bad(`status=${r.details?.status} error=${r.details?.error}`);
  }
} catch (e) {
  bad(`threw: ${e.message}`);
}

// 4. Empty-update guard — NO network call ------------------------------------
console.log("[4] twenty_record_update empty-body guard (Phase D)");
{
  let fetchCount = 0;
  const spyClient = new TwentyClient(
    resolveConfig({
      apiKey,
      serverUrl,
      allowedWorkspaceIds: workspaceId ? [workspaceId] : [],
      defaultWorkspaceId: workspaceId || undefined,
      readOnly: false,
    }),
    silent,
    {
      fetchImpl: async () => {
        fetchCount += 1;
        return {
          ok: true,
          status: 200,
          text: async () => "{}",
          headers: { get: () => null },
        };
      },
    },
  );
  const spyRec = toolsByName(buildRecordTools, spyClient);
  const r = await spyRec.twenty_record_update.execute("v-4", {
    entity: "candidates",
    id: "00000000-0000-0000-0000-000000000000",
    data: {},
  });
  const rejected =
    r.details?.status === "failed" &&
    /at least one record field/i.test(r.details?.error ?? "") &&
    /No HTTP request was made/i.test(r.details?.error ?? "");
  if (rejected && fetchCount === 0) {
    ok("empty update rejected before any HTTP request (fetchCount=0)");
  } else {
    bad(
      `guard failed: status=${r.details?.status} fetchCount=${fetchCount} error=${r.details?.error}`,
    );
  }
}

// 5. workspace_info consistency ----------------------------------------------
console.log("[5] twenty_workspace_info (non-zero object count)");
try {
  const r = await ws.twenty_workspace_info.execute("v-5", {});
  if (r.details?.status === "ok" && (r.details.data?.objectCount ?? 0) > 0) {
    ok(`workspace_info objectCount=${r.details.data.objectCount}`);
  } else {
    bad(
      `status=${r.details?.status} objectCount=${r.details?.data?.objectCount}`,
    );
  }
} catch (e) {
  bad(`threw: ${e.message}`);
}

console.log("");
console.log(`RESULT: ${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
