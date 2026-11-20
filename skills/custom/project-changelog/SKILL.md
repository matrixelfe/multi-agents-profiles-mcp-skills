---
name: project-changelog
description: Create and maintain .agent-docs/CHANGELOG.md following Keep a Changelog. Use as soon as work starts in any repository or project, including the first time a repo is opened in a session, and before every commit.
---

# Project Changelog

## When to activate

- First task of a session in a repository: resolve its root with `git rev-parse --show-toplevel`; without Git use the folder holding the project manifest (`package.json`, `pom.xml`, `Cargo.toml`, `pyproject.toml`, `*.sln`, `go.mod`). Then look for `.agent-docs/CHANGELOG.md` and create it with the initial structure when missing, before touching any other file. Once checked, do not re-check per message.
- Every commit created in that repository, including documentation, tests, and internal maintenance changes.
- Do not activate in folders only inspected or read, or that are not a project.

Read [the user-provided format example](references/format-example.md) when creating or restructuring the changelog. Follow its structure; replace its example versions, dates, links, and entries with real project information. Only declare Semantic Versioning adherence if true.

## Required project changelog

User instruction: every repository or project worked on must have `.agent-docs/CHANGELOG.md` at its root. Create the directory and file when missing. Apply this when working on an actual project, not to unrelated folders merely inspected.

Follow [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/): write readable summaries, maintain `## [Unreleased]` at the top, group entries under `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`, and omit empty category headings. Use the project's language for entries. Preserve existing history and do not invent past versions or claim SemVer adherence without evidence.

For EVERY commit created, update this file before committing and stage the relevant changelog update with the same change. This per-commit requirement is the user's additional policy, including documentation, tests, and internal maintenance changes. Describe the actual effect concisely; do not dump Git logs. Do not create a separate recursive commit merely to document the changelog update itself.

Keep pending changes under Unreleased until a release is actually made. At release time, move them into a version heading with an ISO date `YYYY-MM-DD`, newest releases first, and add comparison links when the repository URL and real tags are known. A commit alone is not a release. Avoid embedding the current commit hash in its own changelog entry.

Initial file structure:

```markdown
# Changelog

Los cambios de este proyecto se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
```

If another changelog already exists, preserve it and ensure `.agent-docs/CHANGELOG.md` is maintained without discarding history. Before finalizing a commit, check that the staged changelog accurately covers that commit's changes.
