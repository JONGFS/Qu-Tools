"""Match approved mappings to current menu nodes."""
from .models import ApprovedMapping, MenuNode, PathResolution

def match_mapping(mapping: ApprovedMapping, candidates: list[MenuNode]) -> PathResolution:
    """
    TODO:
    1. No candidates -> MISSING
    2. Confirm expected PLU
    3. One valid candidate -> safe match
    4. Multiple candidates -> narrow by name/ancestors
    5. Still multiple -> AMBIGUOUS
    6. Item ID found but PLU differs -> PLU_MISMATCH
    """
    raise NotImplementedError
