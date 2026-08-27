# Phase 1.3 — Quality Gate Release

## Purpose

This release is a full Phase 1 correction, not a patch-only release.

### Database/configuration
- `DATABASE_URL` is owned by application Settings.
- SQLAlchemy and Alembic use the same normalized database URL.
- PostgreSQL private Railway URL is supported.
- No migration is executed during application startup.

### Tenant and Brand isolation
- Brand-scoped platform voice references use a composite FK.
- Platform accounts enforce `(brand_id, workspace_id)` ownership.
- Brand member roles enforce workspace/brand/member consistency.
- Workspace member roles enforce workspace role scope.
- Languages are constrained to `ar` and `en`.

### Brand voice
- Only one default voice is permitted per Brand using a PostgreSQL partial unique index.

### Health check
- Database health executes only `SELECT 1`.
- It does not create, alter, or delete data.

### Important scope boundary
AI model cost accounting, research provenance, agent runs, publication idempotency,
budgets, retries, and analytics are deliberately not added to Phase 1 tables.
They are architectural requirements for later phases and must be designed before
Agents/Content/Publishing are implemented.

## Validation performed in the delivery environment

- Python syntax compilation: required.
- Static schema/constraint tests: required.
- Database health behavior: mocked, non-destructive.
- Real PostgreSQL connectivity: NOT claimed here; must be tested on Railway before migration.
- Real Alembic upgrade/downgrade: NOT claimed here; must be tested against the Railway PostgreSQL service after preflight.

## Deployment rule

Do NOT run `alembic upgrade head` until the Railway PostgreSQL preflight has passed.
