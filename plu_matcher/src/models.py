"""Shared data models."""
from dataclasses import dataclass, field
from enum import StrEnum


class ResolutionStatus(StrEnum):
    MATCHED = "MATCHED"
    UNCHANGED = "UNCHANGED"
    UPDATED = "UPDATED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"
    PLU_MISMATCH = "PLU_MISMATCH"
    REVIEW = "REVIEW"


class ReconciliationStatus(StrEnum):
    MATCH = "MATCH"
    MATCH_MULTIPLE_PATHS = "MATCH_MULTIPLE_PATHS"
    AMBIGUOUS_QU_ITEM = "AMBIGUOUS_QU_ITEM"
    EXISTING_MAPPING_CONFLICT = "EXISTING_MAPPING_CONFLICT"
    PLU_MISMATCH_REVIEW = "PLU_MISMATCH_REVIEW"
    NOT_FOUND_IN_QU = "NOT_FOUND_IN_QU"
    NOT_FOUND_IN_CURRENT_CONTEXT = "NOT_FOUND_IN_CURRENT_CONTEXT"


SAFE_RECONCILIATION_STATUSES = frozenset(
    {
        ReconciliationStatus.MATCH,
        ReconciliationStatus.MATCH_MULTIPLE_PATHS,
    }
)


@dataclass
class MenuNode:
    item_master_id: int | None
    title: str
    plu: str | None
    item_path_key: str | None
    parent_path_key: str | None
    item_type: int | None
    deleted: bool
    ancestors: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class ApprovedMapping:
    aloha_plu: str
    aloha_name: str
    qu_item_id: int
    qu_name: str
    old_item_path_key: str | None = None


@dataclass
class PathResolution:
    mapping: ApprovedMapping
    status: ResolutionStatus
    current_node: MenuNode | None
    reason: str
