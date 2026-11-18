# AGENTS.md — agent-tooling

- **Stack:** Python 3.11+ (`sqlite3`, `PyYAML`), PowerShell 5.1 wrappers, Markdown.
- **Security invariant:** Never store PATs, API keys, OAuth tokens, or `state/*.sqlite3` in Git.
- **Verification:** Run `python -m pytest -v` and `python -m agent_tooling doctor` before committing.
- **Safe defaults:** `apply.ps1` and `rollback.ps1` default to `-WhatIf` (dry-run).
