"""Unit tests for ISO 4217 currency metadata registry and fixed-precision conversions."""

import pytest
from app.core.currency import (
    ISO_4217_REGISTRY,
    get_currency_exponent,
    validate_currency_and_exponent,
    minor_to_decimal_str,
    decimal_str_to_minor,
)


def test_iso_4217_registry_exponents():
    """Verify standard exponents across zero-, two-, and three-decimal currencies."""
    assert get_currency_exponent("USD") == 2
    assert get_currency_exponent("EUR") == 2
    assert get_currency_exponent("GBP") == 2
    assert get_currency_exponent("JPY") == 0
    assert get_currency_exponent("KRW") == 0
    assert get_currency_exponent("KWD") == 3
    assert get_currency_exponent("BHD") == 3
    assert get_currency_exponent("OMR") == 3

    # Case-insensitivity
    assert get_currency_exponent("usd") == 2
    assert get_currency_exponent("jpy") == 0


def test_validate_currency_and_exponent():
    """Verify that validate_currency_and_exponent enforces official registry rules."""
    # Valid pairings
    assert validate_currency_and_exponent("USD", 2) == 2
    assert validate_currency_and_exponent("JPY", 0) == 0
    assert validate_currency_and_exponent("KWD", 3) == 3

    # Mismatched exponent rejected
    with pytest.raises(ValueError, match="Invalid currency exponent for USD"):
        validate_currency_and_exponent("USD", 0)

    with pytest.raises(ValueError, match="Invalid currency exponent for JPY"):
        validate_currency_and_exponent("JPY", 2)

    with pytest.raises(ValueError, match="Invalid currency exponent for KWD"):
        validate_currency_and_exponent("KWD", 2)

    # Unknown currency code rejected
    with pytest.raises(ValueError, match="Unrecognized or unsupported"):
        validate_currency_and_exponent("FAKE", 2)


def test_minor_to_decimal_str_zero_decimal():
    """Verify conversion of zero-decimal currencies (e.g. JPY)."""
    assert minor_to_decimal_str(1000, 0) == "1000"
    assert minor_to_decimal_str(0, 0) == "0"
    assert minor_to_decimal_str(50000, 0) == "50000"


def test_minor_to_decimal_str_two_decimal():
    """Verify conversion of standard two-decimal currencies (e.g. USD, EUR)."""
    assert minor_to_decimal_str(1050, 2) == "10.50"
    assert minor_to_decimal_str(1000, 2) == "10.00"
    assert minor_to_decimal_str(5, 2) == "0.05"
    assert minor_to_decimal_str(0, 2) == "0.00"
    assert minor_to_decimal_str(99, 2) == "0.99"


def test_minor_to_decimal_str_three_decimal():
    """Verify conversion of three-decimal currencies (e.g. KWD, BHD)."""
    assert minor_to_decimal_str(10500, 3) == "10.500"
    assert minor_to_decimal_str(10005, 3) == "10.005"
    assert minor_to_decimal_str(1, 3) == "0.001"
    assert minor_to_decimal_str(0, 3) == "0.000"


def test_minor_to_decimal_str_invalid_inputs():
    """Verify rejection of invalid amount or exponent values."""
    with pytest.raises(ValueError, match="cannot be negative"):
        minor_to_decimal_str(-100, 2)

    with pytest.raises(TypeError):
        minor_to_decimal_str("100", 2)  # type: ignore

    with pytest.raises(ValueError, match="Unsupported currency exponent"):
        minor_to_decimal_str(100, 5)


def test_decimal_str_to_minor():
    """Verify parsing decimal strings to exact integer minor units without floating-point math."""
    # Exponent 0
    assert decimal_str_to_minor("1000", 0) == 1000
    with pytest.raises(ValueError, match="Zero-decimal currency cannot contain decimal points"):
        decimal_str_to_minor("1000.50", 0)

    # Exponent 2
    assert decimal_str_to_minor("10.50", 2) == 1050
    assert decimal_str_to_minor("10", 2) == 1000
    assert decimal_str_to_minor("0.05", 2) == 5
    assert decimal_str_to_minor("10.5", 2) == 1050

    # Exceeding decimal places
    with pytest.raises(ValueError, match="Exceeds maximum decimal places"):
        decimal_str_to_minor("10.555", 2)

    # Exponent 3
    assert decimal_str_to_minor("10.500", 3) == 10500
    assert decimal_str_to_minor("10.001", 3) == 10001
    assert decimal_str_to_minor("10.5", 3) == 10500

    with pytest.raises(ValueError, match="Exceeds maximum decimal places"):
        decimal_str_to_minor("10.5555", 3)


def test_bidirectional_roundtrip_precision():
    """Verify that integer minor units survive a full string formatting and parse roundtrip."""
    test_cases = [
        (1000, 0),
        (54321, 0),
        (1050, 2),
        (1, 2),
        (99999999, 2),
        (10500, 3),
        (1, 3),
        (987654321, 3),
    ]
    for amount_minor, exponent in test_cases:
        str_val = minor_to_decimal_str(amount_minor, exponent)
        parsed_minor = decimal_str_to_minor(str_val, exponent)
        assert parsed_minor == amount_minor
