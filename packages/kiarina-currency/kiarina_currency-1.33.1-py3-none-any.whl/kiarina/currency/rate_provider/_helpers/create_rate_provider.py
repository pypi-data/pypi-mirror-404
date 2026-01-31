from typing import Any

from kiarina.utils.common import ImportPath, import_object

from .._settings import settings_manager
from .._types.rate_provider import RateProvider
from .._types.rate_provider_name import RateProviderName


def create_rate_provider(
    provider_name: RateProviderName | ImportPath | None = None,
    **kwargs: Any,
) -> RateProvider:
    settings = settings_manager.get_settings()

    if provider_name is None:
        provider_name = settings.default

    if provider_name in settings.providers:
        import_path = settings.providers[provider_name]
    else:
        import_path = provider_name

    if ":" not in import_path:
        import_path = f"{import_path}:RateProvider"

    provider = import_object(import_path)(**kwargs)

    if not isinstance(provider, RateProvider):
        raise TypeError(
            f"Imported rate provider '{import_path}' is not a valid RateProvider",
        )

    return provider
