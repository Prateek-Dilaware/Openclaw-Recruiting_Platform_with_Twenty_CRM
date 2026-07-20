<#
.SYNOPSIS
  Deploy the maintained-in-repo Twenty plugin into the running OpenClaw
  container as a COMPLETE, self-contained installation artifact.

.DESCRIPTION
  Canonical source: plugins/twenty-plugin (bind-mounted read-only into the
  container at /home/node/plugins/twenty-plugin). The OpenClaw-managed
  installation is treated as a deployment artifact built from that source.

  ROOT CAUSE THIS SCRIPT ADDRESSES
  --------------------------------
  `openclaw plugins install <local-path>` does NOT run `npm install` for a
  plugin's regular `dependencies`; it only symlinks the `openclaw` peer
  dependency (verified in the gateway source `plugin-peer-link`, whose doc
  comment states "Plugin package managers still own third-party
  dependencies"). Therefore the directory handed to `plugins install` MUST
  already be self-contained — it must include a production `node_modules`
  (e.g. @sinclair/typebox). Otherwise the plugin fails at gateway runtime
  with `Cannot find module '@sinclair/typebox'`.

  PIPELINE (Option A — stage a complete package, then install)
  ------------------------------------------------------------
    1. BUILD dir  : copy source -> `npm ci` (full) -> `tsc` -> dist/.
    2. STAGE dir  : assemble a clean deployable package:
                      dist/, package.json, package-lock.json,
                      openclaw.plugin.json, README/LICENSE, then
                      `npm ci --omit=dev` INSIDE the stage so it carries a
                      production-only node_modules (@sinclair/typebox).
    3. INSTALL    : `openclaw plugins install <STAGE> --force`.

  We NEVER hand-install dependencies into the live extensions directory. The
  artifact is complete before installation.

.PARAMETER Container
  OpenClaw container name (default: openclaw).

.PARAMETER PluginId
  Plugin manifest id / config key (default: twenty-openclaw).
#>
param(
    [string]$Container = "openclaw",
    [string]$PluginId = "twenty-openclaw"
)

$ErrorActionPreference = "Stop"

$MountedSource = "/home/node/plugins/twenty-plugin"
$BuildDir = "/tmp/twenty-plugin-build"
$StageDir = "/tmp/twenty-plugin-stage"

function Invoke-InContainer {
    param([string]$Script, [string]$What)
    Write-Host "==> $What" -ForegroundColor Cyan
    docker exec $Container sh -c $Script
    if ($LASTEXITCODE -ne 0) {
        throw "FAILED ($What) exit=$LASTEXITCODE. Stopping. Command: $Script"
    }
}

# --- Preconditions ----------------------------------------------------------
docker exec $Container sh -c "test -f $MountedSource/openclaw.plugin.json"
if ($LASTEXITCODE -ne 0) {
    throw "Source not found at $MountedSource. Ensure '../plugins:/home/node/plugins:ro' is mounted and the container was recreated."
}

# Clean scratch dirs as ROOT first. Prior runs (or docker cp) can leave
# root-owned files that the default `node` user cannot remove, which would
# otherwise break the `rm -rf` in the build step. Non-fatal if nothing exists.
Write-Host "==> Cleaning scratch dirs (as root) to avoid stale-permission failures" -ForegroundColor Cyan
docker exec -u root $Container sh -c "rm -rf $BuildDir $StageDir" | Out-Null

# --- 1. BUILD ---------------------------------------------------------------
Invoke-InContainer `
    "cp -r $MountedSource $BuildDir" `
    "Preparing writable build copy at $BuildDir"

# NODE_ENV=development so npm does not omit devDependencies (typescript, SDK).
Invoke-InContainer `
    "cd $BuildDir && NODE_ENV=development npm ci --include=dev --no-audit --no-fund --loglevel=error" `
    "npm ci (full, for build) - installs typescript + openclaw SDK"

Invoke-InContainer `
    "cd $BuildDir && ./node_modules/.bin/tsc -p tsconfig.json" `
    "Compiling with tsc"

Invoke-InContainer `
    "test -f $BuildDir/dist/index.js" `
    "Verifying dist/index.js was produced"

# --- 2. STAGE (complete, self-contained artifact) ---------------------------
Invoke-InContainer `
    "rm -rf $StageDir && mkdir -p $StageDir" `
    "Creating clean staging dir $StageDir"

# Copy only what the deployable package ships (mirrors package.json `files`).
Invoke-InContainer `
    ("cp -r $BuildDir/dist $StageDir/dist && " +
     "cp $BuildDir/package.json $StageDir/package.json && " +
     "cp $BuildDir/package-lock.json $StageDir/package-lock.json && " +
     "cp $BuildDir/openclaw.plugin.json $StageDir/openclaw.plugin.json && " +
     "cp $BuildDir/README.md $StageDir/README.md 2>/dev/null; " +
     "cp $BuildDir/LICENSE $StageDir/LICENSE 2>/dev/null; " +
     "cp -r $BuildDir/examples $StageDir/examples 2>/dev/null; true") `
    "Assembling deployable package files into stage"

# Production-only node_modules INSIDE the stage (the key fix: the artifact
# carries @sinclair/typebox so the gateway can resolve it at runtime).
Invoke-InContainer `
    "cd $StageDir && NODE_ENV=production npm ci --omit=dev --no-audit --no-fund --loglevel=error" `
    "npm ci --omit=dev (production node_modules for the artifact)"

Invoke-InContainer `
    "test -d $StageDir/node_modules/@sinclair/typebox" `
    "Verifying @sinclair/typebox is present in the staged artifact"

# --- 3. INSTALL -------------------------------------------------------------
Invoke-InContainer `
    "openclaw plugins install $StageDir --force" `
    "Installing the complete staged artifact"

Write-Host ""
Write-Host "==> Installed plugin summary:" -ForegroundColor Cyan
docker exec $Container sh -c "openclaw plugins inspect $PluginId 2>/dev/null | head -20"

Write-Host ""
Write-Host "Deployment complete. Restart the gateway to load the plugin:" -ForegroundColor Green
Write-Host "  docker restart $Container" -ForegroundColor Green
