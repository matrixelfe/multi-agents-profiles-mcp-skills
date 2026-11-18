<#
.SYNOPSIS
  Restores files, repo skills, or archived skills from a ChangeId backup. Defaults to -WhatIf.
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$ChangeId,
  [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$backupDir = Join-Path "$env:LOCALAPPDATA\agent-tooling-backups" $ChangeId
$manifestPath = Join-Path $backupDir "manifest.json"
if (-not (Test-Path $manifestPath)) { throw "Manifest not found: $manifestPath" }

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if (-not $Apply) {
  Write-Output "=== ROLLBACK DRY-RUN (-WhatIf) for $ChangeId ==="
  if ($manifest[0].OriginalPath) {
    $manifest | Format-Table SkillName, OriginalPath, BackupPath -AutoSize
  } else {
    $manifest | Format-Table Target, Existed, Type, Sha256Before -AutoSize
  }
  Write-Output "Re-run with -Apply to restore."
  return
}

foreach ($entry in $manifest) {
  if ($entry.OriginalPath) {
    # Restoring an archived skill
    if (-not (Test-Path $entry.OriginalPath)) {
      Copy-Item $entry.BackupPath $entry.OriginalPath -Recurse -Force
      Write-Output "Restored archived skill: $($entry.OriginalPath)"
    }
  } elseif ($entry.Type -eq 'skill') {
    if (-not $entry.Existed -and (Test-Path $entry.Target)) {
      cmd /c rmdir "$($entry.Target)" 2>$null | Out-Null
      if (Test-Path $entry.Target) {
        Remove-Item $entry.Target -Recurse -Force
      }
      Write-Output "Removed repo skill: $($entry.Target)"
    }
  } else {
    if ($entry.Existed) {
      Copy-Item $entry.Backup $entry.Target -Force
      $restoredHash = (Get-FileHash $entry.Target -Algorithm SHA256).Hash
      if ($restoredHash -ne $entry.Sha256Before) {
        throw "SHA-256 mismatch restoring $($entry.Target)"
      }
      Write-Output "Restored: $($entry.Target) (SHA-256 verified)"
    } else {
      if (Test-Path $entry.Target) {
        Remove-Item $entry.Target -Force
        Write-Output "Removed newly created: $($entry.Target)"
      }
    }
  }
}
Write-Output "Rollback completed successfully for $ChangeId"
