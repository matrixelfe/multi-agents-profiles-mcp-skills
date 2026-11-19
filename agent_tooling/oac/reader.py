"""Read-only inspector and safe atomic updater for Open Agents Control (OAC V3.4) and client configs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from agent_tooling.security.redact import redact_dict

FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)


def _strip_jsonc_comments(text: str) -> str:
    """Strip // line comments and /* */ block comments from JSONC safely."""
    out: list[str] = []
    in_str = False
    escape = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_agent_markdown(md_path: Path, rel_root: Path) -> dict[str, Any]:
    """Parse an agent markdown file's YAML frontmatter (model, mode, steps, permissions)."""
    text = md_path.read_text(encoding="utf-8-sig", errors="replace")
    rel_id = md_path.relative_to(rel_root).as_posix()
    stem = md_path.stem
    fm: dict[str, Any] = {}
    m = FRONTMATTER_RE.match(text)
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            fm = {}

    # Extract allowed/denied subagents & tool permissions
    allowed_subagents: list[str] = []
    denied_tools: list[str] = []
    perms = fm.get("permissions", [])
    if isinstance(perms, list):
        for p in perms:
            if not isinstance(p, dict):
                continue
            action = str(p.get("action", ""))
            resource = str(p.get("resource", ""))
            effect = str(p.get("effect", ""))
            if action == "subagent" and effect == "allow" and resource != "*":
                allowed_subagents.append(resource)
            elif effect == "deny" and action != "subagent":
                denied_tools.append(f"{action}:{resource}")
    elif isinstance(perms, dict):
        for k, v in perms.items():
            if v == "deny":
                denied_tools.append(str(k))

    return {
        "rel_path": rel_id,
        "id": stem,
        "group": "code_mode" if rel_id.startswith("agents/") else "oac",
        "mode": fm.get("mode", "subagent" if "subagent" in rel_id else "primary"),
        "model": fm.get("model"),
        "steps": fm.get("steps"),
        "temperature": fm.get("temperature"),
        "description": fm.get("description", ""),
        "allowed_subagents": allowed_subagents,
        "denied_tools": denied_tools,
        "permissions_raw": perms,
    }


def load_oac_snapshot(
    opencode_root: Path | None = None,
    codex_root: Path | None = None,
    tooling_root: Path | None = None,
) -> dict[str, Any]:
    """Read full OAC V3.4 + OpenCode + Codex + Profiles snapshot without side effects."""
    home = Path.home()
    oc_root = opencode_root or (home / ".config" / "opencode")
    cx_root = codex_root or (home / ".codex")
    tl_root = tooling_root or (home / ".agents" / "tooling")

    # 1. oac-routing.yaml
    routing_path = oc_root / "config" / "oac-routing.yaml"
    routing: dict[str, Any] = {}
    if routing_path.exists():
        routing = yaml.safe_load(routing_path.read_text(encoding="utf-8-sig")) or {}

    # 2. oac-spend-guard.jsonc
    spend_path = oc_root / "config" / "oac-spend-guard.jsonc"
    spend_guard: dict[str, Any] = {}
    if spend_path.exists():
        try:
            spend_guard = json.loads(_strip_jsonc_comments(spend_path.read_text(encoding="utf-8-sig")))
        except Exception:
            spend_guard = {"state": "UNKNOWN"}

    # 3. agent-metadata.json
    meta_path = oc_root / "config" / "agent-metadata.json"
    agent_metadata: dict[str, Any] = {}
    if meta_path.exists():
        try:
            agent_metadata = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        except Exception:
            agent_metadata = {}

    # 4. quota-state.json (read-only summary only, never expose sensitive blobs)
    quota_path = oc_root / "state" / "oac" / "quota-state.json"
    quota_summary: dict[str, Any] = {"exists": quota_path.exists(), "models_tracked": 0, "cooldowns": []}
    if quota_path.exists():
        try:
            qdata = json.loads(quota_path.read_text(encoding="utf-8-sig"))
            if isinstance(qdata, dict):
                models_map = qdata.get("models") or qdata
                if isinstance(models_map, dict):
                    quota_summary["models_tracked"] = len(models_map)
                    for mk, mv in list(models_map.items())[:50]:
                        if isinstance(mv, dict) and (mv.get("cooldownUntil") or mv.get("exhausted") or mv.get("status") == "cooldown"):
                            quota_summary["cooldowns"].append({
                                "model": mk,
                                "status": mv.get("status", "cooldown"),
                                "cooldownUntil": mv.get("cooldownUntil"),
                                "reason": mv.get("lastError") or mv.get("reason"),
                            })
        except Exception:
            pass

    # 5. Agents from agent/**/*.md and agents/*.md
    agents: list[dict[str, Any]] = []
    assignments = routing.get("assignments", {}) if isinstance(routing, dict) else {}
    roles_cfg = routing.get("roles", {}) if isinstance(routing, dict) else {}

    # Reverse map rel_path -> role
    path_to_role: dict[str, str] = {}
    for role_name, rcfg in roles_cfg.items():
        if isinstance(rcfg, dict):
            for ap in rcfg.get("agents", []):
                path_to_role[str(ap).replace("\\", "/")] = role_name

    for sub in ("agent", "agents"):
        d = oc_root / sub
        if not d.exists():
            continue
        for md in sorted(d.rglob("*.md")):
            info = parse_agent_markdown(md, oc_root)
            rp = info["rel_path"]
            info["oac_assigned_model"] = assignments.get(rp) or info["model"]
            info["oac_role"] = path_to_role.get(rp)
            if info["oac_role"] and info["oac_role"] in roles_cfg:
                rcfg = roles_cfg[info["oac_role"]]
                info["preferred_chain"] = rcfg.get("preferred", [])
                info["fallback_chain"] = rcfg.get("fallback", [])
            else:
                info["preferred_chain"] = []
                info["fallback_chain"] = []
            agents.append(info)

    # 6. OpenCode opencode.json (redacted!)
    oc_json_path = oc_root / "opencode.json"
    oc_mcps: dict[str, Any] = {}
    oc_plugins_declared: list[str] = []
    if oc_json_path.exists():
        try:
            oc_data = json.loads(oc_json_path.read_text(encoding="utf-8-sig"))
            mcp_sec = oc_data.get("mcp", {})
            servers = mcp_sec.get("servers", {}) if isinstance(mcp_sec, dict) else {}
            for k, v in servers.items():
                if isinstance(v, dict):
                    oc_mcps[k] = {
                        "type": v.get("type", "local"),
                        "disabled": bool(v.get("disabled", False)),
                        "enabled": not bool(v.get("disabled", False)),
                    }
            oc_plugins_declared = [str(p) for p in oc_data.get("plugins", [])]
        except Exception:
            pass

    # Local plugins dir
    oc_plugins_local: list[str] = []
    pdir = oc_root / "plugins"
    if pdir.exists():
        oc_plugins_local = sorted(p.name for p in pdir.iterdir())

    # 7. Codex config.toml (redacted!)
    cx_toml_path = cx_root / "config.toml"
    codex_mcps: dict[str, Any] = {}
    codex_plugins: dict[str, bool] = {}
    if cx_toml_path.exists():
        try:
            cx_data = tomllib.loads(cx_toml_path.read_text(encoding="utf-8-sig"))
            for k, v in cx_data.get("mcp_servers", {}).items():
                if isinstance(v, dict):
                    codex_mcps[k] = {
                        "enabled": bool(v.get("enabled", True)),
                        "bundled": k == "node_repl",
                    }
            for k, v in cx_data.get("plugins", {}).items():
                if isinstance(v, dict):
                    codex_plugins[k] = bool(v.get("enabled", False))
        except Exception:
            pass

    # 8. Profiles YAML
    profiles: dict[str, Any] = {}
    p_dir = tl_root / "profiles"
    if p_dir.exists():
        for pf in sorted(p_dir.glob("*.yaml")):
            try:
                profiles[pf.stem] = yaml.safe_load(pf.read_text(encoding="utf-8-sig")) or {}
            except Exception:
                pass

    # 9. Recommendations YAML
    rec_path = tl_root / "recommendations.yaml"
    recommendations: dict[str, Any] = {}
    if rec_path.exists():
        try:
            recommendations = yaml.safe_load(rec_path.read_text(encoding="utf-8-sig")) or {}
        except Exception:
            pass

    # 10. Skills inventory counts
    shared_skills_dir = home / ".agents" / "skills"
    shared_skills = sorted(
        d.name for d in shared_skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    ) if shared_skills_dir.exists() else []

    oc_skills_dir = oc_root / "skills"
    oc_skills = sorted(
        d.name for d in oc_skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    ) if oc_skills_dir.exists() else []

    return redact_dict({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "oac": {
            "routing_version": routing.get("routing_version"),
            "routing": routing.get("routing", {}),
            "providers": routing.get("providers", {}),
            "privacy": routing.get("privacy", {}),
            "roles": roles_cfg,
            "assignments": assignments,
            "payg": routing.get("payg", {}),
            "spend_guard": {
                "state": spend_guard.get("state", "UNKNOWN"),
                "blocked_by_policy": spend_guard.get("blocked_by_policy", []),
            },
            "quota_summary": quota_summary,
        },
        "agents": agents,
        "mcps": {
            "opencode": oc_mcps,
            "codex": codex_mcps,
        },
        "plugins": {
            "opencode_declared": oc_plugins_declared,
            "opencode_local": oc_plugins_local,
            "codex": codex_plugins,
        },
        "profiles": profiles,
        "recommendations": recommendations,
        "skills": {
            "shared_count": len(shared_skills),
            "opencode_global_count": len(oc_skills),
            "opencode_global": oc_skills,
            "shared_sample": shared_skills[:60],
        },
    })


def _backup_file(target: Path, tag: str) -> tuple[str, str]:
    """Create private SHA-256 backup under %LOCALAPPDATA%/agent-tooling-backups."""
    local_app = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    change_id = f"chg-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{tag}"
    bdir = local_app / "agent-tooling-backups" / change_id
    bdir.mkdir(parents=True, exist_ok=True)
    bak = bdir / target.name
    shutil.copy2(target, bak)
    h = hashlib.sha256(target.read_bytes()).hexdigest()
    (bdir / "manifest.json").write_text(
        json.dumps({"ChangeId": change_id, "Target": str(target), "Backup": str(bak), "Sha256Before": h}, indent=2),
        encoding="utf-8",
    )
    return change_id, h


def update_oac_assignment(agent_rel_path: str, new_model: str, opencode_root: Path | None = None) -> dict[str, Any]:
    """Safely update an agent's model assignment in oac-routing.yaml (never touching PAYG/privacy)."""
    oc_root = opencode_root or (Path.home() / ".config" / "opencode")
    routing_path = oc_root / "config" / "oac-routing.yaml"
    if not routing_path.exists():
        raise FileNotFoundError(f"oac-routing.yaml not found: {routing_path}")

    # Security guard: block denied PAYG providers
    blocked_prefixes = ("alibaba/", "anthropic/", "google/", "z.ai/", "minimax/", "kimi-for-coding/")
    if any(new_model.startswith(p) for p in blocked_prefixes):
        raise ValueError(f"Model '{new_model}' belongs to a spend-guard blocked provider. Rejected.")

    change_id, pre_hash = _backup_file(routing_path, "ui-oac-assignment")
    text = routing_path.read_text(encoding="utf-8-sig")

    # Preserve comments by doing a targeted line replacement in assignments:
    pattern = re.compile(rf"^(\s*{re.escape(agent_rel_path)}:\s*)(.+)$", re.MULTILINE)
    if not pattern.search(text):
        raise KeyError(f"Assignment '{agent_rel_path}' not found in oac-routing.yaml")

    new_text = pattern.sub(rf"\g<1>{new_model}", text, count=1)
    tmp = routing_path.with_suffix(".yaml.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    # Validate YAML parses cleanly
    yaml.safe_load(tmp.read_text(encoding="utf-8"))
    tmp.replace(routing_path)

    # Optionally run oac-routing-sync.mjs if present
    sync_script = oc_root / "scripts" / "oac-routing-sync.mjs"
    synced = False
    if sync_script.exists():
        res = subprocess.run(["node", str(sync_script)], cwd=str(oc_root), capture_output=True, text=True, timeout=15)
        synced = res.returncode == 0

    return {
        "change_id": change_id,
        "agent": agent_rel_path,
        "model": new_model,
        "sha256_before": pre_hash,
        "synced_jsonc": synced,
    }


def update_oac_retry_behavior(
    line2_fallback_enabled: bool | None = None,
    go_free_allowed: list[str] | None = None,
    opencode_root: Path | None = None,
) -> dict[str, Any]:
    """Safely update routing retry/fallback flags in oac-routing.yaml while preserving comments."""
    oc_root = opencode_root or (Path.home() / ".config" / "opencode")
    routing_path = oc_root / "config" / "oac-routing.yaml"
    if not routing_path.exists():
        raise FileNotFoundError(f"oac-routing.yaml not found: {routing_path}")

    change_id, pre_hash = _backup_file(routing_path, "ui-oac-retry")
    text = routing_path.read_text(encoding="utf-8-sig")

    if line2_fallback_enabled is not None:
        val = "true" if line2_fallback_enabled else "false"
        text = re.sub(r"^(\s*line2_fallback_enabled:\s*)(true|false)", rf"\g<1>{val}", text, count=1, flags=re.MULTILINE)

    if go_free_allowed is not None:
        cleaned = [m.strip() for m in go_free_allowed if m.strip() and "iceman" not in m.lower()]
        arr = "[" + ", ".join(cleaned) + "]"
        text = re.sub(r"^(\s*go_free_allowed:\s*)\[.*?\]", rf"\g<1>{arr}", text, count=1, flags=re.MULTILINE)

    tmp = routing_path.with_suffix(".yaml.tmp")
    tmp.write_text(text, encoding="utf-8")
    yaml.safe_load(tmp.read_text(encoding="utf-8"))
    tmp.replace(routing_path)

    sync_script = oc_root / "scripts" / "oac-routing-sync.mjs"
    synced = False
    if sync_script.exists():
        res = subprocess.run(["node", str(sync_script)], cwd=str(oc_root), capture_output=True, text=True, timeout=15)
        synced = res.returncode == 0

    return {"change_id": change_id, "sha256_before": pre_hash, "synced_jsonc": synced}
