from __future__ import annotations

from pathlib import Path
import re

from sqlalchemy import text

from app.database.session import get_engine


def _migration_heads() -> list[str]:
    """Return all Alembic heads declared by the application, read-only."""
    project_root = Path(__file__).resolve().parents[2]
    versions_dir = project_root / "alembic" / "versions"
    revisions: dict[str, str | None] = {}
    for path in versions_dir.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        revision_match = re.search(r"^revision:\s*str\s*=\s*[\"']([^\"']+)[\"']", source, re.MULTILINE)
        if not revision_match:
            continue
        revision = revision_match.group(1)
        down_match = re.search(r"^down_revision:\s*Union\[str, None\]\s*=\s*(?:[\"']([^\"']+)[\"']|None)", source, re.MULTILINE)
        revisions[revision] = down_match.group(1) if down_match else None

    if not revisions:
        return []

    referenced = {down for down in revisions.values() if down}
    return sorted(set(revisions) - referenced)


def _migration_state(connection) -> dict[str, object]:
    """Inspect Alembic state without creating or changing any database object."""
    heads = _migration_heads()

    table_exists = bool(
        connection.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'alembic_version'"
                ")"
            )
        ).scalar()
    )

    if not table_exists:
        return {
            "status": "not_initialized",
            "current_revision": None,
            "current_revisions": [],
            "head_revision": heads[0] if len(heads) == 1 else None,
            "head_revisions": heads,
            "migration_required": True,
        }

    current_revisions = [
        str(row[0])
        for row in connection.execute(
            text("SELECT version_num FROM alembic_version ORDER BY version_num")
        ).fetchall()
    ]

    current_set = set(current_revisions)
    head_set = set(heads)
    up_to_date = current_set == head_set and bool(head_set)

    if up_to_date:
        status = "up_to_date"
    elif not current_revisions:
        status = "not_initialized"
    else:
        status = "migration_required"

    return {
        "status": status,
        "current_revision": current_revisions[0] if len(current_revisions) == 1 else None,
        "current_revisions": current_revisions,
        "head_revision": heads[0] if len(heads) == 1 else None,
        "head_revisions": heads,
        "migration_required": not up_to_date,
    }


def check_database_connection() -> dict[str, object]:
    """Run read-only database connectivity and Alembic migration checks."""
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        migration = _migration_state(connection)

    return {
        "status": "ok",
        "database": "reachable",
        "migration": migration,
    }
