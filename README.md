# MENA Content Agent

AI content planning, brand governance, review, and publishing foundation for Telegram, X, Reddit, YouTube, Instagram, and LinkedIn.

## Current release

This repository contains the authoritative Phase 1 database foundation. It is designed around strict Workspace and Brand isolation and is the source of truth for subsequent phases.

### Domain foundation

- Workspace and team membership
- Workspace-scoped and Brand-scoped RBAC
- Independent Brands inside a Workspace
- Brand identity, voice, audience, rules, and terminology
- Brand-specific platform profiles
- Multiple publishing accounts per Brand
- Instagram and LinkedIn included in the platform registry
- Cross-workspace and cross-brand integrity enforced at the database level
- Arabic as the default language, with English supported where explicitly configured

### Database

PostgreSQL is required. Railway can provide `DATABASE_URL` using either `postgres://` or `postgresql://`; the application normalizes these to the `psycopg` SQLAlchemy driver.

### Migration safety

Migrations are **not** executed during application startup. Run them deliberately after PostgreSQL connectivity and SQL review have passed:

```bash
alembic upgrade head
```

Offline SQL review:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db alembic upgrade head --sql
```

### Verification

```bash
python -m compileall -q app alembic tests
pytest -q
```

The tests cover model registration, tenant foreign keys, Brand/Voice isolation, language constraints, default-voice uniqueness, platform-account boundaries, and database configuration/health behavior.

### Important scope boundary

AI provider routing, research provenance, content versions, evaluation runs, publication idempotency, retries, budgets, cost accounting, analytics, and full database-backed authorization are **not fabricated into Phase 1**. They remain explicit architectural requirements for the next domain phases and must be designed before implementation.

## Deployment rule

Do not run `alembic upgrade head` on Railway until the release has passed local quality gates and the Railway PostgreSQL preflight has been explicitly verified.
