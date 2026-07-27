"""Compare old simulator paths with current QU paths."""
from .models import PathResolution

def classify_path_change(resolution: PathResolution) -> PathResolution:
    """
    TODO:
    - leave failed/ambiguous results unchanged
    - compare old_item_path_key with current_node.item_path_key
    - classify UNCHANGED or UPDATED
    """
    raise NotImplementedError
