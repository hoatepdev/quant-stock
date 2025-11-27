# Hướng Dẫn Backtest Hoàn Chỉnh

Hướng dẫn đầy đủ về backtest engine của VNQuant, bao gồm quickstart, tham khảo nhanh, và chi tiết kỹ thuật.

---

## Mục Lục

- [1. Quick Start - Bắt Đầu Nhanh](#1-quick-start---bắt-đầu-nhanh)
- [2. Quick Reference - Tham Khảo Nhanh](#2-quick-reference---tham-khảo-nhanh)
- [3. Hướng Dẫn Chi Tiết](#3-hướng-dẫn-chi-tiết)
- [4. Tính Năng Nâng Cao](#4-tính-năng-nâng-cao)
- [5. Technical Details](#5-technical-details)

---

# 1. Quick Start - Bắt Đầu Nhanh

Bắt đầu backtest trong 5 phút.

## 🚀 Các Bước Cơ Bản

### Bước 1: Đảm bảo có dữ liệu

```bash
# Khởi động hệ thống
make docker-up

# Khởi tạo database
make init-db

# Nạp dữ liệu cho một vài mã để test
python scripts/backfill_data.py --tickers VCB,VNM,HPG --start-date 2023-01-01
```

### Bước 2: Chạy Backtest Đơn Giản

```bash
# Backtest chiến lược Moving Average
make backtest-ma
```

Hoặc:

```bash
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM,HPG
```

### Bước 3: So Sánh Các Chiến Lược

```bash
# So sánh tất cả chiến lược
make backtest-compare
```

### Bước 4: Xem Kết Quả

Kết quả sẽ hiển thị trên terminal và được lưu trong thư mục `backtest_results/`:
- `*.json`: Kết quả chi tiết
- `*_trades.csv`: Danh sách giao dịch
- `*_equity.png`: Biểu đồ equity curve

---

## 📊 Các Lệnh Nhanh

### Backtest với Chiến Lược Khác Nhau

```bash
# Moving Average
make backtest-ma

# Momentum
make backtest-momentum

# Mean Reversion
make backtest-mean-reversion

# So sánh tất cả
make backtest-compare
```

### Tùy Chỉnh Tham Số

```bash
# MA với tham số khác
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM \
  --short-window 10 \
  --long-window 30

# Momentum với nhiều cổ phiếu
python scripts/run_backtest.py \
  --strategy momentum \
  --tickers VCB,VNM,HPG,VIC,MSN,FPT,MWG,VRE \
  --lookback 30 \
  --top-n 3
```

### Lưu Kết Quả và Biểu Đồ

```bash
# Lưu kết quả và tạo biểu đồ
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --save \
  --plot
```

---

## 🎯 Các Chiến Lược Có Sẵn

| Chiến lược | Mã | Mô tả | Phù hợp |
|------------|-----|-------|---------|
| **Moving Average** | `ma` | Mua khi MA ngắn cắt lên MA dài | Thị trường có xu hướng |
| **Momentum** | `momentum` | Mua cổ phiếu tăng mạnh nhất | Thị trường tăng |
| **Mean Reversion** | `mean_reversion` | Mua khi giá quá thấp, bán khi quá cao | Thị trường sideway |
| **Buy & Hold** | `buy_hold` | Mua và giữ | Benchmark |

---

# 2. Quick Reference - Tham Khảo Nhanh

## TL;DR

```bash
# ✅ RECOMMENDED: Realistic mode (default)
make backtest-realistic

# Or manually:
python scripts/run_backtest.py --strategy buy_hold --tickers VHC,PVT

# ❌ NOT RECOMMENDED: Baseline mode (overly optimistic)
make backtest-baseline
```

**Key difference:** Realistic mode gives ~70% lower returns for low-liquidity stocks, but represents actual tradeable performance.

---

## Command Cheat Sheet

### Quick Commands (via Makefile)

```bash
# Compare realistic vs baseline
make backtest-test-slippage

# Run with realistic execution (slippage + dynamic sizing)
make backtest-realistic

# Run baseline (theoretical maximum, not realistic)
make backtest-baseline

# Compare all strategies
make backtest-compare

# Show all backtest commands
make help
```

### Manual Commands (via Python script)

```bash
# Basic backtest (realistic mode by default)
python scripts/run_backtest.py \
  --strategy buy_hold \
  --tickers VHC,PVT,VCB

# Custom date range
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --start-date 2023-01-01 \
  --end-date 2024-12-31

# Baseline mode (disable realistic features)
python scripts/run_backtest.py \
  --strategy buy_hold \
  --tickers VHC,PVT \
  --no-slippage \
  --no-dynamic-sizing

# Compare all strategies
python scripts/run_backtest.py \
  --compare \
  --tickers VCB,VNM,HPG,VIC,MSN

# Save results and plot
python scripts/run_backtest.py \
  --strategy momentum \
  --tickers VCB,VNM \
  --save \
  --plot
```

---

## Understanding the Results

### Example Output

```
Vốn ban đầu:         100,000,000 VND
Giá trị cuối:        100,702,050 VND
Lợi nhuận:                 0.70%    ← Realistic return
P&L:                     702,050 VND

--- THỐNG KÊ GIAO DỊCH ---
Tổng giao dịch:                2
Thắng:                         2
Thua:                          0
Tỷ lệ thắng:             100.00%
Sharpe Ratio:               0.00    ← Risk-adjusted return (0 = neutral)
Sortino Ratio:              0.00    ← Downside risk metric
Max Drawdown:               0.00%   ← Maximum decline from peak
```

### What the Numbers Mean

**Total Return:**
- Realistic: What you can actually achieve
- Baseline: Theoretical maximum (2-3x higher)
- **Use realistic for decision-making**

**Sharpe Ratio:**
- > 2.0: Excellent risk-adjusted returns
- > 1.0: Good
- > 0.5: Acceptable
- < 0: Losing money on average

**Sortino Ratio:**
- Similar to Sharpe but only penalizes downside
- Better for strategies with upside volatility
- Higher is better

**Max Drawdown:**
- Maximum peak-to-trough decline
- 10%: Low risk
- 20%: Moderate risk
- >30%: High risk

---

## Mode Comparison

| Feature | Baseline Mode | Realistic Mode (Default) |
|---------|---------------|--------------------------|
| **Slippage** | ❌ No | ✅ Yes (sqrt model) |
| **Position sizing** | ❌ Unlimited | ✅ Limited by volume |
| **Execution price** | Exact close | Close + slippage |
| **Max position** | 100% capital | min(20% capital, 5% volume) |
| **Typical returns** | Higher (theoretical) | Lower (realistic) |
| **Use case** | Academic study | Trading decisions |

### When to Use Each Mode

**Realistic Mode (Default):**
- ✅ Planning actual trades
- ✅ Evaluating strategy performance
- ✅ Risk assessment
- ✅ Portfolio allocation
- ✅ **Always use this for production**

**Baseline Mode:**
- ⚠️ Understanding theoretical maximum
- ⚠️ Academic comparisons
- ⚠️ Algorithm development (before reality check)
- ❌ **Never use for trading decisions**

---

## Common Parameters

### Strategy Parameters

**Moving Average (ma):**
```bash
--short-window 20  # Short MA period (default: 20)
--long-window 50   # Long MA period (default: 50)
```

**Momentum:**
```bash
--lookback 20      # Lookback period (default: 20)
--top-n 5          # Top N stocks to buy (default: 5)
```

**Mean Reversion:**
```bash
--window 20        # Bollinger Band period (default: 20)
--std-threshold 2.0 # Standard deviation (default: 2.0)
```

### Execution Parameters

```bash
--capital 200000000         # Initial capital (default: 100M VND)
--commission 0.002          # Commission rate (default: 0.15%)
--start-date 2023-01-01     # Start date
--end-date 2024-12-31       # End date
--no-slippage               # Disable slippage (not recommended)
--no-dynamic-sizing         # Disable position sizing (not recommended)
```

### Output Parameters

```bash
--save                      # Save results to files
--plot                      # Generate equity curve charts
--output-dir results        # Output directory (default: backtest_results)
```

---

## Tips & Best Practices

### 1. Always Start with Realistic Mode

```bash
# ✅ GOOD
python scripts/run_backtest.py --strategy buy_hold --tickers VHC,PVT

# ❌ BAD
python scripts/run_backtest.py --strategy buy_hold --tickers VHC,PVT --no-slippage --no-dynamic-sizing
```

### 2. Compare Before Trading

```bash
# Test realistic vs baseline to understand impact
make backtest-test-slippage
```

Expected: Realistic returns will be 20-80% lower depending on liquidity.

### 3. Check Multiple Strategies

```bash
# Compare all strategies to find the best fit
make backtest-compare
```

### 4. Validate with Recent Data

```bash
# Test with last 3 months to avoid overfitting
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM \
  --start-date 2024-09-01
```

### 5. Monitor Risk Metrics

- Sharpe < 0.5: Consider different strategy
- Max DD > 30%: Too risky for most investors
- Win rate < 40%: Strategy needs improvement

---

# 3. Hướng Dẫn Chi Tiết

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

## Các Chiến Lược Chi Tiết

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

## Tạo Chiến Lược Riêng

### Bước 1: Tạo File Chiến Lược

```python
"""Chiến lược giao dịch tùy chỉnh của tôi."""

from typing import Dict
import pandas as pd
from src.core.backtesting.engine import Portfolio

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
    """
    signals = {}

    if len(data) < rsi_period + 1:
        return signals

    for ticker in current_prices.keys():
        try:
            close_prices = data[("close", ticker)]

            # Tính RSI
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            has_position = any(p.ticker == ticker for p in portfolio.positions)

            if current_rsi < oversold and not has_position:
                signals[ticker] = "BUY"
            elif current_rsi > overbought and has_position:
                signals[ticker] = "SELL"

        except Exception:
            continue

    return signals
```

Xem thêm ví dụ trong [examples/custom_strategy_example.py](../examples/custom_strategy_example.py)

---

## Best Practices

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

---

# 4. Tính Năng Nâng Cao

## Realistic Execution Features

### 1. Slippage Model

Mô phỏng giá thực thi khác với giá lý thuyết dựa trên khối lượng giao dịch.

**Công thức:**
```
slippage_pct = min(0.1 * sqrt(shares / volume), 5%)
execution_price_buy = base_price + slippage
execution_price_sell = base_price - slippage
```

**Ví dụ:**
- VCB (volume cao): Slippage ~0.7%
- D2D (volume thấp): Slippage ~4.5%

### 2. Dynamic Position Sizing

Tính toán khối lượng giao dịch dựa trên thanh khoản thực tế.

**Rules:**
- Max 20% vốn cho 1 position
- Max 5% khối lượng giao dịch ngày

**Impact:**
- Blue-chips: Ít ảnh hưởng (~10-20%)
- Mid-caps: Ảnh hưởng vừa (~30-40%)
- Small-caps: Ảnh hưởng lớn (~70-90%)

### 3. Risk Metrics

- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Sortino Ratio**: Only penalize downside volatility
- **Maximum Drawdown**: Peak-to-trough decline

---

## Optimization Techniques

### Grid Search

```bash
#!/bin/bash
for short in 10 20 30; do
  for long in 50 100 200; do
    if [ $short -lt $long ]; then
      python scripts/run_backtest.py \
        --strategy ma \
        --tickers VCB,VNM,HPG \
        --short-window $short \
        --long-window $long \
        --save
    fi
  done
done
```

### Walk-Forward Analysis

```bash
# Test trên các quý khác nhau
for quarter in Q1 Q2 Q3 Q4; do
  python scripts/run_backtest.py \
    --strategy ma \
    --tickers VCB,VNM \
    --start-date 2023-${quarter}-01 \
    --end-date 2023-${quarter}-30
done
```

---

# 5. Technical Details

## Slippage Model Implementation

```python
class SlippageModel:
    @staticmethod
    def calculate_slippage(
        price: Decimal,
        volume: int,
        shares: int,
        impact_coefficient: float = 0.1
    ) -> Decimal:
        """Calculate slippage using square-root market impact model."""
        if volume == 0:
            return price * Decimal("0.005")

        volume_percentage = shares / volume if volume > 0 else 1.0
        slippage_pct = min(impact_coefficient * math.sqrt(volume_percentage), 0.05)

        return price * Decimal(str(slippage_pct))
```

## Position Sizing Implementation

```python
class PositionSizer:
    @staticmethod
    def calculate_shares(
        available_capital: Decimal,
        price: Decimal,
        daily_volume: int,
        max_pct_of_volume: float = 0.05,
        max_pct_of_capital: float = 0.2,
    ) -> int:
        """Calculate maximum shares based on liquidity constraints."""
        capital_limit = available_capital * Decimal(str(max_pct_of_capital))
        max_shares_capital = int(capital_limit / price) if price > 0 else 0

        max_shares_volume = int(daily_volume * max_pct_of_volume)

        return min(max_shares_capital, max_shares_volume)
```

## Risk Metrics Calculation

### Sharpe Ratio

```python
mean_return = np.mean(daily_returns)
std_return = np.std(daily_returns)
sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
```

### Sortino Ratio

```python
downside_returns = [r for r in returns if r < 0]
downside_std = np.std(downside_returns)
sortino = (mean_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
```

### Maximum Drawdown

```python
def _calculate_max_drawdown(self) -> float:
    values = [entry["value"] for entry in self.equity_curve]
    peak = values[0]
    max_dd = 0.0

    for value in values:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)

    return max_dd
```

---

## Test Results - VHC + PVT (2024)

| Mode | Total Return | Impact vs Baseline |
|------|--------------|-------------------|
| **Baseline** (no features) | 3.25% | - |
| **Slippage only** | 2.40% | -0.85% |
| **Dynamic sizing only** | 0.81% | -2.44% |
| **Realistic** (both) | 0.70% | -2.55% |

**Phân tích:**
- Slippage impact: -0.85% (moderate)
- Position sizing impact: -2.44% (significant for low-liquidity stocks)
- Combined: 78% of baseline returns lost due to realistic constraints

---

## Troubleshooting

### Q: Returns too low in realistic mode?

**A:** This is expected for low-liquidity stocks. Solutions:
1. Increase `min_avg_volume` in screening (500K instead of 100K)
2. Focus on blue-chip stocks (VCB, VNM, HPG)
3. Accept lower but more realistic returns

### Q: How to interpret Sharpe ratio = 0?

**A:** Zero Sharpe means risk-free rate = return rate. For buy & hold with low trades, this is normal. Focus on total return for buy & hold strategies.

### Q: Baseline vs realistic returns differ by 5x?

**A:** Check stock liquidity. If volume < 100K shares/day → large impact is expected.

---

## Further Reading

- **Screening Guide**: [docs/STOCK_SCREENING_GUIDE.md](STOCK_SCREENING_GUIDE.md)
- **Quant Trading Workflow**: [docs/guides/HUONG_DAN_QUANT_TRADING.md](guides/HUONG_DAN_QUANT_TRADING.md)
- **Phase 2 Documentation**: [docs/phases/PHASE2.md](phases/PHASE2.md)
- **Examples**: [examples/custom_strategy_example.py](../examples/custom_strategy_example.py)

---

**Last updated:** 2025-11-27

**Built with ❤️ for Vietnamese quantitative investors**
