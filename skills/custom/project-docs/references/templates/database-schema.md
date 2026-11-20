# Database Schema and Migration Template (Intermediate)

Use for: database structures, schema changes, and data migrations. Typical
length 150–300 words. Feeds: `specs/<feature>/spec.md` (schema requirements)
or `changes/<change-id>/` (the migration plan itself).

```text
Migration: [Brief description]

Purpose: [What this migration accomplishes and why]

Context:
- [Current database state]
- [Integration with existing tables]

Tables:
Table: [table_name]
Columns:
- [column_name]: [type] [constraints] - [description]

Relationships:
- [Relationship description with foreign keys]

Indexes:
- [Index specification and rationale]

Migration Operations:
UP (Apply):
1. [Operation description]
2. [Operation description]

DOWN (Rollback):
1. [Rollback operation]
2. [Rollback operation]

Data Transformation (if applicable):
[Description of how existing data should be migrated]

Edge Cases:
1. [Case]: [How to handle]
2. [Case]: [How to handle]

Acceptance Criteria:
- [ ] [Criterion]
- [ ] [Criterion]

Performance Impact:
- [Expected migration duration]
- [Downtime requirements]
```

Adapted from SoftwareSeni, "Specification Templates for AI Code Generation"
(https://www.softwareseni.com/specification-templates-for-ai-code-generation-from-first-draft-to-production/).
