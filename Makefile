.PHONY: help install install-dev init-db load-stocks backfill-data run-api run-tests lint format docker-build docker-up docker-down clean

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose -f docker/docker-compose.yml

help:
	@echo "Nền tảng Vietnam Quant - Các lệnh có sẵn:"
	@echo ""
	@echo "Phát triển:"
	@echo "  make install          Cài đặt dependencies production"
	@echo "  make install-dev      Cài đặt dependencies development"
	@echo "  make run-api          Chạy FastAPI server local"
	@echo "  make format           Format code với black và isort"
	@echo "  make lint             Chạy linters (flake8, mypy, pylint)"
	@echo "  make run-tests        Chạy tất cả tests với coverage"
	@echo ""
	@echo "Database:"
	@echo "  make init-db          Khởi tạo schema database"
	@echo "  make load-stocks      Tải danh sách cổ phiếu từ nguồn dữ liệu"
	@echo "  make backfill-data    Nạp dữ liệu lịch sử"
	@echo "  make calc-ratios      Tính chỉ số tài chính cho tất cả cổ phiếu"
	@echo ""
	@echo "Sàng lọc Cổ phiếu:"
	@echo "  make screen-value     Sàng lọc cổ phiếu giá trị"
	@echo "  make screen-growth    Sàng lọc cổ phiếu tăng trưởng"
	@echo "  make screen-quality   Sàng lọc cổ phiếu chất lượng"
	@echo "  make screen-all       Chạy tất cả chiến lược sàng lọc"
	@echo "  make screen-stats     Hiển thị thống kê database"
	@echo ""
	@echo "Backtesting:"
	@echo "  make backtest-ma            Backtest chiến lược Moving Average"
	@echo "  make backtest-momentum      Backtest chiến lược Momentum"
	@echo "  make backtest-compare       So sánh tất cả chiến lược"
	@echo "  make backtest-realistic     Chạy với thực thi thực tế (mặc định)"
	@echo "  make backtest-baseline      Chạy baseline (không slippage/sizing)"
	@echo "  make backtest-test-slippage So sánh realistic vs baseline"
	@echo "  make backtest-demo          Chạy backtest demo"
	@echo "  make backtest-custom        Chạy ví dụ chiến lược tùy chỉnh"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-up        Khởi động tất cả Docker services"
	@echo "  make docker-down      Dừng tất cả Docker services"
	@echo "  make docker-logs      Xem Docker logs"
	@echo ""
	@echo "Tiện ích:"
	@echo "  make clean            Dọn dẹp file tạm và caches"

install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

init-db:
	$(PYTHON) scripts/init_db.py

load-stocks:
	$(PYTHON) scripts/load_stock_list.py

backfill-data:
	$(PYTHON) scripts/backfill_data.py

calc-ratios:
	@echo "Đang tính chỉ số tài chính cho tất cả cổ phiếu (delay 2s để tránh rate limit)..."
	$(PYTHON) scripts/calculate_financial_ratios.py --delay=2.0

calc-ratios-test:
	@echo "Đang test với 10 cổ phiếu..."
	$(PYTHON) scripts/calculate_financial_ratios.py --limit=10 --delay=1.0

calc-ratios-exchange:
	@if [ -z "$(EXCHANGE)" ]; then \
		echo "Cách dùng: make calc-ratios-exchange EXCHANGE=HOSE"; \
		echo "Sàn hợp lệ: HOSE, HNX, UPCOM"; \
	else \
		echo "Đang tính chỉ số cho cổ phiếu $(EXCHANGE) (delay 2s)..."; \
		$(PYTHON) scripts/calculate_financial_ratios.py --exchange=$(EXCHANGE) --delay=2.0; \
	fi

screen-value:
	$(PYTHON) scripts/screen_stocks.py strategy --strategy=value

screen-growth:
	$(PYTHON) scripts/screen_stocks.py strategy --strategy=growth

screen-quality:
	$(PYTHON) scripts/screen_stocks.py strategy --strategy=quality

screen-momentum:
	$(PYTHON) scripts/screen_stocks.py strategy --strategy=momentum

screen-dividend:
	$(PYTHON) scripts/screen_stocks.py strategy --strategy=dividend

screen-all:
	$(PYTHON) scripts/screen_stocks.py strategy --strategy=all

screen-custom:
	@echo "Cách dùng: make screen-custom ARGS='--max-pe=15 --min-roe=15'"
	@echo "Ví dụ bộ lọc: --max-pe, --min-roe, --min-revenue-growth, --max-debt-to-equity"
	@echo "Xem: python scripts/screen_stocks.py custom --help"

screen-stats:
	$(PYTHON) scripts/screen_stocks.py stats

screen-analyze:
	@if [ -z "$(TICKER)" ]; then \
		echo "Cách dùng: make screen-analyze TICKER=VNM"; \
		echo "Ví dụ: make screen-analyze TICKER=HPG"; \
	else \
		$(PYTHON) scripts/screen_stocks.py analyze --ticker=$(TICKER); \
	fi

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-tests:
	pytest src/tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ --max-line-length=100 --exclude=__pycache__,*.pyc
	mypy src/ --ignore-missing-imports
	pylint src/ --max-line-length=100 --disable=C0111,R0903

format:
	black src/ scripts/ --line-length=100
	isort src/ scripts/ --profile=black

docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d
	@echo "Đang khởi động services..."
	@echo "API sẽ có sẵn tại http://localhost:8000"
	@echo "Tài liệu API tại http://localhost:8000/docs"
	@echo "pgAdmin tại http://localhost:5050 (nếu bật dev profile)"

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

docker-restart:
	$(DOCKER_COMPOSE) restart

docker-ps:
	$(DOCKER_COMPOSE) ps

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/
	@echo "Đã dọn dẹp file tạm và caches"

test-unit:
	pytest src/tests/unit/ -v

test-integration:
	pytest src/tests/integration/ -v

dev-setup: install-dev init-db
	@echo "Hoàn tất cài đặt môi trường development!"
	@echo "Chạy 'make docker-up' để khởi động services"
	@echo "Chạy 'make load-stocks' để tải danh sách cổ phiếu"
	@echo "Chạy 'make backfill-data' để tải dữ liệu lịch sử"

# Backtesting commands
backtest-ma:
	@echo "Đang chạy backtest Moving Average trên VCB, VNM, HPG..."
	$(PYTHON) scripts/run_backtest.py --strategy ma --tickers VCB,VNM,HPG --plot --save

backtest-momentum:
	@echo "Đang chạy backtest Momentum trên VCB, VNM, HPG, VIC, MSN..."
	$(PYTHON) scripts/run_backtest.py --strategy momentum --tickers VCB,VNM,HPG,VIC,MSN --plot --save

backtest-mean-reversion:
	@echo "Đang chạy backtest Mean Reversion trên VCB, VNM, HPG..."
	$(PYTHON) scripts/run_backtest.py --strategy mean_reversion --tickers VCB,VNM,HPG --plot --save

backtest-compare:
	@echo "Đang so sánh tất cả chiến lược trên VCB, VNM, HPG, VIC, MSN..."
	$(PYTHON) scripts/run_backtest.py --compare --tickers VCB,VNM,HPG,VIC,MSN --plot --save

backtest-demo:
	@echo "Đang chạy Phase 2 backtest demo..."
	$(PYTHON) scripts/phase2_demo.py

backtest-custom:
	@echo "Đang chạy ví dụ chiến lược tùy chỉnh..."
	$(PYTHON) examples/custom_strategy_example.py

backtest-realistic:
	@echo "Đang chạy backtest với thực thi thực tế (slippage + dynamic sizing)..."
	$(PYTHON) scripts/run_backtest.py --strategy buy_hold --tickers VHC,PVT --start-date 2024-01-01

backtest-baseline:
	@echo "Đang chạy baseline backtest (không slippage, không dynamic sizing)..."
	$(PYTHON) scripts/run_backtest.py --strategy buy_hold --tickers VHC,PVT --start-date 2024-01-01 --no-slippage --no-dynamic-sizing

backtest-test-slippage:
	@echo "Đang test tác động slippage..."
	$(PYTHON) test_slippage_comparison.py

backtest-help:
	@echo "Cách dùng lệnh Backtest:"
	@echo ""
	@echo "Lệnh nhanh:"
	@echo "  make backtest-ma              Chạy chiến lược MA trên các mã mặc định"
	@echo "  make backtest-momentum        Chạy chiến lược Momentum"
	@echo "  make backtest-compare         So sánh tất cả chiến lược"
	@echo ""
	@echo "Backtest tùy chỉnh:"
	@echo "  python scripts/run_backtest.py --strategy ma --tickers VCB,VNM"
	@echo "  python scripts/run_backtest.py --compare --tickers VCB,VNM,HPG,VIC"
	@echo ""
	@echo "Tùy chọn nâng cao:"
	@echo "  --start-date YYYY-MM-DD       Đặt ngày bắt đầu"
	@echo "  --end-date YYYY-MM-DD         Đặt ngày kết thúc"
	@echo "  --capital 200000000           Đặt vốn ban đầu"
	@echo "  --commission 0.002            Đặt tỷ lệ phí giao dịch"
	@echo "  --plot                        Tạo biểu đồ"
	@echo "  --save                        Lưu kết quả vào file"
	@echo ""
	@echo "Để xem đầy đủ trợ giúp:"
	@echo "  python scripts/run_backtest.py --help"
	@echo ""
	@echo "Tài liệu:"
	@echo "  docs/BACKTEST_COMPLETE_GUIDE.md  Hướng dẫn backtest đầy đủ (quickstart + tham chiếu + nâng cao)"
	@echo "  docs/BACKTEST_UPGRADES.md        Chi tiết kỹ thuật về thực thi thực tế"
	@echo "  examples/custom_strategy_example.py  Ví dụ chiến lược tùy chỉnh"
