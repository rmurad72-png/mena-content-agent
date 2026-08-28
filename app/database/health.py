from __future__ import annotations

from sqlalchemy import text

from app.database.session import get_engine


def check_database_connection() -> dict[str, str]:
    """Run a minimal, read-only database connectivity check."""
    engine = get_engine()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    finally:
        # Do not dispose the shared engine after each health check.
        # The pool belongs to the application process.
        pass
