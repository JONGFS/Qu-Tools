"""Print approved mappings whose current QU PLU differs."""

from src.models import ResolutionStatus
from src.normalization import normalize_plu

from .comparison import (
    limited,
    load_comparison,
    parse_args,
    print_heading,
)


def main() -> None:
    args = parse_args("Print Aloha-to-QU PLU mismatches.")
    comparison = load_comparison(args.menu, args.workbook)
    results = [
        result
        for result in comparison.results
        if result.status is ResolutionStatus.PLU_MISMATCH
    ]

    print_heading("PLU_MISMATCH", len(results))
    for result in limited(results, args.limit):
        candidates = comparison.menu_index.get(
            result.mapping.qu_item_id,
            [],
        )
        actual_plus = sorted(
            {
                normalize_plu(node.plu)
                for node in candidates
                if not node.deleted and node.plu is not None
            }
        )
        print(
            f"Expected PLU={result.mapping.aloha_plu} | "
            f"QU ID={result.mapping.qu_item_id} | "
            f"Name={result.mapping.qu_name} | "
            f"Current PLUs={actual_plus}"
        )


if __name__ == "__main__":
    main()
