<#
.SYNOPSIS
  Builds the native Windows desktop app AgentToolingControlCenter.exe
  (embedded WebView2 window, no console, zero lingering background processes on close).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

python -m pip install -q pyinstaller pywebview

python -m PyInstaller `
  --noconfirm `
  --onefile `
  --noconsole `
  --name "AgentToolingControlCenter" `
  --add-data "agent_tooling/ui/index.html;agent_tooling/ui" `
  --collect-all "webview" `
  --hidden-import "agent_tooling.profile_switcher" `
  --hidden-import "agent_tooling.skill_installer" `
  --hidden-import "agent_tooling.token_savers" `
  --hidden-import "agent_tooling.memory_learning_logs" `
  launcher_exe.py

$exe = Join-Path $RepoRoot "dist\AgentToolingControlCenter.exe"
if (Test-Path $exe) {
  $sizeMB = [math]::Round((Get-Item $exe).Length / 1MB, 2)
  Write-Host "Built native desktop EXE successfully: $exe ($sizeMB MB)" -ForegroundColor Green
} else {
  throw "Build failed: $exe not found."
}
