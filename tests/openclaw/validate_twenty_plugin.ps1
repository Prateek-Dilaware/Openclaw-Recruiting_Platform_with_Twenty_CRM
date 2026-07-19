param(
    [string]$PluginRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $PluginRoot) {
    $PluginRoot = docker exec openclaw sh -c 'find /home/node/.openclaw/npm/projects -path "*/node_modules/@lacneu/twenty-openclaw/dist" -type d -print -quit'
}

if (-not $PluginRoot) {
    throw "The installed @lacneu/twenty-openclaw distribution was not found."
}

$scriptPath = Join-Path $PSScriptRoot "test_twenty_metadata_contract.mjs"
$patchPath = Join-Path $PSScriptRoot "patch_twenty_metadata_compatibility.mjs"
docker cp $patchPath "openclaw:/tmp/patch_twenty_metadata_compatibility.mjs"
docker exec -e "TWENTY_OPENCLAW_PLUGIN_ROOT=$PluginRoot" openclaw node /tmp/patch_twenty_metadata_compatibility.mjs
docker cp $scriptPath "openclaw:/tmp/test_twenty_metadata_contract.mjs"
docker exec -e "TWENTY_OPENCLAW_PLUGIN_ROOT=$PluginRoot" openclaw node --test /tmp/test_twenty_metadata_contract.mjs