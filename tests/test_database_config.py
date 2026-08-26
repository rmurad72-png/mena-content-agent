import pytest

from app.database.session import normalize_database_url


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "postgres://user:pass@host:5432/db",
            "postgresql+psycopg://user:pass@host:5432/db",
        ),
        (
            "postgresql://user:pass@host:5432/db",
            "postgresql+psycopg://user:pass@host:5432/db",
        ),
        (
            "postgresql+psycopg://user:pass@host:5432/db",
            "postgresql+psycopg://user:pass@host:5432/db",
        ),
    ],
)
def test_normalize_database_url(value, expected):
    assert normalize_database_url(value) == expected
