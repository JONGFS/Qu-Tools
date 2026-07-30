from openpyxl import load_workbook

from scripts.create_demo_data import (
    DEMO_CONTEXT_KEY,
    create_demo_data,
)
from src.cache_manager import CacheManager


def test_create_demo_data_builds_offline_workbook_and_cache(tmp_path):
    workbook_path, menu_path = create_demo_data(tmp_path)

    assert workbook_path.exists()
    assert menu_path.exists()
    menu = CacheManager(tmp_path / "cache").load_menu(
        DEMO_CONTEXT_KEY
    )
    assert menu["context"]["locationId"] == 99999

    workbook = load_workbook(workbook_path, data_only=True)
    sheet = workbook["Aloha > Qu Item Migration"]
    assert sheet["A9"].value == "900001"
    assert sheet["A11"].value == "900003"
    workbook.close()
