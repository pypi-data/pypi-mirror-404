from typing import TypedDict

from kiarina.currency.rate_provider import RateProvider, RateProviderName
from kiarina.utils.common import ImportPath


class RateOptions(TypedDict, total=False):
    rate_provider: RateProvider | RateProviderName | ImportPath | None
