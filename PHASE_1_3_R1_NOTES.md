# Phase 1.3-R1 — Full Integrity Correction Release

## Release status

This is the authoritative replacement for the previous Phase 1.3 package. It is a complete source tree, not a patch set.

## Corrections

- Model/migration parity restored for language checks and deletion behavior.
- Brand Platform Profile Voice is protected by a composite `(voice_id, brand_id)` foreign key.
- Platform deletion policy is `RESTRICT`, matching the model.
- Only one default Brand Voice is allowed per Brand through a PostgreSQL partial unique index.
- Workspace, User, Brand, Audience, Term, and Platform Profile language values are constrained to `ar`/`en`.
- Brand terms enforce non-blank term and preferred form.
- Requirements explicitly include SQLAlchemy, Alembic, psycopg, and pytest.
- Obsolete backup/test copies are removed from the authoritative tree.

## Validation

The delivery process requires: syntax compilation, unit/schema tests, migration source-contract tests, and offline PostgreSQL SQL generation when a PostgreSQL driver is available. Real Railway PostgreSQL upgrade/downgrade remains a deployment preflight and is never claimed locally without a real PostgreSQL service.
