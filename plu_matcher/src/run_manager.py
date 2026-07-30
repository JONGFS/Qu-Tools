"""Create auditable run directories and provenance records."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping


_SAFE_DIRECTORY_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_run_directory(
    runs_root: Path,
    profile_name: str,
    *,
    created_at: datetime | None = None,
) -> tuple[Path, datetime]:
    """Create ``runs/<profile>/<UTC timestamp>`` without collisions."""
    if not _SAFE_DIRECTORY_NAME.fullmatch(profile_name):
        raise ValueError(f"Unsafe profile directory name: {profile_name!r}")

    timestamp = created_at or utc_now()
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    run_name = timestamp.strftime("%Y%m%dT%H%M%SZ")
    profile_directory = Path(runs_root) / profile_name

    candidate = profile_directory / run_name
    suffix = 1
    while candidate.exists():
        candidate = profile_directory / f"{run_name}-{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate, timestamp


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    resolved = Path(path).resolve()
    return {
        "path": str(resolved),
        "sizeBytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically write readable JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as destination:
        json.dump(
            value,
            destination,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        destination.write("\n")
        destination.flush()
        os.fsync(destination.fileno())
    temporary_path.replace(path)


def write_text(path: Path, value: str) -> None:
    """Atomically write a UTF-8 text artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as destination:
        destination.write(value)
        if value and not value.endswith("\n"):
            destination.write("\n")
        destination.flush()
        os.fsync(destination.fileno())
    temporary_path.replace(path)
