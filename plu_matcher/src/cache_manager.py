"""Local menu and metadata cache."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


class CacheManager:
    def __init__(self, cache_directory: Path) -> None:
        self.cache_directory = cache_directory

    def _context_directory(self, context_key: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", context_key):
            raise ValueError(
                f"Invalid cache context key: {context_key!r}"
            )

        return self.cache_directory / context_key

    def _menu_path(self, context_key: str) -> Path:
        return self._context_directory(context_key) / "menu.json"

    def _metadata_path(self, context_key: str) -> Path:
        return self._context_directory(context_key) / "metadata.json"

    def menu_path(self, context_key: str) -> Path:
        """Return the cached menu path for a context."""
        return self._menu_path(context_key)

    def metadata_path(self, context_key: str) -> Path:
        """Return the cache metadata path for a context."""
        return self._metadata_path(context_key)

    def _read_json(self, path: Path) -> dict:
        try:
            with path.open(encoding="utf-8") as source:
                value = json.load(source)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Cached JSON is invalid: {path}"
            ) from error

        if not isinstance(value, dict):
            raise RuntimeError(
                f"Cached JSON must contain an object: {path}"
            )

        return value

    def _write_json(
        self,
        path: Path,
        value: dict,
        *,
        readable: bool = False,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary file first so an interrupted program does
        # not leave a partially written menu.json.
        temporary_path = path.with_suffix(path.suffix + ".tmp")

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as destination:
            json.dump(
                value,
                destination,
                ensure_ascii=False,
                indent=2 if readable else None,
                separators=None if readable else (",", ":"),
            )
            destination.flush()
            os.fsync(destination.fileno())

        temporary_path.replace(path)

    def load_metadata(self, context_key: str) -> dict:
        metadata_path = self._metadata_path(context_key)
        menu_path = self._menu_path(context_key)

        # If either file is missing, treat this as the first request.
        if not metadata_path.exists() or not menu_path.exists():
            return {}

        return self._read_json(metadata_path)

    def load_menu(self, context_key: str) -> dict:
        menu_path = self._menu_path(context_key)

        if not menu_path.exists():
            raise FileNotFoundError(
                f"No cached menu exists for context {context_key!r}."
            )

        return self._read_json(menu_path)

    def save_menu(
        self,
        context_key: str,
        menu: dict,
        generation_time: str,
    ) -> None:
        if not generation_time or not generation_time.strip():
            raise ValueError(
                "Cannot cache a menu without X-Generation-Time."
            )

        current_time = datetime.now(timezone.utc).isoformat()
        metadata = {
            "generation_time": generation_time,
            "menu_snapshot_id": menu.get("menuSnapshotId"),
            "context": menu.get("context", {}),
            "menu_saved_at": current_time,
            "last_checked_at": current_time,
            "last_response_status": 200,
            "last_check_result": "menu_updated",
        }

        # Save the menu first. If the program stops before metadata is
        # saved, the next run makes another complete request, which is safe.
        self._write_json(
            self._menu_path(context_key),
            menu,
        )
        self._write_json(
            self._metadata_path(context_key),
            metadata,
            readable=True,
        )

    def record_check(
        self,
        context_key: str,
        status_code: int,
    ) -> None:
        """Record an unchanged-menu check without rewriting menu.json."""
        metadata = self.load_metadata(context_key)
        if not metadata:
            raise FileNotFoundError(
                f"No complete cache exists for context {context_key!r}."
            )

        metadata["last_checked_at"] = (
            datetime.now(timezone.utc).isoformat()
        )
        metadata["last_response_status"] = status_code
        metadata["last_check_result"] = "not_modified"
        if (
            "menu_saved_at" not in metadata
            and "saved_at" in metadata
        ):
            metadata["menu_saved_at"] = metadata.pop("saved_at")
        self._write_json(
            self._metadata_path(context_key),
            metadata,
            readable=True,
        )
