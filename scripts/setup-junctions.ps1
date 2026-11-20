<#
.SYNOPSIS
  Links Google Antigravity and GitHub Copilot skills directories to the
  unified ~/.agents/skills repository via Windows NTFS Junctions.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$CentralSkills = Join-Path $env:USERPROFILE ".agents\skills"
if (-not (Test-Path $CentralSkills)) {
  New-Item -ItemType Directory -Force -Path $CentralSkills | Out-Null
}

$Targets = @(
  (Join-Path $env:USERPROFILE ".gemini\config\skills"),
  (Join-Path $env:USERPROFILE ".copilot\skills")
)

$BackupRoot = Join-Path $env:LOCALAPPDATA ("agent-tooling-backups\junction-setup-" + (Get-Date -Format "yyyyMMdd-HHmmss"))

foreach ($link in $Targets) {
  $parent = Split-Path -Parent $link
  if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  if (Test-Path $link) {
    $item = Get-Item $link
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
      Write-Host "Already linked: $link" -ForegroundColor Green
      continue
    }
    New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
    $bDst = Join-Path $BackupRoot (Split-Path -Leaf $parent)
    Write-Host "Backing up existing folder $link -> $bDst" -ForegroundColor Yellow
    Move-Item -Path $link -Destination $bDst -Force
  }
  cmd /c mklink /J "$link" "$CentralSkills"
}

Write-Host "All NTFS Junctions verified -> $CentralSkills" -ForegroundColor Cyan
