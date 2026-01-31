from kiarina.currency.currency_code import CurrencyCode
from kiarina.currency.rate_provider import RateProvider, create_rate_provider

from .._types.rate_options import RateOptions


async def get_exchange_rate(
    from_currency: CurrencyCode,
    to_currency: CurrencyCode,
    *,
    default: float | None = None,
    rate_options: RateOptions | None = None,
) -> float:
    rate_options = rate_options or {}

    provider = rate_options.get("rate_provider")

    if not isinstance(provider, RateProvider):
        provider = create_rate_provider(provider)

    return await provider.get_rate(
        from_currency,
        to_currency,
        default=default,
    )
