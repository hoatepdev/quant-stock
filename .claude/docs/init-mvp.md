I'm building a Vietnam stock market quantitative analysis platform. I need to create an MVP with the following components:

1. Docker environment with PostgreSQL database
2. SSI iBoard API integration for fetching Vietnamese stock data
3. Database schema for storing:
   - Daily OHLCV price data
   - Fundamental ratios (P/E, ROE, P/B, Debt/Equity)
   - Corporate actions (splits, dividends)
4. Basic factor calculation engine (10 factors: P/E, P/B, ROE, ROA, 6-month momentum, debt/equity, current ratio, quick ratio, EPS growth, revenue growth)
5. FastAPI endpoint for stock screening with filters

Requirements:

- Python 3.10+
- Docker + docker-compose setup
- PostgreSQL with TimescaleDB extension
- Data validation and error handling
- RESTful API with /screen endpoint

Please provide:

1. Complete database schema with migrations
2. Docker setup files (Dockerfile, docker-compose.yml)
3. SSI API wrapper with rate limiting
4. Factor calculation modules
5. FastAPI application with screening logic

Focus on production-ready code with proper error handling, logging, and documentation.
