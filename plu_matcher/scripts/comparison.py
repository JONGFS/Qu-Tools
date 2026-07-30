"""Shared helpers for comparing the QU menu with approved Aloha mappings."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from src.mapping_loader import load_mappings
from src.matcher import match_mapping
from src.menu_parser import flatten_menu, index_by_item_id
from src.models import ApprovedMapping, MenuNode, PathResolution


DEFAULT_MENU_PATH = Path(
    "cache/11934-4685-4723/menu.json"
)
DEFAULT_WORKBOOK_PATH = Path(
    "outputs/Aloha_Qu_Menu_Reconciled_Latest.xlsx"
)


@dataclass
class Comparison:
    mappings: list[ApprovedMapping]
    menu_index: dict[int, list[MenuNode]]
    results: list[PathResolution]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--menu",
        type=Path,
        default=DEFAULT_MENU_PATH,
        help=f"Menu JSON path (default: {DEFAULT_MENU_PATH})",
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK_PATH,
        help=f"Mapping workbook path (default: {DEFAULT_WORKBOOK_PATH})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum rows to print; 0 prints every row",
    )
    return parser.parse_args()


def load_comparison(
    menu_path: Path,
    workbook_path: Path,
) -> Comparison:
    if not menu_path.exists():
        raise FileNotFoundError(
            f"Menu JSON was not found: {menu_path}"
        )
    if not workbook_path.exists():
        raise FileNotFoundError(
            f"Mapping workbook was not found: {workbook_path}. "
            "Run `python -m scripts.reconcile_aloha_mappings` first."
        )

    with menu_path.open(encoding="utf-8-sig") as source:
        menu = json.load(source)

    menu_index = index_by_item_id(flatten_menu(menu))
    mappings = load_mappings(workbook_path)
    results = [
        match_mapping(
            mapping,
            menu_index.get(mapping.qu_item_id, []),
        )
        for mapping in mappings
    ]
    return Comparison(
        mappings=mappings,
        menu_index=menu_index,
        results=results,
    )


def format_path(node: MenuNode) -> str:
    return " > ".join((*node.ancestors, node.title))


def limited(items: list, limit: int) -> list:
    return items[:limit] if limit > 0 else items


def print_heading(category: str, count: int) -> None:
    print(f"{category}: {count}")
    print("=" * 80)
