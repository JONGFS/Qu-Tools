"""Create a safely reconciled copy of the Aloha-to-QU workbook."""

import argparse
import json
from pathlib import Path

from src.reconciliation import reconcile_workbook


DEFAULT_SOURCE = Path(
    "outputs/Aloha_Qu_Menu_Reconciled.xlsx"
)
DEFAULT_MENU = Path(
    "cache/11934-4685-4723/menu.json"
)
DEFAULT_OUTPUT = Path(
    "outputs/Aloha_Qu_Menu_Reconciled_Latest.xlsx"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill safe exact-PLU matches and flag ambiguous mappings."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
    )
    parser.add_argument(
        "--menu",
        type=Path,
        default=DEFAULT_MENU,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--include-unmigrated",
        action="store_true",
        help="Also discover and backfill rows not marked Migrated to Qu.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata_path = args.menu.with_name("metadata.json")
    provenance = {}
    if metadata_path.exists():
        provenance = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
    counts = reconcile_workbook(
        source_workbook=args.source,
        menu_path=args.menu,
        output_workbook=args.output,
        include_unmigrated=args.include_unmigrated,
        provenance=provenance,
    )

    print(f"Saved: {args.output}")
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")
    print(f"TOTAL: {sum(counts.values())}")


if __name__ == "__main__":
    main()
