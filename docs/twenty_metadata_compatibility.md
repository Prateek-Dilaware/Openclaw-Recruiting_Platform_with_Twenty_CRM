# Twenty Metadata Compatibility and Regression Validation

## Scope

This document records the verified integration contract between the local
Twenty server and `@lacneu/twenty-openclaw`. It covers schema discovery and
the safe preconditions for recruiting record, relationship, and workflow
operations. It deliberately does **not** contain credentials or CRM data.

## Root cause

The installed plugin is `@lacneu/twenty-openclaw@0.8.4`. Its metadata tools
were written for Twenty's legacy metadata REST envelopes:

```json
{ "data": { "objects": [] } }
{ "data": { "object": { "fields": [] } } }
```

The running `twentycrm/twenty:latest` server returns the current direct
format:

```json
{ "data": [/* objects or fields */], "pageInfo": {}, "totalCount": 34 }
```

and `GET /rest/metadata/objects/{id}` returns the object directly, including
`fields`, rather than nesting it under `data.object`.

The legacy-only expressions `response.data.objects ?? []` and
`response.data.object.fields ?? []` consequently evaluated to `[]`. This was
an **API-version response-envelope incompatibility in the plugin**, not an
empty Twenty workspace, an API-key permission problem, or an OpenClaw routing
failure.

## Evidence gathered on the local stack

Using the plugin's configured credential and server URL:

| Request | Status | Verified response shape |
| --- | ---: | --- |
| `GET /rest/candidates` | 200 | Legacy record wrapper: `data.candidates`; 8 records |
| `GET /rest/metadata/objects` | 200 | Direct `data` array; 34 objects |
| `GET /rest/metadata/fields` | 200 | Direct `data` array; `totalCount` 616 |
| `GET /rest/metadata/objects/{candidateId}` | 200 | Direct object with inline `fields`; 19 candidate fields |
| Metadata request with invalid bearer token | 401 | `UNAUTHENTICATED`, not an empty result |

Current Twenty source confirms that metadata REST endpoints are protected by
`JwtAuthGuard`, `WorkspaceAuthGuard`, and `DATA_MODEL` permission checks, and
that newer versions support a direct metadata response feature flag. Therefore
permission errors must be surfaced; they cannot be normalized into an empty
catalog.

## Applied compatibility behavior

The runtime plugin now:

1. Accepts both direct arrays (`data`) and legacy arrays
   (`data.objects` / `data.fields`).
2. Accepts both a direct single metadata object and legacy
   `data.object` / `data.field` envelopes.
3. Preserves Twenty's server `totalCount` when present.
4. Throws a diagnostic error containing only endpoint and JSON key names for
   an unknown successful response shape. It explicitly says that this is not
   an empty workspace.
5. Leaves HTTP errors, including 401/403, as `TwentyApiError`; the client
   already includes the HTTP status and a bounded response preview.

## Safe recruiting operation flow

1. Discover objects using `twenty_metadata_objects_list`.
2. Resolve a required object by `namePlural`.
3. Inspect its fields with `twenty_metadata_fields_list({ objectMetadataId })`
   before a custom-record create/update or relation write.
4. Use generic record tools only after field and enum/relation validation.
5. For a note relationship, verify the `noteTargets` metadata first, create
   the note, create one verified target relation, then re-read the target at
   relation depth 1. The installed plugin has timeline listing but no dedicated
   attach action, so generic `noteTargets` creation remains a metadata-gated
   operation.
6. Execute lifecycle changes through an approved workflow tool; verify the
   resulting workflow run and record state. Do not bypass workflow execution
   with a direct status update unless an explicit policy permits it.

## Migration (2026-07-20): patch retired, fix absorbed into the maintained plugin

The Twenty plugin is now **maintained in this repository** at
`plugins/twenty-plugin` (package `@crm/twenty-plugin`, vendored from
`@lacneu/twenty-openclaw@0.8.4`). The metadata response-envelope
compatibility described above — plus the empty-write safety guards — are now
**part of the plugin source**, not an external runtime patch:

| Concern | Absorbed into |
| --- | --- |
| Direct-array vs legacy metadata list envelope | `src/tools/metadata.ts` (`metadataList`), `src/tools/workspace.ts` (`metadataObjects`) |
| Direct-object vs legacy `data.object`/`data.field` | `src/tools/metadata.ts` (`metadataItem`) |
| Empty create/update rejected before HTTP | `src/tools/records.ts` (`assertNonEmptyWriteData` + `minProperties:1`) |
| No-retry on non-GET writes, redacted debug logs | `src/twenty-client.ts` |

The former runtime patch `tests/openclaw/patch_twenty_metadata_compatibility.mjs`
has been **deleted**. Deployment is now:

```powershell
# Build + stage a complete artifact (with production node_modules) and install
./scripts/twenty-plugin/deploy_twenty_plugin.ps1
docker restart openclaw

# Live, non-mutating verification against the deployed artifact
./scripts/twenty-plugin/verify_twenty_plugin.ps1
```

## Regression test

Run the contract regression suite against the deployed maintained plugin
(no patching — the fix is in source):

```powershell
./tests/openclaw/validate_twenty_plugin.ps1
```

The suite verifies direct-array object discovery, direct-object field
discovery, workspace-info counts, and the diagnostic failure path for an
unexpected envelope. It is intentionally non-mutating.

Candidate writes, note attachment, and workflow execution require controlled
test fixtures and approval because they mutate CRM state. Their test protocol
is the safe operation flow above; execute it only in a dedicated test
workspace, then assert record creation, one target relation, and workflow-run
completion before cleanup.