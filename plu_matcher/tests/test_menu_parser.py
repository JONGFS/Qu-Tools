from src.menu_parser import flatten_menu, index_by_item_id
from src.models import MenuNode


def test_flatten_menu_includes_nested_children():
    menu = {
        "menuSnapshotId": "test-snapshot",
        "children": [
            {
                "itemMasterId": 100,
                "title": "Drinks",
                "itemPathKey": "100",
                "parentPathKey": None,
                "itemType": 10,
                "displayAttribute": None,
                "children": [
                    {
                        "itemMasterId": 200,
                        "title": "Diet Coke",
                        "itemPathKey": "100-200",
                        "parentPathKey": "100",
                        "itemType": 1,
                        "displayAttribute": {"plu": "902004"},
                        "children": [],
                    }
                ],
            }
        ],
    }

    nodes = list(flatten_menu(menu))

    assert [node.item_master_id for node in nodes] == [100, 200]
    assert nodes[0].title == "Drinks"
    assert nodes[0].plu is None
    assert nodes[0].ancestors == ()
    assert nodes[1].title == "Diet Coke"
    assert nodes[1].plu == "902004"
    assert nodes[1].ancestors == ("Drinks",)


def test_same_item_id_can_have_multiple_paths():
    first_path = MenuNode(
        item_master_id=200,
        title="Diet Coke",
        plu="902004",
        item_path_key="100-200",
        parent_path_key="100",
        item_type=1,
        deleted=False,
    )
    second_path = MenuNode(
        item_master_id=200,
        title="Diet Coke",
        plu="902004",
        item_path_key="300-200",
        parent_path_key="300",
        item_type=1,
        deleted=False,
    )
    missing_id = MenuNode(
        item_master_id=None,
        title="Menu envelope",
        plu=None,
        item_path_key=None,
        parent_path_key=None,
        item_type=None,
        deleted=False,
    )

    index = index_by_item_id(iter([first_path, second_path, missing_id]))

    assert index == {200: [first_path, second_path]}
