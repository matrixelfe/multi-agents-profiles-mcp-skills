# Continuous Learning v2 — OpenCode Observation Plugin

> **Upstream Repository:** [https://github.com/affaan-m/ecc](https://github.com/affaan-m/ecc) (`skills/continuous-learning-v2`)  
> **Target:** OpenCode / OpenChamber (`~/.config/opencode/plugins/continuous-learning.ts`)  
> **Purpose:** Captures `tool.execute.before` and `tool.execute.after` events and forwards them to `cross-agent-hook.py` in the Cold Skill Vault (`~/.agents/catalog/skills/continuous-learning-v2/scripts/cross-agent-hook.py`).

## Installation

1. Copy `skills/continuous-learning-v2` into `~/.agents/catalog/skills/continuous-learning-v2`.
2. Copy `continuous-learning.ts` into `~/.config/opencode/plugins/continuous-learning.ts`.
3. For Codex CLI, register `cross-agent-hook.py post` under `PostToolUse` in `~/.codex/hooks.json`.
4. Run evolution periodically:
   ```powershell
   python "$HOME\.agents\catalog\skills\continuous-learning-v2\scripts\instinct-cli.py" status
   python "$HOME\.agents\catalog\skills\continuous-learning-v2\scripts\instinct-cli.py" evolve
   ```
