from app.config import Settings
from app.database.session import normalize_database_url


def test_normalize_database_url():
    assert normalize_database_url("postgres://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert normalize_database_url("postgresql://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert normalize_database_url("postgresql+psycopg://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_settings_reads_railway_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host:5432/db")
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1000000000000")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql://u:p@host:5432/db"


def test_settings_accepts_railway_private_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_PRIVATE_URL", "postgresql://u:p@private-host:5432/db")
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1000000000000")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql://u:p@private-host:5432/db"


def test_settings_rejects_unresolved_railway_reference(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "${{ Postgres.DATABASE_PRIVATE_URL }}")
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "-1000000000000")

    try:
        Settings(_env_file=None)
    except Exception as exc:
        assert "unresolved Railway variable reference" in str(exc)
    else:
        raise AssertionError("Unresolved Railway reference must be rejected")
