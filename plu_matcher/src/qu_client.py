"""QU authentication and menu requests."""
import logging

import requests

from .settings import Settings

logger = logging.getLogger(__name__)


class QuAuthenticationError(RuntimeError):
    """Raised when QU authentication cannot return a usable token."""


class QuMenuRequestError(RuntimeError):
    """Raised when QU cannot return a usable menu response."""


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

    def _v4_url(self, endpoint: str) -> str:
        base_url = self.settings.base_url.rstrip("/")
        if base_url.casefold().endswith("/api/v4"):
            return f"{base_url}/{endpoint.lstrip('/')}"
        return f"{base_url}/api/v4/{endpoint.lstrip('/')}"
    
    def authenticate(self) -> str:
        """Authenticate with OAuth client credentials and retain the token."""
        url = self._v4_url(
            "authentication/oauth2/access-token"
        )
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
        }
                
        try:
            response = self.session.post(
                url,
                data=data,
                timeout=30,
            )
            response.raise_for_status()
        except requests.Timeout as error:
            raise QuAuthenticationError(
                "QU authentication timed out."
            ) from error
        except requests.HTTPError as error:
            status = (
                error.response.status_code
                if error.response is not None
                else "unknown"
            )
            raise QuAuthenticationError(
                f"QU authentication failed (HTTP {status}). "
                "Check QU_CLIENT_ID and QU_CLIENT_SECRET."
            ) from error
        except requests.RequestException as error:
            raise QuAuthenticationError(
                "Could not connect to the QU authentication service."
            ) from error

        try:
            payload = response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise QuAuthenticationError(
                "QU returned an invalid authentication response."
            ) from error

        token = payload.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise QuAuthenticationError(
                "QU authentication response contained no access token."
            )

        self.access_token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        logger.info("Authentication successful")
        return token
        

    def fetch_menu(self, previous_generation_time: str | None = None) -> requests.Response:
        """Request the selected effective menu, optionally conditionally."""
        if not self.access_token:
            raise RuntimeError(
                "Authenticate before requesting the menu."
            )
        
        url = self._v4_url("menus")
        params = {
            "LocationId": self.settings.location_id,
            "OrderChannelId": self.settings.order_channel_id,
            "OrderTypeId": self.settings.order_type_id,
        }
        
        if previous_generation_time:
            params["PrevGenerationTime"] = previous_generation_time

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=60,
            )
            response.raise_for_status()
            return response
        except requests.Timeout as error:
            raise QuMenuRequestError(
                "The QU menu request timed out."
            ) from error
        except requests.HTTPError as error:
            status = (
                error.response.status_code
                if error.response is not None
                else "unknown"
            )
            raise QuMenuRequestError(
                f"QU menu request failed (HTTP {status}) for "
                f"location {self.settings.location_id}, channel "
                f"{self.settings.order_channel_id}, and order type "
                f"{self.settings.order_type_id}."
            ) from error
        except requests.RequestException as error:
            raise QuMenuRequestError(
                "Could not connect to the QU menu service."
            ) from error

        
