"""Run reconciliation and path matching against one consistent input set."""

import argparse
from collections import Counter
import json
from pathlib import Path

from src.reconciliation import reconcile_workbook

from .comparison import load_comparison


DEFAULT_SOURCE = Path(
    "outputs/Aloha_Qu_Menu_Reconciled.xlsx"
)
DEFAULT_MENU = Path(
    "cache/11934-4685-4723/menu.json"
)
DEFAULT_OUTPUT = Path(
    "outputs/Aloha_Qu_Menu_Reconciled_Latest.xlsx"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile Aloha mappings and run path matching."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--menu", type=Path, default=DEFAULT_MENU)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--include-unmigrated",
        action="store_true",
        help="Also discover and backfill rows not marked Migrated to Qu.",
    )
    args = parser.parse_args()

    metadata_path = args.menu.with_name("metadata.json")
    provenance = {}
    if metadata_path.exists():
        provenance = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )

    try:
        reconciliation_counts = reconcile_workbook(
            source_workbook=args.source,
            menu_path=args.menu,
            output_workbook=args.output,
            include_unmigrated=args.include_unmigrated,
            provenance=provenance,
        )
    except PermissionError as error:
        raise SystemExit(
            f"Cannot write {args.output}. Close the workbook in Excel "
            "and run this command again."
        ) from error
    comparison = load_comparison(args.menu, args.output)
    resolution_counts = Counter(
        result.status.value
        for result in comparison.results
    )

    print(f"Menu: {args.menu}")
    print(f"Reconciled workbook: {args.output}")
    print("\nRECONCILIATION")
    print("-" * 40)
    for status, count in sorted(reconciliation_counts.items()):
        print(f"{status}: {count}")
    print(f"TOTAL: {sum(reconciliation_counts.values())}")

    print("\nPATH MATCHING (SAFE IDENTITIES ONLY)")
    print("-" * 40)
    for status, count in sorted(resolution_counts.items()):
        print(f"{status}: {count}")
    print(f"TOTAL: {sum(resolution_counts.values())}")

    print("\nReview commands:")
    print(
        "  python -m scripts.print_reconciliation_review "
        f'--workbook "{args.output}"'
    )
    print(
        "  python -m scripts.print_path_review "
        f'--menu "{args.menu}" --workbook "{args.output}"'
    )
    print(
        "  python -m scripts.print_plu_mismatches "
        f'--menu "{args.menu}" --workbook "{args.output}"'
    )


if __name__ == "__main__":
    main()
