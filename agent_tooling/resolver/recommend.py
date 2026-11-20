"""Deterministic, zero-LLM contextual recommender for ECC skills and subagents."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# Deterministic task signal detectors (no LLM calls)
TASK_SIGNALS: dict[str, re.Pattern[str]] = {
    "missing_codebase_context": re.compile(r"\b(explore|find|where|search|unknown|locate|context|codebase|repo)\b", re.I),
    "complex_orchestrated_task": re.compile(r"\b(architect|refactor|migrate|multi|plan|orchestrat|phase|design|system)\b", re.I),
    "research_before_implementation": re.compile(r"\b(implement|build|add|create|integrate|library|package|api)\b", re.I),
    "repeated_failure_no_progress": re.compile(r"\b(loop|retry|stuck|failing|still fails|debug|crash|error|bug)\b", re.I),
    "code_review_or_qa": re.compile(r"\b(review|audit|qa|verify|regression|test|security|check)\b", re.I),
    "frontend_ui": re.compile(r"\b(ui|frontend|react|css|component|browser|layout|vite|html)\b", re.I),
    "gamedev_cpp": re.compile(r"\b(game|cpp|c\+\+|directx|renderdoc|pix|shader|fps|recomp|stutter|cmake)\b", re.I),
    "reverse_engineering": re.compile(r"\b(reverse|binary|decompile|apk|jadx|xex|disassemble|ghidra|frida)\b", re.I),
    "browser_navigation_or_interaction": re.compile(r"\b(navigate|navegar|browse|open\s+url|webpage|página|formulario|form|click|fill|scrape\s+dynamic|dinámic[oa]|snapshot|agent-browser)\b", re.I),
    "browser_devtools_debug": re.compile(r"\b(console\s+error|errores?\s+de\s+consola|network\s+traffic|tráfico\s+http|devtools|lighthouse|web\s+performance|rendimiento\s+web|har)\b", re.I),
    "browser_e2e_suite": re.compile(r"\b(e2e|playwright\s+test|regresiones?\s+automatizadas|automated\s+regression)\b", re.I),
}

# Client surface capability matrix for skills & delegation
SURFACE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "opencode:local": {"skills": True, "delegation": True, "status": "SUPPORTED"},
    "openchamber:opencode-runtime": {"skills": True, "delegation": True, "status": "SUPPORTED"},
    "codex:local": {"skills": True, "delegation": False, "status": "SUPPORTED"},
    "claude:code-local": {"skills": True, "delegation": True, "status": "SUPPORTED"},
    "claude:chat": {"skills": False, "delegation": False, "status": "MANUAL_ONLY"},
    "claude:cowork": {"skills": False, "delegation": False, "status": "MANUAL_ONLY"},
    "claude:code-cloud": {"skills": False, "delegation": False, "status": "UNSUPPORTED"},
    "antigravity:app": {"skills": True, "delegation": True, "status": "SUPPORTED"},
    "antigravity:ide": {"skills": True, "delegation": True, "status": "SUPPORTED"},
    "antigravity:cli": {"skills": True, "delegation": True, "status": "SUPPORTED"},
}


def load_recommendations_policy(tooling_root: Path) -> dict[str, Any]:
    path = tooling_root / "recommendations.yaml"
    if not path.exists():
        return {"schema_version": 1, "agent_skill_recommendations": {"defaults": {}, "agents": {}}}
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def detect_signals(task: str) -> list[str]:
    if not task or not task.strip():
        return []
    return [name for name, pat in TASK_SIGNALS.items() if pat.search(task)]


def recommend(
    agent_id: str,
    task: str,
    client_target: str = "openchamber:opencode-runtime",
    project_profile: str = "core",
    tooling_root: Path | None = None,
    skills_root: Path | None = None,
    agent_permissions: dict[str, Any] | None = None,
    max_skills: int = 3,
    max_subagents: int = 2,
) -> dict[str, Any]:
    """Produce deterministic, explainable skill & subagent recommendations (0 LLM calls)."""
    home = Path.home()
    tl_root = tooling_root or (home / ".agents" / "tooling")
    sk_root = skills_root or (home / ".agents" / "skills")
    policy = load_recommendations_policy(tl_root)
    cfg = policy.get("agent_skill_recommendations", {})
    defaults = cfg.get("defaults", {})
    agents_cfg = cfg.get("agents", {})

    surface = SURFACE_CAPABILITIES.get(
        client_target, {"skills": False, "delegation": False, "status": "UNKNOWN"}
    )
    signals = detect_signals(task)

    # T01: Simple question in read-only 'ask' agent -> do not inject irrelevant editing/dev skills
    if agent_id in ("ask", "agent/ask.md") and not any(
        s in signals for s in ("missing_codebase_context", "code_review_or_qa")
    ):
        return {
            "agent": agent_id,
            "client_target": client_target,
            "surface_status": surface["status"],
            "project_profile": project_profile,
            "signals_detected": signals,
            "skills": [],
            "subagents": [],
            "note": "Simple query in read-only agent; zero skills injected to preserve minimal context.",
        }

    # Resolve agent rule entry (support both short name and rel path)
    norm_id = agent_id.replace("\\", "/")
    agent_rule = agents_cfg.get(norm_id) or agents_cfg.get(Path(norm_id).stem) or {}
    candidates = list(agent_rule.get("recommended", []))

    # Add profile-aware contextual suggestions (without overriding core/empty repo)
    if project_profile == "web" and "frontend_ui" in signals:
        candidates.append({"resource": "frontend-ui-engineering", "when": "frontend_ui", "policy": "RECOMMENDED"})
    if project_profile == "gamedev" and "gamedev_cpp" in signals:
        candidates.append({"resource": "gamedev-performance", "when": "gamedev_cpp", "policy": "RECOMMENDED"})
    if project_profile == "reverse" and "reverse_engineering" in signals:
        candidates.append({"resource": "reverse-engineer-anything", "when": "reverse_engineering", "policy": "RECOMMENDED"})
    if "code_review_or_qa" in signals:
        candidates.append({"resource": "security-review", "when": "code_review_or_qa", "policy": "RECOMMENDED"})
    # Intelligent browser-automation routing & escalation
    if "browser_devtools_debug" in signals:
        candidates.insert(0, {"resource": "browser-testing-with-devtools", "when": "browser_devtools_debug", "policy": "RECOMMENDED"})
    elif "browser_e2e_suite" in signals:
        candidates.insert(0, {"resource": "e2e-testing", "when": "browser_e2e_suite", "policy": "RECOMMENDED"})
    elif "browser_navigation_or_interaction" in signals:
        candidates.insert(0, {"resource": "agent-browser", "when": "browser_navigation_or_interaction", "policy": "RECOMMENDED"})

    # Deduplicate and evaluate each skill candidate
    seen: set[str] = set()
    skill_results: list[dict[str, Any]] = []
    for item in candidates:
        res_id = str(item.get("resource", ""))
        if not res_id or res_id in seen:
            continue
        seen.add(res_id)

        when = str(item.get("when", "always"))
        matched = (when == "always") or (when in signals)
        if not matched and signals:
            continue

        # Check physical availability in ~/.agents/skills/<name>/SKILL.md or catalog
        skill_name = res_id.split("/")[-1]
        in_shared = (sk_root / skill_name / "SKILL.md").exists()
        in_catalog = (home / ".agents" / "catalog" / "skills" / skill_name / "SKILL.md").exists()
        available = in_shared or in_catalog

        compatible = bool(surface["skills"])
        decision = str(item.get("policy", "RECOMMENDED")).upper()
        permission = "allow"

        if not compatible:
            decision = "BLOCKED"
            permission = "unsupported_surface"
        elif not available:
            decision = "OPTIONAL" if defaults.get("auto_install") is False else decision
            permission = "install_required"

        skill_results.append({
            "resource_id": res_id,
            "kind": "skill",
            "target_agent": agent_id,
            "client_target": client_target,
            "project_profile": project_profile,
            "decision": decision,
            "reason_code": when,
            "available": available,
            "compatible": compatible,
            "permission": permission,
            "confidence": "high" if matched else "medium",
            "load_now": False,
        })

    # Rank: compatible & available & matched first
    skill_results.sort(key=lambda x: (not x["compatible"], not x["available"], x["decision"] == "BLOCKED"))
    skill_results = skill_results[:max_skills]

    # Evaluate subagent recommendations respecting real allowlists!
    allowed_subagents: list[str] = []
    if agent_permissions and isinstance(agent_permissions.get("allowed_subagents"), list):
        allowed_subagents = list(agent_permissions["allowed_subagents"])
    elif isinstance(agent_rule.get("allowed_subagents"), list):
        allowed_subagents = list(agent_rule["allowed_subagents"])

    subagent_candidates: list[tuple[str, str]] = []
    if "missing_codebase_context" in signals:
        subagent_candidates.append(("code-explorer", "missing_codebase_context"))
    if "code_review_or_qa" in signals:
        subagent_candidates.append(("code-qa", "code_review_or_qa"))
    if "research_before_implementation" in signals or "repeated_failure_no_progress" in signals:
        subagent_candidates.append(("code-implementer", "implementation_or_fix"))
    if "complex_orchestrated_task" in signals or "gamedev_cpp" in signals:
        subagent_candidates.append(("code-specialist", "complex_domain_investigation"))

    subagent_results: list[dict[str, Any]] = []
    seen_sa: set[str] = set()
    for sa, reason in subagent_candidates:
        if sa in seen_sa:
            continue
        seen_sa.add(sa)
        inv_allowed = bool(surface["delegation"]) and (sa in allowed_subagents)
        subagent_results.append({
            "recommended_agent": sa,
            "reason_code": reason,
            "invocation_allowed": inv_allowed,
            "decision": "RECOMMENDED" if inv_allowed else "BLOCKED",
        })

    return {
        "agent": agent_id,
        "client_target": client_target,
        "surface_status": surface["status"],
        "project_profile": project_profile,
        "signals_detected": signals,
        "skills": skill_results,
        "subagents": subagent_results[:max_subagents],
    }
