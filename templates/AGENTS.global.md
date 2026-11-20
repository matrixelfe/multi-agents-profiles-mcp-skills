# Unified Cross-Agent Environment & Persistence Contract (`~/.agents/AGENTS.md`)

> Single Source of Truth for **OpenCode V2, OpenChamber, Codex CLI, Claude Code, and Google Antigravity**.

## 1. Shared Environment & Paths
- **Central Skills Repository:** `~/.agents/skills/` (shared across all IDEs and CLI agents; link via symlink/NTFS junction where supported). Always install, update, and read custom skills here—never scatter duplicates across client-isolated folders.
- **Cold Skill Catalog:** `~/.agents/catalog/skills/` (specialized skill packs linked per-repo on demand).
- **Tooling & Governance Engine (`agent-tooling` v3):** `~/.agents/tooling/`
  - **SQLite Registry (Observed State & History):** `~/.agents/tooling/state/registry.sqlite3` (`WAL`, `foreign_keys=ON`, zero secrets).
  - **Declarative Profiles:** `~/.agents/tooling/profiles/*.yaml` (`core`, `web`, `gamedev`, `windows-native`, `android`, `research`, `reverse`, `experimental`, `browser-automation`).
  - **Contextual Recommendations:** `~/.agents/tooling/recommendations.yaml`.

## 2. Single Persistence & Update Contract
1. **SQLite** stores observed inventory, installations, client targets, and history (never edit manually; update with `agent-tooling scan`).
2. **YAML** stores declarative desired state (`profiles/*.yaml`, `policy.yaml`, `recommendations.yaml`).
3. **Markdown** stores human knowledge (`AGENTS.md`, `SKILL.md`, `.agent-docs/`, `CHANGELOG.md`).
4. **Native Client Configs** (`opencode.jsonc`, `.codex/config.toml`, `.mcp.json`, `.agents/mcp_config.json`) are generated outputs—never duplicate editable state in two places.
5. **Zero Secrets:** Never store PATs, API keys, OAuth tokens, or cookies in Git, SQLite, reports, or prompts.

## 3. Core Cross-Agent Workflows
- **Documentation Standard:** Project `README.md` files should follow `othneildrew/Best-README-Template`.
- **Cross-Agent Project Documentation & Changelog (`.agent-docs/` + `AGENTS.md`):**
  - Applies to **every evolving project** (web, desktop, Windows, mobile app, CLI, library, etc.), **with or without Git initialized**.
  - **One-Time Consent:** If a project has no `.agent-docs/` (or repo `AGENTS.md`), ask the user **once** whether to generate it and keep it updated as the project evolves. If `.agent-docs/` exists but is incomplete, ask **once** whether to complete it. Once approved, keep `.agent-docs/`, `.agent-docs/CHANGELOG.md` (via `project-changelog`), and repo `AGENTS.md` (via `project-docs`) updated automatically as the project progresses.
  - **Mandatory Git / GitHub Inclusion:** Every commit or push to Git/GitHub **MUST** stage and include updated `.agent-docs/` (including `CHANGELOG.md`) and `AGENTS.md`. If a project has no Git yet, continue maintaining `.agent-docs/` normally; as soon as Git is initialized, `.agent-docs/` and `AGENTS.md` **MUST** be tracked and included from the first commit onward.
- **Conventional Commits:** Use Conventional Commits 1.0.0 (`conventional-commits` skill) for all Git commit messages.
- **Management Commands:**
  - `agent-tooling scan` / `status` / `doctor`
  - `agent-tooling recommend --agent <id> --task "<task>" --profile <profile>`
  - `agent-tooling ui` (local Control Center)
