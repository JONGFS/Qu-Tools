"""Shared data models."""
from dataclasses import dataclass, field
from enum import StrEnum

class ResolutionStatus(StrEnum):
    UNCHANGED = "UNCHANGED"
    UPDATED = "UPDATED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"
    PLU_MISMATCH = "PLU_MISMATCH"
    REVIEW = "REVIEW"

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
