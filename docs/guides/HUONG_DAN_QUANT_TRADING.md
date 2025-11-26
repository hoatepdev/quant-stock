# Hướng Dẫn Sử Dụng VNQuant Cho Quantitative Trading

Hướng dẫn chi tiết cách sử dụng nền tảng VNQuant để thực hiện quantitative trading trên thị trường chứng khoán Việt Nam.

## Mục Lục

1. [Thiết Lập Ban Đầu](#thiết-lập-ban-đầu)
2. [Workflow Trading Cơ Bản](#workflow-trading-cơ-bản)
3. [1. Stock Screening - Tìm Cổ Phiếu](#1-stock-screening---tìm-cổ-phiếu)
4. [2. Backtesting - Kiểm Thử Chiến Lược](#2-backtesting---kiểm-thử-chiến-lược)
5. [3. Portfolio Optimization - Tối Ưu Danh Mục](#3-portfolio-optimization---tối-ưu-danh-mục)
6. [4. Paper Trading - Giao Dịch Mô Phỏng](#4-paper-trading---giao-dịch-mô-phỏng)
7. [5. Live Trading - Giao Dịch Thực Tế](#5-live-trading---giao-dịch-thực-tế)
8. [Ví Dụ Hoàn Chỉnh](#ví-dụ-hoàn-chỉnh)

## Thiết Lập Ban Đầu

### Bước 1: Cài Đặt

```bash
# Clone hoặc vào thư mục dự án
cd vnquant

# Copy file cấu hình
cp .env.example .env

# Chỉnh sửa .env (tối thiểu cần set DB_PASSWORD)
nano .env
```

### Bước 2: Khởi Động Services

```bash
# Khởi động Docker containers
make docker-up

# Đợi 30-60 giây để services sẵn sàng
# Kiểm tra status
make docker-ps

# Khởi tạo database
make init-db
```

### Bước 3: Nạp Dữ Liệu

```bash
# Nạp dữ liệu cho một vài mã để test
python scripts/backfill_data.py --tickers VNM,HPG,VIC,VCB --start-date 2024-01-01

# Hoặc nạp toàn bộ (mất 1-2 giờ)
make backfill-data
```

## Workflow Trading Cơ Bản

Quy trình trading với VNQuant thường theo các bước sau:

```
1. Screening → Tìm cổ phiếu tiềm năng
2. Backtesting → Kiểm thử chiến lược trên dữ liệu lịch sử
3. Portfolio Optimization → Tối ưu tỷ trọng danh mục
4. Paper Trading → Test với tiền giả
5. Live Trading → Giao dịch thực tế với risk management
```

## 1. Stock Screening - Tìm Cổ Phiếu

### Sử Dụng API

```bash
# Tìm cổ phiếu có ROE > 15% và P/E < 15
curl -X POST "http://localhost:8000/api/v1/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "roe": {"min": 15},
      "pe_ratio": {"max": 15}
    },
    "exchanges": ["HOSE"],
    "sort_by": "roe",
    "limit": 20
  }'
```

### Sử Dụng Python

```python
from src.core.screening.advanced_strategies import (
    value_investing_strategy,
    momentum_strategy,
    growth_investing_strategy
)

# Chiến lược Value Investing
value_stocks = value_investing_strategy(
    min_pe=5,
    max_pe=15,
    min_roe=15,
    min_current_ratio=1.5
)

print(f"Tìm thấy {len(value_stocks)} cổ phiếu value:")
for stock in value_stocks[:10]:
    print(f"  {stock['ticker']}: P/E={stock['pe_ratio']:.1f}, ROE={stock['roe']:.1f}%")

# Chiến lược Momentum
momentum_stocks = momentum_strategy(
    min_momentum_6m=10,
    min_volume_ratio=1.5
)

print(f"\nTìm thấy {len(momentum_stocks)} cổ phiếu momentum:")
for stock in momentum_stocks[:10]:
    print(f"  {stock['ticker']}: Momentum 6M={stock['momentum_6m']:.1f}%")
```

### Lọc Nhiều Tiêu Chí

```python
from src.api.routes.screening import screen_stocks
from src.database.connection import get_sync_session

db = next(get_sync_session())

# Tìm cổ phiếu đáp ứng nhiều điều kiện
results = screen_stocks(
    filters={
        "pe_ratio": {"min": 5, "max": 15},
        "roe": {"min": 15},
        "current_ratio": {"min": 1.5},
        "momentum_6m": {"min": 10},
        "rsi": {"min": 30, "max": 70}  # Không quá mua/quá bán
    },
    exchanges=["HOSE"],
    sort_by="roe",
    limit=20
)

for stock in results:
    print(f"{stock['ticker']}: "
          f"P/E={stock['pe_ratio']:.1f}, "
          f"ROE={stock['roe']:.1f}%, "
          f"Momentum={stock['momentum_6m']:.1f}%")
```

## 2. Backtesting - Kiểm Thử Chiến Lược

### Backtest Chiến Lược Đơn Giản

```python
from src.core.backtesting.engine import BacktestEngine
from src.core.backtesting.strategies import simple_moving_average_strategy
from datetime import date, timedelta
from src.database.connection import get_sync_session

db = next(get_sync_session())

# Khởi tạo backtest engine
engine = BacktestEngine(db)

# Thiết lập tham số
start_date = date(2023, 1, 1)
end_date = date(2024, 12, 31)
initial_capital = 100_000_000  # 100 triệu VND
tickers = ["VCB", "VNM", "HPG", "VIC"]

# Chạy backtest với chiến lược MA Crossover
results = engine.run_backtest(
    strategy=simple_moving_average_strategy,
    tickers=tickers,
    start_date=start_date,
    end_date=end_date,
    initial_capital=initial_capital,
    strategy_params={
        "short_window": 20,
        "long_window": 50
    }
)

# Xem kết quả
print("=== KẾT QUẢ BACKTEST ===")
print(f"Tổng lợi nhuận: {results['total_return']:.2%}")
print(f"Lợi nhuận năm: {results['annualized_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")
print(f"Số giao dịch: {results['total_trades']}")
```

### Backtest Chiến Lược Momentum

```python
from src.core.backtesting.strategies import momentum_strategy

results = engine.run_backtest(
    strategy=momentum_strategy,
    tickers=tickers,
    start_date=start_date,
    end_date=end_date,
    initial_capital=initial_capital,
    strategy_params={
        "lookback_period": 90,  # 3 tháng
        "min_momentum": 10,     # Tối thiểu 10% tăng trưởng
        "hold_period": 30       # Giữ 30 ngày
    }
)
```

### Tạo Chiến Lược Tùy Chỉnh

```python
from typing import Dict, List
from datetime import date
from src.core.backtesting.engine import BacktestEngine, BacktestResult

def my_custom_strategy(
    prices: Dict[str, pd.DataFrame],
    signals: Dict[str, pd.DataFrame],
    params: Dict
) -> Dict[str, pd.DataFrame]:
    """
    Chiến lược tùy chỉnh của bạn.

    Ví dụ: Mua khi RSI < 30 và P/E < 15
    """
    positions = {}

    for ticker, df in prices.items():
        # Logic của bạn ở đây
        buy_signal = (df['rsi'] < 30) & (df['pe_ratio'] < 15)
        sell_signal = (df['rsi'] > 70)

        positions[ticker] = pd.DataFrame({
            'signal': 0,
            'quantity': 0
        })
        positions[ticker].loc[buy_signal, 'signal'] = 1
        positions[ticker].loc[sell_signal, 'signal'] = -1

    return positions

# Chạy backtest với chiến lược tùy chỉnh
results = engine.run_backtest(
    strategy=my_custom_strategy,
    tickers=["VCB", "VNM"],
    start_date=date(2023, 1, 1),
    end_date=date(2024, 12, 31),
    initial_capital=100_000_000,
    strategy_params={}
)
```

## 3. Portfolio Optimization - Tối Ưu Danh Mục

### Tối Ưu Danh Mục Cơ Bản

```python
from src.core.portfolio.optimizer import PortfolioOptimizer
from datetime import date, timedelta
from src.database.connection import get_sync_session

db = next(get_sync_session())
optimizer = PortfolioOptimizer(db)

# Danh sách cổ phiếu muốn tối ưu
tickers = ["VCB", "VNM", "HPG", "VIC", "VRE", "MSN", "MWG", "FPT"]

# Thời gian tính toán
end_date = date.today()
start_date = end_date - timedelta(days=365)

# Tối ưu theo Maximum Sharpe Ratio
optimal_weights = optimizer.optimize_max_sharpe(
    tickers=tickers,
    start_date=start_date,
    end_date=end_date,
    risk_free_rate=0.08  # 8% lãi suất không rủi ro
)

print("=== TỐI ƯU DANH MỤC (Max Sharpe) ===")
total_weight = 0
for ticker, weight in optimal_weights.items():
    if weight > 0.01:  # Chỉ hiển thị > 1%
        print(f"{ticker}: {weight:.1%}")
        total_weight += weight
print(f"\nTổng tỷ trọng: {total_weight:.1%}")
```

### Tối Ưu Danh Mục Tối Thiểu Rủi Ro

```python
# Tối ưu để giảm thiểu volatility
min_vol_weights = optimizer.optimize_min_volatility(
    tickers=tickers,
    start_date=start_date,
    end_date=end_date
)

print("=== DANH MỤC TỐI THIỂU RỦI RO ===")
for ticker, weight in min_vol_weights.items():
    if weight > 0.01:
        print(f"{ticker}: {weight:.1%}")
```

### Tối Ưu Với Mục Tiêu Lợi Nhuận

```python
# Tối ưu để đạt lợi nhuận mục tiêu 20%/năm
target_return_weights = optimizer.optimize_target_return(
    tickers=tickers,
    start_date=start_date,
    end_date=end_date,
    target_return=0.20  # 20% mục tiêu
)

print("=== DANH MỤC MỤC TIÊU 20%/NĂM ===")
for ticker, weight in target_return_weights.items():
    if weight > 0.01:
        print(f"{ticker}: {weight:.1%}")
```

### Tính Efficient Frontier

```python
# Tính đường biên hiệu quả
frontier = optimizer.calculate_efficient_frontier(
    tickers=tickers,
    start_date=start_date,
    end_date=end_date,
    num_portfolios=50
)

print("=== EFFICIENT FRONTIER ===")
print("Return\tVolatility\tSharpe")
for point in frontier[:10]:  # Hiển thị 10 điểm đầu
    print(f"{point['return']:.2%}\t{point['volatility']:.2%}\t{point['sharpe']:.2f}")
```

## 4. Paper Trading - Giao Dịch Mô Phỏng

### Thiết Lập Paper Trading

```python
import asyncio
from decimal import Decimal
from src.core.trading.broker_adapter import (
    PaperTradingAdapter,
    OrderSide,
    OrderType
)

async def paper_trading_demo():
    # Khởi tạo với vốn ban đầu 100 triệu
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    # Kiểm tra số dư
    balance = await broker.get_account_balance()
    print(f"Số dư ban đầu: {balance['cash']:,.0f} VND")

    # Tạo lệnh mua
    order = await broker.create_order(
        ticker="VCB",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1000,
        price=Decimal("95.5")
    )

    # Gửi lệnh
    result = await broker.submit_order(order)
    print(f"Lệnh ID: {result['order_id']}")
    print(f"Trạng thái: {result['status']}")

    # Kiểm tra vị thế
    positions = await broker.get_positions()
    for pos in positions:
        print(f"{pos['ticker']}: {pos['quantity']} cổ phiếu @ {pos['avg_price']:.2f}")

    # Kiểm tra số dư sau giao dịch
    balance = await broker.get_account_balance()
    print(f"Số dư còn lại: {balance['cash']:,.0f} VND")
    print(f"Tổng giá trị: {balance['total_value']:,.0f} VND")

    await broker.disconnect()

# Chạy demo
asyncio.run(paper_trading_demo())
```

### Paper Trading Với Risk Management

```python
from src.core.trading.risk_manager import RiskLimits, RiskManager
from src.core.trading.order_manager import OrderManager
from src.core.trading.position_tracker import PositionTracker

async def paper_trading_with_risk():
    # Setup
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    # Thiết lập risk limits
    risk_limits = RiskLimits(
        max_position_size_pct=0.10,      # Tối đa 10% mỗi vị thế
        max_daily_loss_pct=0.02,         # Tối đa 2% lỗ mỗi ngày
        max_portfolio_leverage=1.0,      # Không dùng đòn bẩy
        min_cash_balance_pct=0.05        # Giữ tối thiểu 5% tiền mặt
    )

    db = next(get_sync_session())
    risk_manager = RiskManager(db, risk_limits)
    order_manager = OrderManager(db, broker, risk_manager)
    tracker = PositionTracker(db, broker)

    # Lấy giá trị danh mục
    balance = await broker.get_account_balance()
    portfolio_value = balance['total_value']

    # Tính toán kích thước vị thế
    ticker = "VCB"
    entry_price = Decimal("95.5")

    quantity = risk_manager.calculate_position_size(
        ticker=ticker,
        portfolio_value=portfolio_value,
        risk_per_trade_pct=0.01,  # Rủi ro 1% mỗi giao dịch
        entry_price=entry_price
    )

    print(f"Kích thước vị thế đề xuất: {quantity} cổ phiếu")

    # Tính stop loss
    from datetime import date, timedelta
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    stop_loss = risk_manager.calculate_stop_loss(
        ticker=ticker,
        entry_price=entry_price,
        method="atr",
        atr_multiplier=2.0,
        start_date=start_date,
        end_date=end_date
    )

    # Tính take profit
    take_profit = risk_manager.calculate_take_profit(
        entry_price=entry_price,
        stop_loss=stop_loss,
        risk_reward_ratio=2.0  # Tỷ lệ risk/reward 1:2
    )

    print(f"Entry: {entry_price}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")

    # Tạo và gửi lệnh
    entry_order = await order_manager.create_limit_order(
        ticker=ticker,
        side=OrderSide.BUY,
        quantity=quantity,
        price=entry_price,
        submit=True  # Tự động kiểm tra risk trước khi gửi
    )

    print(f"Lệnh mua đã gửi: {entry_order['order_id']}")

    # Tạo stop loss order
    stop_order = await order_manager.create_stop_order(
        ticker=ticker,
        side=OrderSide.SELL,
        quantity=quantity,
        stop_price=stop_loss,
        submit=True
    )

    # Tạo take profit order
    tp_order = await order_manager.create_limit_order(
        ticker=ticker,
        side=OrderSide.SELL,
        quantity=quantity,
        price=take_profit,
        submit=True
    )

    # Đồng bộ và kiểm tra vị thế
    await tracker.sync_with_broker()
    position = tracker.get_position(ticker)

    if position:
        print(f"\nVị thế đã mở:")
        print(f"  Số lượng: {position.quantity}")
        print(f"  Giá trung bình: {position.avg_price:.2f}")
        print(f"  P&L hiện tại: {position.unrealized_pnl:,.0f} VND")

    await broker.disconnect()

asyncio.run(paper_trading_with_risk())
```

## 5. Live Trading - Giao Dịch Thực Tế

### Kết Nối Broker Thực Tế

**Lưu ý**: Cần có tài khoản và API credentials từ broker (SSI hoặc DNSE)

```python
from src.core.trading.broker_adapter import SSIBrokerAdapter
from src.utils.config import get_settings

settings = get_settings()

# Kết nối với SSI (cần credentials)
broker = SSIBrokerAdapter(
    api_key=settings.SSI_TRADING_API_KEY,
    secret_key=settings.SSI_TRADING_SECRET_KEY
)

await broker.connect()

# Sử dụng giống như Paper Trading
order = await broker.create_order(
    ticker="VCB",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=100
)

result = await broker.submit_order(order)
```

### Trading Với Risk Management Đầy Đủ

```python
async def live_trading_workflow():
    # 1. Setup broker và risk management
    broker = SSIBrokerAdapter(...)  # Hoặc DNSEBrokerAdapter
    await broker.connect()

    risk_limits = RiskLimits(
        max_position_size_pct=0.10,
        max_daily_loss_pct=0.02,
        max_sector_exposure_pct=0.30
    )

    db = next(get_sync_session())
    risk_manager = RiskManager(db, risk_limits)
    order_manager = OrderManager(db, broker, risk_manager)
    tracker = PositionTracker(db, broker)

    # 2. Lấy danh sách cổ phiếu từ screening
    candidates = screen_stocks(
        filters={"roe": {"min": 15}, "pe_ratio": {"max": 15}},
        limit=10
    )

    # 3. Với mỗi cổ phiếu, kiểm tra risk và giao dịch
    for stock in candidates:
        ticker = stock['ticker']

        # Kiểm tra risk trước
        is_valid, message = risk_manager.validate_order(
            ticker=ticker,
            side=OrderSide.BUY,
            quantity=1000,
            price=Decimal(str(stock['current_price'])),
            portfolio_value=await get_portfolio_value(broker),
            current_positions=await broker.get_positions()
        )

        if is_valid:
            # Tạo lệnh với risk management
            order = await order_manager.create_limit_order(
                ticker=ticker,
                side=OrderSide.BUY,
                quantity=1000,
                price=Decimal(str(stock['current_price'])),
                submit=True
            )
            print(f"Đã gửi lệnh mua {ticker}")
        else:
            print(f"Lệnh {ticker} bị từ chối: {message}")

    # 4. Theo dõi vị thế
    await tracker.sync_with_broker()
    summary = tracker.get_portfolio_summary()

    print(f"Tổng giá trị: {summary['total_value']:,.0f} VND")
    print(f"P&L: {summary['total_unrealized_pnl']:+,.0f} VND")

    # 5. Tạo risk report
    positions = await broker.get_positions()
    report = risk_manager.generate_risk_report(
        positions=positions,
        portfolio_value=summary['total_value']
    )

    print(f"VaR (95%): {report['var_95_1day']:,.0f} VND")
    print(f"Max Position: {report['max_position_size_pct']:.1%}")

    await broker.disconnect()
```

## Ví Dụ Hoàn Chỉnh

### Workflow Từ A-Z: Từ Screening Đến Trading

```python
import asyncio
from datetime import date, timedelta
from decimal import Decimal
from src.database.connection import get_sync_session
from src.core.screening.advanced_strategies import value_investing_strategy
from src.core.backtesting.engine import BacktestEngine
from src.core.backtesting.strategies import simple_moving_average_strategy
from src.core.portfolio.optimizer import PortfolioOptimizer
from src.core.trading.broker_adapter import PaperTradingAdapter, OrderSide, OrderType
from src.core.trading.risk_manager import RiskLimits, RiskManager
from src.core.trading.order_manager import OrderManager

async def complete_trading_workflow():
    """Workflow hoàn chỉnh từ screening đến trading."""

    db = next(get_sync_session())

    print("=== BƯỚC 1: SCREENING ===")
    # Tìm cổ phiếu value
    value_stocks = value_investing_strategy(
        min_pe=5,
        max_pe=15,
        min_roe=15
    )

    tickers = [s['ticker'] for s in value_stocks[:10]]
    print(f"Tìm thấy {len(tickers)} cổ phiếu: {', '.join(tickers)}")

    print("\n=== BƯỚC 2: BACKTESTING ===")
    # Backtest chiến lược
    engine = BacktestEngine(db)
    start_date = date(2023, 1, 1)
    end_date = date(2024, 12, 31)

    backtest_results = engine.run_backtest(
        strategy=simple_moving_average_strategy,
        tickers=tickers[:5],  # Test với 5 mã đầu
        start_date=start_date,
        end_date=end_date,
        initial_capital=100_000_000,
        strategy_params={"short_window": 20, "long_window": 50}
    )

    print(f"Lợi nhuận: {backtest_results['total_return']:.2%}")
    print(f"Sharpe: {backtest_results['sharpe_ratio']:.2f}")

    if backtest_results['sharpe_ratio'] < 1.0:
        print("Chiến lược không đủ tốt, dừng lại")
        return

    print("\n=== BƯỚC 3: PORTFOLIO OPTIMIZATION ===")
    # Tối ưu danh mục
    optimizer = PortfolioOptimizer(db)
    optimal_weights = optimizer.optimize_max_sharpe(
        tickers=tickers[:5],
        start_date=start_date,
        end_date=end_date,
        risk_free_rate=0.08
    )

    print("Tỷ trọng tối ưu:")
    for ticker, weight in optimal_weights.items():
        if weight > 0.01:
            print(f"  {ticker}: {weight:.1%}")

    print("\n=== BƯỚC 4: PAPER TRADING ===")
    # Paper trading với danh mục tối ưu
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    risk_limits = RiskLimits(
        max_position_size_pct=0.15,
        max_daily_loss_pct=0.02
    )
    risk_manager = RiskManager(db, risk_limits)
    order_manager = OrderManager(db, broker, risk_manager)

    balance = await broker.get_account_balance()
    portfolio_value = balance['total_value']

    # Mua theo tỷ trọng tối ưu
    for ticker, target_weight in optimal_weights.items():
        if target_weight < 0.01:
            continue

        target_value = portfolio_value * Decimal(str(target_weight))
        # Giả sử giá hiện tại (trong thực tế cần lấy từ API)
        current_price = Decimal("100.0")  # Placeholder
        quantity = int(target_value / current_price / 100) * 100  # Làm tròn về 100

        if quantity > 0:
            order = await order_manager.create_limit_order(
                ticker=ticker,
                side=OrderSide.BUY,
                quantity=quantity,
                price=current_price,
                submit=True
            )
            print(f"Đã gửi lệnh mua {ticker}: {quantity} cổ phiếu")

    # Kiểm tra kết quả
    positions = await broker.get_positions()
    print(f"\nSố vị thế: {len(positions)}")
    for pos in positions:
        print(f"  {pos['ticker']}: {pos['quantity']} @ {pos['avg_price']:.2f}")

    balance = await broker.get_account_balance()
    print(f"\nTổng giá trị: {balance['total_value']:,.0f} VND")

    await broker.disconnect()

    print("\n=== HOÀN TẤT ===")

# Chạy workflow
asyncio.run(complete_trading_workflow())
```

## Chạy Demo Scripts

Dự án có sẵn các demo scripts:

```bash
# Demo Phase 2: Backtesting & Portfolio
python scripts/phase2_demo.py

# Demo Phase 3: ML & Sentiment
python scripts/phase3_demo.py

# Demo Phase 4: Trading System
python scripts/phase4_demo.py
```

## Lưu Ý Quan Trọng

### Risk Management

1. **Luôn sử dụng stop loss**: Không bao giờ giao dịch mà không có stop loss
2. **Giới hạn rủi ro mỗi giao dịch**: Không rủi ro quá 1-2% vốn mỗi giao dịch
3. **Đa dạng hóa**: Không tập trung quá nhiều vào một cổ phiếu (tối đa 10-15%)
4. **Giới hạn lỗ hàng ngày**: Dừng giao dịch nếu lỗ quá 2-3% trong ngày

### Best Practices

1. **Luôn backtest trước**: Không bao giờ giao dịch chiến lược chưa được backtest
2. **Bắt đầu với paper trading**: Test kỹ với tiền giả trước khi dùng tiền thật
3. **Theo dõi performance**: Thường xuyên review và cải thiện chiến lược
4. **Cập nhật dữ liệu**: Đảm bảo dữ liệu được cập nhật hàng ngày

### Cấu Hình Production

Khi sẵn sàng giao dịch thực tế:

1. **Bảo mật**: Bảo vệ API keys, không commit vào git
2. **Monitoring**: Thiết lập cảnh báo cho các sự kiện quan trọng
3. **Backup**: Backup database thường xuyên
4. **Testing**: Test kỹ trên môi trường staging trước

## Tài Liệu Tham Khảo

- [Quick Start Guide](QUICKSTART.md) - Hướng dẫn setup nhanh
- [Phase 2 Guide](../phases/PHASE2.md) - Backtesting & Portfolio chi tiết
- [Phase 3 Guide](../phases/PHASE3.md) - ML & Sentiment Analysis
- [Phase 4 Guide](../phases/PHASE4.md) - Trading System chi tiết
- [API Documentation](http://localhost:8000/docs) - Tài liệu API đầy đủ

---

**Chúc bạn trading thành công!** 🚀
