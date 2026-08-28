from unittest.mock import patch

from app.database import session


def test_engine_is_cached_and_uses_connection_safety_options():
    session.get_engine.cache_clear()
    with patch(
        "app.database.session.create_engine",
        return_value=object(),
    ) as create_engine:
        first = session.get_engine()
        second = session.get_engine()

    assert first is second
    create_engine.assert_called_once_with(
        "postgresql+psycopg://test:test@localhost:5432/testdb",
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 10},
        future=True,
    )
    session.get_engine.cache_clear()


def test_dispose_database_engine_clears_caches():
    session.get_engine.cache_clear()
    session.get_session_factory.cache_clear()

    fake_engine = type("FakeEngine", (), {"dispose": lambda self: None})()
    with patch("app.database.session.create_engine", return_value=fake_engine):
        assert session.get_engine() is fake_engine
        session.get_session_factory()

    with patch.object(fake_engine, "dispose") as dispose:
        session.dispose_database_engine()
        dispose.assert_called_once()

    assert session.get_engine.cache_info().currsize == 0
    assert session.get_session_factory.cache_info().currsize == 0
