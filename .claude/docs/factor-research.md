Develop a factor research framework for Vietnam stock market:

**Factor categories:**

1. Value: P/E, P/B, EV/EBITDA, dividend yield, earnings yield
2. Quality: ROE, ROA, profit margin, asset turnover, accruals
3. Momentum: 1/3/6/12-month returns, 52-week high, relative strength
4. Size: Market cap, liquidity
5. Volatility: Beta, idiosyncratic vol, downside deviation
6. Vietnam-specific: Foreign ownership %, foreign room, prop trading

**Analysis pipeline:**

1. Factor calculation from raw data
2. Factor normalization (z-score, rank)
3. Quintile portfolio formation
4. Factor return calculation
5. Statistical tests (t-tests, IC, IR)
6. Factor combination (equal-weight, IC-weight, ML)
7. Decay analysis
8. Factor correlation matrix

**Implementation:**

- Vectorized calculations using pandas/numpy
- Efficient data structures
- Caching mechanism
- Parallel processing for speed

**Output:**

- Factor definition library
- Historical factor values
- Factor performance reports
- Signal generation module

Provide modular, extensible codebase.
