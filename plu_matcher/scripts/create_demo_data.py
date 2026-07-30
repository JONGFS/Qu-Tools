"""Create sanitized workbook and cache inputs for an offline handoff demo."""

from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import Workbook

from src.cache_manager import CacheManager


DEMO_CONTEXT_KEY = "99999-1-1"


def build_demo_menu() -> dict:
    return {
        "menuSnapshotId": "sanitized-demo-snapshot",
        "context": {
            "companyId": 1,
            "locationId": 99999,
            "orderChannelId": 1,
            "orderTypeId": 1,
        },
        "children": [
            {
                "itemMasterId": 10,
                "title": "Demo Menu",
                "itemPathKey": "10",
                "parentPathKey": None,
                "itemType": 10,
                "children": [
                    {
                        "itemMasterId": 100,
                        "title": "Demo Milk",
                        "itemPathKey": "10-100",
                        "parentPathKey": "10",
                        "itemType": 1,
                        "displayAttribute": {"plu": "900001"},
                        "children": [],
                    },
                    {
                        "itemMasterId": 200,
                        "title": "Demo Tea",
                        "itemPathKey": "10-200",
                        "parentPathKey": "10",
                        "itemType": 1,
                        "displayAttribute": {"plu": "900002"},
                        "children": [],
                    },
                    {
                        "itemMasterId": 300,
                        "title": "Demo Ambiguous A",
                        "itemPathKey": "10-300",
                        "parentPathKey": "10",
                        "itemType": 1,
                        "displayAttribute": {"plu": "900003"},
                        "children": [],
                    },
                    {
                        "itemMasterId": 301,
                        "title": "Demo Ambiguous B",
                        "itemPathKey": "10-301",
                        "parentPathKey": "10",
                        "itemType": 1,
                        "displayAttribute": {"plu": "900003"},
                        "children": [],
                    },
                ],
            }
        ],
    }


def create_demo_data(
    project_root: Path,
    *,
    force: bool = False,
) -> tuple[Path, Path]:
    project_root = Path(project_root).resolve()
    workbook_path = (
        project_root / "inputs" / "Aloha_Qu_Menu_Demo.xlsx"
    )
    cache = CacheManager(project_root / "cache")
    menu_path = cache.menu_path(DEMO_CONTEXT_KEY)

    if workbook_path.exists() and not force:
        raise FileExistsError(
            f"Demo workbook already exists: {workbook_path}. "
            "Use --force to recreate sanitized demo data."
        )

    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Aloha > Qu Item Migration"
    for _ in range(7):
        sheet.append([])
    sheet.append(
        [
            "Number",
            "Long name",
            "Migrated to Qu?",
            "Qu Item ID",
            "Qu Item Name",
        ]
    )
    sheet.append(
        ["900001", "Demo Milk", "Yes", 100, "Demo Milk"]
    )
    sheet.append(
        ["900002", "Demo Tea", "Yes", 999, "Old Demo Tea"]
    )
    sheet.append(
        ["900003", "Demo Ambiguous", "Yes", None, None]
    )
    workbook.save(workbook_path)
    workbook.close()

    cache.save_menu(
        DEMO_CONTEXT_KEY,
        build_demo_menu(),
        "sanitized-demo-generation-1",
    )
    return workbook_path, menu_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create sanitized inputs for `qu-tools run --offline`."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    workbook_path, menu_path = create_demo_data(
        args.project_root,
        force=args.force,
    )
    print(f"Demo workbook: {workbook_path}")
    print(f"Demo menu cache: {menu_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
