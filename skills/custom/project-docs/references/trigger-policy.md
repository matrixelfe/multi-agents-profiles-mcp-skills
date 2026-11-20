# Trigger Policy

When documentation work happens, and when it is skipped. The plugin triggers;
this skill decides and performs.

## Triggers

| Situation | Mode | Write policy |
| --- | --- | --- |
| First real user prompt in a Git repository | `bootstrap` | Create only missing, fact-supported docs. |
| Source/config/test files changed, execution finished | `sync` | Update only impacted docs; one sync per worktree. |
| Agent is about to commit | pre-commit check | Docs and changelog synchronized and staged **before** the commit. |
| Explicit release request or tag | `release-audit` | Reconcile, archive, prune; no invented versions. |
| `status` request | `status` | No writes. |

## Skip conditions (report no-op, write nothing)

- The directory is not a Git repository or worktree.
- Read-only inspection: no project, no files changed, questions only.
- Child/subagent sessions and nested plugin operations.
- Docs already current (identical sync fingerprint, docs-only repeat).
- The folder only holds no project (inspected-only passes through).
- The work happened outside the session's project (never cross-repo writes).

## Failure behavior

- Interruption, permission denial, or skill error: preserve files, keep the
  sync pending, report a recoverable warning. Never claim docs are current
  when sync did not run.
- If a commit begins before sync succeeds: stop the agent-driven commit and
  request manual remediation. A later idle sync must not "repair" an existing
  commit.
- Commits made outside OpenCode cannot be intercepted here; an optional Git
  pre-commit guard may be installed separately, never silently.

## Hard limits

- Never auto-commit, push, release, or run destructive cleanup.
- Writes only inside the current repository and only to `.agent-docs/**` and
  the repo `AGENTS.md`.
- Never dispatch a second sync from the sync's own work (loop guard).
- Rapid edits coalesce: at most one pending sync per worktree.
