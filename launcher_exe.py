"""Standalone Windows .exe launcher for Agent Tooling v3 Control Center.

Double-click to launch:
- If http://127.0.0.1:8765 is already running, opens the browser immediately.
- Otherwise starts the local Control Center server and opens the browser.
"""
from __future__ import annotations

import socket
import webbrowser

from agent_tooling.ui.server import run_server


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def main() -> None:
    host = "127.0.0.1"
    port = 8765
    url = f"http://{host}:{port}"
    if _is_port_open(host, port):
        webbrowser.open(url)
        return
    run_server(host=host, port=port, open_browser=True)


if __name__ == "__main__":
    main()
