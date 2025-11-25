# VIETNAM STOCK MARKET QUANTITATIVE ANALYSIS PLATFORM - FULL PROJECT SETUP

## PROJECT CONTEXT

I need to build a complete quantitative investment research and trading platform specifically for the Vietnam stock market. This is a professional-grade system that will analyze ~1,800 stocks across HOSE, HNX, and UPCoM exchanges using 7 investment methodologies: Fundamental Analysis, Technical Analysis, Quantitative Research, Macro Analysis, Behavioral Finance, Event-based Trading, and Market Flow Analysis.

## IMMEDIATE TASK: CREATE COMPLETE MVP PROJECT STRUCTURE (4 WEEKS)

Please create a production-ready project with the following structure:

### 1. PROJECT ARCHITECTURE

vietnam-quant-platform/
├── docker/
│ ├── Dockerfile.api
│ ├── Dockerfile.worker
│ └── docker-compose.yml
├── src/
│ ├── api/ # FastAPI application
│ │ ├── init.py
│ │ ├── main.py
│ │ ├── routes/
│ │ │ ├── screening.py
│ │ │ ├── factors.py
│ │ │ └── health.py
│ │ ├── models/
│ │ └── dependencies.py
│ ├── core/ # Core business logic
│ │ ├── data_ingestion/
│ │ │ ├── ssi_client.py
│ │ │ ├── vndirect_client.py
│ │ │ └── data_fetcher.py
│ │ ├── factors/
│ │ │ ├── fundamental.py
│ │ │ ├── technical.py
│ │ │ ├── momentum.py
│ │ │ └── factor_engine.py
│ │ ├── corporate_actions/
│ │ │ ├── detector.py
│ │ │ ├── adjuster.py
│ │ │ └── split_handler.py
│ │ └── screening/
│ │ ├── screener.py
│ │ └── filters.py
│ ├── database/
│ │ ├── models.py # SQLAlchemy models
│ │ ├── migrations/ # Alembic migrations
│ │ ├── connection.py
│ │ └── schemas.sql
│ ├── utils/
│ │ ├── validators.py
│ │ ├── logger.py
│ │ ├── config.py
│ │ └── helpers.py
│ └── tests/
│ ├── unit/
│ ├── integration/
│ └── fixtures/
├── scripts/
│ ├── init_db.py
│ ├── backfill_data.py
│ └── run_daily_update.py
├── config/
│ ├── config.yaml
│ ├── logging.yaml
│ └── .env.example
├── notebooks/ # Jupyter notebooks for research
│ └── factor_research.ipynb
├── docs/
│ ├── API.md
│ ├── SETUP.md
│ └── ARCHITECTURE.md
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .gitignore
├── .dockerignore
├── README.md
└── Makefile

### 2. CORE FEATURES TO IMPLEMENT

#### A. Data Infrastructure

**File: `src/core/data_ingestion/ssi_client.py`**

```python
# SSI iBoard API client with:
- Rate limiting (100 requests/minute)
- Retry logic with exponential backoff
- Error handling for API failures
- Support for: daily OHLCV, financial statements, corporate actions
- Data validation before storage
- Caching mechanism using Redis
```

**File: `src/database/models.py`**

```python
# SQLAlchemy models for:
1. DailyPrice (ticker, date, open, high, low, close, volume, adjusted_close)
2. FinancialStatement (ticker, quarter, year, revenue, profit, assets, equity, etc.)
3. FinancialRatio (ticker, date, pe, pb, roe, roa, debt_equity, etc.)
4. CorporateAction (ticker, date, action_type, ratio, adjustment_factor)
5. Factor (ticker, date, factor_name, value)
6. StockInfo (ticker, name, exchange, industry, market_cap, foreign_room)

# Include:
- Proper indexes for query optimization
- Constraints and relationships
- TimescaleDB hypertables for time-series data
```

**File: `docker/docker-compose.yml`**

```yaml
# Services:
- PostgreSQL 14 with TimescaleDB extension
- Redis for caching
- FastAPI application
- pgAdmin (optional, for development)
# Volumes for data persistence
# Environment variables configuration
# Health checks for all services
```

#### B. Corporate Actions System

**File: `src/core/corporate_actions/detector.py`**

```python
# Automatic detection of:
1. Stock splits (detect price gaps > 30% with volume spike)
2. Reverse splits
3. Bonus shares
4. Dividend payments
5. Rights issues

# Algorithm:
- Analyze price discontinuities
- Cross-reference with volume patterns
- Calculate adjustment factors
- Flag for manual review if uncertain
```

**File: `src/core/corporate_actions/adjuster.py`**

```python
# Price adjustment engine:
- Backward adjustment of historical prices
- Maintain both adjusted and unadjusted series
- Audit trail for all adjustments
- Batch adjustment capability
- Validation of adjustment accuracy
```

#### C. Factor Calculation Engine

**File: `src/core/factors/fundamental.py`**

```python
# Calculate fundamental factors:
1. Valuation: P/E, P/B, P/S, EV/EBITDA, Dividend Yield, Earnings Yield
2. Profitability: ROE, ROA, ROI, Gross Margin, Operating Margin, Net Margin
3. Leverage: Debt/Equity, Debt/Assets, Interest Coverage, Current Ratio
4. Efficiency: Asset Turnover, Inventory Turnover, Receivables Turnover
5. Growth: Revenue Growth, EPS Growth, Book Value Growth (YoY, QoQ)

# Features:
- Handle missing data gracefully
- Industry-adjusted ratios
- Percentile rankings
- Z-score normalization
```

**File: `src/core/factors/technical.py`**

```python
# Calculate technical factors:
1. Trend: SMA(5,10,20,50,200), EMA, MACD, ADX
2. Momentum: RSI, Stochastic, ROC, Williams %R
3. Volatility: Bollinger Bands, ATR, Historical Volatility
4. Volume: OBV, MFI, VWAP, Volume MA Ratio
5. Price Action: Distance from 52-week high/low, Price vs MA

# Use: pandas-ta library
# Vectorized calculations for performance
# Handle Vietnam's ±7% daily limit scenarios
```

**File: `src/core/factors/momentum.py`**

```python
# Calculate momentum factors:
1. Returns: 1-week, 1-month, 3-month, 6-month, 12-month
2. Relative strength vs VN-Index
3. New 52-week high/low indicators
4. Acceleration metrics
5. Risk-adjusted momentum (returns/volatility)

# Include:
- Skip recent 1-week for reversal effect
- Adjust for corporate actions
- Handle delisted stocks
```

#### D. Stock Screening API

**File: `src/api/routes/screening.py`**

```python
# FastAPI endpoints:

POST /api/v1/screen
{
  "filters": {
    "pe_ratio": {"min": 5, "max": 15},
    "roe": {"min": 15},
    "market_cap": {"min": 1000000000000},
    "momentum_6m": {"min": 10},
    "exchange": ["HOSE", "HNX"]
  },
  "sort_by": "roe",
  "limit": 50
}

Response: List of tickers with factor values

GET /api/v1/factors/{ticker}
# Return all factors for a specific ticker

GET /api/v1/tickers
# List all available tickers with basic info

POST /api/v1/backtest
# Run simple backtest on screening criteria
```

#### E. Configuration & Environment

**File: `config/config.yaml`**

```yaml
# Application configuration:
- Database connection strings
- API endpoints and keys
- Rate limits
- Logging levels
- Calculation parameters
- Market calendar (Vietnam holidays)
- Factor definitions
```

**File: `.env.example`**
DB_HOST=localhost
DB_PORT=5432
DB_NAME=vietnam_quant
DB_USER=postgres
DB_PASSWORD=your_password_here
REDIS_URL=redis://localhost:6379
SSI_API_KEY=your_ssi_key
LOG_LEVEL=INFO
ENVIRONMENT=development

### 3. DATA INITIALIZATION SCRIPTS

**File: `scripts/init_db.py`**

```python
# Initialize database:
1. Create all tables
2. Set up TimescaleDB hypertables
3. Create indexes
4. Load initial stock list
5. Set up foreign key constraints
```

**File: `scripts/backfill_data.py`**

```python
# Backfill historical data:
1. Fetch 5 years of daily price data for all tickers
2. Download financial statements (quarterly, last 20 quarters)
3. Calculate all factors for historical period
4. Detect and adjust for corporate actions
5. Progress tracking and error handling
6. Resumable if interrupted

# Usage: python scripts/backfill_data.py --start-date 2020-01-01 --tickers all
```

**File: `scripts/run_daily_update.py`**

```python
# Daily update job (schedule with cron):
1. Fetch previous day's OHLCV data
2. Update financial data if new quarter released
3. Detect new corporate actions
4. Recalculate factors
5. Run data quality checks
6. Send alerts if issues detected
7. Generate daily summary report

# Should complete in < 10 minutes
```

### 4. TESTING FRAMEWORK

**File: `src/tests/unit/test_factors.py`**

```python
# Unit tests for factor calculations:
- Test PE ratio calculation with edge cases
- Test ROE calculation
- Test momentum calculation
- Test technical indicators
- Test with missing data
- Test with corporate action adjustments
```

**File: `src/tests/integration/test_screening.py`**

```python
# Integration tests:
- Test full screening workflow
- Test API endpoints
- Test database queries
- Test data pipeline end-to-end
```

### 5. DOCUMENTATION

**File: `README.md`**

```markdown
# Vietnam Stock Market Quant Platform

## Quick Start

1. Clone repository
2. Copy .env.example to .env and configure
3. Run `docker-compose up -d`
4. Initialize database: `make init-db`
5. Backfill data: `make backfill-data`
6. Access API: http://localhost:8000/docs

## Features

- 1,800+ Vietnamese stocks coverage
- 50+ investment factors
- Stock screening API
- Corporate actions handling
- Historical data back to 2020

## Architecture

[Diagram and explanation]

## API Documentation

See docs/API.md
```

**File: `docs/SETUP.md`**

```markdown
# Detailed setup instructions

# System requirements

# Installation steps

# Configuration guide

# Troubleshooting
```

### 6. UTILITIES & HELPERS

**File: `src/utils/logger.py`**

```python
# Centralized logging:
- JSON structured logging
- Different log levels for different modules
- Log to file and console
- Integration with monitoring tools
```

**File: `src/utils/validators.py`**

```python
# Data validation:
- Validate price data (OHLC relationships)
- Validate financial ratios (reasonable ranges)
- Detect outliers
- Check data completeness
```

**File: `Makefile`**

```makefile
# Common commands:
init-db: Initialize database
backfill-data: Load historical data
run-api: Start API server
run-tests: Run all tests
lint: Run code linting
format: Format code with black
docker-build: Build Docker images
docker-up: Start all services
docker-down: Stop all services
```

### 7. KEY REQUIREMENTS

**Code Quality:**

- Type hints for all functions
- Docstrings (Google style)
- Error handling with custom exceptions
- Logging at appropriate levels
- Input validation
- SQL injection prevention
- Rate limiting on API endpoints

**Performance:**

- Vectorized operations with pandas/numpy
- Database query optimization
- Caching frequently accessed data
- Batch processing where possible
- Async I/O for API calls
- Connection pooling

**Vietnam Market Specifics:**

- Handle ±7% daily price limits
- T+2 settlement period
- Foreign ownership limits tracking
- Vietnamese market holidays calendar
- Three exchanges: HOSE, HNX, UPCoM
- Ticker naming conventions

**Data Quality:**

- Validation rules for all data inputs
- Automatic outlier detection
- Missing data handling strategy
- Data reconciliation between sources
- Audit trail for data modifications

### 8. INITIAL 10 FACTORS FOR MVP

Please implement these 10 factors first:

1. **PE_Ratio**: Price / Earnings Per Share (TTM)
2. **PB_Ratio**: Price / Book Value Per Share
3. **ROE**: Net Income / Shareholders' Equity (%)
4. **ROA**: Net Income / Total Assets (%)
5. **Debt_Equity**: Total Debt / Total Equity
6. **Current_Ratio**: Current Assets / Current Liabilities
7. **Momentum_6M**: 6-month price return (%)
8. **RSI_14**: 14-period Relative Strength Index
9. **Volume_MA_Ratio**: Current Volume / 20-day Average Volume
10. **Distance_52W_High**: (Current Price - 52W High) / 52W High (%)

### 9. SAMPLE DATA FOR TESTING

Please include sample data generators for testing:

- 100 sample tickers with realistic price data
- Sample financial statements
- Sample corporate actions
- Expected factor calculation results for validation

## DELIVERABLES

Please provide:

1. **Complete project structure** with all folders and files
2. **Fully functional code** for all components above
3. **docker-compose.yml** ready to run
4. **Database schema** with migrations
5. **API documentation** (OpenAPI/Swagger)
6. **Unit tests** with >80% coverage for core modules
7. **README.md** with clear setup instructions
8. **Sample .env file** with all required variables
9. **Makefile** for common operations
10. **requirements.txt** with all dependencies

## EXECUTION INSTRUCTIONS

- Use Python 3.10+ features
- Follow PEP 8 style guide
- Use Black for formatting (line length 100)
- Use FastAPI best practices
- Use SQLAlchemy 2.0 syntax
- Include comprehensive error messages
- Add TODO comments for future enhancements
- Make it easy to extend with new factors

## EXPECTED OUTPUT FORMAT

Please create the project as an artifact that includes:

1. Complete file structure visualization
2. All code files with full implementation (no placeholders)
3. Configuration files
4. Documentation files

Start with the most critical components:

- Docker setup
- Database models
- SSI API client
- Factor calculation engine
- Screening API

Then add supporting components:

- Tests
- Scripts
- Documentation
- Utilities

Make this production-ready, not a prototype. The code should be deployable immediately after adding real API credentials.
