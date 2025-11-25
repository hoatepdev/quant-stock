I need a corporate actions adjustment system for Vietnamese stock market data. Build a module that:

1. Detects stock splits, reverse splits, and bonus shares from price patterns
2. Identifies dividend payments
3. Adjusts historical prices backward for splits
4. Stores corporate action events in database
5. Provides adjusted vs unadjusted price series

Input data format:

- Daily OHLCV data from SSI iBoard API
- Corporate action announcements (if available)

Requirements:

- Automatic split detection algorithm (analyze price gaps + volume spikes)
- Split ratio calculation
- Backward adjustment of historical prices
- Audit trail for all adjustments
- PostgreSQL storage schema

Provide complete implementation with unit tests.
