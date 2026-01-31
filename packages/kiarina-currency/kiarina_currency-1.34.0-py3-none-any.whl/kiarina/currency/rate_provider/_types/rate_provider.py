from typing import Protocol, runtime_checkable

from kiarina.currency.currency_code import CurrencyCode


@runtime_checkable
class RateProvider(Protocol):
    async def get_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        *,
        default: float | None = None,
    ) -> float: ...
