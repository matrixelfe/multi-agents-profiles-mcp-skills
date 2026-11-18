"""CLI entry point for python -m agent_tooling."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from agent_tooling.db.schema import backup_db, connect, migrate
from agent_tooling.scanner.discover import (
    import_registry_yaml,
    scan_codex,
    scan_opencode,
    scan_skills_dir,
    seed_client_targets,
)

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


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent_tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", help="Read-only scan of all local clients and skills into SQLite")
    sub.add_parser("status", help="Show SQLite inventory counts")
    sub.add_parser("doctor", help="Verify SQLite integrity, foreign keys, and WAL mode")
    bkp = sub.add_parser("backup", help="Create online SQLite backup")
    bkp.add_argument("--dest", required=True, help="Destination .sqlite3 path")

    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan()
    elif args.command == "status":
        cmd_status()
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "backup":
        cmd_backup(args.dest)


if __name__ == "__main__":
    main()
