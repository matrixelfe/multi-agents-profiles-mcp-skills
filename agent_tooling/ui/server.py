"""On-demand local HTTP dashboard server for agent-tooling (zero external dependencies, localhost only)."""
from __future__ import annotations

import json
import os
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from agent_tooling.db.schema import connect, migrate
from agent_tooling.oac.reader import (
    _backup_file,
    load_oac_snapshot,
    update_oac_assignment,
    update_oac_retry_behavior,
)
from agent_tooling.resolver.recommend import recommend

STATIC_INDEX = Path(__file__).parent / "index.html"


def get_tooling_root() -> Path:
    return Path(os.environ.get("AGENT_TOOLING_ROOT", Path.home() / ".agents" / "tooling"))


def get_sqlite_health(tooling_root: Path) -> dict[str, Any]:
    db_path = tooling_root / "state" / "registry.sqlite3"
    if not db_path.exists():
        return {"exists": False, "db_path": str(db_path)}
    conn = connect(db_path)
    try:
        migrate(conn)
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        ic = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        res = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
        inst = conn.execute("SELECT COUNT(*) FROM installations").fetchone()[0]
        tgts = [
            dict(r)
            for r in conn.execute(
                "SELECT target_id, family, surface, scope, availability FROM client_targets ORDER BY target_id"
            ).fetchall()
        ]
        return {
            "exists": True,
            "db_path": str(db_path),
            "foreign_keys": fk,
            "journal_mode": jm,
            "integrity_check": ic,
            "resources": res,
            "installations": inst,
            "client_targets": tgts,
        }
    finally:
        conn.close()


def list_recent_backups(limit: int = 20) -> list[dict[str, Any]]:
    local_app = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    root = local_app / "agent-tooling-backups"
    if not root.exists():
        return []
    dirs = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for d in dirs[:limit]:
        mpath = d / "manifest.json"
        out.append({"change_id": d.name, "has_manifest": mpath.exists()})
    return out


def toggle_profile_mcp(profile_name: str, mcp_name: str, enabled: bool, tooling_root: Path) -> dict[str, Any]:
    pfile = tooling_root / "profiles" / f"{profile_name}.yaml"
    if not pfile.exists():
        raise FileNotFoundError(f"Profile not found: {profile_name}")
    change_id, pre_hash = _backup_file(pfile, f"ui-profile-{profile_name}")
    data = yaml.safe_load(pfile.read_text(encoding="utf-8-sig")) or {}
    mcps = list(data.get("mcp_servers") or [])
    if enabled and mcp_name not in mcps:
        mcps.append(mcp_name)
    elif not enabled and mcp_name in mcps:
        mcps.remove(mcp_name)
    data["mcp_servers"] = mcps
    tmp = pfile.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(pfile)
    return {"change_id": change_id, "profile": profile_name, "mcp_servers": mcps, "sha256_before": pre_hash}


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return  # Keep terminal clean

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        tl_root = get_tooling_root()
        if parsed.path in ("/", "/index.html"):
            html = STATIC_INDEX.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if parsed.path == "/api/snapshot":
            snap = load_oac_snapshot(tooling_root=tl_root)
            snap["sqlite"] = get_sqlite_health(tl_root)
            snap["backups"] = list_recent_backups()
            self._send_json(snap)
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        tl_root = get_tooling_root()
        try:
            body = self._read_json()
            if parsed.path == "/api/oac/assignment":
                res = update_oac_assignment(str(body["agent"]), str(body["model"]))
                self._send_json({"ok": True, "result": res})
                return

            if parsed.path == "/api/oac/retry":
                res = update_oac_retry_behavior(
                    line2_fallback_enabled=body.get("line2_fallback_enabled"),
                    go_free_allowed=body.get("go_free_allowed"),
                )
                self._send_json({"ok": True, "result": res})
                return

            if parsed.path == "/api/profile/mcp":
                res = toggle_profile_mcp(
                    str(body["profile"]),
                    str(body["mcp"]),
                    bool(body["enabled"]),
                    tl_root,
                )
                self._send_json({"ok": True, "result": res})
                return

            if parsed.path == "/api/recommend":
                snap = load_oac_snapshot(tooling_root=tl_root)
                agent_id = str(body.get("agent", "auto-orchestrator"))
                agent_info = next(
                    (a for a in snap["agents"] if a["id"] == agent_id or a["rel_path"] == agent_id),
                    None,
                )
                res = recommend(
                    agent_id=agent_id,
                    task=str(body.get("task", "")),
                    client_target=str(body.get("client_target", "openchamber:opencode-runtime")),
                    project_profile=str(body.get("project_profile", "core")),
                    tooling_root=tl_root,
                    agent_permissions=agent_info,
                )
                self._send_json({"ok": True, "result": res})
                return

            self._send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)


def run_server(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    url = f"http://{host}:{port}"
    print(f"agent-tooling UI running at {url} (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping agent-tooling UI...")
    finally:
        server.server_close()
