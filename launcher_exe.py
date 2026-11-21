"""Native Windows Desktop App (.exe) for Agent Tooling v3 Control Center.

Embeds the Control Center inside a native Windows WebView2 window (no browser tab)
and cleanly shuts down the embedded HTTP server with zero background processes
left behind when the window is closed.
"""
from __future__ import annotations

import os
import socket
import threading
from http.server import ThreadingHTTPServer

import webview

from agent_tooling.ui.server import DashboardHandler


def _pick_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def main() -> None:
    host = "127.0.0.1"
    port = _pick_port(8765)
    url = f"http://{host}:{port}"

    server = ThreadingHTTPServer((host, port), DashboardHandler)
    server.daemon_threads = True

    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    try:
        webview.create_window(
            title="Agent Tooling v3 — Multi-IDE Control Center",
            url=url,
            width=1420,
            height=900,
            min_size=(1024, 680),
            background_color="#111317",
        )
        webview.start(gui="edgechromium")
    finally:
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass
        # Guarantee zero lingering daemon/background processes on window close
        os._exit(0)


if __name__ == "__main__":
    main()
