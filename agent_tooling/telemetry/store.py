"""SQLite + Rotating JSONL Telemetry Store (Zero-Secrets, WAL-safe)."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_tooling.db.schema import connect, migrate
from agent_tooling.telemetry.analyzer import (
    AUDIT_BASELINE_BY_HARNESS,
    analyze_session_traces,
    sanitize_title,
)

MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB per file
MAX_LOG_FILES = 5


def get_default_trace_log_path(tooling_root: Path | None = None) -> Path:
    root = tooling_root or Path(os.environ.get("AGENT_TOOLING_ROOT", Path.home() / ".agents" / "tooling"))
    return root / "state" / "telemetry" / "token-traces.jsonl"


def _rotate_jsonl_if_needed(log_path: Path, max_bytes: int = MAX_LOG_BYTES, max_files: int = MAX_LOG_FILES) -> None:
    if not log_path.exists():
        return
    try:
        if log_path.stat().st_size < max_bytes:
            return
    except OSError:
        return
    # Shift .4 -> .5, .3 -> .4, ..., base -> .1
    for idx in range(max_files - 1, 0, -1):
        src = log_path.with_name(f"{log_path.stem}.{idx}{log_path.suffix}")
        dst = log_path.with_name(f"{log_path.stem}.{idx + 1}{log_path.suffix}")
        if src.exists():
            if dst.exists():
                dst.unlink()
            src.replace(dst)
    first_rot = log_path.with_name(f"{log_path.stem}.1{log_path.suffix}")
    if first_rot.exists():
        first_rot.unlink()
    log_path.replace(first_rot)


def _cutoff_iso(range_key: str) -> str | None:
    key = (range_key or "all").strip().lower()
    now = datetime.now(timezone.utc)
    if key in ("1d", "24h", "today"):
        return (now - timedelta(hours=24)).isoformat()
    if key == "3d":
        return (now - timedelta(days=3)).isoformat()
    if key in ("7d", "week"):
        return (now - timedelta(days=7)).isoformat()
    if key in ("30d", "month"):
        return (now - timedelta(days=30)).isoformat()
    if key == "90d":
        return (now - timedelta(days=90)).isoformat()
    return None


def _range_days(range_key: str) -> int | None:
    key = (range_key or "all").strip().lower()
    return {"24h": 1, "1d": 1, "today": 1, "3d": 3, "7d": 7, "week": 7, "30d": 30, "month": 30, "90d": 90}.get(key)


def _infer_provider(model: str) -> str:
    m = (model or "").lower()
    if any(x in m for x in ("claude", "opus", "sonnet", "haiku", "anthropic")):
        return "Anthropic"
    if any(x in m for x in ("gpt", "openai", "o1", "o3", "o4", "codex", "luna", "terra", "astra", "sol")):
        return "OpenAI"
    if any(x in m for x in ("gemini", "google", "gemma")):
        return "Google"
    if any(x in m for x in ("glm", "zhipu", "z.ai")):
        return "Zhipu"
    if any(x in m for x in ("grok", "xai")):
        return "xAI"
    if any(x in m for x in ("deepseek", "qwen", "nemotron", "llama", "kimi", "minimax")):
        return "Open Weights"
    return "Other"


def _parse_iso_dt(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _session_duration_sec(started_at: str, ended_at: str, calls_count: int) -> float:
    s_dt = _parse_iso_dt(started_at)
    e_dt = _parse_iso_dt(ended_at)
    if s_dt and e_dt:
        diff = (e_dt - s_dt).total_seconds()
        if 0 < diff <= 14400:  # cap single session active duration at 4h to exclude multi-day idle gaps
            return diff
        if diff > 14400:
            return min(14400.0, max(60.0, calls_count * 25.0))
    return max(15.0, calls_count * 12.0)


def _pct_delta(cur: float, prev: float) -> float | None:
    if prev <= 0:
        return None
    return round(((cur - prev) / prev) * 100.0, 1)


class TelemetryStore:
    """Unified read/write store for token telemetry sessions, traces, anomalies, and JSONL logs."""

    def __init__(
        self,
        db_path: Path,
        trace_log_path: Path | None = None,
        max_log_bytes: int = MAX_LOG_BYTES,
    ) -> None:
        self.db_path = Path(db_path)
        self.trace_log_path = Path(trace_log_path) if trace_log_path else (
            self.db_path.parent / "telemetry" / "token-traces.jsonl"
        )
        self.max_log_bytes = max_log_bytes

    def _conn(self) -> sqlite3.Connection:
        conn = connect(self.db_path)
        migrate(conn)
        return conn

    def get_watermark(self, source_key: str) -> tuple[float, str]:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT last_mtime, last_cursor FROM telemetry_watermarks WHERE source_key = ?",
                (source_key,),
            ).fetchone()
            if not row:
                return 0.0, ""
            return float(row["last_mtime"] or 0.0), str(row["last_cursor"] or "")
        finally:
            conn.close()

    def set_watermark(self, source_key: str, last_mtime: float, last_cursor: str = "") -> None:
        conn = self._conn()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO telemetry_watermarks(source_key, last_mtime, last_cursor, last_synced_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_key) DO UPDATE SET
                        last_mtime = excluded.last_mtime,
                        last_cursor = excluded.last_cursor,
                        last_synced_at = excluded.last_synced_at
                    """,
                    (source_key, float(last_mtime), str(last_cursor), now),
                )
        finally:
            conn.close()

    def upsert_session_with_traces(
        self,
        session: dict[str, Any],
        traces: list[dict[str, Any]] | None = None,
        write_jsonl: bool = True,
    ) -> dict[str, int]:
        """Insert or update a session, its call traces, anomalies, and append new traces to JSONL."""
        traces = traces or []
        session_clean = dict(session)
        session_clean["title_sanitized"] = sanitize_title(str(session_clean.get("title_sanitized", "")))

        # Recompute cache_hit_ratio if not provided
        in_u = int(session_clean.get("input_uncached", 0) or 0)
        c_r = int(session_clean.get("cache_read", 0) or 0)
        c_w = int(session_clean.get("cache_write", 0) or 0)
        in_all = in_u + c_r + c_w
        if in_all > 0:
            session_clean["cache_hit_ratio"] = round((c_r / in_all) * 100.0, 2)
        else:
            session_clean["cache_hit_ratio"] = float(session_clean.get("cache_hit_ratio", 0.0) or 0.0)

        analyzed_traces, anomalies = analyze_session_traces(session_clean, traces)
        session_clean["anomaly_count"] = len(anomalies)

        new_trace_rows: list[dict[str, Any]] = []
        conn = self._conn()
        try:
            existing_trace_ids = {
                r["trace_id"]
                for r in conn.execute(
                    "SELECT trace_id FROM token_traces WHERE session_id = ?",
                    (session_clean["session_id"],),
                ).fetchall()
            }

            with conn:
                conn.execute(
                    """
                    INSERT INTO token_sessions (
                        session_id, harness, mode, title_sanitized, primary_model, profile_active,
                        started_at, ended_at, calls_count, input_uncached, cache_read, cache_write,
                        output_tokens, reasoning_tokens, total_tokens, cache_hit_ratio,
                        cost_usd, ai_credits, anomaly_count, source_file, source_mtime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        harness = excluded.harness,
                        mode = excluded.mode,
                        title_sanitized = CASE
                            WHEN excluded.title_sanitized != '' THEN excluded.title_sanitized
                            ELSE token_sessions.title_sanitized
                        END,
                        primary_model = CASE
                            WHEN excluded.primary_model != 'unknown' THEN excluded.primary_model
                            ELSE token_sessions.primary_model
                        END,
                        profile_active = CASE
                            WHEN excluded.profile_active != 'unknown' THEN excluded.profile_active
                            ELSE token_sessions.profile_active
                        END,
                        started_at = excluded.started_at,
                        ended_at = excluded.ended_at,
                        calls_count = MAX(token_sessions.calls_count, excluded.calls_count),
                        input_uncached = excluded.input_uncached,
                        cache_read = excluded.cache_read,
                        cache_write = excluded.cache_write,
                        output_tokens = excluded.output_tokens,
                        reasoning_tokens = excluded.reasoning_tokens,
                        total_tokens = excluded.total_tokens,
                        cache_hit_ratio = excluded.cache_hit_ratio,
                        cost_usd = excluded.cost_usd,
                        ai_credits = excluded.ai_credits,
                        anomaly_count = excluded.anomaly_count,
                        source_file = excluded.source_file,
                        source_mtime = excluded.source_mtime
                    """,
                    (
                        str(session_clean["session_id"]),
                        str(session_clean.get("harness", "unknown")).lower(),
                        str(session_clean.get("mode", "default")),
                        str(session_clean["title_sanitized"]),
                        str(session_clean.get("primary_model", "unknown")),
                        str(session_clean.get("profile_active", "unknown")),
                        str(session_clean.get("started_at", "")),
                        str(session_clean.get("ended_at", "")),
                        int(session_clean.get("calls_count", len(analyzed_traces)) or 0),
                        in_u,
                        c_r,
                        c_w,
                        int(session_clean.get("output_tokens", 0) or 0),
                        int(session_clean.get("reasoning_tokens", 0) or 0),
                        int(session_clean.get("total_tokens", 0) or 0),
                        float(session_clean["cache_hit_ratio"]),
                        float(session_clean.get("cost_usd", 0.0) or 0.0),
                        float(session_clean.get("ai_credits", 0.0) or 0.0),
                        len(anomalies),
                        str(session_clean.get("source_file", "")),
                        float(session_clean.get("source_mtime", 0.0) or 0.0),
                    ),
                )

                for tr in analyzed_traces:
                    tid = str(tr["trace_id"])
                    tools_list = [str(x)[:64] for x in (tr.get("tools_called") or [])]
                    flags_list = [str(x)[:40] for x in (tr.get("anomaly_flags") or [])]
                    conn.execute(
                        """
                        INSERT INTO token_traces (
                            trace_id, session_id, turn_index, call_index, timestamp, model,
                            input_uncached, cache_read, cache_write, output_tokens, reasoning_tokens,
                            total_tokens, cost_usd, ai_credits, latency_ms,
                            tools_called_json, anomaly_flags_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(trace_id) DO UPDATE SET
                            input_uncached = excluded.input_uncached,
                            cache_read = excluded.cache_read,
                            cache_write = excluded.cache_write,
                            output_tokens = excluded.output_tokens,
                            reasoning_tokens = excluded.reasoning_tokens,
                            total_tokens = excluded.total_tokens,
                            cost_usd = excluded.cost_usd,
                            ai_credits = excluded.ai_credits,
                            latency_ms = excluded.latency_ms,
                            tools_called_json = excluded.tools_called_json,
                            anomaly_flags_json = excluded.anomaly_flags_json
                        """,
                        (
                            tid,
                            str(session_clean["session_id"]),
                            int(tr.get("turn_index", 1) or 1),
                            int(tr.get("call_index", 1) or 1),
                            str(tr.get("timestamp", session_clean.get("ended_at", ""))),
                            str(tr.get("model", session_clean.get("primary_model", "unknown"))),
                            int(tr.get("input_uncached", 0) or 0),
                            int(tr.get("cache_read", 0) or 0),
                            int(tr.get("cache_write", 0) or 0),
                            int(tr.get("output_tokens", 0) or 0),
                            int(tr.get("reasoning_tokens", 0) or 0),
                            int(tr.get("total_tokens", 0) or 0),
                            float(tr.get("cost_usd", 0.0) or 0.0),
                            float(tr.get("ai_credits", 0.0) or 0.0),
                            float(tr.get("latency_ms", 0.0) or 0.0),
                            json.dumps(tools_list, ensure_ascii=False),
                            json.dumps(flags_list, ensure_ascii=False),
                        ),
                    )
                    if tid not in existing_trace_ids:
                        new_trace_rows.append({
                            "schema_v": 1,
                            "trace_id": tid,
                            "recorded_at": str(tr.get("timestamp", session_clean.get("ended_at", ""))),
                            "harness": str(session_clean.get("harness", "unknown")).lower(),
                            "mode": str(session_clean.get("mode", "default")),
                            "session_id": str(session_clean["session_id"]),
                            "turn_index": int(tr.get("turn_index", 1) or 1),
                            "call_index": int(tr.get("call_index", 1) or 1),
                            "model": str(tr.get("model", session_clean.get("primary_model", "unknown"))),
                            "profile_active": str(session_clean.get("profile_active", "unknown")),
                            "input_uncached": int(tr.get("input_uncached", 0) or 0),
                            "cache_read": int(tr.get("cache_read", 0) or 0),
                            "cache_write": int(tr.get("cache_write", 0) or 0),
                            "output_tokens": int(tr.get("output_tokens", 0) or 0),
                            "reasoning_tokens": int(tr.get("reasoning_tokens", 0) or 0),
                            "total_tokens": int(tr.get("total_tokens", 0) or 0),
                            "cost_usd": round(float(tr.get("cost_usd", 0.0) or 0.0), 6),
                            "ai_credits": round(float(tr.get("ai_credits", 0.0) or 0.0), 4),
                            "latency_ms": round(float(tr.get("latency_ms", 0.0) or 0.0), 1),
                            "tools_called": tools_list,
                            "anomalies": flags_list,
                        })

                # Replace anomalies for this session cleanly
                conn.execute("DELETE FROM token_anomalies WHERE session_id = ?", (session_clean["session_id"],))
                for anm in anomalies:
                    conn.execute(
                        """
                        INSERT INTO token_anomalies (
                            anomaly_id, session_id, trace_id, rule_code, severity,
                            detected_at, metric_value, threshold_value, recommendation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            anm["anomaly_id"],
                            anm["session_id"],
                            anm.get("trace_id"),
                            anm["rule_code"],
                            anm["severity"],
                            anm["detected_at"],
                            float(anm["metric_value"]),
                            float(anm["threshold_value"]),
                            sanitize_title(str(anm["recommendation"]), max_len=240),
                        ),
                    )
        finally:
            conn.close()

        if write_jsonl and new_trace_rows:
            self._append_jsonl(new_trace_rows)

        return {"traces_new": len(new_trace_rows), "anomalies": len(anomalies)}

    def _append_jsonl(self, rows: list[dict[str, Any]]) -> None:
        self.trace_log_path.parent.mkdir(parents=True, exist_ok=True)
        _rotate_jsonl_if_needed(self.trace_log_path, max_bytes=self.max_log_bytes)
        with self.trace_log_path.open("a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def get_summary(self, range_key: str = "all", harness: str = "all") -> dict[str, Any]:
        cutoff = _cutoff_iso(range_key)
        clauses: list[str] = []
        params: list[Any] = []
        if cutoff:
            clauses.append("ended_at >= ?")
            params.append(cutoff)
        if harness and harness.lower() != "all":
            clauses.append("harness = ?")
            params.append(harness.lower())
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        conn = self._conn()
        try:
            agg = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS sessions_count,
                    COALESCE(SUM(calls_count), 0) AS calls_count,
                    COALESCE(SUM(input_uncached), 0) AS input_uncached,
                    COALESCE(SUM(cache_read), 0) AS cache_read,
                    COALESCE(SUM(cache_write), 0) AS cache_write,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COALESCE(SUM(reasoning_tokens), 0) AS reasoning_tokens,
                    COALESCE(SUM(total_tokens), 0) AS total_tokens,
                    COALESCE(SUM(cost_usd), 0.0) AS cost_usd,
                    COALESCE(SUM(ai_credits), 0.0) AS ai_credits,
                    COALESCE(SUM(anomaly_count), 0) AS anomalies_count
                FROM token_sessions
                {where_sql}
                """,
                params,
            ).fetchone()

            in_u = int(agg["input_uncached"])
            c_r = int(agg["cache_read"])
            c_w = int(agg["cache_write"])
            in_all = in_u + c_r + c_w
            cache_hit_ratio = round((c_r / in_all) * 100.0, 2) if in_all > 0 else 0.0

            by_harness = []
            for r in conn.execute(
                f"""
                SELECT
                    harness,
                    COUNT(*) AS sessions,
                    COALESCE(SUM(calls_count), 0) AS calls,
                    COALESCE(SUM(input_uncached), 0) AS input_uncached,
                    COALESCE(SUM(cache_read), 0) AS cache_read,
                    COALESCE(SUM(cache_write), 0) AS cache_write,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COALESCE(SUM(total_tokens), 0) AS total_tokens,
                    COALESCE(SUM(cost_usd), 0.0) AS cost_usd,
                    COALESCE(SUM(ai_credits), 0.0) AS ai_credits,
                    COALESCE(SUM(anomaly_count), 0) AS anomalies
                FROM token_sessions
                {where_sql}
                GROUP BY harness
                ORDER BY total_tokens DESC
                """,
                params,
            ).fetchall():
                h_in_all = int(r["input_uncached"]) + int(r["cache_read"]) + int(r["cache_write"])
                h_calls = max(int(r["calls"]), 1)
                h_key = str(r["harness"])
                base_info = AUDIT_BASELINE_BY_HARNESS.get(h_key, {})
                by_harness.append({
                    "harness": h_key,
                    "label": base_info.get("label", h_key),
                    "sessions": int(r["sessions"]),
                    "calls": int(r["calls"]),
                    "input_uncached": int(r["input_uncached"]),
                    "cache_read": int(r["cache_read"]),
                    "output_tokens": int(r["output_tokens"]),
                    "total_tokens": int(r["total_tokens"]),
                    "avg_tokens_per_call": round(int(r["total_tokens"]) / h_calls),
                    "cache_hit_ratio": round((int(r["cache_read"]) / h_in_all) * 100.0, 1) if h_in_all > 0 else 0.0,
                    "cost_usd": round(float(r["cost_usd"]), 4),
                    "ai_credits": round(float(r["ai_credits"]), 2),
                    "anomalies": int(r["anomalies"]),
                    "baseline_turn1_input": base_info.get("baseline_turn1_input"),
                    "target_turn1_input": base_info.get("target_turn1_input"),
                })

            by_model = [
                {
                    "model": str(r["primary_model"]),
                    "sessions": int(r["sessions"]),
                    "calls": int(r["calls"]),
                    "total_tokens": int(r["total_tokens"]),
                    "cost_usd": round(float(r["cost_usd"]), 4),
                }
                for r in conn.execute(
                    f"""
                    SELECT primary_model, COUNT(*) AS sessions,
                           COALESCE(SUM(calls_count), 0) AS calls,
                           COALESCE(SUM(total_tokens), 0) AS total_tokens,
                           COALESCE(SUM(cost_usd), 0.0) AS cost_usd
                    FROM token_sessions
                    {where_sql}
                    GROUP BY primary_model
                    ORDER BY total_tokens DESC
                    LIMIT 15
                    """,
                    params,
                ).fetchall()
            ]

            daily = [
                {
                    "day": str(r["day"]),
                    "sessions": int(r["sessions"]),
                    "calls": int(r["calls"]),
                    "input_uncached": int(r["input_uncached"]),
                    "cache_read": int(r["cache_read"]),
                    "output_tokens": int(r["output_tokens"]),
                    "total_tokens": int(r["total_tokens"]),
                    "cost_usd": round(float(r["cost_usd"]), 4),
                }
                for r in conn.execute(
                    f"""
                    SELECT SUBSTR(ended_at, 1, 10) AS day,
                           COUNT(*) AS sessions,
                           COALESCE(SUM(calls_count), 0) AS calls,
                           COALESCE(SUM(input_uncached), 0) AS input_uncached,
                           COALESCE(SUM(cache_read), 0) AS cache_read,
                           COALESCE(SUM(output_tokens), 0) AS output_tokens,
                           COALESCE(SUM(total_tokens), 0) AS total_tokens,
                           COALESCE(SUM(cost_usd), 0.0) AS cost_usd
                    FROM token_sessions
                    {where_sql}
                    GROUP BY day
                    ORDER BY day ASC
                    LIMIT 30
                    """,
                    params,
                ).fetchall()
                if r["day"]
            ]

            daily_by_harness_rows = conn.execute(
                f"""
                SELECT SUBSTR(ended_at, 1, 10) AS day,
                       harness,
                       COUNT(*) AS sessions,
                       COALESCE(SUM(calls_count), 0) AS calls,
                       COALESCE(SUM(input_uncached), 0) AS input_uncached,
                       COALESCE(SUM(cache_read), 0) AS cache_read,
                       COALESCE(SUM(cache_write), 0) AS cache_write,
                       COALESCE(SUM(output_tokens), 0) AS output_tokens,
                       COALESCE(SUM(total_tokens), 0) AS total_tokens,
                       COALESCE(SUM(cost_usd), 0.0) AS cost_usd
                FROM token_sessions
                {where_sql}
                GROUP BY day, harness
                ORDER BY day ASC
                """,
                params,
            ).fetchall()

            days_sorted = sorted({str(r["day"]) for r in daily_by_harness_rows if r["day"]})[-30:]
            days_set = set(days_sorted)
            series_map: dict[str, dict[str, dict[str, Any]]] = {}
            for r in daily_by_harness_rows:
                d_str = str(r["day"] or "")
                if d_str not in days_set:
                    continue
                hk = str(r["harness"])
                h_in = int(r["input_uncached"]) + int(r["cache_read"]) + int(r["cache_write"])
                series_map.setdefault(hk, {})[d_str] = {
                    "day": d_str,
                    "calls": int(r["calls"]),
                    "input_uncached": int(r["input_uncached"]),
                    "cache_read": int(r["cache_read"]),
                    "output_tokens": int(r["output_tokens"]),
                    "total_tokens": int(r["total_tokens"]),
                    "cache_hit_ratio": round((int(r["cache_read"]) / h_in) * 100.0, 1) if h_in > 0 else 0.0,
                    "cost_usd": round(float(r["cost_usd"]), 4),
                }

            # Keep top 8 harnesses by volume for crisp multi-line rendering
            top_harnesses = [h["harness"] for h in by_harness[:8]]
            daily_by_harness = {
                "days": days_sorted,
                "series": {
                    hk: [
                        series_map.get(hk, {}).get(
                            d_str,
                            {
                                "day": d_str,
                                "calls": 0,
                                "input_uncached": 0,
                                "cache_read": 0,
                                "output_tokens": 0,
                                "total_tokens": 0,
                                "cache_hit_ratio": 0.0,
                                "cost_usd": 0.0,
                            },
                        )
                        for d_str in days_sorted
                    ]
                    for hk in top_harnesses
                },
            }

            calls_tot = max(int(agg["calls_count"]), 1)
            sess_tot = max(int(agg["sessions_count"]), 1)
            out_tot = int(agg["output_tokens"]) + int(agg["reasoning_tokens"])
            tok_tot = max(int(agg["total_tokens"]), 1)
            avg_tok_per_call = round(int(agg["total_tokens"]) / calls_tot)
            avg_uncached_per_call = round(in_u / calls_tot)
            # Efficiency score (0..100): 55% Cache Hit + 25% Uncached/Call leanness + 20% low anomaly rate
            uncached_lean = max(0.0, min(100.0, 100.0 - max(0.0, (avg_uncached_per_call - 5000) / 500.0)))
            anm_ratio = min(1.0, int(agg["anomalies_count"]) / sess_tot)
            clean_score = (1.0 - anm_ratio) * 100.0
            efficiency_score = round(0.55 * cache_hit_ratio + 0.25 * uncached_lean + 0.20 * clean_score, 1)

            # Detailed per-session pass for exact agent_time, rellamados, 7x24 heatmap, and daily sparklines
            sess_rows = conn.execute(
                f"""
                SELECT session_id, harness, primary_model, started_at, ended_at,
                       calls_count, input_uncached, cache_read, cache_write,
                       output_tokens, reasoning_tokens, total_tokens, cost_usd, anomaly_count
                FROM token_sessions
                {where_sql}
                ORDER BY ended_at ASC
                """,
                params,
            ).fetchall()

            heatmap = [[0 for _ in range(24)] for _ in range(7)]
            harness_time: dict[str, float] = {}
            harness_rellamados: dict[str, int] = {}
            provider_tokens: dict[str, int] = {}
            daily_extra: dict[str, dict[str, Any]] = {}
            total_agent_time_sec = 0.0
            total_rellamados = 0
            min_day = ""
            max_day = ""

            for sr in sess_rows:
                h_key = str(sr["harness"])
                c_cnt = int(sr["calls_count"] or 0)
                rell = max(0, c_cnt - 1)
                dur = _session_duration_sec(str(sr["started_at"] or ""), str(sr["ended_at"] or ""), c_cnt)
                total_agent_time_sec += dur
                total_rellamados += rell
                harness_time[h_key] = harness_time.get(h_key, 0.0) + dur
                harness_rellamados[h_key] = harness_rellamados.get(h_key, 0) + rell

                prov = _infer_provider(str(sr["primary_model"] or ""))
                s_in = int(sr["input_uncached"] or 0) + int(sr["cache_read"] or 0) + int(sr["cache_write"] or 0)
                s_out = int(sr["output_tokens"] or 0) + int(sr["reasoning_tokens"] or 0)
                provider_tokens[prov] = provider_tokens.get(prov, 0) + max(s_in + s_out, int(sr["total_tokens"] or 0))

                dt_end = _parse_iso_dt(str(sr["ended_at"] or sr["started_at"] or ""))
                if dt_end is not None:
                    local_dt = dt_end.astimezone()
                    heatmap[local_dt.weekday()][local_dt.hour] += max(1, c_cnt)
                    d_str = local_dt.strftime("%Y-%m-%d")
                else:
                    d_str = str(sr["ended_at"] or "")[:10]

                if d_str:
                    if not min_day or d_str < min_day:
                        min_day = d_str
                    if not max_day or d_str > max_day:
                        max_day = d_str
                    de = daily_extra.setdefault(
                        d_str,
                        {
                            "day": d_str,
                            "sessions": 0,
                            "calls": 0,
                            "rellamados": 0,
                            "input_tokens": 0,
                            "input_uncached": 0,
                            "cache_read": 0,
                            "output_tokens": 0,
                            "total_tokens": 0,
                            "agent_time_sec": 0.0,
                            "cost_usd": 0.0,
                            "anomalies": 0,
                        },
                    )
                    de["sessions"] += 1
                    de["calls"] += c_cnt
                    de["rellamados"] += rell
                    de["input_tokens"] += s_in
                    de["input_uncached"] += int(sr["input_uncached"] or 0)
                    de["cache_read"] += int(sr["cache_read"] or 0)
                    de["output_tokens"] += s_out
                    de["total_tokens"] += int(sr["total_tokens"] or 0)
                    de["agent_time_sec"] += dur
                    de["cost_usd"] += float(sr["cost_usd"] or 0.0)
                    de["anomalies"] += int(sr["anomaly_count"] or 0)

            # Enrich by_harness with input_tokens, rellamados, agent_time_sec
            for h_item in by_harness:
                hk = h_item["harness"]
                h_item["input_tokens"] = h_item["input_uncached"] + h_item["cache_read"]
                h_item["rellamados"] = harness_rellamados.get(hk, 0)
                h_item["agent_time_sec"] = round(harness_time.get(hk, 0.0), 1)

            # Enrich by_model with input/output/provider
            by_model = [
                {
                    "model": str(r["primary_model"]),
                    "provider": _infer_provider(str(r["primary_model"])),
                    "sessions": int(r["sessions"]),
                    "calls": int(r["calls"]),
                    "input_tokens": int(r["input_uncached"]) + int(r["cache_read"]) + int(r["cache_write"]),
                    "output_tokens": int(r["output_tokens"]) + int(r["reasoning_tokens"]),
                    "total_tokens": int(r["total_tokens"]),
                    "cost_usd": round(float(r["cost_usd"]), 4),
                }
                for r in conn.execute(
                    f"""
                    SELECT primary_model, COUNT(*) AS sessions,
                           COALESCE(SUM(calls_count), 0) AS calls,
                           COALESCE(SUM(input_uncached), 0) AS input_uncached,
                           COALESCE(SUM(cache_read), 0) AS cache_read,
                           COALESCE(SUM(cache_write), 0) AS cache_write,
                           COALESCE(SUM(output_tokens), 0) AS output_tokens,
                           COALESCE(SUM(reasoning_tokens), 0) AS reasoning_tokens,
                           COALESCE(SUM(total_tokens), 0) AS total_tokens,
                           COALESCE(SUM(cost_usd), 0.0) AS cost_usd
                    FROM token_sessions
                    {where_sql}
                    GROUP BY primary_model
                    ORDER BY total_tokens DESC
                    LIMIT 20
                    """,
                    params,
                ).fetchall()
            ]

            prov_tot = max(sum(provider_tokens.values()), 1)
            by_provider = sorted(
                [
                    {"provider": k, "tokens": v, "pct": round((v / prov_tot) * 100.0, 1)}
                    for k, v in provider_tokens.items()
                    if v > 0
                ],
                key=lambda x: x["tokens"],
                reverse=True,
            )

            # Most active weekday & hour for heatmap
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            best_val = 0
            best_d, best_h = 0, 0
            for di in range(7):
                for hi in range(24):
                    if heatmap[di][hi] > best_val:
                        best_val = heatmap[di][hi]
                        best_d, best_h = di, hi
            most_active_label = f"{day_names[best_d]} {best_h:02d} h" if best_val > 0 else "—"

            # Build continuous daily series for sparklines and mirrored input/output chart
            daily_enriched = []
            for d_str in sorted(daily_extra.keys())[-30:]:
                de = daily_extra[d_str]
                d_in = max(de["input_tokens"], 1)
                d_cr = round((de["cache_read"] / d_in) * 100.0, 1) if de["input_tokens"] > 0 else 0.0
                d_calls = max(de["calls"], 1)
                d_u_lean = max(0.0, min(100.0, 100.0 - max(0.0, ((de["input_uncached"] / d_calls) - 5000) / 500.0)))
                d_clean = (1.0 - min(1.0, de["anomalies"] / max(de["sessions"], 1))) * 100.0
                de["efficiency_score"] = round(0.55 * d_cr + 0.25 * d_u_lean + 0.20 * d_clean, 1)
                de["agent_time_sec"] = round(de["agent_time_sec"], 1)
                de["cost_usd"] = round(de["cost_usd"], 4)
                daily_enriched.append(de)

            # Previous period deltas (when a bounded range is selected)
            deltas: dict[str, float | None] = {
                "input_pct": None,
                "output_pct": None,
                "tasks_pct": None,
                "rellamados_pct": None,
                "efficiency_pct": None,
                "time_pct": None,
            }
            rdays = _range_days(range_key)
            if rdays is not None and cutoff:
                prev_start = (datetime.now(timezone.utc) - timedelta(days=rdays * 2)).isoformat()
                prev_clauses = ["ended_at >= ?", "ended_at < ?"]
                prev_params: list[Any] = [prev_start, cutoff]
                if harness and harness.lower() != "all":
                    prev_clauses.append("harness = ?")
                    prev_params.append(harness.lower())
                p_rows = conn.execute(
                    f"""
                    SELECT started_at, ended_at, calls_count, input_uncached, cache_read, cache_write,
                           output_tokens, reasoning_tokens, anomaly_count
                    FROM token_sessions
                    WHERE {' AND '.join(prev_clauses)}
                    """,
                    prev_params,
                ).fetchall()
                if p_rows:
                    p_in = sum(int(r["input_uncached"] or 0) + int(r["cache_read"] or 0) + int(r["cache_write"] or 0) for r in p_rows)
                    p_cr = sum(int(r["cache_read"] or 0) for r in p_rows)
                    p_u = sum(int(r["input_uncached"] or 0) for r in p_rows)
                    p_out = sum(int(r["output_tokens"] or 0) + int(r["reasoning_tokens"] or 0) for r in p_rows)
                    p_tasks = len(p_rows)
                    p_calls = sum(int(r["calls_count"] or 0) for r in p_rows)
                    p_rell = sum(max(0, int(r["calls_count"] or 0) - 1) for r in p_rows)
                    p_anm = sum(int(r["anomaly_count"] or 0) for r in p_rows)
                    p_time = sum(_session_duration_sec(str(r["started_at"] or ""), str(r["ended_at"] or ""), int(r["calls_count"] or 0)) for r in p_rows)
                    p_cr_pct = (p_cr / p_in * 100.0) if p_in > 0 else 0.0
                    p_u_lean = max(0.0, min(100.0, 100.0 - max(0.0, ((p_u / max(p_calls, 1)) - 5000) / 500.0)))
                    p_clean = (1.0 - min(1.0, p_anm / max(p_tasks, 1))) * 100.0
                    p_eff = 0.55 * p_cr_pct + 0.25 * p_u_lean + 0.20 * p_clean

                    deltas["input_pct"] = _pct_delta(float(in_all), float(p_in))
                    deltas["output_pct"] = _pct_delta(float(out_tot), float(p_out))
                    deltas["tasks_pct"] = _pct_delta(float(int(agg["sessions_count"])), float(p_tasks))
                    deltas["rellamados_pct"] = _pct_delta(float(total_rellamados), float(p_rell))
                    deltas["efficiency_pct"] = _pct_delta(float(efficiency_score), float(p_eff))
                    deltas["time_pct"] = _pct_delta(float(total_agent_time_sec), float(p_time))

            active_days = len(daily_extra)
            window_days = rdays if rdays is not None else max(active_days, 1)
            avg_tokens_per_day = round(int(agg["total_tokens"]) / max(active_days, 1))

            wm = conn.execute(
                "SELECT MAX(last_synced_at) AS last_synced_at FROM telemetry_watermarks"
            ).fetchone()

            log_size = self.trace_log_path.stat().st_size if self.trace_log_path.exists() else 0

            return {
                "range": range_key,
                "harness": harness,
                "date_span": {"start": min_day, "end": max_day, "active_days": active_days, "window_days": window_days, "avg_tokens_per_day": avg_tokens_per_day},
                "last_synced_at": wm["last_synced_at"] if wm else None,
                "trace_log_path": str(self.trace_log_path),
                "trace_log_bytes": log_size,
                "kpis": {
                    "sessions_count": int(agg["sessions_count"]),
                    "calls_count": int(agg["calls_count"]),
                    "rellamados_count": total_rellamados,
                    "avg_rellamados_per_task": round(total_rellamados / sess_tot, 1),
                    "agent_time_sec": round(total_agent_time_sec, 1),
                    "input_tokens": in_all,
                    "input_uncached": in_u,
                    "cache_read": c_r,
                    "cache_write": c_w,
                    "output_tokens": int(agg["output_tokens"]),
                    "reasoning_tokens": int(agg["reasoning_tokens"]),
                    "output_total": out_tot,
                    "avg_output_per_call": round(out_tot / calls_tot),
                    "total_tokens": int(agg["total_tokens"]),
                    "cache_hit_ratio": cache_hit_ratio,
                    "efficiency_score": efficiency_score,
                    "avg_tokens_per_call": avg_tok_per_call,
                    "avg_uncached_per_call": avg_uncached_per_call,
                    "input_uncached_pct": round((in_u / tok_tot) * 100.0, 1),
                    "cache_read_pct": round((c_r / tok_tot) * 100.0, 1),
                    "output_pct": round((out_tot / tok_tot) * 100.0, 1),
                    "cost_usd": round(float(agg["cost_usd"]), 4),
                    "ai_credits": round(float(agg["ai_credits"]), 2),
                    "anomalies_count": int(agg["anomalies_count"]),
                    "deltas": deltas,
                },
                "by_harness": by_harness,
                "by_model": by_model,
                "by_provider": by_provider,
                "daily": daily_enriched,
                "daily_by_harness": daily_by_harness,
                "when_they_work": {"matrix": heatmap, "most_active": most_active_label, "max_cell": best_val},
                "baseline_reference": AUDIT_BASELINE_BY_HARNESS,
            }
        finally:
            conn.close()

    def list_sessions(
        self,
        range_key: str = "all",
        harness: str = "all",
        model: str = "all",
        anomalies_only: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        cutoff = _cutoff_iso(range_key)
        clauses: list[str] = []
        params: list[Any] = []
        if cutoff:
            clauses.append("ended_at >= ?")
            params.append(cutoff)
        if harness and harness.lower() != "all":
            clauses.append("harness = ?")
            params.append(harness.lower())
        if model and model.lower() != "all":
            clauses.append("primary_model = ?")
            params.append(model)
        if anomalies_only:
            clauses.append("anomaly_count > 0")
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(max(1, min(int(limit), 250)))

        conn = self._conn()
        try:
            rows = conn.execute(
                f"""
                SELECT * FROM token_sessions
                {where_sql}
                ORDER BY ended_at DESC, total_tokens DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_session_traces(self, session_id: str) -> dict[str, Any]:
        conn = self._conn()
        try:
            sess = conn.execute(
                "SELECT * FROM token_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not sess:
                return {"session": None, "traces": [], "anomalies": []}
            traces = []
            for r in conn.execute(
                "SELECT * FROM token_traces WHERE session_id = ? ORDER BY call_index ASC, timestamp ASC",
                (session_id,),
            ).fetchall():
                d = dict(r)
                d["tools_called"] = json.loads(d.pop("tools_called_json", "[]") or "[]")
                d["anomaly_flags"] = json.loads(d.pop("anomaly_flags_json", "[]") or "[]")
                traces.append(d)
            anomalies = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM token_anomalies WHERE session_id = ? ORDER BY detected_at DESC",
                    (session_id,),
                ).fetchall()
            ]
            return {"session": dict(sess), "traces": traces, "anomalies": anomalies}
        finally:
            conn.close()

    def list_anomalies(self, severity: str = "all", limit: int = 50) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if severity and severity.lower() != "all":
            clauses.append("a.severity = ?")
            params.append(severity.upper())
        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(max(1, min(int(limit), 200)))

        conn = self._conn()
        try:
            rows = conn.execute(
                f"""
                SELECT a.*, s.harness, s.primary_model, s.title_sanitized
                FROM token_anomalies a
                LEFT JOIN token_sessions s ON s.session_id = a.session_id
                {where_sql}
                ORDER BY
                    CASE a.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                    a.detected_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def tail_trace_log(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.trace_log_path.exists():
            return []
        try:
            lines = self.trace_log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            out = []
            for ln in lines[-max(1, min(limit, 200)):]:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    continue
            return list(reversed(out))
        except OSError:
            return []

    def prune_old_traces(self, days: int = 90) -> dict[str, int]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max(1, days))).isoformat()
        conn = self._conn()
        try:
            with conn:
                cur = conn.execute("DELETE FROM token_sessions WHERE ended_at < ?", (cutoff,))
                deleted = cur.rowcount
            return {"deleted_sessions": deleted, "cutoff": cutoff}
        finally:
            conn.close()
