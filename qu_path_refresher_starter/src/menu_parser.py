"""Flatten and index the nested menu."""
from collections.abc import Iterator
from typing import Any
from .models import MenuNode

def flatten_menu(node: dict[str, Any], ancestors: tuple[str, ...] = ()) -> Iterator[MenuNode]:

    display_attribute = node.get("displayAttribute") or {}
    item_id = node.get("itemMasterId")
    title = node.get("title")
    if item_id is not None: 
        yield MenuNode(
            item_master_id=item_id,
            title=title,
            plu=display_attribute.get("plu"),
            item_path_key=node.get("itemPathKey"),
            parent_path_key=node.get("parentPathKey"),
            item_type=node.get("itemType"),
            deleted=bool(node.get("deleted",False)),
            ancestors=ancestors,
        )
        child_ancestors = ancestors + (title or "",)
    else:
        child_ancestors = ancestors
        

    for child in node.get("children") or []:
        yield from flatten_menu(child, child_ancestors)


def index_by_item_id(nodes: Iterator[MenuNode]) -> dict[int, list[MenuNode]]:
    index: dict[int,list[MenuNode]] = {}

    for node in nodes:
        if node.item_master_id is None:
            continue
        index.setdefault(node.item_master_id,[]).append(node)

    return index


