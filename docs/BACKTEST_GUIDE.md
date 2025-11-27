# 📊 Hướng Dẫn Chi Tiết Backtest

Hướng dẫn sử dụng công cụ backtest để kiểm thử chiến lược giao dịch trên dữ liệu lịch sử.

## Mục Lục

- [Giới Thiệu](#giới-thiệu)
- [Cài Đặt](#cài-đặt)
- [Sử Dụng Cơ Bản](#sử-dụng-cơ-bản)
- [Các Chiến Lược Có Sẵn](#các-chiến-lược-có-sẵn)
- [Tùy Chỉnh Tham Số](#tùy-chỉnh-tham-số)
- [So Sánh Chiến Lược](#so-sánh-chiến-lược)
- [Xuất Kết Quả](#xuất-kết-quả)
- [Tạo Chiến Lược Riêng](#tạo-chiến-lược-riêng)
- [Tips & Best Practices](#tips--best-practices)

---

## Giới Thiệu

**Backtest** là quá trình kiểm thử một chiến lược giao dịch trên dữ liệu lịch sử để đánh giá hiệu quả của nó trước khi áp dụng vào giao dịch thực tế.

### Tại sao cần Backtest?

- ✅ **Kiểm chứng ý tưởng**: Xem chiến lược có hiệu quả không
- ✅ **Tối ưu tham số**: Tìm bộ tham số tối ưu
- ✅ **Đánh giá rủi ro**: Hiểu rõ drawdown, win rate, etc.
- ✅ **Tăng tự tin**: Biết chiến lược hoạt động trước khi dùng tiền thật

### Các Chỉ Số Quan Trọng

- **Total Return**: Tổng lợi nhuận (%)
- **Win Rate**: Tỷ lệ giao dịch thắng
- **Profit Factor**: Tỷ lệ lợi nhuận/thua lỗ
- **Max Drawdown**: Thua lỗ tối đa từ đỉnh
- **Sharpe Ratio**: Lợi nhuận điều chỉnh theo rủi ro

---

## Cài Đặt

### Bước 1: Đảm bảo có dữ liệu

```bash
# Khởi động hệ thống
make docker-up
make init-db

# Nạp dữ liệu cho các mã cụ thể
python scripts/backfill_data.py --tickers VCB,VNM,HPG,VIC,MSN --start-date 2023-01-01

# Hoặc nạp toàn bộ
make backfill-data
```

### Bước 2: Cài thư viện cần thiết

```bash
pip install matplotlib pandas
```

---

## Sử Dụng Cơ Bản

### Backtest Đơn Giản

Backtest chiến lược Moving Average với VCB, VNM, HPG:

```bash
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG
```

Kết quả:

```
======================================================================
KẾT QUẢ BACKTEST - MA
======================================================================

Thời gian: 2024-01-01 → 2024-12-31
Mã CP: VCB, VNM, HPG
Tham số: {'short_window': 20, 'long_window': 50}

--- TỔNG QUAN ---
Vốn ban đầu:        100,000,000 VND
Giá trị cuối:       112,500,000 VND
Lợi nhuận:                12.50%
P&L:                 12,500,000 VND

--- THỐNG KÊ GIAO DỊCH ---
Tổng giao dịch:                 24
Thắng:                          15
Thua:                            9
Tỷ lệ thắng:                62.50%
P&L trung bình:         520,833 VND
Thắng TB:             1,200,000 VND
Thua TB:               -650,000 VND
Profit Factor:               1.85
```

### Xem Tất Cả Tùy Chọn

```bash
python scripts/run_backtest.py --help
```

---

## Các Chiến Lược Có Sẵn

### 1. Moving Average Crossover (`ma`)

**Nguyên lý**: Mua khi MA ngắn hạn cắt lên MA dài hạn, bán khi cắt xuống.

```bash
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --short-window 20 \
  --long-window 50
```

**Tham số**:
- `--short-window`: MA ngắn hạn (mặc định: 20 ngày)
- `--long-window`: MA dài hạn (mặc định: 50 ngày)

**Phù hợp**: Thị trường có xu hướng rõ ràng

---

### 2. Momentum Strategy (`momentum`)

**Nguyên lý**: Mua cổ phiếu tăng mạnh nhất, bán cổ phiếu yếu.

```bash
python scripts/run_backtest.py \
  --strategy momentum \
  --tickers VCB,VNM,HPG,VIC,MSN,FPT,MWG,VRE \
  --lookback 20 \
  --top-n 5
```

**Tham số**:
- `--lookback`: Kỳ tính momentum (mặc định: 20 ngày)
- `--top-n`: Số lượng cổ phiếu giữ (mặc định: 5)

**Phù hợp**: Thị trường tăng mạnh, xu hướng kéo dài

---

### 3. Mean Reversion (`mean_reversion`)

**Nguyên lý**: Mua khi giá quá thấp (dưới lower band), bán khi quá cao (trên upper band).

```bash
python scripts/run_backtest.py \
  --strategy mean_reversion \
  --tickers VCB,VNM,HPG \
  --window 20 \
  --std-threshold 2.0
```

**Tham số**:
- `--window`: Kỳ tính Bollinger Bands (mặc định: 20 ngày)
- `--std-threshold`: Số độ lệch chuẩn (mặc định: 2.0)

**Phù hợp**: Thị trường sideway, dao động

---

### 4. Buy and Hold (`buy_hold`)

**Nguyên lý**: Mua và giữ từ đầu đến cuối.

```bash
python scripts/run_backtest.py \
  --strategy buy_hold \
  --tickers VCB,VNM,HPG
```

**Phù hợp**: Benchmark để so sánh với các chiến lược khác

---

## Tùy Chỉnh Tham Số

### Thời Gian Backtest

```bash
# Backtest từ 2023-01-01 đến 2024-12-31
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM \
  --start-date 2023-01-01 \
  --end-date 2024-12-31
```

### Vốn và Phí

```bash
# Vốn 200 triệu, phí 0.2%
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --capital 200000000 \
  --commission 0.002
```

### Tối Ưu Tham Số

Thử nhiều bộ tham số để tìm tối ưu:

```bash
# MA 10-30
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM --short-window 10 --long-window 30

# MA 20-50 (mặc định)
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM --short-window 20 --long-window 50

# MA 50-200
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM --short-window 50 --long-window 200
```

---

## So Sánh Chiến Lược

### So Sánh Tất Cả Chiến Lược

```bash
python scripts/run_backtest.py \
  --compare \
  --tickers VCB,VNM,HPG,VIC,MSN
```

Kết quả:

```
====================================================================================================
SO SÁNH CHIẾN LƯỢC
====================================================================================================

Chiến lược          | Lợi nhuận    | P&L             | Giao dịch  | Tỷ lệ thắng  | Profit Factor
----------------------------------------------------------------------------------------------------
ma                  |      12.50% |   12,500,000    |         24 |      62.50%  |           1.85
momentum            |      18.30% |   18,300,000    |         48 |      58.33%  |           1.92
mean_reversion      |       8.20% |    8,200,000    |         36 |      55.56%  |           1.45
buy_hold            |      15.00% |   15,000,000    |          3 |     100.00%  |           0.00

🏆 Chiến lược tốt nhất: MOMENTUM (18.30%)
```

---

## Xuất Kết Quả

### Lưu Kết Quả

```bash
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --save
```

Tạo các file trong `backtest_results/`:
- `ma_20250126.json`: Kết quả chi tiết
- `ma_20250126_trades.csv`: Danh sách giao dịch
- `ma_20250126_equity.csv`: Equity curve

### Tạo Biểu Đồ

```bash
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --plot
```

Tạo biểu đồ equity curve: `backtest_results/ma_20250126_equity.png`

### Lưu và Vẽ Biểu Đồ

```bash
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --save \
  --plot \
  --output-dir my_results
```

### So Sánh và Vẽ Biểu Đồ

```bash
python scripts/run_backtest.py \
  --compare \
  --tickers VCB,VNM,HPG,VIC,MSN \
  --plot \
  --save
```

Tạo biểu đồ so sánh: `backtest_results/comparison_20250126.png`

---

## Tạo Chiến Lược Riêng

### Bước 1: Tạo File Chiến Lược

Tạo file `my_custom_strategy.py`:

```python
"""Chiến lược giao dịch tùy chỉnh của tôi."""

from typing import Dict
import pandas as pd
from src.core.backtesting.engine import Portfolio
from src.utils.logger import get_logger

logger = get_logger(__name__)


def my_rsi_strategy(
    data: pd.DataFrame,
    portfolio: Portfolio,
    current_prices: Dict[str, float],
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0
) -> Dict[str, str]:
    """
    Chiến lược RSI.

    Logic:
    - Mua khi RSI < oversold (30)
    - Bán khi RSI > overbought (70)

    Args:
        data: DataFrame giá lịch sử
        portfolio: Portfolio hiện tại
        current_prices: Giá hiện tại
        rsi_period: Kỳ tính RSI
        oversold: Ngưỡng quá bán
        overbought: Ngưỡng quá mua

    Returns:
        Dict[ticker, signal] - signal là "BUY", "SELL", hoặc "HOLD"
    """
    signals = {}

    # Cần đủ dữ liệu
    if len(data) < rsi_period + 1:
        return signals

    for ticker in current_prices.keys():
        try:
            # Lấy giá đóng cửa
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

            # Kiểm tra có vị thế không
            has_position = any(p.ticker == ticker for p in portfolio.positions)

            # Logic mua: RSI < oversold và chưa có vị thế
            if current_rsi < oversold and not has_position:
                signals[ticker] = "BUY"
                logger.info(f"BUY {ticker}: RSI={current_rsi:.2f} (oversold)")

            # Logic bán: RSI > overbought và đang có vị thế
            elif current_rsi > overbought and has_position:
                signals[ticker] = "SELL"
                logger.info(f"SELL {ticker}: RSI={current_rsi:.2f} (overbought)")

        except Exception as e:
            logger.warning(f"Error processing {ticker}: {e}")
            continue

    return signals


# Wrapper để dễ sử dụng
def create_rsi_strategy(rsi_period=14, oversold=30, overbought=70):
    """Factory function để tạo chiến lược RSI với tham số."""
    def strategy(data, portfolio, prices):
        return my_rsi_strategy(
            data, portfolio, prices,
            rsi_period=rsi_period,
            oversold=oversold,
            overbought=overbought
        )
    return strategy
```

### Bước 2: Sử Dụng Chiến Lược

Tạo file `test_my_strategy.py`:

```python
"""Test chiến lược RSI."""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.backtesting.engine import BacktestEngine
from src.database.connection import get_sync_session
from my_custom_strategy import create_rsi_strategy

# Kết nối DB
db = next(get_sync_session())

# Khởi tạo engine
engine = BacktestEngine(db, initial_capital=Decimal("100000000"))

# Thiết lập
tickers = ["VCB", "VNM", "HPG"]
end_date = date.today()
start_date = end_date - timedelta(days=365)

# Tạo chiến lược
my_strategy = create_rsi_strategy(
    rsi_period=14,
    oversold=30,
    overbought=70
)

# Chạy backtest
print("Đang chạy backtest với chiến lược RSI...")
results = engine.run(
    strategy=my_strategy,
    tickers=tickers,
    start_date=start_date,
    end_date=end_date
)

# Hiển thị kết quả
print(f"\nVốn ban đầu: {results['initial_capital']:,.0f} VND")
print(f"Giá trị cuối: {results['final_value']:,.0f} VND")
print(f"Lợi nhuận: {results['total_return']:.2%}")
print(f"Số giao dịch: {results['statistics']['total_trades']}")
print(f"Tỷ lệ thắng: {results['statistics']['win_rate']:.2%}")

db.close()
```

Chạy:

```bash
python test_my_strategy.py
```

---

## Tips & Best Practices

### ⚠️ Những Điều Cần Tránh

1. **Overfitting**: Tối ưu quá mức trên dữ liệu quá khứ
   - ❌ Test với 100 bộ tham số, chọn tốt nhất
   - ✅ Chia dữ liệu: train (60%), validation (20%), test (20%)

2. **Look-Ahead Bias**: Sử dụng dữ liệu tương lai
   - ❌ Dùng giá đóng cửa hôm sau để quyết định hôm nay
   - ✅ Chỉ dùng dữ liệu đến thời điểm hiện tại

3. **Survivorship Bias**: Chỉ test trên cổ phiếu "sống sót"
   - ❌ Chỉ test VN30 hiện tại
   - ✅ Test trên cả cổ phiếu đã bị hủy niêm yết

4. **Bỏ qua Chi Phí**: Không tính phí, thuế, slippage
   - ❌ Backtest không phí
   - ✅ Luôn tính phí 0.15% + slippage

### ✅ Quy Trình Đề Xuất

```
1. Ý tưởng → Xây dựng chiến lược
2. Backtest trên dữ liệu train (2020-2022)
3. Validate trên dữ liệu validation (2023)
4. Walk-forward test (2024)
5. Paper trading 1-3 tháng
6. Live trading với vốn nhỏ
7. Scale up nếu thành công
```

### 📊 Tiêu Chí Đánh Giá

Một chiến lược tốt cần:

- ✅ **Total Return > 15%/năm** (cao hơn lãi suất ngân hàng đáng kể)
- ✅ **Win Rate > 50%** (trên 50% giao dịch thắng)
- ✅ **Profit Factor > 1.5** (lời nhiều hơn lỗ 1.5 lần)
- ✅ **Max Drawdown < 20%** (thua tối đa không quá 20%)
- ✅ **Sharpe Ratio > 1.0** (lợi nhuận điều chỉnh rủi ro)

### 🔧 Tối Ưu Hóa

#### Grid Search

Test nhiều tham số:

```bash
#!/bin/bash
# test_ma_params.sh

for short in 10 20 30; do
  for long in 50 100 200; do
    if [ $short -lt $long ]; then
      echo "Testing MA $short/$long"
      python scripts/run_backtest.py \
        --strategy ma \
        --tickers VCB,VNM,HPG \
        --short-window $short \
        --long-window $long \
        --save \
        --output-dir results/ma_${short}_${long}
    fi
  done
done
```

#### Walk-Forward Analysis

```bash
# 2023 Q1
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM \
  --start-date 2023-01-01 --end-date 2023-03-31

# 2023 Q2
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM \
  --start-date 2023-04-01 --end-date 2023-06-30

# 2023 Q3
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM \
  --start-date 2023-07-01 --end-date 2023-09-30

# 2023 Q4
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM \
  --start-date 2023-10-01 --end-date 2023-12-31
```

### 📝 Ghi Chép

Luôn ghi lại:
- Ý tưởng chiến lược
- Kết quả backtest
- Tham số sử dụng
- Nhận xét, điều chỉnh
- Lý do thành công/thất bại

---

## Ví Dụ Hoàn Chỉnh

### Workflow A-Z

```bash
# 1. Chuẩn bị dữ liệu
python scripts/backfill_data.py --tickers VCB,VNM,HPG,VIC,MSN --start-date 2022-01-01

# 2. So sánh các chiến lược
python scripts/run_backtest.py \
  --compare \
  --tickers VCB,VNM,HPG,VIC,MSN \
  --start-date 2023-01-01 \
  --end-date 2024-12-31 \
  --plot \
  --save

# 3. Chọn chiến lược tốt nhất (giả sử là momentum)
# Tối ưu tham số
python scripts/run_backtest.py \
  --strategy momentum \
  --tickers VCB,VNM,HPG,VIC,MSN,FPT,MWG,VRE \
  --lookback 30 \
  --top-n 3 \
  --plot \
  --save

# 4. Walk-forward test
python scripts/run_backtest.py \
  --strategy momentum \
  --tickers VCB,VNM,HPG,VIC,MSN,FPT,MWG,VRE \
  --lookback 30 \
  --top-n 3 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --plot

# 5. Nếu OK → Paper trading
# Xem hướng dẫn paper trading trong HUONG_DAN_QUANT_TRADING.md
```

---

## Tài Liệu Tham Khảo

- [Hướng Dẫn Quant Trading](HUONG_DAN_QUANT_TRADING.md) - Workflow đầy đủ
- [Stock Screening Guide](STOCK_SCREENING_GUIDE.md) - Tìm cổ phiếu
- [Phase 2 Documentation](../phases/PHASE2.md) - Backtesting & Portfolio
- [API Documentation](http://localhost:8000/docs) - API endpoints

---

## Câu Hỏi Thường Gặp

### Q: Backtest cho kết quả tốt nhưng live trading lỗ?

**A**: Có thể do:
- Overfitting (tối ưu quá mức trên dữ liệu quá khứ)
- Slippage (giá thực tế khác giá backtest)
- Thị trường thay đổi (quá khứ không đại diện tương lai)
- Chi phí giao dịch cao hơn dự tính

**Giải pháp**:
- Test trên nhiều khoảng thời gian
- Paper trading trước khi live
- Tính đủ chi phí trong backtest
- Monitor và điều chỉnh chiến lược

### Q: Cần bao nhiêu dữ liệu để backtest?

**A**: Tối thiểu 1-2 năm, lý tưởng 3-5 năm để bao quát nhiều điều kiện thị trường.

### Q: Làm sao biết chiến lược tốt?

**A**: So sánh với buy-and-hold benchmark. Nếu không beat được buy-hold, chiến lược không đủ tốt.

### Q: Có thể backtest với short (bán khống)?

**A**: Hiện tại hệ thống hỗ trợ SHORT trong code nhưng thị trường VN hạn chế short. Tốt nhất chỉ dùng LONG.

---

**Chúc bạn backtest thành công!** 🚀

Nếu có câu hỏi, hãy tạo issue tại [GitHub Issues](https://github.com/your-repo/vnquant/issues).
