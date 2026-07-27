"""QU authentication and menu requests."""
import requests
from .settings import Settings

class QuClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_access_token(self) -> str:
        """
        TODO:
        - POST to access-token endpoint
        - use credentials proven in Postman
        - raise_for_status()
        - return access_token
        """
        raise NotImplementedError

    def fetch_menu(self, access_token: str, previous_generation_time: str | None = None) -> requests.Response:
        """
        TODO:
        - build menu context params
        - add PrevGenerationTime only when available
        - add Authorization, X-Integration, Accept-Encoding
        - GET /api/v4/menus
        - return raw Response
        """
        raise NotImplementedError
