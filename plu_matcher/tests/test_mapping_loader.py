from openpyxl import Workbook
import pytest

from src.mapping_loader import load_mappings, normalize_plu
from src.models import ApprovedMapping


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" 900001 ", "900001"),
        (900001, "900001"),
        (900001.0, "900001"),
        (None, ""),
    ],
)
def test_normalize_plu_preserves_identifier(value, expected):
    assert normalize_plu(value) == expected


def test_load_mappings_reads_only_migrated_rows(tmp_path):
    workbook_path = tmp_path / "mappings.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Aloha > Qu Item Migration"

    for _ in range(7):
        sheet.append([])

    sheet.append(
        [
            "Number",
            "Long name",
            "Sales/retail category",
            "Short name",
            "Chit name",
            "Migrated to Qu?",
            "Qu Item ID",
            "Qu Item Name",
        ]
    )
    sheet.append(
        [
            900001,
            "Milk",
            "Cold Beverage",
            "Milk",
            "Milk",
            "Yes",
            194275,
            "Milk",
        ]
    )
    sheet.append(
        [
            900002,
            "Chocolate Milk",
            "Cold Beverage",
            "Choc Milk",
            "Choc Milk",
            None,
            None,
            None,
        ]
    )
    sheet.append(
        [
            900010,
            "Small Lemonade",
            "Cold Beverage",
            "SM Lemonade",
            "SM Lemonade",
            " yes ",
            163754,
            "Shack-made Lemonade",
        ]
    )
    sheet.append([])
    workbook.save(workbook_path)
    workbook.close()

    mappings = load_mappings(workbook_path)

    assert mappings == [
        ApprovedMapping(
            aloha_plu="900001",
            aloha_name="Milk",
            qu_item_id=194275,
            qu_name="Milk",
            old_item_path_key=None,
        ),
        ApprovedMapping(
            aloha_plu="900010",
            aloha_name="Small Lemonade",
            qu_item_id=163754,
            qu_name="Shack-made Lemonade",
            old_item_path_key=None,
        ),
    ]


def test_load_mappings_uses_safe_reconciliation_statuses(tmp_path):
    workbook_path = tmp_path / "reconciled.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Aloha > Qu Item Migration"

    for _ in range(7):
        sheet.append([])

    sheet.append(
        [
            "Number",
            "Long name",
            "Migrated to Qu?",
            "Qu Item ID",
            "Qu Item Name",
            "Reconciliation Status",
        ]
    )
    sheet.append(
        [
            900001,
            "Exact Match",
            "Yes",
            1001,
            "Exact Match",
            "MATCH",
        ]
    )
    sheet.append(
        [
            900002,
            "Combo Item",
            "Yes",
            1002,
            "Combo Item",
            "MATCH_MULTIPLE_PATHS",
        ]
    )
    sheet.append(
        [
            900003,
            "Ambiguous Item",
            "Yes",
            1003,
            "Ambiguous Item",
            "AMBIGUOUS_QU_ITEM",
        ]
    )
    sheet.append(
        [
            900004,
            "Missing Item",
            "No",
            None,
            None,
            "NOT_FOUND_IN_QU",
        ]
    )
    workbook.save(workbook_path)
    workbook.close()

    mappings = load_mappings(workbook_path)

    assert [mapping.aloha_plu for mapping in mappings] == [
        "900001",
        "900002",
    ]
