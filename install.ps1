<#
.SYNOPSIS
  Installer for agent-tooling v3 (Windows PowerShell 5.1+).
  Sets up ~/.agents/tooling, cold skill catalog, Python package, and initial read-only scan.
#>
$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot
$ToolingHome = Join-Path $env:USERPROFILE ".agents\tooling"
$SkillsHome = Join-Path $env:USERPROFILE ".agents\skills"
$CatalogHome = Join-Path $env:USERPROFILE ".agents\catalog\skills"

Write-Output "=== Installing agent-tooling v3 ==="
New-Item -ItemType Directory -Path $ToolingHome, $SkillsHome, $CatalogHome -Force | Out-Null

# Install bundled core skills (e.g., project-docs, project-changelog) into ~/.agents/skills
$bundledSkills = Join-Path $RepoRoot "skills"
if (Test-Path $bundledSkills) {
  Get-ChildItem -Path $bundledSkills -Directory | ForEach-Object {
    $targetSkill = Join-Path $SkillsHome $_.Name
    if (-not (Test-Path $targetSkill)) {
      Copy-Item $_.FullName $targetSkill -Recurse -Force
      Write-Output "Installed bundled skill: $($_.Name) -> $targetSkill"
    }
  }
}

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

$globalAgentsTarget = Join-Path (Join-Path $env:USERPROFILE ".agents") "AGENTS.md"
$globalAgentsTemplate = Join-Path $RepoRoot "templates\AGENTS.global.md"
if ((Test-Path $globalAgentsTemplate) -and (-not (Test-Path $globalAgentsTarget))) {
  Copy-Item $globalAgentsTemplate $globalAgentsTarget -Force
  Write-Output "Created starter global AGENTS.md at $globalAgentsTarget"
}

Write-Output "Installing Python package (editable/user)..."
python -m pip install --quiet --upgrade PyYAML
python -m pip install --quiet -e $RepoRoot

Write-Output "Running initial read-only scan and health check..."
python -m agent_tooling scan
python -m agent_tooling doctor

Write-Output "`nDone! Use 'agent-tooling scan|status|doctor|backup' or 'scripts\apply.ps1 -RepoPath <path> -Profiles <profile>'."
