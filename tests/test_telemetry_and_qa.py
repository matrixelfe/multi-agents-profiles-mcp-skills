"""Unit, security, collector, profile, and HTTP API tests for Token Telemetry & QA."""
from __future__ import annotations

import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from agent_tooling.db.schema import connect, migrate
from agent_tooling.profile_switcher import switch_active_profile
from agent_tooling.telemetry.analyzer import analyze_session_traces, sanitize_title
from agent_tooling.telemetry.collectors import (
    collect_codex_rollouts,
    collect_copilot_events,
    collect_zcode_rollouts,
)
from agent_tooling.telemetry.exporter import export_report
from agent_tooling.telemetry.store import TelemetryStore
from agent_tooling.ui.server import DashboardHandler


def test_migration_v3_idempotent_and_integrity(tmp_path: Path) -> None:
    db = tmp_path / "registry.sqlite3"
    conn = connect(db)
    try:
        applied1 = migrate(conn)
        assert 3 in applied1
        applied2 = migrate(conn)
        assert applied2 == []
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert {"token_sessions", "token_traces", "token_anomalies", "telemetry_watermarks"}.issubset(tables)
        assert conn.execute("PRAGMA integrity_check;").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
    finally:
        conn.close()


def test_anomaly_detector_rules() -> None:
    session = {
        "session_id": "ses_test_anomalies",
        "harness": "copilot",
        "total_tokens": 1_250_000,
        "cost_usd": 2.45,
        "calls_count": 28,
        "ended_at": "2026-11-21T12:00:00Z",
    }
    traces = [
        # Turn 1 double call (short output)
        {"trace_id": "t1", "turn_index": 1, "call_index": 1, "input_uncached": 38500, "cache_read": 0, "output_tokens": 25, "tools_called": ["rename_session"]},
        {"trace_id": "t2", "turn_index": 1, "call_index": 2, "input_uncached": 38565, "cache_read": 0, "output_tokens": 40, "tools_called": []},
        # High cache read followed by cache break + context bloat > 80K
        {"trace_id": "t3", "turn_index": 2, "call_index": 3, "input_uncached": 5000, "cache_read": 72000, "output_tokens": 300, "tools_called": ["read_file"]},
        {"trace_id": "t4", "turn_index": 2, "call_index": 4, "input_uncached": 76000, "cache_read": 6500, "output_tokens": 300, "tools_called": ["read_file"]},
        # Tool loop (4 consecutive read_file calls: t3, t4, t5, t6)
        {"trace_id": "t5", "turn_index": 2, "call_index": 5, "input_uncached": 4000, "cache_read": 60000, "output_tokens": 120, "tools_called": ["read_file"]},
        {"trace_id": "t6", "turn_index": 2, "call_index": 6, "input_uncached": 4000, "cache_read": 60000, "output_tokens": 120, "tools_called": ["read_file"]},
    ]
    updated, anomalies = analyze_session_traces(session, traces)
    rules = {a["rule_code"] for a in anomalies}
    assert "OUTLIER_SESSION" in rules
    assert "DOUBLE_CALL_TURN1" in rules
    assert "CACHE_BREAK" in rules
    assert "CONTEXT_BLOAT" in rules
    assert "TOOL_LOOP" in rules
    assert "DOUBLE_CALL_TURN1" in updated[1]["anomaly_flags"]
    assert "CACHE_BREAK" in updated[3]["anomaly_flags"]
    assert "TOOL_LOOP" in updated[5]["anomaly_flags"]


def test_zero_secrets_and_jsonl_rotation(tmp_path: Path) -> None:
    dirty = "Auth sk-1234567890abcdefghijklmnop and ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
    clean = sanitize_title(dirty)
    assert "sk-1234567890" not in clean
    assert "ghp_ABCDEF" not in clean

    log_path = tmp_path / "telemetry" / "token-traces.jsonl"
    store = TelemetryStore(tmp_path / "registry.sqlite3", trace_log_path=log_path, max_log_bytes=350)
    for i in range(4):
        store.upsert_session_with_traces(
            {
                "session_id": f"ses_rot_{i}",
                "harness": "opencode",
                "title_sanitized": dirty,
                "primary_model": "gpt-6-luna",
                "started_at": "2026-11-21T10:00:00Z",
                "ended_at": "2026-11-21T10:01:00Z",
                "calls_count": 1,
                "input_uncached": 12000,
                "cache_read": 0,
                "output_tokens": 50,
                "total_tokens": 12050,
            },
            traces=[{
                "trace_id": f"ses_rot_{i}#c1",
                "turn_index": 1,
                "call_index": 1,
                "timestamp": "2026-11-21T10:00:30Z",
                "model": "gpt-6-luna",
                "input_uncached": 12000,
                "cache_read": 0,
                "output_tokens": 50,
                "total_tokens": 12050,
            }],
        )
    assert log_path.exists()
    rotated = log_path.with_name("token-traces.1.jsonl")
    assert rotated.exists()
    for p in (log_path, rotated):
        txt = p.read_text(encoding="utf-8")
        assert "sk-1234567890" not in txt
        assert "ghp_ABCDEF" not in txt


def test_collectors_idempotent_watermarks(tmp_path: Path) -> None:
    home = tmp_path / "home"
    store = TelemetryStore(tmp_path / "registry.sqlite3", tmp_path / "token-traces.jsonl")

    # 1. Copilot fixture
    cp_dir = home / ".copilot" / "session-state" / "1823f03d-test"
    cp_dir.mkdir(parents=True)
    (cp_dir / "events.jsonl").write_text(
        "\n".join([
            json.dumps({"type": "user.message", "timestamp": "2026-11-21T10:00:00Z", "data": {}}),
            json.dumps({"type": "session.title_changed", "timestamp": "2026-11-21T10:00:01Z", "data": {"title": "Saludo"}}),
            json.dumps({"type": "assistant.usage", "timestamp": "2026-11-21T10:00:02Z", "data": {"model": "claude-sonnet-4.6", "inputTokens": 38506, "cacheReadTokens": 35000, "outputTokens": 40, "cost": 0.18}}),
            json.dumps({"type": "assistant.usage", "timestamp": "2026-11-21T10:00:04Z", "data": {"model": "claude-sonnet-4.6", "inputTokens": 38565, "cacheReadTokens": 35000, "outputTokens": 84, "cost": 0.19}}),
        ]) + "\n",
        encoding="utf-8",
    )

    # 2. Codex fixture
    cx_dir = home / ".codex" / "sessions" / "2026" / "11" / "21"
    cx_dir.mkdir(parents=True)
    (cx_dir / "rollout-2026-11-21-test.jsonl").write_text(
        "\n".join([
            json.dumps({"type": "turn_context", "timestamp": "2026-11-21T10:05:00Z", "payload": {"model": "gpt-5.4"}}),
            json.dumps({"type": "event_msg", "timestamp": "2026-11-21T10:05:03Z", "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 28709, "cached_input_tokens": 26240, "output_tokens": 64}}}}),
        ]) + "\n",
        encoding="utf-8",
    )

    # 3. ZCode fixture
    zc_dir = home / ".zcode" / "cli" / "rollout"
    zc_dir.mkdir(parents=True)
    (zc_dir / "model-io-sess_test1.jsonl").write_text(
        json.dumps({"timestamp": "2026-11-21T10:10:00Z", "request": {"body": {"model": "glm-5-turbo"}}, "response": {"usage": {"input_tokens": 27533, "cache_read_input_tokens": 0, "output_tokens": 110}}}) + "\n",
        encoding="utf-8",
    )

    r1_cp = collect_copilot_events(store, home=home, active_profile="core-lean")
    r1_cx = collect_codex_rollouts(store, home=home, active_profile="core-lean")
    r1_zc = collect_zcode_rollouts(store, home=home, active_profile="core-lean")
    assert r1_cp["sessions"] == 1 and r1_cp["traces_new"] == 2
    assert r1_cx["sessions"] == 1 and r1_cx["traces_new"] == 1
    assert r1_zc["sessions"] == 1 and r1_zc["traces_new"] == 1

    # Second run must be a no-op via watermark
    assert collect_copilot_events(store, home=home)["traces_new"] == 0
    assert collect_codex_rollouts(store, home=home)["traces_new"] == 0
    assert collect_zcode_rollouts(store, home=home)["traces_new"] == 0

    summary = store.get_summary()
    assert summary["kpis"]["sessions_count"] == 3
    assert summary["kpis"]["calls_count"] == 4
    md, mime, ext = export_report(summary, store.list_sessions(), store.list_anomalies(), fmt="md")
    assert ext == "md" and "Reporte de Telemetría" in md and "text/markdown" in mime
    csv_txt, _, csv_ext = export_report(summary, store.list_sessions(), store.list_anomalies(), fmt="csv")
    assert csv_ext == "csv" and "session_id" in csv_txt


def test_core_lean_profile_exposes_only_6_skills(tmp_path: Path) -> None:
    home = tmp_path / "fakehome"
    cold = home / ".agents" / "catalog" / "skills"
    profiles = home / ".agents" / "tooling" / "profiles"
    profiles.mkdir(parents=True)
    for name in (
        "find-skills",
        "verification-before-completion",
        "systematic-debugging",
        "code-review-and-quality",
        "project-docs",
        "project-changelog",
        "using-superpowers",
        "brainstorming",
        "frontend-design",
    ):
        (cold / name).mkdir(parents=True)
        (cold / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

    (profiles / "core-lean.yaml").write_text(
        "profile: core-lean\nskills:\n  - find-skills\n  - verification-before-completion\n"
        "  - systematic-debugging\n  - code-review-and-quality\n  - project-docs\n  - project-changelog\n",
        encoding="utf-8",
    )

    res = switch_active_profile("core-lean", home=home, dry_run=False)
    assert res["active_profile"] == "core-lean"
    assert res["active_skills_count"] == 6
    assert res["catalog_skills_count"] == 9
    active_names = sorted(p.name for p in (home / ".agents" / "skills").iterdir())
    assert "using-superpowers" not in active_names
    assert len(active_names) == 6


def test_telemetry_http_api_and_ui_tab(tmp_path: Path, monkeypatch) -> None:
    tl_root = tmp_path / "tooling"
    db_path = tl_root / "state" / "registry.sqlite3"
    store = TelemetryStore(db_path, tl_root / "state" / "telemetry" / "token-traces.jsonl")
    store.upsert_session_with_traces(
        {
            "session_id": "ses_api_1",
            "harness": "opencode",
            "mode": "build",
            "title_sanitized": "API QA Session",
            "primary_model": "gpt-6-luna",
            "profile_active": "core-lean",
            "started_at": "2026-11-21T11:00:00Z",
            "ended_at": "2026-11-21T11:01:00Z",
            "calls_count": 1,
            "input_uncached": 14500,
            "cache_read": 0,
            "output_tokens": 60,
            "total_tokens": 14560,
            "cost_usd": 0.0,
        },
        traces=[{
            "trace_id": "ses_api_1#c1",
            "turn_index": 1,
            "call_index": 1,
            "timestamp": "2026-11-21T11:00:10Z",
            "model": "gpt-6-luna",
            "input_uncached": 14500,
            "cache_read": 0,
            "output_tokens": 60,
            "total_tokens": 14560,
        }],
    )
    monkeypatch.setenv("AGENT_TOOLING_ROOT", str(tl_root))

    server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        html = urllib.request.urlopen(f"{base}/").read().decode("utf-8")
        assert 'id="tab-telemetry"' in html
        assert 'id="nav-telemetry"' in html

        sum_resp = json.loads(urllib.request.urlopen(f"{base}/api/telemetry/summary").read().decode("utf-8"))
        assert sum_resp["ok"] is True
        assert sum_resp["result"]["kpis"]["total_tokens"] == 14560

        ses_resp = json.loads(urllib.request.urlopen(f"{base}/api/telemetry/sessions").read().decode("utf-8"))
        assert len(ses_resp["sessions"]) == 1

        trc_resp = json.loads(urllib.request.urlopen(f"{base}/api/telemetry/traces?session_id=ses_api_1").read().decode("utf-8"))
        assert len(trc_resp["result"]["traces"]) == 1

        log_resp = json.loads(urllib.request.urlopen(f"{base}/api/telemetry/log").read().decode("utf-8"))
        assert len(log_resp["entries"]) == 1

        exp_md = urllib.request.urlopen(f"{base}/api/telemetry/export?format=md").read().decode("utf-8")
        assert "Reporte de Telemetría" in exp_md
    finally:
        server.shutdown()
        server.server_close()
