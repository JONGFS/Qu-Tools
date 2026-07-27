"""Load and validate environment configuration."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    base_url: str
    client_id: str
    client_secret: str
    integration_id: str
    location_id: int
    order_channel_id: int
    order_type_id: int
    context_time: str | None
    meal_period_id: int | None

def load_settings() -> Settings:
    """
    TODO:
    - load .env
    - read environment variables
    - convert numeric IDs
    - require ContextTime or MealPeriodId
    - return Settings
    """
    raise NotImplementedError
