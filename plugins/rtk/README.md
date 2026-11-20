# RTK (Rust Token Killer) Plugin for OpenCode

> **Upstream Repository:** [https://github.com/rtk-ai/rtk](https://github.com/rtk-ai/rtk)  
> **Package / Binary:** `rtk` (Rust native binary)  
> **Target:** OpenCode (`~/.config/opencode/plugins/rtk.ts`)  
> **Purpose:** Ultra-fast (<25 ms) shell output compressor that cuts command output tokens by 60%–90% for builds, tests, diffs, and git commands.

## How It Works

This plugin intercepts command execution in OpenCode and delegates to `rtk hook opencode`. RTK compresses verbose command outputs before the LLM ingests them into the context window, without altering command execution semantics or violating permission rules.

## Installation

1. Install the `rtk` CLI binary (e.g., via GitHub releases or package manager).
2. Deploy `rtk.ts` to `~/.config/opencode/plugins/rtk.ts`.
3. Check accumulated token savings at any time with `rtk gain`.
