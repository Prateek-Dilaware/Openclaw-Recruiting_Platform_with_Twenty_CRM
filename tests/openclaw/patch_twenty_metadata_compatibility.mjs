import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

const pluginRoot = process.env.TWENTY_OPENCLAW_PLUGIN_ROOT;

if (!pluginRoot) {
  throw new Error("TWENTY_OPENCLAW_PLUGIN_ROOT is required.");
}

const metadataPath = join(pluginRoot, "tools", "metadata.js");
const workspacePath = join(pluginRoot, "tools", "workspace.js");
const recordsPath = join(pluginRoot, "tools", "records.js");
const clientPath = join(pluginRoot, "twenty-client.js");
const factoryPath = join(pluginRoot, "tools", "_factory.js");

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
let records = await readFile(recordsPath, "utf8");
let client = await readFile(clientPath, "utf8");
let factory = await readFile(factoryPath, "utf8");

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

if (!records.includes("function assertNonEmptyCreateData(")) {
  const createGuard = `/**
 * A generic create with no fields is syntactically valid JSON but never a
 * meaningful CRM operation. Twenty accepts it and creates a blank record,
 * so reject it locally before the request client can reach the network.
 */
function assertNonEmptyCreateData(data, entity) {
    if (!data || typeof data !== "object" || Array.isArray(data) || Object.keys(data).length === 0) {
        throw new Error(\`Refused to create \\\${entity}: data must contain at least one record field. No HTTP request was made.\`);
    }
}
`;
  records = records.replace("/**\n * Twenty wraps every write/get response", `${createGuard}/**\n * Twenty wraps every write/get response`);
  records = replaceRequired(records, "additionalProperties: true,\n        description: \"Record fields.", "additionalProperties: true,\n        minProperties: 1,\n        description: \"Record fields.", recordsPath);
  records = replaceRequired(records, "assertValidEntity(params.entity);\n                const resp = await c.request(\"POST\", `/rest/\${params.entity}`, { body: params.data, signal });", "assertValidEntity(params.entity);\n                assertNonEmptyCreateData(params.data, params.entity);\n                const resp = await c.request(\"POST\", `/rest/\${params.entity}`, { body: params.data, signal });", recordsPath);
  await writeFile(recordsPath, records);
}

if (!client.includes("const canRetry = method === \"GET\";")) {
  client = replaceRequired(client, "this.logger.debug?.(`${spanName} start` +\n                (body ? ` body=${body.slice(0, 200)}` : \"\"));", "const bodySummary = opts.body && typeof opts.body === \"object\" && !Array.isArray(opts.body)\n                ? ` fields=[${Object.keys(opts.body).join(\",\")}] fieldCount=${Object.keys(opts.body).length}`\n                : body ? \" body=<redacted>\" : \"\";\n            this.logger.debug?.(`${spanName} start${bodySummary}`);", clientPath);
  client = replaceRequired(client, "if (!RETRY_STATUSES.has(resp.status) || attempt === MAX_RETRIES) {", "const canRetry = method === \"GET\";\n            if (!canRetry || !RETRY_STATUSES.has(resp.status) || attempt === MAX_RETRIES) {", clientPath);
  await writeFile(clientPath, client);
}

if (!factory.includes("def.run(params, client, signal, _toolCallId)")) {
  factory = replaceRequired(factory, "const data = await def.run(params, client, signal);", "const data = await def.run(params, client, signal, _toolCallId);", factoryPath);
  await writeFile(factoryPath, factory);
}

if (!records.includes("twenty_record_create callId=")) {
  records = replaceRequired(records, "run: async (params, c, signal) => {\n                assertValidEntity(params.entity);\n                assertNonEmptyCreateData(params.data, params.entity);", "run: async (params, c, signal, toolCallId) => {\n                assertValidEntity(params.entity);\n                assertNonEmptyCreateData(params.data, params.entity);\n                c.logger?.debug?.(`twenty_record_create callId=${toolCallId} entity=${params.entity} endpoint=/rest/${params.entity} fields=[${Object.keys(params.data).join(\",\")}] fieldCount=${Object.keys(params.data).length}`);", recordsPath);
  await writeFile(recordsPath, records);
}

console.log("Applied Twenty metadata compatibility and create-safety patches.");