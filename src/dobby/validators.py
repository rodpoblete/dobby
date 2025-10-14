"""Custom validators for Chilean-specific data formats."""

import re
from typing import Any


def validate_rut(rut: str) -> bool:
    """
    Validate Chilean RUT format and check digit.

    Supports two types of identifiers:
    - Regular RUT: Validates check digit using standard algorithm
    - IPE (Identificador Provisorio del Estudiante): RUTs starting with 100 or 200 million
      for foreign students without definitive Chilean ID

    Args:
        rut: RUT string in format "12345678-9" or "12345678-K"

    Returns:
        True if RUT is valid, False otherwise
    """
    if not rut or not isinstance(rut, str):
        return False

    # Remove dots and hyphens
    clean_rut = rut.replace(".", "").replace("-", "").upper().strip()

    # Check format: digits + optional K
    if not re.match(r"^\d{7,9}[0-9K]$", clean_rut):
        return False

    # Split RUT and check digit
    rut_digits = clean_rut[:-1]
    check_digit = clean_rut[-1]

    # Check if it's an IPE (Identificador Provisorio del Estudiante)
    # IPEs start with 100 or 200 million and don't follow standard RUT validation
    rut_number = int(rut_digits)
    if 100000000 <= rut_number < 200000000 or 200000000 <= rut_number < 300000000:
        # IPE: Accept without check digit validation
        return True

    # Regular RUT: Calculate expected check digit
    reversed_digits = map(int, reversed(rut_digits))
    factors = [2, 3, 4, 5, 6, 7]

    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    remainder = s % 11
    expected_digit = 11 - remainder

    if expected_digit == 11:
        expected_digit_str = "0"
    elif expected_digit == 10:
        expected_digit_str = "K"
    else:
        expected_digit_str = str(expected_digit)

    return check_digit == expected_digit_str


def format_rut(rut: str, dv: str) -> str:
    """
    Format RUT by combining number and check digit.

    Args:
        rut: RUT number as string
        dv: Check digit (digito verificador)

    Returns:
        Formatted RUT string
    """
    return f"{rut}-{dv}"


def validate_email(email: str) -> bool:
    """
    Basic email validation.

    Args:
        email: Email address string

    Returns:
        True if email format is valid
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: Any) -> bool:
    """
    Validate Chilean phone number.

    Args:
        phone: Phone number (can be int or string)

    Returns:
        True if phone format is valid
    """
    if phone is None or phone == 0:
        return True  # Allow empty phones

    phone_str = str(phone)

    # Chilean mobile phones: 9 digits starting with 9
    return bool(re.match(r"^9\d{8}$", phone_str))


def clean_address(address: str) -> str:
    """
    Clean address by removing city names and extra whitespace.

    Args:
        address: Raw address string

    Returns:
        Cleaned address string
    """
    if not address or not isinstance(address, str):
        return ""

    # Remove common city names
    patterns = [
        r"\bla serena\b",
        r"\blaserena\b",
        r"\bserena\b",
        r"\blaserna\b",
        r"\bla  serena\b",
        r"\bcoquimbo\b",
        r"\bvicuña\b",
    ]

    cleaned = address
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Remove commas
    cleaned = cleaned.replace(",", "")

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned
