"""Helper utilities and common functions."""
from datetime import date, datetime, timedelta
from typing import List, Optional

import pandas as pd
import pytz
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.utils.config import get_settings

settings = get_settings()


def get_vietnam_timezone() -> pytz.timezone:
    """Get Vietnam timezone.

    Returns:
        Vietnam timezone object
    """
    return pytz.timezone("Asia/Ho_Chi_Minh")


def get_current_vietnam_time() -> datetime:
    """Get current time in Vietnam timezone.

    Returns:
        Current datetime in Vietnam timezone
    """
    return datetime.now(get_vietnam_timezone())


def is_trading_day(check_date: date) -> bool:
    """Check if a given date is a trading day (not weekend or holiday).

    Args:
        check_date: Date to check

    Returns:
        True if trading day, False otherwise

    Note:
        Currently only checks for weekends.
        TODO: Add Vietnam holiday calendar
    """
    # Monday = 0, Sunday = 6
    return check_date.weekday() < 5


def get_trading_days(
    start_date: date,
    end_date: date,
    include_holidays: bool = False,
) -> List[date]:
    """Get list of trading days between start and end dates.

    Args:
        start_date: Start date
        end_date: End date
        include_holidays: Whether to include holidays (default: False)

    Returns:
        List of trading days
    """
    days = []
    current_date = start_date

    while current_date <= end_date:
        if include_holidays or is_trading_day(current_date):
            days.append(current_date)
        current_date += timedelta(days=1)

    return days


def get_last_trading_day(reference_date: Optional[date] = None) -> date:
    """Get the last trading day before or on the reference date.

    Args:
        reference_date: Reference date (default: today)

    Returns:
        Last trading day
    """
    if reference_date is None:
        reference_date = date.today()

    current_date = reference_date
    while not is_trading_day(current_date):
        current_date -= timedelta(days=1)

    return current_date


def get_next_trading_day(reference_date: Optional[date] = None) -> date:
    """Get the next trading day after the reference date.

    Args:
        reference_date: Reference date (default: today)

    Returns:
        Next trading day
    """
    if reference_date is None:
        reference_date = date.today()

    current_date = reference_date + timedelta(days=1)
    while not is_trading_day(current_date):
        current_date += timedelta(days=1)

    return current_date


def chunk_list(items: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size.

    Args:
        items: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero

    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
            return default
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default


def calculate_percentage_change(
    current: float,
    previous: float,
    default: float = 0.0,
) -> float:
    """Calculate percentage change between two values.

    Args:
        current: Current value
        previous: Previous value
        default: Default value if calculation fails

    Returns:
        Percentage change
    """
    if previous == 0 or pd.isna(previous) or pd.isna(current):
        return default

    try:
        return ((current - previous) / abs(previous)) * 100
    except (ZeroDivisionError, TypeError):
        return default


def convert_to_billions(value: float) -> float:
    """Convert value to billions (Vietnamese dong to billion dong).

    Args:
        value: Value in Vietnamese dong

    Returns:
        Value in billions
    """
    return value / 1_000_000_000


def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0):
    """Decorator for retrying failed operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff

    Returns:
        Retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )


def format_large_number(value: float, decimals: int = 2) -> str:
    """Format large numbers with appropriate suffix (K, M, B, T).

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.{decimals}f}T"
    elif abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.{decimals}f}B"
    elif abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.{decimals}f}M"
    elif abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.{decimals}f}K"
    else:
        return f"{sign}{abs_value:.{decimals}f}"


def calculate_ttm(
    df: pd.DataFrame,
    value_column: str,
    date_column: str = "date",
) -> pd.Series:
    """Calculate Trailing Twelve Months (TTM) values.

    Args:
        df: DataFrame with quarterly data
        value_column: Column name for values to sum
        date_column: Column name for dates

    Returns:
        Series with TTM values
    """
    df = df.sort_values(date_column)
    return df[value_column].rolling(window=4, min_periods=4).sum()
