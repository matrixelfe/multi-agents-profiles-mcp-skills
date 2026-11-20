# AGENTS.md — agent-tooling

## Core Invariants
- **Stack:** Python 3.11+ (`sqlite3`, `PyYAML`), PowerShell 5.1 / Bash wrappers, Markdown.
- **Security:** Never store PATs, API keys, OAuth tokens, credentials, or `state/*.sqlite3` in Git or SQLite. All sensitive fields must be redacted via `agent_tooling.security.redact`.
- **Verification:** Always run `python -m pytest -v` and `agent-tooling doctor` before committing changes.
- **Safe Defaults:** `apply.ps1` and `rollback.ps1` must always default to `-WhatIf` (dry-run). Real application requires explicit `-Apply`.

## Cross-Agent Project Documentation & Changelog (`.agent-docs/` + `AGENTS.md`)
Applies to **every evolving project** (web, desktop, Windows, mobile app, CLI, library, etc.) across all supported agents, **whether or not Git is initialized yet**:
- **One-Time Consent (Missing Docs):** If a project has no `.agent-docs/` directory or repo `AGENTS.md`, ask the user **once** whether to generate them and keep them updated as the project evolves.
- **One-Time Consent (Incomplete Docs):** If `.agent-docs/` exists but is incomplete, ask the user **once** whether to complete the missing documents and keep them updated.
- **Continuous Sync:** Once approved (or once `.agent-docs/` is established), automatically maintain `.agent-docs/`, `.agent-docs/CHANGELOG.md` (via `project-changelog`), and the repo `AGENTS.md` (via `project-docs`) as the project progresses.
- **Mandatory Git / GitHub Inclusion:** Every commit or push to Git / GitHub **MUST** stage and include updated `.agent-docs/` (including `CHANGELOG.md`) and `AGENTS.md`. If the project does not have Git initialized yet, continue maintaining `.agent-docs/` normally on disk; as soon as Git is initialized, `.agent-docs/` and `AGENTS.md` **MUST** be tracked and included from the first commit onward.

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
