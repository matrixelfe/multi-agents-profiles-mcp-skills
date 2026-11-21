"""Token Savers & Context Optimization Inspector.

Audits every token-saving tool, plugin, hook, and skill across all 5 harnesses
(OpenCode/OpenChamber, Google Antigravity, Codex CLI, Claude Code, GitHub Copilot)
and provides curated recommendations for additional token optimizers.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from agent_tooling.profile_switcher import get_active_profile_state


_VERSION_CACHE: dict[str, str] = {}
_NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def _get_cmd_version(cmd: list[str], cache_key: str) -> str:
    if cache_key in _VERSION_CACHE:
        return _VERSION_CACHE[cache_key]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2.5,
            encoding="utf-8",
            errors="replace",
            creationflags=_NO_WIN,
        )
        out = (proc.stdout or proc.stderr or "").strip().splitlines()
        val = out[0][:60] if out else "instalado"
    except Exception:
        val = "instalado"
    _VERSION_CACHE[cache_key] = val
    return val


def _read_npm_pkg_version(pkg_name: str) -> str:
    """Fast 0ms version check from global npm node_modules without spawning node."""
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        pj = Path(appdata) / "npm" / "node_modules" / pkg_name / "package.json"
        if pj.exists():
            try:
                return f"{pkg_name} {json.loads(pj.read_text(encoding='utf-8-sig')).get('version', '')}".strip()
            except Exception:
                pass
    return ""


def _read_text_safe(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def inspect_token_savers(home: Path | None = None) -> dict[str, Any]:
    home = home or Path.home()

    oc_json_txt = _read_text_safe(home / ".config" / "opencode" / "opencode.json")
    cx_toml_txt = _read_text_safe(home / ".codex" / "config.toml")
    cl_settings_txt = _read_text_safe(home / ".claude" / "settings.json")
    cl_json_txt = _read_text_safe(home / ".claude.json")
    ag_mcp_txt = _read_text_safe(home / ".gemini" / "config" / "mcp_config.json")
    cp_mcp_txt = _read_text_safe(home / ".copilot" / "mcp-config.json")

    hot_dir = home / ".agents" / "skills"
    cold_dir = home / ".agents" / "catalog" / "skills"
    ap_state = get_active_profile_state(home)

    def _skill_present(name: str) -> bool:
        return (hot_dir / name).exists() or (cold_dir / name).exists()

    installed: list[dict[str, Any]] = []

    # 1. NTFS Junction Farm + Cold Vault (our native profile switcher)
    active_cnt = ap_state.get("active_skills_count", 0)
    total_cnt = ap_state.get("catalog_skills_count", 0)
    reduction_pct = round((1 - (active_cnt / max(total_cnt, 1))) * 100) if total_cnt else 0
    is_trimmed = ap_state.get("active_profile", "all") != "all" and reduction_pct > 20
    installed.append({
        "id": "profile-junction-farm",
        "name": "Bóveda Fría + Perfil Activo (NTFS Junctions)",
        "category": "Metadatos de Skills",
        "active": is_trimmed,
        "health": "ok" if is_trimmed else "warn",
        "health_detail": f"Perfil '{ap_state.get('active_profile')}' ({active_cnt}/{total_cnt} skills, -{max(0, reduction_pct)}% tokens)"
        if is_trimmed
        else f"Perfil 'all' activo ({active_cnt} skills cargadas; cambia a 'core' para ahorrar ~93%)",
        "version": "v3.3.0",
        "update_status": "Al día",
        "harnesses": ["OpenCode / OpenChamber", "Antigravity", "Codex", "GitHub Copilot", "Claude Code"],
        "estimated_saving": f"-{max(0, reduction_pct)}% contexto inicial",
    })

    # 2. RTK (Rust Token Killer)
    rtk_bin = shutil.which("rtk")
    rtk_ver = _get_cmd_version([rtk_bin, "--version"], "rtk") if rtk_bin else ""
    rtk_harnesses = []
    if (home / ".gemini" / "config" / "plugins" / "rtk").exists():
        rtk_harnesses.append("Antigravity")
    if "rtk hook claude" in cl_settings_txt:
        rtk_harnesses.append("Claude Code")
    if rtk_bin:
        rtk_harnesses.append("CLI Global")
    installed.append({
        "id": "rtk",
        "name": "RTK (Rust Token Killer)",
        "category": "Compresión de salida CLI",
        "active": bool(rtk_bin and rtk_harnesses),
        "health": "ok" if rtk_bin else "error",
        "health_detail": "Condensa salidas de git, pytest y terminal eliminando ruido" if rtk_bin else "Binario rtk no encontrado en PATH",
        "version": rtk_ver or "N/A",
        "update_status": "Al día" if rtk_ver else "Instalar",
        "harnesses": rtk_harnesses,
        "estimated_saving": "60%–85% en logs CLI",
    })

    # 3. context-mode
    cm_harnesses = []
    if "context-mode" in oc_json_txt:
        cm_harnesses.append("OpenCode / OpenChamber")
    if "context-mode" in cx_toml_txt:
        cm_harnesses.append("Codex")
    if "context-mode" in cl_settings_txt:
        cm_harnesses.append("Claude Code")
    installed.append({
        "id": "context-mode",
        "name": "Context-Mode",
        "category": "Cache y compactación de contexto",
        "active": bool(cm_harnesses),
        "health": "ok" if cm_harnesses else "warn",
        "health_detail": "Plugin @latest activo con cache-heal en Claude y OpenCode" if cm_harnesses else "No detectado en clientes activos",
        "version": "@latest",
        "update_status": "Auto (@latest)",
        "harnesses": cm_harnesses,
        "estimated_saving": "40%–70% en sesiones largas",
    })

    # 4. Dynamic Context Pruning (@tarquinen/opencode-dcp)
    dcp_active = "opencode-dcp" in oc_json_txt
    installed.append({
        "id": "opencode-dcp",
        "name": "Dynamic Context Pruning (opencode-dcp)",
        "category": "Poda dinámica de historial",
        "active": dcp_active,
        "health": "ok" if dcp_active else "warn",
        "health_detail": "Poda automáticamente respuestas antiguas y redundantes en OpenCode" if dcp_active else "Inactivo en opencode.json",
        "version": "@latest",
        "update_status": "Auto (@latest)",
        "harnesses": ["OpenCode / OpenChamber"] if dcp_active else [],
        "estimated_saving": "30%–55% en hilos largos",
    })

    # 5. Agent Browser (Vercel Labs)
    ab_bin = shutil.which("agent-browser")
    ab_ver = _read_npm_pkg_version("agent-browser") or ("instalado" if ab_bin else "")
    ab_active = bool(ab_bin and _skill_present("agent-browser"))
    installed.append({
        "id": "agent-browser",
        "name": "Agent Browser (Vercel Labs)",
        "category": "Snapshots web compactos",
        "active": ab_active,
        "health": "ok" if ab_active else "warn",
        "health_detail": "Usa snapshot -i en lugar de enviar DOM completo o screenshots continuos" if ab_active else "Falta CLI o skill agent-browser",
        "version": ab_ver or "N/A",
        "update_status": "Al día" if ab_ver else "Instalar",
        "harnesses": ["OpenCode / OpenChamber", "Antigravity", "Codex", "GitHub Copilot", "Claude Code"] if ab_active else [],
        "estimated_saving": "70%–90% vs DOM/Playwright MCP",
    })

    # 6. CodeGraph (AST-only code reads)
    cg_bin = shutil.which("codegraph")
    cg_harnesses = []
    if "codegraph" in oc_json_txt:
        cg_harnesses.append("OpenCode / OpenChamber")
    if "codegraph" in cx_toml_txt:
        cg_harnesses.append("Codex")
    if "codegraph" in ag_mcp_txt:
        cg_harnesses.append("Antigravity")
    if "codegraph" in cp_mcp_txt:
        cg_harnesses.append("GitHub Copilot")
    if "codegraph" in cl_settings_txt:
        cg_harnesses.append("Claude Code")
    installed.append({
        "id": "codegraph",
        "name": "CodeGraph MCP (Lectura por AST)",
        "category": "Búsqueda semántica / AST",
        "active": bool(cg_bin and cg_harnesses),
        "health": "ok" if cg_bin else "error",
        "health_detail": "Consulta símbolos y grafos de llamadas sin leer archivos enteros" if cg_bin else "codegraph no encontrado en PATH",
        "version": "CLI + MCP",
        "update_status": "Al día",
        "harnesses": cg_harnesses,
        "estimated_saving": "50%–80% en exploración de código",
    })

    # 7. PMB Shared (Cross-IDE persistent memory)
    pmb_harnesses = []
    if "pmb-shared" in oc_json_txt:
        pmb_harnesses.append("OpenCode / OpenChamber")
    if "pmb-shared" in cx_toml_txt:
        pmb_harnesses.append("Codex")
    if "pmb-shared" in ag_mcp_txt:
        pmb_harnesses.append("Antigravity")
    if "pmb-shared" in cp_mcp_txt:
        pmb_harnesses.append("GitHub Copilot")
    if "pmb-shared" in cl_json_txt:
        pmb_harnesses.append("Claude Code")
    installed.append({
        "id": "pmb-shared",
        "name": "PMB Shared Memory",
        "category": "Memoria persistente cross-IDE",
        "active": len(pmb_harnesses) >= 4,
        "health": "ok" if pmb_harnesses else "warn",
        "health_detail": f"Conectado en {len(pmb_harnesses)}/5 harnesses vía stdio (evita re-explicar contexto)",
        "version": "stdio (personal)",
        "update_status": "Al día",
        "harnesses": pmb_harnesses,
        "estimated_saving": "Evita 2k–10k tokens por sesión",
    })

    # 8. Headroom & Code-Mode (OpenCode skills)
    hm_active = (home / ".config" / "opencode" / "skills" / "headroom").exists() or _skill_present("headroom")
    installed.append({
        "id": "headroom",
        "name": "Headroom & Code-Mode",
        "category": "Presupuesto de ventana",
        "active": hm_active,
        "health": "ok" if hm_active else "warn",
        "health_detail": "Control de headroom de contexto y consolidación de tool-calls" if hm_active else "En catálogo frío",
        "version": "Skill local",
        "update_status": "Al día",
        "harnesses": ["OpenCode / OpenChamber"] if hm_active else [],
        "estimated_saving": "15%–30% en tool calls",
    })

    # Suggested additional token savers not yet installed
    suggested: list[dict[str, Any]] = [
        {
            "id": "tokeneconomizer",
            "name": "TokenEconomizer / Token-Budget Guard",
            "category": "Auditoría y límite de tokens",
            "status": "Sugerido",
            "harnesses_compatible": ["OpenCode / OpenChamber", "Claude Code", "Codex", "Antigravity"],
            "benefit": "Analiza qué archivos/reglas disparan el gasto por turno y aplica compresión selectiva.",
            "install_hint": "Buscar en Vercel skills.sh: 'token' o 'context-optimization'",
            "vercel_query": "token",
        },
        {
            "id": "repomix",
            "name": "Repomix (Empaquetado compacto con compresión Tree-sitter)",
            "category": "Resumen de repositorios",
            "status": "Sugerido" if not shutil.which("repomix") else "Instalado en PATH",
            "harnesses_compatible": ["Todos los harnesses (CLI / MCP)"],
            "benefit": "Empaqueta un repositorio eliminando comentarios e implementaciones redundantes (--compress) ahorrando ~70% de tokens.",
            "install_hint": "npx repomix --compress",
            "vercel_query": "repomix",
        },
        {
            "id": "llmlingua-compression",
            "name": "LLMLingua / Prompt Compression",
            "category": "Compresión semántica de prompts",
            "status": "Sugerido",
            "harnesses_compatible": ["OpenCode / OpenChamber", "Pipelines Python"],
            "benefit": "Comprime prompts y documentos largos hasta 5x–10x preservando las entidades clave.",
            "install_hint": "pip install llmlingua",
            "vercel_query": "compression",
        },
        {
            "id": "serena-lsp",
            "name": "Serena MCP (LSP Symbol-Level Editing)",
            "category": "Edición quirúrgica por símbolo",
            "status": "Sugerido",
            "harnesses_compatible": ["Claude Code", "Codex", "OpenCode", "Antigravity"],
            "benefit": "Edita funciones y clases exactas vía LSP sin cargar archivos de 2,000 líneas en contexto.",
            "install_hint": "uvx --from git+https://github.com/oraios/serena serena-mcp-server",
            "vercel_query": "lsp",
        },
    ]

    active_count = 0
    ok_count = 0
    overrides = _load_saver_overrides(home)
    for item in installed:
        if item["id"] in overrides and item["id"] != "profile-junction-farm":
            item["active"] = bool(overrides[item["id"]])
        if item["active"]:
            active_count += 1
        if item["health"] == "ok":
            ok_count += 1

    return {
        "installed": installed,
        "suggested": suggested,
        "summary": {
            "active_count": active_count,
            "total_installed": len(installed),
            "ok_count": ok_count,
            "profile_reduction_pct": max(0, reduction_pct),
            "active_profile": ap_state.get("active_profile", "all"),
        },
    }



def _get_savers_override_file(home: Path) -> Path:
    return home / ".agents" / "tooling" / "state" / "token-savers-state.json"


def _load_saver_overrides(home: Path) -> dict[str, bool]:
    p = _get_savers_override_file(home)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {}


def toggle_token_saver(saver_id: str, enabled: bool, home: Path | None = None) -> dict[str, Any]:
    """Toggle a token saver on or off across config files and persistent state."""
    home = home or Path.home()
    saver_id = (saver_id or "").strip()
    overrides = _load_saver_overrides(home)
    overrides[saver_id] = bool(enabled)
    state_file = _get_savers_override_file(home)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Profile junction farm toggles between 'core' (-93% tokens) and 'all'
    if saver_id == "profile-junction-farm":
        from agent_tooling.profile_switcher import switch_active_profile
        target_prof = "core" if enabled else "all"
        res = switch_active_profile(target_prof, home=home)
        state_file.write_text(json.dumps(overrides, indent=2) + "\n", encoding="utf-8")
        return {"saver_id": saver_id, "enabled": enabled, "detail": f"Perfil cambiado a '{target_prof}' ({res['active_skills_count']} skills)"}

    # 2. OpenCode plugins (context-mode, opencode-dcp)
    oc_path = home / ".config" / "opencode" / "opencode.json"
    if saver_id in ("opencode-dcp", "context-mode") and oc_path.exists():
        try:
            data = json.loads(oc_path.read_text(encoding="utf-8-sig"))
            plugins = list(data.get("plugins") or [])
            pkg = "@tarquinen/opencode-dcp@latest" if saver_id == "opencode-dcp" else "context-mode@latest"
            match_key = "opencode-dcp" if saver_id == "opencode-dcp" else "context-mode"
            plugins = [p for p in plugins if match_key not in str(p)]
            if enabled:
                plugins.append(pkg)
            data["plugins"] = plugins
            oc_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            pass

    # 3. OpenCode MCP servers (codegraph, pmb-shared)
    if saver_id in ("codegraph", "pmb-shared") and oc_path.exists():
        try:
            data = json.loads(oc_path.read_text(encoding="utf-8-sig"))
            srv = data.get("mcp", {}).get("servers", {}).get(saver_id)
            if isinstance(srv, dict):
                srv["enabled"] = bool(enabled)
                oc_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            pass

    state_file.write_text(json.dumps(overrides, indent=2) + "\n", encoding="utf-8")
    return {"saver_id": saver_id, "enabled": bool(enabled), "detail": f"{saver_id} {'activado' if enabled else 'desactivado'}"}
