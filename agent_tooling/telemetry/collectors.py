"""Read-only incremental telemetry collectors across all installed agent harnesses."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_tooling.profile_switcher import get_active_profile_state
from agent_tooling.telemetry.analyzer import sanitize_title
from agent_tooling.telemetry.store import TelemetryStore


def _iso_from_any(val: Any) -> str:
    if not val:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(val, (int, float)):
        ts = float(val)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()
    s = str(val).strip()
    if s.isdigit():
        return _iso_from_any(int(s))
    return s


def _norm_harness(raw: str) -> str:
    val = (raw or "unknown").strip().lower()
    if "opencode" in val or "openchamber" in val:
        return "opencode"
    if "codex" in val:
        return "codex"
    if "copilot" in val:
        return "copilot"
    if "antigravity" in val:
        return "antigravity"
    if "zcode" in val:
        return "zcode"
    if "cline" in val:
        return "cline"
    if "claude" in val:
        return "claude"
    return val or "unknown"


def collect_token_monitor(
    store: TelemetryStore,
    archive_path: Path | None = None,
    active_profile: str = "unknown",
) -> dict[str, int]:
    """Ingest cross-agent session archive from Token Monitor SQLite (read-only)."""
    if archive_path is None:
        appdata = os.environ.get("APPDATA", "")
        archive_path = Path(appdata) / "Token Monitor" / "session-usage-archive.sqlite" if appdata else Path("")
    if not archive_path or not archive_path.exists():
        return {"sessions": 0, "traces_new": 0}

    mtime = archive_path.stat().st_mtime
    last_mtime, _ = store.get_watermark("token_monitor")
    if mtime <= last_mtime:
        return {"sessions": 0, "traces_new": 0}

    sessions_ingested = 0
    traces_new = 0
    try:
        con = sqlite3.connect(f"file:{archive_path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        # Token Monitor v1 schema: sessions(session_key, entry_json, revision)
        if "sessions" in tables:
            cols = {r[1] for r in con.execute("PRAGMA table_info(sessions)").fetchall()}
            if "entry_json" in cols:
                for r in con.execute("SELECT session_key, entry_json FROM sessions").fetchall():
                    skey = str(r["session_key"] or "")
                    if not skey or not r["entry_json"]:
                        continue
                    try:
                        entry = json.loads(r["entry_json"])
                    except Exception:
                        continue
                    periods = entry.get("periods") or {}
                    all_time = periods.get("allTime") or periods.get("month") or periods.get("today") or entry
                    in_u = int(all_time.get("inputTokens", 0) or 0)
                    c_r = int(all_time.get("cacheReadTokens", 0) or 0)
                    c_w = int(all_time.get("cacheWriteTokens", 0) or 0)
                    out_t = int(all_time.get("outputTokens", 0) or 0)
                    reas_t = int(all_time.get("reasoningTokens", 0) or 0)
                    tot = int(all_time.get("totalTokens", in_u + c_r + c_w + out_t) or 0)
                    calls = int(
                        all_time.get("messageCount")
                        or all_time.get("requestCount")
                        or all_time.get("calls")
                        or entry.get("calls")
                        or 1
                    )
                    cost = float(all_time.get("costUsd", 0.0) or 0.0)
                    harness = _norm_harness(str(all_time.get("client") or entry.get("client") or skey.split(":")[0]))
                    models_raw = all_time.get("models") or entry.get("models") or {}
                    if isinstance(models_raw, dict) and models_raw:
                        model = str(max(models_raw.items(), key=lambda kv: float(kv[1] or 0))[0])
                    elif isinstance(models_raw, list) and models_raw:
                        first_m = models_raw[0]
                        model = str(first_m.get("model") if isinstance(first_m, dict) else first_m)
                    else:
                        model = str(all_time.get("latestModel") or entry.get("model") or "unknown")
                    started = _iso_from_any(
                        all_time.get("startedAt")
                        or entry.get("startedAt")
                        or all_time.get("lastUsedAt")
                        or entry.get("capturedAt")
                    )
                    ended = _iso_from_any(
                        all_time.get("lastUsedAt")
                        or all_time.get("endedAt")
                        or all_time.get("updatedAt")
                        or entry.get("updatedAt")
                        or started
                    )
                    title_raw = str(all_time.get("title") or entry.get("title") or "")
                    res = store.upsert_session_with_traces(
                        {
                            "session_id": skey,
                            "harness": harness,
                            "mode": str(all_time.get("sessionKind") or entry.get("mode") or "default"),
                            "title_sanitized": sanitize_title(title_raw),
                            "primary_model": model,
                            "profile_active": active_profile,
                            "started_at": started,
                            "ended_at": ended,
                            "calls_count": calls,
                            "input_uncached": in_u,
                            "cache_read": c_r,
                            "cache_write": c_w,
                            "output_tokens": out_t,
                            "reasoning_tokens": reas_t,
                            "total_tokens": tot,
                            "cost_usd": cost,
                            "ai_credits": 0.0,
                            "source_file": str(archive_path),
                            "source_mtime": mtime,
                        },
                        traces=[],
                        write_jsonl=False,
                    )
                    sessions_ingested += 1
                    traces_new += res["traces_new"]

        if sessions_ingested == 0 and "archived_sessions" in tables:
            cols = {r[1] for r in con.execute("PRAGMA table_info(archived_sessions)").fetchall()}
            rows = con.execute("SELECT * FROM archived_sessions").fetchall()
            for r in rows:
                d = dict(r)
                payload = {}
                for json_col in ("payload_json", "data_json", "session_json", "snapshot_json"):
                    if json_col in cols and d.get(json_col):
                        try:
                            payload = json.loads(d[json_col])
                            break
                        except Exception:
                            pass
                sid = str(d.get("session_id") or d.get("id") or payload.get("sessionId") or "")
                if not sid:
                    continue
                harness = _norm_harness(str(d.get("client") or d.get("source") or payload.get("client") or sid.split(":")[0]))
                all_time = (payload.get("periods") or {}).get("allTime") or payload.get("usage") or d
                in_u = int(all_time.get("inputTokens", all_time.get("input_tokens", 0)) or 0)
                c_r = int(all_time.get("cacheReadTokens", all_time.get("cache_read_tokens", 0)) or 0)
                c_w = int(all_time.get("cacheWriteTokens", all_time.get("cache_write_tokens", 0)) or 0)
                out_t = int(all_time.get("outputTokens", all_time.get("output_tokens", 0)) or 0)
                tot = int(all_time.get("totalTokens", all_time.get("total_tokens", in_u + c_r + c_w + out_t)) or 0)
                calls = int(all_time.get("requestCount", all_time.get("calls", d.get("calls", 1))) or 1)
                cost = float(all_time.get("costUsd", all_time.get("cost_usd", 0.0)) or 0.0)
                title = sanitize_title(str(d.get("title") or payload.get("title") or ""))
                models = payload.get("models") or []
                model = str(d.get("model") or (models[0] if isinstance(models, list) and models else "unknown"))
                started = _iso_from_any(d.get("started_at") or payload.get("startedAt") or d.get("created_at"))
                ended = _iso_from_any(d.get("updated_at") or payload.get("updatedAt") or d.get("ended_at") or started)
                res = store.upsert_session_with_traces(
                    {
                        "session_id": sid,
                        "harness": harness,
                        "mode": str(payload.get("mode") or "default"),
                        "title_sanitized": title,
                        "primary_model": model,
                        "profile_active": active_profile,
                        "started_at": started,
                        "ended_at": ended,
                        "calls_count": calls,
                        "input_uncached": in_u,
                        "cache_read": c_r,
                        "cache_write": c_w,
                        "output_tokens": out_t,
                        "reasoning_tokens": 0,
                        "total_tokens": tot,
                        "cost_usd": cost,
                        "ai_credits": 0.0,
                        "source_file": str(archive_path),
                        "source_mtime": mtime,
                    },
                    traces=[],
                    write_jsonl=False,
                )
                sessions_ingested += 1
                traces_new += res["traces_new"]
        elif "archive_state" in tables or "kv" in tables or "sessions" in tables:
            # Generic fallback: inspect JSON state blobs (e.g., Token Monitor stores state JSON in a single/multi row table)
            for tbl in ("sessions", "archive_state", "kv"):
                if tbl not in tables:
                    continue
                for r in con.execute(f"SELECT * FROM {tbl}").fetchall():
                    for val in dict(r).values():
                        if not isinstance(val, str) or not val.startswith("{"):
                            continue
                        try:
                            blob = json.loads(val)
                        except Exception:
                            continue
                        sess_map = blob.get("sessions") if isinstance(blob, dict) else None
                        if isinstance(sess_map, dict):
                            items = list(sess_map.items())
                        elif isinstance(sess_map, list):
                            items = [(s.get("id") or s.get("sessionId"), s) for s in sess_map if isinstance(s, dict)]
                        else:
                            continue
                        for sid, sdata in items:
                            if not sid or not isinstance(sdata, dict):
                                continue
                            periods = sdata.get("periods") or {}
                            all_time = periods.get("allTime") or sdata
                            in_u = int(all_time.get("inputTokens", 0) or 0)
                            c_r = int(all_time.get("cacheReadTokens", 0) or 0)
                            c_w = int(all_time.get("cacheWriteTokens", 0) or 0)
                            out_t = int(all_time.get("outputTokens", 0) or 0)
                            tot = int(all_time.get("totalTokens", in_u + c_r + c_w + out_t) or 0)
                            calls = int(all_time.get("requestCount", all_time.get("calls", 1)) or 1)
                            cost = float(all_time.get("costUsd", 0.0) or 0.0)
                            harness = _norm_harness(str(sdata.get("client") or str(sid).split(":")[0]))
                            models = sdata.get("models") or []
                            model = str(sdata.get("model") or (models[0] if isinstance(models, list) and models else "unknown"))
                            started = _iso_from_any(sdata.get("startedAt") or sdata.get("createdAt"))
                            ended = _iso_from_any(sdata.get("updatedAt") or sdata.get("lastActivityAt") or started)
                            res = store.upsert_session_with_traces(
                                {
                                    "session_id": str(sid),
                                    "harness": harness,
                                    "mode": str(sdata.get("mode") or "default"),
                                    "title_sanitized": sanitize_title(str(sdata.get("title") or "")),
                                    "primary_model": model,
                                    "profile_active": active_profile,
                                    "started_at": started,
                                    "ended_at": ended,
                                    "calls_count": calls,
                                    "input_uncached": in_u,
                                    "cache_read": c_r,
                                    "cache_write": c_w,
                                    "output_tokens": out_t,
                                    "reasoning_tokens": 0,
                                    "total_tokens": tot,
                                    "cost_usd": cost,
                                    "ai_credits": 0.0,
                                    "source_file": str(archive_path),
                                    "source_mtime": mtime,
                                },
                                traces=[],
                                write_jsonl=False,
                            )
                            sessions_ingested += 1
                            traces_new += res["traces_new"]
        con.close()
        store.set_watermark("token_monitor", mtime, str(sessions_ingested))
    except Exception:
        pass
    return {"sessions": sessions_ingested, "traces_new": traces_new}


def collect_copilot_events(
    store: TelemetryStore,
    home: Path | None = None,
    active_profile: str = "unknown",
    max_files: int = 40,
) -> dict[str, int]:
    """Ingest granular per-call traces from GitHub Copilot session-state events.jsonl."""
    home = home or Path.home()
    root = home / ".copilot" / "session-state"
    if not root.exists():
        return {"sessions": 0, "traces_new": 0}

    files = sorted(
        root.glob("*/events.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:max_files]
    sessions_n = 0
    traces_new = 0

    for ev_file in files:
        mtime = ev_file.stat().st_mtime
        wm_key = f"copilot:{ev_file.parent.name}"
        last_mtime, _ = store.get_watermark(wm_key)
        if mtime <= last_mtime:
            continue

        sid = f"copilot:{ev_file.parent.name}"
        traces: list[dict[str, Any]] = []
        title = ""
        started_at = ""
        ended_at = ""
        primary_model = "unknown"
        tot_in_u = tot_cr = tot_cw = tot_out = 0
        tot_cost = tot_credits = 0.0
        turn_idx = 0
        call_idx = 0

        try:
            for line in ev_file.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                etype = str(ev.get("type") or "")
                ts = _iso_from_any(ev.get("timestamp"))
                if not started_at:
                    started_at = ts
                ended_at = ts
                data = ev.get("data") or {}

                if etype == "user.message":
                    turn_idx += 1
                elif etype == "session.title_changed":
                    title = sanitize_title(str(data.get("title") or title))
                elif etype in ("assistant.usage", "session.usage_record"):
                    call_idx += 1
                    model = str(data.get("model") or primary_model)
                    if model != "unknown":
                        primary_model = model
                    in_raw = int(data.get("inputTokens", 0) or 0)
                    c_r = int(data.get("cacheReadTokens", 0) or 0)
                    c_w = int(data.get("cacheWriteTokens", 0) or 0)
                    in_u = max(0, in_raw - c_r - c_w) if in_raw >= (c_r + c_w) else in_raw
                    out_t = int(data.get("outputTokens", 0) or 0)
                    cost = float(data.get("costUsd", 0.0) or 0.0)
                    credits = float(data.get("cost", data.get("aiCredits", 0.0)) or 0.0)
                    dur = float(data.get("duration", 0.0) or 0.0)

                    tot_in_u += in_u
                    tot_cr += c_r
                    tot_cw += c_w
                    tot_out += out_t
                    tot_cost += cost
                    tot_credits += credits

                    traces.append({
                        "trace_id": f"{sid}#c{call_idx}",
                        "turn_index": max(turn_idx, 1),
                        "call_index": call_idx,
                        "timestamp": ts,
                        "model": model,
                        "input_uncached": in_u,
                        "cache_read": c_r,
                        "cache_write": c_w,
                        "output_tokens": out_t,
                        "reasoning_tokens": 0,
                        "total_tokens": in_u + c_r + c_w + out_t,
                        "cost_usd": cost,
                        "ai_credits": credits,
                        "latency_ms": dur,
                        "tools_called": [],
                    })

            if traces:
                res = store.upsert_session_with_traces(
                    {
                        "session_id": sid,
                        "harness": "copilot",
                        "mode": "agent",
                        "title_sanitized": title or f"Copilot {ev_file.parent.name[:8]}",
                        "primary_model": primary_model,
                        "profile_active": active_profile,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "calls_count": len(traces),
                        "input_uncached": tot_in_u,
                        "cache_read": tot_cr,
                        "cache_write": tot_cw,
                        "output_tokens": tot_out,
                        "reasoning_tokens": 0,
                        "total_tokens": tot_in_u + tot_cr + tot_cw + tot_out,
                        "cost_usd": round(tot_cost, 6),
                        "ai_credits": round(tot_credits, 4),
                        "source_file": str(ev_file),
                        "source_mtime": mtime,
                    },
                    traces=traces,
                    write_jsonl=True,
                )
                sessions_n += 1
                traces_new += res["traces_new"]
            store.set_watermark(wm_key, mtime, str(len(traces)))
        except Exception:
            continue

    return {"sessions": sessions_n, "traces_new": traces_new}


def collect_codex_rollouts(
    store: TelemetryStore,
    home: Path | None = None,
    active_profile: str = "unknown",
    max_files: int = 40,
) -> dict[str, int]:
    """Ingest per-call token_count traces from Codex rollout-*.jsonl files."""
    home = home or Path.home()
    root = home / ".codex" / "sessions"
    if not root.exists():
        return {"sessions": 0, "traces_new": 0}

    files = sorted(
        root.rglob("rollout-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:max_files]
    sessions_n = 0
    traces_new = 0

    for rf in files:
        mtime = rf.stat().st_mtime
        wm_key = f"codex:{rf.stem}"
        last_mtime, _ = store.get_watermark(wm_key)
        if mtime <= last_mtime:
            continue

        sid = f"codex:{rf.stem}"
        traces: list[dict[str, Any]] = []
        started_at = ""
        ended_at = ""
        primary_model = "unknown"
        tot_in_u = tot_cr = tot_out = tot_reas = 0
        turn_idx = 0
        call_idx = 0

        try:
            for line in rf.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _iso_from_any(ev.get("timestamp"))
                if not started_at:
                    started_at = ts
                ended_at = ts
                etype = str(ev.get("type") or "")
                payload = ev.get("payload") or {}

                if etype == "turn_context":
                    primary_model = str(payload.get("model") or primary_model)
                    turn_idx += 1
                elif etype == "event_msg" and payload.get("type") == "token_count":
                    info = payload.get("info") or {}
                    last = info.get("last_token_usage") or {}
                    if not last:
                        continue
                    call_idx += 1
                    in_raw = int(last.get("input_tokens", 0) or 0)
                    c_r = int(last.get("cached_input_tokens", 0) or 0)
                    in_u = max(0, in_raw - c_r)
                    out_t = int(last.get("output_tokens", 0) or 0)
                    reas = int(last.get("reasoning_output_tokens", 0) or 0)
                    tot_in_u += in_u
                    tot_cr += c_r
                    tot_out += out_t
                    tot_reas += reas
                    traces.append({
                        "trace_id": f"{sid}#c{call_idx}",
                        "turn_index": max(turn_idx, 1),
                        "call_index": call_idx,
                        "timestamp": ts,
                        "model": primary_model,
                        "input_uncached": in_u,
                        "cache_read": c_r,
                        "cache_write": 0,
                        "output_tokens": out_t,
                        "reasoning_tokens": reas,
                        "total_tokens": in_u + c_r + out_t + reas,
                        "cost_usd": 0.0,
                        "ai_credits": 0.0,
                        "latency_ms": 0.0,
                        "tools_called": [],
                    })

            if traces:
                res = store.upsert_session_with_traces(
                    {
                        "session_id": sid,
                        "harness": "codex",
                        "mode": "cli",
                        "title_sanitized": f"Codex {rf.stem[-12:]}",
                        "primary_model": primary_model,
                        "profile_active": active_profile,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "calls_count": len(traces),
                        "input_uncached": tot_in_u,
                        "cache_read": tot_cr,
                        "cache_write": 0,
                        "output_tokens": tot_out,
                        "reasoning_tokens": tot_reas,
                        "total_tokens": tot_in_u + tot_cr + tot_out + tot_reas,
                        "cost_usd": 0.0,
                        "ai_credits": 0.0,
                        "source_file": str(rf),
                        "source_mtime": mtime,
                    },
                    traces=traces,
                    write_jsonl=True,
                )
                sessions_n += 1
                traces_new += res["traces_new"]
            store.set_watermark(wm_key, mtime, str(len(traces)))
        except Exception:
            continue

    return {"sessions": sessions_n, "traces_new": traces_new}


def collect_zcode_rollouts(
    store: TelemetryStore,
    home: Path | None = None,
    active_profile: str = "unknown",
    max_files: int = 30,
) -> dict[str, int]:
    """Ingest per-call model-io traces from ZCode rollout logs."""
    home = home or Path.home()
    candidates = [
        home / ".zcode" / "cli" / "rollout",
        home / ".zcode" / "logs",
    ]
    files: list[Path] = []
    for cdir in candidates:
        if cdir.exists():
            files.extend(cdir.glob("model-io-sess_*.jsonl"))
    files = sorted(set(files), key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]

    sessions_n = 0
    traces_new = 0
    for zf in files:
        mtime = zf.stat().st_mtime
        wm_key = f"zcode:{zf.stem}"
        last_mtime, _ = store.get_watermark(wm_key)
        if mtime <= last_mtime:
            continue

        sid = f"zcode:{zf.stem.replace('model-io-', '')}"
        traces: list[dict[str, Any]] = []
        started_at = ""
        ended_at = ""
        primary_model = "unknown"
        tot_in_u = tot_cr = tot_out = 0
        call_idx = 0

        try:
            for line in zf.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                resp = rec.get("response") or {}
                usage = resp.get("usage") or rec.get("usage") or {}
                if not usage:
                    continue
                call_idx += 1
                ts = _iso_from_any(rec.get("timestamp") or rec.get("createdAt"))
                if not started_at:
                    started_at = ts
                ended_at = ts
                req_body = (rec.get("request") or {}).get("body") or {}
                model = str(req_body.get("model") or resp.get("model") or primary_model)
                if model != "unknown":
                    primary_model = model

                in_raw = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
                c_r = int(usage.get("cache_read_input_tokens", (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)) or 0)
                in_u = max(0, in_raw - c_r)
                out_t = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
                tot_in_u += in_u
                tot_cr += c_r
                tot_out += out_t
                traces.append({
                    "trace_id": f"{sid}#c{call_idx}",
                    "turn_index": 1 if call_idx == 1 else 2,
                    "call_index": call_idx,
                    "timestamp": ts,
                    "model": model,
                    "input_uncached": in_u,
                    "cache_read": c_r,
                    "cache_write": 0,
                    "output_tokens": out_t,
                    "reasoning_tokens": 0,
                    "total_tokens": in_u + c_r + out_t,
                    "cost_usd": 0.0,
                    "ai_credits": 0.0,
                    "latency_ms": float(rec.get("durationMs", 0.0) or 0.0),
                    "tools_called": [],
                })

            if traces:
                res = store.upsert_session_with_traces(
                    {
                        "session_id": sid,
                        "harness": "zcode",
                        "mode": "desktop",
                        "title_sanitized": f"ZCode {zf.stem[-10:]}",
                        "primary_model": primary_model,
                        "profile_active": active_profile,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "calls_count": len(traces),
                        "input_uncached": tot_in_u,
                        "cache_read": tot_cr,
                        "cache_write": 0,
                        "output_tokens": tot_out,
                        "reasoning_tokens": 0,
                        "total_tokens": tot_in_u + tot_cr + tot_out,
                        "cost_usd": 0.0,
                        "ai_credits": 0.0,
                        "source_file": str(zf),
                        "source_mtime": mtime,
                    },
                    traces=traces,
                    write_jsonl=True,
                )
                sessions_n += 1
                traces_new += res["traces_new"]
            store.set_watermark(wm_key, mtime, str(len(traces)))
        except Exception:
            continue

    return {"sessions": sessions_n, "traces_new": traces_new}


def sync_all_harnesses(
    tooling_root: Path | None = None,
    home: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Run incremental read-only telemetry sync across all detected harnesses."""
    home = home or Path.home()
    root = tooling_root or Path(os.environ.get("AGENT_TOOLING_ROOT", home / ".agents" / "tooling"))
    resolved_db = db_path or (root / "state" / "registry.sqlite3")
    store = TelemetryStore(resolved_db, root / "state" / "telemetry" / "token-traces.jsonl")

    ap = get_active_profile_state(home)
    active_profile = str(ap.get("active_profile", "unknown"))

    results = {
        "token_monitor": collect_token_monitor(store, active_profile=active_profile),
        "copilot": collect_copilot_events(store, home=home, active_profile=active_profile),
        "codex": collect_codex_rollouts(store, home=home, active_profile=active_profile),
        "zcode": collect_zcode_rollouts(store, home=home, active_profile=active_profile),
    }
    total_sessions = sum(v["sessions"] for v in results.values())
    total_traces_new = sum(v["traces_new"] for v in results.values())
    return {
        "ok": True,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "active_profile": active_profile,
        "sessions_updated": total_sessions,
        "traces_new": total_traces_new,
        "by_source": results,
    }
