param(
    [string]$PluginRoot = ""
)

$ErrorActionPreference = "Stop"

# NOTE (migration 2026-07-20): the external runtime patch
# `patch_twenty_metadata_compatibility.mjs` has been RETIRED. The metadata
# response-envelope compatibility fix and the empty-write safety guards are
# now part of the maintained plugin source at `plugins/twenty-plugin`
# (src/tools/metadata.ts, workspace.ts, records.ts, twenty-client.ts).
# This script therefore no longer patches anything — it only runs the
# contract tests against the DEPLOYED maintained plugin.

if (-not $PluginRoot) {
    # Primary: the maintained plugin installed under the extensions dir.
    $probe = docker exec openclaw sh -c 'test -f /home/node/.openclaw/extensions/twenty-openclaw/dist/index.js && echo /home/node/.openclaw/extensions/twenty-openclaw/dist'
    if ($probe) { $PluginRoot = $probe.Trim() }
}
if (-not $PluginRoot) {
    # Fallback: legacy npm-projects install (pre-migration upstream package).
    $PluginRoot = docker exec openclaw sh -c 'find /home/node/.openclaw/npm/projects -path "*/node_modules/@lacneu/twenty-openclaw/dist" -type d -print -quit'
}

if (-not $PluginRoot) {
    throw "No deployed Twenty plugin dist found. Run scripts/twenty-plugin/deploy_twenty_plugin.ps1 first."
}

$PluginRoot = $PluginRoot.Trim()
Write-Host "Validating deployed plugin at: $PluginRoot" -ForegroundColor Cyan

$scriptPath = Join-Path $PSScriptRoot "test_twenty_metadata_contract.mjs"
$writeScriptPath = Join-Path $PSScriptRoot "test_twenty_write_contract.mjs"
docker cp $scriptPath "openclaw:/tmp/test_twenty_metadata_contract.mjs"
docker exec -e "TWENTY_OPENCLAW_PLUGIN_ROOT=$PluginRoot" openclaw node --test /tmp/test_twenty_metadata_contract.mjs
docker cp $writeScriptPath "openclaw:/tmp/test_twenty_write_contract.mjs"
docker exec -e "TWENTY_OPENCLAW_PLUGIN_ROOT=$PluginRoot" openclaw node --test /tmp/test_twenty_write_contract.mjs