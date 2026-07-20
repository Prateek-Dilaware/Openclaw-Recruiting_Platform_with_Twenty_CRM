# Twenty Plugin — Migration to a Maintained-in-Repo Plugin

**Date:** 2026-07-20
**Status:** Complete and verified against the live stack.

## Summary

The Twenty CRM plugin is no longer a third-party npm runtime dependency. It is
now **vendored, maintained, and built from this repository** at
`plugins/twenty-plugin`, and OpenClaw loads **our** build instead of the
npm-installed `@lacneu/twenty-openclaw`.

- **Canonical source:** `plugins/twenty-plugin` (package `@crm/twenty-plugin`,
  version `0.8.4-crm.1`), forked from `@lacneu/twenty-openclaw@0.8.4`.
- **Plugin manifest id kept as `twenty-openclaw`** so existing `openclaw.json`
  config, tool names (`twenty_*`), and skills keep working unchanged.
- The external runtime patch `tests/openclaw/patch_twenty_metadata_compatibility.mjs`
  is **deleted**; its fixes are absorbed into source.
- The deployment artifact is **complete before installation** (it carries its
  own production `node_modules`), because `openclaw plugins install <path>`
  installs only the `openclaw` peer dependency, never a plugin's regular deps.

## Why the deployment artifact must be self-contained (root cause)

`openclaw plugins install <local-path>` copies the plugin into
`~/.openclaw/extensions/<id>` and **only symlinks the `openclaw` peer
dependency** — it does not run `npm install` for regular `dependencies`
(verified in the gateway source `plugin-peer-link`, comment: *"Plugin package
managers still own third-party dependencies"*). A plugin missing its runtime
deps therefore fails at gateway load with
`Cannot find module '@sinclair/typebox'`.

The old npm plugin worked only because npm-spec installs land under
`~/.openclaw/npm/projects/<hash>` **with a full `node_modules`**. Our
local-path install uses a different path that skips dependency installation.

**Fix (Option A):** the deploy pipeline stages a complete package that already
contains a production-only `node_modules` (`@sinclair/typebox`) before calling
`openclaw plugins install`.

## What changed

### Added
- `plugins/twenty-plugin/**` — vendored TypeScript source + committed `dist/`.
- `scripts/twenty-plugin/deploy_twenty_plugin.ps1` — build → stage (with prod
  `node_modules`) → install pipeline.
- `scripts/twenty-plugin/verify_twenty_plugin.ps1` + `verify_twenty_plugin.mjs`
  — live, non-mutating verification (metadata compat, field discovery, read,
  empty-update guard, workspace-info).
- `plugins/twenty-plugin/test/tools/metadata.compat.test.ts` and new empty-write
  guard tests (in the records test file).
- `docs/TWENTY_PLUGIN_MIGRATION.md` (this file).

### Modified
- `plugins/twenty-plugin/package.json` → `@crm/twenty-plugin`, `0.8.4-crm.1`.
- `plugins/twenty-plugin/package-lock.json` → root identity aligned + synced.
- `plugins/twenty-plugin/openclaw.plugin.json` → name/description mark it as
  the maintained fork (id kept `twenty-openclaw`).
- `plugins/twenty-plugin/src/index.ts` → branded ready-log + typed default
  export.
- `plugins/twenty-plugin/src/tools/metadata.ts` → absorbed metadata-envelope
  compatibility (`metadataList`, `metadataItem`).
- `plugins/twenty-plugin/src/tools/workspace.ts` → absorbed `metadataObjects`.
- `plugins/twenty-plugin/src/tools/records.ts` → `assertNonEmptyWriteData`
  (create + update), `minProperties:1` on both schemas, redacted debug logs.
- `plugins/twenty-plugin/src/twenty-client.ts` → no-retry on non-GET writes,
  redacted body logging.
- `plugins/twenty-plugin/src/tools/_factory.ts` → thread `toolCallId` into `run`.
- `docker/docker-compose.dev.yml` → bind mount `../plugins:/home/node/plugins:ro`.
- `tests/openclaw/validate_twenty_plugin.ps1` → target the deployed maintained
  plugin; removed the patch step.
- `docs/twenty_metadata_compatibility.md` → documents the retirement.

### Removed
- `tests/openclaw/patch_twenty_metadata_compatibility.mjs` (retired).

## Deploy & verify

```powershell
# 1. Ensure the plugins mount exists (once): docker/docker-compose.dev.yml has
#    ../plugins:/home/node/plugins:ro  — recreate the container if newly added:
docker compose -f docker/docker-compose.dev.yml up -d --force-recreate openclaw

# 2. Build a complete artifact and install it
./scripts/twenty-plugin/deploy_twenty_plugin.ps1

# 3. Reload the gateway
docker restart openclaw

# 4. Live verification (non-mutating)
./scripts/twenty-plugin/verify_twenty_plugin.ps1

# 5. Contract regression tests (no patching)
./tests/openclaw/validate_twenty_plugin.ps1
```

## Evidence captured on 2026-07-20

- Install/load log:
  `twenty-openclaw [CRM maintained @crm/twenty-plugin]: ready — 148 tool(s)
  registered, 52 approval-gated, 1 allowed workspace(s), readOnly=false
  (metadata-compat + empty-write-guard absorbed)`
- `openclaw plugins inspect twenty-openclaw` → `Status: loaded`,
  `Recorded version: 0.8.4-crm.1`, install path
  `~/.openclaw/extensions/twenty-openclaw`.
- Live verify: **5/5 passed** — 34 metadata objects discovered, 19 candidate
  fields, read ok, empty-update rejected with `fetchCount=0`, workspace
  objectCount=34.
- Contract tests: **6/6 passed** (3 metadata + 3 write) with no runtime patch.
- Plugin unit tests: **88/88 passed** (79 upstream + 9 added).

## Remaining work (before enhancing write tools)

1. Decide whether to commit the plugin's production `node_modules` or keep the
   build-time staging approach (current: staging; nothing committed under
   `node_modules`). The deploy script rebuilds the artifact each run.
2. Optionally add `plugins.allow: ["twenty-openclaw"]` to `openclaw.json` to
   silence the "non-bundled plugin auto-load" trust advisory.
3. Consider a bundled-`dist` (esbuild) variant later for a zero-`node_modules`
   artifact if we want to avoid the staging `npm ci` entirely.
4. Then begin the write-tool enhancements (recruiting-aware typed writes) on
   top of this maintained plugin.
