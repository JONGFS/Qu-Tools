"""Print mappings that uniquely match a current QU menu path."""

from src.models import ResolutionStatus

from .comparison import (
    format_path,
    limited,
    load_comparison,
    parse_args,
    print_heading,
)


def main() -> None:
    args = parse_args("Print uniquely matched Aloha-to-QU mappings.")
    comparison = load_comparison(args.menu, args.workbook)
    results = [
        result
        for result in comparison.results
        if result.status is ResolutionStatus.MATCHED
    ]

    print_heading("MATCHED", len(results))
    for result in limited(results, args.limit):
        node = result.current_node
        path = format_path(node) if node is not None else ""
        print(
            f"PLU={result.mapping.aloha_plu} | "
            f"QU ID={result.mapping.qu_item_id} | "
            f"Name={result.mapping.qu_name} | "
            f"Path={path}"
        )


if __name__ == "__main__":
    main()
