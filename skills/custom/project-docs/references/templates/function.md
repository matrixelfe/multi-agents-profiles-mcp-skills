# Function Specification Template (Beginner)

Use for: single-purpose functions, utilities, data transformations, validation
logic. Typical length 100–200 words. Feeds: `specs/<feature>/spec.md`
(function-level requirements sections).

```text
Function: [Function name and signature]

Purpose: [1-2 sentences describing what this function does and why it exists]

Context:
- [Key background information]
- [Relevant system constraints]

Inputs:
- [Parameter name]: [Type] - [Description and constraints]

Expected Output:
- [Return type]: [Description]

Behaviour:
[2-3 sentences describing the processing logic]

Edge Cases:
1. [Case description]: [Expected behaviour]
2. [Case description]: [Expected behaviour]
3. [Case description]: [Expected behaviour]

Examples:
Example 1: [Input] → [Output]
Example 2: [Input] → [Output]
Example 3: [Input] → [Output]

Acceptance Criteria:
- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Testable criterion 3]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
