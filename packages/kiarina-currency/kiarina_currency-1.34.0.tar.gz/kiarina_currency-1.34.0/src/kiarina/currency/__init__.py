import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .currency_code import CurrencyCode
    from .currency_error import CurrencyError, ExchangeRateNotFoundError
    from .rate import RateOptions, get_exchange_rate
    from .rate_provider import (
        RateProvider,
        RateProviderName,
        RateProviderSettings,
        create_rate_provider,
        settings_manager as rate_provider_settings_manager,
    )
    from .system_currency import get_system_currency

__version__ = version("kiarina-currency")

__all__ = [
    # .currency_code
    "CurrencyCode",
    # .currency_error
    "CurrencyError",
    "ExchangeRateNotFoundError",
    # .rate
    "RateOptions",
    "get_exchange_rate",
    # .rate_provider
    "RateProvider",
    "RateProviderName",
    "RateProviderSettings",
    "create_rate_provider",
    "rate_provider_settings_manager",
    # .system_currency
    "get_system_currency",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # .currency_code
        "CurrencyCode": ".currency_code",
        # .currency_error
        "CurrencyError": ".currency_error",
        "ExchangeRateNotFoundError": ".currency_error",
        # .rate
        "RateOptions": ".rate",
        "get_exchange_rate": ".rate",
        # .rate_provider
        "RateProvider": ".rate_provider",
        "RateProviderName": ".rate_provider",
        "RateProviderSettings": ".rate_provider",
        "create_rate_provider": ".rate_provider",
        "rate_provider_settings_manager": ".rate_provider",
        # .system_currency
        "get_system_currency": ".system_currency",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
