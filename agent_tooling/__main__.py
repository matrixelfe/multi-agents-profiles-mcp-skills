"""CLI entry point for python -m agent_tooling / agent-tooling."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from agent_tooling.adapters.antigravity_agents import sync_antigravity_agents
from agent_tooling.db.schema import backup_db, connect, migrate
from agent_tooling.oac.reader import load_oac_snapshot
from agent_tooling.resolver.recommend import recommend
from agent_tooling.scanner.discover import (
    import_registry_yaml,
    scan_codex,
    scan_opencode,
    scan_skills_dir,
    seed_client_targets,
)
from agent_tooling.ui.server import run_server

TOOLING_ROOT = Path(os.environ.get("AGENT_TOOLING_ROOT", Path.home() / ".agents" / "tooling"))
DB_PATH = TOOLING_ROOT / "state" / "registry.sqlite3"


def cmd_scan() -> None:
    conn = connect(DB_PATH)
    try:
        migrated = migrate(conn)
        targets = seed_client_targets(conn)
        reg_count = import_registry_yaml(conn, TOOLING_ROOT / "registry.yaml")
        oc_count = scan_opencode(conn, Path.home() / ".config" / "opencode" / "opencode.json")
        codex_count = scan_codex(conn, Path.home() / ".codex" / "config.toml")
        shared_skills = scan_skills_dir(conn, Path.home() / ".agents" / "skills", "shared", "user")
        oc_skills = scan_skills_dir(conn, Path.home() / ".config" / "opencode" / "skills", "opencode", "user")
        codex_skills = scan_skills_dir(conn, Path.home() / ".codex" / "skills", "codex", "user")

        print(f"DB: {DB_PATH} (migrations applied: {migrated})")
        print(f"Targets detected: {len(targets)}")
        for tid, avail in targets.items():
            print(f"  {tid}: {avail}")
        print(f"Imported registry.yaml servers: {reg_count}")
        print(f"Scanned OpenCode MCPs: {oc_count} | Codex MCPs: {codex_count}")
        print(f"Scanned skills -> shared: {shared_skills}, opencode: {oc_skills}, codex: {codex_skills}")
    finally:
        conn.close()


def cmd_status() -> None:
    conn = connect(DB_PATH)
    try:
        migrate(conn)
        res_count = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        inst_count = conn.execute("SELECT COUNT(*) FROM installations").fetchone()[0]
        tgt_count = conn.execute("SELECT COUNT(*) FROM client_targets").fetchone()[0]
        print(f"Resources: {res_count} | Installations: {inst_count} | Client Targets: {tgt_count}")
    finally:
        conn.close()


def cmd_doctor() -> None:
    conn = connect(DB_PATH)
    try:
        migrate(conn)
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        ic = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        print(f"foreign_keys={fk} | journal_mode={jm} | integrity_check={ic}")
    finally:
        conn.close()


def cmd_backup(dest: str) -> None:
    res = backup_db(DB_PATH, Path(dest))
    print(f"Backup created at {dest} (integrity_check={res})")


def cmd_recommend(args: argparse.Namespace) -> None:
    snap = load_oac_snapshot(tooling_root=TOOLING_ROOT)
    agent_info = next(
        (a for a in snap["agents"] if a["id"] == args.agent or a["rel_path"] == args.agent),
        None,
    )
    res = recommend(
        agent_id=args.agent,
        task=args.task,
        client_target=args.client,
        project_profile=args.profile,
        tooling_root=TOOLING_ROOT,
        agent_permissions=agent_info,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", help="Read-only scan of all local clients and skills into SQLite")
    sub.add_parser("status", help="Show SQLite inventory counts")
    sub.add_parser("doctor", help="Verify SQLite integrity, foreign keys, and WAL mode")

    bkp = sub.add_parser("backup", help="Create online SQLite backup")
    bkp.add_argument("--dest", required=True, help="Destination .sqlite3 path")

    rec = sub.add_parser("recommend", help="Deterministic ECC contextual skill/subagent recommender")
    rec.add_argument("--agent", default="auto-orchestrator", help="Target agent ID")
    rec.add_argument("--task", required=True, help="Task description")
    rec.add_argument("--client", default="openchamber:opencode-runtime", help="Client surface target")
    rec.add_argument("--profile", default="core", help="Active project profile")

    ui = sub.add_parser("ui", help="Launch on-demand local Web UI for OAC, Agents, Models, MCPs & ECC")
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument("--no-browser", action="store_true")

    sag = sub.add_parser("sync-antigravity-agents", help="Project OAC/OpenCode agents into Antigravity plugin bundle")
    sag.add_argument("--dry-run", action="store_true", help="Preview without writing files")

    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan()
    elif args.command == "status":
        cmd_status()
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "backup":
        cmd_backup(args.dest)
    elif args.command == "recommend":
        cmd_recommend(args)
    elif args.command == "ui":
        run_server(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.command == "sync-antigravity-agents":
        res = sync_antigravity_agents(dry_run=args.dry_run)
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
