<#
.SYNOPSIS
  Installs the cross-agent .agent-docs pre-commit hook into a target Git repository.
  Defaults to dry-run; pass -Apply to write the hook.
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,
  [switch]$Apply
)

$ErrorActionPreference = 'Stop'

$gitDir = Join-Path $RepoPath ".git"
if (-not (Test-Path $gitDir)) {
  throw "Target path is not a Git repository (missing .git): $RepoPath"
}

$srcHook = Join-Path $PSScriptRoot "hooks\pre-commit"
$hooksDir = Join-Path $gitDir "hooks"
$dstHook = Join-Path $hooksDir "pre-commit"

if (-not $Apply) {
  Write-Output "[DRY-RUN] Would install pre-commit hook: $srcHook -> $dstHook"
  Write-Output "Re-run with -Apply to install."
  exit 0
}

New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
Copy-Item -Path $srcHook -Destination $dstHook -Force
Write-Output "Installed .agent-docs pre-commit hook at $dstHook"
