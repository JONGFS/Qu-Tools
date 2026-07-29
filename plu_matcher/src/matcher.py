"""Match approved mappings to current menu nodes."""
from .models import ApprovedMapping, MenuNode, PathResolution, ResolutionStatus
from .normalization import normalize_plu

COMBO_KEYWORDS = {"combo"}


def normalize_text(value: object) -> str:
    return str(value or "").strip().casefold()


def is_combo_path(node: MenuNode) -> bool:
    return any(
        keyword in normalize_text(ancestor)
        for ancestor in node.ancestors
        for keyword in COMBO_KEYWORDS
    )


def format_path(node: MenuNode) -> str:
    return " > ".join((*node.ancestors, node.title))


def match_mapping(
    mapping: ApprovedMapping,
    candidates: list[MenuNode],
) -> PathResolution:
    active_candidates = [
        node for node in candidates
        if not node.deleted
    ]

    if not active_candidates:
        return PathResolution(
            mapping=mapping,
            status=ResolutionStatus.MISSING,
            current_node=None,
            reason="No active menu node found for the QU item ID",
        )

    expected_plu = normalize_plu(mapping.aloha_plu)

    plu_matches = [
        node
        for node in active_candidates
        if normalize_plu(node.plu) == expected_plu
    ]

    if not plu_matches:
        return PathResolution(
            mapping=mapping,
            status=ResolutionStatus.PLU_MISMATCH,
            current_node=None,
            reason="QU item ID exists, but the expected PLU was not found",
        )

    if len(plu_matches) == 1:
        return PathResolution(
            mapping=mapping,
            status=ResolutionStatus.MATCHED,
            current_node=plu_matches[0],
            reason="Matched uniquely by QU item ID and PLU",
        )

    expected_name = normalize_text(mapping.qu_name)

    name_matches = [
        node
        for node in plu_matches
        if normalize_text(node.title) == expected_name
    ]

    if len(name_matches) == 1:
        return PathResolution(
            mapping=mapping,
            status=ResolutionStatus.MATCHED,
            current_node=name_matches[0],
            reason="Matched uniquely by QU item ID, PLU, and name",
        )

    remaining_matches = name_matches or plu_matches

    combo_matches = [
        node for node in remaining_matches
        if is_combo_path(node)
    ]
    regular_matches = [
        node for node in remaining_matches
        if not is_combo_path(node)
    ]

    paths = "; ".join(format_path(node) for node in remaining_matches)

    if combo_matches and regular_matches:
        reason = (
            f"PLU appears in both regular and combo paths: "
            f"{len(regular_matches)} regular and "
            f"{len(combo_matches)} combo. Candidates: {paths}"
        )
    elif combo_matches:
        reason = (
            f"Multiple combo paths match this item. Candidates: {paths}"
        )
    else:
        reason = (
            f"Multiple regular paths match this item. Candidates: {paths}"
        )

    return PathResolution(
        mapping=mapping,
        status=ResolutionStatus.AMBIGUOUS,
        current_node=None,
        reason=reason,
    )
