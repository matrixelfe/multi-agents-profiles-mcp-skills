"""3-Layer Global Instructions Synchronizer (BEGIN/END Managed Block).

Propagates the canonical ~/.agents/AGENTS.md into all 5 harnesses
(OpenCode/OpenChamber, Codex CLI, Claude Code, GitHub Copilot, Google Antigravity)
WITHOUT overwriting each harness's native rules outside the managed block.
Creates SHA-256 backups in %LOCALAPPDATA%\\agent-tooling-backups before modifying files.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BEGIN_MARKER = "<!-- BEGIN:UNIFIED-AGENTS (managed by agent-tooling sync-instructions — do not edit inside this block) -->"
END_MARKER = "<!-- END:UNIFIED-AGENTS -->"
_BLOCK_RE = re.compile(
    r"<!-- BEGIN:UNIFIED-AGENTS[^>]*-->.*?<!-- END:UNIFIED-AGENTS -->",
    re.DOTALL,
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _get_targets(home: Path) -> list[tuple[str, Path]]:
    return [
        ("opencode", home / ".config" / "opencode" / "AGENTS.md"),
        ("codex", home / ".codex" / "AGENTS.md"),
        ("claude", home / ".claude" / "CLAUDE.md"),
        ("copilot", home / ".copilot" / "copilot-instructions.md"),
        ("antigravity", home / ".gemini" / "config" / "plugins" / "oac-custom-agents" / "rules" / "AGENTS.md"),
    ]


def _backup_if_exists(path: Path, backup_dir: Path, harness: str) -> str | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    raw = path.read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    shutil.copy2(path, backup_dir / f"{harness}_{path.name}")
    return h


def _merge_managed_block(existing_text: str, canonical_body: str) -> str:
    managed = f"{BEGIN_MARKER}\n{canonical_body.strip()}\n{END_MARKER}"
    if _BLOCK_RE.search(existing_text):
        return _BLOCK_RE.sub(lambda _: managed, existing_text, count=1)
    # If file already equals canonical_body (e.g. OpenCode exact copy), wrap cleanly
    if existing_text.strip() == canonical_body.strip():
        return managed + "\n"
    if not existing_text.strip():
        return managed + "\n"
    return existing_text.rstrip() + "\n\n" + managed + "\n"


def get_instructions_sync_status(home: Path | None = None) -> dict[str, Any]:
    home = home or Path.home()
    src = home / ".agents" / "AGENTS.md"
    if not src.exists():
        return {"source": str(src), "source_exists": False, "targets": []}

    canonical_body = src.read_text(encoding="utf-8-sig").strip()
    expected_sha = _sha256_text(canonical_body)
    results = []
    for harness, path in _get_targets(home):
        if not path.exists():
            results.append({"harness": harness, "path": str(path), "status": "missing"})
            continue
        txt = path.read_text(encoding="utf-8-sig", errors="replace")
        m = _BLOCK_RE.search(txt)
        if m:
            inner = re.sub(r"^<!-- BEGIN:UNIFIED-AGENTS[^>]*-->\s*", "", m.group(0))
            inner = re.sub(r"\s*<!-- END:UNIFIED-AGENTS -->$", "", inner).strip()
            synced = _sha256_text(inner) == expected_sha
            results.append({"harness": harness, "path": str(path), "status": "synced" if synced else "outdated"})
        else:
            results.append({"harness": harness, "path": str(path), "status": "unmanaged"})
    return {
        "source": str(src),
        "source_exists": True,
        "source_sha": expected_sha,
        "targets": results,
    }


def sync_global_instructions(
    home: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Sync ~/.agents/AGENTS.md into all 5 harnesses via BEGIN/END managed blocks."""
    home = home or Path.home()
    src = home / ".agents" / "AGENTS.md"
    if not src.exists():
        raise FileNotFoundError(f"Canonical instructions file not found: {src}")

    canonical_body = src.read_text(encoding="utf-8-sig").strip()
    change_id = "chg-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-sync-instructions"
    local_app = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    backup_dir = local_app / "agent-tooling-backups" / change_id

    report: list[dict[str, Any]] = []
    backups_meta: dict[str, str] = {}

    for harness, target in _get_targets(home):
        existed = target.exists()
        existing_text = target.read_text(encoding="utf-8-sig", errors="replace") if existed else ""
        new_text = _merge_managed_block(existing_text, canonical_body)

        if existed and new_text == existing_text:
            report.append({"harness": harness, "path": str(target), "action": "unchanged"})
            continue

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            if existed:
                h = _backup_if_exists(target, backup_dir, harness)
                if h:
                    backups_meta[str(target)] = h
            target.write_text(new_text, encoding="utf-8")

            # Ensure Antigravity plugin.json exists (rules-only, no OAC custom agents)
            if harness == "antigravity":
                pjson = target.parent.parent / "plugin.json"
                if not pjson.exists():
                    pjson.write_text(
                        json.dumps(
                            {
                                "name": "oac-custom-agents",
                                "description": "Unified cross-agent governance rules (AGENTS.md). OAC multimodel agents run exclusively in OpenCode/OpenChamber.",
                            },
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )

        report.append({
            "harness": harness,
            "path": str(target),
            "action": "created" if not existed else "updated",
        })

    if not dry_run and backups_meta:
        (backup_dir / "manifest.json").write_text(
            json.dumps({"ChangeId": change_id, "Backups": backups_meta}, indent=2),
            encoding="utf-8",
        )

    return {
        "change_id": change_id,
        "source": str(src),
        "source_sha": _sha256_text(canonical_body),
        "dry_run": dry_run,
        "results": report,
    }
