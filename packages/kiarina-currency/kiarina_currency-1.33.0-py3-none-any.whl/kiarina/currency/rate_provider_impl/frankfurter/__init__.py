from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._models.frankfurter_rate_provider import FrankfurterRateProvider
    from ._settings import FrankfurterRateProviderSettings, settings_manager

__all__ = [
    # ._models
    "FrankfurterRateProvider",
    # ._settings
    "FrankfurterRateProviderSettings",
    "settings_manager",
]


def __getattr__(name: str) -> object:
    if name not in __all__:  # pragma: no cover
        raise AttributeError(f"module {__name__} has no attribute {name}")

    module_map = {
        # ._models
        "FrankfurterRateProvider": "._models.frankfurter_rate_provider",
        # ._settings
        "FrankfurterRateProviderSettings": "._settings",
        "settings_manager": "._settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
