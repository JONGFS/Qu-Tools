"""Export a cached nested QU menu as flat, auditable artifacts."""

from __future__ import annotations

from collections.abc import Mapping
import csv
import json
from pathlib import Path
from typing import Any

from .menu_parser import flatten_menu
from .models import MenuNode
from .normalization import normalize_plu


MENU_ITEM_FIELDS = (
    "item_master_id",
    "plu",
    "title",
    "item_path_key",
    "parent_path_key",
    "full_path",
    "ancestors",
    "item_type",
    "deleted",
    "active",
    "path_classification",
)

MENU_METADATA_FIELDS = (
    "location",
    "location_id",
    "company_id",
    "order_channel_id",
    "order_type_id",
    "meal_period_id",
    "menu_snapshot_id",
    "generation_time",
    "context",
)

MENU_CSV_FIELDS = MENU_METADATA_FIELDS + MENU_ITEM_FIELDS

_CONTEXT_EXPORT_KEYS = {
    "location_id": "locationId",
    "company_id": "companyId",
    "order_channel_id": "orderChannelId",
    "order_type_id": "orderTypeId",
    "meal_period_id": "mealPeriodId",
}


def _as_mapping(value: object, *, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping.")
    return dict(value)


def _merge_metadata(
    menu: Mapping[str, Any],
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    supplied = _as_mapping(metadata, name="metadata")
    menu_context = _as_mapping(menu.get("context"), name="menu context")
    supplied_context = _as_mapping(
        supplied.get("context"),
        name="metadata context",
    )
    context = {**menu_context, **supplied_context}

    snapshot_id = (
        supplied.get("menu_snapshot_id")
        or supplied.get("menuSnapshotId")
        or menu.get("menuSnapshotId")
    )
    generation_time = (
        supplied.get("generation_time")
        or supplied.get("generationTime")
        or menu.get("generationTime")
    )
    location = (
        supplied.get("location")
        or supplied.get("location_name")
        or ""
    )

    normalized: dict[str, Any] = {
        "location": str(location).strip(),
        "menu_snapshot_id": snapshot_id,
        "generation_time": generation_time,
        "context": context,
    }
    for export_key, context_key in _CONTEXT_EXPORT_KEYS.items():
        normalized[export_key] = supplied.get(
            export_key,
            context.get(context_key),
        )

    return normalized


def _readable_segments(node: MenuNode) -> tuple[str, ...]:
    return tuple(
        segment.strip()
        for segment in (*node.ancestors, node.title or "")
        if segment and segment.strip()
    )


def _classify_path(node: MenuNode) -> str:
    is_combo = any(
        "combo" in segment.casefold()
        for segment in _readable_segments(node)
    )
    return "COMBO" if is_combo else "REGULAR"


def _item_row(node: MenuNode) -> dict[str, Any]:
    ancestors = [
        segment.strip()
        for segment in node.ancestors
        if segment and segment.strip()
    ]
    return {
        "item_master_id": node.item_master_id,
        "plu": normalize_plu(node.plu),
        "title": str(node.title or "").strip(),
        "item_path_key": node.item_path_key or "",
        "parent_path_key": node.parent_path_key or "",
        "full_path": " > ".join(_readable_segments(node)),
        "ancestors": ancestors,
        "item_type": node.item_type,
        "deleted": node.deleted,
        "active": not node.deleted,
        "path_classification": _classify_path(node),
    }


def build_menu_export(
    menu: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a JSON-ready flattened menu and its provenance metadata."""
    if not isinstance(menu, Mapping):
        raise TypeError("menu must be a mapping.")

    menu_dict = dict(menu)
    items = [
        _item_row(node)
        for node in flatten_menu(menu_dict)
    ]
    return {
        "metadata": _merge_metadata(menu_dict, metadata),
        "items": items,
    }


def _csv_row(
    metadata: Mapping[str, Any],
    item: Mapping[str, Any],
) -> dict[str, Any]:
    row = {**metadata, **item}
    row["context"] = json.dumps(
        metadata.get("context") or {},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    row["ancestors"] = " > ".join(item.get("ancestors") or [])
    return row


def export_menu(
    menu: Mapping[str, Any],
    csv_path: Path,
    json_path: Path,
    metadata: Mapping[str, Any] | None = None,
) -> int:
    """Write flattened menu CSV/JSON files and return occurrence count."""
    export = build_menu_export(menu, metadata)
    csv_path = Path(csv_path)
    json_path = Path(json_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=MENU_CSV_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        for item in export["items"]:
            writer.writerow(_csv_row(export["metadata"], item))

    with json_path.open("w", encoding="utf-8") as destination:
        json.dump(
            export,
            destination,
            ensure_ascii=False,
            indent=2,
        )
        destination.write("\n")

    return len(export["items"])


def export_cached_menu(
    menu_path: Path,
    csv_path: Path,
    json_path: Path,
    *,
    metadata_path: Path | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> int:
    """Load a cache entry, merge metadata, and export every occurrence.

    When ``metadata_path`` is omitted, an adjacent ``metadata.json`` is
    loaded when present. Explicit ``metadata`` values take precedence.
    """
    menu_path = Path(menu_path)
    with menu_path.open(encoding="utf-8-sig") as source:
        menu = json.load(source)
    if not isinstance(menu, dict):
        raise ValueError(
            f"Cached menu must contain a JSON object: {menu_path}"
        )

    resolved_metadata_path = (
        Path(metadata_path)
        if metadata_path is not None
        else menu_path.with_name("metadata.json")
    )
    cached_metadata: dict[str, Any] = {}
    if (
        metadata_path is not None
        and not resolved_metadata_path.exists()
    ):
        raise FileNotFoundError(
            f"Cache metadata was not found: {resolved_metadata_path}"
        )
    if resolved_metadata_path.exists():
        with resolved_metadata_path.open(
            encoding="utf-8-sig",
        ) as source:
            loaded_metadata = json.load(source)
        if not isinstance(loaded_metadata, dict):
            raise ValueError(
                "Cache metadata must contain a JSON object: "
                f"{resolved_metadata_path}"
            )
        cached_metadata = loaded_metadata

    supplied_metadata = _as_mapping(metadata, name="metadata")
    merged_context = {
        **_as_mapping(
            cached_metadata.get("context"),
            name="cache metadata context",
        ),
        **_as_mapping(
            supplied_metadata.get("context"),
            name="metadata context",
        ),
    }
    merged_metadata = {
        **cached_metadata,
        **supplied_metadata,
        "context": merged_context,
    }
    return export_menu(
        menu,
        csv_path,
        json_path,
        merged_metadata,
    )
