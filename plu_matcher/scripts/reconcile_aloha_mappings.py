"""Create a safely reconciled copy of the Aloha-to-QU workbook."""

import argparse
from pathlib import Path

from src.reconciliation import reconcile_workbook


DEFAULT_SOURCE = Path(
    "private_data/Aloha_Qu_Menu_In_Progress.xlsx"
)
DEFAULT_MENU = Path("private_data/response+Alc.json")
DEFAULT_OUTPUT = Path(
    "outputs/Aloha_Qu_Menu_Reconciled.xlsx"
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = reconcile_workbook(
        source_workbook=args.source,
        menu_path=args.menu,
        output_workbook=args.output,
    )

    print(f"Saved: {args.output}")
    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")
    print(f"TOTAL: {sum(counts.values())}")


if __name__ == "__main__":
    main()
