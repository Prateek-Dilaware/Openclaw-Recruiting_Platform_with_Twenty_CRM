import assert from "node:assert/strict";
import test from "node:test";

const pluginRoot = process.env.TWENTY_OPENCLAW_PLUGIN_ROOT;

if (!pluginRoot) {
  test("Twenty plugin metadata contract", { skip: "Set TWENTY_OPENCLAW_PLUGIN_ROOT to run plugin contract tests." }, () => {});
} else {
  const { buildMetadataTools } = await import(`${pluginRoot}/tools/metadata.js`);
  const { buildWorkspaceTools } = await import(`${pluginRoot}/tools/workspace.js`);

  function buildTools(payload) {
    const client = {
      serverUrl: "https://crm.test.invalid",
      async request() {
        return payload;
      },
    };

    return {
      metadata: Object.fromEntries(buildMetadataTools(client).map((tool) => [tool.name, tool])),
      workspace: Object.fromEntries(buildWorkspaceTools(client).map((tool) => [tool.name, tool])),
    };
  }

  test("metadata object discovery accepts the current direct-array response", async () => {
    const { metadata, workspace } = buildTools({
      data: [{ id: "candidate-id", nameSingular: "candidate", namePlural: "candidates", fields: [] }],
      totalCount: 1,
    });

    const objects = await metadata.twenty_metadata_objects_list.execute("test", {});
    const info = await workspace.twenty_workspace_info.execute("test", {});

    assert.equal(objects.details.status, "ok");
    assert.equal(objects.details.data.data.length, 1);
    assert.equal(objects.details.data.totalCount, 1);
    assert.equal(info.details.data.objectCount, 1);
  });

  test("field discovery accepts a direct object response with inline fields", async () => {
    const { metadata } = buildTools({
      id: "candidate-id",
      fields: [{ id: "name-id", name: "name", type: "FULL_NAME" }],
    });

    const fields = await metadata.twenty_metadata_fields_list.execute("test", { objectMetadataId: "candidate-id" });

    assert.equal(fields.details.status, "ok");
    assert.equal(fields.details.data.source, "object");
    assert.equal(fields.details.data.data[0].name, "name");
  });

  test("unexpected successful metadata shapes fail rather than becoming an empty workspace", async () => {
    const { metadata } = buildTools({ data: { unsupported: [] } });

    const result = await metadata.twenty_metadata_objects_list.execute("test", {});

    assert.equal(result.details.status, "failed");
    assert.match(String(result.details.error), /Unexpected Twenty metadata list response/);
    assert.match(String(result.details.error), /not an empty workspace/i);
  });
}