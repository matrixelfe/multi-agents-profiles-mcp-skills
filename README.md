<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h1 align="center">⚡ Multi-Agent Profiles, MCP & Skills Manager</h1>
  <p align="center">
    <strong>A local, lightweight, reproducible and portable manager for MCP servers, plugins, skills, and per-project profiles across multiple AI coding agents and IDEs.</strong>
    <br />
    <br />
    <a href="https://github.com/matrixelfe/multi-agents-profiles-mcp-skills"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#the-problem">The Problem</a></li>
        <li><a href="#the-architecture">The Architecture</a></li>
        <li><a href="#supported-clients--surfaces">Supported Clients & Surfaces</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#1-read-only-environment-scan">1. Read-Only Environment Scan</a></li>
        <li><a href="#2-plan-and-apply-profiles-to-a-project">2. Plan and Apply Profiles to a Project</a></li>
        <li><a href="#3-atomic-rollback">3. Atomic Rollback</a></li>
        <li><a href="#4-database-health--backup">4. Database Health & Backup</a></li>
      </ul>
    </li>
    <li><a href="#available-profiles">Available Profiles</a></li>
    <li><a href="#security--invariants">Security & Invariants</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

When building modern software with AI coding agents (OpenCode, OpenChamber, OpenAI Codex, Claude Code, Google Antigravity), managing dozens of MCP servers (DirectX, C++, RenderDoc, Database toolboxes, Scrapers, Mobile emulators) and hundreds of specialized skills globally causes critical friction:

1. **Idle RAM & Process Bloat:** Global MCPs launch background processes on every new session, idling at 300MB–1.5GB+ RAM across multiple processes.
2. **Context Window & Token Waste:** Every session injects dozens of irrelevant tool schemas and skill descriptions into the system prompt, increasing token costs and causing tool confusion.
3. **Client Incompatibilities:** Different agents use different config formats (`opencode.jsonc`, `.codex/config.toml`, `.mcp.json`, `.agents/mcp_config.json`).

**`agent-tooling` v3** solves this by establishing a **Core Minimal Global + Cold Catalog + Per-Project Profile** system that dynamically generates native configuration for each agent.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### The Problem

```text
BEFORE (Global Bloat):
Opening a simple web app -> Launches C++ Clangd MCP + DirectX PIX MCP + RenderDoc + ETW + Android MCP
Result: 15+ irrelevant tool schemas in prompt, hundreds of MB in RAM waste, high token cost.

AFTER (agent-tooling v3):
Opening web app -> Profile 'web' activates ONLY Scrapling + Chrome DevTools + Web Skills.
Opening game recomp -> Profile 'gamedev' activates C++ + PIX + Game Player + Gamedev Skills.
Global Core: ZERO specialized MCPs running idle.
```

### The Architecture

* **Layer A — Minimal Global Core:** Zero heavy/specialized MCPs enabled globally. Minimal universal skills (5–15).
* **Layer B — Per-Repository Profiles (`profiles/*.yaml`):** Managed native configs generated on demand (`opencode.jsonc`, `.codex/config.toml`, `.mcp.json`, `.agents/mcp_config.json`). Skills linked via zero-cost NTFS junctions or verified directory copies.
* **Layer C — Cold Catalog (`~/.agents/catalog/skills/`):** Master storage for specialized skills outside the global discovery scan.
* **Layer D — Canonical SQLite Registry (`state/registry.sqlite3`):** Observed installations, inventory, capabilities, change history, and metrics.
* **Layer E — Human Knowledge:** Standard `AGENTS.md`, `.agent-docs/`, and `SKILL.md` rules preserved without duplication.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Supported Clients & Surfaces

| Client Family | Target Surface | Mode | Native Output Artifact |
|---|---|---|---|
| **OpenCode V2** | `opencode:local` | Managed | `opencode.jsonc` (`mcp.servers.*`) |
| **OpenChamber** | `openchamber:opencode-runtime` | Managed | Inherits OpenCode runtime |
| **OpenAI Codex** | `codex:local` | Managed | `.codex/config.toml` (`[mcp_servers.*]`) |
| **Claude Desktop / Code** | `claude:code-local` | Managed | `.mcp.json` (`mcpServers`) |
| **Claude Desktop / Code** | `claude:chat`, `claude:cowork`, `claude:code-cloud` | Observe Only | Documented guidance & recommendations |
| **Google Antigravity** | `antigravity:app`, `antigravity:ide`, `antigravity:cli` | Managed | `.agents/mcp_config.json` & `.agents/skills/` |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Python][Python.org]][Python-url]
* [![SQLite][SQLite.org]][SQLite-url]
* [![YAML][YAML.org]][YAML-url]
* [![PowerShell][PowerShell.com]][PowerShell-url]
* [![Bash][Bash.org]][Bash-url]
* [![Markdown][Markdown.org]][Markdown-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Follow these steps to set up `agent-tooling` in your local environment.

### Prerequisites

* **Python:** 3.11 or newer
* **PowerShell:** 5.1+ (Windows) or **Bash** (Linux / macOS / WSL2)
* **Git** installed and configured

### Installation

#### Windows (PowerShell 5.1+)
```powershell
# Clone the repository
git clone https://github.com/matrixelfe/multi-agents-profiles-mcp-skills.git
cd multi-agents-profiles-mcp-skills

# Run automated installer
.\install.ps1
```

#### Linux / macOS / WSL2
```bash
# Clone the repository
git clone https://github.com/matrixelfe/multi-agents-profiles-mcp-skills.git
cd multi-agents-profiles-mcp-skills

# Run automated installer
chmod +x install.sh && ./install.sh
```

The installer:
1. Creates `~/.agents/tooling` and cold catalog `~/.agents/catalog/skills`.
2. Deploys profiles, surface matrixes, policies, and starter `registry.yaml`.
3. Installs the Python CLI package (`agent-tooling`).
4. Executes an initial read-only discovery scan and database integrity check.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### 1. Read-Only Environment Scan

Scan all detected clients, MCP servers, and skills into SQLite without starting servers or mutating configurations:

```bash
# Run multi-client discovery scan
agent-tooling scan

# View inventory counts (resources, installations, targets)
agent-tooling status

# Verify database integrity (foreign_keys, WAL mode, integrity_check)
agent-tooling doctor
```

### 2. Plan and Apply Profiles to a Project

`apply.ps1` operates in **safe `-WhatIf` (dry-run) mode by default**.

```powershell
# 1. Preview changes without touching files (Dry-run)
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\apply.ps1" -RepoPath "C:\path\to\my-project" -Profiles web

# 2. Apply profile with automatic SHA-256 backup and junction creation
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\apply.ps1" -RepoPath "C:\path\to\my-project" -Profiles web -Apply

# 3. Combine multiple profiles (e.g. gamedev + windows-native)
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\apply.ps1" -RepoPath "C:\path\to\game-recomp" -Profiles gamedev,windows-native -Apply
```

### 3. Atomic Rollback

Every execution creates an isolated snapshot under `%LOCALAPPDATA%\agent-tooling-backups\<change-id>\` with a `manifest.json`.

```powershell
# Preview restoration (-WhatIf)
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\rollback.ps1" -ChangeId "chg-20261118-102222"

# Apply atomic rollback
powershell -File "$env:USERPROFILE\.agents\tooling\scripts\rollback.ps1" -ChangeId "chg-20261118-102222" -Apply
```

### 4. Database Health & Backup

```bash
# Perform live online SQLite backup using sqlite3.Connection.backup()
agent-tooling backup --dest "C:/path/to/backup.sqlite3"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- PROFILES -->
## Available Profiles

Profiles are defined in declarative YAML under `profiles/*.yaml`:

| Profile | Purpose | MCP Servers Included | Skills Included |
|---|---|---|---|
| **`core`** | Minimal universal baseline | `computer-use` | Universal guidelines |
| **`web`** | Frontend, fullstack, APIs | `chrome-devtools`, `scrapling`, `computer-use` | `browser-testing-with-devtools`, `frontend-ui-engineering`, `api-and-interface-design` |
| **`windows-native`** | Win32, C++, Rust, performance | `cpp`, `etw-trace-analyzer`, `computer-use` | WinDbg, profiling |
| **`android`** | Android, Flutter, mobile apps | `mobile-mcp`, `rea`, `computer-use` | Android build & debugging |
| **`gamedev`** | Games, DirectX, RenderDoc | `cpp`, `pix-mcp`, `dcc-mcp-renderdoc`, `etw-trace-analyzer`, `game-player` | 28 `gamedev-*` suite |
| **`research`** | Code analysis, scraping, PRs | `github`, `scrapling`, `computer-use` | Research workflows |
| **`reverse`** | Binary reversing, decompilation | `rea`, `craft-anything`, `computer-use` | REA & static analysis |
| **`experimental`** | Isolated tool testing | None auto-enabled | Sandbox testing |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- SECURITY -->
## Security & Invariants

* **No Secrets in Database or Git:** Authentication tokens, PATs, API keys, and Authorization headers are automatically redacted by `agent_tooling/security/redact.py` and are never committed or persisted in SQLite.
* **Scanning is Not Executing:** Running `agent-tooling scan` never launches background MCP binaries or installs packages.
* **Safe SQLite Defaults:** Enforces `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`, and `PRAGMA busy_timeout = 5000`.
* **Zero Disruption:** Core configurations, models, API providers, and existing `.agent-docs/` or `CHANGELOG.md` files are strictly preserved.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [x] Initial Phase 0-6 Architecture (OpenCode V2 + OpenChamber + Codex)
- [x] Phase 7 v3 Multi-Client Engine (Claude Desktop + Google Antigravity + SQLite)
- [x] Pinned version registry to eliminate runtime `npx` cold-start latency
- [x] Cross-client `computer-use-for-all-agents` support
- [ ] Automated GUI tray / TUI for quick profile toggling
- [ ] Exportable workspace lockfiles (`.agent-profile.lock`)

See the [open issues](https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/issues) for a full list of proposed features and active development.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions make open-source a great place to build tools for the AI agent ecosystem. Any contributions are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Run tests (`python -m pytest -v`)
4. Commit your Changes (`git commit -m 'feat: Add AmazingFeature'`)
5. Push to the Branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Edgar Sánchez — [@matrixelfe](https://github.com/matrixelfe)

Project Link: [https://github.com/matrixelfe/multi-agents-profiles-mcp-skills](https://github.com/matrixelfe/multi-agents-profiles-mcp-skills)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [othneildrew/Best-README-Template](https://github.com/othneildrew/Best-README-Template) for the README structure and standards.
* [OpenCode AI](https://opencode.ai) for the V2 MCP server specification.
* [OpenAI Codex](https://github.com/openai/codex) for the CLI agent platform.
* [Anthropic Claude Code](https://github.com/anthropics) for project-scoped MCP specifications.
* [Google Antigravity](https://deepmind.google) for agentic engineering workflows.
* [Xeakaes/computer-use-for-all-agents](https://github.com/Xeakaes/computer-use-for-all-agents) for cross-client GUI automation.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/matrixelfe/multi-agents-profiles-mcp-skills.svg?style=for-the-badge
[contributors-url]: https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/matrixelfe/multi-agents-profiles-mcp-skills.svg?style=for-the-badge
[forks-url]: https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/network/members
[stars-shield]: https://img.shields.io/github/stars/matrixelfe/multi-agents-profiles-mcp-skills.svg?style=for-the-badge
[stars-url]: https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/stargazers
[issues-shield]: https://img.shields.io/github/issues/matrixelfe/multi-agents-profiles-mcp-skills.svg?style=for-the-badge
[issues-url]: https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/issues
[license-shield]: https://img.shields.io/github/license/matrixelfe/multi-agents-profiles-mcp-skills.svg?style=for-the-badge
[license-url]: https://github.com/matrixelfe/multi-agents-profiles-mcp-skills/blob/main/LICENSE
[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[SQLite.org]: https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white
[SQLite-url]: https://www.sqlite.org/
[YAML.org]: https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white
[YAML-url]: https://yaml.org/
[PowerShell.com]: https://img.shields.io/badge/PowerShell-5391FE?style=for-the-badge&logo=powershell&logoColor=white
[PowerShell-url]: https://microsoft.com/powershell
[Bash.org]: https://img.shields.io/badge/Bash-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white
[Bash-url]: https://www.gnu.org/software/bash/
[Markdown.org]: https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white
[Markdown-url]: https://daringfireball.net/projects/markdown/
