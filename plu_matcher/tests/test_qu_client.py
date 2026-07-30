from dataclasses import replace

import requests

import pytest

from src.qu_client import (
    QuAuthenticationError,
    QuClient,
    QuMenuRequestError,
)
from src.settings import Settings


class FakeSession:
    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.headers: dict[str, str] = {}
        self.post_call: dict | None = None
        self.get_call: dict | None = None

    def post(self, url, *, data, timeout):
        self.post_call = {
            "url": url,
            "data": data,
            "timeout": timeout,
        }
        return self.response

    def get(self, url, *, params, timeout):
        self.get_call = {
            "url": url,
            "params": params,
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


def test_authenticate_reports_rejected_credentials():
    response = requests.Response()
    response.status_code = 401
    response._content = b'{"error": "invalid_client"}'
    session = FakeSession(response)
    client = QuClient(make_settings(), session=session)

    with pytest.raises(
        QuAuthenticationError,
        match="HTTP 401",
    ):
        client.authenticate()


def test_fetch_menu_uses_context_and_previous_generation_time():
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"children":[]}'
    session = FakeSession(response)
    client = QuClient(make_settings(), session=session)
    client.access_token = "token"

    client.fetch_menu(previous_generation_time="generation-1")

    assert session.get_call == {
        "url": "https://gateway-api.qubeyond.com/api/v4/menus",
        "params": {
            "LocationId": 11934,
            "OrderChannelId": 4685,
            "OrderTypeId": 4723,
            "PrevGenerationTime": "generation-1",
        },
        "timeout": 60,
    }


def test_fetch_menu_reports_http_failure_with_context():
    response = requests.Response()
    response.status_code = 500
    response._content = b'{"error":"server"}'
    session = FakeSession(response)
    client = QuClient(make_settings(), session=session)
    client.access_token = "token"

    with pytest.raises(
        QuMenuRequestError,
        match=r"HTTP 500.*location 11934",
    ):
        client.fetch_menu()


def test_client_accepts_base_url_that_already_contains_v4_path():
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"access_token": "test-token"}'
    session = FakeSession(response)
    settings = replace(
        make_settings(),
        base_url="https://gateway-api.qubeyond.com/api/v4",
    )

    QuClient(settings, session=session).authenticate()

    assert session.post_call["url"] == (
        "https://gateway-api.qubeyond.com"
        "/api/v4/authentication/oauth2/access-token"
    )
