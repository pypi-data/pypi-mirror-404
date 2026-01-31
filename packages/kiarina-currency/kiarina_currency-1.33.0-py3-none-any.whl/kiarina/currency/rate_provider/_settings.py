from kiarina.utils.common import ImportPath
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager

from ._types.rate_provider_name import RateProviderName


class RateProviderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIARINA_CURRENCY_RATE_PROVIDER_",
    )

    default: RateProviderName = "static"

    providers: dict[RateProviderName, ImportPath] = {
        "frankfurter": "kiarina.currency.rate_provider_impl.frankfurter:FrankfurterRateProvider",
        "static": "kiarina.currency.rate_provider_impl.static:StaticRateProvider",
    }


settings_manager = SettingsManager(RateProviderSettings)
