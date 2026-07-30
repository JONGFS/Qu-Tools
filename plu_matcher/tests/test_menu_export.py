import csv
import json

from src.menu_export import export_cached_menu, export_menu


def _sample_menu():
    return {
        "menuSnapshotId": "menu-snapshot",
        "context": {
            "companyId": 447,
            "locationId": 11934,
            "orderChannelId": 4685,
            "orderTypeId": 4723,
            "mealPeriodId": 617,
        },
        "children": [
            {
                "itemMasterId": 10,
                "title": "Combos",
                "itemPathKey": "10",
                "parentPathKey": None,
                "itemType": 10,
                "children": [
                    {
                        "itemMasterId": 20,
                        "title": "Korean ShackBurger",
                        "itemPathKey": "10-20",
                        "parentPathKey": "10",
                        "itemType": 1,
                        "displayAttribute": {"plu": 950285.0},
                        "children": [],
                    }
                ],
            },
            {
                "itemMasterId": 30,
                "title": "Burgers",
                "itemPathKey": "30",
                "parentPathKey": None,
                "itemType": 10,
                "children": [
                    {
                        "itemMasterId": 20,
                        "title": "Korean ShackBurger",
                        "itemPathKey": "30-20",
                        "parentPathKey": "30",
                        "itemType": 1,
                        "displayAttribute": {"plu": "950285"},
                        "deleted": True,
                        "children": [],
                    }
                ],
            },
        ],
    }


def test_export_menu_preserves_occurrences_and_provenance(tmp_path):
    csv_path = tmp_path / "flat" / "flattened_menu.csv"
    json_path = tmp_path / "flat" / "flattened_menu.json"

    count = export_menu(
        _sample_menu(),
        csv_path,
        json_path,
        metadata={
            "location": "atlanta",
            "generation_time": "2026-07-30T10:00:00Z",
        },
    )

    assert count == 4
    with json_path.open(encoding="utf-8") as source:
        exported = json.load(source)

    assert exported["metadata"] == {
        "location": "atlanta",
        "menu_snapshot_id": "menu-snapshot",
        "generation_time": "2026-07-30T10:00:00Z",
        "context": {
            "companyId": 447,
            "locationId": 11934,
            "orderChannelId": 4685,
            "orderTypeId": 4723,
            "mealPeriodId": 617,
        },
        "location_id": 11934,
        "company_id": 447,
        "order_channel_id": 4685,
        "order_type_id": 4723,
        "meal_period_id": 617,
    }

    occurrences = [
        item
        for item in exported["items"]
        if item["item_master_id"] == 20
    ]
    assert len(occurrences) == 2
    assert {item["item_path_key"] for item in occurrences} == {
        "10-20",
        "30-20",
    }
    assert {item["plu"] for item in occurrences} == {"950285"}

    combo = next(
        item for item in occurrences
        if item["item_path_key"] == "10-20"
    )
    assert combo["ancestors"] == ["Combos"]
    assert combo["full_path"] == "Combos > Korean ShackBurger"
    assert combo["path_classification"] == "COMBO"
    assert combo["active"] is True
    assert combo["deleted"] is False

    deleted = next(
        item for item in occurrences
        if item["item_path_key"] == "30-20"
    )
    assert deleted["path_classification"] == "REGULAR"
    assert deleted["active"] is False
    assert deleted["deleted"] is True

    with csv_path.open(
        encoding="utf-8-sig",
        newline="",
    ) as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 4
    csv_combo = next(
        row for row in rows
        if row["item_path_key"] == "10-20"
    )
    assert csv_combo["location"] == "atlanta"
    assert csv_combo["location_id"] == "11934"
    assert csv_combo["menu_snapshot_id"] == "menu-snapshot"
    assert csv_combo["plu"] == "950285"
    assert csv_combo["ancestors"] == "Combos"
    assert json.loads(csv_combo["context"])["orderTypeId"] == 4723


def test_export_cached_menu_loads_adjacent_metadata_and_allows_override(
    tmp_path,
):
    cache = tmp_path / "cache" / "11934-4685-4723"
    cache.mkdir(parents=True)
    menu_path = cache / "menu.json"
    metadata_path = cache / "metadata.json"
    menu_path.write_text(
        json.dumps(_sample_menu()),
        encoding="utf-8",
    )
    metadata_path.write_text(
        json.dumps(
            {
                "generation_time": "cached-time",
                "menu_snapshot_id": "cached-snapshot",
                "context": {"orderTypeId": 4000},
            }
        ),
        encoding="utf-8",
    )

    csv_path = tmp_path / "menu.csv"
    json_path = tmp_path / "menu.json"
    count = export_cached_menu(
        menu_path,
        csv_path,
        json_path,
        metadata={
            "location": "atlanta",
            "context": {"orderTypeId": 4723},
        },
    )

    assert count == 4
    exported = json.loads(json_path.read_text(encoding="utf-8"))
    metadata = exported["metadata"]
    assert metadata["location"] == "atlanta"
    assert metadata["generation_time"] == "cached-time"
    assert metadata["menu_snapshot_id"] == "cached-snapshot"
    assert metadata["context"]["locationId"] == 11934
    assert metadata["context"]["orderTypeId"] == 4723


def test_export_cached_menu_rejects_non_object_json(tmp_path):
    menu_path = tmp_path / "menu.json"
    menu_path.write_text("[]", encoding="utf-8")

    try:
        export_cached_menu(
            menu_path,
            tmp_path / "menu.csv",
            tmp_path / "flat.json",
        )
    except ValueError as error:
        assert "must contain a JSON object" in str(error)
    else:
        raise AssertionError("Expected invalid cached menu to fail.")


def test_export_cached_menu_requires_explicit_metadata_path(tmp_path):
    menu_path = tmp_path / "menu.json"
    menu_path.write_text(
        json.dumps(_sample_menu()),
        encoding="utf-8",
    )

    missing_metadata = tmp_path / "missing-metadata.json"
    try:
        export_cached_menu(
            menu_path,
            tmp_path / "menu.csv",
            tmp_path / "flat.json",
            metadata_path=missing_metadata,
        )
    except FileNotFoundError as error:
        assert str(missing_metadata) in str(error)
    else:
        raise AssertionError("Expected missing metadata to fail.")
