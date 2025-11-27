# Examples - Ví Dụ Sử Dụng

Thư mục này chứa các ví dụ về cách sử dụng hệ thống VNQuant.

## 📁 Các File Ví Dụ

### 1. Custom Strategy Example
**File**: `custom_strategy_example.py`

Các chiến lược giao dịch tùy chỉnh bao gồm:

- **RSI Strategy**: Mua khi RSI < 30, bán khi RSI > 70
- **MACD Strategy**: Mua/bán dựa trên MACD crossover
- **Breakout Strategy**: Giao dịch khi giá đột phá kênh
- **Combo Strategy**: Kết hợp nhiều chỉ báo (MA + RSI + Volume)
- **Trailing Stop Strategy**: Sử dụng trailing stop loss

**Cách chạy**:
```bash
python examples/custom_strategy_example.py
```

hoặc:

```bash
make backtest-custom
```

## 🚀 Cách Sử Dụng

### 1. Chạy Tất Cả Ví Dụ

```bash
cd examples
python custom_strategy_example.py
```

### 2. Sử Dụng Chiến Lược Trong Backtest

```python
from custom_strategy_example import rsi_strategy

# Import backtest engine
from src.core.backtesting.engine import BacktestEngine
from src.database.connection import get_sync_session

# Setup
db = next(get_sync_session())
engine = BacktestEngine(db)

# Chạy backtest
results = engine.run(
    strategy=rsi_strategy,
    tickers=["VCB", "VNM", "HPG"],
    start_date=...,
    end_date=...
)
```

### 3. Tùy Chỉnh Chiến Lược

Copy một chiến lược từ `custom_strategy_example.py` và chỉnh sửa theo ý bạn:

```python
def my_custom_strategy(data, portfolio, current_prices):
    """Chiến lược của bạn."""
    signals = {}

    # Logic của bạn ở đây
    for ticker in current_prices.keys():
        # Phân tích và tạo tín hiệu
        if condition_to_buy:
            signals[ticker] = "BUY"
        elif condition_to_sell:
            signals[ticker] = "SELL"

    return signals
```

## 📚 Tài Liệu Tham Khảo

- [Backtest Complete Guide](../docs/BACKTEST_COMPLETE_GUIDE.md) - Hướng dẫn hoàn chỉnh về backtest (bao gồm quickstart và advanced features)
- [Quant Trading Guide](../docs/guides/HUONG_DAN_QUANT_TRADING.md) - Workflow đầy đủ

## 💡 Tips

1. **Test từng chiến lược riêng**: Hiểu rõ cách hoạt động trước khi kết hợp
2. **So sánh với Buy & Hold**: Đảm bảo chiến lược tốt hơn mua và giữ
3. **Tối ưu tham số**: Thử nhiều bộ tham số khác nhau
4. **Walk-forward test**: Test trên nhiều khoảng thời gian

## 🎯 Tiếp Theo

Sau khi hiểu các ví dụ:

1. Tạo chiến lược riêng của bạn
2. Backtest với dữ liệu lịch sử
3. Tối ưu tham số
4. Paper trading
5. Live trading (với risk management)

---

**Happy Trading!** 📈
