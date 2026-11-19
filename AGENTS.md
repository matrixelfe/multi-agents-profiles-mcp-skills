# AGENTS.md — agent-tooling

## Core Invariants
- **Stack:** Python 3.11+ (`sqlite3`, `PyYAML`), PowerShell 5.1 / Bash wrappers, Markdown.
- **Security:** Never store PATs, API keys, OAuth tokens, credentials, or `state/*.sqlite3` in Git or SQLite. All sensitive fields must be redacted via `agent_tooling.security.redact`.
- **Verification:** Always run `python -m pytest -v` and `agent-tooling doctor` before committing changes.
- **Safe Defaults:** `apply.ps1` and `rollback.ps1` must always default to `-WhatIf` (dry-run). Real application requires explicit `-Apply`.

## README & Documentation Standard (Mandatory for All Agents)
All project README files created or updated across repositories managed by this tooling must follow the **Best-README-Template** standard (`https://github.com/othneildrew/Best-README-Template`):
1. **Top Anchor & Shields:** `<a id="readme-top"></a>` anchor with relevant badges (contributors, forks, stars, issues, license, tech stack).
2. **Project Header:** Clean title, concise one-sentence description, quick links (`Explore docs`, `Report Bug`, `Request Feature`).
3. **Table of Contents:** Collapsible `<details><summary>Table of Contents</summary>...</details>` block.
4. **About The Project:** Clear statement of the problem, architectural comparison (Before vs After), supported targets/surfaces, and `Built With` badge list.
5. **Getting Started:** Explicit prerequisites, cross-platform installation instructions (Windows PowerShell, Linux/macOS/WSL2).
6. **Usage:** Concrete CLI and script invocation examples with expected outputs.
7. **Profiles / Features Table:** Structured tables detailing capabilities, included MCPs, and skills.
8. **Security & Invariants:** Clear security policies and execution boundaries.
9. **Standard Sections:** Roadmap (checkboxes), Contributing guidelines, License, Contact/Maintainer, and Acknowledgments.
10. **Navigation:** Back-to-top links (`<p align="right">(<a href="#readme-top">back to top</a>)</p>`) at the end of each major section.
