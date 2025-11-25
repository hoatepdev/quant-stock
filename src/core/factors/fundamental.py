"""Fundamental factor calculations."""
from decimal import Decimal
from typing import Optional

import pandas as pd

from src.utils.helpers import safe_divide
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FundamentalFactors:
    """Calculate fundamental investment factors."""

    @staticmethod
    def calculate_pe_ratio(price: float, eps_ttm: float) -> Optional[float]:
        """Calculate Price-to-Earnings ratio.

        Args:
            price: Current stock price
            eps_ttm: Trailing twelve months earnings per share

        Returns:
            P/E ratio or None if cannot calculate
        """
        if eps_ttm and eps_ttm != 0:
            return safe_divide(price, eps_ttm, None)
        return None

    @staticmethod
    def calculate_pb_ratio(
        price: float,
        book_value_per_share: float,
    ) -> Optional[float]:
        """Calculate Price-to-Book ratio.

        Args:
            price: Current stock price
            book_value_per_share: Book value per share

        Returns:
            P/B ratio or None
        """
        return safe_divide(price, book_value_per_share, None)

    @staticmethod
    def calculate_ps_ratio(
        price: float,
        revenue_per_share: float,
    ) -> Optional[float]:
        """Calculate Price-to-Sales ratio.

        Args:
            price: Current stock price
            revenue_per_share: Revenue per share (TTM)

        Returns:
            P/S ratio or None
        """
        return safe_divide(price, revenue_per_share, None)

    @staticmethod
    def calculate_roe(net_income: float, shareholders_equity: float) -> Optional[float]:
        """Calculate Return on Equity.

        Args:
            net_income: Net income (TTM)
            shareholders_equity: Average shareholders' equity

        Returns:
            ROE as percentage or None
        """
        roe = safe_divide(net_income, shareholders_equity, None)
        return roe * 100 if roe is not None else None

    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> Optional[float]:
        """Calculate Return on Assets.

        Args:
            net_income: Net income (TTM)
            total_assets: Average total assets

        Returns:
            ROA as percentage or None
        """
        roa = safe_divide(net_income, total_assets, None)
        return roa * 100 if roa is not None else None

    @staticmethod
    def calculate_roi(
        net_income: float,
        total_assets: float,
        current_liabilities: float,
    ) -> Optional[float]:
        """Calculate Return on Investment.

        Args:
            net_income: Net income (TTM)
            total_assets: Total assets
            current_liabilities: Current liabilities

        Returns:
            ROI as percentage or None
        """
        invested_capital = total_assets - current_liabilities
        roi = safe_divide(net_income, invested_capital, None)
        return roi * 100 if roi is not None else None

    @staticmethod
    def calculate_gross_margin(
        gross_profit: float,
        revenue: float,
    ) -> Optional[float]:
        """Calculate Gross Profit Margin.

        Args:
            gross_profit: Gross profit
            revenue: Total revenue

        Returns:
            Gross margin as percentage or None
        """
        margin = safe_divide(gross_profit, revenue, None)
        return margin * 100 if margin is not None else None

    @staticmethod
    def calculate_operating_margin(
        operating_profit: float,
        revenue: float,
    ) -> Optional[float]:
        """Calculate Operating Profit Margin.

        Args:
            operating_profit: Operating profit
            revenue: Total revenue

        Returns:
            Operating margin as percentage or None
        """
        margin = safe_divide(operating_profit, revenue, None)
        return margin * 100 if margin is not None else None

    @staticmethod
    def calculate_net_margin(net_income: float, revenue: float) -> Optional[float]:
        """Calculate Net Profit Margin.

        Args:
            net_income: Net income
            revenue: Total revenue

        Returns:
            Net margin as percentage or None
        """
        margin = safe_divide(net_income, revenue, None)
        return margin * 100 if margin is not None else None

    @staticmethod
    def calculate_debt_to_equity(
        total_debt: float,
        total_equity: float,
    ) -> Optional[float]:
        """Calculate Debt-to-Equity ratio.

        Args:
            total_debt: Total debt
            total_equity: Total equity

        Returns:
            Debt-to-Equity ratio or None
        """
        return safe_divide(total_debt, total_equity, None)

    @staticmethod
    def calculate_debt_to_assets(
        total_debt: float,
        total_assets: float,
    ) -> Optional[float]:
        """Calculate Debt-to-Assets ratio.

        Args:
            total_debt: Total debt
            total_assets: Total assets

        Returns:
            Debt-to-Assets ratio or None
        """
        return safe_divide(total_debt, total_assets, None)

    @staticmethod
    def calculate_current_ratio(
        current_assets: float,
        current_liabilities: float,
    ) -> Optional[float]:
        """Calculate Current Ratio.

        Args:
            current_assets: Current assets
            current_liabilities: Current liabilities

        Returns:
            Current ratio or None
        """
        return safe_divide(current_assets, current_liabilities, None)

    @staticmethod
    def calculate_quick_ratio(
        current_assets: float,
        inventory: float,
        current_liabilities: float,
    ) -> Optional[float]:
        """Calculate Quick Ratio (Acid Test).

        Args:
            current_assets: Current assets
            inventory: Inventory
            current_liabilities: Current liabilities

        Returns:
            Quick ratio or None
        """
        quick_assets = current_assets - inventory
        return safe_divide(quick_assets, current_liabilities, None)

    @staticmethod
    def calculate_asset_turnover(revenue: float, total_assets: float) -> Optional[float]:
        """Calculate Asset Turnover ratio.

        Args:
            revenue: Total revenue (TTM)
            total_assets: Average total assets

        Returns:
            Asset turnover ratio or None
        """
        return safe_divide(revenue, total_assets, None)

    @staticmethod
    def calculate_dividend_yield(
        annual_dividend: float,
        price: float,
    ) -> Optional[float]:
        """Calculate Dividend Yield.

        Args:
            annual_dividend: Annual dividend per share
            price: Current stock price

        Returns:
            Dividend yield as percentage or None
        """
        div_yield = safe_divide(annual_dividend, price, None)
        return div_yield * 100 if div_yield is not None else None

    @staticmethod
    def calculate_earnings_yield(price: float, eps_ttm: float) -> Optional[float]:
        """Calculate Earnings Yield (inverse of P/E).

        Args:
            price: Current stock price
            eps_ttm: Trailing twelve months EPS

        Returns:
            Earnings yield as percentage or None
        """
        earn_yield = safe_divide(eps_ttm, price, None)
        return earn_yield * 100 if earn_yield is not None else None

    @staticmethod
    def calculate_revenue_growth(
        current_revenue: float,
        previous_revenue: float,
    ) -> Optional[float]:
        """Calculate Revenue Growth rate.

        Args:
            current_revenue: Current period revenue
            previous_revenue: Previous period revenue

        Returns:
            Revenue growth as percentage or None
        """
        if previous_revenue and previous_revenue != 0:
            growth = ((current_revenue - previous_revenue) / abs(previous_revenue)) * 100
            return growth
        return None

    @staticmethod
    def calculate_eps_growth(current_eps: float, previous_eps: float) -> Optional[float]:
        """Calculate EPS Growth rate.

        Args:
            current_eps: Current period EPS
            previous_eps: Previous period EPS

        Returns:
            EPS growth as percentage or None
        """
        if previous_eps and previous_eps != 0:
            growth = ((current_eps - previous_eps) / abs(previous_eps)) * 100
            return growth
        return None
