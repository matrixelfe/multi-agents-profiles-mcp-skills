# Code Migration Specification Template (Advanced)

Use for: language upgrades, framework migrations, platform transitions.
Typical length 400–700 words. Feeds: `changes/<change-id>/` (scoped active
plan with phased rollout; closed once done).

```text
Migration: [From X to Y]

Purpose: [Why this migration is necessary]

Context:
- [Business drivers]
- [Technical drivers]
- [Timeline]

Source Environment:
- Platform: [Current platform and version]
- Framework: [Current framework]
- Key dependencies: [List]

Target Environment:
- Platform: [Target platform and version]
- Framework: [Target framework]
- Key dependencies: [List]

Migration Strategy:
[Overall approach: big bang, phased, strangler fig]
[Rationale]

Compatibility Requirements:
- [Requirement]: [Description]

Migration Steps:
1. [Step description]
2. [Step description]

Code Transformation Patterns:
- [Pattern]: [From syntax] → [To syntax]

Testing Strategy:
- [Test type]: [Approach]

Phased Rollout Plan:
Phase 1: [Scope and success criteria]
Phase 2: [Scope and success criteria]

Rollback Procedure:
[Detailed steps to revert if migration fails]

Edge Cases and Compatibility Issues:
1. [Known issue]: [How to handle]

Migration Status Tracking:
[How to track progress across files/modules]

Acceptance Criteria:
- [ ] [Criterion]
- [ ] All tests pass in target environment

Risk Assessment:
- [Risk]: [Mitigation]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
