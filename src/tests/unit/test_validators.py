"""Unit tests for validators."""
from datetime import date
from decimal import Decimal

import pytest

from src.utils.validators import (
    ValidationError,
    validate_date_range,
    validate_exchange,
    validate_ohlc_data,
    validate_ticker,
)


class TestValidators:
    """Test validation functions."""

    def test_validate_ticker_valid(self) -> None:
        """Test valid ticker validation."""
        assert validate_ticker("VNM") is True
        assert validate_ticker("HPG") is True
        assert validate_ticker("VIC") is True

    def test_validate_ticker_empty(self) -> None:
        """Test empty ticker validation."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_ticker("")

    def test_validate_ticker_invalid_chars(self) -> None:
        """Test ticker with invalid characters."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_ticker("VN-M")

    def test_validate_ticker_too_long(self) -> None:
        """Test ticker that is too long."""
        with pytest.raises(ValidationError, match="too long"):
            validate_ticker("VERYLONGTICKER")

    def test_validate_ohlc_valid(self) -> None:
        """Test valid OHLC data."""
        assert validate_ohlc_data(
            open_price=Decimal("100"),
            high=Decimal("105"),
            low=Decimal("98"),
            close=Decimal("103"),
            volume=1000000
        ) is True

    def test_validate_ohlc_high_less_than_low(self) -> None:
        """Test OHLC with high less than low."""
        with pytest.raises(ValidationError, match="High.*cannot be less than low"):
            validate_ohlc_data(
                open_price=Decimal("100"),
                high=Decimal("95"),
                low=Decimal("98"),
                close=Decimal("96"),
                volume=1000000
            )

    def test_validate_ohlc_negative_volume(self) -> None:
        """Test OHLC with negative volume."""
        with pytest.raises(ValidationError, match="Volume.*cannot be negative"):
            validate_ohlc_data(
                open_price=Decimal("100"),
                high=Decimal("105"),
                low=Decimal("98"),
                close=Decimal("103"),
                volume=-1000
            )

    def test_validate_date_range_valid(self) -> None:
        """Test valid date range."""
        assert validate_date_range(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        ) is True

    def test_validate_date_range_start_after_end(self) -> None:
        """Test date range with start after end."""
        with pytest.raises(ValidationError, match="Start date.*cannot be after end date"):
            validate_date_range(
                start_date=date(2023, 12, 31),
                end_date=date(2023, 1, 1)
            )

    def test_validate_date_range_too_large(self) -> None:
        """Test date range that is too large."""
        with pytest.raises(ValidationError, match="Date range is too large"):
            validate_date_range(
                start_date=date(2000, 1, 1),
                end_date=date(2024, 1, 1),
                max_years=20
            )

    def test_validate_exchange_valid(self) -> None:
        """Test valid exchange validation."""
        assert validate_exchange("HOSE") is True
        assert validate_exchange("HNX") is True
        assert validate_exchange("UPCOM") is True

    def test_validate_exchange_invalid(self) -> None:
        """Test invalid exchange validation."""
        with pytest.raises(ValidationError, match="Invalid exchange"):
            validate_exchange("INVALID")
