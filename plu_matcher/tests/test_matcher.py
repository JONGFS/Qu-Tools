from src.matcher import is_combo_path, match_mapping
from src.models import (
    ApprovedMapping,
    MenuNode,
    ResolutionStatus,
)


def make_mapping(
    *,
    plu: str = "900014",
    qu_item_id: int = 163811,
    qu_name: str = "Lemonade 50/50",
) -> ApprovedMapping:
    return ApprovedMapping(
        aloha_plu=plu,
        aloha_name="SM Fifty-Fifty",
        qu_item_id=qu_item_id,
        qu_name=qu_name,
    )


def make_node(
    *,
    title: str = "Lemonade 50/50",
    plu: str | None = "900014",
    path: str = "100-163811",
    ancestors: tuple[str, ...] = ("Drinks",),
    deleted: bool = False,
) -> MenuNode:
    return MenuNode(
        item_master_id=163811,
        title=title,
        plu=plu,
        item_path_key=path,
        parent_path_key="100",
        item_type=1,
        deleted=deleted,
        ancestors=ancestors,
    )


def test_unique_item_id_and_plu_match():
    mapping = make_mapping()
    candidate = make_node()

    resolution = match_mapping(mapping, [candidate])

    assert resolution.status is ResolutionStatus.MATCHED
    assert resolution.current_node is candidate
    assert resolution.mapping is mapping
    assert resolution.reason == "Matched uniquely by QU item ID and PLU"


def test_missing_item_returns_missing():
    mapping = make_mapping()

    resolution = match_mapping(mapping, [])

    assert resolution.status is ResolutionStatus.MISSING
    assert resolution.current_node is None


def test_only_deleted_candidates_return_missing():
    mapping = make_mapping()

    resolution = match_mapping(
        mapping,
        [make_node(deleted=True)],
    )

    assert resolution.status is ResolutionStatus.MISSING
    assert resolution.current_node is None


def test_item_id_found_but_plu_differs():
    mapping = make_mapping()

    resolution = match_mapping(
        mapping,
        [make_node(plu="DIFFERENT")],
    )

    assert resolution.status is ResolutionStatus.PLU_MISMATCH
    assert resolution.current_node is None


def test_name_narrows_multiple_plu_matches_to_one_candidate():
    mapping = make_mapping(qu_name="Lemonade 50/50")
    expected = make_node(
        title=" lemonade 50/50 ",
        path="100-163811",
    )
    other = make_node(
        title="Different QU Name",
        path="200-163811",
    )

    resolution = match_mapping(mapping, [expected, other])

    assert resolution.status is ResolutionStatus.MATCHED
    assert resolution.current_node is expected
    assert resolution.reason == "Matched uniquely by QU item ID, PLU, and name"


def test_regular_and_combo_paths_return_ambiguous():
    mapping = make_mapping()
    regular = make_node(
        path="100-163811",
        ancestors=("Drinks",),
    )
    combo = make_node(
        path="200-163811",
        ancestors=("Master Menu", "Combos", "Drink Choice"),
    )

    resolution = match_mapping(mapping, [regular, combo])

    assert resolution.status is ResolutionStatus.AMBIGUOUS
    assert resolution.current_node is None
    assert "1 regular and 1 combo" in resolution.reason
    assert "Drinks > Lemonade 50/50" in resolution.reason
    assert "Combos" in resolution.reason


def test_multiple_combo_paths_return_ambiguous():
    mapping = make_mapping()
    first = make_node(
        path="200-163811",
        ancestors=("Combos", "Combo One"),
    )
    second = make_node(
        path="300-163811",
        ancestors=("Combos", "Combo Two"),
    )

    resolution = match_mapping(mapping, [first, second])

    assert resolution.status is ResolutionStatus.AMBIGUOUS
    assert resolution.current_node is None
    assert resolution.reason.startswith("Multiple combo paths")


def test_multiple_regular_paths_return_ambiguous():
    mapping = make_mapping()
    first = make_node(
        path="100-163811",
        ancestors=("Drinks",),
    )
    second = make_node(
        path="400-163811",
        ancestors=("Seasonal Drinks",),
    )

    resolution = match_mapping(mapping, [first, second])

    assert resolution.status is ResolutionStatus.AMBIGUOUS
    assert resolution.current_node is None
    assert resolution.reason.startswith("Multiple regular paths")


def test_combo_detection_is_case_insensitive():
    node = make_node(ancestors=("Master Menu", "SUMMER COMBOS"))

    assert is_combo_path(node) is True
