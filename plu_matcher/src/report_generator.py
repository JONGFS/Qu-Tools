"""Generate CSV validation output."""
from pathlib import Path
from .models import PathResolution

def write_csv_report(results: list[PathResolution], output_path: Path) -> None:
    """
    TODO columns:
    Aloha PLU, Aloha Name, QU Item ID, Expected QU Name,
    Current QU Name, Old Path, Current Path, Ancestors,
    Status, Reason
    """
    raise NotImplementedError
