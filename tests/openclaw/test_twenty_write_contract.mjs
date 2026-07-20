import assert from "node:assert/strict";
import test from "node:test";

const pluginRoot = process.env.TWENTY_OPENCLAW_PLUGIN_ROOT;

if (!pluginRoot) {
  test("Twenty plugin write contract", { skip: "Set TWENTY_OPENCLAW_PLUGIN_ROOT to run plugin contract tests." }, () => {});
} else {
  const { buildRecordTools } = await import(`${pluginRoot}/tools/records.js`);
  const { TwentyClient } = await import(`${pluginRoot}/twenty-client.js`);

  function createTool(request) {
    const diagnostics = [];
    const client = { readOnly: false, request, logger: { debug: (message) => diagnostics.push(message) } };
    return {
      tool: Object.fromEntries(buildRecordTools(client).map((tool) => [tool.name, tool])).twenty_record_create,
      diagnostics,
    };
  }

  test("generic record create rejects an empty body without a network request", async () => {
    let requestCount = 0;
    const { tool } = createTool(async () => {
      requestCount += 1;
      throw new Error("request must not run");
    });
    const result = await tool.execute("empty-call", { entity: "candidates", data: {} });

    assert.equal(requestCount, 0);
    assert.equal(result.details.status, "failed");
    assert.match(result.details.error, /data must contain at least one record field/i);
    assert.match(result.details.error, /No HTTP request was made/i);
  });

  test("generic record create forwards a populated body exactly once", async () => {
    const calls = [];
    const payload = { name: "Contract Candidate", emails: { primaryEmail: "contract@example.test", additionalEmails: [] } };
    const { tool, diagnostics } = createTool(async (method, path, options) => {
      calls.push({ method, path, body: options.body });
      return { data: { createCandidate: { id: "candidate-id", ...options.body } } };
    });
    const result = await tool.execute("create-call-42", { entity: "candidates", data: payload });

    assert.deepEqual(calls, [{ method: "POST", path: "/rest/candidates", body: payload }]);
    assert.equal(result.details.status, "ok");
    assert.equal(result.details.data.name, "Contract Candidate");
    assert.equal(result.details.data.emails.primaryEmail, "contract@example.test");
    assert.match(diagnostics[0], /callId=create-call-42/);
    assert.match(diagnostics[0], /entity=candidates/);
    assert.match(diagnostics[0], /fieldCount=2/);
    assert.doesNotMatch(diagnostics[0], /Contract Candidate|contract@example\.test/);
  });

  test("HTTP client does not retry non-idempotent POST requests", async () => {
    let fetchCount = 0;
    const client = new TwentyClient({
      apiKey: "test-key",
      serverUrl: "https://crm.test.invalid",
      defaultWorkspaceId: undefined,
      allowedWorkspaceIds: [],
      readOnly: false,
      logLevel: "debug",
    }, { debug() {}, warn() {} }, {
      fetchImpl: async () => {
        fetchCount += 1;
        return { ok: false, status: 503, text: async () => "unavailable", headers: { get: () => null } };
      },
    });

    await assert.rejects(() => client.request("POST", "/rest/candidates", { body: { name: "Safe" } }), /Twenty API 503/);
    assert.equal(fetchCount, 1);
  });
}