"""Load and validate environment configuration."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    base_url: str
    client_id: str
    client_secret: str
    x_integration_id: str
    location_id: int
    order_channel_id: int
    order_type_id: int

def load_settings() -> Settings:
    """Load and validate QU configuration from the environment."""
    load_dotenv()

    # QU calls this value Qu_SID, but OAuth expects it in the
    # client_secret form field. Keep the old name as a temporary fallback.
    client_secret = (
        os.getenv("QU_CLIENT_SECRET")
        or os.getenv("QU_SESSION_ID")
    )
    required = {
        "QU_BASE_URL": os.getenv("QU_BASE_URL"),
        "QU_CLIENT_ID": os.getenv("QU_CLIENT_ID"),
        "QU_CLIENT_SECRET": client_secret,
        "QU_X_INTEGRATION": os.getenv("QU_X_INTEGRATION"),
        "QU_LOCATION_ID": os.getenv("QU_LOCATION_ID"),
        "QU_ORDER_CHANNEL_ID": os.getenv("QU_ORDER_CHANNEL_ID"),
        "QU_ORDER_TYPE_ID": os.getenv("QU_ORDER_TYPE_ID"),
    }

    missing = [
        name
        for name, value in required.items()
        if not value or not value.strip()
    ]

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )
    
    return Settings(
        base_url=required["QU_BASE_URL"].strip(),
        client_id=required["QU_CLIENT_ID"].strip(),
        client_secret=client_secret.strip(),
        x_integration_id=required["QU_X_INTEGRATION"].strip(),
        location_id=int(required["QU_LOCATION_ID"]),
        order_channel_id=int(required["QU_ORDER_CHANNEL_ID"]),
        order_type_id=int(required["QU_ORDER_TYPE_ID"]),
    )
