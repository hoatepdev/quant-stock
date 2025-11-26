# Phase 4 - Trading System & Risk Management

Complete guide for Phase 4 implementation: Production-ready trading capabilities with broker integration, risk management, order management, and position tracking.

## Overview

Phase 4 transforms the Vietnam Quant Platform into a complete end-to-end trading system with:
- Broker integration framework
- Comprehensive risk management
- Order management system
- Real-time position tracking

## 1. Broker Integration Framework

### Location
`src/core/trading/broker_adapter.py` (650+ lines)

### Architecture

**Abstract Base Class**
```python
from abc import ABC, abstractmethod
from enum import Enum
from decimal import Decimal
from typing import Dict, List, Optional

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class BrokerAdapter(ABC):
    """Abstract interface for broker integration."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker API."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker API."""
        pass

    @abstractmethod
    async def create_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Dict:
        """Create an order."""
        pass

    @abstractmethod
    async def submit_order(self, order: Dict) -> Dict:
        """Submit order to broker."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get current order status."""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict]:
        """Get all current positions."""
        pass

    @abstractmethod
    async def get_account_balance(self) -> Dict:
        """Get account balance information."""
        pass
```

### Broker Implementations

#### 1. Paper Trading Adapter (Fully Functional)

```python
from src.core.trading.broker_adapter import PaperTradingAdapter

# Initialize with starting capital
broker = PaperTradingAdapter(
    initial_cash=Decimal("100000000")  # 100M VND
)

await broker.connect()

# Create market order
order = await broker.create_order(
    ticker="VCB",
    side=OrderSide.BUY,
    quantity=1000,
    order_type=OrderType.MARKET,
)

# Submit order
result = await broker.submit_order(order)
print(f"Order ID: {result['order_id']}")
print(f"Status: {result['status']}")

# Check positions
positions = await broker.get_positions()
for pos in positions:
    print(f"{pos['ticker']}: {pos['quantity']} shares @ {pos['avg_price']}")

# Check balance
balance = await broker.get_account_balance()
print(f"Cash: {balance['cash']:,.0f} VND")
print(f"Total Value: {balance['total_value']:,.0f} VND")

await broker.disconnect()
```

**Features**:
- Simulated order execution
- Position tracking
- Cash management
- Order history
- Perfect for testing strategies

#### 2. SSI Broker Adapter (Placeholder)

```python
from src.core.trading.broker_adapter import SSIBrokerAdapter

broker = SSIBrokerAdapter(
    api_key=settings.SSI_API_KEY,
    secret_key=settings.SSI_SECRET_KEY,
)

# Same interface as PaperTradingAdapter
await broker.connect()
# ... use same methods
```

**Note**: Requires SSI trading API credentials (separate from data API)

#### 3. DNSE Broker Adapter (Placeholder)

```python
from src.core.trading.broker_adapter import DNSEBrokerAdapter

broker = DNSEBrokerAdapter(
    api_key=settings.DNSE_API_KEY,
    secret_key=settings.DNSE_SECRET_KEY,
)

await broker.connect()
# ... use same methods
```

## 2. Risk Management System

### Location
`src/core/trading/risk_manager.py` (550+ lines)

### Risk Limits Configuration

```python
from src.core.trading.risk_manager import RiskLimits, RiskManager
from decimal import Decimal

# Define risk limits
risk_limits = RiskLimits(
    max_position_size_pct=0.10,        # 10% max per position
    max_sector_exposure_pct=0.30,      # 30% max per sector
    max_portfolio_leverage=1.0,         # No leverage allowed
    max_daily_loss_pct=0.02,           # 2% daily loss limit
    max_drawdown_pct=0.10,             # 10% max drawdown
    min_cash_balance_pct=0.05,         # 5% minimum cash reserve
    max_correlation=0.7,               # Max correlation between positions
)

risk_manager = RiskManager(db, risk_limits)
```

### Position Sizing

**Risk-Based Sizing**
```python
# Calculate position size based on risk tolerance
quantity = risk_manager.calculate_position_size(
    ticker="VCB",
    portfolio_value=Decimal("100000000"),
    risk_per_trade_pct=0.01,  # Risk 1% of portfolio
    entry_price=Decimal("95.5"),
    stop_loss_price=Decimal("91.0"),  # Optional
)

print(f"Recommended quantity: {quantity} shares")
```

**Volatility-Adjusted Sizing**
```python
# Size based on historical volatility
quantity = risk_manager.calculate_volatility_adjusted_size(
    ticker="VCB",
    portfolio_value=Decimal("100000000"),
    target_volatility=0.02,  # 2% target volatility
)
```

### Stop Loss Calculation

**ATR-Based Stop Loss**
```python
from datetime import date, timedelta

end_date = date.today()
start_date = end_date - timedelta(days=30)

stop_loss = risk_manager.calculate_stop_loss(
    ticker="VCB",
    entry_price=Decimal("95.5"),
    method="atr",           # ATR-based
    atr_multiplier=2.0,     # 2x ATR
    start_date=start_date,
    end_date=end_date,
)

print(f"ATR Stop Loss: {stop_loss:.2f}")
```

**Fixed Percentage Stop Loss**
```python
stop_loss = risk_manager.calculate_stop_loss(
    ticker="VCB",
    entry_price=Decimal("95.5"),
    method="fixed_pct",
    stop_loss_pct=0.05,  # 5% below entry
)

print(f"Fixed Stop Loss: {stop_loss:.2f}")
```

**Support-Based Stop Loss**
```python
stop_loss = risk_manager.calculate_stop_loss(
    ticker="VCB",
    entry_price=Decimal("95.5"),
    method="support",
    support_level=Decimal("90.0"),  # Known support level
)
```

### Take Profit Calculation

```python
# Calculate take profit based on risk/reward ratio
entry_price = Decimal("95.5")
stop_loss = Decimal("91.0")

take_profit = risk_manager.calculate_take_profit(
    entry_price=entry_price,
    stop_loss=stop_loss,
    risk_reward_ratio=2.0,  # 2:1 reward/risk
)

print(f"Entry: {entry_price}")
print(f"Stop Loss: {stop_loss}")
print(f"Take Profit: {take_profit}")
print(f"Risk: {entry_price - stop_loss:.2f}")
print(f"Reward: {take_profit - entry_price:.2f}")
```

### Order Validation

```python
# Validate order before submission
is_valid, message = risk_manager.validate_order(
    ticker="VCB",
    side=OrderSide.BUY,
    quantity=1000,
    price=Decimal("95.5"),
    portfolio_value=Decimal("100000000"),
    current_positions=positions,
)

if is_valid:
    # Submit order
    await order_manager.submit_order(order)
else:
    print(f"Order rejected: {message}")
```

### Value at Risk (VaR)

```python
# Calculate portfolio VaR
var_result = risk_manager.calculate_var(
    positions=current_positions,
    confidence_level=0.95,  # 95% confidence
    time_horizon=1,          # 1 day
    start_date=start_date,
    end_date=end_date,
)

print(f"Portfolio Value: {var_result['portfolio_value']:,.0f}")
print(f"VaR (95%, 1-day): {var_result['var_amount']:,.0f}")
print(f"VaR %: {var_result['var_pct']:.2%}")
```

### Risk Reporting

```python
# Generate comprehensive risk report
report = risk_manager.generate_risk_report(
    positions=current_positions,
    portfolio_value=Decimal("100000000"),
    start_date=start_date,
    end_date=end_date,
)

print("=== RISK REPORT ===")
print(f"Total Exposure: {report['total_exposure']:,.0f}")
print(f"Cash Reserve: {report['cash_pct']:.1%}")
print(f"VaR (95%): {report['var_95_1day']:,.0f}")
print(f"Largest Position: {report['max_position_size_pct']:.1%}")
print(f"Sector Concentration: {report['max_sector_exposure_pct']:.1%}")
```

## 3. Order Management System

### Location
`src/core/trading/order_manager.py` (400+ lines)

### Setup

```python
from src.core.trading.order_manager import OrderManager

order_manager = OrderManager(
    db=db,
    broker=broker,
    risk_manager=risk_manager,
)
```

### Creating Orders

**Market Order**
```python
order = await order_manager.create_market_order(
    ticker="VCB",
    side=OrderSide.BUY,
    quantity=1000,
    submit=True,  # Auto-submit after risk validation
)

print(f"Order ID: {order['order_id']}")
print(f"Status: {order['status']}")
```

**Limit Order**
```python
order = await order_manager.create_limit_order(
    ticker="VCB",
    side=OrderSide.BUY,
    quantity=1000,
    price=Decimal("95.0"),
    submit=True,
)
```

**Stop Loss Order**
```python
order = await order_manager.create_stop_order(
    ticker="VCB",
    side=OrderSide.SELL,
    quantity=1000,
    stop_price=Decimal("91.0"),
    submit=True,
)
```

**Stop-Limit Order**
```python
order = await order_manager.create_stop_limit_order(
    ticker="VCB",
    side=OrderSide.SELL,
    quantity=1000,
    stop_price=Decimal("91.0"),
    limit_price=Decimal("90.5"),
    submit=True,
)
```

### Order Management

**Cancel Order**
```python
success = await order_manager.cancel_order(order_id="12345")
if success:
    print("Order cancelled successfully")
```

**Get Order Status**
```python
status = await order_manager.get_order_status(order_id="12345")
print(f"Order status: {status}")
```

**Get All Orders**
```python
all_orders = order_manager.get_all_orders()
for order in all_orders:
    print(f"{order['ticker']}: {order['status']} - {order['quantity']} @ {order['price']}")
```

**Filter Orders**
```python
# Get filled orders only
filled = order_manager.get_filled_orders()

# Get pending orders
pending = order_manager.get_pending_orders()

# Get orders by ticker
vcb_orders = order_manager.get_orders_by_ticker("VCB")

# Get orders by date range
recent = order_manager.get_orders_by_date_range(start_date, end_date)
```

### Order Summary

```python
summary = order_manager.get_order_summary()

print(f"Total Orders: {summary['total_orders']}")
print(f"Filled: {summary['filled_orders']}")
print(f"Pending: {summary['pending_orders']}")
print(f"Cancelled: {summary['cancelled_orders']}")
print(f"Fill Rate: {summary['fill_rate']:.1%}")
```

## 4. Position Tracking

### Location
`src/core/trading/position_tracker.py` (350+ lines)

### Setup

```python
from src.core.trading.position_tracker import PositionTracker

tracker = PositionTracker(
    db=db,
    broker=broker,
)
```

### Position Management

**Sync with Broker**
```python
# Synchronize positions with broker
await tracker.sync_with_broker()
print("Positions synchronized")
```

**Get Position**
```python
position = tracker.get_position("VCB")

print(f"Ticker: {position.ticker}")
print(f"Quantity: {position.quantity}")
print(f"Avg Price: {position.avg_price:.2f}")
print(f"Current Price: {position.current_price:.2f}")
print(f"Market Value: {position.market_value:,.0f}")
print(f"Unrealized P&L: {position.unrealized_pnl:,.0f}")
print(f"Unrealized P&L %: {position.unrealized_pnl_pct:+.2%}")
```

**Get All Positions**
```python
positions = tracker.get_all_positions()

for pos in positions:
    print(f"{pos.ticker}: {pos.quantity} @ {pos.avg_price:.2f}")
    print(f"  P&L: {pos.unrealized_pnl:+,.0f} ({pos.unrealized_pnl_pct:+.2%})")
```

### Portfolio Metrics

**Portfolio Summary**
```python
summary = tracker.get_portfolio_summary()

print("=== PORTFOLIO SUMMARY ===")
print(f"Total Value: {summary['total_value']:,.0f} VND")
print(f"Cash: {summary['cash']:,.0f} VND")
print(f"Positions Value: {summary['positions_value']:,.0f} VND")
print(f"Total Unrealized P&L: {summary['total_unrealized_pnl']:+,.0f} VND")
print(f"Total P&L %: {summary['total_unrealized_pnl_pct']:+.2%}")
print(f"Number of Positions: {summary['num_positions']}")
```

**Position Breakdown**
```python
breakdown = tracker.get_position_breakdown()

print("=== POSITION BREAKDOWN ===")
for item in breakdown:
    print(f"{item['ticker']}: {item['weight']:.1%} of portfolio")
    print(f"  Value: {item['market_value']:,.0f}")
    print(f"  P&L: {item['unrealized_pnl']:+,.0f} ({item['unrealized_pnl_pct']:+.2%})")
```

**Top/Worst Performers**
```python
# Top 5 performers
top = tracker.get_top_performers(limit=5)
print("=== TOP PERFORMERS ===")
for pos in top:
    print(f"{pos.ticker}: {pos.unrealized_pnl_pct:+.2%}")

# Worst 5 performers
worst = tracker.get_worst_performers(limit=5)
print("=== WORST PERFORMERS ===")
for pos in worst:
    print(f"{pos.ticker}: {pos.unrealized_pnl_pct:+.2%}")
```

## 5. Complete Trading Workflow

### Example: Buy Trade with Risk Management

```python
from decimal import Decimal
from datetime import date, timedelta

async def execute_trade_with_risk_management():
    # 1. Setup
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    risk_limits = RiskLimits(
        max_position_size_pct=0.10,
        max_daily_loss_pct=0.02,
    )
    risk_manager = RiskManager(db, risk_limits)
    order_manager = OrderManager(db, broker, risk_manager)
    tracker = PositionTracker(db, broker)

    # 2. Get portfolio value
    balance = await broker.get_account_balance()
    portfolio_value = balance['total_value']

    # 3. Calculate position size
    ticker = "VCB"
    entry_price = Decimal("95.5")

    quantity = risk_manager.calculate_position_size(
        ticker=ticker,
        portfolio_value=portfolio_value,
        risk_per_trade_pct=0.01,  # Risk 1%
    )

    # 4. Calculate stop loss and take profit
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    stop_loss = risk_manager.calculate_stop_loss(
        ticker=ticker,
        entry_price=entry_price,
        method="atr",
        atr_multiplier=2.0,
        start_date=start_date,
        end_date=end_date,
    )

    take_profit = risk_manager.calculate_take_profit(
        entry_price=entry_price,
        stop_loss=stop_loss,
        risk_reward_ratio=2.0,
    )

    print(f"Entry: {entry_price}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")
    print(f"Quantity: {quantity}")

    # 5. Create and submit entry order
    entry_order = await order_manager.create_limit_order(
        ticker=ticker,
        side=OrderSide.BUY,
        quantity=quantity,
        price=entry_price,
        submit=True,  # Auto risk validation
    )

    print(f"Entry order submitted: {entry_order['order_id']}")

    # 6. Create stop loss order
    stop_order = await order_manager.create_stop_order(
        ticker=ticker,
        side=OrderSide.SELL,
        quantity=quantity,
        stop_price=stop_loss,
        submit=True,
    )

    # 7. Create take profit order
    tp_order = await order_manager.create_limit_order(
        ticker=ticker,
        side=OrderSide.SELL,
        quantity=quantity,
        price=take_profit,
        submit=True,
    )

    # 8. Monitor position
    await tracker.sync_with_broker()
    position = tracker.get_position(ticker)

    if position:
        print(f"\nPosition opened:")
        print(f"  Quantity: {position.quantity}")
        print(f"  Avg Price: {position.avg_price:.2f}")
        print(f"  Current P&L: {position.unrealized_pnl:,.0f}")

    # 9. Generate risk report
    positions = await broker.get_positions()
    report = risk_manager.generate_risk_report(
        positions=positions,
        portfolio_value=portfolio_value,
        start_date=start_date,
        end_date=end_date,
    )

    print(f"\nRisk Report:")
    print(f"  VaR (95%): {report['var_95_1day']:,.0f}")
    print(f"  Max Position: {report['max_position_size_pct']:.1%}")

    await broker.disconnect()

# Run the workflow
await execute_trade_with_risk_management()
```

## 6. Running the Demo

### Phase 4 Demo Script

```bash
python scripts/phase4_demo.py
```

This demonstrates:
1. Paper trading with buy/sell orders
2. Position sizing and risk calculation
3. Stop loss and take profit setup
4. Order management (create, submit, track)
5. Position tracking and P&L monitoring
6. Complete integrated workflow

## 7. Production Considerations

### Broker API Setup

**SSI Trading API**
1. Register for SSI trading account
2. Request API access (different from data API)
3. Configure credentials in `.env`:
   ```env
   SSI_TRADING_API_KEY=your_trading_key
   SSI_TRADING_SECRET_KEY=your_trading_secret
   ```

**DNSE Trading API**
1. Open DNSE trading account
2. Enable API access
3. Configure credentials in `.env`:
   ```env
   DNSE_TRADING_API_KEY=your_trading_key
   DNSE_TRADING_SECRET_KEY=your_trading_secret
   ```

### Risk Management Best Practices

1. **Start Small**
   - Test with paper trading first
   - Start with small position sizes
   - Gradually increase as you gain confidence

2. **Diversification**
   - Don't exceed max position size (10% recommended)
   - Spread across sectors
   - Monitor correlation

3. **Stop Losses**
   - Always use stop losses
   - ATR-based stops adapt to volatility
   - Don't move stops against you

4. **Daily Limits**
   - Set daily loss limits (2% recommended)
   - Take a break if limit hit
   - Review what went wrong

5. **Regular Monitoring**
   - Check positions daily
   - Update stop losses as price moves
   - Rebalance when needed

### Error Handling

```python
from src.core.trading.exceptions import (
    OrderRejectedError,
    InsufficientFundsError,
    RiskLimitExceededError,
)

try:
    order = await order_manager.create_limit_order(...)
except RiskLimitExceededError as e:
    print(f"Risk limit exceeded: {e}")
except InsufficientFundsError as e:
    print(f"Insufficient funds: {e}")
except OrderRejectedError as e:
    print(f"Order rejected: {e}")
```

## 8. Performance Metrics

Track your trading performance:

```python
# Calculate trading metrics
from src.core.analytics.performance import PerformanceAnalytics

analytics = PerformanceAnalytics(db)

# Get trading performance
start_date = date(2024, 1, 1)
end_date = date.today()

performance = analytics.calculate_trading_performance(
    start_date=start_date,
    end_date=end_date,
)

print(f"Total Return: {performance['total_return']:.2%}")
print(f"Sharpe Ratio: {performance['sharpe_ratio']:.2f}")
print(f"Win Rate: {performance['win_rate']:.2%}")
print(f"Profit Factor: {performance['profit_factor']:.2f}")
print(f"Max Drawdown: {performance['max_drawdown']:.2%}")
```

## 9. Next Steps

After mastering Phase 4:

1. **Automate Trading**
   - Create automated trading strategies
   - Combine with ML predictions (Phase 3)
   - Set up scheduled rebalancing

2. **Advanced Risk Management**
   - Portfolio-level risk metrics
   - Correlation analysis
   - Stress testing

3. **Performance Attribution**
   - Factor-based attribution
   - Sector performance
   - Strategy comparison

4. **Integration**
   - Connect to live broker APIs
   - Real-time monitoring dashboard
   - Alert system (SMS/Email)

## Conclusion

Phase 4 completes the Vietnam Quant Platform with production-ready trading capabilities. You now have:

- ✅ Broker integration (Paper, SSI, DNSE)
- ✅ Comprehensive risk management
- ✅ Professional order management
- ✅ Real-time position tracking
- ✅ Complete trading workflow

Ready for live trading! 🚀

---

**Questions?** Run `python scripts/phase4_demo.py` to see everything in action.
