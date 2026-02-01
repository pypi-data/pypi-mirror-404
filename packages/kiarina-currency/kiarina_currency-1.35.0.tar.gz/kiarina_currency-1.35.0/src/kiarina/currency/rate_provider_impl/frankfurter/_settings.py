from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class FrankfurterRateProviderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIARINA_CURRENCY_RATE_PROVIDER_IMPL_FRANKFURTER_",
    )

    base_url: str = "https://api.frankfurter.app"
    """Base URL for Frankfurter API"""

    timeout: float = 10.0
    """Request timeout in seconds"""


settings_manager = SettingsManager(FrankfurterRateProviderSettings)
