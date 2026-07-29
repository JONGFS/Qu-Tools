from src.models import MenuNode
from src.reconciliation import (
    MenuIndexes,
    STATUS_AMBIGUOUS,
    STATUS_CONFLICT,
    STATUS_MATCH,
    STATUS_MISMATCH,
    STATUS_MULTIPLE_PATHS,
    STATUS_NOT_FOUND,
    STATUS_NOT_IN_CONTEXT,
    decide_reconciliation,
)


def make_node(
    *,
    item_id: int,
    plu: str,
    title: str,
    path: str,
) -> MenuNode:
    return MenuNode(
        item_master_id=item_id,
        title=title,
        plu=plu,
        item_path_key=path,
        parent_path_key=None,
        item_type=1,
        deleted=False,
    )


def make_indexes(*nodes: MenuNode) -> MenuIndexes:
    by_plu: dict[str, list[MenuNode]] = {}
    by_item_id: dict[int, list[MenuNode]] = {}
    for node in nodes:
        by_plu.setdefault(str(node.plu), []).append(node)
        by_item_id.setdefault(node.item_master_id, []).append(node)
    return MenuIndexes(by_plu=by_plu, by_item_id=by_item_id)


def test_unique_item_id_is_safe_to_backfill():
    node = make_node(
        item_id=100,
        plu="900001",
        title="Milk",
        path="1-100",
    )

    decision = decide_reconciliation(
        "900001",
        None,
        "",
        make_indexes(node),
    )

    assert decision.status == STATUS_MATCH
    assert decision.proposed_item_id == 100
    assert decision.apply_mapping is True


def test_one_item_id_on_multiple_paths_is_safe_identity():
    nodes = (
        make_node(
            item_id=100,
            plu="900001",
            title="Milk",
            path="1-100",
        ),
        make_node(
            item_id=100,
            plu="900001",
            title="Milk",
            path="2-100",
        ),
    )

    decision = decide_reconciliation(
        "900001",
        None,
        "",
        make_indexes(*nodes),
    )

    assert decision.status == STATUS_MULTIPLE_PATHS
    assert decision.proposed_item_id == 100
    assert decision.path_count == 2
    assert decision.apply_mapping is True


def test_multiple_item_ids_are_ambiguous_and_not_backfilled():
    nodes = (
        make_node(
            item_id=100,
            plu="900001",
            title="Milk A",
            path="1-100",
        ),
        make_node(
            item_id=200,
            plu="900001",
            title="Milk B",
            path="1-200",
        ),
    )

    decision = decide_reconciliation(
        "900001",
        None,
        "",
        make_indexes(*nodes),
    )

    assert decision.status == STATUS_AMBIGUOUS
    assert decision.proposed_item_id is None
    assert decision.apply_mapping is False
    assert "100:" in decision.candidates
    assert "200:" in decision.candidates


def test_existing_different_item_id_is_preserved_as_conflict():
    node = make_node(
        item_id=200,
        plu="900001",
        title="Current Milk",
        path="1-200",
    )

    decision = decide_reconciliation(
        "900001",
        100,
        "Existing Milk",
        make_indexes(node),
    )

    assert decision.status == STATUS_CONFLICT
    assert decision.proposed_item_id == 200
    assert decision.apply_mapping is False


def test_existing_item_with_different_plu_requires_review():
    node = make_node(
        item_id=100,
        plu="900002",
        title="Milk",
        path="1-100",
    )

    decision = decide_reconciliation(
        "900001",
        100,
        "Milk",
        make_indexes(node),
    )

    assert decision.status == STATUS_MISMATCH
    assert decision.apply_mapping is False
    assert "900002" in decision.notes


def test_unmapped_plu_not_in_qu_is_not_found():
    decision = decide_reconciliation(
        "900001",
        None,
        "",
        make_indexes(),
    )

    assert decision.status == STATUS_NOT_FOUND
    assert decision.apply_mapping is False


def test_existing_item_absent_from_context_is_preserved():
    decision = decide_reconciliation(
        "900001",
        100,
        "Milk",
        make_indexes(),
    )

    assert decision.status == STATUS_NOT_IN_CONTEXT
    assert decision.apply_mapping is False
