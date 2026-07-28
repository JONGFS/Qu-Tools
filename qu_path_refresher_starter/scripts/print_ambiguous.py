"""Print mappings with multiple valid current QU menu paths."""

from src.matcher import is_combo_path, normalize_text
from src.models import ResolutionStatus

from .comparison import (
    format_path,
    limited,
    load_comparison,
    parse_args,
    print_heading,
)


MAX_PATHS_PER_MAPPING = 10


def main() -> None:
    args = parse_args("Print mappings with ambiguous QU menu paths.")
    comparison = load_comparison(args.menu, args.workbook)
    results = [
        result
        for result in comparison.results
        if result.status is ResolutionStatus.AMBIGUOUS
    ]

    print_heading("AMBIGUOUS", len(results))
    for result in limited(results, args.limit):
        expected_plu = normalize_text(result.mapping.aloha_plu)
        candidates = [
            node
            for node in comparison.menu_index.get(
                result.mapping.qu_item_id,
                [],
            )
            if (
                not node.deleted
                and normalize_text(node.plu) == expected_plu
            )
        ]
        combo_count = sum(is_combo_path(node) for node in candidates)
        regular_count = len(candidates) - combo_count

        print(
            f"\nPLU={result.mapping.aloha_plu} | "
            f"QU ID={result.mapping.qu_item_id} | "
            f"Name={result.mapping.qu_name} | "
            f"Regular={regular_count} | Combo={combo_count}"
        )
        for node in candidates[:MAX_PATHS_PER_MAPPING]:
            context = "COMBO" if is_combo_path(node) else "REGULAR"
            print(f"  [{context}] {format_path(node)}")
        remaining = len(candidates) - MAX_PATHS_PER_MAPPING
        if remaining > 0:
            print(f"  ... {remaining} additional paths not shown")


if __name__ == "__main__":
    main()
