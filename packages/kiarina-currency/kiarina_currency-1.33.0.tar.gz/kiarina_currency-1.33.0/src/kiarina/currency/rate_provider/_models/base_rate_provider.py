from abc import ABC, abstractmethod
from typing import Any

from kiarina.currency.currency_code import CurrencyCode

from .._types.rate_provider import RateProvider


class BaseRateProvider(RateProvider, ABC):
    def __init__(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    async def get_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        *,
        default: float | None = None,
    ) -> float: ...
