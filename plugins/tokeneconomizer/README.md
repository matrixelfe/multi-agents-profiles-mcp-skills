# TokenEconomizer Plugin for OpenCode

> **Upstream Repository:** [https://github.com/microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer)  
> **Authors:** Microsoft Research & UC Berkeley  
> **Target:** OpenCode (`~/.config/opencode/plugins/tokeneconomizer.ts`) and cross-harness (`.agents/apps/TokenEconomizer`)  
> **Purpose:** Experience-driven cost control for AI coding agents: micro-skills injection, unused tool pruning, and failure-loop intervention (18%–31% lower cost).

## Architecture

This plugin speaks the dispatcher protocol (`te-hook --host opencode`) connecting OpenCode's lifecycle hooks to TokenEconomizer's unified Python engine:
- `session.created` -> `SessionStart` (injects learned repo micro-skills).
- `experimental.chat.system.transform` -> appends active manual to system prompt.
- `tool.execute.after` -> `PostToolUse` guard (detects repetitive loops and nudges redirect).
- `session.idle` / `session.execution.*` -> Turn completion and session folding.

## Setup

Deploy to `~/.config/opencode/plugins/tokeneconomizer.ts`. Relies on the central TokenEconomizer runtime in `~/.agents/apps/TokenEconomizer/plugin/scripts`.
