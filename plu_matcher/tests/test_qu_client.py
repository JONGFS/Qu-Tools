import requests

from src.qu_client import QuClient
from src.settings import Settings


class FakeSession:
    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.headers: dict[str, str] = {}
        self.post_call: dict | None = None

    def post(self, url, *, data, timeout):
        self.post_call = {
            "url": url,
            "data": data,
            "timeout": timeout,
        }
        return self.response


def make_settings() -> Settings:
    return Settings(
        base_url="https://gateway-api.qubeyond.com/",
        client_id="client-id",
        client_secret="qu-sid-value",
        x_integration_id="integration-id",
        location_id=11934,
        order_channel_id=4685,
        order_type_id=4723,
    )


def test_authenticate_uses_client_credentials_and_stores_token():
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"access_token": "test-token"}'
    session = FakeSession(response)
    client = QuClient(make_settings(), session=session)

    token = client.authenticate()

    assert token == "test-token"
    assert client.access_token == "test-token"
    assert session.post_call == {
        "url": (
            "https://gateway-api.qubeyond.com"
            "/api/v4/authentication/oauth2/access-token"
        ),
        "data": {
            "grant_type": "client_credentials",
            "client_id": "client-id",
            "client_secret": "qu-sid-value",
        },
        "timeout": 30,
    }
    assert session.headers["Authorization"] == "Bearer test-token"
    assert session.headers["X-Integration"] == "integration-id"
