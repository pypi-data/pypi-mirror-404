from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._helpers.create_rate_provider import create_rate_provider
    from ._models.base_rate_provider import BaseRateProvider
    from ._settings import RateProviderSettings, settings_manager
    from ._types.rate_provider import RateProvider
    from ._types.rate_provider_name import RateProviderName

__all__ = [
    # ._helpers
    "create_rate_provider",
    # ._models
    "BaseRateProvider",
    # ._settings
    "RateProviderSettings",
    "settings_manager",
    # ._types
    "RateProvider",
    "RateProviderName",
]


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module {__name__} has no attribute {name}")

    module_map = {
        # ._helpers
        "create_rate_provider": "._helpers.create_rate_provider",
        # ._models
        "BaseRateProvider": "._models.base_rate_provider",
        # ._settings
        "RateProviderSettings": "._settings",
        "settings_manager": "._settings",
        # ._types
        "RateProvider": "._types.rate_provider",
        "RateProviderName": "._types.rate_provider_name",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
