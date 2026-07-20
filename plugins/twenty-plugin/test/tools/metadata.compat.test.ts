// Verifies the metadata response-envelope COMPATIBILITY behavior that was
// absorbed from the former `patch_twenty_metadata_compatibility.mjs` runtime
// patch (see docs/twenty_metadata_compatibility.md).
//
// The installed Twenty server (v2.21+) returns the DIRECT format:
//   list:  { data: [ ... ], totalCount }
//   item:  { ...object, fields: [] }        (the object itself)
// while the legacy 0.8.4 plugin expected:
//   list:  { data: { objects|fields: [ ... ] } }
//   item:  { data: { object|field: { ... } } }
//
// The plugin must accept BOTH, preserve the server totalCount, and — most
// importantly — THROW on an unknown successful shape rather than silently
// returning an empty catalog (which made a records-present workspace look
// empty and skipped every metadata-gated write).

import { strict as assert } from "node:assert";
import { describe, it } from "node:test";

import { resolveConfig } from "../../src/config.js";
import { buildMetadataTools } from "../../src/tools/metadata.js";
import { buildWorkspaceTools } from "../../src/tools/workspace.js";
import { TwentyClient } from "../../src/twenty-client.js";

interface FetchCapture {
  url: string;
  init: RequestInit | undefined;
}

function fakeFetch(
  payload: unknown,
  capture: FetchCapture[],
  status = 200,
): typeof fetch {
  return (async (input: RequestInfo | URL, init?: RequestInit) => {
    capture.push({ url: String(input), init });
    return new Response(JSON.stringify(payload), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
}

const silentLogger = {
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
};

function buildClient(payload: unknown, calls: FetchCapture[], status = 200) {
  const config = resolveConfig({
    apiKey: "test-key",
    serverUrl: "https://crm.test.local",
    allowedWorkspaceIds: ["ws-1"],
    defaultWorkspaceId: "ws-1",
  });
  return new TwentyClient(config, silentLogger, {
    fetchImpl: fakeFetch(payload, calls, status),
  });
}

interface ToolHandle {
  name: string;
  execute: (id: string, params: unknown) => Promise<{
    details?: { status: string; data?: unknown; error?: string };
  }>;
}

function findMetaTool(client: TwentyClient, name: string): ToolHandle {
  const tool = buildMetadataTools(client).find((t) => t.name === name);
  if (!tool) throw new Error(`tool ${name} not registered`);
  return tool as unknown as ToolHandle;
}

describe("metadata compat — objects list", () => {
  it("accepts the v2.21+ DIRECT array `{ data: [...] }` and preserves totalCount", async () => {
    const calls: FetchCapture[] = [];
    const client = buildClient(
      {
        data: [
          { id: "o1", nameSingular: "candidate", isCustom: true },
          { id: "o2", nameSingular: "person", isCustom: false },
        ],
        totalCount: 34,
      },
      calls,
    );

    const tool = findMetaTool(client, "twenty_metadata_objects_list");
    const result = await tool.execute("c1", {});

    assert.equal(result.details?.status, "ok");
    const out = result.details?.data as { data: unknown[]; totalCount: number };
    assert.equal(out.data.length, 2);
    // Server-provided totalCount is preserved even though only 2 items
    // were returned on this page.
    assert.equal(out.totalCount, 34);
  });

  it("still accepts the LEGACY enveloped `{ data: { objects: [...] } }`", async () => {
    const calls: FetchCapture[] = [];
    const client = buildClient({ data: { objects: [{ id: "o1" }] } }, calls);

    const tool = findMetaTool(client, "twenty_metadata_objects_list");
    const result = await tool.execute("c2", {});

    assert.equal(result.details?.status, "ok");
    const out = result.details?.data as { data: unknown[] };
    assert.equal(out.data.length, 1);
  });

  it("THROWS on an unknown successful shape — never a silent empty workspace", async () => {
    const calls: FetchCapture[] = [];
    const client = buildClient({ unexpected: { shape: true } }, calls);

    const tool = findMetaTool(client, "twenty_metadata_objects_list");
    const result = await tool.execute("c3", {});

    assert.equal(result.details?.status, "failed");
    assert.match(
      String(result.details?.error ?? ""),
      /not an empty workspace/i,
    );
  });
});

describe("metadata compat — object get (direct object with inline fields)", () => {
  it("accepts the DIRECT object `{ id, fields: [...] }` returned by GET /:id", async () => {
    const calls: FetchCapture[] = [];
    const client = buildClient(
      { id: "cand-obj", nameSingular: "candidate", fields: [{ id: "f1" }] },
      calls,
    );

    const tool = findMetaTool(client, "twenty_metadata_object_get");
    const result = await tool.execute("c4", { id: "cand-obj" });

    assert.equal(result.details?.status, "ok");
    const obj = result.details?.data as { id: string; fields: unknown[] };
    assert.equal(obj.id, "cand-obj");
    assert.equal(obj.fields.length, 1);
  });
});

describe("metadata compat — fields list via objectMetadataId (direct object)", () => {
  it("reads inline fields[] from the DIRECT object format", async () => {
    const calls: FetchCapture[] = [];
    const client = buildClient(
      { id: "cand-obj", fields: [{ id: "f1" }, { id: "f2" }] },
      calls,
    );

    const tool = findMetaTool(client, "twenty_metadata_fields_list");
    const result = await tool.execute("c5", { objectMetadataId: "cand-obj" });

    assert.equal(result.details?.status, "ok");
    const out = result.details?.data as {
      data: unknown[];
      totalCount: number;
      source: string;
    };
    assert.equal(out.data.length, 2);
    assert.equal(out.totalCount, 2);
    assert.equal(out.source, "object");
  });
});

describe("workspace_info compat", () => {
  it("counts objects from the DIRECT array format and flags an unknown shape", async () => {
    const okCalls: FetchCapture[] = [];
    const okClient = buildClient(
      { data: [{ id: "o1", isCustom: true }, { id: "o2", isCustom: false }] },
      okCalls,
    );
    const okTool = buildWorkspaceTools(okClient).find(
      (t) => t.name === "twenty_workspace_info",
    ) as unknown as ToolHandle;
    const okResult = await okTool.execute("w1", {});
    assert.equal(okResult.details?.status, "ok");
    const info = okResult.details?.data as {
      objectCount: number;
      customObjectCount: number;
    };
    assert.equal(info.objectCount, 2);
    assert.equal(info.customObjectCount, 1);

    const badCalls: FetchCapture[] = [];
    const badClient = buildClient({ weird: true }, badCalls);
    const badTool = buildWorkspaceTools(badClient).find(
      (t) => t.name === "twenty_workspace_info",
    ) as unknown as ToolHandle;
    const badResult = await badTool.execute("w2", {});
    assert.equal(badResult.details?.status, "failed");
    assert.match(
      String(badResult.details?.error ?? ""),
      /not an empty workspace/i,
    );
  });
});
