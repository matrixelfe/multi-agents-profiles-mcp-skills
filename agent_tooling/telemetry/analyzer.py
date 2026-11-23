"""Anomaly detection, zero-secrets sanitization, and audit baseline comparisons."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from agent_tooling.security.redact import redact_text

# Observed Turn-1 ("HOLA") forensic baseline from audit-output/canonical-sessions.csv (2026-11-21)
AUDIT_BASELINE_BY_HARNESS: dict[str, dict[str, Any]] = {
    "opencode": {
        "label": "OpenCode / OpenChamber",
        "baseline_turn1_input": 39514,
        "target_turn1_input": 15000,
        "baseline_calls_turn1": 2,
        "notes": "Build/Plan 2 calls por using-superpowers + triple AGENTS.md + 37 skills",
    },
    "codex": {
        "label": "Codex CLI / App",
        "baseline_turn1_input": 28709,
        "target_turn1_input": 19500,
        "baseline_calls_turn1": 1,
        "notes": "198 skills (63 físicas duplicadas) + doble hook context-mode",
    },
    "cline": {
        "label": "Cline Desktop",
        "baseline_turn1_input": 18754,
        "target_turn1_input": 15200,
        "baseline_calls_turn1": 1,
        "notes": "26 skills + AGENTS.md completo",
    },
    "copilot": {
        "label": "GitHub Copilot Fusion",
        "baseline_turn1_input": 77071,
        "target_turn1_input": 36000,
        "baseline_calls_turn1": 2,
        "notes": "59 tools (24.6K) + rename_session en Call #1 + riesgo de cache break",
    },
    "antigravity": {
        "label": "Google Antigravity",
        "baseline_turn1_input": 18830,
        "target_turn1_input": 15500,
        "baseline_calls_turn1": 1,
        "notes": "Doble AGENTS.md + doble RTK en <user_rules>",
    },
    "zcode": {
        "label": "ZCode Desktop",
        "baseline_turn1_input": 27533,
        "target_turn1_input": 20700,
        "baseline_calls_turn1": 1,
        "notes": "4 plugins Office + node_repl (21 MCP tools, 5.2K tok/call)",
    },
    "claude": {
        "label": "Claude Code CLI",
        "baseline_turn1_input": 44074,
        "target_turn1_input": 18000,
        "baseline_calls_turn1": 1,
        "notes": "Hooks globales PMB + context-mode en ~/.claude/settings.json",
    },
}

_SECRET_EXTRA_PATTERNS = [
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,})\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}\b", re.IGNORECASE),
]


def sanitize_title(raw: str, max_len: int = 80) -> str:
    """Strip any accidental secrets or newlines from a session title."""
    if not raw:
        return ""
    cleaned = redact_text(str(raw))
    for pat in _SECRET_EXTRA_PATTERNS:
        cleaned = pat.sub("[REDACTED]", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned[:max_len]


def _make_anomaly_id(session_id: str, trace_id: str | None, rule_code: str) -> str:
    raw = f"{session_id}|{trace_id or ''}|{rule_code}"
    return "anm_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def analyze_session_traces(
    session: dict[str, Any],
    traces: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run deterministic anomaly rules over a session and its ordered call traces.

    Returns (updated_traces_with_flags, anomalies_list).
    """
    session_id = str(session["session_id"])
    now_iso = datetime.now(timezone.utc).isoformat()
    anomalies: list[dict[str, Any]] = []
    updated_traces: list[dict[str, Any]] = []

    # Rule 1: OUTLIER_SESSION (session-level)
    total_tokens = int(session.get("total_tokens", 0) or 0)
    cost_usd = float(session.get("cost_usd", 0.0) or 0.0)
    calls_count = int(session.get("calls_count", len(traces)) or 0)

    if total_tokens > 1_000_000 or cost_usd > 1.0:
        anomalies.append({
            "anomaly_id": _make_anomaly_id(session_id, None, "OUTLIER_SESSION"),
            "session_id": session_id,
            "trace_id": None,
            "rule_code": "OUTLIER_SESSION",
            "severity": "CRITICAL",
            "detected_at": session.get("ended_at") or now_iso,
            "metric_value": float(total_tokens),
            "threshold_value": 1_000_000.0,
            "recommendation": "Sesión extrema (>1M tokens o >$1 USD). Ejecutar /compact o dividir en sesiones cortas.",
        })

    if calls_count > 25:
        anomalies.append({
            "anomaly_id": _make_anomaly_id(session_id, None, "CONTEXT_BLOAT"),
            "session_id": session_id,
            "trace_id": None,
            "rule_code": "CONTEXT_BLOAT",
            "severity": "MEDIUM",
            "detected_at": session.get("ended_at") or now_iso,
            "metric_value": float(calls_count),
            "threshold_value": 25.0,
            "recommendation": f"Sesión con {calls_count} llamadas (>25). Recomendado compactar contexto.",
        })

    # Per-trace rules
    turn1_calls = [t for t in traces if int(t.get("turn_index", 1) or 1) == 1]
    has_double_turn1 = (
        len(turn1_calls) >= 2
        and sum(int(t.get("output_tokens", 0) or 0) for t in turn1_calls) < 250
    )

    prev_cache_read = 0
    consecutive_tool = ""
    consecutive_tool_count = 0
    bloat_trace_flagged = False

    for idx, tr in enumerate(traces):
        tr_copy = dict(tr)
        flags: list[str] = list(tr_copy.get("anomaly_flags") or [])
        trace_id = str(tr_copy.get("trace_id", f"{session_id}#{idx + 1}"))
        ts = str(tr_copy.get("timestamp") or session.get("ended_at") or now_iso)

        in_uncached = int(tr_copy.get("input_uncached", 0) or 0)
        cache_read = int(tr_copy.get("cache_read", 0) or 0)
        cache_write = int(tr_copy.get("cache_write", 0) or 0)
        in_total = in_uncached + cache_read + cache_write

        # Rule 2: DOUBLE_CALL_TURN1
        if has_double_turn1 and int(tr_copy.get("turn_index", 1) or 1) == 1 and int(tr_copy.get("call_index", idx + 1)) == 2:
            flags.append("DOUBLE_CALL_TURN1")
            anomalies.append({
                "anomaly_id": _make_anomaly_id(session_id, trace_id, "DOUBLE_CALL_TURN1"),
                "session_id": session_id,
                "trace_id": trace_id,
                "rule_code": "DOUBLE_CALL_TURN1",
                "severity": "HIGH",
                "detected_at": ts,
                "metric_value": float(len(turn1_calls)),
                "threshold_value": 1.0,
                "recommendation": "Turno 1 ejecutó >=2 llamadas para una respuesta corta (revisar using-superpowers o rename_session).",
            })

        # Rule 3: CACHE_BREAK
        if prev_cache_read >= 15_000 and cache_read < (prev_cache_read * 0.5) and in_total >= 15_000:
            flags.append("CACHE_BREAK")
            anomalies.append({
                "anomaly_id": _make_anomaly_id(session_id, trace_id, "CACHE_BREAK"),
                "session_id": session_id,
                "trace_id": trace_id,
                "rule_code": "CACHE_BREAK",
                "severity": "HIGH",
                "detected_at": ts,
                "metric_value": float(cache_read),
                "threshold_value": float(prev_cache_read * 0.5),
                "recommendation": f"Caída brusca de cache_read ({prev_cache_read:,} -> {cache_read:,}). Revisar mutación de prompt o TTL.",
            })

        # Rule 4: CONTEXT_BLOAT (single call > 80K input)
        if in_total > 80_000:
            flags.append("CONTEXT_BLOAT")
            if not bloat_trace_flagged:
                bloat_trace_flagged = True
                anomalies.append({
                    "anomaly_id": _make_anomaly_id(session_id, trace_id, "CONTEXT_BLOAT"),
                    "session_id": session_id,
                    "trace_id": trace_id,
                    "rule_code": "CONTEXT_BLOAT",
                    "severity": "MEDIUM",
                    "detected_at": ts,
                    "metric_value": float(in_total),
                    "threshold_value": 80_000.0,
                    "recommendation": f"Contexto de entrada alcanzó {in_total:,} tokens (>80K). Ejecutar /compact.",
                })

        # Rule 5: TOOL_LOOP (>=4 consecutive calls invoking the exact same primary tool)
        tools_called = list(tr_copy.get("tools_called") or [])
        if len(tools_called) == 1:
            tname = str(tools_called[0])
            if tname == consecutive_tool:
                consecutive_tool_count += 1
            else:
                consecutive_tool = tname
                consecutive_tool_count = 1
            if consecutive_tool_count == 4:
                flags.append("TOOL_LOOP")
                anomalies.append({
                    "anomaly_id": _make_anomaly_id(session_id, trace_id, "TOOL_LOOP"),
                    "session_id": session_id,
                    "trace_id": trace_id,
                    "rule_code": "TOOL_LOOP",
                    "severity": "HIGH",
                    "detected_at": ts,
                    "metric_value": float(consecutive_tool_count),
                    "threshold_value": 4.0,
                    "recommendation": f"Posible bucle de herramienta '{tname}' (4+ llamadas seguidas). Verificar oac-quota-guard.",
                })
        else:
            consecutive_tool = ""
            consecutive_tool_count = 0

        if cache_read > 0:
            prev_cache_read = cache_read

        tr_copy["anomaly_flags"] = sorted(set(flags))
        updated_traces.append(tr_copy)

    # Deduplicate anomalies by anomaly_id
    dedup: dict[str, dict[str, Any]] = {}
    for a in anomalies:
        dedup[a["anomaly_id"]] = a
    return updated_traces, list(dedup.values())
