"""QU authentication and menu requests."""
import logging

import requests

from .settings import Settings

logger = logging.getLogger(__name__)

class QuClient:
    def __init__(
        self,
        settings: Settings,
        session: requests.Session | None = None,
    ) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        self.access_token: str | None = None
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Integration": settings.x_integration_id,
            }
        )
    
    def authenticate(self) -> str:
        """
        TODO:
        - POST to access-token endpoint
        - use credentials proven in Postman
        - raise_for_status()
        - return access_token
        """
        url = (
            f"{self.settings.base_url.rstrip('/')}"
            "/api/v4/authentication/oauth2/access-token"
        )
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
        }
                
        response = self.session.post(
            url,
            data=data,
            timeout=30,
        )
        response.raise_for_status()

        token = response.json().get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise RuntimeError(
                "QU authentication response contained no access token."
            )

        self.access_token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        logger.info("Authentication successful")
        return token
        

    def fetch_menu(self, previous_generation_time: str | None = None) -> requests.Response:
        """
        TODO:
        - build menu context params
        - add PrevGenerationTime only when available
        - add Authorization, X-Integration, Accept-Encoding
        - GET /api/v4/menus
        - return raw Response
        """
        if not self.access_token:
            raise RuntimeError(
                "Authenticate before requesting the menu."
            )
        
        url = f"{self.settings.base_url.rstrip('/')}/api/v4/menus"
        params = {
            "LocationId": self.settings.location_id,
            "OrderChannelId": self.settings.order_channel_id,
            "OrderTypeId": self.settings.order_type_id,
        }
        
        if previous_generation_time:
            params["PrevGenerationTime"] = previous_generation_time

        response = self.session.get(
            url,
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return response

        
