from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager

from kiarina.currency.currency_code import CurrencyCode


class StaticRateProviderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIARINA_CURRENCY_RATE_PROVIDER_IMPL_STATIC_",
    )

    base_currency: CurrencyCode = "USD"

    rates: dict[CurrencyCode, dict[CurrencyCode, float]] = Field(
        default_factory=lambda: {
            # Exchange rates as of 2026-01-16 04:52 UTC (source: x-rates.com)
            # Format: 1 USD = X currency
            "USD": {
                "JPY": 158.2683,  # Japanese Yen
                "EUR": 0.861128,  # Euro
                "GBP": 0.746835,  # British Pound
                "CNY": 6.966439,  # Chinese Yuan
                "KRW": 1473.6515,  # South Korean Won
                "AUD": 1.491355,  # Australian Dollar
                "CAD": 1.388642,  # Canadian Dollar
                "CHF": 0.802271,  # Swiss Franc
                "HKD": 7.798380,  # Hong Kong Dollar
                "SGD": 1.287205,  # Singapore Dollar
                "INR": 90.439582,  # Indian Rupee
            },
        },
    )
    """
    Exchange rates in nested dictionary format.

    Example:
        {
            "USD": {"JPY": 150.0, "EUR": 0.85},
            "EUR": {"GBP": 0.86}
        }
    """


settings_manager = SettingsManager(StaticRateProviderSettings)
