# Code Refactoring Specification Template (Advanced)

Use for: targeted code improvements and technical debt reduction. Typical
length 300–500 words. Feeds: `changes/<change-id>/` (scoped active plan;
closed once done). Requires automated tests around the touched behavior.

```text
Refactoring: [Brief description]

Purpose: [What improvement this achieves]

Context:
- [Current code problems]
- [Business/technical drivers]

Current State:
[Existing code structure and problems]

Target State:
[Desired code structure]

Refactoring Patterns to Apply:
1. [Pattern name]: [Where and how to apply]
2. [Pattern name]: [Where and how to apply]

Constraints to Maintain:
- [Constraint]: [Description]
  (e.g., backward compatibility, existing APIs)

Behaviour Preservation:
[Explicit list of behaviours that must not change]

Testing Requirements:
- [Test type]: [What to test]

Before/After Structure Example:
Before: [Brief code structure description]
After: [Brief code structure description]

Edge Cases:
1. [Case to handle during refactoring]

Acceptance Criteria:
- [ ] [Criterion]
- [ ] All existing tests pass

Rollback Considerations:
[How to revert if problems arise]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
