<#
.SYNOPSIS
  Builds the standalone AgentToolingControlCenter.exe (no console window)
  using PyInstaller so the Control Center launches with a double-click.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not (python -m pip show pyinstaller 2>$null)) {
  Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
  python -m pip install pyinstaller
}

python -m PyInstaller `
  --noconfirm `
  --onefile `
  --noconsole `
  --name "AgentToolingControlCenter" `
  --add-data "agent_tooling/ui/index.html;agent_tooling/ui" `
  --hidden-import "agent_tooling.profile_switcher" `
  --hidden-import "agent_tooling.skill_installer" `
  --hidden-import "agent_tooling.token_savers" `
  launcher_exe.py

$exe = Join-Path $RepoRoot "dist\AgentToolingControlCenter.exe"
if (Test-Path $exe) {
  $sizeMB = [math]::Round((Get-Item $exe).Length / 1MB, 2)
  Write-Host "Built successfully: $exe ($sizeMB MB)" -ForegroundColor Green
} else {
  throw "Build failed: $exe not found."
}
