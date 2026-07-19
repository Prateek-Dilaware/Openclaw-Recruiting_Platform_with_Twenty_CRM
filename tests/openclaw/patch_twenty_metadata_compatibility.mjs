import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

const pluginRoot = process.env.TWENTY_OPENCLAW_PLUGIN_ROOT;

if (!pluginRoot) {
  throw new Error("TWENTY_OPENCLAW_PLUGIN_ROOT is required.");
}

const metadataPath = join(pluginRoot, "tools", "metadata.js");
const workspacePath = join(pluginRoot, "tools", "workspace.js");

const metadataHelpers = `// Twenty v2.21+ returns the new direct REST metadata format:
// { data: [...] } for lists and an object directly for GET /:id. Older
// servers return the legacy { data: { objects|fields: [...] } } envelope.
// Unknown shapes must be errors, never a silently empty workspace.
function metadataList(response, collection, path) {
    if (Array.isArray(response?.data)) return response.data;
    if (Array.isArray(response?.data?.[collection])) return response.data[collection];
    if (Array.isArray(response?.[collection])) return response[collection];
    const responseKeys = response && typeof response === "object" ? Object.keys(response).join(",") : typeof response;
    const dataKeys = response?.data && typeof response.data === "object" && !Array.isArray(response.data)
        ? Object.keys(response.data).join(",")
        : Array.isArray(response?.data) ? "<array>" : typeof response?.data;
    throw new Error(\`Unexpected Twenty metadata list response from \${path}; topLevelKeys=[\${responseKeys}], dataKeys=[\${dataKeys}]. This is not an empty workspace.\`);
}
function metadataItem(response, item, path) {
    if (response && typeof response === "object" && !Array.isArray(response) &&
        (typeof response.id === "string" || Array.isArray(response.fields))) return response;
    if (response?.data?.[item] && typeof response.data[item] === "object") return response.data[item];
    if (response?.[item] && typeof response[item] === "object") return response[item];
    const responseKeys = response && typeof response === "object" ? Object.keys(response).join(",") : typeof response;
    const dataKeys = response?.data && typeof response.data === "object" && !Array.isArray(response.data)
        ? Object.keys(response.data).join(",")
        : typeof response?.data;
    throw new Error(\`Unexpected Twenty metadata item response from \${path}; topLevelKeys=[\${responseKeys}], dataKeys=[\${dataKeys}].\`);
}
`;

const workspaceHelpers = `function metadataObjects(response) {
    if (Array.isArray(response?.data)) return response.data;
    if (Array.isArray(response?.data?.objects)) return response.data.objects;
    if (Array.isArray(response?.objects)) return response.objects;
    const responseKeys = response && typeof response === "object" ? Object.keys(response).join(",") : typeof response;
    const dataKeys = response?.data && typeof response.data === "object" && !Array.isArray(response.data)
        ? Object.keys(response.data).join(",")
        : Array.isArray(response?.data) ? "<array>" : typeof response?.data;
    throw new Error(\`Unexpected Twenty metadata list response from /rest/metadata/objects; topLevelKeys=[\${responseKeys}], dataKeys=[\${dataKeys}]. This is not an empty workspace.\`);
}
`;

function replaceRequired(source, from, to, file) {
  if (!source.includes(from)) {
    throw new Error(`Expected unpatched source was not found in ${file}: ${from}`);
  }

  return source.replace(from, to);
}

let metadata = await readFile(metadataPath, "utf8");
let workspace = await readFile(workspacePath, "utf8");

if (!metadata.includes("function metadataList(")) {
  metadata = metadata.replace("// Permissive icon naming guidance", `${metadataHelpers}// Permissive icon naming guidance`);
  metadata = replaceRequired(metadata, "const items = resp?.data?.objects ?? [];", "const items = metadataList(resp, \"objects\", METADATA_OBJECTS_PATH);", metadataPath);
  metadata = replaceRequired(metadata, "totalCount: items.length,", "totalCount: resp?.totalCount ?? items.length,", metadataPath);
  metadata = replaceRequired(metadata, "return resp?.data?.object ?? null;", "return metadataItem(resp, \"object\", `${METADATA_OBJECTS_PATH}/${encodeURIComponent(params.id)}`);", metadataPath);
  metadata = replaceRequired(metadata, "const fields = (resp?.data?.object?.fields ?? []);", "const object = metadataItem(resp, \"object\", `${METADATA_OBJECTS_PATH}/${encodeURIComponent(params.objectMetadataId)}`);\n                    if (!Array.isArray(object.fields)) throw new Error(`Twenty metadata object ${params.objectMetadataId} did not include a fields array.`);\n                    const fields = object.fields;", metadataPath);
  metadata = replaceRequired(metadata, "const items = resp?.data?.fields ?? [];", "const items = metadataList(resp, \"fields\", METADATA_FIELDS_PATH);", metadataPath);
  metadata = replaceRequired(metadata, "return resp?.data?.field ?? null;", "return metadataItem(resp, \"field\", `${METADATA_FIELDS_PATH}/${encodeURIComponent(params.id)}`);", metadataPath);
  await writeFile(metadataPath, metadata);
}

if (!workspace.includes("function metadataObjects(")) {
  workspace = workspace.replace('import { defineTwentyTool } from "./_factory.js";\n', `import { defineTwentyTool } from "./_factory.js";\n${workspaceHelpers}`);
  workspace = replaceRequired(workspace, "resp?.data?.objects ?? resp?.objects ?? []", "metadataObjects(resp)", workspacePath);
  await writeFile(workspacePath, workspace);
}

console.log("Applied Twenty metadata envelope compatibility patch.");