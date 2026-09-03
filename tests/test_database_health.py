from unittest.mock import MagicMock, patch

from app.database.health import check_database_connection


def test_database_health_reports_uninitialized_migrations_read_only():
    fake_connection = MagicMock()
    fake_connection.execute.side_effect = [
        MagicMock(scalar=lambda: 1),
        MagicMock(scalar=lambda: False),
    ]
    fake_engine = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = fake_connection

    with patch("app.database.health.get_engine", return_value=fake_engine), patch(
        "app.database.health._migration_heads", return_value=["001_phase1"]
    ):
        result = check_database_connection()

    assert result["status"] == "ok"
    assert result["database"] == "reachable"
    assert result["migration"]["status"] == "not_initialized"
    assert result["migration"]["current_revision"] is None
    assert result["migration"]["head_revision"] == "001_phase1"
    assert result["migration"]["migration_required"] is True
    fake_engine.dispose.assert_not_called()


def test_database_health_reports_up_to_date_migrations_read_only():
    fake_connection = MagicMock()
    fake_connection.execute.side_effect = [
        MagicMock(scalar=lambda: 1),
        MagicMock(scalar=lambda: True),
        MagicMock(fetchall=lambda: [("001_phase1",)]),
    ]
    fake_engine = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = fake_connection

    with patch("app.database.health.get_engine", return_value=fake_engine), patch(
        "app.database.health._migration_heads", return_value=["001_phase1"]
    ):
        result = check_database_connection()

    assert result["migration"]["status"] == "up_to_date"
    assert result["migration"]["current_revision"] == "001_phase1"
    assert result["migration"]["migration_required"] is False
    fake_engine.dispose.assert_not_called()
