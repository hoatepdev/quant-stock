"""Momentum factor calculations."""
from typing import Optional

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MomentumFactors:
    """Calculate momentum-based investment factors."""

    @staticmethod
    def calculate_returns(df: pd.DataFrame, periods: list = [5, 21, 63, 126, 252]) -> pd.DataFrame:
        """Calculate returns over multiple periods.

        Args:
            df: DataFrame with 'close' column
            periods: List of periods for return calculation
                    (5=1week, 21=1month, 63=3months, 126=6months, 252=1year)

        Returns:
            DataFrame with return columns
        """
        result = pd.DataFrame(index=df.index)

        for period in periods:
            result[f"return_{period}d"] = df["close"].pct_change(periods=period) * 100

        return result

    @staticmethod
    def calculate_momentum_6m(df: pd.DataFrame, skip_recent_days: int = 21) -> pd.Series:
        """Calculate 6-month momentum skipping recent period.

        This follows the common practice of skipping the most recent month
        to avoid short-term reversal effects.

        Args:
            df: DataFrame with 'close' column
            skip_recent_days: Days to skip from recent data (default 21 = 1 month)

        Returns:
            6-month momentum values
        """
        # Calculate return from 6 months ago to 1 month ago
        shifted_close = df["close"].shift(skip_recent_days)
        shifted_close_6m = df["close"].shift(126)  # 6 months

        return ((shifted_close - shifted_close_6m) / shifted_close_6m) * 100

    @staticmethod
    def calculate_relative_strength(
        stock_df: pd.DataFrame,
        market_df: pd.DataFrame,
        period: int = 126,
    ) -> pd.Series:
        """Calculate relative strength vs market index.

        Args:
            stock_df: DataFrame with stock 'close' prices
            market_df: DataFrame with market index 'close' prices
            period: Period for return calculation

        Returns:
            Relative strength values
        """
        stock_returns = stock_df["close"].pct_change(periods=period) * 100
        market_returns = market_df["close"].pct_change(periods=period) * 100

        return stock_returns - market_returns

    @staticmethod
    def calculate_new_high_indicator(df: pd.DataFrame, period: int = 252) -> pd.Series:
        """Calculate indicator for stocks making new highs.

        Args:
            df: DataFrame with 'close' column
            period: Lookback period (252 = 1 year)

        Returns:
            Binary indicator (1 if new high, 0 otherwise)
        """
        rolling_max = df["close"].rolling(window=period, min_periods=1).max()
        return (df["close"] >= rolling_max).astype(int)

    @staticmethod
    def calculate_new_low_indicator(df: pd.DataFrame, period: int = 252) -> pd.Series:
        """Calculate indicator for stocks making new lows.

        Args:
            df: DataFrame with 'close' column
            period: Lookback period (252 = 1 year)

        Returns:
            Binary indicator (1 if new low, 0 otherwise)
        """
        rolling_min = df["close"].rolling(window=period, min_periods=1).min()
        return (df["close"] <= rolling_min).astype(int)

    @staticmethod
    def calculate_price_acceleration(df: pd.DataFrame) -> pd.Series:
        """Calculate price acceleration (rate of change of returns).

        Args:
            df: DataFrame with 'close' column

        Returns:
            Price acceleration values
        """
        returns_21d = df["close"].pct_change(periods=21)
        returns_63d = df["close"].pct_change(periods=63)

        # Acceleration is the difference in momentum
        return (returns_21d - returns_63d) * 100

    @staticmethod
    def calculate_risk_adjusted_momentum(
        df: pd.DataFrame,
        return_period: int = 126,
        volatility_period: int = 63,
    ) -> pd.Series:
        """Calculate risk-adjusted momentum (return / volatility).

        Args:
            df: DataFrame with 'close' column
            return_period: Period for return calculation
            volatility_period: Period for volatility calculation

        Returns:
            Risk-adjusted momentum (Sharpe-like ratio)
        """
        returns = df["close"].pct_change(periods=return_period)
        volatility = df["close"].pct_change().rolling(window=volatility_period).std()

        # Avoid division by zero
        volatility = volatility.replace(0, float("nan"))

        return returns / volatility

    @staticmethod
    def calculate_consecutive_up_days(df: pd.DataFrame, window: int = 252) -> pd.Series:
        """Calculate number of consecutive up days in recent period.

        Args:
            df: DataFrame with 'close' column
            window: Rolling window for calculation

        Returns:
            Count of consecutive up days
        """
        daily_returns = df["close"].pct_change()
        up_days = (daily_returns > 0).astype(int)

        # Calculate consecutive up days
        consecutive = up_days.rolling(window=window, min_periods=1).sum()

        return consecutive

    @staticmethod
    def calculate_momentum_score(
        df: pd.DataFrame,
        weights: Optional[dict] = None,
    ) -> pd.Series:
        """Calculate composite momentum score from multiple timeframes.

        Args:
            df: DataFrame with 'close' column
            weights: Dictionary of period weights (default: equal weights)

        Returns:
            Composite momentum score
        """
        if weights is None:
            weights = {
                21: 0.20,   # 1 month
                63: 0.30,   # 3 months
                126: 0.30,  # 6 months
                252: 0.20,  # 1 year
            }

        score = pd.Series(0.0, index=df.index)

        for period, weight in weights.items():
            returns = df["close"].pct_change(periods=period) * 100
            score += returns * weight

        return score

    @staticmethod
    def calculate_momentum_percentile(
        df: pd.DataFrame,
        period: int = 126,
        window: int = 252,
    ) -> pd.Series:
        """Calculate momentum percentile rank over rolling window.

        Args:
            df: DataFrame with 'close' column
            period: Period for return calculation
            window: Rolling window for percentile calculation

        Returns:
            Momentum percentile rank (0-100)
        """
        returns = df["close"].pct_change(periods=period)

        # Calculate rolling percentile rank
        percentile = returns.rolling(window=window).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100
            if len(x) > 0 else None
        )

        return percentile
