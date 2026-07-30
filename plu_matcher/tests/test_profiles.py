import json

import pytest

from src.profiles import (
    ProfileConfigurationError,
    get_profile,
    load_profiles,
)


def write_profiles(path, profiles):
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"profiles": profiles}),
        encoding="utf-8",
    )


def test_load_profiles_resolves_workbook_from_project_root(tmp_path):
    config_path = tmp_path / "config" / "locations.json"
    write_profiles(
        config_path,
        {
            "atlanta": {
                "locationId": 11934,
                "orderChannelId": 4685,
                "orderTypeId": 4723,
                "sourceWorkbook": "inputs/Aloha.xlsx",
            }
        },
    )

    profiles = load_profiles(config_path)

    profile = profiles["atlanta"]
    assert profile.context_key == "11934-4685-4723"
    assert profile.source_workbook == (
        tmp_path / "inputs" / "Aloha.xlsx"
    ).resolve()


def test_get_profile_is_case_insensitive(tmp_path):
    config_path = tmp_path / "config" / "locations.json"
    write_profiles(
        config_path,
        {
            "Atlanta-Lab": {
                "locationId": "11934",
                "orderChannelId": "4685",
                "orderTypeId": "4723",
                "sourceWorkbook": "inputs/Aloha.xlsx",
            }
        },
    )

    profile = get_profile("atlanta-lab", config_path)

    assert profile.name == "Atlanta-Lab"
    assert profile.location_id == 11934


@pytest.mark.parametrize(
    "profile_values, message",
    [
        (
            {
                "orderChannelId": 4685,
                "orderTypeId": 4723,
                "sourceWorkbook": "inputs/Aloha.xlsx",
            },
            "locationId",
        ),
        (
            {
                "locationId": 11934,
                "orderChannelId": 4685,
                "orderTypeId": 4723,
                "sourceWorkbook": "",
            },
            "sourceWorkbook",
        ),
        (
            {
                "locationId": 0,
                "orderChannelId": 4685,
                "orderTypeId": 4723,
                "sourceWorkbook": "inputs/Aloha.xlsx",
            },
            "positive integer",
        ),
    ],
)
def test_invalid_profile_has_actionable_error(
    tmp_path,
    profile_values,
    message,
):
    config_path = tmp_path / "config" / "locations.json"
    write_profiles(config_path, {"atlanta": profile_values})

    with pytest.raises(ProfileConfigurationError, match=message):
        load_profiles(config_path)


def test_unknown_profile_lists_available_names(tmp_path):
    config_path = tmp_path / "config" / "locations.json"
    write_profiles(
        config_path,
        {
            "atlanta": {
                "locationId": 11934,
                "orderChannelId": 4685,
                "orderTypeId": 4723,
                "sourceWorkbook": "inputs/Aloha.xlsx",
            }
        },
    )

    with pytest.raises(ProfileConfigurationError) as caught:
        get_profile("new-york", config_path)

    assert "Available profiles: atlanta" in str(caught.value)
