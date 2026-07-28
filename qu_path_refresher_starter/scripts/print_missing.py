"""Print approved mappings whose QU item ID is absent from the menu."""

from src.models import ResolutionStatus

from .comparison import (
    limited,
    load_comparison,
    parse_args,
    print_heading,
)


def main() -> None:
    args = parse_args("Print approved mappings missing from the QU menu.")
    comparison = load_comparison(args.menu, args.workbook)
    results = [
        result
        for result in comparison.results
        if result.status is ResolutionStatus.MISSING
    ]

    print_heading("MISSING", len(results))
    for result in limited(results, args.limit):
        print(
            f"PLU={result.mapping.aloha_plu} | "
            f"QU ID={result.mapping.qu_item_id} | "
            f"Aloha Name={result.mapping.aloha_name} | "
            f"QU Name={result.mapping.qu_name} | "
            f"Reason={result.reason}"
        )


if __name__ == "__main__":
    main()
