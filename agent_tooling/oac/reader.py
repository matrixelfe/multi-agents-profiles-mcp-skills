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

# Static + audited load profile for MCPs, plugins, and clients (System RAM vs Agent Context/Tokens)
RESOURCE_LOAD_CATALOG: dict[str, dict[str, str]] = {
    "github": {"ram": "~35-100 MB", "tokens": "Alto (~40+ tools)", "level": "HIGH", "note": "Usa gh CLI en tareas simples; activar solo en perfil research."},
    "rea": {"ram": "~60-180 MB (Node+JADX)", "tokens": "Muy Alto (80+ tools)", "level": "HIGH", "note": "Solo para perfil reverse / android."},
    "craft-anything": {"ram": "~80-200 MB", "tokens": "Muy Alto (100+ tools)", "level": "HIGH", "note": "Solo para ingeniería inversa / reconstrucción."},
    "pix-mcp": {"ram": "~25-90 MB (DirectX)", "tokens": "Medio (~15 tools)", "level": "HIGH", "note": "Exclusivo perfil gamedev DirectX."},
    "cpp": {"ram": "~20-150 MB (clangd)", "tokens": "Medio (~15 tools)", "level": "HIGH", "note": "Solo proyectos C/C++ (windows-native / gamedev)."},
    "etw-trace-analyzer": {"ram": "~50-120 MB (Python)", "tokens": "Medio (~12 tools)", "level": "HIGH", "note": "Solo profiling ETW bajo demanda."},
    "dcc-mcp-renderdoc": {"ram": "Externo (RenderDoc)", "tokens": "Medio (~20 tools)", "level": "MEDIUM", "note": "Solo depuración GPU en gamedev."},
    "game-player": {"ram": "~40-90 MB (Python+Win32)", "tokens": "Medio (~15 tools)", "level": "MEDIUM", "note": "GUI automation exclusivo de gamedev."},
    "chrome-devtools": {"ram": "~60-150 MB (Chrome)", "tokens": "Alto (~25+ tools)", "level": "HIGH", "note": "Escalar solo para consola/red/perf; usar agent-browser CLI para navegar."},
    "scrapling": {"ram": "~25-60 MB (Python)", "tokens": "Bajo (~8 tools)", "level": "MEDIUM", "note": "Activar en perfil web / research."},
    "mcp-toolbox-for-databases": {"ram": "~30-70 MB", "tokens": "Medio (según tools.yaml)", "level": "MEDIUM", "note": "Activar solo en repos con base de datos."},
    "mobile-mcp": {"ram": "~30-80 MB", "tokens": "Medio (~18 tools)", "level": "MEDIUM", "note": "Activar solo con emulador/dispositivo Android."},
    "computer-use": {"ram": "~25-55 MB (Python)", "tokens": "Bajo-Medio (~12 tools)", "level": "LOW", "note": "Cross-client activo en todos los perfiles excepto gamedev."},
    "turbo": {"ram": "~40-80 MB (Node)", "tokens": "Medio (~15 tools)", "level": "MEDIUM", "note": "Desactivado para no duplicar computer-use."},
    "stitch": {"ram": "0 MB (Remote HTTP)", "tokens": "Bajo (~8 tools)", "level": "LOW", "note": "Activar bajo demanda para diseño UI Stitch."},
    "node_repl": {"ram": "~10-30 MB (Bundled)", "tokens": "Nativo Codex", "level": "LOW", "note": "Nativo bundled de Codex (do-not-touch)."},
}


def get_live_process_load() -> list[dict[str, Any]]:
    """Inspect live Windows AI/MCP processes (read-only, zero external deps)."""
    try:
        res = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if res.returncode != 0:
            return []
        tracked = re.compile(
            r"(openchamber|opencode|codex|github-mcp|mcp-cpp|pix-mcp|scrapling|node_repl|agent-browser)",
            re.I,
        )
        agg: dict[str, dict[str, Any]] = {}
        for line in res.stdout.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) < 5:
                continue
            pname = parts[0]
            if not tracked.search(pname):
                continue
            mem_digits = re.sub(r"[^\d]", "", parts[4])
            mem_mb = round(int(mem_digits) / 1024.0, 1) if mem_digits else 0.0
            entry = agg.setdefault(pname, {"process": pname, "count": 0, "ram_mb": 0.0})
            entry["count"] += 1
            entry["ram_mb"] = round(entry["ram_mb"] + mem_mb, 1)
        return sorted(agg.values(), key=lambda x: x["ram_mb"], reverse=True)
    except Exception:
        return []


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
    oc_mcps_raw: dict[str, Any] = {}
    oc_plugins_declared: list[str] = []
    if oc_json_path.exists():
        try:
            oc_data = json.loads(oc_json_path.read_text(encoding="utf-8-sig"))
            mcp_sec = oc_data.get("mcp", {})
            servers = mcp_sec.get("servers", {}) if isinstance(mcp_sec, dict) else {}
            for k, v in servers.items():
                if isinstance(v, dict):
                    oc_mcps_raw[k] = v
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
    codex_mcps_raw: dict[str, Any] = {}
    codex_plugins: dict[str, bool] = {}
    if cx_toml_path.exists():
        try:
            cx_data = tomllib.loads(cx_toml_path.read_text(encoding="utf-8-sig"))
            for k, v in cx_data.get("mcp_servers", {}).items():
                if isinstance(v, dict):
                    codex_mcps_raw[k] = v
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

    cx_skills_dir = cx_root / "skills"
    cx_skills_count = sum(
        1 for d in cx_skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    ) if cx_skills_dir.exists() else 0

    # 11. Antigravity, Claude & GitHub Copilot inspection
    ag_mcp_dir = home / ".gemini" / "antigravity" / "mcp"
    ag_mcps_set = {d.name for d in ag_mcp_dir.iterdir() if d.is_dir()} if ag_mcp_dir.exists() else set()
    ag_mcp_cfg = home / ".gemini" / "config" / "mcp_config.json"
    if ag_mcp_cfg.exists():
        try:
            ag_cfg_data = json.loads(ag_mcp_cfg.read_text(encoding="utf-8-sig"))
            ag_mcps_set.update((ag_cfg_data.get("mcpServers") or {}).keys())
        except Exception:
            pass
    ag_mcps = sorted(ag_mcps_set)
    ag_plugins_dir = home / ".gemini" / "config" / "plugins"
    ag_plugins = sorted(d.name for d in ag_plugins_dir.iterdir() if d.is_dir()) if ag_plugins_dir.exists() else []
    ag_custom_agents_dir = ag_plugins_dir / "oac-custom-agents" / "agents"
    ag_custom_agents_count = len(list(ag_custom_agents_dir.glob("*.md"))) if ag_custom_agents_dir.exists() else 0

    claude_dir = home / ".claude"
    claude_desktop_dir = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Claude"

    copilot_dir = home / ".copilot"
    copilot_mcp_cfg = copilot_dir / "mcp-config.json"
    copilot_mcps: dict[str, Any] = {}
    if copilot_mcp_cfg.exists():
        try:
            cp_data = json.loads(copilot_mcp_cfg.read_text(encoding="utf-8-sig"))
            for mk, mv in (cp_data.get("mcpServers") or {}).items():
                if isinstance(mv, dict):
                    copilot_mcps[mk] = {
                        "enabled": mv.get("enabled", True),
                        "type": mv.get("type", "local"),
                        "command": mv.get("command", ""),
                        "managed_externally": True,
                    }
        except Exception:
            pass
    copilot_plugins_dir = copilot_dir / "installed-plugins"
    copilot_plugins = sorted(d.name for d in copilot_plugins_dir.iterdir() if d.is_dir()) if copilot_plugins_dir.exists() else []
    copilot_skills_dir = copilot_dir / "skills"
    copilot_skills_count = len([d for d in copilot_skills_dir.iterdir() if d.is_dir()]) if copilot_skills_dir.exists() else 0

    ides = {
        "opencode": {
            "title": "OpenCode V2 & OpenChamber",
            "editable": True,
            "config_path": str(oc_json_path),
            "status": "available" if oc_json_path.exists() else "not_installed",
            "mcps": oc_mcps,
            "plugins_active": oc_plugins_declared + oc_plugins_local,
            "skills_count": len(oc_skills),
            "agents_count": len(agents),
        },
        "codex": {
            "title": "OpenAI Codex CLI",
            "editable": True,
            "config_path": str(cx_toml_path),
            "status": "available" if cx_toml_path.exists() else "not_installed",
            "mcps": codex_mcps,
            "plugins_active": [k for k, v in codex_plugins.items() if v],
            "skills_count": cx_skills_count,
            "agents_count": 0,
        },
        "antigravity": {
            "title": "Google Antigravity (App / IDE / CLI)",
            "editable": False,
            "sync_supported": True,
            "config_path": str(home / ".gemini" / "config"),
            "status": "available" if (home / ".gemini" / "antigravity").exists() else "not_installed",
            "mcps": {m: {"enabled": True, "managed_externally": True} for m in ag_mcps},
            "plugins_active": ag_plugins,
            "skills_count": len(shared_skills),
            "agents_count": ag_custom_agents_count,
        },
        "copilot": {
            "title": "GitHub Copilot (CLI & VS Code)",
            "editable": False,
            "config_path": str(copilot_mcp_cfg),
            "status": "available" if copilot_dir.exists() else "not_installed",
            "mcps": copilot_mcps,
            "plugins_active": copilot_plugins,
            "skills_count": copilot_skills_count,
            "agents_count": 0,
        },
        "claude": {
            "title": "Claude Desktop / Claude Code",
            "editable": False,
            "config_path": str(claude_dir),
            "status": "available" if claude_dir.exists() else "not_installed",
            "surfaces": {
                "code-local": "available" if claude_dir.exists() else "not_installed",
                "cowork": "available" if claude_desktop_dir.exists() else "not_installed",
                "chat": "observe_only",
            },
            "mcps": {},
            "plugins_active": [],
            "skills_count": len(shared_skills),
            "agents_count": 0,
        },
    }

    live_procs = get_live_process_load()
    catalog = build_catalog_lists(
        home=home,
        oc_root=oc_root,
        cx_root=cx_root,
        tl_root=tl_root,
        oc_mcps=oc_mcps,
        oc_mcps_raw=oc_mcps_raw,
        codex_mcps=codex_mcps,
        codex_mcps_raw=codex_mcps_raw,
        ag_mcps=ag_mcps,
        profiles=profiles,
        live_procs=live_procs,
    )

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
        "ides": ides,
        "catalog": catalog,
        "system_load": {
            "live_processes": live_procs,
            "resource_catalog": RESOURCE_LOAD_CATALOG,
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


def save_ide_mcps(
    ide: str,
    mcp_states: dict[str, bool],
    opencode_root: Path | None = None,
    codex_root: Path | None = None,
) -> dict[str, Any]:
    """Safely save edited MCP enabled/disabled states for OpenCode or Codex with SHA-256 backup."""
    home = Path.home()
    if ide == "opencode":
        oc_path = (opencode_root or (home / ".config" / "opencode")) / "opencode.json"
        if not oc_path.exists():
            raise FileNotFoundError(f"opencode.json not found: {oc_path}")
        change_id, pre_hash = _backup_file(oc_path, "ui-ide-opencode")
        data = json.loads(oc_path.read_text(encoding="utf-8-sig"))
        servers = data.setdefault("mcp", {}).setdefault("servers", {})
        updated = []
        for name, enabled in mcp_states.items():
            if name in servers and isinstance(servers[name], dict):
                servers[name]["disabled"] = not bool(enabled)
                updated.append(f"{name}={'ON' if enabled else 'OFF'}")
        tmp = oc_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        json.loads(tmp.read_text(encoding="utf-8"))
        tmp.replace(oc_path)
        return {"ide": ide, "change_id": change_id, "sha256_before": pre_hash, "updated": updated}

    if ide == "codex":
        cx_path = (codex_root or (home / ".codex")) / "config.toml"
        if not cx_path.exists():
            raise FileNotFoundError(f"config.toml not found: {cx_path}")
        change_id, pre_hash = _backup_file(cx_path, "ui-ide-codex")
        lines = cx_path.read_text(encoding="utf-8-sig").splitlines()
        out_lines: list[str] = []
        current_server: str | None = None
        wrote_enabled = False
        updated = []

        for line in lines:
            m = re.match(r"^\[mcp_servers\.([^\]\.]+)\]\s*$", line.strip())
            if m:
                if current_server and current_server in mcp_states and not wrote_enabled:
                    val = "true" if mcp_states[current_server] else "false"
                    out_lines.append(f"enabled = {val}")
                current_server = m.group(1)
                if current_server == "node_repl":
                    current_server = None  # Protect bundled node_repl
                wrote_enabled = False
                out_lines.append(line)
                continue
            if line.strip().startswith("["):
                if current_server and current_server in mcp_states and not wrote_enabled:
                    val = "true" if mcp_states[current_server] else "false"
                    out_lines.append(f"enabled = {val}")
                current_server = None
                wrote_enabled = False
                out_lines.append(line)
                continue
            if current_server and current_server in mcp_states and re.match(r"^\s*enabled\s*=", line):
                val = "true" if mcp_states[current_server] else "false"
                out_lines.append(f"enabled = {val}")
                wrote_enabled = True
                updated.append(f"{current_server}={'ON' if mcp_states[current_server] else 'OFF'}")
                continue
            out_lines.append(line)

        if current_server and current_server in mcp_states and not wrote_enabled:
            val = "true" if mcp_states[current_server] else "false"
            out_lines.append(f"enabled = {val}")
            updated.append(f"{current_server}={'ON' if mcp_states[current_server] else 'OFF'}")

        new_text = "\n".join(out_lines) + "\n"
        tomllib.loads(new_text)  # Validate TOML before atomic write
        tmp = cx_path.with_suffix(".toml.tmp")
        tmp.write_text(new_text, encoding="utf-8")
        tmp.replace(cx_path)
        return {"ide": ide, "change_id": change_id, "sha256_before": pre_hash, "updated": updated}

    raise ValueError(f"IDE '{ide}' is observe-only or unsupported for direct MCP edits.")


def restore_ide_defaults(
    ide: str,
    opencode_root: Path | None = None,
    codex_root: Path | None = None,
) -> dict[str, Any]:
    """Restore safe Core Minimal defaults for an IDE (computer-use ON, all specialized MCPs OFF)."""
    snap = load_oac_snapshot(opencode_root=opencode_root, codex_root=codex_root)
    if ide not in ("opencode", "codex"):
        raise ValueError(f"IDE '{ide}' does not support automatic restore.")
    mcps = snap["ides"][ide]["mcps"]
    defaults = {name: (name == "computer-use") for name in mcps.keys() if name != "node_repl"}
    return save_ide_mcps(ide, defaults, opencode_root=opencode_root, codex_root=codex_root)


def generate_ai_config_recommendations(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Deterministic AI Config Optimizer: audits all IDEs, load, OAC safety, and returns prioritized advice."""
    findings: list[dict[str, Any]] = []
    score = 100

    # 1. Check OpenCode global MCP bloat
    oc_mcps = snapshot.get("ides", {}).get("opencode", {}).get("mcps", {})
    oc_heavy_on = [
        k for k, v in oc_mcps.items()
        if v.get("enabled") and k != "computer-use"
    ]
    if oc_heavy_on:
        score -= min(30, len(oc_heavy_on) * 8)
        findings.append({
            "severity": "HIGH",
            "category": "OpenCode RAM & Tokens",
            "title": f"{len(oc_heavy_on)} MCP(s) especializados activos globalmente en OpenCode",
            "detail": f"Activos en global: {', '.join(oc_heavy_on)}. Moverlos a perfiles por proyecto libera RAM y reduce schemas en el prompt.",
            "action": "restore_opencode_core",
            "action_label": "Optimizar OpenCode a Core Mínimo",
        })
    else:
        findings.append({
            "severity": "OPTIMAL",
            "category": "OpenCode Core",
            "title": "OpenCode V2 en estado Core Mínimo óptimo",
            "detail": "Solo computer-use activo globalmente; 0 MCPs pesados de GameDev/Reversing/C++ en reposo.",
        })

    # 2. Check Codex global MCP bloat
    cx_mcps = snapshot.get("ides", {}).get("codex", {}).get("mcps", {})
    cx_heavy_on = [
        k for k, v in cx_mcps.items()
        if v.get("enabled") and k not in ("computer-use", "node_repl")
    ]
    if cx_heavy_on:
        score -= min(25, len(cx_heavy_on) * 8)
        findings.append({
            "severity": "HIGH",
            "category": "Codex Cold-Start & Tokens",
            "title": f"{len(cx_heavy_on)} MCP(s) especializados activos globalmente en Codex",
            "detail": f"Activos en global: {', '.join(cx_heavy_on)}. Desactivarlos en global evita procesos ociosos y latencia de arranque.",
            "action": "restore_codex_core",
            "action_label": "Optimizar Codex a Core Mínimo",
        })
    else:
        findings.append({
            "severity": "OPTIMAL",
            "category": "Codex Core",
            "title": "Codex CLI en estado Core Mínimo óptimo",
            "detail": "Solo node_repl (bundled) y computer-use activos; servidores especializados desactivados globalmente.",
        })

    # 3. Check Spend Guard
    sg = snapshot.get("oac", {}).get("spend_guard", {}).get("state", "UNKNOWN")
    if sg != "DENY":
        score -= 30
        findings.append({
            "severity": "CRITICAL",
            "category": "OAC Spend Guard",
            "title": f"PAYG Spend Guard está en estado '{sg}' (debería ser DENY)",
            "detail": "Revisa config/oac-spend-guard.jsonc y opencode.json para evitar cargos PAYG accidentales.",
        })
    else:
        findings.append({
            "severity": "OPTIMAL",
            "category": "OAC Spend Guard",
            "title": "Barrera PAYG activa (DENY)",
            "detail": "Proveedores facturables bloqueados por política; cero riesgo de fallback de pago automático.",
        })

    # 4. Check Antigravity Custom Agents sync
    ag_agents = snapshot.get("ides", {}).get("antigravity", {}).get("agents_count", 0)
    if ag_agents == 0:
        score -= 10
        findings.append({
            "severity": "MEDIUM",
            "category": "Antigravity Sync",
            "title": "Agentes OAC no sincronizados con Antigravity",
            "detail": "Sincroniza los 4 agentes primarios y 15 subagentes ocultos en ~/.gemini/config/plugins/oac-custom-agents.",
            "action": "sync_antigravity_agents",
            "action_label": "Sincronizar Agentes a Antigravity",
        })
    else:
        findings.append({
            "severity": "OPTIMAL",
            "category": "Antigravity Custom Agents",
            "title": f"{ag_agents} agentes proyectados en Antigravity (4 primarios + 15 subagentes ocultos)",
            "detail": "Plugin oac-custom-agents activo sin saturar el selector principal.",
        })

    # 5. Check OpenCode global skills count
    oc_sk = snapshot.get("skills", {}).get("opencode_global_count", 0)
    if oc_sk > 15:
        score -= 10
        findings.append({
            "severity": "MEDIUM",
            "category": "Contexto de Skills",
            "title": f"{oc_sk} skills globales en OpenCode (objetivo: 5–15)",
            "detail": "Mueve skills especializadas al catálogo frío ~/.agents/catalog/skills/ para reducir tokens de sistema.",
        })
    else:
        findings.append({
            "severity": "OPTIMAL",
            "category": "Contexto de Skills",
            "title": f"Catálogo global compacto ({oc_sk} skills en OpenCode)",
            "detail": "Divulgación progresiva y catálogo frío funcionando correctamente.",
        })

    return {
        "score": max(0, score),
        "grade": "A" if score >= 90 else ("B" if score >= 75 else ("C" if score >= 60 else "D")),
        "findings": findings,
    }


def _check_executable_health(exe: str) -> tuple[str, str]:
    """Verify if an MCP executable exists on disk or in PATH."""
    if not exe:
        return "ok", "Servidor remoto HTTP / URL"
    clean = exe.replace("\\\\?\\", "")
    p = Path(clean)
    if p.is_absolute():
        if p.exists():
            return "ok", f"Binario verificado: {p.name}"
        return "error", f"No existe el binario: {clean}"
    found = shutil.which(clean)
    if found:
        return "ok", f"En PATH: {Path(found).name}"
    return "error", f"Comando no encontrado en PATH: {clean}"


def build_catalog_lists(
    home: Path,
    oc_root: Path,
    cx_root: Path,
    tl_root: Path,
    oc_mcps: dict[str, Any],
    oc_mcps_raw: dict[str, Any],
    codex_mcps: dict[str, Any],
    codex_mcps_raw: dict[str, Any],
    ag_mcps: list[str],
    profiles: dict[str, Any],
    live_procs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build complete MCP and Skill inventory with health status, active IDEs, and paths."""
    reg_path = tl_root / "registry.yaml"
    reg_servers: dict[str, Any] = {}
    if reg_path.exists():
        try:
            reg_servers = (yaml.safe_load(reg_path.read_text(encoding="utf-8-sig")) or {}).get("servers", {})
        except Exception:
            pass

    all_mcp_names = sorted(
        set(oc_mcps.keys()) | set(codex_mcps.keys()) | set(ag_mcps) | set(reg_servers.keys())
    )
    mcps_list: list[dict[str, Any]] = []

    for name in all_mcp_names:
        running_in: list[str] = []
        if oc_mcps.get(name, {}).get("enabled"):
            running_in.append("OpenCode / OpenChamber")
        if codex_mcps.get(name, {}).get("enabled"):
            running_in.append("Codex")
        if name in ag_mcps:
            running_in.append("Antigravity")

        # Resolve executable / command for health check
        exe = ""
        args: list[str] = []
        transport = "stdio"
        explorer_path = str(oc_root / "opencode.json")

        if name in reg_servers and isinstance(reg_servers[name], dict):
            rc = reg_servers[name]
            transport = str(rc.get("transport", "stdio"))
            exe = str(rc.get("executable", ""))
            args = [str(a) for a in rc.get("args", [])]
            explorer_path = str(reg_path)
        elif name in oc_mcps_raw:
            raw_oc = oc_mcps_raw[name]
            cmd_arr = raw_oc.get("command") or []
            if isinstance(cmd_arr, list) and cmd_arr:
                exe = str(cmd_arr[0])
                args = [str(a) for a in cmd_arr[1:]]
            transport = str(raw_oc.get("type", "local"))
            explorer_path = str(oc_root / "opencode.json")
        elif name in codex_mcps_raw:
            raw_cx = codex_mcps_raw[name]
            exe = str(raw_cx.get("command", ""))
            args = [str(a) for a in raw_cx.get("args", [])]
            transport = "http" if raw_cx.get("url") else "stdio"
            explorer_path = str(cx_root / "config.toml")
        elif name in ag_mcps:
            ag_p = home / ".gemini" / "antigravity" / "mcp" / name
            explorer_path = str(ag_p)

        if exe and Path(exe.replace("\\\\?\\", "")).exists():
            explorer_path = str(Path(exe.replace("\\\\?\\", "")))

        health, health_detail = ("ok", "Esquema MCP en Antigravity") if (name in ag_mcps and not exe) else _check_executable_health(exe)
        used_in_profiles = [pname for pname, pdata in profiles.items() if name in (pdata.get("mcp_servers") or [])]

        # Match live process RAM if running
        live_ram = 0.0
        for lp in live_procs:
            pname_low = lp["process"].lower()
            if name.lower().replace("-mcp", "") in pname_low or (name == "node_repl" and "node_repl" in pname_low):
                live_ram = lp["ram_mb"]
                break

        load_info = RESOURCE_LOAD_CATALOG.get(name, {"level": "LOW", "ram": "Bajo", "tokens": "Bajo", "note": ""})
        mcps_list.append({
            "id": name,
            "kind": "mcp",
            "transport": transport,
            "executable": exe,
            "args": args,
            "explorer_path": explorer_path,
            "health": health,
            "health_detail": health_detail,
            "is_loaded": len(running_in) > 0 or live_ram > 0,
            "running_in": running_in,
            "live_ram_mb": live_ram,
            "profiles": used_in_profiles,
            "load_level": load_info["level"],
            "ram_est": load_info["ram"],
            "tokens_est": load_info["tokens"],
            "note": load_info["note"],
            "bundled": name == "node_repl",
        })

    # Build Skills list across shared (~/.agents/skills), opencode, codex, and cold catalog
    shared_dir = home / ".agents" / "skills"
    oc_sk_dir = oc_root / "skills"
    cx_sk_dir = cx_root / "skills"
    cold_dir = home / ".agents" / "catalog" / "skills"

    skill_sources: dict[str, dict[str, Any]] = {}
    for label, sdir, is_active, ides_where in [
        ("shared", shared_dir, True, ["Antigravity", "OpenCode", "Codex", "Copilot", "Claude Code"]),
        ("opencode", oc_sk_dir, True, ["OpenCode / OpenChamber"]),
        ("codex", cx_sk_dir, True, ["Codex"]),
        ("cold_catalog", cold_dir, False, ["Catálogo Frío"]),
    ]:
        if not sdir.exists():
            continue
        for entry in sorted(sdir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            sk_md = entry / "SKILL.md"
            rec = skill_sources.get(entry.name)
            if not rec:
                desc = ""
                health = "ok"
                health_detail = "SKILL.md válido"
                if not sk_md.exists():
                    health = "error"
                    health_detail = "Falta archivo SKILL.md"
                else:
                    try:
                        txt = sk_md.read_text(encoding="utf-8-sig", errors="replace")
                        if not txt.strip():
                            health = "error"
                            health_detail = "SKILL.md está vacío"
                        else:
                            m = FRONTMATTER_RE.match(txt)
                            if m:
                                fm = yaml.safe_load(m.group(1)) or {}
                                desc = str(fm.get("description", "")).strip()[:180]
                            else:
                                desc = txt.strip().splitlines()[0][:160]
                    except Exception as exc:
                        health = "error"
                        health_detail = f"Frontmatter YAML inválido: {exc}"

                used_profs = [pname for pname, pdata in profiles.items() if entry.name in (pdata.get("skills") or [])]
                skill_sources[entry.name] = {
                    "id": entry.name,
                    "kind": "skill",
                    "description": desc or f"Skill {entry.name}",
                    "scope": label,
                    "path": str(sk_md if sk_md.exists() else entry),
                    "folder_path": str(entry),
                    "health": health,
                    "health_detail": health_detail,
                    "is_loaded": is_active and health == "ok",
                    "running_in": list(ides_where),
                    "profiles": used_profs,
                }
            else:
                for ide_lbl in ides_where:
                    if ide_lbl not in rec["running_in"] and ide_lbl != "Catálogo Frío":
                        rec["running_in"].append(ide_lbl)

    skills_list = sorted(
        skill_sources.values(),
        key=lambda x: (x["health"] != "error", not x["is_loaded"], x["id"]),
    )

    # Build Plugins list across OpenCode (declared + local), Codex, and Antigravity
    plugins_list: list[dict[str, Any]] = []
    oc_json_p = oc_root / "opencode.json"
    if oc_json_p.exists():
        try:
            oc_d = json.loads(oc_json_p.read_text(encoding="utf-8-sig"))
            for p_entry in oc_d.get("plugins", []):
                p_str = str(p_entry)
                p_name = p_str.split("/")[-1] if p_str.startswith("file://") else p_str
                p_path = p_str.replace("file:///", "").replace("%20", " ") if p_str.startswith("file://") else str(oc_json_p)
                exists = Path(p_path).exists()
                plugins_list.append({
                    "id": p_name,
                    "kind": "plugin",
                    "source": "opencode.json (declared)",
                    "path": p_path,
                    "explorer_path": p_path,
                    "health": "ok" if exists else "error",
                    "health_detail": "Plugin declarado verificado" if exists else f"Ruta no encontrada: {p_path}",
                    "is_loaded": True,
                    "running_in": ["OpenCode / OpenChamber"],
                })
        except Exception:
            pass

    oc_pdir = oc_root / "plugins"
    if oc_pdir.exists():
        for p in sorted(oc_pdir.iterdir()):
            plugins_list.append({
                "id": p.name,
                "kind": "plugin",
                "source": "~/.config/opencode/plugins",
                "path": str(p),
                "explorer_path": str(p),
                "health": "ok",
                "health_detail": "Plugin local en directorio de descubrimiento",
                "is_loaded": True,
                "running_in": ["OpenCode / OpenChamber"],
            })

    cx_toml_p = cx_root / "config.toml"
    if cx_toml_p.exists():
        try:
            cx_d = tomllib.loads(cx_toml_p.read_text(encoding="utf-8-sig"))
            for pk, pv in sorted(cx_d.get("plugins", {}).items()):
                en = bool(pv.get("enabled", False)) if isinstance(pv, dict) else False
                plugins_list.append({
                    "id": pk,
                    "kind": "plugin",
                    "source": "~/.codex/config.toml",
                    "path": str(cx_toml_p),
                    "explorer_path": str(cx_toml_p),
                    "health": "ok",
                    "health_detail": "Plugin nativo/registrado en Codex",
                    "is_loaded": en,
                    "running_in": ["Codex"] if en else [],
                })
        except Exception:
            pass

    ag_pdir = home / ".gemini" / "config" / "plugins"
    if ag_pdir.exists():
        for p in sorted(ag_pdir.iterdir()):
            if not p.is_dir():
                continue
            pjson = p / "plugin.json"
            plugins_list.append({
                "id": p.name,
                "kind": "plugin",
                "source": "~/.gemini/config/plugins",
                "path": str(pjson if pjson.exists() else p),
                "explorer_path": str(pjson if pjson.exists() else p),
                "health": "ok" if pjson.exists() else "error",
                "health_detail": "Bundle Antigravity con plugin.json" if pjson.exists() else "Falta plugin.json",
                "is_loaded": pjson.exists(),
                "running_in": ["Antigravity"] if pjson.exists() else [],
            })

    # Hygiene / Duplicates summary
    dup_skills = [s["id"] for s in skills_list if len(s["running_in"]) > 1 and "OpenCode / OpenChamber" in s["running_in"]]
    return {
        "mcps": mcps_list,
        "skills": skills_list,
        "plugins": plugins_list,
        "hygiene": {
            "duplicate_skills_count": len(dup_skills),
            "duplicate_skills_sample": dup_skills[:25],
            "cold_catalog_count": sum(1 for s in skills_list if s["scope"] == "cold_catalog"),
            "errors_count": sum(1 for s in skills_list if s["health"] == "error") + sum(1 for m in mcps_list if m["health"] == "error"),
        },
    }


def get_resource_info(kind: str, res_id: str, tooling_root: Path | None = None) -> dict[str, Any]:
    """Return full details and editable text content for a skill or MCP."""
    snap = load_oac_snapshot(tooling_root=tooling_root)
    cat = snap.get("catalog", {})
    if kind == "skill":
        item = next((s for s in cat.get("skills", []) if s["id"] == res_id), None)
        if not item:
            raise FileNotFoundError(f"Skill no encontrada: {res_id}")
        p = Path(item["path"])
        content = p.read_text(encoding="utf-8-sig", errors="replace") if (p.exists() and p.is_file()) else ""
        return {"item": item, "content": content}

    if kind == "mcp":
        item = next((m for m in cat.get("mcps", []) if m["id"] == res_id), None)
        if not item:
            raise FileNotFoundError(f"MCP no encontrado: {res_id}")
        editable_obj = {
            "executable": item["executable"],
            "args": item["args"],
            "transport": item["transport"],
            "opencode_enabled": "OpenCode / OpenChamber" in item["running_in"],
            "codex_enabled": "Codex" in item["running_in"],
        }
        return {"item": item, "content": yaml.safe_dump(editable_obj, sort_keys=False, allow_unicode=True)}

    if kind == "plugin":
        item = next((p for p in cat.get("plugins", []) if p["id"] == res_id), None)
        if not item:
            raise FileNotFoundError(f"Plugin no encontrado: {res_id}")
        p = Path(item["path"])
        content = p.read_text(encoding="utf-8-sig", errors="replace") if (p.exists() and p.is_file()) else json.dumps(item, indent=2, ensure_ascii=False)
        return {"item": item, "content": content}

    raise ValueError(f"Tipo inválido: {kind}")


def edit_resource(kind: str, res_id: str, content: str, tooling_root: Path | None = None) -> dict[str, Any]:
    """Save edited SKILL.md or MCP YAML definition with automatic SHA-256 backup."""
    home = Path.home()
    tl_root = tooling_root or (home / ".agents" / "tooling")
    info = get_resource_info(kind, res_id, tooling_root=tl_root)["item"]

    if kind == "skill":
        target = Path(info["path"])
        if target.is_dir():
            target = target / "SKILL.md"
        change_id, pre_hash = _backup_file(target, f"ui-edit-skill-{res_id}") if target.exists() else ("chg-new", "")
        m = FRONTMATTER_RE.match(content)
        if m:
            yaml.safe_load(m.group(1))  # Validate frontmatter YAML before saving
        tmp = target.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
        return {"change_id": change_id, "sha256_before": pre_hash, "target": str(target)}

    if kind == "mcp":
        parsed = yaml.safe_load(content) or {}
        reg_path = tl_root / "registry.yaml"
        change_id = "chg-mcp-edit"
        if reg_path.exists():
            change_id, _ = _backup_file(reg_path, f"ui-edit-mcp-{res_id}")
            reg_data = yaml.safe_load(reg_path.read_text(encoding="utf-8-sig")) or {}
            servers = reg_data.setdefault("servers", {})
            entry = servers.setdefault(res_id, {})
            if "executable" in parsed:
                entry["executable"] = str(parsed["executable"])
            if "args" in parsed and isinstance(parsed["args"], list):
                entry["args"] = [str(a) for a in parsed["args"]]
            if "transport" in parsed:
                entry["transport"] = str(parsed["transport"])
            tmp = reg_path.with_suffix(".yaml.tmp")
            tmp.write_text(yaml.safe_dump(reg_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
            tmp.replace(reg_path)

        if "opencode_enabled" in parsed and res_id in (load_oac_snapshot(tooling_root=tl_root)["mcps"]["opencode"]):
            save_ide_mcps("opencode", {res_id: bool(parsed["opencode_enabled"])})
        if "codex_enabled" in parsed and res_id != "node_repl" and res_id in (load_oac_snapshot(tooling_root=tl_root)["mcps"]["codex"]):
            save_ide_mcps("codex", {res_id: bool(parsed["codex_enabled"])})
        return {"change_id": change_id, "target": str(reg_path)}

    raise ValueError(f"Tipo inválido: {kind}")


def open_in_explorer(kind: str, res_id: str, tooling_root: Path | None = None) -> dict[str, Any]:
    """Open Windows Explorer selecting the skill's SKILL.md or MCP binary/config."""
    info = get_resource_info(kind, res_id, tooling_root=tooling_root)["item"]
    raw_path = info.get("path") if kind == "skill" else info.get("explorer_path")
    target = Path(str(raw_path)).resolve()
    if not target.exists():
        target = target.parent
    subprocess.Popen(["explorer.exe", f"/select,{target}"])
    return {"opened": str(target)}


def delete_or_archive_resource(kind: str, res_id: str, tooling_root: Path | None = None) -> dict[str, Any]:
    """Safely archive a skill to private backup folder or disable/archive an MCP (never permanently destroys bytes)."""
    home = Path.home()
    tl_root = tooling_root or (home / ".agents" / "tooling")
    local_app = Path(os.environ.get("LOCALAPPDATA", home / ".local" / "share"))
    change_id = f"chg-{datetime.now().strftime('%Y%m%d-%H%M%S')}-archive-{kind}-{res_id}"
    bdir = local_app / "agent-tooling-backups" / change_id
    bdir.mkdir(parents=True, exist_ok=True)

    info = get_resource_info(kind, res_id, tooling_root=tl_root)["item"]
    if kind == "skill":
        folder = Path(info["folder_path"])
        if not folder.exists():
            raise FileNotFoundError(f"Carpeta no existe: {folder}")
        dest_bak = bdir / folder.name
        shutil.copytree(folder, dest_bak, dirs_exist_ok=True)
        (bdir / "manifest.json").write_text(
            json.dumps([{"SkillName": res_id, "OriginalPath": str(folder), "BackupPath": str(dest_bak)}], indent=2),
            encoding="utf-8",
        )
        shutil.rmtree(folder)
        return {"change_id": change_id, "archived_from": str(folder), "backup": str(dest_bak)}

    if kind == "mcp":
        if res_id == "node_repl":
            raise ValueError("node_repl es una herramienta nativa bundled de Codex y no debe eliminarse.")
        snap = load_oac_snapshot(tooling_root=tl_root)
        if res_id in snap["mcps"]["opencode"]:
            save_ide_mcps("opencode", {res_id: False})
        if res_id in snap["mcps"]["codex"]:
            save_ide_mcps("codex", {res_id: False})
        return {"change_id": change_id, "disabled_mcp": res_id}

    raise ValueError(f"Tipo inválido: {kind}")


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def vercel_find_skills(query: str) -> list[dict[str, str]]:
    """Search Vercel skills registry via `npx -y skills find <query>`."""
    q = query.strip()
    if not q:
        return []
    res = subprocess.run(
        ["cmd", "/c", "npx", "-y", "skills", "find", q],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    clean = ANSI_RE.sub("", res.stdout or "")
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    results: list[dict[str, str]] = []
    for i, ln in enumerate(lines):
        m = re.match(r"^([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+)\s+(.+?installs?)$", ln)
        if m:
            url = ""
            if i + 1 < len(lines) and "https://" in lines[i + 1]:
                url = lines[i + 1].split("https://", 1)[1].strip()
                url = "https://" + url
            results.append({"package": m.group(1), "installs": m.group(2), "url": url})
    return results
