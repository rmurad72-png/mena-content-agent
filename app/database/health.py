from __future__ import annotations

from sqlalchemy import text

from app.database.session import get_engine


def check_database_connection() -> dict[str, str]:
    engine = get_engine()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    finally:
        engine.dispose()
