<#
.SYNOPSIS
  Applies planned opencode.jsonc, .codex/config.toml, and profile skills to a target repo. Defaults to -WhatIf.
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$RepoPath,
  [Parameter(Mandatory = $true)]
  [string[]]$Profiles,
  [switch]$Apply,
  [string]$ToolingRoot = "$env:USERPROFILE\.agents\tooling"
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }

$planScript = Join-Path $ToolingRoot "scripts\plan.ps1"
$plan = & $planScript -RepoPath $RepoPath -Profiles $Profiles -ToolingRoot $ToolingRoot

$ocTarget = Join-Path $RepoPath "opencode.jsonc"
$codexDir = Join-Path $RepoPath ".codex"
$codexTarget = Join-Path $codexDir "config.toml"
$repoSkillsDir = Join-Path $RepoPath ".agents\skills"

if (-not $Apply) {
  Write-Output "=== DRY-RUN (-WhatIf) ==="
  Write-Output "Target Repo: $RepoPath"
  Write-Output "Profiles: $($Profiles -join ', ')"
  Write-Output "Target OpenCode: $ocTarget"
  Write-Output $plan.OpenCodeJsonc
  Write-Output "`nTarget Codex: $codexTarget"
  Write-Output $plan.CodexToml
  Write-Output "`nSelected Skills for Repo: $($plan.SelectedSkills.Count)"
  if ($plan.SelectedSkills.Count -gt 0) {
    Write-Output "Skills: $($plan.SelectedSkills -join ', ')"
  }
  Write-Output "`nRe-run with -Apply to write files, link skills, and create a rollback manifest."
  return
}

$changeId = "chg-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$backupDir = Join-Path "$env:LOCALAPPDATA\agent-tooling-backups" $changeId
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$manifest = @()
foreach ($target in @($ocTarget, $codexTarget)) {
  if (Test-Path $target) {
    $rel = $target.Replace($RepoPath, '').TrimStart('\', '/')
    $bakFile = Join-Path $backupDir ($rel -replace '[\\/]', '_')
    Copy-Item $target $bakFile -Force
    $hash = (Get-FileHash $target -Algorithm SHA256).Hash
    $manifest += [PSCustomObject]@{ Target = $target; Backup = $bakFile; Existed = $true; Sha256Before = $hash; Type = 'file' }
  } else {
    $manifest += [PSCustomObject]@{ Target = $target; Backup = ''; Existed = $false; Sha256Before = ''; Type = 'file' }
  }
}

# Atomic write of config files
$ocTmp = "$ocTarget.tmp"
$plan.OpenCodeJsonc | Set-Content $ocTmp -Encoding UTF8
Move-Item $ocTmp $ocTarget -Force

if (-not (Test-Path $codexDir)) { New-Item -ItemType Directory -Path $codexDir -Force | Out-Null }
$codexTmp = "$codexTarget.tmp"
$plan.CodexToml | Set-Content $codexTmp -Encoding UTF8
Move-Item $codexTmp $codexTarget -Force

# Link / copy repo-specific skills
if ($plan.SelectedSkills.Count -gt 0) {
  if (-not (Test-Path $repoSkillsDir)) {
    New-Item -ItemType Directory -Path $repoSkillsDir -Force | Out-Null
  }
  $catalogDir = "$env:USERPROFILE\.agents\catalog\skills"
  $sharedSkillsDir = "$env:USERPROFILE\.agents\skills"

  foreach ($s in $plan.SelectedSkills) {
    $dest = Join-Path $repoSkillsDir $s
    if (Test-Path $dest) {
      $manifest += [PSCustomObject]@{ Target = $dest; Backup = ''; Existed = $true; Sha256Before = ''; Type = 'skill' }
      continue
    }

    $src = $null
    if (Test-Path (Join-Path $catalogDir $s)) {
      $src = Join-Path $catalogDir $s
    } elseif (Test-Path (Join-Path $sharedSkillsDir $s)) {
      $src = Join-Path $sharedSkillsDir $s
    }

    if ($src) {
      cmd /c mklink /J "$dest" "$src" 2>$null | Out-Null
      if (-not (Test-Path $dest)) {
        Copy-Item $src $dest -Recurse -Force
      }
      $manifest += [PSCustomObject]@{ Target = $dest; Backup = ''; Existed = $false; Sha256Before = ''; Type = 'skill' }
    } else {
      Write-Warning "Skill source not found for: $s"
    }
  }
}

$manifest | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $backupDir "manifest.json") -Encoding UTF8

Write-Output "Applied profiles [$($Profiles -join ', ')] to $RepoPath"
Write-Output "ChangeId: $changeId (Backup: $backupDir)"
