import httpx

from kiarina.currency.currency_code import CurrencyCode
from kiarina.currency.currency_error import ExchangeRateNotFoundError
from kiarina.currency.rate_provider import BaseRateProvider

from .._settings import settings_manager


class FrankfurterRateProvider(BaseRateProvider):
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

        # Call Frankfurter API
        url = f"{settings.base_url}/latest"
        params = {
            "from": from_currency,
            "to": to_currency,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Extract rate from response
                if "rates" in data and to_currency in data["rates"]:
                    return float(data["rates"][to_currency])

                # Rate not found in response
                if default is None:
                    raise ExchangeRateNotFoundError(
                        f"Exchange rate not found from {from_currency} to {to_currency}"
                    )
                return default

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 404 for unsupported currency)
            if default is None:
                raise ExchangeRateNotFoundError(
                    f"Exchange rate not found from {from_currency} to {to_currency}: {e}"
                ) from e
            return default

        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Handle network errors
            if default is None:
                raise ExchangeRateNotFoundError(
                    f"Failed to fetch exchange rate from {from_currency} to {to_currency}: {e}"
                ) from e
            return default
