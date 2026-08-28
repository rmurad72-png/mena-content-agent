from unittest.mock import MagicMock, patch

from app.database.health import check_database_connection


def test_database_health_executes_select_one_without_disposing_shared_engine():
    fake_connection = MagicMock()
    fake_engine = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = fake_connection

    with patch("app.database.health.get_engine", return_value=fake_engine):
        result = check_database_connection()

    fake_connection.execute.assert_called_once()
    fake_engine.dispose.assert_not_called()
    assert result == {"status": "ok", "database": "reachable"}
