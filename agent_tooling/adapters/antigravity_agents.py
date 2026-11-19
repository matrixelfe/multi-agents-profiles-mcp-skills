"""Sync OpenCode/OAC agents into a clean Antigravity plugin bundle (~/.gemini/config/plugins/oac-custom-agents).

Only the 4 primary agents (auto-orchestrator, ask, openagent, opencoder) are exposed in the
main agent selector (mainAgent: true, subagent: false). All 15 subagents stay hidden from the
main selector (mainAgent: false, subagent: true) to avoid cluttering the UI dropdown.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", re.DOTALL)

PRIMARY_IDS = {"auto-orchestrator", "ask", "openagent", "opencoder"}
READ_ONLY_SUBAGENTS = {"code-explorer", "contextscout", "externalscout", "reviewer", "context-organizer"}
QA_SUBAGENTS = {"code-qa"}

FULL_TOOLS = ["read_file", "edit_file", "write_file", "run_command", "manage_task", "search_web"]
ORCHESTRATOR_TOOLS = ["read_file", "invoke_subagent", "send_message", "manage_subagents", "ask_question"]
PRIMARY_DEV_TOOLS = FULL_TOOLS + ["invoke_subagent", "send_message", "manage_subagents"]
READ_ONLY_TOOLS = ["read_file", "search_web"]
QA_TOOLS = ["read_file", "run_command", "manage_task"]


def _choose_tools(agent_id: str, is_primary: bool) -> list[str]:
    if agent_id == "auto-orchestrator":
        return ORCHESTRATOR_TOOLS
    if agent_id == "ask":
        return READ_ONLY_TOOLS
    if is_primary:
        return PRIMARY_DEV_TOOLS
    if agent_id in READ_ONLY_SUBAGENTS:
        return READ_ONLY_TOOLS
    if agent_id in QA_SUBAGENTS:
        return QA_TOOLS
    return FULL_TOOLS


def convert_agent_to_antigravity(md_path: Path) -> tuple[str, str, bool]:
    """Convert an OpenCode/OAC agent markdown file to Antigravity custom agent format.

    Returns (agent_id, converted_markdown, is_primary).
    """
    raw = md_path.read_text(encoding="utf-8-sig", errors="replace")
    agent_id = md_path.stem
    fm: dict[str, Any] = {}
    body = raw

    m = FRONTMATTER_RE.match(raw)
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            fm = {}
        body = raw[m.end() :]

    desc = str(fm.get("description") or f"OAC/OpenCode agent: {agent_id}").strip()
    is_primary = agent_id in PRIMARY_IDS
    tools = _choose_tools(agent_id, is_primary)

    ag_fm = {
        "name": agent_id,
        "description": desc,
        "mainAgent": is_primary,
        "subagent": not is_primary,
        "tools": tools,
    }
    fm_yaml = yaml.safe_dump(ag_fm, sort_keys=False, allow_unicode=True).strip()
    converted = f"---\n{fm_yaml}\n---\n\n{body.lstrip()}"
    return agent_id, converted, is_primary


def sync_antigravity_agents(
    opencode_root: Path | None = None,
    plugin_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate ~/.gemini/config/plugins/oac-custom-agents/ from ~/.config/opencode/agent(s)."""
    home = Path.home()
    oc_root = opencode_root or (home / ".config" / "opencode")
    pl_root = plugin_root or (home / ".gemini" / "config" / "plugins" / "oac-custom-agents")
    agents_out = pl_root / "agents"

    primaries: list[str] = []
    subagents: list[str] = []
    files_to_write: dict[Path, str] = {}

    for sub in ("agent", "agents"):
        d = oc_root / sub
        if not d.exists():
            continue
        for md in sorted(d.rglob("*.md")):
            agent_id, content, is_primary = convert_agent_to_antigravity(md)
            if is_primary:
                primaries.append(agent_id)
            else:
                subagents.append(agent_id)
            files_to_write[agents_out / f"{agent_id}.md"] = content

    plugin_json = {
        "name": "oac-custom-agents",
        "description": "OAC & OpenChamber custom agents (4 primary agents in selector + 15 background subagents).",
    }

    if not dry_run:
        agents_out.mkdir(parents=True, exist_ok=True)
        (pl_root / "plugin.json").write_text(
            json.dumps(plugin_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        for path, content in files_to_write.items():
            path.write_text(content, encoding="utf-8")

    return {
        "plugin_root": str(pl_root),
        "dry_run": dry_run,
        "primary_agents": sorted(primaries),
        "subagents": sorted(subagents),
        "total": len(primaries) + len(subagents),
    }
