"""Load validated mappings from Excel."""
from pathlib import Path
from .models import ApprovedMapping

def load_mappings(workbook_path: Path) -> list[ApprovedMapping]:
    """
    TODO:
    - open workbook with openpyxl
    - identify header row and columns
    - preserve PLUs as strings
    - ignore blank rows
    - validate QU Item ID
    - preserve duplicate PLUs
    """
    raise NotImplementedError

def normalize_plu(value: object) -> str:
    """TODO: Avoid scientific notation and trailing .0."""
    raise NotImplementedError
