"""
Ví dụ về cách tạo chiến lược giao dịch tùy chỉnh.

File này chứa các ví dụ về chiến lược bạn có thể tạo và test.
"""

import sys
from pathlib import Path
from typing import Dict

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.backtesting.engine import Portfolio
from src.utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# VÍ DỤ 1: CHIẾN LƯỢC RSI
# =============================================================================

def rsi_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict[str, float],
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0
) -> Dict[str, str]:
    """
    Chiến lược RSI (Relative Strength Index).

    Logic:
    - Mua khi RSI < 30 (oversold - quá bán)
    - Bán khi RSI > 70 (overbought - quá mua)

    Args:
        data: DataFrame giá lịch sử
        portfolio: Portfolio hiện tại
        current_prices: Giá hiện tại
        rsi_period: Kỳ tính RSI (mặc định 14)
        oversold: Ngưỡng quá bán (mặc định 30)
        overbought: Ngưỡng quá mua (mặc định 70)

    Returns:
        Dict[ticker, signal] với signal là "BUY", "SELL", hoặc "HOLD"
    """
    signals = {}

    if len(data) < rsi_period + 1:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]

            if len(close_prices) < rsi_period + 1:
                continue

            # Tính RSI
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Mua khi oversold
            if current_rsi < oversold and not has_position:
                signals[ticker] = "BUY"
                logger.debug(f"BUY {ticker}: RSI={current_rsi:.2f}")

            # Bán khi overbought
            elif current_rsi > overbought and has_position:
                signals[ticker] = "SELL"
                logger.debug(f"SELL {ticker}: RSI={current_rsi:.2f}")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


# =============================================================================
# VÍ DỤ 2: CHIẾN LƯỢC MACD
# =============================================================================

def macd_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict[str, float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, str]:
    """
    Chiến lược MACD (Moving Average Convergence Divergence).

    Logic:
    - Mua khi MACD cắt lên Signal line
    - Bán khi MACD cắt xuống Signal line

    Args:
        data: DataFrame giá lịch sử
        portfolio: Portfolio hiện tại
        current_prices: Giá hiện tại
        fast_period: EMA nhanh (mặc định 12)
        slow_period: EMA chậm (mặc định 26)
        signal_period: Signal line (mặc định 9)

    Returns:
        Dict[ticker, signal]
    """
    signals = {}

    min_period = slow_period + signal_period

    if len(data) < min_period:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]

            if len(close_prices) < min_period:
                continue

            # Tính MACD
            ema_fast = close_prices.ewm(span=fast_period, adjust=False).mean()
            ema_slow = close_prices.ewm(span=slow_period, adjust=False).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal_period, adjust=False).mean()

            # Giá trị hiện tại và trước đó
            curr_macd = macd.iloc[-1]
            curr_signal = signal_line.iloc[-1]
            prev_macd = macd.iloc[-2]
            prev_signal = signal_line.iloc[-2]

            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Bullish crossover: MACD cắt lên Signal
            if prev_macd <= prev_signal and curr_macd > curr_signal:
                if not has_position:
                    signals[ticker] = "BUY"
                    logger.debug(f"BUY {ticker}: MACD crossover")

            # Bearish crossover: MACD cắt xuống Signal
            elif prev_macd >= prev_signal and curr_macd < curr_signal:
                if has_position:
                    signals[ticker] = "SELL"
                    logger.debug(f"SELL {ticker}: MACD crossunder")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


# =============================================================================
# VÍ DỤ 3: CHIẾN LƯỢC ĐỘT PHÁ KÊNH (BREAKOUT)
# =============================================================================

def breakout_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict[str, float],
    lookback: int = 20,
    breakout_threshold: float = 0.02  # 2%
) -> Dict[str, str]:
    """
    Chiến lược đột phá kênh.

    Logic:
    - Mua khi giá vượt qua đỉnh của N ngày trước
    - Bán khi giá giảm xuống dưới đáy của N ngày trước

    Args:
        data: DataFrame giá lịch sử
        portfolio: Portfolio hiện tại
        current_prices: Giá hiện tại
        lookback: Số ngày nhìn lại (mặc định 20)
        breakout_threshold: % vượt qua để xác nhận breakout (mặc định 2%)

    Returns:
        Dict[ticker, signal]
    """
    signals = {}

    if len(data) < lookback:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]
            high_prices = data[("high", ticker)]
            low_prices = data[("low", ticker)]

            if len(close_prices) < lookback:
                continue

            # Tìm đỉnh và đáy trong lookback period (không bao gồm ngày hiện tại)
            highest = high_prices.iloc[-lookback:-1].max()
            lowest = low_prices.iloc[-lookback:-1].min()

            current_price = close_prices.iloc[-1]

            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Breakout lên trên
            if current_price > highest * (1 + breakout_threshold):
                if not has_position:
                    signals[ticker] = "BUY"
                    logger.debug(
                        f"BUY {ticker}: Breakout above {highest:.2f}, "
                        f"current {current_price:.2f}"
                    )

            # Breakdown xuống dưới
            elif current_price < lowest * (1 - breakout_threshold):
                if has_position:
                    signals[ticker] = "SELL"
                    logger.debug(
                        f"SELL {ticker}: Breakdown below {lowest:.2f}, "
                        f"current {current_price:.2f}"
                    )

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


# =============================================================================
# VÍ DỤ 4: CHIẾN LƯỢC KẾT HỢP (COMBO)
# =============================================================================

def combo_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict[str, float]
) -> Dict[str, str]:
    """
    Chiến lược kết hợp nhiều chỉ báo.

    Logic:
    - Mua khi:
        * MA20 > MA50 (uptrend)
        * RSI < 50 (chưa quá mua)
        * Volume > average volume * 1.2 (có volume)

    - Bán khi:
        * RSI > 70 (quá mua)
        HOẶC
        * MA20 < MA50 (downtrend)

    Args:
        data: DataFrame giá lịch sử
        portfolio: Portfolio hiện tại
        current_prices: Giá hiện tại

    Returns:
        Dict[ticker, signal]
    """
    signals = {}

    min_period = 50

    if len(data) < min_period:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]
            volume = data[("volume", ticker)]

            if len(close_prices) < min_period:
                continue

            # Tính các chỉ báo
            ma20 = close_prices.rolling(window=20).mean()
            ma50 = close_prices.rolling(window=50).mean()

            # RSI
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Volume average
            avg_volume = volume.rolling(window=20).mean()

            # Giá trị hiện tại
            curr_ma20 = ma20.iloc[-1]
            curr_ma50 = ma50.iloc[-1]
            curr_rsi = rsi.iloc[-1]
            curr_volume = volume.iloc[-1]
            curr_avg_volume = avg_volume.iloc[-1]

            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Logic mua
            if not has_position:
                buy_conditions = [
                    curr_ma20 > curr_ma50,  # Uptrend
                    curr_rsi < 50,  # Chưa quá mua
                    curr_volume > curr_avg_volume * 1.2  # Volume cao
                ]

                if all(buy_conditions):
                    signals[ticker] = "BUY"
                    logger.debug(
                        f"BUY {ticker}: MA20={curr_ma20:.2f}, MA50={curr_ma50:.2f}, "
                        f"RSI={curr_rsi:.2f}, Vol={curr_volume:.0f}"
                    )

            # Logic bán
            else:
                sell_conditions = [
                    curr_rsi > 70,  # Quá mua
                    curr_ma20 < curr_ma50  # Downtrend
                ]

                if any(sell_conditions):
                    signals[ticker] = "SELL"
                    logger.debug(
                        f"SELL {ticker}: MA20={curr_ma20:.2f}, MA50={curr_ma50:.2f}, "
                        f"RSI={curr_rsi:.2f}"
                    )

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


# =============================================================================
# VÍ DỤ 5: CHIẾN LƯỢC TRAILING STOP
# =============================================================================

def trailing_stop_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict[str, float],
    entry_rsi_threshold: float = 30.0,
    trailing_stop_pct: float = 0.10  # 10%
) -> Dict[str, str]:
    """
    Chiến lược với trailing stop loss.

    Logic:
    - Mua khi RSI < 30 (oversold)
    - Bán khi giá giảm 10% so với giá cao nhất kể từ khi mua

    Args:
        data: DataFrame giá lịch sử
        portfolio: Portfolio hiện tại
        current_prices: Giá hiện tại
        entry_rsi_threshold: Ngưỡng RSI để vào lệnh
        trailing_stop_pct: % trailing stop

    Returns:
        Dict[ticker, signal]
    """
    signals = {}

    if len(data) < 14:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]

            if len(close_prices) < 14:
                continue

            # Tính RSI
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            current_price = current_prices[ticker]

            # Tìm position cho ticker này (nếu có)
            position = next(
                (p for p in portfolio.positions if p.ticker == ticker),
                None
            )

            # Logic mua: RSI oversold
            if not position and current_rsi < entry_rsi_threshold:
                signals[ticker] = "BUY"
                logger.debug(f"BUY {ticker}: RSI={current_rsi:.2f}")

            # Logic bán: trailing stop
            elif position:
                # Tìm giá cao nhất từ khi mua
                entry_index = close_prices[close_prices.index >= position.entry_date].index[0]
                prices_since_entry = close_prices.loc[entry_index:]
                highest_since_entry = prices_since_entry.max()

                # Tính trailing stop price
                trailing_stop_price = highest_since_entry * (1 - trailing_stop_pct)

                if current_price < trailing_stop_price:
                    signals[ticker] = "SELL"
                    logger.debug(
                        f"SELL {ticker}: Trailing stop hit. "
                        f"Highest={highest_since_entry:.2f}, "
                        f"Stop={trailing_stop_price:.2f}, "
                        f"Current={current_price:.2f}"
                    )

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


# =============================================================================
# CÁCH SỬ DỤNG
# =============================================================================

if __name__ == "__main__":
    """
    Demo cách sử dụng các chiến lược tùy chỉnh.
    """

    from datetime import date, timedelta
    from decimal import Decimal
    from src.core.backtesting.engine import BacktestEngine
    from src.database.connection import get_sync_session

    # Kết nối DB
    db = next(get_sync_session())

    # Khởi tạo engine
    engine = BacktestEngine(db, initial_capital=Decimal("100000000"))

    # Thiết lập
    tickers = ["VCB", "VNM", "HPG"]
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    print("="*70)
    print("DEMO CHIẾN LƯỢC TÙY CHỈNH")
    print("="*70)

    # Test từng chiến lược
    strategies_to_test = {
        "RSI Strategy": rsi_strategy,
        "MACD Strategy": macd_strategy,
        "Breakout Strategy": breakout_strategy,
        "Combo Strategy": combo_strategy,
        "Trailing Stop Strategy": trailing_stop_strategy
    }

    for name, strategy in strategies_to_test.items():
        print(f"\nTesting {name}...")

        # Reset engine
        engine = BacktestEngine(db, initial_capital=Decimal("100000000"))

        try:
            results = engine.run(
                strategy=strategy,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date
            )

            if results:
                print(f"  ✓ Return: {results['total_return']:.2%}")
                print(f"  ✓ Trades: {results['statistics']['total_trades']}")
                print(f"  ✓ Win Rate: {results['statistics']['win_rate']:.2%}")
            else:
                print(f"  ✗ No results")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    db.close()

    print("\n" + "="*70)
    print("Để sử dụng chiến lược của bạn với run_backtest.py:")
    print("1. Copy chiến lược vào file riêng (vd: my_strategy.py)")
    print("2. Import và test trong script Python")
    print("3. Hoặc tích hợp vào BacktestRunner trong run_backtest.py")
    print("="*70)
