import argparse
from pathlib import Path
from collections.abc import Sequence

from .cache_manager import CacheManager
from .qu_client import QuClient
from .settings import Settings, load_settings


def build_context_key(settings: Settings) -> str:
    return (
        f"{settings.location_id}-"
        f"{settings.order_channel_id}-"
        f"{settings.order_type_id}"
    )


def refresh_menu(
    settings: Settings | None = None,
    client: QuClient | None = None,
    cache: CacheManager | None = None,
) -> dict:
    settings = settings or load_settings()
    client = client or QuClient(settings)
    cache = cache or CacheManager(Path("cache"))
    context_key = build_context_key(settings)
    metadata = cache.load_metadata(context_key)
    previous_generation_time = metadata.get("generation_time")

    client.authenticate()

    response = client.fetch_menu(
        previous_generation_time=previous_generation_time,
    )

    if response.status_code in {204, 304} or not response.content:
        if not previous_generation_time:
            raise RuntimeError(
                "QU returned no menu on the initial request."
            )

        cache.record_check(context_key, response.status_code)
        print("The cached menu is already current.")
        print(f"Cache: {cache.menu_path(context_key)}")
        return cache.load_menu(context_key)

    try:
        menu = response.json()
    except ValueError as error:
        raise RuntimeError(
            "QU returned an invalid menu JSON response."
        ) from error
    if not isinstance(menu, dict):
        raise RuntimeError("QU menu response must be a JSON object.")

    context = menu.get("context") or {}
    returned_location = context.get("locationId")
    if (
        returned_location is not None
        and int(returned_location) != settings.location_id
    ):
        raise RuntimeError(
            "QU returned a menu for a different location: "
            f"expected {settings.location_id}, got {returned_location}."
        )
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

    print(f"Saved menu generation: {generation_time}")
    print(f"Cache: {cache.menu_path(context_key)}")
    return menu


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh one QU menu context into the local cache."
    )
    parser.add_argument("--location-id", type=int)
    parser.add_argument("--order-channel-id", type=int)
    parser.add_argument("--order-type-id", type=int)
    parser.add_argument(
        "--cache-directory",
        type=Path,
        default=Path("cache"),
    )
    parser.add_argument("--env-file", type=Path)
    args = parser.parse_args(argv)

    settings = load_settings(
        location_id=args.location_id,
        order_channel_id=args.order_channel_id,
        order_type_id=args.order_type_id,
        env_file=args.env_file,
    )
    menu = refresh_menu(
        settings=settings,
        cache=CacheManager(args.cache_directory),
    )
    print(f"Snapshot ID: {menu.get('menuSnapshotId')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
