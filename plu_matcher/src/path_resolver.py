"""Compare old simulator paths with current QU paths."""
from dataclasses import replace

from .models import PathResolution
from .models import ResolutionStatus

def classify_path_change(resolution: PathResolution) -> PathResolution:
    """Classify a safe identity match against its stored simulator path."""
    if (
        resolution.status is not ResolutionStatus.MATCHED
        or resolution.current_node is None
    ):
        return resolution

    old_path = resolution.mapping.old_item_path_key
    current_path = resolution.current_node.item_path_key

    if not old_path:
        return replace(
            resolution,
            status=ResolutionStatus.REVIEW,
            reason="No stored itemPathKey is available for comparison",
        )

    if old_path == current_path:
        return replace(
            resolution,
            status=ResolutionStatus.UNCHANGED,
            reason="Stored itemPathKey is still current",
        )

    return replace(
        resolution,
        status=ResolutionStatus.UPDATED,
        reason="Current QU itemPathKey differs from the stored path",
    )
