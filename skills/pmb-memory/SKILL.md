---
name: pmb-memory
description: Local-first cross-agent persistent memory engine (PMB). Use this skill to query, store, and recall persistent project decisions, lessons, personal preferences, and architecture context across all AI agents (Antigravity, Claude Code, Cursor, Codex, Gemini, etc.).
---

# PMB Memory (Persistent Memory Bank)

> **Upstream Repository:** [https://github.com/oleksiijko/pmb](https://github.com/oleksiijko/pmb)  
> **Package:** `pmb-ai` (PyPI / npm / standalone binary)  
> **Purpose:** Local-first, cross-agent persistent memory engine backed by SQLite, LanceDB vector storage, and BM25 lexical search.

PMB is a local-first memory layer for AI coding agents backed by SQLite, LanceDB vector storage, and BM25 lexical search. It persists context, architectural decisions, past bugs, lessons, and project constraints locally across sessions and different agents.

## Core Principles

1. **Local-First & Offline**: Everything is stored in `~/.pmb` (SQLite + LanceDB). No cloud, no external API keys required.
2. **Cross-Agent**: All agents (Antigravity, Claude Code, Cursor, Codex, Windsurf, etc.) share the same memory workspace or project-specific memory.
3. **Recall Before Asking**: Check memory when tackling complex architectural questions, past bugs, recurring preferences, or prior design decisions.
4. **Proactive Recording**: Record critical decisions, durable lessons learned, and fixed tricky bugs so future sessions/agents don't repeat mistakes.

---

## Quick Reference CLI Commands

### Capture Memory

- **Record a standalone fact or decision**:
  ```bash
  pmb fact "Database migrations must use batch size 500 to avoid locking"
  ```
- **Record a Q&A pair**:
  ```bash
  pmb remember -q "Why do we use custom allocator in module X?" -a "Prevents fragmentation under heavy streaming loads"
  ```
- **Teach a durable lesson (procedural rule)**:
  ```bash
  pmb learn "When modifying auth tokens, always update the refresh middleware signature in src/auth"
  ```
- **Quick note from terminal**:
  ```bash
  pmb note "Investigating memory spike in worker thread 3"
  ```

### Recall & Query Memory

- **Search memory by topic / query**:
  ```bash
  pmb recall "auth token expiration"
  ```
- **List durable lessons**:
  ```bash
  pmb lessons
  ```
- **Prepare context block for a prompt/message**:
  ```bash
  pmb prepare-context "fix LoadGuard pricing bug"
  ```
- **Inspect memory statistics**:
  ```bash
  pmb stats
  ```

### Workspace & Maintenance

- **List all workspaces**:
  ```bash
  pmb workspaces
  ```
- **Set default shared workspace**:
  ```bash
  pmb workspace use <name_or_id>
  ```
- **Run diagnostic health check**:
  ```bash
  pmb doctor
  ```
- **Start/check background daemon**:
  ```bash
  pmb daemon start
  pmb daemon status
  ```

---

## MCP Server Integration

PMB exposes an MCP server for agents to interact with directly.

- **Executable**: `C:\Users\edgar\.local\bin\pmb-mcp.exe` (or `pmb mcp` / `pmb-mcp`)
- **Shared Daemon HTTP Endpoint**: `http://127.0.0.1:8765/mcp`
- **Native MCP Tools Available**:
  - `recall`: Search relevant facts, lessons, and decisions.
  - `record_fact`: Save a fact, project constraint, or user preference.
  - `record_lesson`: Save a durable technique or rule learned from a mistake.
  - `prepare`: Get project context for an incoming task.
