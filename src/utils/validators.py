"""Data validation utilities."""
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_ticker(ticker: str) -> bool:
    """Validate ticker symbol format.

    Args:
        ticker: Stock ticker symbol

    Returns:
        True if valid

    Raises:
        ValidationError: If ticker is invalid
    """
    if not ticker:
        raise ValidationError("Ticker cannot be empty")

    if not ticker.isalnum():
        raise ValidationError(f"Ticker '{ticker}' contains invalid characters")

    if len(ticker) > 10:
        raise ValidationError(f"Ticker '{ticker}' is too long (max 10 characters)")

    return True


def validate_ohlc_data(
    open_price: Decimal,
    high: Decimal,
    low: Decimal,
    close: Decimal,
    volume: int,
) -> bool:
    """Validate OHLC price data relationships.

    Args:
        open_price: Opening price
        high: High price
        low: Low price
        close: Closing price
        volume: Trading volume

    Returns:
        True if valid

    Raises:
        ValidationError: If data is invalid
    """
    if high < low:
        raise ValidationError(f"High ({high}) cannot be less than low ({low})")

    if high < open_price:
        raise ValidationError(f"High ({high}) cannot be less than open ({open_price})")

    if high < close:
        raise ValidationError(f"High ({high}) cannot be less than close ({close})")

    if low > open_price:
        raise ValidationError(f"Low ({low}) cannot be greater than open ({open_price})")

    if low > close:
        raise ValidationError(f"Low ({low}) cannot be greater than close ({close})")

    if volume < 0:
        raise ValidationError(f"Volume ({volume}) cannot be negative")

    # Check for unrealistic price movements (Vietnam has ±7% daily limit, but allow ±10% for edge cases)
    if open_price > 0:
        daily_change = abs((close - open_price) / open_price) * 100
        if daily_change > 15:
            logger.warning(
                f"Unusual price movement detected: {daily_change:.2f}% "
                f"(open={open_price}, close={close})"
            )

    return True


def validate_financial_ratio(
    ratio_name: str,
    value: float,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> bool:
    """Validate financial ratio values are within reasonable ranges.

    Args:
        ratio_name: Name of the ratio
        value: Ratio value
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Returns:
        True if valid

    Raises:
        ValidationError: If ratio is out of reasonable range
    """
    # Define reasonable ranges for common ratios
    ratio_ranges = {
        "pe_ratio": (-1000, 1000),
        "pb_ratio": (-100, 100),
        "roe": (-500, 500),
        "roa": (-500, 500),
        "debt_to_equity": (0, 50),
        "current_ratio": (0, 100),
        "gross_margin": (-100, 100),
        "net_margin": (-100, 100),
    }

    if ratio_name.lower() in ratio_ranges:
        default_min, default_max = ratio_ranges[ratio_name.lower()]
        min_val = min_value if min_value is not None else default_min
        max_val = max_value if max_value is not None else default_max

        if not (min_val <= value <= max_val):
            raise ValidationError(
                f"{ratio_name} value {value} is outside reasonable range "
                f"[{min_val}, {max_val}]"
            )

    return True


def detect_outliers(
    df: pd.DataFrame,
    column: str,
    method: str = "iqr",
    threshold: float = 3.0,
) -> pd.Series:
    """Detect outliers in a data series.

    Args:
        df: DataFrame containing the data
        column: Column name to check for outliers
        method: Detection method ('iqr' or 'zscore')
        threshold: Threshold for outlier detection

    Returns:
        Boolean Series indicating outliers
    """
    if method == "iqr":
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        return (df[column] < lower_bound) | (df[column] > upper_bound)

    elif method == "zscore":
        mean = df[column].mean()
        std = df[column].std()
        z_scores = ((df[column] - mean) / std).abs()
        return z_scores > threshold

    else:
        raise ValueError(f"Unknown outlier detection method: {method}")


def check_data_completeness(
    df: pd.DataFrame,
    required_columns: List[str],
    max_missing_pct: float = 0.1,
) -> Dict[str, Any]:
    """Check data completeness and missing values.

    Args:
        df: DataFrame to check
        required_columns: List of required column names
        max_missing_pct: Maximum allowed percentage of missing values

    Returns:
        Dictionary with completeness statistics
    """
    results = {
        "total_rows": len(df),
        "missing_columns": [],
        "incomplete_columns": {},
        "is_complete": True,
    }

    # Check for missing columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        results["missing_columns"] = list(missing_cols)
        results["is_complete"] = False

    # Check missing values in each column
    for col in required_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_pct = missing_count / len(df)
                if missing_pct > max_missing_pct:
                    results["incomplete_columns"][col] = {
                        "missing_count": int(missing_count),
                        "missing_percentage": round(missing_pct * 100, 2),
                    }
                    results["is_complete"] = False

    return results


def validate_date_range(
    start_date: date,
    end_date: date,
    max_years: int = 20,
) -> bool:
    """Validate date range parameters.

    Args:
        start_date: Start date
        end_date: End date
        max_years: Maximum allowed years in range

    Returns:
        True if valid

    Raises:
        ValidationError: If date range is invalid
    """
    if start_date > end_date:
        raise ValidationError(
            f"Start date ({start_date}) cannot be after end date ({end_date})"
        )

    days_diff = (end_date - start_date).days
    if days_diff > max_years * 365:
        raise ValidationError(
            f"Date range is too large ({days_diff} days). "
            f"Maximum allowed is {max_years} years"
        )

    if end_date > date.today():
        raise ValidationError(
            f"End date ({end_date}) cannot be in the future"
        )

    return True


def validate_exchange(exchange: str) -> bool:
    """Validate Vietnam stock exchange name.

    Args:
        exchange: Exchange name

    Returns:
        True if valid

    Raises:
        ValidationError: If exchange is invalid
    """
    valid_exchanges = {"HOSE", "HNX", "UPCOM"}

    if exchange.upper() not in valid_exchanges:
        raise ValidationError(
            f"Invalid exchange '{exchange}'. "
            f"Must be one of: {', '.join(valid_exchanges)}"
        )

    return True
