"""Workflow orchestration."""
from pathlib import Path

from .cache_manager import CacheManager
from .qu_client import QuClient
from .settings import load_settings

def refresh_menu() -> dict:
    settings = load_settings()
    client = QuClient(settings)
    cache = CacheManager(Path("chace"))
    context_key = (
        f"{settings.location_id}-"
        f"{settings.order_channel_id}-"
        f"{settings.order_type_id}"
    )

    metadata = cache.load_metadata(context_key)
    previous_generation_time = metadata.get("generation_time")

    client.authenticate()

    response = client.fetch_menu(
        previous_generation_time=previous_generation_time
    )

    # QU is saying that the cached generation is still current.
    if response.status_code in {204, 304} or not response.content:
        if not previous_generation_time:
            raise RuntimeError(
                "QU returned no menu on the first request."
            )

        return cache.load_menu(context_key)

    # A 200 response with content means this is a new menu generation.
    menu = response.json()

    generation_time = response.headers.get("X-Generation-Time")
    if not generation_time:
        raise RuntimeError(
            "QU returned a menu without X-Generation-Time."
        )

    cache.save_menu(
        context_key=context_key,
        menu=menu,
        generation_time=generation_time,
    )

    return menu


""" def validate_and_generate() -> None:
    TODO:
    1. obtain current/cached menu
    2. flatten and index it
    3. load workbook mappings
    4. match each mapping
    5. compare old/current paths
    6. write CSV report
    7. generate simulator JSON

    raise NotImplementedError """

if __name__ == "__main__":
    refresh_menu()
