# kiarina-currency

Currency utilities for the kiarina namespace with exchange rate support.

## Purpose

Provides currency code types and exchange rate retrieval with pluggable rate providers.

## Installation

```bash
pip install kiarina-currency
```

## Quick Start

### Basic Usage

```python
from kiarina.currency import get_exchange_rate, get_system_currency

# Get system currency
currency = get_system_currency()
print(f"System currency: {currency}")  # e.g., "JPY" on Japanese system

# Get exchange rate (uses static provider by default)
rate = await get_exchange_rate("USD", "JPY")
print(f"1 USD = {rate} JPY")

# With default value for unsupported currencies
rate = await get_exchange_rate("USD", "XXX", default=1.0)
```

### Using Different Rate Providers

```python
from kiarina.currency import get_exchange_rate

# Use Frankfurter API for real-time rates
rate = await get_exchange_rate(
    "USD", "EUR",
    rate_options={"rate_provider": "frankfurter"}
)
```

### Custom Rate Provider

```python
from kiarina.currency import BaseRateProvider, get_exchange_rate

class MyRateProvider(BaseRateProvider):
    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        *,
        default: float | None = None,
    ) -> float:
        # Your custom implementation
        return 1.5

# Use custom provider
rate = await get_exchange_rate(
    "USD", "EUR",
    rate_options={"rate_provider": MyRateProvider()}
)
```

## API Reference

### `get_system_currency()`

Get system currency code from locale settings.

```python
def get_system_currency() -> CurrencyCode
```

**Returns:** Currency code (ISO 4217) based on system locale. Falls back to "USD" if detection fails.

**Detection Strategy:**
1. Try to get currency from `locale.localeconv()["int_curr_symbol"]`
2. Map locale string to currency (e.g., `ja_JP` → `JPY`, `en_US` → `USD`)
3. Check environment variables (`LC_ALL`, `LC_MONETARY`, `LANG`)
4. Fallback to `"USD"`

**Examples:**
```python
from kiarina.currency import get_system_currency

# On Japanese system
currency = get_system_currency()  # Returns "JPY"

# On US system
currency = get_system_currency()  # Returns "USD"

# On unknown system
currency = get_system_currency()  # Returns "USD" (fallback)
```

### `get_exchange_rate()`

Get exchange rate between two currencies.

```python
async def get_exchange_rate(
    from_currency: CurrencyCode,
    to_currency: CurrencyCode,
    *,
    default: float | None = None,
    rate_options: RateOptions | None = None,
) -> float
```

**Parameters:**
- `from_currency`: Source currency code (ISO 4217)
- `to_currency`: Target currency code (ISO 4217)
- `default`: Default value if rate not found (raises `ExchangeRateNotFoundError` if None)
- `rate_options`: Options for rate provider selection

**Returns:** Exchange rate as float

**Raises:** `ExchangeRateNotFoundError` if rate not found and no default provided

### Rate Providers

#### Built-in Providers

- **`static`** (default): Configuration-based static rates
  - Supports direct rates, inverted rates, and indirect rates via base currency
  - Default rates from USD to 11 major currencies (JPY, EUR, GBP, CNY, KRW, AUD, CAD, CHF, HKD, SGD, INR)
  
- **`frankfurter`**: Real-time rates from [Frankfurter API](https://www.frankfurter.app/)
  - Free, open-source API for currency exchange rates
  - Updated daily from European Central Bank
  - Default value fallback for unsupported currencies or network errors

#### Creating Custom Providers

Implement the `BaseRateProvider` abstract class:

```python
from kiarina.currency import BaseRateProvider

class MyRateProvider(BaseRateProvider):
    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        *,
        default: float | None = None,
    ) -> float:
        # Your implementation
        pass
```

## Configuration

### Static Rate Provider

Configure static exchange rates:

```yaml
kiarina.currency.rate_provider_impl.static:
  base_currency: "USD"
  rates:
    USD:
      JPY: 158.27
      EUR: 0.86
      GBP: 0.75
    EUR:
      GBP: 0.86
```

**Rate Resolution:**
1. Direct rate: `rates[from_currency][to_currency]`
2. Inverted rate: `1.0 / rates[to_currency][from_currency]`
3. Indirect rate via base currency: `from → base → to`

### Frankfurter Rate Provider

Configure Frankfurter API settings:

```yaml
kiarina.currency.rate_provider_impl.frankfurter:
  base_url: "https://api.frankfurter.app"
  timeout: 10.0
```

### Rate Provider Selection

Set default rate provider:

```yaml
kiarina.currency.rate_provider:
  default: "static"  # or "frankfurter"
  providers:
    static: "kiarina.currency.rate_provider_impl.static:StaticRateProvider"
    frankfurter: "kiarina.currency.rate_provider_impl.frankfurter:FrankfurterRateProvider"
    custom: "myapp.providers:CustomRateProvider"
```

**Environment Variables:**
- `KIARINA_CURRENCY_RATE_PROVIDER_DEFAULT`: Default provider name
- `KIARINA_CURRENCY_RATE_PROVIDER_IMPL_STATIC_BASE_CURRENCY`: Base currency for static provider
- `KIARINA_CURRENCY_RATE_PROVIDER_IMPL_FRANKFURTER_BASE_URL`: Frankfurter API base URL
- `KIARINA_CURRENCY_RATE_PROVIDER_IMPL_FRANKFURTER_TIMEOUT`: Request timeout in seconds

## Testing

```bash
# Run tests
mise run package:test kiarina-currency

# Enable Frankfurter API tests (requires internet connection)
export KIARINA_CURRENCY_RATE_PROVIDER_IMPL_FRANKFURTER_TEST_ENABLED=1
mise run package:test kiarina-currency
```

## Dependencies

- `httpx>=0.28.1` - HTTP client for API calls
- `kiarina-utils-common>=1.11.0` - Common utilities
- `pydantic>=2.10.6` - Data validation
- `pydantic-settings>=2.7.1` - Settings management
- `pydantic-settings-manager>=2.3.0` - Settings manager

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Related Projects

- [kiarina-python](https://github.com/kiarina/kiarina-python) - Parent monorepo
- [Frankfurter API](https://www.frankfurter.app/) - Free currency exchange rate API
