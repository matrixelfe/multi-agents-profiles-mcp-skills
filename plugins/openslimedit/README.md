# OpenSlimedit Plugin for OpenCode

> **Upstream Repository:** [https://github.com/ASidorenkoCode/openslimedit](https://github.com/ASidorenkoCode/openslimedit)  
> **Author:** ASidorenkoCode  
> **Target:** OpenCode V1 / V2 (`~/.config/opencode/plugins/openslimedit.ts`)  
> **Purpose:** Compresses tool definitions and compacts file read outputs to reduce token usage by 20%–45% without external runtime overhead.

## What it does

1. **Tool Description Compression (`tool.definition`)**: Shortens verbose built-in tool descriptions (`read`, `edit`, `apply_patch`, `write`, `bash`, `glob`, `grep`, `list`, `fetch`).
2. **Compact File Reads (`tool.execute.after`)**: Normalizes absolute paths to relative paths and removes footer boilerplate.
3. **Line-Range Expansion (`tool.execute.before`)**: Enables editing via line ranges like `"55-64"` in `oldString`.

## Installation & Reuse

Copy `openslimedit.ts` to `~/.config/opencode/plugins/openslimedit.ts`. OpenCode auto-discovers plugins placed in this directory.
