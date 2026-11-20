# RTK (Rust Token Killer) — Cross-Harness Plugin & Hooks

> **Upstream Repository:** [https://github.com/rtk-ai/rtk](https://github.com/rtk-ai/rtk)  
> **Binary:** `rtk` (`~/.local/bin/rtk.exe` on Windows, native Rust binary)  
> **Purpose:** Ultra-fast (<25 ms) shell output compressor that cuts command output tokens by 60%–90% across builds, test runners, diffs, and git commands.

## Cross-Harness Hook Installation

1. **Install the binary** (Windows prebuilt release from GitHub or `winget install rtk-ai.rtk`):
   ```powershell
   # Verify binary
   rtk --version
   ```
2. **Register hooks across all harnesses**:
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

## Verification

```powershell
# Inspect installed hooks and files
rtk init --show

# Dry-run rewrite check
rtk hook check "git status"

# View accumulated token savings
rtk gain
```
