# Phase 1.1 — Database Preflight Foundation

This package fixes the database configuration consistency and adds a read-only
database connectivity check plus local schema/configuration tests.

Important:
- Do NOT run `alembic upgrade head` yet.
- Do NOT modify Railway database data.
- `app/main.py` is intentionally not replaced in this package; the existing
  runtime remains unchanged until the connectivity check is deliberately wired
  into the application.
- The next step after deployment is to verify the DB connection, then perform
  an Alembic dry-run, then apply the migration.
