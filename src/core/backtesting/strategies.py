"""Sample trading strategies for backtesting."""
from typing import Dict, Optional

import pandas as pd

from src.core.backtesting.engine import Portfolio
from src.utils.logger import get_logger

logger = get_logger(__name__)


def simple_moving_average_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict,
    short_window: int = 20,
    long_window: int = 50,
) -> Dict[str, str]:
    """Simple moving average crossover strategy.

    Buy when short MA crosses above long MA.
    Sell when short MA crosses below long MA.

    Args:
        data: Historical price data
        portfolio: Current portfolio
        current_prices: Current prices
        short_window: Short moving average window
        long_window: Long moving average window

    Returns:
        Dictionary of ticker -> signal (BUY, SELL, HOLD)
    """
    signals = {}

    if len(data) < long_window:
        return signals

    for ticker in current_prices.keys():
        try:
            # Calculate moving averages
            close_prices = data[("close", ticker)]

            if len(close_prices) < long_window:
                continue

            short_ma = close_prices.rolling(window=short_window).mean()
            long_ma = close_prices.rolling(window=long_window).mean()

            # Get current and previous values
            curr_short = short_ma.iloc[-1]
            curr_long = long_ma.iloc[-1]
            prev_short = short_ma.iloc[-2] if len(short_ma) > 1 else None
            prev_long = long_ma.iloc[-2] if len(long_ma) > 1 else None

            if prev_short is None or prev_long is None:
                continue

            # Check for crossover
            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Bullish crossover
            if prev_short <= prev_long and curr_short > curr_long:
                if not has_position:
                    signals[ticker] = "BUY"
                    logger.debug(f"BUY signal for {ticker}: MA crossover")

            # Bearish crossover
            elif prev_short >= prev_long and curr_short < curr_long:
                if has_position:
                    signals[ticker] = "SELL"
                    logger.debug(f"SELL signal for {ticker}: MA crossunder")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


def momentum_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict,
    lookback: int = 20,
    top_n: int = 5,
) -> Dict[str, str]:
    """Momentum strategy - buy top performers, sell bottom performers.

    Args:
        data: Historical price data
        portfolio: Current portfolio
        current_prices: Current prices
        lookback: Lookback period for momentum calculation
        top_n: Number of top stocks to hold

    Returns:
        Dictionary of ticker -> signal
    """
    signals = {}

    if len(data) < lookback:
        return signals

    try:
        # Calculate momentum for each ticker
        momentum_scores = {}

        for ticker in current_prices.keys():
            try:
                close_prices = data[("close", ticker)]

                if len(close_prices) < lookback:
                    continue

                # Calculate momentum as % change over lookback period
                current_price = close_prices.iloc[-1]
                past_price = close_prices.iloc[-lookback]

                if past_price > 0:
                    momentum = (current_price - past_price) / past_price
                    momentum_scores[ticker] = momentum

            except:
                continue

        if not momentum_scores:
            return signals

        # Sort by momentum
        sorted_tickers = sorted(
            momentum_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Get top N tickers
        top_tickers = [ticker for ticker, _ in sorted_tickers[:top_n]]

        # Current holdings
        current_holdings = {p.ticker for p in portfolio.positions}

        # Buy signals for top tickers not held
        for ticker in top_tickers:
            if ticker not in current_holdings:
                signals[ticker] = "BUY"
                logger.debug(f"BUY signal for {ticker}: high momentum")

        # Sell signals for holdings not in top N
        for ticker in current_holdings:
            if ticker not in top_tickers:
                signals[ticker] = "SELL"
                logger.debug(f"SELL signal for {ticker}: low momentum")

    except Exception as e:
        logger.error(f"Error in momentum strategy: {e}")

    return signals


def mean_reversion_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict,
    window: int = 20,
    std_threshold: float = 2.0,
) -> Dict[str, str]:
    """Mean reversion strategy using Bollinger Bands.

    Buy when price drops below lower band.
    Sell when price rises above upper band.

    Args:
        data: Historical price data
        portfolio: Current portfolio
        current_prices: Current prices
        window: Moving average window
        std_threshold: Number of standard deviations for bands

    Returns:
        Dictionary of ticker -> signal
    """
    signals = {}

    if len(data) < window:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]

            if len(close_prices) < window:
                continue

            # Calculate Bollinger Bands
            rolling_mean = close_prices.rolling(window=window).mean()
            rolling_std = close_prices.rolling(window=window).std()

            upper_band = rolling_mean + (rolling_std * std_threshold)
            lower_band = rolling_mean - (rolling_std * std_threshold)

            current_price = close_prices.iloc[-1]
            curr_upper = upper_band.iloc[-1]
            curr_lower = lower_band.iloc[-1]

            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Price below lower band - oversold, buy signal
            if current_price < curr_lower and not has_position:
                signals[ticker] = "BUY"
                logger.debug(f"BUY signal for {ticker}: oversold")

            # Price above upper band - overbought, sell signal
            elif current_price > curr_upper and has_position:
                signals[ticker] = "SELL"
                logger.debug(f"SELL signal for {ticker}: overbought")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


def buy_and_hold_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict,
) -> Dict[str, str]:
    """Simple buy and hold strategy.

    Buy on first day and hold until end.

    Args:
        data: Historical price data
        portfolio: Current portfolio
        current_prices: Current prices

    Returns:
        Dictionary of ticker -> signal
    """
    signals = {}

    # Only buy if we don't have any positions
    if not portfolio.positions:
        for ticker in current_prices.keys():
            signals[ticker] = "BUY"

    return signals
