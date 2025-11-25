# Phase 2 Features Guide

This document describes the Phase 2 features implemented in the Vietnam Quant Platform.

## Overview

Phase 2 adds advanced quantitative analysis capabilities:

1. **Corporate Action Adjuster** - Automatic price adjustment for splits and dividends
2. **Market Index Tracking** - Track and analyze VN-Index, HNX-Index, etc.
3. **Backtesting Framework** - Test trading strategies on historical data
4. **Portfolio Optimization** - Modern Portfolio Theory optimization

## 1. Corporate Actions

### Detection

The system can automatically detect stock splits and reverse splits from price patterns:

```python
from src.core.corporate_actions.detector import CorporateActionDetector
from src.database.connection import get_sync_session

db = next(get_sync_session())
detector = CorporateActionDetector(db)

# Detect splits for a ticker
splits = detector.detect_stock_splits("VCB")
print(f"Found {len(splits)} potential splits")

# Save detected actions
saved = detector.save_detected_actions(splits)
```

### Adjustment

Apply price adjustments for corporate actions:

```python
from src.core.corporate_actions.adjuster import CorporateActionAdjuster

adjuster = CorporateActionAdjuster(db)

# Apply adjustments for a ticker
adjusted = adjuster.apply_adjustments_for_ticker("VCB")
print(f"Adjusted {adjusted} price records")

# Recalculate all adjustments from scratch
recalculated = adjuster.recalculate_adjusted_prices("VCB")

# Get unverified actions
unverified = adjuster.get_unverified_actions("VCB")
```

### Workflow

1. **Detection** - System automatically detects potential corporate actions
2. **Verification** - Manual review of detected actions (set `is_verified=True`)
3. **Application** - Apply verified actions to adjust historical prices
4. **Monitoring** - Track which actions have been applied

## 2. Market Index Tracking

Track Vietnam market indices and compare stock performance:

```python
from src.core.market_index.tracker import MarketIndexTracker
from datetime import date, timedelta

db = next(get_sync_session())
tracker = MarketIndexTracker(db)

# Get latest index value
latest = tracker.get_latest_index_value("VN-INDEX")
print(f"VN-Index: {latest.close}")

# Calculate returns
end_date = date.today()
start_date = end_date - timedelta(days=365)
returns = tracker.calculate_index_returns("VN-INDEX", start_date, end_date)
print(f"1-year return: {returns:.2%}")

# Get index summary
summary = tracker.get_index_summary("VN-INDEX")
print(f"Volatility: {summary['year_volatility']:.2%}")

# Compare stock to index
comparison = tracker.compare_stock_to_index(
    "VCB", "VN-INDEX", start_date, end_date
)
print(f"Alpha: {comparison['alpha']:.2%}")
```

### Supported Indices

- **VN-INDEX** - Ho Chi Minh Stock Exchange
- **HNX-INDEX** - Hanoi Stock Exchange
- **UPCOM-INDEX** - Unlisted Public Company Market
- **VN30** - Top 30 stocks by market cap
- **HNX30** - Top 30 HNX stocks

## 3. Backtesting Framework

Test trading strategies on historical data:

```python
from src.core.backtesting.engine import BacktestEngine
from src.core.backtesting.strategies import simple_moving_average_strategy
from datetime import date, timedelta
from decimal import Decimal

db = next(get_sync_session())
engine = BacktestEngine(
    db,
    initial_capital=Decimal("100000000"),  # 100M VND
    commission_rate=0.0015  # 0.15%
)

# Define backtest parameters
tickers = ["VCB", "VHM", "VIC"]
end_date = date.today()
start_date = end_date - timedelta(days=365)

# Run backtest
results = engine.run(
    strategy=simple_moving_average_strategy,
    tickers=tickers,
    start_date=start_date,
    end_date=end_date,
)

# View results
print(f"Initial Capital: {results['initial_capital']:,.0f} VND")
print(f"Final Value: {results['final_value']:,.0f} VND")
print(f"Total Return: {results['total_return']:.2%}")
print(f"Win Rate: {results['statistics']['win_rate']:.2%}")
```

### Built-in Strategies

1. **Simple Moving Average** - MA crossover strategy
2. **Momentum** - Buy top performers, sell bottom performers
3. **Mean Reversion** - Bollinger Bands strategy
4. **Buy and Hold** - Baseline strategy

### Custom Strategy

Create your own strategy:

```python
def my_strategy(data, portfolio, current_prices):
    """Custom trading strategy.

    Args:
        data: Historical price DataFrame
        portfolio: Current portfolio
        current_prices: Dict of current prices

    Returns:
        Dict of ticker -> signal (BUY, SELL, HOLD)
    """
    signals = {}

    for ticker in current_prices.keys():
        # Your strategy logic here
        if should_buy(ticker, data):
            signals[ticker] = "BUY"
        elif should_sell(ticker, data):
            signals[ticker] = "SELL"

    return signals

# Run with your strategy
results = engine.run(my_strategy, tickers, start_date, end_date)
```

### Performance Metrics

The backtest engine calculates:
- Total return
- Win rate
- Average profit/loss
- Profit factor
- Sharpe ratio (via portfolio optimization)
- Equity curve

## 4. Portfolio Optimization

Optimize portfolio weights using Modern Portfolio Theory:

```python
from src.core.portfolio.optimizer import PortfolioOptimizer

db = next(get_sync_session())
optimizer = PortfolioOptimizer(db)

tickers = ["VCB", "VHM", "VIC", "GAS", "MSN"]
end_date = date.today()
start_date = end_date - timedelta(days=730)  # 2 years

# Maximum Sharpe Ratio
max_sharpe = optimizer.optimize_max_sharpe(
    tickers, start_date, end_date, risk_free_rate=0.03
)
print(f"Sharpe Ratio: {max_sharpe['sharpe_ratio']:.2f}")
print(f"Expected Return: {max_sharpe['expected_return']:.2%}")
print(f"Volatility: {max_sharpe['volatility']:.2%}")
for ticker, weight in max_sharpe['weights'].items():
    print(f"{ticker}: {weight:.2%}")

# Minimum Volatility
min_vol = optimizer.optimize_min_volatility(tickers, start_date, end_date)

# Target Return
target_return = optimizer.optimize_target_return(
    tickers, target_return=0.15, start_date=start_date, end_date=end_date
)

# Efficient Frontier
frontier = optimizer.efficient_frontier(
    tickers, start_date, end_date, num_points=50
)
```

### Optimization Methods

1. **Maximum Sharpe Ratio** - Best risk-adjusted returns
2. **Minimum Volatility** - Lowest risk portfolio
3. **Target Return** - Achieve specific return with minimum risk
4. **Efficient Frontier** - Plot of all optimal portfolios

### Weighting Schemes

```python
# Equal weight
equal_weights = optimizer.equal_weight_portfolio(tickers)

# Market cap weighted
mcap_weights = optimizer.market_cap_weighted_portfolio(tickers)
```

## Running the Demo

Test all Phase 2 features with the demo script:

```bash
python scripts/phase2_demo.py
```

This will demonstrate:
1. Corporate action detection
2. Market index tracking and comparison
3. Backtesting with multiple strategies
4. Portfolio optimization methods

## API Integration

Phase 2 features can be exposed via REST API:

```python
# In src/api/routes/

@router.post("/backtest")
async def run_backtest(
    tickers: List[str],
    start_date: date,
    end_date: date,
    strategy: str = "moving_average",
    db: Session = Depends(get_db),
):
    """Run backtest endpoint."""
    engine = BacktestEngine(db)
    # ... implementation

@router.post("/optimize")
async def optimize_portfolio(
    tickers: List[str],
    method: str = "max_sharpe",
    db: Session = Depends(get_db),
):
    """Portfolio optimization endpoint."""
    optimizer = PortfolioOptimizer(db)
    # ... implementation
```

## Dependencies

Phase 2 requires additional Python packages:

```bash
pip install scipy numpy pandas
```

These are included in `requirements.txt`.

## Best Practices

### Corporate Actions

1. Always verify detected actions manually before applying
2. Keep backup of unadjusted prices
3. Document adjustment ratios and dates
4. Use `recalculate_adjusted_prices()` when fixing mistakes

### Backtesting

1. Use sufficient historical data (at least 2 years)
2. Account for transaction costs
3. Consider survivorship bias
4. Test multiple time periods
5. Validate strategy logic before production

### Portfolio Optimization

1. Use 2-3 years of data for covariance estimation
2. Rebalance regularly (monthly or quarterly)
3. Consider transaction costs when rebalancing
4. Don't over-optimize (overfitting)
5. Use constraints (max position size, sector limits)

## Performance Considerations

- **Backtesting**: Can be slow for many tickers/long periods. Consider:
  - Limiting number of tickers
  - Using monthly rebalancing instead of daily
  - Caching price data

- **Portfolio Optimization**: scipy.optimize can be slow. Consider:
  - Using coarser efficient frontier (fewer points)
  - Caching returns/covariance calculations
  - Using faster optimization methods

## Troubleshooting

### "No price data found"
- Ensure tickers exist in database
- Run backfill script first: `python scripts/backfill_data.py`
- Check date range is valid

### "Optimization failed"
- Ensure scipy is installed: `pip install scipy`
- Check for sufficient price data
- Try different initial weights

### "Insufficient funds" in backtest
- Reduce position sizes
- Increase initial capital
- Check commission rate

## Next Steps

After Phase 2, consider:
- Real-time data feeds (Phase 3)
- Machine learning models (Phase 3)
- Advanced risk management
- Multi-asset optimization
- Transaction cost optimization

## Examples

See [examples/phase2_examples.py](../examples/phase2_examples.py) for complete examples.

## API Reference

Full API documentation available at:
- Corporate Actions: [src/core/corporate_actions/](../src/core/corporate_actions/)
- Market Index: [src/core/market_index/](../src/core/market_index/)
- Backtesting: [src/core/backtesting/](../src/core/backtesting/)
- Portfolio: [src/core/portfolio/](../src/core/portfolio/)
