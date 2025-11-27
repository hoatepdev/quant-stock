# Hướng dẫn Khởi động Nhanh

Khởi chạy Nền tảng Vietnam Quant chỉ trong 10 phút!

## Danh sách Kiểm tra Yêu cầu

- [x] Đã cài đặt Docker và Docker Compose
- [x] Có sẵn 4GB+ RAM
- [x] Có sẵn 20GB+ dung lượng đĩa
- [ ] Thông tin đăng nhập SSI API (TÙY CHỌN - chỉ cần nếu dùng SSI làm nguồn dữ liệu)

## Cài đặt 5 Bước

### 1. Cấu hình Môi trường (2 phút)

```bash
# Sao chép template môi trường
cp .env.example .env

# Chỉnh sửa với thông tin của bạn
nano .env
```

**Cài đặt tối thiểu cần thiết:**

```env
# Database (có thể giữ mặc định cho development)
DB_PASSWORD=postgres

# Nguồn dữ liệu (vnstock là mặc định và MIỄN PHÍ - không cần API key!)
DATA_SOURCE=vnstock

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO

# Tùy chọn: Chỉ cần nếu muốn sử dụng SSI thay vì vnstock
# SSI_API_KEY=your_actual_key_here
# SSI_SECRET_KEY=your_actual_secret_here
```

**Lưu ý:** Nền tảng hiện sử dụng **vnstock** làm nguồn dữ liệu mặc định, với các ưu điểm:
- ✅ **MIỄN PHÍ** - Không cần đăng ký API hay key
- ✅ **NHANH** - Hiệu suất tốt hơn SSI
- ✅ **ỔN ĐỊNH** - Điều chỉnh sự kiện doanh nghiệp tự động
- ✅ **TOÀN DIỆN** - Bao gồm các sàn HOSE, HNX và UPCoM

Bạn có thể tùy chọn chuyển sang SSI bằng cách đặt `DATA_SOURCE=ssi` trong `.env`

### 2. Khởi động Dịch vụ (2 phút)

```bash
# Build và khởi động tất cả dịch vụ
make docker-up

# Đợi các dịch vụ sẵn sàng (~30 giây)
# Kiểm tra trạng thái
make docker-ps
```

### 3. Khởi tạo Database (1 phút)

```bash
# Tạo bảng và indexes
make init-db
```

### 4. Xác minh Cài đặt (1 phút)

```bash
# Kiểm tra API health
curl http://localhost:8000/api/v1/health

# Truy cập tài liệu API
open http://localhost:8000/docs
```

### 5. Tải Dữ liệu Mẫu (Tùy chọn - 5 phút)

```bash
# Test nhanh với một vài cổ phiếu
python scripts/backfill_data.py --tickers VNM,HPG,VIC --start-date 2024-01-01
```

## Kiểm tra Cài đặt

### Test 1: Lấy danh sách Mã cổ phiếu

```bash
curl http://localhost:8000/api/v1/tickers | jq
```

### Test 2: Sàng lọc Cổ phiếu

```bash
curl -X POST http://localhost:8000/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "roe": {"min": 15}
    },
    "limit": 5
  }' | jq
```

### Test 3: Lấy Chỉ số Cổ phiếu

```bash
curl http://localhost:8000/api/v1/factors/VNM | jq
```

## Các vấn đề Thường gặp & Giải pháp

### Vấn đề: Docker containers không khởi động

**Giải pháp:**

```bash
# Kiểm tra Docker đang chạy
docker ps

# Nếu không, khởi động Docker Desktop
# Sau đó thử lại
make docker-down
make docker-up
```

### Vấn đề: Lỗi "Connection refused"

**Giải pháp:**

```bash
# Đợi dịch vụ khởi động hoàn toàn (có thể mất 30-60 giây)
sleep 30

# Kiểm tra logs
make docker-logs
```

### Vấn đề: API không trả về dữ liệu

**Giải pháp:**

```bash
# Đảm bảo database đã được khởi tạo
make init-db

# Tải một số dữ liệu
python scripts/backfill_data.py --tickers VNM --start-date 2024-01-01
```

### Vấn đề: Lỗi nguồn dữ liệu

**Giải pháp:**

**Nếu dùng vnstock (mặc định):**
- Không cần API key
- Kiểm tra kết nối internet
- Xác minh vnstock đã cài đặt: `pip install vnstock==0.3.2`

**Nếu dùng SSI:**
1. Xác minh thông tin đăng nhập API đúng trong `.env`
2. Kiểm tra bạn đã bật API access trên SSI iBoard
3. Đảm bảo không vượt quá rate limit (100 requests/phút)
4. Đặt `DATA_SOURCE=ssi` trong `.env`

## Bước tiếp theo

Khi mọi thứ đã chạy:

1. **Tải thêm Dữ liệu** - Chạy backfill đầy đủ:

   ```bash
   make backfill-data
   ```

   ⚠️ Mất khoảng 1-2 giờ cho tất cả cổ phiếu

2. **Khám phá API** - Truy cập http://localhost:8000/docs

   - Thử các tiêu chí sàng lọc khác nhau
   - Lấy lịch sử chỉ số
   - Test lọc và sắp xếp

3. **Thiết lập Cập nhật Hàng ngày** - Thêm vào cron:

   ```bash
   0 18 * * 1-5 cd /path/to/vnquant && python scripts/run_daily_update.py
   ```

4. **Đọc Tài liệu Đầy đủ**:
   - [README.md](README.md) - Tổng quan tính năng
   - [docs/SETUP.md](docs/SETUP.md) - Hướng dẫn cài đặt chi tiết
   - [docs/API.md](docs/API.md) - Tài liệu API

## Quy trình Phát triển

### Chạy Tests

```bash
make run-tests
```

### Format Code

```bash
make format
```

### Xem Logs

```bash
# Tất cả dịch vụ
make docker-logs

# Dịch vụ cụ thể
docker logs vietnam_quant_api -f
```

### Dừng Dịch vụ

```bash
make docker-down
```

### Truy cập Database

```bash
# Dùng psql
docker exec -it vietnam_quant_db psql -U postgres -d vietnam_quant

# Hoặc dùng pgAdmin tại http://localhost:5050
# (nếu chạy với dev profile: docker-compose --profile dev up)
```

## Danh sách Kiểm tra Production

Trước khi triển khai production:

- [ ] Thay đổi tất cả mật khẩu mặc định trong `.env`
- [ ] Đặt `ENVIRONMENT=production`
- [ ] Đặt `DEBUG=false`
- [ ] Cấu hình HTTPS/SSL
- [ ] Thiết lập backup tự động
- [ ] Cấu hình monitoring
- [ ] Xem xét và điều chỉnh rate limits
- [ ] Thiết lập tổng hợp log
- [ ] Cấu hình firewall rules
- [ ] Test quy trình khôi phục thảm họa

## Nhận Trợ giúp

**Tài liệu:**

- README.md - Tổng quan và tính năng
- docs/SETUP.md - Hướng dẫn cài đặt chi tiết
- docs/API.md - Tham chiếu API
- docs/ARCHITECTURE.md - Kiến trúc hệ thống

**Hỗ trợ:**

- GitHub Issues: Báo cáo lỗi và yêu cầu tính năng
- Logs: Kiểm tra `logs/app.log` và `logs/error.log`
- Docker logs: `make docker-logs`

## Tham chiếu Nhanh

### Các lệnh Makefile

```bash
make help              # Hiển thị tất cả lệnh có sẵn
make docker-up         # Khởi động dịch vụ
make docker-down       # Dừng dịch vụ
make docker-logs       # Xem logs
make init-db           # Khởi tạo database
make backfill-data     # Tải dữ liệu lịch sử
make run-tests         # Chạy tests
make format            # Format code
make lint              # Chạy linters
make clean             # Dọn dẹp file tạm
```

### API Endpoints

- `GET /api/v1/health` - Kiểm tra health
- `GET /api/v1/tickers` - Danh sách mã CP
- `POST /api/v1/screen` - Sàng lọc cổ phiếu
- `GET /api/v1/factors/{ticker}` - Lấy chỉ số cổ phiếu
- `GET /api/v1/factors/available` - Danh sách chỉ số có sẵn

### Ports Mặc định

- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- pgAdmin: http://localhost:5050 (dev profile)

---

**Hoàn tất!** 🚀

Bắt đầu khám phá cổ phiếu Việt Nam với phân tích định lượng!
