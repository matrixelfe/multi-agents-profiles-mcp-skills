# Microservice Specification Template (Advanced)

Use for: complete microservices including API, data layer, and
infrastructure. Typical length 500–800 words. Feeds:
`architecture/overview.md` (per-service section). Compose with
`rest-api-endpoint.md` and `database-schema.md` for its inner blocks.

```text
Service: [ServiceName]

Purpose: [What business capability this service implements]

Context:
- [System architecture context]
- [Bounded context description]

Service Boundaries:
[Clear description of what this service owns]

API Contract:
[Use the REST API Endpoint template for each endpoint]

Data Models:
[Use the Database Schema template or describe entities]

Dependencies:
Internal Services:
- [Service name]: [What we need from it]

External Services:
- [Service name]: [Integration details]

Configuration:
- [Config parameter]: [Description and default]

Deployment Requirements:
- Runtime: [Platform and version]
- Resources: [CPU, memory, storage]
- Scaling: [Scaling approach]

Observability:
Logging: [What to log]
Metrics: [Key metrics to expose]
Tracing: [Distributed tracing requirements]
Health Checks: [Endpoint and logic]

Inter-Service Communication:
- [Communication pattern: sync/async]
- [Protocol: REST/gRPC/message queue]
- [Error handling and retry logic]

Edge Cases:
1. [Case]: [Expected behaviour]
2. [Case]: [Expected behaviour]

Acceptance Criteria:
- [ ] [Criterion]
- [ ] [Criterion]

Non-Functional Requirements:
- Response time: [Target]
- Availability: [Target]
- Throughput: [Target]
- Security: [Requirements]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
