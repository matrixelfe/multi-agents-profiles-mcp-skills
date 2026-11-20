# `oac.project-docs` — OpenCode V2 / OpenChamber Plugin

Server plugin that pairs with the cross-agent `project-docs` skill to automatically observe file edits and dispatch isolated `[project-docs sync]` notices per Git worktree.

## Features
- Strict worktree isolation (`scope.mjs`): validates session identity before accepting edits or dispatching sync prompts.
- Per-owner batch tracking (`sync-state.mjs`): prevents cross-session or cross-worktree interference.
- Safe default (`dryRun: true`): starts in proposal-only mode until explicitly enabled.

## Installation (OpenCode V2 / OpenChamber)
Copy or symlink this directory into `~/.config/opencode/plugins/project-docs/`.

Optional config (`project-docs.config.json` next to `index.ts`):
```json
{
  "disabled": false,
  "dryRun": true,
  "attachOnPrompt": true,
  "debounceMs": 1500
}
```

## Verification
```bash
node --test tests/*.test.mjs
```
