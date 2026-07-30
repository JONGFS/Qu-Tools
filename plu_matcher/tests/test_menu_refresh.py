from dataclasses import dataclass

import pytest

from src.cache_manager import CacheManager
from src.main import main, refresh_menu
from src.settings import Settings


@dataclass
class FakeResponse:
    status_code: int
    content: bytes
    payload: dict
    headers: dict[str, str]

    def json(self) -> dict:
        return self.payload


class FakeClient:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.authenticated = False
        self.previous_generation_time: str | None = None

    def authenticate(self) -> str:
        self.authenticated = True
        return "token"

    def fetch_menu(
        self,
        previous_generation_time: str | None = None,
    ) -> FakeResponse:
        self.previous_generation_time = previous_generation_time
        return self.response


def make_settings() -> Settings:
    return Settings(
        base_url="https://example.test",
        client_id="client",
        client_secret="secret",
        x_integration_id="integration",
        location_id=11934,
        order_channel_id=4685,
        order_type_id=4723,
    )


def test_first_refresh_downloads_and_saves_menu(tmp_path):
    menu = {"menuSnapshotId": "new", "children": []}
    client = FakeClient(
        FakeResponse(
            status_code=200,
            content=b'{"menuSnapshotId":"new"}',
            payload=menu,
            headers={"X-Generation-Time": "generation-1"},
        )
    )
    cache = CacheManager(tmp_path / "cache")

    result = refresh_menu(make_settings(), client, cache)

    assert result == menu
    assert client.authenticated is True
    assert client.previous_generation_time is None
    assert cache.load_menu("11934-4685-4723") == menu


def test_unchanged_refresh_reuses_cache_and_records_check(tmp_path):
    cached_menu = {"menuSnapshotId": "cached", "children": []}
    cache = CacheManager(tmp_path / "cache")
    cache.save_menu(
        "11934-4685-4723",
        cached_menu,
        "generation-1",
    )
    client = FakeClient(
        FakeResponse(
            status_code=204,
            content=b"",
            payload={},
            headers={},
        )
    )

    result = refresh_menu(make_settings(), client, cache)

    assert result == cached_menu
    assert client.previous_generation_time == "generation-1"
    metadata = cache.load_metadata("11934-4685-4723")
    assert metadata["last_response_status"] == 204


def test_changed_refresh_replaces_cached_menu(tmp_path):
    cache = CacheManager(tmp_path / "cache")
    cache.save_menu(
        "11934-4685-4723",
        {"menuSnapshotId": "old", "children": []},
        "generation-1",
    )
    new_menu = {"menuSnapshotId": "new", "children": []}
    client = FakeClient(
        FakeResponse(
            status_code=200,
            content=b'{"menuSnapshotId":"new"}',
            payload=new_menu,
            headers={"X-Generation-Time": "generation-2"},
        )
    )

    result = refresh_menu(make_settings(), client, cache)

    assert result == new_menu
    assert client.previous_generation_time == "generation-1"
    metadata = cache.load_metadata("11934-4685-4723")
    assert metadata["generation_time"] == "generation-2"


def test_refresh_rejects_menu_for_different_location(tmp_path):
    client = FakeClient(
        FakeResponse(
            status_code=200,
            content=b'{"context":{"locationId":11526}}',
            payload={
                "context": {"locationId": 11526},
                "children": [],
            },
            headers={"X-Generation-Time": "generation-1"},
        )
    )

    with pytest.raises(
        RuntimeError,
        match="different location",
    ):
        refresh_menu(
            make_settings(),
            client,
            CacheManager(tmp_path / "cache"),
        )


def test_main_help_does_not_attempt_live_request(capsys):
    with pytest.raises(SystemExit) as result:
        main(["--help"])

    assert result.value.code == 0
    assert "Refresh one QU menu context" in capsys.readouterr().out
