"""Tests for agent_tooling v3 (SQLite, migrations, scanner, adapters, redaction)."""
from __future__ import annotations

import json
from pathlib import Path

from agent_tooling.adapters.clients import (
    render_antigravity_mcp_json,
    render_claude_mcp_json,
    render_codex_toml,
    render_opencode_v2,
)
from agent_tooling.db.schema import backup_db, connect, migrate
from agent_tooling.scanner.discover import (
    import_registry_yaml,
    scan_codex,
    scan_opencode,
    scan_skills_dir,
    seed_client_targets,
)
from agent_tooling.security.redact import redact_dict


def test_migrations_idempotent_and_fk(tmp_path: Path) -> None:
    db = tmp_path / "registry.sqlite3"
    conn = connect(db)
    try:
        v1 = migrate(conn)
        assert v1 == [1, 2]
        v2 = migrate(conn)
        assert v2 == []
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk == 1
        ic = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        assert ic == "ok"
    finally:
        conn.close()


def test_backup_db_integrity(tmp_path: Path) -> None:
    db = tmp_path / "registry.sqlite3"
    conn = connect(db)
    migrate(conn)
    seed_client_targets(conn, home=tmp_path)
    conn.close()

    bkp = tmp_path / "backup.sqlite3"
    assert backup_db(db, bkp) == "ok"
    assert bkp.exists()


def test_seed_client_targets_v3(tmp_path: Path) -> None:
    conn = connect(tmp_path / "registry.sqlite3")
    migrate(conn)
    targets = seed_client_targets(conn, home=tmp_path)
    assert len(targets) == 10
    assert "claude:chat" in targets
    assert "claude:code-local" in targets
    assert "antigravity:ide" in targets
    conn.close()


def test_scan_opencode_codex_and_skills(tmp_path: Path) -> None:
    oc = tmp_path / "opencode.json"
    oc.write_text(json.dumps({"mcp": {"servers": {"cpp": {"type": "local", "disabled": True}}}}), encoding="utf-8")

    codex = tmp_path / "config.toml"
    codex.write_text('[mcp_servers.scrapling]\nenabled = false\ncommand = "scrapling-mcp.exe"\n', encoding="utf-8")

    skills = tmp_path / "skills"
    (skills / "my-skill").mkdir(parents=True)
    (skills / "my-skill" / "SKILL.md").write_text("---\nname: my-skill\n---\n", encoding="utf-8")

    conn = connect(tmp_path / "registry.sqlite3")
    migrate(conn)
    assert scan_opencode(conn, oc) == 1
    assert scan_codex(conn, codex) == 1
    assert scan_skills_dir(conn, skills, "shared", "user") == 1
    conn.close()


def test_redact_dict() -> None:
    raw = {"url": "https://example.com", "X-Goog-Api-Key": "secret123", "nested": {"pat": "ghp_abc"}}
    cleaned = redact_dict(raw)
    assert cleaned["url"] == "https://example.com"
    assert cleaned["X-Goog-Api-Key"] == "[REDACTED]"
    assert cleaned["nested"]["pat"] == "[REDACTED]"


def test_adapters_render() -> None:
    servers = {
        "cpp": {
            "transport": "stdio",
            "executable": "C:/bin/cpp.exe",
            "args": ["--stdio"],
            "supported_clients": ["opencode", "codex"],
        }
    }
    oc = json.loads(render_opencode_v2(servers))
    assert oc["mcp"]["servers"]["cpp"]["disabled"] is False
    toml = render_codex_toml(servers, ["gamedev"])
    assert "[mcp_servers.cpp]" in toml
    claude = json.loads(render_claude_mcp_json(servers))
    assert "cpp" in claude["mcpServers"]
    ag = json.loads(render_antigravity_mcp_json(servers))
    assert "cpp" in ag["mcpServers"]
