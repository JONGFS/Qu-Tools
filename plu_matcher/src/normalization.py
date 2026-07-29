"""Shared normalization helpers."""


def normalize_plu(value: object) -> str:
    """Return a stable string representation for a PLU identifier."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()
