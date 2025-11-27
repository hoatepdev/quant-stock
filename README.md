# Nền tảng Phân tích Định lượng Thị trường Chứng khoán Việt Nam

Nền tảng nghiên cứu đầu tư và giao dịch định lượng sẵn sàng cho production, được thiết kế đặc biệt cho thị trường chứng khoán Việt Nam. Phân tích ~1,800 cổ phiếu trên các sàn HOSE, HNX và UPCoM sử dụng nhiều phương pháp đầu tư khác nhau.

## 🚀 Bắt đầu nhanh

Chỉ cần 10 phút để bắt đầu! Xem [Hướng dẫn Khởi động Nhanh](docs/guides/QUICKSTART.md)

```bash
# 1. Cấu hình môi trường
cp .env.example .env
# Không cần API key! Sử dụng vnstock (miễn phí) mặc định
# Tùy chọn: nano .env để cấu hình mật khẩu database

# 2. Khởi động các dịch vụ
make docker-up

# 3. Khởi tạo database
make init-db

# 4. Truy cập API
open http://localhost:8000/docs
```

## ✨ Tính năng

- **🆓 Nguồn dữ liệu MIỄN PHÍ**: Sử dụng vnstock (không cần API key!)
- **📊 Phủ sóng toàn diện**: 1,800+ cổ phiếu Việt Nam (HOSE, HNX, UPCoM)
- **📈 50+ Chỉ số đầu tư**: Chỉ số cơ bản, kỹ thuật và động lượng
- **🔍 Sàng lọc nâng cao**: Sàng lọc cổ phiếu đa chỉ số với bộ lọc linh hoạt
- **💰 Sự kiện doanh nghiệp**: Giá điều chỉnh sẵn (không cần điều chỉnh thủ công)
- **📅 Dữ liệu lịch sử**: Dữ liệu giá và tài chính từ năm 2020
- **⚡ Hiệu suất cao**: Tối ưu hóa TimescaleDB cho dữ liệu chuỗi thời gian
- **🐳 Sẵn sàng Production**: Triển khai Docker với PostgreSQL + Redis

## 🛠️ Công nghệ sử dụng

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0
- **Database**: PostgreSQL 14 + TimescaleDB
- **Cache**: Redis
- **Nguồn dữ liệu**: vnstock (mặc định, miễn phí, không cần API key) hoặc SSI iBoard API
- **Xử lý dữ liệu**: pandas, numpy, pandas-ta
- **Triển khai**: Docker, Docker Compose

## 📈 Các chỉ số đầu tư

### Chỉ số cơ bản (20+)
- Định giá: P/E, P/B, P/S, EV/EBITDA, Tỷ suất cổ tức
- Khả năng sinh lời: ROE, ROA, ROI, Biên lợi nhuận (Gộp, Hoạt động, Thuần)
- Đòn bẩy: Nợ/Vốn chủ, Nợ/Tài sản, Khả năng thanh toán lãi vay
- Thanh khoản: Tỷ số thanh toán hiện hành, Tỷ số thanh toán nhanh, Tỷ số tiền mặt
- Hiệu quả: Vòng quay tài sản, Vòng quay hàng tồn kho
- Tăng trưởng: Tăng trưởng doanh thu, Tăng trưởng EPS (YoY, QoQ)

### Chỉ số kỹ thuật (15+)
- Xu hướng: SMA, EMA, MACD, ADX
- Động lượng: RSI, Stochastic, Williams %R
- Biến động: Bollinger Bands, ATR
- Khối lượng: OBV, MFI, VWAP, Tỷ lệ khối lượng MA
- Hành động giá: Khoảng cách từ đỉnh/đáy 52 tuần

### Động lượng (10+)
- Lợi nhuận: 1 tuần, 1 tháng, 3 tháng, 6 tháng, 12 tháng
- Sức mạnh tương đối so với VN-Index
- Động lượng điều chỉnh rủi ro
- Gia tốc giá

## 🌐 Ví dụ API

### Sàng lọc cổ phiếu
```bash
curl -X POST "http://localhost:8000/api/v1/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "pe_ratio": {"min": 5, "max": 15},
      "roe": {"min": 15},
      "momentum_6m": {"min": 10}
    },
    "exchanges": ["HOSE"],
    "sort_by": "roe",
    "limit": 20
  }'
```

### Lấy chỉ số cổ phiếu
```bash
curl "http://localhost:8000/api/v1/factors/VNM"
```

### Danh sách mã cổ phiếu
```bash
curl "http://localhost:8000/api/v1/tickers?exchange=HOSE"
```

## 📁 Cấu trúc dự án

```
vnquant/
├── src/
│   ├── api/              # Ứng dụng FastAPI
│   ├── core/             # Logic nghiệp vụ
│   │   ├── factors/      # Tính toán chỉ số
│   │   ├── data_ingestion/ # Client dữ liệu
│   │   └── corporate_actions/
│   ├── database/         # Model SQLAlchemy
│   ├── utils/            # Tiện ích
│   └── tests/            # Bộ test
├── docker/               # Cấu hình Docker
├── scripts/              # Scripts vận hành
├── config/               # Cấu hình
└── docs/                 # Tài liệu
```

## 🔧 Phát triển

```bash
# Cài đặt dependencies
make install-dev

# Chạy tests
make run-tests

# Format code
make format

# Lint code
make lint
```

## 🇻🇳 Đặc thù thị trường Việt Nam

- **Biên độ ±7% hàng ngày**: Xử lý các tình huống giá trần/sàn
- **Thanh toán T+2**: Theo dõi chu kỳ thanh toán
- **Room ngoại**: Theo dõi giới hạn sở hữu nước ngoài
- **Ngày nghỉ lễ**: Tích hợp lịch Việt Nam
- **Ba sàn giao dịch**: Hỗ trợ HOSE, HNX, UPCoM

## 📊 Các bảng Database

1. **stock_info** - Thông tin metadata cổ phiếu
2. **daily_price** - Dữ liệu OHLCV (TimescaleDB hypertable)
3. **financial_statement** - Báo cáo tài chính quý/năm
4. **financial_ratio** - Các chỉ số tài chính đã tính
5. **corporate_action** - Chia tách, cổ tức
6. **factor** - Các chỉ số đầu tư (TimescaleDB hypertable)
7. **market_index** - Dữ liệu VN-Index, HNX-Index
8. **data_quality_log** - Log kiểm tra chất lượng dữ liệu

## 🎯 Trạng thái dự án

### ✅ Đã hoàn thành tất cả các Phase!

- **Phase 1 (MVP)** ✅ - Hạ tầng cốt lõi, chỉ số, sàng lọc
- **Phase 2** ✅ - Backtest, tối ưu danh mục, sự kiện doanh nghiệp
- **Phase 3** ✅ - Mô hình ML, phân tích cảm xúc, dữ liệu real-time
- **Phase 4** ✅ - Tích hợp giao dịch, quản lý rủi ro, quản lý lệnh

Xem [Tài liệu các Phase](docs/phases/) để biết chi tiết.

## �� Tài liệu

### Khởi động & Cài đặt
- [Hướng dẫn Khởi động Nhanh](docs/guides/QUICKSTART.md) - Bắt đầu trong 10 phút
- [Hướng dẫn Cài đặt Chi tiết](docs/guides/SETUP.md) - Cài đặt toàn diện
- [Tích hợp VNStock](docs/guides/VNSTOCK_INTEGRATION.md) - Thiết lập nguồn dữ liệu miễn phí
- [Hướng dẫn Quant Trading](docs/guides/HUONG_DAN_QUANT_TRADING.md) - Quy trình giao dịch hoàn chỉnh

### Backtest & Giao dịch
- [Hướng dẫn Backtest Toàn diện](docs/BACKTEST_COMPLETE_GUIDE.md) - Hướng dẫn backtest đầy đủ (khởi động + tham chiếu + tính năng nâng cao)
- [Nâng cấp Backtest](docs/BACKTEST_UPGRADES.md) - Chi tiết kỹ thuật về thực thi thực tế & chỉ số rủi ro

### Tài liệu các Phase
- [Hướng dẫn Phase 2](docs/phases/PHASE2.md) - Backtest & tối ưu danh mục
- [Hướng dẫn Phase 3](docs/phases/PHASE3.md) - ML & phân tích cảm xúc
- [Hướng dẫn Phase 4](docs/phases/PHASE4.md) - Hệ thống giao dịch & quản lý rủi ro

### Sàng lọc Cổ phiếu
- [Hướng dẫn Sàng lọc Cổ phiếu](docs/STOCK_SCREENING_GUIDE.md) - Tài liệu sàng lọc toàn diện
- [Cải tiến Sàng lọc](docs/SCREENING_IMPROVEMENTS.md) - Các cải tiến mới nhất cho hệ thống sàng lọc

### Kiến trúc & Kỹ thuật
- [Tài liệu Kiến trúc](docs/ARCHITECTURE.md) - Tổng quan kỹ thuật & chi tiết triển khai
- [Mục lục Tài liệu](docs/README.md) - Cấu trúc tài liệu hoàn chỉnh

### Tài liệu API
- Tài liệu API tương tác: http://localhost:8000/docs (sau khi khởi động)

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Thực hiện thay đổi kèm tests
4. Chạy `make format && make lint && make run-tests`
5. Gửi pull request

## 📝 Giấy phép

[Your License Here]

## 🙏 Lời cảm ơn

- SSI cung cấp API dữ liệu thị trường
- TimescaleDB cho tối ưu hóa chuỗi thời gian
- FastAPI cho web framework xuất sắc
- Cộng đồng đầu tư Việt Nam

## 📧 Hỗ trợ

- Tài liệu: Xem thư mục [docs/](docs/)
- Issues: GitHub Issues
- Email: your.email@example.com

---

**Xây dựng với ❤️ dành cho nhà đầu tư định lượng Việt Nam**

**Phiên bản 0.1.0 | Sẵn sàng Production**
