# REST API Endpoint Specification Template (Intermediate)

Use for: backend API endpoints and RESTful services. Works in natural
language or OpenAPI/JSON. Typical length 200–400 words. Feeds:
`specs/<feature>/spec.md` (API behavior) and `api/openapi.yaml` (the
machine-readable contract — keep both aligned).

```text
Endpoint: [HTTP Method] [Path]

Purpose: [What this endpoint does and its role in the system]

Context:
- [System integration points]
- [Authentication/authorisation context]

Request:
Method: [GET|POST|PUT|DELETE|PATCH]
Path: [/api/resource/{id}]
Headers:
- [Header name]: [Value or description]

Request Body (if applicable):
{
  "field1": "type - description",
  "field2": "type - description"
}

Authentication:
[Description of authentication requirements]

Response Schemas:
Success (200/201):
{
  "field1": "type - description",
  "field2": "type - description"
}

Error Responses:
- 400 Bad Request: [When and what response]
- 401 Unauthorised: [When and what response]
- 404 Not Found: [When and what response]
- 500 Server Error: [When and what response]

Behaviour:
[Processing logic, data validation, side effects]

Edge Cases:
1. [Case]: [Expected response]
2. [Case]: [Expected response]

Examples:
Request Example 1: [Complete request] → [Complete response]
Request Example 2: [Complete request] → [Complete response]

Acceptance Criteria:
- [ ] [Criterion]
- [ ] [Criterion]

Performance Requirements:
- Response time: [Target]
- Rate limits: [Specification]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
