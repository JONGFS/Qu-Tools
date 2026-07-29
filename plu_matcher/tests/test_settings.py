from src.settings import load_settings


def _set_required_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "QU_BASE_URL",
        "https://gateway-api.qubeyond.com",
    )
    monkeypatch.setenv("QU_CLIENT_ID", "client-id")
    monkeypatch.setenv("QU_X_INTEGRATION", "integration-id")
    monkeypatch.setenv("QU_LOCATION_ID", "11934")
    monkeypatch.setenv("QU_ORDER_CHANNEL_ID", "4685")
    monkeypatch.setenv("QU_ORDER_TYPE_ID", "4723")
    monkeypatch.setattr("src.settings.load_dotenv", lambda: None)


def test_load_settings_reads_client_secret(monkeypatch):
    _set_required_environment(monkeypatch)
    monkeypatch.setenv("QU_CLIENT_SECRET", "secret-value")
    monkeypatch.delenv("QU_SESSION_ID", raising=False)

    settings = load_settings()

    assert settings.client_secret == "secret-value"


def test_load_settings_temporarily_supports_session_id(monkeypatch):
    _set_required_environment(monkeypatch)
    monkeypatch.delenv("QU_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("QU_SESSION_ID", "legacy-secret-value")

    settings = load_settings()

    assert settings.client_secret == "legacy-secret-value"
