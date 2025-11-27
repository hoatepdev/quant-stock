# Tài liệu

Chào mừng đến với tài liệu Nền tảng Vietnam Quant!

## 📖 Mục lục

### Bắt đầu

#### Khởi động Nhanh & Cài đặt

- [Hướng dẫn Khởi động Nhanh](guides/QUICKSTART.md) - Bắt đầu trong 10 phút
- [Hướng dẫn Cài đặt Chi tiết](guides/SETUP.md) - Cài đặt và cấu hình toàn diện
- [Tích hợp VNStock](guides/VNSTOCK_INTEGRATION.md) - Thiết lập nguồn dữ liệu miễn phí (không cần API key)
- [Hướng dẫn Quant Trading](guides/HUONG_DAN_QUANT_TRADING.md) - Hướng dẫn đầy đủ quy trình giao dịch định lượng
- [Hướng dẫn Sàng lọc Cổ phiếu](STOCK_SCREENING_GUIDE.md) - Hướng dẫn toàn diện về sàng lọc cổ phiếu với nhiều chiến lược

### Tài liệu các Phase

#### Các Phase Triển khai

- [Phase 2 - Backtesting & Danh mục](phases/PHASE2.md) - Framework backtest, tối ưu danh mục, sự kiện doanh nghiệp
- [Phase 3 - ML & Phân tích](phases/PHASE3.md) - Machine learning, phân tích cảm xúc, dữ liệu real-time
- [Phase 4 - Hệ thống Giao dịch](phases/PHASE4.md) - Tích hợp broker, quản lý rủi ro, quản lý lệnh

### Backtesting & Giao dịch

- [Hướng dẫn Backtest Toàn diện](BACKTEST_COMPLETE_GUIDE.md) - Hướng dẫn backtest đầy đủ (khởi động + tham chiếu + nâng cao)
- [Nâng cấp Backtest](BACKTEST_UPGRADES.md) - Chi tiết kỹ thuật về thực thi thực tế & chỉ số rủi ro
- [Cải tiến Sàng lọc](SCREENING_IMPROVEMENTS.md) - Các cải tiến mới nhất của hệ thống sàng lọc

### Kiến trúc & Tổng quan

- [Tài liệu Kiến trúc](ARCHITECTURE.md) - Tổng quan kỹ thuật & chi tiết triển khai
- [README Chính](../README.md) - Giới thiệu nền tảng và tham chiếu nhanh

## 🗂️ Cấu trúc Tài liệu

```
docs/
├── README.md (file này)
├── guides/
│   ├── QUICKSTART.md                    # Hướng dẫn cài đặt 10 phút
│   ├── SETUP.md                         # Hướng dẫn cài đặt chi tiết
│   ├── VNSTOCK_INTEGRATION.md           # Hướng dẫn nguồn dữ liệu VNStock
│   └── HUONG_DAN_QUANT_TRADING.md      # Hướng dẫn quant trading đầy đủ
└── phases/
    ├── PHASE2.md              # Backtesting & tối ưu danh mục
    ├── PHASE3.md              # ML, sentiment, tính năng real-time
    └── PHASE4.md              # Hệ thống giao dịch & quản lý rủi ro
```

## 🚀 Bắt đầu từ đâu?

1. **Người dùng mới**: Bắt đầu với [Hướng dẫn Khởi động Nhanh](guides/QUICKSTART.md)
2. **Quant Trading**: Đọc [Hướng dẫn Quant Trading](guides/HUONG_DAN_QUANT_TRADING.md) để có quy trình đầy đủ
3. **Cài đặt Chi tiết**: Đọc [Hướng dẫn Cài đặt](guides/SETUP.md)
4. **Nguồn Dữ liệu**: Cấu hình [VNStock](guides/VNSTOCK_INTEGRATION.md)
5. **Backtesting**: Khám phá [Hướng dẫn Phase 2](phases/PHASE2.md)
6. **ML & AI**: Xem [Hướng dẫn Phase 3](phases/PHASE3.md)
7. **Giao dịch**: Học [Hướng dẫn Phase 4](phases/PHASE4.md)

## 📋 Liên kết Nhanh

### Tài liệu các Phase

- [Phase 2 - Backtesting & Danh mục](phases/PHASE2.md) ✅
- [Phase 3 - ML & Phân tích](phases/PHASE3.md) ✅
- [Phase 4 - Hệ thống Giao dịch](phases/PHASE4.md) ✅

### Tài liệu API

- Swagger UI tương tác: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔍 Tài liệu theo Tính năng

### Hạ tầng Dữ liệu

- [Khởi động Nhanh - Bước 5: Tải Dữ liệu Mẫu](guides/QUICKSTART.md#5-load-sample-data-optional---5-minutes)
- [Hướng dẫn Tích hợp VNStock](guides/VNSTOCK_INTEGRATION.md)

### Sàng lọc Cổ phiếu

- [Hướng dẫn Sàng lọc Cổ phiếu](STOCK_SCREENING_GUIDE.md) - Tài liệu sàng lọc đầy đủ
- [Chiến lược Có sẵn](STOCK_SCREENING_GUIDE.md#2-sàng-lọc-theo-chiến-lược-có-sẵn) - Value, Growth, Quality, Momentum, Dividend
- [Sàng lọc Tùy chỉnh](STOCK_SCREENING_GUIDE.md#3-custom-screening-sàng-lọc-tùy-chỉnh) - Xây dựng bộ lọc riêng

### Backtesting

- [Hướng dẫn Backtest Toàn diện](BACKTEST_COMPLETE_GUIDE.md) - Hướng dẫn đầy đủ với khởi động và tính năng nâng cao
- [Phase 2 - Framework Backtesting](phases/PHASE2.md#3-backtesting-framework)
- [Chiến lược Có sẵn](phases/PHASE2.md#built-in-strategies)

### Tối ưu Danh mục

- [Phase 2 - Tối ưu Danh mục](phases/PHASE2.md#4-portfolio-optimization)
- [Phương pháp Tối ưu](phases/PHASE2.md#optimization-methods)

### Machine Learning

- [Phase 3 - ML Predictor](phases/PHASE3.md#1-machine-learning-models-)
- [Huấn luyện & Đánh giá Mô hình](phases/PHASE3.md#example-usage)

### Phân tích Cảm xúc

- [Phase 3 - Phân tích Cảm xúc](phases/PHASE3.md#2-sentiment-analysis-)
- [Hỗ trợ Tiếng Việt](phases/PHASE3.md#2-sentiment-analysis)

### Dữ liệu Real-time

- [Phase 3 - Feed Real-time](phases/PHASE3.md#3-real-time-data-feed-)
- [Cảnh báo Giá](phases/PHASE3.md#example-usage)

### Hệ thống Giao dịch

- [Hướng dẫn Phase 4](phases/PHASE4.md) - Tài liệu chi tiết
- [Tích hợp Broker](phases/PHASE4.md#1-broker-integration-framework)
- [Quản lý Rủi ro](phases/PHASE4.md#2-risk-management-system)
- [Quản lý Lệnh](phases/PHASE4.md#3-order-management-system)
- [Theo dõi Vị thế](phases/PHASE4.md#4-position-tracking)

## 💡 Mẹo

- Sử dụng chức năng tìm kiếm trong editor để tìm chủ đề cụ thể
- Tất cả ví dụ code đã được kiểm tra và sẵn sàng sử dụng
- Xem [Tài liệu Kiến trúc](ARCHITECTURE.md) để biết chi tiết kỹ thuật
- Xem các demo script trong thư mục `scripts/` để có ví dụ hoạt động

## 🤝 Đóng góp Tài liệu

Khi thêm tài liệu:

1. Đặt hướng dẫn cài đặt/tutorial trong `guides/`
2. Đặt tài liệu theo phase trong `phases/`
3. Cập nhật README này với link mới
4. Giữ ví dụ ngắn gọn và có thể chạy được
5. Bao gồm link đến source code

---

**Cần trợ giúp?** Kiểm tra phần troubleshooting trong từng hướng dẫn hoặc xem lại [README chính](../README.md).
