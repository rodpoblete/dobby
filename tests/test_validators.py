"""Tests for validators module."""

import pytest

from dobby.validators import (
    clean_address,
    format_rut,
    validate_email,
    validate_phone,
    validate_rut,
)


class TestRutValidation:
    """Tests for RUT validation."""

    def test_valid_rut_with_hyphen(self):
        """Test valid RUT with hyphen."""
        assert validate_rut("12345678-5") is True

    def test_valid_rut_with_k(self):
        """Test valid RUT with K check digit."""
        # Real RUT from data with K
        assert validate_rut("23762615-K") is True

    def test_invalid_rut_wrong_check_digit(self):
        """Test invalid RUT with wrong check digit."""
        assert validate_rut("12345678-9") is False

    def test_invalid_rut_format(self):
        """Test invalid RUT format."""
        assert validate_rut("invalid") is False
        assert validate_rut("") is False
        assert validate_rut(None) is False

    def test_rut_format(self):
        """Test RUT formatting."""
        assert format_rut("12345678", "5") == "12345678-5"
        assert format_rut("11111111", "K") == "11111111-K"

    def test_valid_ipe_100_million(self):
        """Test valid IPE starting with 100 million."""
        assert validate_rut("100123456-0") is True
        assert validate_rut("100123456-5") is True
        assert validate_rut("199999999-K") is True

    def test_valid_ipe_200_million(self):
        """Test valid IPE starting with 200 million."""
        assert validate_rut("200123456-0") is True
        assert validate_rut("200123456-7") is True
        assert validate_rut("299999999-3") is True

    def test_ipe_accepts_any_check_digit(self):
        """Test that IPE accepts any check digit without validation."""
        # IPE doesn't validate check digit, so all should be valid
        assert validate_rut("100000000-0") is True
        assert validate_rut("100000000-9") is True
        assert validate_rut("100000000-K") is True


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@domain.co.uk") is True

    def test_invalid_email(self):
        """Test invalid email addresses."""
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("") is False
        assert validate_email(None) is False


class TestPhoneValidation:
    """Tests for phone validation."""

    def test_valid_phone(self):
        """Test valid phone numbers."""
        assert validate_phone(987654321) is True
        assert validate_phone("987654321") is True
        assert validate_phone(0) is True
        assert validate_phone(None) is True

    def test_invalid_phone(self):
        """Test invalid phone numbers."""
        assert validate_phone(123456789) is False
        assert validate_phone("87654321") is False


class TestAddressCleaning:
    """Tests for address cleaning."""

    def test_clean_address_removes_city_names(self):
        """Test that city names are removed."""
        address = "Calle Principal 123, La Serena"
        cleaned = clean_address(address)
        assert "la serena" not in cleaned.lower()
        assert "Calle Principal 123" in cleaned

    def test_clean_address_removes_commas(self):
        """Test that commas are removed."""
        address = "Calle Principal, 123"
        cleaned = clean_address(address)
        assert "," not in cleaned

    def test_clean_address_handles_empty(self):
        """Test handling of empty addresses."""
        assert clean_address("") == ""
        assert clean_address(None) == ""

    def test_clean_address_normalizes_whitespace(self):
        """Test whitespace normalization."""
        address = "Calle   Principal    123"
        cleaned = clean_address(address)
        assert "  " not in cleaned
