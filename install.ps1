<#
.SYNOPSIS
  Installer for agent-tooling v3 (Windows PowerShell 5.1+).
  Sets up ~/.agents/tooling, cold skill catalog, Python package, and initial read-only scan.
#>
$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot
$ToolingHome = Join-Path $env:USERPROFILE ".agents\tooling"
$CatalogHome = Join-Path $env:USERPROFILE ".agents\catalog\skills"

Write-Output "=== Installing agent-tooling v3 ==="
New-Item -ItemType Directory -Path $ToolingHome, $CatalogHome -Force | Out-Null

# Copy profiles, clients, scripts, and policy if not present
foreach ($dir in @("profiles", "clients", "scripts")) {
  $src = Join-Path $RepoRoot $dir
  $dst = Join-Path $ToolingHome $dir
  if (Test-Path $src) {
    Copy-Item $src $dst -Recurse -Force
  }
}
Copy-Item (Join-Path $RepoRoot "policy.yaml") (Join-Path $ToolingHome "policy.yaml") -Force

$regTarget = Join-Path $ToolingHome "registry.yaml"
if (-not (Test-Path $regTarget)) {
  Copy-Item (Join-Path $RepoRoot "registry.example.yaml") $regTarget -Force
  Write-Output "Created starter registry at $regTarget"
}

Write-Output "Installing Python package (editable/user)..."
python -m pip install --quiet --upgrade PyYAML
python -m pip install --quiet -e $RepoRoot

Write-Output "Running initial read-only scan and health check..."
python -m agent_tooling scan
python -m agent_tooling doctor

Write-Output "`nDone! Use 'agent-tooling scan|status|doctor|backup' or 'scripts\apply.ps1 -RepoPath <path> -Profiles <profile>'."
