from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def normalize_database_url(value: str) -> str:
    url = value.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def get_database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DATABASE_URL is required for database operations. "
            "Configure PostgreSQL before running migrations or the database-backed app."
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
