"""Technical factor calculations using pandas-ta."""
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TechnicalFactors:
    """Calculate technical analysis indicators."""

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index.

        Args:
            df: DataFrame with 'close' column
            period: RSI period (default 14)

        Returns:
            RSI values
        """
        return ta.rsi(df["close"], length=period)

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        """Calculate MACD indicator.

        Args:
            df: DataFrame with 'close' column
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            DataFrame with MACD, signal, and histogram
        """
        macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
        return macd

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std: float = 2.0,
    ) -> pd.DataFrame:
        """Calculate Bollinger Bands.

        Args:
            df: DataFrame with 'close' column
            period: Moving average period
            std: Number of standard deviations

        Returns:
            DataFrame with upper, middle, lower bands
        """
        bbands = ta.bbands(df["close"], length=period, std=std)
        return bbands

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period

        Returns:
            ATR values
        """
        return ta.atr(df["high"], df["low"], df["close"], length=period)

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ADX period

        Returns:
            ADX values
        """
        adx = ta.adx(df["high"], df["low"], df["close"], length=period)
        if adx is not None and f"ADX_{period}" in adx.columns:
            return adx[f"ADX_{period}"]
        return pd.Series()

    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume.

        Args:
            df: DataFrame with 'close' and 'volume' columns

        Returns:
            OBV values
        """
        return ta.obv(df["close"], df["volume"])

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price.

        Args:
            df: DataFrame with 'high', 'low', 'close', 'volume' columns

        Returns:
            VWAP values
        """
        return ta.vwap(df["high"], df["low"], df["close"], df["volume"])

    @staticmethod
    def calculate_moving_averages(
        df: pd.DataFrame,
        periods: list = [5, 10, 20, 50, 200],
    ) -> pd.DataFrame:
        """Calculate Simple Moving Averages for multiple periods.

        Args:
            df: DataFrame with 'close' column
            periods: List of MA periods

        Returns:
            DataFrame with MA columns
        """
        result = pd.DataFrame(index=df.index)
        for period in periods:
            result[f"sma_{period}"] = ta.sma(df["close"], length=period)
        return result

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average.

        Args:
            df: DataFrame with 'close' column
            period: EMA period

        Returns:
            EMA values
        """
        return ta.ema(df["close"], length=period)

    @staticmethod
    def calculate_stochastic(
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3,
    ) -> pd.DataFrame:
        """Calculate Stochastic Oscillator.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            k_period: %K period
            d_period: %D period

        Returns:
            DataFrame with %K and %D values
        """
        stoch = ta.stoch(df["high"], df["low"], df["close"], k=k_period, d=d_period)
        return stoch

    @staticmethod
    def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: Williams %R period

        Returns:
            Williams %R values
        """
        return ta.willr(df["high"], df["low"], df["close"], length=period)

    @staticmethod
    def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Money Flow Index.

        Args:
            df: DataFrame with 'high', 'low', 'close', 'volume' columns
            period: MFI period

        Returns:
            MFI values
        """
        return ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)

    @staticmethod
    def calculate_volume_ma_ratio(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate ratio of current volume to moving average volume.

        Args:
            df: DataFrame with 'volume' column
            period: MA period for volume

        Returns:
            Volume MA ratio
        """
        volume_ma = ta.sma(df["volume"], length=period)
        return df["volume"] / volume_ma

    @staticmethod
    def calculate_distance_from_52w_high(df: pd.DataFrame) -> pd.Series:
        """Calculate distance from 52-week high.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Percentage distance from 52-week high
        """
        rolling_max = df["close"].rolling(window=252, min_periods=1).max()
        return ((df["close"] - rolling_max) / rolling_max) * 100

    @staticmethod
    def calculate_distance_from_52w_low(df: pd.DataFrame) -> pd.Series:
        """Calculate distance from 52-week low.

        Args:
            df: DataFrame with 'close' column

        Returns:
            Percentage distance from 52-week low
        """
        rolling_min = df["close"].rolling(window=252, min_periods=1).min()
        return ((df["close"] - rolling_min) / rolling_min) * 100
