"""ISO 4217 currency metadata registry and fixed-precision conversion utilities."""

from typing import Dict

# ISO 4217 standard currency exponents (minor unit decimals)
ISO_4217_REGISTRY: Dict[str, int] = {
    # Zero-decimal currencies (Exponent 0)
    "JPY": 0,
    "KRW": 0,
    "CLP": 0,
    "PYG": 0,
    "VND": 0,
    "UGX": 0,
    "RWF": 0,
    "BIF": 0,
    "DJF": 0,
    "GNF": 0,
    "KMF": 0,
    "XAF": 0,
    "XOF": 0,
    "XPF": 0,

    # Standard two-decimal currencies (Exponent 2)
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "CAD": 2,
    "AUD": 2,
    "CHF": 2,
    "INR": 2,
    "CNY": 2,
    "NZD": 2,
    "SGD": 2,
    "HKD": 2,
    "SEK": 2,
    "NOK": 2,
    "DKK": 2,
    "PLN": 2,
    "CZK": 2,
    "HUF": 2,
    "ILS": 2,
    "MXN": 2,
    "BRL": 2,
    "ZAR": 2,
    "THB": 2,
    "MYR": 2,
    "PHP": 2,
    "IDR": 2,
    "TRY": 2,
    "AED": 2,
    "SAR": 2,
    "QAR": 2,

    # Three-decimal currencies (Exponent 3)
    "BHD": 3,
    "KWD": 3,
    "OMR": 3,
    "JOD": 3,
    "TND": 3,
    "IQD": 3,
    "LYD": 3,
}


def get_currency_exponent(currency: str) -> int:
    """Retrieve the standard ISO 4217 minor unit exponent for a currency code."""
    code = currency.strip().upper()
    if code not in ISO_4217_REGISTRY:
        raise ValueError(f"Unrecognized or unsupported ISO 4217 currency code: {currency}")
    return ISO_4217_REGISTRY[code]


def validate_currency_and_exponent(currency: str, exponent: int) -> int:
    """
    Validates that the provided exponent strictly matches the official ISO 4217 registry.
    Never trusts client-supplied exponents.
    """
    expected = get_currency_exponent(currency)
    if exponent != expected:
        raise ValueError(
            f"Invalid currency exponent for {currency.upper()}: supplied {exponent}, expected {expected}"
        )
    return expected


def minor_to_decimal_str(amount_minor: int, exponent: int) -> str:
    """
    Converts integer minor units to gateway-ready decimal string
    strictly using integer arithmetic (zero floating-point math).

    Examples:
        minor_to_decimal_str(1000, 0) -> "1000"
        minor_to_decimal_str(1050, 2) -> "10.50"
        minor_to_decimal_str(10500, 3) -> "10.500"
    """
    if not isinstance(amount_minor, int):
        raise TypeError(f"amount_minor must be an integer, got {type(amount_minor).__name__}")
    if amount_minor < 0:
        raise ValueError("amount_minor cannot be negative")
    if exponent < 0 or exponent > 4:
        raise ValueError(f"Unsupported currency exponent: {exponent}")

    if exponent == 0:
        return str(amount_minor)

    factor = 10 ** exponent
    units, fraction = divmod(amount_minor, factor)
    return f"{units}.{fraction:0{exponent}d}"


def decimal_str_to_minor(val_str: str, exponent: int) -> int:
    """
    Parses a decimal string into exact integer minor units without float conversion.

    Examples:
        decimal_str_to_minor("1000", 0) -> 1000
        decimal_str_to_minor("10.50", 2) -> 1050
        decimal_str_to_minor("10.500", 3) -> 10500
    """
    if not isinstance(val_str, str):
        raise TypeError(f"val_str must be a string, got {type(val_str).__name__}")
    if exponent < 0 or exponent > 4:
        raise ValueError(f"Unsupported currency exponent: {exponent}")

    val_str = val_str.strip()
    if not val_str:
        raise ValueError("Empty currency string")

    if exponent == 0:
        if "." in val_str:
            raise ValueError(f"Zero-decimal currency cannot contain decimal points: {val_str}")
        return int(val_str)

    parts = val_str.split(".")
    if len(parts) == 1:
        units_str = parts[0]
        fraction_str = ""
    elif len(parts) == 2:
        units_str, fraction_str = parts[0], parts[1]
    else:
        raise ValueError(f"Invalid decimal string: {val_str}")

    units = int(units_str)
    if units < 0:
        raise ValueError("Currency value cannot be negative")

    if len(fraction_str) > exponent:
        raise ValueError(f"Exceeds maximum decimal places ({exponent}) for currency: {val_str}")

    fraction_str = fraction_str.ljust(exponent, "0")
    fraction = int(fraction_str) if fraction_str else 0

    return units * (10 ** exponent) + fraction
