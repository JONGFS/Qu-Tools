from src.cache_manager import CacheManager


def test_save_and_load_menu_and_metadata(tmp_path):
    cache = CacheManager(tmp_path / "cache")
    menu = {
        "menuSnapshotId": "snapshot-1",
        "context": {"locationId": 11934},
        "children": [],
    }

    cache.save_menu("11934-4685-4723", menu, "generation-1")

    assert cache.load_menu("11934-4685-4723") == menu
    metadata = cache.load_metadata("11934-4685-4723")
    assert metadata["generation_time"] == "generation-1"
    assert metadata["menu_snapshot_id"] == "snapshot-1"
    assert metadata["last_response_status"] == 200
    assert metadata["last_check_result"] == "menu_updated"
    assert metadata["menu_saved_at"]
    assert metadata["last_checked_at"]


def test_record_check_updates_check_fields_without_rewriting_menu(
    tmp_path,
):
    cache = CacheManager(tmp_path / "cache")
    menu = {"menuSnapshotId": "snapshot-1", "children": []}
    cache.save_menu("context", menu, "generation-1")
    menu_modified_time = cache.menu_path("context").stat().st_mtime_ns

    cache.record_check("context", 204)

    metadata = cache.load_metadata("context")
    assert metadata["generation_time"] == "generation-1"
    assert metadata["last_response_status"] == 204
    assert metadata["last_check_result"] == "not_modified"
    assert cache.menu_path("context").stat().st_mtime_ns == (
        menu_modified_time
    )


def test_incomplete_cache_is_treated_as_first_request(tmp_path):
    cache = CacheManager(tmp_path / "cache")
    cache.metadata_path("context").parent.mkdir(parents=True)
    cache.metadata_path("context").write_text(
        '{"generation_time": "old"}',
        encoding="utf-8",
    )

    assert cache.load_metadata("context") == {}
