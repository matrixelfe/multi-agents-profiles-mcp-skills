"""Read-only multi-client scanner for OpenCode, OpenChamber, Codex, Claude, and Antigravity."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fp(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def seed_client_targets(conn: sqlite3.Connection, home: Path | None = None) -> dict[str, str]:
    """Register v3 client_targets and detect local availability without executing anything."""
    home = home or Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    now = _now()

    targets = [
        ("opencode:local", "opencode", "local", "user", (home / ".config" / "opencode" / "opencode.json").exists(), "~/.config/opencode/opencode.json"),
        ("openchamber:opencode-runtime", "openchamber", "opencode-runtime", "user", (appdata / "openchamber").exists(), "AppData/Roaming/openchamber"),
        ("codex:local", "codex", "local", "user", (home / ".codex" / "config.toml").exists(), "~/.codex/config.toml"),
        ("claude:chat", "claude", "chat", "account", False, "account-only"),
        ("claude:cowork", "claude", "cowork", "desktop", (appdata / "Claude").exists(), "AppData/Roaming/Claude"),
        ("claude:code-local", "claude", "code-local", "repo", (home / ".claude").exists(), "~/.claude"),
        ("claude:code-cloud", "claude", "code-cloud", "cloud", False, "cloud-only"),
        ("antigravity:app", "antigravity", "app", "user", (home / ".gemini" / "antigravity").exists(), "~/.gemini/antigravity"),
        ("antigravity:ide", "antigravity", "ide", "repo", (home / ".gemini" / "antigravity").exists(), "~/.gemini/antigravity"),
        ("antigravity:cli", "antigravity", "cli", "user", (home / ".gemini" / "antigravity").exists(), "~/.gemini/antigravity"),
    ]

    status_map: dict[str, str] = {}
    with conn:
        for tid, fam, surf, scope, exists, ev in targets:
            avail = "available" if exists else ("observe_only" if scope in ("account", "cloud") else "not_installed")
            status_map[tid] = avail
            conn.execute(
                """
                INSERT INTO client_targets(target_id, family, surface, scope, availability, last_verified, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(target_id) DO UPDATE SET
                    availability = excluded.availability,
                    last_verified = excluded.last_verified,
                    evidence = excluded.evidence
                """,
                (tid, fam, surf, scope, avail, now, ev),
            )
    return status_map


def import_registry_yaml(conn: sqlite3.Connection, registry_path: Path) -> int:
    """Import registry.yaml in read-only mode into SQLite resources."""
    if not registry_path.exists():
        return 0
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    servers = data.get("servers", {})
    count = 0
    with conn:
        for name, cfg in servers.items():
            rid = f"mcp:{name}"
            fp = _fp(json.dumps(cfg, sort_keys=True))
            conn.execute(
                """
                INSERT INTO resources(resource_id, kind, display_name, source, owner_client, fingerprint, risk, managed_by)
                VALUES (?, 'mcp', ?, 'registry.yaml', 'shared', ?, 'LOW', 'agent_tooling')
                ON CONFLICT(resource_id) DO UPDATE SET
                    fingerprint = excluded.fingerprint
                """,
                (rid, name, fp),
            )
            count += 1
    return count


def scan_opencode(conn: sqlite3.Connection, oc_path: Path) -> int:
    """Scan OpenCode opencode.json (read-only) and record installations."""
    if not oc_path.exists():
        return 0
    data = json.loads(oc_path.read_text(encoding="utf-8-sig"))
    mcp = data.get("mcp", {})
    servers = mcp.get("servers", {}) if isinstance(mcp, dict) else {}
    now = _now()
    count = 0
    with conn:
        for name, cfg in servers.items():
            rid = f"mcp:{name}"
            disabled = bool(cfg.get("disabled", False)) if isinstance(cfg, dict) else False
            enabled = 0 if disabled else 1
            conn.execute(
                """
                INSERT OR IGNORE INTO resources(resource_id, kind, display_name, source, owner_client, managed_by)
                VALUES (?, 'mcp', ?, 'opencode.json', 'opencode', 'manual')
                """,
                (rid, name),
            )
            inst_id = f"opencode:user:{name}"
            conn.execute(
                """
                INSERT INTO installations(installation_id, resource_id, client, scope, path_ref, availability, detected_enabled, last_seen)
                VALUES (?, ?, 'opencode', 'user', ?, 'available', ?, ?)
                ON CONFLICT(resource_id, client, scope, path_ref) DO UPDATE SET
                    detected_enabled = excluded.detected_enabled,
                    last_seen = excluded.last_seen
                """,
                (inst_id, rid, str(oc_path), enabled, now),
            )
            count += 1
    return count


def scan_codex(conn: sqlite3.Connection, codex_path: Path) -> int:
    """Scan Codex config.toml (read-only) and record installations without reading secrets."""
    if not codex_path.exists():
        return 0
    data = tomllib.loads(codex_path.read_text(encoding="utf-8-sig"))
    servers = data.get("mcp_servers", {})
    now = _now()
    count = 0
    with conn:
        for name, cfg in servers.items():
            rid = f"mcp:{name}"
            enabled_val = cfg.get("enabled", True) if isinstance(cfg, dict) else True
            enabled = 1 if enabled_val else 0
            conn.execute(
                """
                INSERT OR IGNORE INTO resources(resource_id, kind, display_name, source, owner_client, managed_by)
                VALUES (?, 'mcp', ?, 'config.toml', 'codex', 'manual')
                """,
                (rid, name),
            )
            inst_id = f"codex:user:{name}"
            conn.execute(
                """
                INSERT INTO installations(installation_id, resource_id, client, scope, path_ref, availability, detected_enabled, last_seen)
                VALUES (?, ?, 'codex', 'user', ?, 'available', ?, ?)
                ON CONFLICT(resource_id, client, scope, path_ref) DO UPDATE SET
                    detected_enabled = excluded.detected_enabled,
                    last_seen = excluded.last_seen
                """,
                (inst_id, rid, str(codex_path), enabled, now),
            )
            count += 1
    return count


def scan_skills_dir(conn: sqlite3.Connection, skills_dir: Path, client: str, scope: str) -> int:
    """Scan a skills directory for SKILL.md entries without loading bodies."""
    if not skills_dir.exists():
        return 0
    now = _now()
    count = 0
    with conn:
        for entry in skills_dir.iterdir():
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if not skill_md.exists():
                continue
            rid = f"skill:{entry.name}"
            conn.execute(
                """
                INSERT OR IGNORE INTO resources(resource_id, kind, display_name, source, owner_client, managed_by)
                VALUES (?, 'skill', ?, ?, ?, 'manual')
                """,
                (rid, entry.name, str(skills_dir), client),
            )
            inst_id = f"{client}:{scope}:{entry.name}"
            conn.execute(
                """
                INSERT INTO installations(installation_id, resource_id, client, scope, path_ref, availability, detected_enabled, last_seen)
                VALUES (?, ?, ?, ?, ?, 'available', 1, ?)
                ON CONFLICT(resource_id, client, scope, path_ref) DO UPDATE SET
                    last_seen = excluded.last_seen
                """,
                (inst_id, rid, client, scope, str(entry), now),
            )
            count += 1
    return count
