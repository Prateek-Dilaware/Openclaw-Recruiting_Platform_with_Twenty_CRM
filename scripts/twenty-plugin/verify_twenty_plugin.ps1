<#
.SYNOPSIS
  Run the live verification suite against the DEPLOYED (OpenClaw-managed)
  Twenty plugin artifact.

.DESCRIPTION
  Locates the installed plugin dist inside the container's managed npm
  projects, copies the verification script in, and runs it. Proves metadata
  compatibility, object/field discovery, a read, the empty-update guard, and
  workspace-info consistency — all against the live Twenty instance and
  WITHOUT mutating CRM data.

.PARAMETER Container
  OpenClaw container name (default: openclaw).

.PARAMETER PluginRoot
  Override the plugin dist path inside the container. When omitted, the
  script auto-discovers the managed installation.
#>
param(
    [string]$Container = "openclaw",
    [string]$PluginRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $PluginRoot) {
    # Primary: the installed extension dir (where copy-install places local
    # plugins and where the gateway actually loads them from). This dir also
    # carries the production node_modules, so imports resolve.
    $probe = docker exec $Container sh -c 'test -f /home/node/.openclaw/extensions/twenty-openclaw/dist/index.js && echo /home/node/.openclaw/extensions/twenty-openclaw/dist'
    if ($probe) { $PluginRoot = $probe.Trim() }

    if (-not $PluginRoot) {
        # Fallback: legacy npm-projects install (upstream package layout).
        $PluginRoot = docker exec $Container sh -c 'find /home/node/.openclaw/npm/projects -path "*/node_modules/@lacneu/twenty-openclaw/dist" -type d -print -quit 2>/dev/null'
    }
    if (-not $PluginRoot) {
        # Last resort: the staged artifact (has its own node_modules too).
        $probe2 = docker exec $Container sh -c 'test -f /tmp/twenty-plugin-stage/dist/index.js && echo /tmp/twenty-plugin-stage/dist'
        if ($probe2) { $PluginRoot = $probe2.Trim() }
    }
}

if (-not $PluginRoot) {
    throw "Could not locate a deployed Twenty plugin dist. Run deploy_twenty_plugin.ps1 first."
}

$PluginRoot = $PluginRoot.Trim()
Write-Host "==> Verifying plugin at: $PluginRoot" -ForegroundColor Cyan

$scriptPath = Join-Path $PSScriptRoot "verify_twenty_plugin.mjs"
docker cp $scriptPath "${Container}:/tmp/verify_twenty_plugin.mjs"
docker exec $Container node /tmp/verify_twenty_plugin.mjs --plugin-root $PluginRoot
exit $LASTEXITCODE
