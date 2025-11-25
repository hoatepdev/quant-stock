Build a robust backtesting engine for Vietnamese stock market strategies with:

**Core features:**

1. Event-driven backtesting architecture
2. Vietnam market constraints:
   - ±7% daily price limits
   - T+2 settlement
   - Trading hours: 9:00-15:00
   - Foreign ownership limits
3. Transaction cost modeling (0.15% brokerage + 0.1% tax)
4. Slippage simulation
5. Walk-forward analysis capability
6. Monte Carlo simulation for robustness testing

**Performance metrics:**

- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Win rate, profit factor, expectancy
- Maximum drawdown, recovery time
- Alpha vs VN-Index
- Rolling performance analysis

**Input:**

- Strategy signals (buy/sell/hold)
- Historical price/volume data
- Factor values

**Output:**

- Detailed performance report
- Equity curve
- Trade log
- Risk metrics
- Statistical significance tests

Use vectorbt or create custom framework. Provide complete implementation.
