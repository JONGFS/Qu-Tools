"""Generate safe simulator configuration."""
from pathlib import Path
from .models import PathResolution

SAFE_STATUSES = {"UNCHANGED", "UPDATED"}

def build_simulator_config(results: list[PathResolution], menu_snapshot_id: str, context: dict) -> dict:
    """
    TODO:
    - include only safe unambiguous matches
    - use current itemPathKey
    - include itemMasterId, PLU, title, snapshot and context
    """
    raise NotImplementedError

def write_simulator_config(config: dict, output_path: Path) -> None:
    """TODO: Write formatted JSON without overwriting original config."""
    raise NotImplementedError
