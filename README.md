# MENA Content Agent

Production foundation for a multi-workspace, multi-brand content platform.

## Current authoritative release

**Sprint Release 0.6.1** establishes the PostgreSQL domain foundation and runtime database lifecycle.

### Domain foundation

- Workspace and team membership.
- Workspace-scoped and Brand-scoped RBAC.
- Independent Brands inside a Workspace.
- Brand identity, voice, audience, rules, and terminology.
- Brand-specific platform profiles.
- Multiple publishing accounts per Brand.
- Telegram, X, Reddit, YouTube, Instagram, and LinkedIn platform registry; only implemented publishing adapters are exposed in the Telegram UI.
- Cross-workspace and cross-brand integrity enforced by PostgreSQL foreign keys.
- Arabic is the default language; English is supported when explicitly configured.

### Database/runtime foundation

- PostgreSQL via SQLAlchemy 2 + psycopg 3.
- Railway private-database aliases: `DATABASE_URL`, `DATABASE_PRIVATE_URL`, and `POSTGRES_PRIVATE_URL`; supported URL schemes are `postgres://`, `postgresql://`, and `postgresql+psycopg://`.
- Explicit environment aliases for Railway variables.
- One process-wide SQLAlchemy engine/pool instead of creating a new pool per session.
- Connection pre-ping, connection timeout, and pool recycling for operational resilience.
- Read-only `/health/db` endpoint that returns HTTP 503 without leaking connection details when PostgreSQL is unavailable.
- Database access remains optional during application boot; migrations are never run automatically.

### Migration safety

Run deliberately only after PostgreSQL preflight:

```bash
alembic upgrade head
```

Offline SQL review:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db alembic upgrade head --sql
```

Downgrade SQL review:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db alembic downgrade 001_phase1:base --sql
```

### Verification

```bash
python -m compileall -q app alembic tests
pytest -q
```

The quality gate covers configuration aliases, unresolved Railway references, database lifecycle, health behavior, model registration, tenant foreign keys, Brand/Voice isolation, language constraints, default-voice uniqueness, platform-account boundaries, API contracts, and migration contracts.

### Explicit next-domain boundary

The following are intentionally **not fabricated into Phase 1** and must be designed as first-class domains before implementation:

- AI provider routing and model selection.
- Research sources/provenance and retrieval.
- Content items, immutable versions, and editorial state transitions.
- Multi-model writing and evaluation.
- Human approval workflow.
- Publication jobs, idempotency, retries, and platform adapters.
- AI/API usage metering, budgets, cost accounting, and financial controls.
- Analytics and reporting.
- Database-backed authorization enforcement.

This boundary prevents premature tables and protects future financial, operational, and authorization correctness.

## Deployment rule

Do not run migrations on Railway until this release passes the local quality gate and Railway PostgreSQL preflight has been explicitly verified.
