# Installation & Cross-Harness Notes (Skills, Plugins, Hooks & MCPs)

Single-source reference for installing, wiring, and verifying every cross-agent skill, plugin, hook, and MCP server in this ecosystem (**OpenCode / OpenChamber**, **Codex CLI**, **Claude Code**, **GitHub Copilot CLI**, **Google Antigravity**, and **Gemini CLI**).

> **Important (Cold Skill Vault Rule):** Store master skill folders inside `~/.agents/catalog/skills/<skill-name>` and point any direct IDE junctions or hook scripts to `catalog/skills/` (never to `~/.agents/skills/` directly, since active profile switches recreate `~/.agents/skills/`).

---

## 1. PMB — Local-First Cross-Agent Memory (`pmb-shared` MCP + `pmb-memory` Skill)

- **Upstream:** [https://github.com/oleksiijko/pmb](https://github.com/oleksiijko/pmb)
- **Purpose:** Persistent local memory backed by SQLite + LanceDB + BM25 shared across all agents (`PMB_WORKSPACE=personal`).

### Install
```powershell
uv tool install pmb-ai
pmb warmup
pmb doctor
```

### Wire Cross-Harness
- **MCP Server (`pmb-shared`):** Configure `pmb workspace use personal`, `pmb config set daemon.idle_exit_min 0 --global`, start `pmb daemon start --host 127.0.0.1 --port 8765`, and register `~/.local/bin/pmb.exe` with `["mcp", "proxy", "--no-fallback"]` using `templates/mcp-cross-agent.json` (shares one warm daemon instead of loading ~1.2 GiB RAM per client).
- **Hooks (Claude Code):** `pmb connect claude-code --workspace personal --active` registers `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and `Stop` hooks in `~/.claude/settings.json`.
- **Skill:** Copy `skills/pmb-memory/` to `~/.agents/catalog/skills/pmb-memory/`.

### Verify
```powershell
pmb doctor
pmb stats
```

---

## 2. RTK (Rust Token Killer) — Cross-Harness Shell Output Compressor

- **Upstream:** [https://github.com/rtk-ai/rtk](https://github.com/rtk-ai/rtk)
- **Purpose:** Native Rust hook engine (<25 ms) that compresses verbose shell output (tests, builds, diffs, git) by 60%–90% before reaching the LLM.

### Install Binary (Windows)
Download `rtk-x86_64-pc-windows-msvc.zip` from GitHub Releases into `~/.local/bin/rtk.exe` (or `winget install rtk-ai.rtk`).

### Register Hooks Across All Harnesses
```powershell
# Claude Code (~/.claude/settings.json PreToolUse + ~/.claude/RTK.md)
rtk init --global --auto-patch

# OpenCode / OpenChamber (~/.config/opencode/plugins/rtk.ts)
rtk init --global --opencode --auto-patch

# OpenAI Codex CLI (~/.codex/hooks.json PreToolUse + ~/.codex/RTK.md)
rtk init --global --codex

# Google Antigravity (~/.gemini/config/plugins/rtk/hooks.json + rules/AGENTS.md)
rtk init --global --agent antigravity --auto-patch

# GitHub Copilot CLI (~/.copilot/hooks/rtk-rewrite.json + copilot-instructions.md)
rtk init --global --copilot

# Gemini CLI (~/.gemini/hooks/rtk-hook-gemini.sh + ~/.gemini/GEMINI.md)
rtk init --global --gemini --auto-patch
```

### Bundled Skills
Copy `skills/rtk-tdd/` and `skills/rtk-triage/` into `~/.agents/catalog/skills/`.

### Verify
```powershell
rtk --version
rtk init --show
rtk hook check "git status"
rtk gain
```

---

## 3. OpenSlimedit — OpenCode / OpenChamber Token Optimizer Plugin

- **Upstream:** [https://github.com/ASidorenkoCode/openslimedit](https://github.com/ASidorenkoCode/openslimedit)
- **Scope:** **OpenCode / OpenChamber only** (relies on OpenCode's `tool.definition`, `tool.execute.before`, and `tool.execute.after` hooks).
- **Purpose:** Compresses built-in tool descriptions, strips boilerplate from file reads, and adds line-range edit expansion (`"55-64"`).

### Install
```powershell
Copy-Item plugins/openslimedit/openslimedit.ts "$HOME\.config\opencode\plugins\openslimedit.ts" -Force
```

---

## 4. Headroom — Transversal Context Compression Layer

- **Upstream:** [https://github.com/headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom)
- **Scope:** **Cross-harness** (OpenCode, Codex, Claude Code, Copilot, Cursor, Antigravity, Python/TS SDK).
- **Purpose:** Compresses large tool outputs, JSON arrays, logs, and chat history (21%–57% fewer input tokens) while preserving errors and stack traces verbatim.

### Install
```powershell
uv tool install --python 3.13 headroom-ai
```

### Usage (Experimental / On-Demand)
```powershell
# Wrap any coding agent transparently
headroom wrap opencode
headroom wrap codex
headroom wrap claude

# Or run as a standalone proxy (port 8787)
headroom proxy --port 8787
```

### Skill
Copy `skills/headroom/` into `~/.agents/catalog/skills/headroom/`.

---

## 5. UTCP Code-Mode — Sandboxed TypeScript Tool Execution (`code-mode` MCP + `utcp` CLI)

- **Upstream:** [https://github.com/universal-tool-calling-protocol/code-mode](https://github.com/universal-tool-calling-protocol/code-mode)
- **Scope:** **Cross-harness** (OpenCode, Codex, Claude Code, Copilot CLI, Gemini CLI, Antigravity).
- **Purpose:** Replaces dozens of iterative JSON tool calls with a single sandboxed TypeScript execution (`call_tool_chain`) and on-demand schema discovery (`search_tools`).

### Install
```powershell
npm install -g @utcp/code-mode-cli @utcp/code-mode-mcp
```

### Configure
1. Create shared UTCP config at `~/.agents/.utcp_config.json`.
2. Register `code-mode` MCP server (`mcp-bridge.cmd` with `UTCP_CONFIG_FILE=~/.agents/.utcp_config.json`) in:
   - OpenCode: `~/.config/opencode/opencode.json` (`mcp.servers.code-mode`)
   - Codex: `~/.codex/config.toml` (`[mcp_servers.code-mode]`)
   - Claude Code: `~/.claude.json` (`mcpServers.code-mode`)
   - Copilot CLI: `~/.copilot/mcp-config.json` (`mcpServers.code-mode`)
   - Gemini CLI: `~/.gemini/settings.json` (`mcpServers.code-mode`)
3. Copy `skills/code-mode/` into `~/.agents/catalog/skills/code-mode/`.

### Verify
```powershell
utcp --help
opencode mcp list
codex mcp list
```

---

## 6. Continuous Learning v2 (ECC) — Passive Observation & Instinct Evolution

- **Upstream:** [https://github.com/affaan-m/ecc](https://github.com/affaan-m/ecc) (`skills/continuous-learning-v2`)
- **Scope:** **Cross-harness** (adapted for Windows via `cross-agent-hook.py`).
- **Purpose:** Passively records tool execution observations per project (`~/.local/share/ecc-homunculus/`) and evolves repeated patterns into atomic instincts and reusable skills.

### Install
1. Copy `skills/continuous-learning-v2/` into `~/.agents/catalog/skills/continuous-learning-v2/`.
2. **OpenCode:** Copy `plugins/continuous-learning/continuous-learning.ts` to `~/.config/opencode/plugins/continuous-learning.ts`.
3. **Codex CLI:** Add to `PostToolUse` in `~/.codex/hooks.json`:
   ```json
   {
     "type": "command",
     "command": "python \"<USER_HOME>\\.agents\\catalog\\skills\\continuous-learning-v2\\scripts\\cross-agent-hook.py\" post",
     "timeout": 5
   }
   ```

### Verify & Evolve
```powershell
python "$HOME\.agents\catalog\skills\continuous-learning-v2\scripts\instinct-cli.py" status
python "$HOME\.agents\catalog\skills\continuous-learning-v2\scripts\instinct-cli.py" evolve
```

---

## 7. TokenEconomizer — Experience-Driven Cost Control

- **Upstream:** [https://github.com/microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer)
- **Scope:** **Cross-harness** (Claude Code, Codex, Copilot CLI, OpenCode, Cursor, Antigravity, Pi).
- **Purpose:** Repository micro-skills injection, unused tool pruning, and failure-loop intervention (18%–31% lower cost).

### Install
1. Clone into `~/.agents/apps/TokenEconomizer`.
2. For OpenCode, deploy `plugins/tokeneconomizer/tokeneconomizer.ts` to `~/.config/opencode/plugins/tokeneconomizer.ts`.
3. For other harnesses, use the native manifests under `~/.agents/apps/TokenEconomizer/plugin/`.
