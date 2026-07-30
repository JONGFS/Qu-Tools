from src.models import (
    ApprovedMapping,
    MenuNode,
    PathResolution,
    ResolutionStatus,
)
from src.path_resolver import classify_path_change


def make_resolution(
    old_path: str | None,
    current_path: str,
    status: ResolutionStatus = ResolutionStatus.MATCHED,
) -> PathResolution:
    mapping = ApprovedMapping(
        aloha_plu="900001",
        aloha_name="Milk",
        qu_item_id=100,
        qu_name="Milk",
        old_item_path_key=old_path,
    )
    node = MenuNode(
        item_master_id=100,
        title="Milk",
        plu="900001",
        item_path_key=current_path,
        parent_path_key="1",
        item_type=1,
        deleted=False,
    )
    return PathResolution(
        mapping=mapping,
        status=status,
        current_node=node,
        reason="Identity matched",
    )


def test_same_path_is_unchanged():
    result = classify_path_change(
        make_resolution("1-100", "1-100")
    )

    assert result.status is ResolutionStatus.UNCHANGED

def test_changed_parent_hierarchy_is_updated():
    # Old: Fountain Drinks -> Small/Large -> Drink Choice -> Diet Coke
    # New: Small Fountain Drink -> Drink Choice -> Diet Coke
    result = classify_path_change(
        make_resolution(
            "1-10-20-100",
            "1-30-40-100",
        )
    )

    assert result.status is ResolutionStatus.UPDATED


def test_missing_stored_path_requires_review():
    result = classify_path_change(
        make_resolution(None, "1-100")
    )

    assert result.status is ResolutionStatus.REVIEW


def test_unsafe_identity_result_is_not_reclassified():
    resolution = make_resolution(
        "1-100",
        "1-200",
        status=ResolutionStatus.AMBIGUOUS,
    )

    assert classify_path_change(resolution) is resolution
