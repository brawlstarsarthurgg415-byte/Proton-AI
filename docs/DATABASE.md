# Proton-AI PostgreSQL schema

Schema version 1 is in `migrations/001_initial_schema.sql`.

Tables:
- `knowledge`: proposed knowledge; starts as `pending_review` and is never training-eligible by default.
- `knowledge_sources`: source URLs for each proposal.
- `guardian_reviews`: append-only review history; model verdicts are advisory.
- `training_runs`: training job metadata and metrics.
- `audit_events`: event history.

Safety invariants:
- New knowledge is not approved.
- `training_eligible` defaults to false.
- A database constraint prevents training eligibility unless a curator explicitly marks a lesson/correction/reference as approved.
- Guardian screening alone must never approve a record.
- Ownership claims remain unverified and cannot become training data.
- Migration uses CREATE IF NOT EXISTS and does not drop existing data.

The migration has been committed to the repository. It is not applied to Railway until a migration runner is deployed and executed against the Postgres service.
