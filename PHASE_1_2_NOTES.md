# Phase 1.2 — Database Configuration & Preflight Test Hardening

## Purpose

This revision keeps the Phase 1 domain/database foundation intact and fixes the local test bootstrap so database modules can be imported without real Railway secrets.

## Changes

- `app/config.py` exposes `database_url` through the existing Pydantic Settings object.
- `app/database/session.py` consumes `settings.database_url` rather than reading the environment directly.
- `app/database/health.py` performs a read-only `SELECT 1` check and disposes the test engine.
- `tests/conftest.py` provides harmless test-only environment values before settings are imported.
- No migration is executed by the application startup.
- No production secrets are included.

## Railway rule

Do not run `alembic upgrade head` yet. Phase 1.2 only establishes configuration and a safe connectivity test foundation.
