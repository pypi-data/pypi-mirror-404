import locale

from kiarina.currency.currency_code import CurrencyCode


def get_system_currency() -> CurrencyCode:
    """
    Get system currency code from locale settings.

    Returns:
        Currency code (ISO 4217) based on system locale.
        Falls back to "USD" if detection fails.

    Examples:
        >>> get_system_currency()  # On Japanese system
        'JPY'
        >>> get_system_currency()  # On US system
        'USD'
    """
    try:
        # Try to get currency from locale
        conv = locale.localeconv()
        if "int_curr_symbol" in conv:
            currency = conv["int_curr_symbol"].strip()
            if currency and len(currency) == 3:
                return currency

        # Fallback: map locale to common currencies
        try:
            loc = locale.getlocale(locale.LC_MONETARY)
            loc_str = loc[0] if loc and loc[0] else ""
        except Exception:
            loc_str = ""

        if not loc_str:
            try:
                # Try to get from environment variables as fallback
                import os

                for var in ("LC_ALL", "LC_MONETARY", "LANG"):
                    if var in os.environ:
                        loc_str = os.environ[var].split(".")[0]
                        break
            except Exception:
                loc_str = ""

        if loc_str:
            # Common locale -> currency mappings
            currency_map = {
                "ja": "JPY",
                "en_US": "USD",
                "en_GB": "GBP",
                "en_AU": "AUD",
                "en_CA": "CAD",
                "en_NZ": "NZD",
                "de": "EUR",
                "fr": "EUR",
                "it": "EUR",
                "es": "EUR",
                "nl": "EUR",
                "pt": "EUR",
                "zh_CN": "CNY",
                "zh_TW": "TWD",
                "zh_HK": "HKD",
                "ko": "KRW",
                "ru": "RUB",
                "ar": "SAR",
                "hi": "INR",
                "th": "THB",
                "vi": "VND",
                "id": "IDR",
                "ms": "MYR",
                "tr": "TRY",
                "pl": "PLN",
                "sv": "SEK",
                "no": "NOK",
                "da": "DKK",
                "fi": "EUR",
                "cs": "CZK",
                "hu": "HUF",
                "ro": "RON",
                "el": "EUR",
                "he": "ILS",
                "pt_BR": "BRL",
                "es_MX": "MXN",
                "es_AR": "ARS",
                "es_CL": "CLP",
                "es_CO": "COP",
            }

            for prefix, currency in currency_map.items():
                if loc_str.startswith(prefix):
                    return currency

    except Exception:
        pass

    # Final fallback
    return "USD"
