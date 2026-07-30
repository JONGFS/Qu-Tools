"""Location profiles for repeatable, multi-location menu checks."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES_PATH = PROJECT_ROOT / "config" / "locations.json"
_PROFILE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


class ProfileConfigurationError(ValueError):
    """Raised when the location profile file is missing or invalid."""


@dataclass(frozen=True)
class LocationProfile:
    """Non-secret settings that identify one effective-menu context."""

    name: str
    location_id: int
    order_channel_id: int
    order_type_id: int
    source_workbook: Path

    @property
    def context_key(self) -> str:
        return (
            f"{self.location_id}-"
            f"{self.order_channel_id}-"
            f"{self.order_type_id}"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "locationId": self.location_id,
            "orderChannelId": self.order_channel_id,
            "orderTypeId": self.order_type_id,
            "sourceWorkbook": str(self.source_workbook),
            "contextKey": self.context_key,
        }


def _profile_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept the documented schema plus the earlier ``locations`` name."""
    if "profiles" in payload:
        profiles = payload["profiles"]
    elif "locations" in payload:
        profiles = payload["locations"]
    else:
        profiles = payload

    if not isinstance(profiles, dict) or not profiles:
        raise ProfileConfigurationError(
            "Location profile JSON must contain a non-empty "
            "'profiles' object."
        )
    return profiles


def _field(
    values: dict[str, Any],
    *,
    camel_name: str,
    snake_name: str,
    profile_name: str,
) -> Any:
    if camel_name in values:
        return values[camel_name]
    if snake_name in values:
        return values[snake_name]
    raise ProfileConfigurationError(
        f"Profile {profile_name!r} is missing {camel_name!r}."
    )


def _positive_integer(
    value: Any,
    *,
    field_name: str,
    profile_name: str,
) -> int:
    if isinstance(value, bool):
        raise ProfileConfigurationError(
            f"Profile {profile_name!r} field {field_name!r} "
            "must be a positive integer."
        )
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise ProfileConfigurationError(
            f"Profile {profile_name!r} field {field_name!r} "
            "must be a positive integer."
        ) from error
    if result <= 0:
        raise ProfileConfigurationError(
            f"Profile {profile_name!r} field {field_name!r} "
            "must be a positive integer."
        )
    return result


def load_profiles(
    config_path: Path = DEFAULT_PROFILES_PATH,
    *,
    project_root: Path | None = None,
) -> dict[str, LocationProfile]:
    """Load all profiles, resolving workbook paths from the project root."""
    config_path = Path(config_path)
    try:
        with config_path.open(encoding="utf-8-sig") as source:
            payload = json.load(source)
    except FileNotFoundError as error:
        raise ProfileConfigurationError(
            f"Location profile file was not found: {config_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ProfileConfigurationError(
            f"Location profile JSON is invalid: {config_path} "
            f"(line {error.lineno}, column {error.colno})"
        ) from error

    if not isinstance(payload, dict):
        raise ProfileConfigurationError(
            "Location profile JSON must contain an object."
        )

    raw_profiles = _profile_mapping(payload)
    path_root = (
        Path(project_root)
        if project_root is not None
        else config_path.resolve().parent.parent
    )
    profiles: dict[str, LocationProfile] = {}
    normalized_names: set[str] = set()

    for raw_name, raw_values in raw_profiles.items():
        name = str(raw_name).strip()
        if not _PROFILE_NAME_PATTERN.fullmatch(name):
            raise ProfileConfigurationError(
                f"Invalid profile name {raw_name!r}. Use only letters, "
                "numbers, underscores, and hyphens."
            )
        normalized_name = name.casefold()
        if normalized_name in normalized_names:
            raise ProfileConfigurationError(
                f"Profile names must be unique ignoring case: {name!r}."
            )
        normalized_names.add(normalized_name)

        if not isinstance(raw_values, dict):
            raise ProfileConfigurationError(
                f"Profile {name!r} must contain an object."
            )

        location_id = _positive_integer(
            _field(
                raw_values,
                camel_name="locationId",
                snake_name="location_id",
                profile_name=name,
            ),
            field_name="locationId",
            profile_name=name,
        )
        order_channel_id = _positive_integer(
            _field(
                raw_values,
                camel_name="orderChannelId",
                snake_name="order_channel_id",
                profile_name=name,
            ),
            field_name="orderChannelId",
            profile_name=name,
        )
        order_type_id = _positive_integer(
            _field(
                raw_values,
                camel_name="orderTypeId",
                snake_name="order_type_id",
                profile_name=name,
            ),
            field_name="orderTypeId",
            profile_name=name,
        )
        workbook_value = _field(
            raw_values,
            camel_name="sourceWorkbook",
            snake_name="source_workbook",
            profile_name=name,
        )
        if not isinstance(workbook_value, str) or not workbook_value.strip():
            raise ProfileConfigurationError(
                f"Profile {name!r} field 'sourceWorkbook' "
                "must be a non-empty path."
            )
        workbook_path = Path(workbook_value.strip()).expanduser()
        if not workbook_path.is_absolute():
            workbook_path = path_root / workbook_path

        profiles[name] = LocationProfile(
            name=name,
            location_id=location_id,
            order_channel_id=order_channel_id,
            order_type_id=order_type_id,
            source_workbook=workbook_path.resolve(),
        )

    return profiles


def get_profile(
    profile_name: str,
    config_path: Path = DEFAULT_PROFILES_PATH,
    *,
    project_root: Path | None = None,
) -> LocationProfile:
    """Return one profile by case-insensitive name."""
    requested_name = profile_name.strip().casefold()
    profiles = load_profiles(config_path, project_root=project_root)
    for name, profile in profiles.items():
        if name.casefold() == requested_name:
            return profile

    available = ", ".join(sorted(profiles, key=str.casefold))
    raise ProfileConfigurationError(
        f"Unknown location profile {profile_name!r}. "
        f"Available profiles: {available}"
    )
