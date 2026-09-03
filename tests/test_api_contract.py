from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "app" / "main.py"


def test_api_contract_exposes_db_health_and_release_version():
    text = MAIN.read_text()
    assert 'APP_VERSION = "0.6.1"' in text
    assert '@app.get("/health/db")' in text
    assert 'status_code=503' in text
    assert 'detail="database unavailable"' in text


def test_publish_ui_does_not_advertise_unimplemented_platforms():
    text = MAIN.read_text()
    assert 'callback_data="channel_telegram"' in text
    assert 'callback_data="channel_x"' not in text
    assert 'callback_data="channel_reddit"' not in text
