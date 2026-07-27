"""Workflow orchestration."""

def refresh_menu() -> dict:
    """
    TODO:
    1. load settings
    2. create context cache key
    3. load saved generation time
    4. authenticate
    5. fetch menu
    6. empty/204 -> load cached menu
    7. 200 -> save new menu and generation time
    8. return menu
    """
    raise NotImplementedError

def validate_and_generate() -> None:
    """
    TODO:
    1. obtain current/cached menu
    2. flatten and index it
    3. load workbook mappings
    4. match each mapping
    5. compare old/current paths
    6. write CSV report
    7. generate simulator JSON
    """
    raise NotImplementedError

if __name__ == "__main__":
    pass
