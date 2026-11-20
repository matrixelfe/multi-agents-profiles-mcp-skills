# Unified Cross-Agent Environment & Persistence Contract (`~/.agents/AGENTS.md`)

> Single Source of Truth for **OpenCode V2, OpenChamber, Codex CLI, Claude Code, and Google Antigravity**.

## 1. Shared Environment & Paths (Windows)
- **Central Skills Repository:** `C:\Users\edgar\.agents\skills\` (shared across all IDEs; linked via NTFS junction to `~/.gemini/config/skills`). Always install, update, and read custom skills here—never scatter duplicates across client-isolated folders.
- **Cold Skill Catalog:** `C:\Users\edgar\.agents\catalog\skills\` (specialized packages like the 28 `gamedev-*` skills; linked per-repo on demand via NTFS junctions).
- **Tooling & Governance Engine (`agent-tooling` v3):** `C:\Users\edgar\.agents\tooling\`
  - **SQLite Registry (Observed State & History):** `C:\Users\edgar\.agents\tooling\state\registry.sqlite3` (`WAL`, `foreign_keys=ON`, zero secrets).
  - **Declarative Profiles:** `C:\Users\edgar\.agents\tooling\profiles\*.yaml` (`core`, `web`, `gamedev`, `windows-native`, `android`, `research`, `reverse`, `experimental`, `browser-automation`).
  - **ECC Contextual Recommendations:** `C:\Users\edgar\.agents\tooling\recommendations.yaml`.
  - **Private Backups & Rollback:** `%LOCALAPPDATA%\agent-tooling-backups\<change-id>\` (SHA-256 verified).

## 2. Single Persistence & Update Contract
1. **SQLite** stores observed inventory, installations, client targets, and history (never edit manually; update with `agent-tooling scan`).
2. **YAML** stores declarative desired state (`profiles/*.yaml`, `policy.yaml`, `recommendations.yaml`, `config/oac-routing.yaml`).
3. **Markdown** stores human knowledge (`AGENTS.md`, `SKILL.md`, `.agent-docs/`, `CHANGELOG.md`).
4. **Native Client Configs** (`opencode.jsonc`, `.codex/config.toml`, `.mcp.json`, `.agents/mcp_config.json`) are generated outputs—never duplicate editable state in two places.
5. **Zero Secrets:** Never store PATs, API keys, OAuth tokens, or cookies in Git, SQLite, reports, or prompts.

## 3. Core Capabilities & Routing Rules
- **OAC V3.4 Governance:** `config/oac-routing.yaml` is the sole authority for model routing and fallbacks. **PAYG Spend Guard (`DENY`)** is strictly protected; never edit `state/oac/quota-state.json`.
- **Browser Automation (`browser-automation`):** Prefer `agent-browser` CLI + Skill (`snapshot -i`, isolated sessions, `close` on finish; quote `'@eN'` refs in PowerShell 5.1) for navigation, forms, and dynamic web extraction. Escalate to `chrome-devtools` for console/network/perf, `Playwright Test` for maintainable E2E, and `computer-use` for native Windows apps.
- **Documentation Standard:** Project `README.md` files must follow `othneildrew/Best-README-Template`.
- **Cross-Agent Project Documentation & Changelog (`.agent-docs/` + `AGENTS.md`):**
  - Applies to **every evolving project** (web, Windows, app, CLI, etc.), **with or without Git initialized**.
  - **One-Time Consent:** If a project has no `.agent-docs/` (or repo `AGENTS.md`), ask the user **once** whether to generate it and keep it updated as the project evolves. If `.agent-docs/` exists but is incomplete, ask **once** whether to complete it. Once approved, keep `.agent-docs/`, `.agent-docs/CHANGELOG.md` (via `project-changelog`), and repo `AGENTS.md` (via `project-docs`) updated automatically as the project progresses.
  - **Mandatory Git / GitHub Inclusion:** Every commit or push to Git/GitHub **MUST** stage and include updated `.agent-docs/` (including `CHANGELOG.md`) and `AGENTS.md`. If a project has no Git yet, continue maintaining `.agent-docs/` normally; as soon as Git is initialized, `.agent-docs/` and `AGENTS.md` **MUST** be tracked and included in commits.
- **Management Commands:**
  - `agent-tooling scan` / `status` / `doctor`
  - `agent-tooling recommend --agent <id> --task "<task>" --profile <profile>`
  - `agent-tooling sync-antigravity-agents`
  - `agent-tooling ui` (local Control Center at `http://127.0.0.1:8765`)
