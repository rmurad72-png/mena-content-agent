from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def normalize_database_url(value: str) -> str:
    """Normalize Railway/PostgreSQL URLs to the psycopg SQLAlchemy driver."""
    url = value.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def get_database_url() -> str:
    value = settings.database_url
    if not value or not value.strip():
        raise RuntimeError(
            "DATABASE_URL is required for database operations. "
            "Configure Railway PostgreSQL before running database operations."
        )
    return normalize_database_url(value)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine.

    Creating an engine per request creates unnecessary pools and can exhaust
    database connections under load. A single cached engine is the correct
    lifecycle for this application process.
    """
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 10},
        future=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def dispose_database_engine() -> None:
    """Dispose the cached engine and clear its factory cache.

    Intended for controlled shutdown/tests. Normal request handling should
    reuse the cached engine.
    """
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
