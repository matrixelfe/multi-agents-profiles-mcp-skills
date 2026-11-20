# System Architecture Specification Template (Advanced)

Use for: multi-component system design and architectural decisions. Typical
length 600–1000 words. Feeds: `architecture/overview.md`; its Architecture
Decisions blocks feed `architecture/adr/<id>.md` (context/decision/
consequences).

```text
System: [SystemName]

Purpose: [What business problem this system solves]

Context:
- [Business context and drivers]
- [Technical landscape]
- [Constraints]

System Context:
Users: [Who uses this system]
External Systems: [What external systems it integrates with]

Component Identification:
Component: [ComponentName]
Responsibility: [What it does]
Technology: [Platform/framework]
Interfaces: [APIs it exposes]

Interaction Patterns:
- [Pattern 1]: [When and why it's used]
- [Pattern 2]: [When and why it's used]

Data Flows:
1. [Flow description]
2. [Flow description]

Integration Points:
- [Integration point]: [Protocol, data format, error handling]

Scaling Requirements:
- [Component]: [Scaling approach and targets]

Security Boundaries:
- [Boundary]: [Controls in place]

Operational Characteristics:
- Availability: [Targets and approach]
- Performance: [Targets]
- Disaster Recovery: [RPO/RTO]
- Deployment: [Strategy]

Architecture Decisions:
Decision: [Topic]
Context: [Why we needed to decide]
Decision: [What we decided]
Consequences: [Implications]

Technology Stack:
- [Layer]: [Technology choices]

Acceptance Criteria:
- [ ] [System-level criterion]

Non-Functional Requirements:
- [Requirement]: [Target and measurement]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
