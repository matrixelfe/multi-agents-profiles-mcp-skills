# Document Contracts

What each artifact must contain, and what belongs elsewhere. Create a file
only when there is real, verified content; never create empty directories.

| Artifact | Required content | Keep out |
| --- | --- | --- |
| `AGENTS.md` (repo root) | Overview, Architecture (+ Key Modules), Context Navigation (flow + where-to-look map), Rules, Debugging Strategy, Verify commands, Documentation Map. Structure: `references/repo-agents-template.md` | Global policy, invented layers, placeholders, copied spec bodies |
| `specs/<feature>/spec.md` | Purpose, testable requirements, acceptance scenarios | Implementation diaries, step-by-step logs |
| `changes/<change-id>/` | Scoped proposal, design notes, task checklist, status | Permanent duplicates of specs |
| `architecture/overview.md` | Components, boundaries, key dependencies | Every implementation detail |
| `architecture/adr/<id>.md` | Context, decision, consequences, status | Routine refactors |
| `api/openapi.yaml` | Valid HTTP contract, when an HTTP API exists | Planning narratives |
| `guides/<task>.md` | Prerequisites, commands, expected result | Background essays |
| `security/…` | Documented security boundaries and models of this project | Generic security advice |
| `evals/…` | Agent behavior evaluation cases, if applicable | Test fixtures that belong to the test suite |
| `memory.md` | Verified handoffs, current blockers, known limitations, next steps — each with source/date | Rules, release history, secrets, spec copies |
| `CHANGELOG.md` | Owned by the `project-changelog` skill — do not edit here beyond its conventions | Anything not covered by its format |

## memory.md template

```markdown
# Project Memory
Last reviewed: YYYY-MM-DD

## Active Context
- <verified context that helps resume work>

## Known Constraints
- <constraint and link to evidence or source>

## Open Questions
- <question, owner/status, next step>
```

If there is no useful state to preserve, omit `memory.md` or leave it with only
verified facts; do not manufacture entries.

## Writing conventions

- Descriptive headings, relative links, code fences with language identifiers.
- English for all new or revised documentation; do not translate existing
  authored docs (user-facing docs may stay in the project's language).
- Target 80–120 lines for routine documents as an editing guide; split by
  responsibility only when it genuinely improves retrieval.
- Replace stale text instead of appending corrections.
