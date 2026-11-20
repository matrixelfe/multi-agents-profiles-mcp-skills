# React Component Specification Template (Intermediate)

Use for: frontend UI components and interactive widgets. Typical length
200–350 words. Feeds: `specs/<feature>/spec.md` (UI behavior: props, state,
a11y, rendering).

```text
Component: [ComponentName]

Purpose: [What this component does and where it fits in the UI]

Context:
- [Parent component or page context]
- [Design system guidelines]

Props Interface:
{
  propName: type; // description
  propName?: type; // optional prop
}

State Management:
[Component state, what triggers state changes]

Event Handlers:
- [Event type]: [What should happen]

Render Behaviour:
[UI rendering logic, conditional rendering, loading/error states]

Styling Requirements:
- [Key styling requirement]
- [Responsive behaviour]

Accessibility:
- [ARIA labels needed]
- [Keyboard navigation requirements]

Edge Cases:
1. [Case]: [Expected UI behaviour]
2. [Case]: [Expected UI behaviour]

Examples:
Scenario 1: [Props values] → [Rendered output description]
Scenario 2: [Props values] → [Rendered output description]

Acceptance Criteria:
- [ ] [Criterion]
- [ ] [Criterion]

Performance Requirements:
- [Rendering performance targets]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
