# MENA Content Agent

AI content planning and review system for Telegram, X, Reddit, YouTube, Instagram, and LinkedIn.

## Phase 1

Phase 1 introduces the PostgreSQL domain foundation for:

- Workspace and team membership
- Workspace-scoped roles and permissions
- Brand-scoped roles and permissions
- Independent brands inside a workspace
- Brand identity, voice, audience, rules, and terminology
- Platform definitions
- Brand-specific platform publishing profiles
- Multiple platform accounts per brand
- Cross-workspace and cross-brand integrity constraints

### Database

PostgreSQL is required.

Set:

```text
DATABASE_URL=postgresql://...
```

The application accepts Railway's `postgres://` and `postgresql://` forms and normalizes them to the `psycopg` SQLAlchemy driver.

### Migration

Install dependencies, then run:

```bash
alembic upgrade head
```

To inspect the SQL without applying it:

```bash
alembic upgrade head --sql
```

### Verification

Run:

```bash
pytest -q
```

The Phase 1 schema tests verify:

- expected tables are registered
- tenant keys exist
- brand-scoped assignments use composite cross-tenant foreign keys
- platform accounts cannot cross a brand/workspace boundary
- brand platform profiles are unique per brand/platform/language

## Architecture rule

Phase 1 does not modify `app/main.py` or automatically run migrations during application startup. This is intentional: the database foundation is introduced without changing the existing Telegram/FastAPI runtime behavior.

The next phase will add database-backed services and authorization enforcement before application routes are migrated.
