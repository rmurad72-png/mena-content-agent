from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def normalize_database_url(value: str) -> str:
    url = value.strip()

    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]

    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]

    return url


def get_database_url() -> str:
    value = settings.database_url

    if not value:
        raise RuntimeError(
            "DATABASE_URL is required for database operations. "
            "Configure Railway PostgreSQL before running database operations."
        )

    return normalize_database_url(value)


def get_engine() -> Engine:
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        future=True,
    )


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
