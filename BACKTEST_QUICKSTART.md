# ⚡ Backtest Quick Start

Hướng dẫn nhanh để bắt đầu backtest trong 5 phút.

## 🚀 Bắt Đầu Nhanh

### 1. Đảm bảo có dữ liệu

```bash
# Khởi động hệ thống
make docker-up

# Khởi tạo database
make init-db

# Nạp dữ liệu cho một vài mã để test
python scripts/backfill_data.py --tickers VCB,VNM,HPG --start-date 2023-01-01
```

### 2. Chạy Backtest Đơn Giản

```bash
# Backtest chiến lược Moving Average
make backtest-ma
```

Hoặc:

```bash
python scripts/run_backtest.py --strategy ma --tickers VCB,VNM,HPG
```

### 3. So Sánh Các Chiến Lược

```bash
# So sánh tất cả chiến lược
make backtest-compare
```

### 4. Xem Kết Quả

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

### Tùy Chỉnh Thời Gian

```bash
# Backtest trong năm 2023
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --start-date 2023-01-01 \
  --end-date 2023-12-31
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

## 📖 Ví Dụ Đầy Đủ

### Ví dụ 1: Backtest MA Strategy

```bash
python scripts/run_backtest.py \
  --strategy ma \
  --tickers VCB,VNM,HPG \
  --short-window 20 \
  --long-window 50 \
  --capital 100000000 \
  --commission 0.0015 \
  --plot \
  --save
```

**Kết quả**:
```
======================================================================
KẾT QUẢ BACKTEST - MA
======================================================================

Thời gian: 2024-01-26 → 2025-01-26
Mã CP: VCB, VNM, HPG

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
```

### Ví dụ 2: So Sánh Chiến Lược

```bash
python scripts/run_backtest.py \
  --compare \
  --tickers VCB,VNM,HPG,VIC,MSN \
  --plot \
  --save
```

**Kết quả**:
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

## 🛠️ Tạo Chiến Lược Riêng

Xem ví dụ trong file `examples/custom_strategy_example.py`:

```bash
# Chạy ví dụ chiến lược tùy chỉnh
make backtest-custom
```

Hoặc:

```bash
python examples/custom_strategy_example.py
```

File này có sẵn các ví dụ:
- RSI Strategy
- MACD Strategy
- Breakout Strategy
- Combo Strategy
- Trailing Stop Strategy

---

## 📚 Tài Liệu Chi Tiết

Để tìm hiểu sâu hơn, xem:

- **[docs/BACKTEST_GUIDE.md](docs/BACKTEST_GUIDE.md)** - Hướng dẫn đầy đủ về backtest
- **[docs/guides/HUONG_DAN_QUANT_TRADING.md](docs/guides/HUONG_DAN_QUANT_TRADING.md)** - Workflow quant trading hoàn chỉnh
- **[examples/custom_strategy_example.py](examples/custom_strategy_example.py)** - Ví dụ chiến lược tùy chỉnh

---

## ❓ Câu Hỏi Thường Gặp

### Q: Làm sao xem tất cả tùy chọn?

```bash
python scripts/run_backtest.py --help
```

hoặc:

```bash
make backtest-help
```

### Q: Kết quả được lưu ở đâu?

Trong thư mục `backtest_results/`:
- JSON files: Kết quả chi tiết
- CSV files: Danh sách giao dịch và equity curve
- PNG files: Biểu đồ

### Q: Làm sao test với nhiều tham số?

Xem phần "Grid Search" trong [docs/BACKTEST_GUIDE.md](docs/BACKTEST_GUIDE.md).

### Q: Có thể backtest với dữ liệu của mình không?

Có! Chỉ cần đảm bảo dữ liệu đã được nạp vào database qua `scripts/backfill_data.py`.

---

## 🎓 Bước Tiếp Theo

Sau khi backtest xong:

1. **Tối ưu tham số**: Thử nhiều bộ tham số khác nhau
2. **Walk-forward test**: Test trên nhiều khoảng thời gian
3. **Paper trading**: Test với tiền giả (xem [docs/guides/HUONG_DAN_QUANT_TRADING.md](docs/guides/HUONG_DAN_QUANT_TRADING.md#4-paper-trading---giao-dịch-mô-phỏng))
4. **Live trading**: Giao dịch thực tế với risk management

---

**Chúc bạn backtest thành công!** 🚀

Có câu hỏi? Tạo issue tại GitHub hoặc xem tài liệu chi tiết.
