---
name: conventional-commits
description: Apply the Conventional Commits 1.0.0 format when proposing, creating, or reviewing Git commit messages.
---

# Conventional Commits

For Git commit messages, follow the [Conventional Commits 1.0.0 specification](https://www.conventionalcommits.org/en/v1.0.0/).

Use this structure:

```text
<type>[optional scope][!]: <short description>

[optional body]

[optional footer(s)]
```

- Use `feat` for a new feature and `fix` for a bug fix. Other useful types include `build`, `chore`, `ci`, `docs`, `perf`, `refactor`, `revert`, `style`, and `test`; choose the type that accurately describes the change.
- Add a short noun scope in parentheses when it improves context, such as `fix(parser): ...`.
- Keep the description concise and specific. Use the repository's established capitalization and language conventions when present; otherwise use lowercase type and a clear imperative description.
- Put a longer explanation in the body, separated from the subject by a blank line.
- Mark breaking changes with `!` before the colon, such as `feat(api)!: ...`, or with a `BREAKING CHANGE: <description>` footer. The footer token must use uppercase `BREAKING CHANGE`.
- Format other footers as `<Token>: <value>` or `<Token> #<value>`, separated from the body by a blank line.
- Respect explicit repository contribution rules and existing project conventions where they add constraints; keep the commit message compliant with Conventional Commits.

When asked to commit, inspect the actual staged change and choose the message type from that change. Do not claim a commit was created unless Git confirms it. When asked only to suggest a message, return the message without making a commit.

