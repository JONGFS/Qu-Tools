from openpyxl import Workbook

from scripts.print_plu_mismatches import (
    PluMismatchRecord,
    find_likely_descendants,
    load_plu_mismatch_records,
)
from src.models import MenuNode


def make_node(
    *,
    item_id: int,
    title: str,
    plu: str,
    path: str,
    ancestors: tuple[str, ...],
) -> MenuNode:
    return MenuNode(
        item_master_id=item_id,
        title=title,
        plu=plu,
        item_path_key=path,
        parent_path_key=None,
        item_type=1,
        deleted=False,
        ancestors=ancestors,
    )


def test_loads_only_reconciliation_plu_mismatches(tmp_path):
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
            "Qu Item ID",
            "Qu Item Name",
            "Reconciliation Status",
            "Reconciliation Notes",
        ]
    )
    sheet.append(
        [
            950285,
            "Triple Korean BBQ Burger",
            189830,
            "Triple Korean ShackBurger Combo",
            "PLU_MISMATCH_REVIEW",
            "Expected 950285; current 2002.",
        ]
    )
    sheet.append(
        [
            900001,
            "Milk",
            100,
            "Milk",
            "MATCH",
            "Exact match.",
        ]
    )
    workbook.save(workbook_path)
    workbook.close()

    records = load_plu_mismatch_records(workbook_path)

    assert records == [
        PluMismatchRecord(
            aloha_plu="950285",
            aloha_name="Triple Korean BBQ Burger",
            qu_item_id=189830,
            qu_item_name="Triple Korean ShackBurger Combo",
            notes="Expected 950285; current 2002.",
        )
    ]


def test_finds_name_similar_nested_entree_without_remapping():
    record = PluMismatchRecord(
        aloha_plu="950285",
        aloha_name="Triple Korean BBQ Burger",
        qu_item_id=189830,
        qu_item_name="Triple Korean ShackBurger Combo",
        notes="Mismatch.",
    )
    wrapper = make_node(
        item_id=189830,
        title="Triple Korean ShackBurger Combo",
        plu="2002",
        path="1-189830",
        ancestors=("Shake Shack", "Combos"),
    )
    entree = make_node(
        item_id=180507,
        title="Korean Shackburger - Triple",
        plu="950252",
        path="1-189830-10-180507",
        ancestors=(
            "Shake Shack",
            "Combos",
            "Triple Korean ShackBurger Combo",
            "Entree Choice",
        ),
    )
    unrelated = make_node(
        item_id=200,
        title="French Fries",
        plu="952001",
        path="1-189830-20-200",
        ancestors=("Shake Shack", "Combos"),
    )

    candidates = find_likely_descendants(
        record,
        [wrapper],
        [wrapper, entree, unrelated],
    )

    assert candidates == [entree]
