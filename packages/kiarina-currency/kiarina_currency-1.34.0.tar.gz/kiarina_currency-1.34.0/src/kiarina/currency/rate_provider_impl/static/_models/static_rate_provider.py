from kiarina.currency.currency_code import CurrencyCode
from kiarina.currency.currency_error import ExchangeRateNotFoundError
from kiarina.currency.rate_provider import BaseRateProvider

from .._settings import settings_manager


class StaticRateProvider(BaseRateProvider):
    async def get_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        *,
        default: float | None = None,
    ) -> float:
        settings = settings_manager.get_settings()

        # Same currency
        if from_currency == to_currency:
            return 1.0

        # 1. Direct rate
        if from_currency in settings.rates:
            if to_currency in settings.rates[from_currency]:
                return settings.rates[from_currency][to_currency]

        # 2. Inverted rate
        if to_currency in settings.rates:
            if from_currency in settings.rates[to_currency]:
                return 1.0 / settings.rates[to_currency][from_currency]

        # 3. Indirect rate via base_currency
        base = settings.base_currency
        if base != from_currency and base != to_currency:
            # Try: from_currency -> base -> to_currency
            from_to_base = None
            base_to_to = None

            # Get from_currency -> base rate
            if (
                from_currency in settings.rates
                and base in settings.rates[from_currency]
            ):
                from_to_base = settings.rates[from_currency][base]
            elif base in settings.rates and from_currency in settings.rates[base]:
                from_to_base = 1.0 / settings.rates[base][from_currency]

            # Get base -> to_currency rate
            if base in settings.rates and to_currency in settings.rates[base]:
                base_to_to = settings.rates[base][to_currency]
            elif to_currency in settings.rates and base in settings.rates[to_currency]:
                base_to_to = 1.0 / settings.rates[to_currency][base]

            # Calculate indirect rate
            if from_to_base is not None and base_to_to is not None:
                return from_to_base * base_to_to

        # Rate not found
        if default is None:
            raise ExchangeRateNotFoundError(
                f"Exchange rate not found from {from_currency} to {to_currency}"
            )

        return default
