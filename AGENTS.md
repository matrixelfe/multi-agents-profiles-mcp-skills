# Unified Cross-Agent Environment & Persistence Contract (`~/.agents/AGENTS.md`)

> Single Source of Truth for **OpenCode V2, OpenChamber, Codex CLI, Claude Code, and Google Antigravity**.
>
> **Agent-Guided Onboarding:** If a user asks you *"instálame este repo"* or *"configure this framework"*, follow **[INSTALL-WITH-AGENT.md](INSTALL-WITH-AGENT.md)** and **[manifests/skills-catalog-by-profile.md](manifests/skills-catalog-by-profile.md)**: install the base framework + Vercel `find-skills`, ask the user which skill profiles they want (Core/Superpowers, Fullstack/UI, GameDev, Engineering/Security, Mobile, Reverse, or All), install via `npx skills add`, and auto-repair/consolidate into the Cold Vault (`~/.agents/catalog/skills/`).

## 1. Shared Environment & Paths (Windows)
- **Active Skills Repository (`~/.agents/skills`):** Linked via NTFS junction to Antigravity (`~/.gemini/config/skills`), GitHub Copilot (`~/.copilot/skills`), Claude (`~/.claude/skills`), and OpenCode. Controlled by the active profile (`core`, `web`, `gamedev`, etc.) to keep sessions fast, un-truncated, and under context token budgets.
- **Cold Skill Vault (`~/.agents/catalog/skills`):** Master repository holding all 359+ installed skills.
  - **Just-in-Time (JIT) Skill Activation:** Any agent can read and execute any specialized skill directly from `C:\Users\edgar\.agents\catalog\skills\<skill-name>\SKILL.md` whenever needed, without requiring it to be preloaded globally in the active session.
  - **Global Profile Switch:** When starting a specialized session (e.g. web, gamedev, reverse), switch profiles with `agent-tooling switch-profile <name>` or via the Control Center UI (`http://127.0.0.1:8765`).
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
  - `agent-tooling sync-instructions` *(propagates this file into all 5 harnesses via `BEGIN/END` managed blocks without overwriting native harness rules)*
  - `agent-tooling recommend --agent <id> --task "<task>" --profile <profile>`
  - `agent-tooling switch-profile <profile>`
  - `agent-tooling ui` (local Control Center at `http://127.0.0.1:8765`)

## 4. Shared Behavior & 3-Layer Instructions Hierarchy
To share global rules across **OpenCode/OpenChamber, Codex CLI, Claude Code, GitHub Copilot, and Google Antigravity** without causing drift or deleting harness-specific rules, follow this 3-layer cascade:
1. **Layer 1 — Canonical Global Contract (`~/.agents/AGENTS.md`):** Single Source of Truth for universal rules (active skills & Cold Vault JIT, `pmb-shared`, `agent-browser`, `.agent-docs/` + `CHANGELOG.md`, zero secrets). Edit ONLY here.
2. **Layer 2 — Harness-Native Files (Managed Block Injection):** Each harness keeps its own native global file (`~/.config/opencode/AGENTS.md`, `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.copilot/copilot-instructions.md`, `~/.gemini/config/plugins/oac-custom-agents/rules/AGENTS.md`). Running `agent-tooling sync-instructions` updates ONLY the `<!-- BEGIN:UNIFIED-AGENTS --> ... <!-- END:UNIFIED-AGENTS -->` block inside each file (with SHA-256 backup), preserving all harness-specific instructions outside the block.
3. **Layer 3 — Project-Local `AGENTS.md`:** Every repository keeps its own `AGENTS.md` (maintained by `project-docs`) for repo stack, commands, and architecture; it layers on top of the global rules and is never overwritten by `sync-instructions`.
- **Feedback Loop (Two Speeds):** Day-to-day learnings, facts, and decisions go to **PMB (`pmb-shared`, workspace `personal`)** so `~/.agents/AGENTS.md` stays compact. Only recurring, high-confidence patterns distilled via PMB / `ecc-homunculus` instincts are promoted into `~/.agents/AGENTS.md` and synced with `agent-tooling sync-instructions`.
