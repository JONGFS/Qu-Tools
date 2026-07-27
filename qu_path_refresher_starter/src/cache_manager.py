"""Local menu and metadata cache."""
from pathlib import Path

class CacheManager:
    def __init__(self, cache_directory: Path) -> None:
        self.cache_directory = cache_directory

    def load_metadata(self, context_key: str) -> dict:
        """TODO: Return {} when metadata does not exist."""
        raise NotImplementedError

    def load_menu(self, context_key: str) -> dict:
        """TODO: Load cached menu JSON or raise a clear error."""
        raise NotImplementedError

    def save_menu(self, context_key: str, menu: dict, generation_time: str) -> None:
        """
        TODO:
        Save:
        - menu JSON
        - X-Generation-Time
        - menuSnapshotId
        - context metadata
        """
        raise NotImplementedError
