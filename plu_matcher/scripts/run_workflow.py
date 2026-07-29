"""Run reconciliation and path matching against one consistent input set."""

import argparse
from collections import Counter
from pathlib import Path

from src.reconciliation import reconcile_workbook

from .comparison import load_comparison


DEFAULT_SOURCE = Path(
    "private_data/Aloha_Qu_Menu_In_Progress.xlsx"
)
DEFAULT_MENU = Path("private_data/response+Alc.json")
DEFAULT_OUTPUT = Path(
    "outputs/Aloha_Qu_Menu_Reconciled.xlsx"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile Aloha mappings and run path matching."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--menu", type=Path, default=DEFAULT_MENU)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        reconciliation_counts = reconcile_workbook(
            source_workbook=args.source,
            menu_path=args.menu,
            output_workbook=args.output,
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


if __name__ == "__main__":
    main()
