<#
.SYNOPSIS
  Installs or updates curated upstream skills from manifests/skills-top.yaml
  and copies custom local skills into ~/.agents/skills.
#>
[CmdletBinding()]
param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$TargetSkills = Join-Path $env:USERPROFILE ".agents\skills"
New-Item -ItemType Directory -Force -Path $TargetSkills | Out-Null

$ManifestPath = Join-Path $RepoRoot "manifests\skills-top.yaml"
Write-Host "Reading manifest: $ManifestPath" -ForegroundColor Cyan

$cmds = Select-String -Path $ManifestPath -Pattern 'install_cmd:\s*"([^"]+)"' | ForEach-Object {
  $_.Matches[0].Groups[1].Value
}

foreach ($cmd in $cmds) {
  Write-Host "-> $cmd" -ForegroundColor Yellow
  if (-not $DryRun) {
    Invoke-Expression $cmd
  }
}

$CustomDir = Join-Path $RepoRoot "skills\custom"
if (Test-Path $CustomDir) {
  Get-ChildItem -Path $CustomDir -Directory | ForEach-Object {
    $dst = Join-Path $TargetSkills $_.Name
    Write-Host "-> Syncing custom skill $($_.Name) -> $dst" -ForegroundColor Green
    if (-not $DryRun) {
      New-Item -ItemType Directory -Force -Path $dst | Out-Null
      Copy-Item -Path "$($_.FullName)\*" -Destination $dst -Recurse -Force
    }
  }
}

Write-Host "Done. Run 'agent-tooling scan' to refresh the SQLite registry." -ForegroundColor Cyan
