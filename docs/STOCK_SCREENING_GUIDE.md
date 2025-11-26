# Stock Screening Guide

Hướng dẫn sử dụng công cụ sàng lọc cổ phiếu (Stock Screening) cho Vietnam Quant Platform.

## Tổng quan

Script `screen_stocks.py` cung cấp công cụ mạnh mẽ để sàng lọc cổ phiếu dựa trên nhiều tiêu chí khác nhau, bao gồm:

- **Predefined Strategies**: Các chiến lược đầu tư định sẵn (Value, Growth, Quality, Momentum, Dividend)
- **Custom Screening**: Tùy chỉnh tiêu chí lọc theo ý muốn
- **Stock Analysis**: Phân tích chi tiết từng cổ phiếu
- **Database Statistics**: Thống kê dữ liệu trong hệ thống

## Cài đặt

Đảm bảo bạn đã cài đặt tất cả dependencies:

```bash
pip install -r requirements.txt
```

Và đã có dữ liệu trong database:

```bash
make init-db
make load-stocks
make backfill-data
```

## Các lệnh cơ bản

### 1. Xem thống kê database

Kiểm tra số lượng cổ phiếu và phạm vi dữ liệu:

```bash
# Toàn bộ thị trường
python scripts/screen_stocks.py stats

# Hoặc sử dụng Makefile
make screen-stats

# Theo sàn cụ thể
python scripts/screen_stocks.py stats --exchange=HOSE
```

### 2. Sàng lọc theo chiến lược có sẵn

#### Value Strategy (Cổ phiếu giá trị)

Tìm cổ phiếu bị định giá thấp với fundamentals tốt:

```bash
# Sử dụng script trực tiếp
python scripts/screen_stocks.py strategy --strategy=value

# Hoặc sử dụng Makefile
make screen-value

# Với filter theo sàn
python scripts/screen_stocks.py strategy --strategy=value --exchange=HOSE --limit=10
```

**Tiêu chí Value Strategy:**
- P/E ratio < 15
- P/B ratio < 2
- Dividend yield > 3%
- ROE > 10%
- Current ratio > 1.5
- Debt/Equity < 1

#### Growth Strategy (Cổ phiếu tăng trưởng)

Tìm cổ phiếu có tăng trưởng cao:

```bash
make screen-growth

# Hoặc
python scripts/screen_stocks.py strategy --strategy=growth --limit=20
```

**Tiêu chí Growth Strategy:**
- Revenue growth YoY > 20%
- EPS growth YoY > 20%
- ROE > 15%
- Net margin > 10%

#### Quality Strategy (Cổ phiếu chất lượng cao)

Tìm cổ phiếu có chất lượng tài chính tốt:

```bash
make screen-quality

# Hoặc
python scripts/screen_stocks.py strategy --strategy=quality
```

**Tiêu chí Quality Strategy:**
- ROE > 15%
- ROA > 10%
- Net margin > 15%
- Debt/Equity < 0.5
- Current ratio > 2

#### Momentum Strategy (Cổ phiếu có động lượng)

Tìm cổ phiếu có xu hướng tăng mạnh:

```bash
make screen-momentum

# Hoặc
python scripts/screen_stocks.py strategy --strategy=momentum --exchange=HOSE
```

**Tiêu chí Momentum Strategy:**
- Strong price momentum (6 tháng)
- Tăng volume giao dịch
- So sánh returns

#### Dividend Strategy (Cổ phiếu cổ tức cao)

Tìm cổ phiếu có cổ tức tốt:

```bash
make screen-dividend

# Hoặc
python scripts/screen_stocks.py strategy --strategy=dividend
```

**Tiêu chí Dividend Strategy:**
- Dividend yield >= 4%
- P/E ratio > 0
- ROE > 10%
- Current ratio > 1.5

#### Chạy tất cả các chiến lược

```bash
make screen-all

# Hoặc
python scripts/screen_stocks.py strategy --strategy=all --limit=10
```

### 3. Custom Screening (Sàng lọc tùy chỉnh)

Tạo bộ lọc riêng theo nhu cầu:

#### Ví dụ 1: Tìm cổ phiếu undervalued với ROE cao

```bash
python scripts/screen_stocks.py custom \
  --max-pe=10 \
  --min-roe=15 \
  --max-debt-to-equity=0.8 \
  --exchange=HOSE \
  --sort-by=roe \
  --descending
```

#### Ví dụ 2: Tìm cổ phiếu tăng trưởng mạnh với balance sheet tốt

```bash
python scripts/screen_stocks.py custom \
  --min-revenue-growth=20 \
  --min-eps-growth=20 \
  --max-debt-to-equity=0.5 \
  --min-current-ratio=2 \
  --sort-by=revenue_growth_yoy
```

#### Ví dụ 3: Tìm cổ phiếu dividend cao với P/E thấp

```bash
python scripts/screen_stocks.py custom \
  --min-dividend-yield=5 \
  --max-pe=15 \
  --min-current-ratio=1.5 \
  --sort-by=dividend_yield \
  --limit=30
```

#### Ví dụ 4: Tìm cổ phiếu có vốn hóa lớn với fundamentals tốt

```bash
python scripts/screen_stocks.py custom \
  --min-market-cap=10 \
  --max-pe=15 \
  --min-pb=0.5 \
  --max-pb=2 \
  --min-roe=15 \
  --max-debt-to-equity=1 \
  --exchange=HOSE \
  --sort-by=market_cap \
  --limit=20
```

#### Các tham số available cho custom screening:

**Valuation Ratios:**
- `--min-pe`: P/E ratio tối thiểu
- `--max-pe`: P/E ratio tối đa
- `--min-pb`: P/B ratio tối thiểu
- `--max-pb`: P/B ratio tối đa

**Profitability:**
- `--min-roe`: ROE tối thiểu (%)
- `--min-roa`: ROA tối thiểu (%)

**Financial Health:**
- `--max-debt-to-equity`: Debt/Equity tối đa
- `--min-current-ratio`: Current ratio tối thiểu

**Growth:**
- `--min-revenue-growth`: Tăng trưởng doanh thu YoY tối thiểu (%)
- `--min-eps-growth`: Tăng trưởng EPS YoY tối thiểu (%)

**Dividend:**
- `--min-dividend-yield`: Dividend yield tối thiểu (%)

**Other Filters:**
- `--exchange`: Lọc theo sàn (HOSE, HNX, UPCOM)
- `--min-market-cap`: Vốn hóa tối thiểu (tỷ VND)
- `--limit`: Số lượng kết quả tối đa
- `--sort-by`: Sắp xếp theo chỉ số
- `--ascending/--descending`: Thứ tự sắp xếp

### 4. Phân tích cổ phiếu cụ thể

Xem thông tin chi tiết của một cổ phiếu:

```bash
# Sử dụng Makefile
make screen-analyze TICKER=VNM

# Hoặc script trực tiếp
python scripts/screen_stocks.py analyze --ticker=VNM
python scripts/screen_stocks.py analyze --ticker=HPG
```

Kết quả sẽ hiển thị:
- Thông tin cơ bản (tên, sàn, ngành, vốn hóa)
- Giá gần nhất (OHLCV)
- Financial ratios (P/E, P/B, ROE, ROA, etc.)
- Growth metrics
- Financial health indicators

### 5. Export kết quả ra CSV

Tất cả các lệnh screening đều hỗ trợ export ra file CSV:

```bash
# Export strategy results
python scripts/screen_stocks.py strategy --strategy=value --export=value_stocks.csv

# Export custom screening results
python scripts/screen_stocks.py custom \
  --max-pe=10 \
  --min-roe=15 \
  --export=undervalued_stocks.csv

# Export all strategies
python scripts/screen_stocks.py strategy --strategy=all --export=all_strategies.csv
```

## Workflow đề xuất

### Workflow 1: Tìm kiếm cổ phiếu đầu tư dài hạn

```bash
# Bước 1: Check database stats
make screen-stats

# Bước 2: Chạy value strategy
make screen-value

# Bước 3: Chạy quality strategy
make screen-quality

# Bước 4: Phân tích chi tiết các cổ phiếu quan tâm
make screen-analyze TICKER=VNM
make screen-analyze TICKER=HPG
```

### Workflow 2: Tìm kiếm cổ phiếu tăng trưởng

```bash
# Bước 1: Chạy growth strategy
make screen-growth

# Bước 2: Custom screening với tiêu chí cụ thể hơn
python scripts/screen_stocks.py custom \
  --min-revenue-growth=30 \
  --min-eps-growth=25 \
  --max-debt-to-equity=0.5 \
  --min-roe=20 \
  --export=high_growth_stocks.csv

# Bước 3: Analyze top picks
make screen-analyze TICKER=<TICKER>
```

### Workflow 3: Tìm kiếm cổ phiếu cổ tức

```bash
# Bước 1: Dividend strategy
make screen-dividend

# Bước 2: Lọc thêm với financial health tốt
python scripts/screen_stocks.py custom \
  --min-dividend-yield=6 \
  --max-pe=12 \
  --min-current-ratio=2 \
  --max-debt-to-equity=0.8 \
  --exchange=HOSE \
  --export=dividend_stocks.csv
```

## Tips & Best Practices

1. **Kiểm tra data coverage trước khi screen:**
   ```bash
   make screen-stats
   ```

2. **Kết hợp nhiều strategies:** Chạy nhiều strategies khác nhau để tìm cổ phiếu xuất hiện trong nhiều danh sách

3. **Sử dụng exchange filter:** Nếu chỉ quan tâm đến sàn HOSE (cổ phiếu lớn):
   ```bash
   --exchange=HOSE
   ```

4. **Export và phân tích với Excel/Python:** Export kết quả ra CSV để phân tích sâu hơn

5. **Kết hợp technical analysis:** Sau khi có danh sách từ fundamental screening, kết hợp thêm phân tích kỹ thuật

6. **Regular screening:** Chạy screening định kỳ (weekly/monthly) để cập nhật danh sách

7. **Backtest strategies:** Test lại các strategies với dữ liệu lịch sử trước khi áp dụng

## Troubleshooting

### Lỗi "No financial data available"

```bash
# Solution: Cần có dữ liệu financial ratios
# Hiện tại hệ thống chỉ có price data
# Cần implement tính toán financial ratios từ financial statements
```

### Không có kết quả nào

- Thử nới lỏng tiêu chí (giảm min values, tăng max values)
- Check data coverage với `make screen-stats`
- Thử lại với exchange khác

### Script chạy chậm

- Giảm `--limit`
- Lọc theo exchange cụ thể
- Đảm bảo database có indexes

## Advanced Usage

### Chaining với jq (JSON processing)

```bash
# Export và process với jq
python scripts/screen_stocks.py custom \
  --max-pe=10 \
  --min-roe=15 \
  --export=stocks.csv

# Process CSV với pandas
python -c "
import pandas as pd
df = pd.read_csv('stocks.csv')
print(df.describe())
print(df[df['roe'] > 20])
"
```

### Automation với cron

```bash
# Chạy screening tự động hàng ngày
0 18 * * 1-5 cd /path/to/vnquant && make screen-all > /tmp/screening_$(date +\%Y\%m\%d).log
```

### Integration với Slack/Discord

```bash
# Send results to Slack
python scripts/screen_stocks.py strategy --strategy=value --export=value.csv
# Then use slack API to send the file
```

## Next Steps

1. Implement financial ratio calculation from financial statements
2. Add more technical indicators to screening
3. Create combination strategies (Value + Momentum)
4. Add backtesting capability
5. Create web interface for easier screening
6. Add alerts for new stocks matching criteria

## Tham khảo

- [Quantitative Stock Screening](https://www.investopedia.com/terms/s/stockscreener.asp)
- [Value Investing](https://www.investopedia.com/terms/v/valueinvesting.asp)
- [Growth Investing](https://www.investopedia.com/terms/g/growthinvesting.asp)
- [Momentum Investing](https://www.investopedia.com/terms/m/momentum_investing.asp)
