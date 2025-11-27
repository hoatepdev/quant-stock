# Stock Screening Improvements - Giải quyết vấn đề Lookback Bias và Quality Filters

## Vấn đề ban đầu

Khi chạy stock screening, các mã được chọn (D2D, KKC, VCM, PDB, DDV, SJD) có chỉ số tài chính tốt nhưng **lợi nhuận backtest thấp hơn** các mã blue-chip (VCB, VNM, HPG, VIC, MSN).

### Nguyên nhân phân tích

1. **Lookback Bias (Thiên lệch thời gian)**
   - Screening sử dụng dữ liệu mới nhất (2025-09-30)
   - Backtest chạy trên dữ liệu lịch sử
   - Chỉ số tài chính hiện tại ≠ Chỉ số trong quá khứ

2. **Value Trap (Bẫy giá trị)**
   - P/E ratio quá thấp (D2D: 3.33)
   - Dividend yield quá cao (D2D: 12.9%)
   - Growth rate bất thường (D2D: Revenue +278%, EPS +641%)
   - Thiếu tính bền vững

3. **Thiếu Liquidity Filter**
   - D2D volume: 49,200 shares/day
   - VCB volume: 2,699,600 shares/day
   - Backtest không tính slippage → Lợi nhuận thực tế thấp hơn

4. **Thiếu Market Cap Filter**
   - Không có dữ liệu market cap cho nhiều stocks
   - Có thể chọn phải micro-cap stocks
   - Rủi ro cao, thanh khoản kém

## Giải pháp đã implement

### 1. Thêm Liquidity Filter (Minimum Average Volume)

```python
# Tính average volume trong 30 ngày qua
min_avg_volume: int = 100_000  # 100K shares/day minimum

WITH avg_volumes AS (
    SELECT ticker, AVG(volume) as avg_volume
    FROM daily_price
    WHERE date >= :thirty_days_ago
    GROUP BY ticker
)
...
AND COALESCE(av.avg_volume, 0) >= :min_avg_volume
```

**Lợi ích:**
- Loại bỏ stocks thanh khoản kém
- Đảm bảo có thể trade thực tế
- Giảm slippage trong thực tế

### 2. Thêm Market Cap Filter (Optional)

```python
min_market_cap: float = 1_000_000_000_000  # 1 trillion VND

AND (si.market_cap >= :min_market_cap OR si.market_cap IS NULL)
```

**Lưu ý:** Market cap là optional vì nhiều stocks thiếu dữ liệu này trong database.

### 3. Growth Sustainability Checks

**Value Strategy:**
```python
# Reject abnormal growth rates (>100%)
AND (fr.revenue_growth_yoy IS NULL OR fr.revenue_growth_yoy < 100)
AND (fr.eps_growth_yoy IS NULL OR fr.eps_growth_yoy < 100)
```

**Growth Strategy:**
```python
# Only accept sustainable growth (20-80% range)
AND fr.revenue_growth_yoy BETWEEN 20 AND 80
AND fr.eps_growth_yoy BETWEEN 20 AND 80
```

**Lợi ích:**
- Loại bỏ growth bất thường (base effect)
- Chỉ chọn stocks có tăng trưởng bền vững
- Tránh value traps

### 4. Điều chỉnh Dividend Yield Range

**Trước:**
```python
AND fr.dividend_yield > 3
```

**Sau:**
```python
# Value: Giảm threshold
AND (fr.dividend_yield > 2 OR fr.dividend_yield IS NULL)

# Dividend Strategy: Thêm upper bound
AND fr.dividend_yield BETWEEN :min_yield AND :max_yield  # 4-15%
```

**Lợi ích:**
- Tránh chọn stocks có dividend không bền vững (>15%)
- Value strategy linh hoạt hơn với dividend

### 5. Cập nhật CLI với New Parameters

```bash
# Mặc định: Market cap >= 1T VND, Volume >= 100K shares/day
python scripts/screen_stocks.py strategy --strategy=value

# Custom filters
python scripts/screen_stocks.py strategy \
  --strategy=value \
  --min-market-cap=5 \      # 5 trillion VND
  --min-volume=500000       # 500K shares/day

# Chạy tất cả strategies
python scripts/screen_stocks.py strategy --strategy=all --limit=10
```

## Kết quả sau khi cải tiến

### So sánh Before vs After

| Metric | Before (D2D) | After (VHC) | After (PVT) |
|--------|--------------|-------------|-------------|
| **Volume (avg 30d)** | 49,200 | 1,478,945 | 3,216,631 |
| **P/E Ratio** | 3.33 | 8.28 | 8.85 |
| **Dividend Yield** | 12.9% | 3.48% | 5.41% |
| **Revenue Growth** | 278.92% | 5.63% | 50.62% |
| **EPS Growth** | 641.33% | 35.05% | -27.84% |
| **ROE** | 44.32% | 17.00% | 12.22% |
| **Assessment** | ❌ Value trap | ✅ Sustainable | ✅ High liquidity |

### Các stocks mới được chọn (Value Strategy)

1. **ECI** - P/E: 4.75, Volume: 124K, Dividend: 11.11%
2. **DRI** - P/E: 6.02, Volume: 614K, Dividend: 7.06%
3. **VHC** - P/E: 8.28, Volume: 1.5M, Dividend: 3.48%
4. **PVT** - P/E: 8.85, Volume: 3.2M, Dividend: 5.41%
5. **DHC** - P/E: 10.37, Volume: 229K, Dividend: 6.06%

**Đặc điểm chung:**
- ✅ Thanh khoản cao hơn (>100K shares/day)
- ✅ Growth rate hợp lý (<100%)
- ✅ P/E ratio không quá thấp (tránh value trap)
- ✅ Có thể trade thực tế

## Best Practices khi sử dụng

### 1. Chọn filters phù hợp với mục tiêu

**Day Trading / Short-term:**
```bash
--min-volume=500000  # Cần thanh khoản cao
--min-market-cap=5   # Blue-chips ổn định
```

**Long-term Value Investing:**
```bash
--min-volume=100000  # Thanh khoản vừa phải
--min-market-cap=1   # Cho phép mid-caps
```

**Growth Investing:**
```bash
--strategy=growth
--min-volume=200000  # Thanh khoản tốt
```

### 2. Kết hợp với Backtest

**Quan trọng:** Luôn backtest các stocks được screening trước khi trade:

```bash
# 1. Screen stocks
python scripts/screen_stocks.py strategy --strategy=value --export=screened.csv

# 2. Backtest từng stock
python scripts/run_backtest.py --tickers=VHC,PVT,VHC --start-date=2023-01-01

# 3. So sánh performance
python scripts/run_backtest.py --compare
```

### 3. Monitoring và Re-screening

- **Re-screen hàng tuần:** Financial ratios có thể thay đổi
- **Monitor volume:** Đảm bảo liquidity vẫn đủ
- **Check fundamentals:** Xác nhận growth rate bền vững

## Hạn chế hiện tại

1. **Market Cap Data thiếu**
   - Nhiều stocks không có market_cap trong database
   - Workaround: Filter là optional `(market_cap >= X OR market_cap IS NULL)`

2. **Volume có thể thay đổi**
   - Average 30-day volume có thể không đại diện cho long-term
   - Cân nhắc tăng lookback period lên 60-90 days

3. **Growth rate không phản ánh quality**
   - Cần thêm factors: cash flow, debt sustainability
   - Future enhancement: Composite quality score

## Roadmap cải tiến tiếp theo

### Phase 1 (Completed ✅)
- [x] Thêm liquidity filter
- [x] Thêm growth sustainability checks
- [x] Cập nhật CLI parameters

### Phase 2 (Future)
- [ ] Thêm composite quality score ranking
- [ ] Walk-forward testing với point-in-time data
- [ ] Sector/industry diversification filters
- [ ] Backfill market cap data from external sources
- [ ] Add price stability metrics (volatility, beta)

### Phase 3 (Advanced)
- [ ] Machine learning-based ranking
- [ ] Multi-factor portfolio optimization
- [ ] Risk-adjusted return metrics
- [ ] Correlation analysis between screened stocks

## Kết luận

Các cải tiến đã giải quyết được:
1. ✅ Loại bỏ stocks thanh khoản kém (value traps)
2. ✅ Lọc stocks có growth bất thường
3. ✅ Cải thiện quality của screened stocks
4. ✅ Tăng khả năng trade thực tế

**Kết quả:** Stocks được screening giờ đây có profile gần với blue-chips hơn, đồng thời vẫn giữ được tiềm năng value/growth.

**Next Steps:**
- Backtest các stocks mới để xác nhận performance
- Theo dõi performance thực tế trong 1-3 tháng
- Tinh chỉnh thresholds dựa trên kết quả

---

*Document này được tạo ngày 2025-11-27 sau khi phân tích và cải tiến stock screening system.*
