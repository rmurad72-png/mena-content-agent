# Sprint Release 0.6.0 — Authoritative Phase 1 Hardening

## Quality Gate

- Python compileall: PASS
- Automated tests: PASS
- PostgreSQL DDL compilation: PASS
- Alembic PostgreSQL offline upgrade SQL generation: PASS
- Alembic PostgreSQL offline downgrade SQL generation: PASS
- Configuration/Railway alias simulation: PASS
- Unresolved Railway reference rejection: PASS

## Runtime hardening

- `DATABASE_URL`, `DATABASE_PRIVATE_URL`, and `POSTGRES_PRIVATE_URL` are accepted through one settings layer.
- Unresolved Railway interpolation values such as `${{ Postgres.DATABASE_PRIVATE_URL }}` are rejected early.
- SQLAlchemy engine is process-cached.
- Connection pre-ping, timeout, and pool recycling are enabled.
- Controlled shutdown disposes the shared database engine.
- `/health` is a non-database liveness check.
- `/health/db` is a read-only readiness check and returns HTTP 503 without connection details when unavailable.
- Telegram UI exposes only the currently implemented Telegram publishing adapter; registry entries for future platforms are not presented as executable features.
- Alembic and application runtime use the same configuration normalization path.

## Scope integrity

Future AI/research/content-version/evaluation/approval/publishing-job/cost-accounting domains remain intentionally unimplemented until their domain and financial/operational rules are designed and tested.

## Local verification limitation

The simulation environment has no network access to the user's Railway PostgreSQL instance and no Docker daemon. Live Railway connectivity and migration execution are therefore not claimed as locally tested.
