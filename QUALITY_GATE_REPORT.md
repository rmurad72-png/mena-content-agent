# MENA Content Agent — Phase 1.3-R1 Quality Gate

## Scope

Authoritative replacement release for the current repository snapshot. No legacy source copies are required by this release.

## Checks executed

| Check | Result |
|---|---|
| Python compilation (`compileall`) | PASS |
| Unit/schema tests | PASS — 16 tests |
| PostgreSQL DDL compilation from SQLAlchemy metadata | PASS |
| Alembic PostgreSQL offline upgrade SQL generation | PASS |
| Alembic PostgreSQL offline downgrade SQL generation | PASS |
| Real PostgreSQL connectivity | NOT CLAIMED — Railway preflight required |
| Real Railway migration upgrade | NOT CLAIMED — must be performed after preflight |
| Real Railway migration downgrade | NOT CLAIMED — must be performed in a controlled pre-production context |

## Integrity guarantees covered

- Workspace and Brand ownership boundaries are represented in composite foreign keys where cross-tenant leakage is possible.
- A Brand Platform Profile can reference only a Voice belonging to the same Brand.
- A Brand can have at most one default Voice.
- Supported language values are restricted to Arabic and English on all current language-scoped records.
- Platform profiles cannot silently orphan a platform through deletion; platform deletion is restricted.
- Platform accounts cannot cross Workspace/Brand boundaries.
- Deterministic permission/platform seed IDs are used by the migration.
- Database migrations are not executed during application startup.

## Deliberate non-claims

This release does not pretend that the following are already implemented: AI provider routing, research provenance, content/version lifecycle, evaluation runs, publication job idempotency, retry orchestration, usage/cost accounting, budgets, analytics, or complete database-backed authorization enforcement. Those require their own domain design before implementation.
