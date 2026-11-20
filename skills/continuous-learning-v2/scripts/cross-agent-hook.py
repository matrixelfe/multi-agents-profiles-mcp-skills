"""
Continuous Learning v2 - Cross-Agent Hook Adapter (OpenCode, Codex, Claude Code)
Compatible with Windows, Linux, macOS.

Receives hook JSON on stdin (or via CLI args) and records observation events
into the project/global instinct storage directory.
"""

import sys
import os
import json
import hashlib
import time
from pathlib import Path

def get_homunculus_dir() -> Path:
    # Match homunculus-dir.sh logic:
    # Prefer $XDG_DATA_HOME/ecc-homunculus or ~/.local/share/ecc-homunculus
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        base = Path(xdg) / "ecc-homunculus"
    else:
        base = Path.home() / ".local" / "share" / "ecc-homunculus"
    base.mkdir(parents=True, exist_ok=True)
    return base

def detect_project(cwd: Path) -> tuple[str, str, Path]:
    """Returns (project_id, project_name, project_dir)"""
    git_dir = cwd
    while git_dir != git_dir.parent:
        if (git_dir / ".git").exists():
            break
        git_dir = git_dir.parent

    if (git_dir / ".git").exists():
        # Hash repo root
        root_path = str(git_dir.resolve()).lower()
        proj_hash = hashlib.sha256(root_path.encode()).hexdigest()[:12]
        proj_name = git_dir.name
        homunculus = get_homunculus_dir()
        proj_dir = homunculus / "projects" / proj_hash
        proj_dir.mkdir(parents=True, exist_ok=True)
        return proj_hash, proj_name, proj_dir

    # Fallback to global
    homunculus = get_homunculus_dir()
    global_dir = homunculus / "global"
    global_dir.mkdir(parents=True, exist_ok=True)
    return "global", "global", global_dir

def handle_hook(phase: str, hook_input: dict):
    cwd_str = hook_input.get("cwd") or os.getcwd()
    cwd = Path(cwd_str)
    proj_id, proj_name, proj_dir = detect_project(cwd)

    obs_dir = proj_dir / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    obs_file = obs_dir / f"obs_{timestamp}_{os.getpid()}.jsonl"

    record = {
        "timestamp": timestamp,
        "phase": phase,
        "project_id": proj_id,
        "project_name": proj_name,
        "data": hook_input
    }

    try:
        with open(obs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.stderr.write(f"[CLv2] Error writing observation: {e}\n")

def main():
    phase = "post"
    if len(sys.argv) > 1:
        phase = sys.argv[1].lower()

    try:
        raw = sys.stdin.read().strip()
        if raw:
            data = json.loads(raw)
        else:
            data = {}
    except Exception:
        data = {}

    handle_hook(phase, data)
    # Output empty response to continue
    print(json.dumps({}))

if __name__ == "__main__":
    main()
