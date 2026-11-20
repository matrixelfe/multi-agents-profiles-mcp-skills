# Repo AGENTS.md Template

Use for: the repository `AGENTS.md` (one per Git repo). Fills the contract in
`document-contracts.md` — project-specific facts and pointers only. No global
maintenance policy here; that lives in the global `AGENTS.md` and in
`SKILL.md`. Fill with verified facts only; never commit placeholders.

## Rules for this file

- Target 40–80 lines. English. One source of truth: link, do not copy
  (`.agent-docs/` and `README.md` hold the detail).
- Every command must be executed or read from a manifest; a command that
  fails goes in `memory.md` as an open question, not here.
- Omit any section with no verified content. Do not invent layers.

```text
# Project Overview

<One paragraph: what this repo is, stack, runtime, who uses it.>

## Architecture

- `<folder>` → <role> (entrypoints / orchestration / core logic / data access / UI / config)
- `<folder>` → <role>

## Key Modules

- `<folder-or-file>`: <what it owns>
- `<folder-or-file>`: <what it owns>

## Context Navigation

### To understand a flow

1. Start at <entrypoint>
2. Follow to <middle layer>
3. Then <core layer>

## Rules

- <Only hard constraints that actually apply here, as bullets.>
- <Never-do rules with a concrete reason.>

## Context Navigation Map

### Main Flows

- <Flow name>: `<A>` → `<B>` → `<C>`

### Where to look for

- <Topic> → `<path>`
- <Topic> → `<path>`

## Debugging Strategy

1. <First check: input / config / env>
2. <Second check: trace / logs / boundary>
3. <Third check: contract / data / version evidence>

## Verify

Run from the repository root:

- Build: `<real command>`
- Test: `<real command>`
- Lint / typecheck: `<real command, or "none — no linter configured">`

## Documentation Map

- Architecture and ADRs: `.agent-docs/architecture/`
- Requirements: `.agent-docs/specs/`
- Work in progress: `.agent-docs/changes/`
- API contract (if present): `.agent-docs/api/`
- Guides and security: `.agent-docs/guides/`, `.agent-docs/security/`
- Operational handoff: `.agent-docs/memory.md` (if present)
- Changelog (this repo): `.agent-docs/CHANGELOG.md`
```

## Worked shape (structure only, not content)

Java Spring Boot microservices, adapted to the same skeleton:

```text
# Project Overview

This is a Java Spring Boot microservices project.

## Architecture

- `controller` → REST entrypoints
- `facade` → orchestration layer
- `service` → business logic
- `repository` → database access

## Key Modules

- `/controller`: REST endpoints
- `/facade`: orchestration logic
- `/service`: business rules

## Context Navigation

### To understand a flow

1. Start at controller
2. Follow to facade
3. Then service layer

## Rules

- Always follow clean architecture
- Avoid putting logic in controllers

## Context Navigation Map

### Main Flows

- API flow: `controller` → `facade` → `service` → `repository`

### Where to look for

- Business logic → `/service`
- Orchestration → `/facade`
- DTOs → `/dto`
- Config → `/config`

## Debugging Strategy

1. Check controller input
2. Trace facade
3. Validate service logic
```

Note: the worked shape keeps the Java vocabulary because those layer names
were given; in a real repo, replace them with the folders that actually exist.
A repo with a single flat layout (no layers) gets the same sections with its
real paths — the skeleton stays, the nouns change.

Reference origin: user-supplied Spring Boot overview + navigation map,
generalized 2026-11-09.
