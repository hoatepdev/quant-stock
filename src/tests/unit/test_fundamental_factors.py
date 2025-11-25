"""Unit tests for fundamental factor calculations."""
import pytest

from src.core.factors.fundamental import FundamentalFactors


class TestFundamentalFactors:
    """Test fundamental factor calculations."""

    def test_calculate_pe_ratio(self) -> None:
        """Test P/E ratio calculation."""
        pe = FundamentalFactors.calculate_pe_ratio(price=100.0, eps_ttm=5.0)
        assert pe == 20.0

    def test_calculate_pe_ratio_zero_eps(self) -> None:
        """Test P/E ratio with zero EPS."""
        pe = FundamentalFactors.calculate_pe_ratio(price=100.0, eps_ttm=0.0)
        assert pe is None

    def test_calculate_pb_ratio(self) -> None:
        """Test P/B ratio calculation."""
        pb = FundamentalFactors.calculate_pb_ratio(
            price=50.0,
            book_value_per_share=25.0
        )
        assert pb == 2.0

    def test_calculate_roe(self) -> None:
        """Test ROE calculation."""
        roe = FundamentalFactors.calculate_roe(
            net_income=1000000.0,
            shareholders_equity=5000000.0
        )
        assert roe == 20.0

    def test_calculate_roe_zero_equity(self) -> None:
        """Test ROE with zero equity."""
        roe = FundamentalFactors.calculate_roe(
            net_income=1000000.0,
            shareholders_equity=0.0
        )
        assert roe is None

    def test_calculate_roa(self) -> None:
        """Test ROA calculation."""
        roa = FundamentalFactors.calculate_roa(
            net_income=1000000.0,
            total_assets=10000000.0
        )
        assert roa == 10.0

    def test_calculate_debt_to_equity(self) -> None:
        """Test Debt-to-Equity calculation."""
        de = FundamentalFactors.calculate_debt_to_equity(
            total_debt=2000000.0,
            total_equity=5000000.0
        )
        assert de == 0.4

    def test_calculate_current_ratio(self) -> None:
        """Test Current Ratio calculation."""
        cr = FundamentalFactors.calculate_current_ratio(
            current_assets=5000000.0,
            current_liabilities=2000000.0
        )
        assert cr == 2.5

    def test_calculate_gross_margin(self) -> None:
        """Test Gross Margin calculation."""
        gm = FundamentalFactors.calculate_gross_margin(
            gross_profit=3000000.0,
            revenue=10000000.0
        )
        assert gm == 30.0

    def test_calculate_revenue_growth(self) -> None:
        """Test Revenue Growth calculation."""
        growth = FundamentalFactors.calculate_revenue_growth(
            current_revenue=11000000.0,
            previous_revenue=10000000.0
        )
        assert growth == 10.0

    def test_calculate_revenue_growth_negative(self) -> None:
        """Test Revenue Growth with decline."""
        growth = FundamentalFactors.calculate_revenue_growth(
            current_revenue=9000000.0,
            previous_revenue=10000000.0
        )
        assert growth == -10.0
