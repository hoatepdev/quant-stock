# Vietnam Stock Market Quantitative Analysis Platform

A production-ready quantitative investment research and trading platform specifically designed for the Vietnam stock market. Analyze ~1,800 stocks across HOSE, HNX, and UPCoM exchanges using multiple investment methodologies.

## 🚀 Quick Start

Get started in 10 minutes! See [QUICKSTART.md](QUICKSTART.md)

```bash
# 1. Configure environment
cp .env.example .env
# No API keys required! Uses vnstock (free) by default
# Optional: nano .env to configure database password

# 2. Start services
make docker-up

# 3. Initialize database
make init-db

# 4. Access API
open http://localhost:8000/docs
```

## ✨ Features

- **🆓 FREE Data Source**: Uses vnstock (no API keys required!)
- **📊 Comprehensive Coverage**: 1,800+ Vietnamese stocks (HOSE, HNX, UPCoM)
- **📈 50+ Investment Factors**: Fundamental, technical, and momentum indicators
- **🔍 Advanced Screening**: Multi-factor stock screening with flexible filters
- **💰 Corporate Actions**: Pre-adjusted prices (no manual adjustments needed)
- **📅 Historical Data**: Price and financial data back to 2020
- **⚡ High Performance**: TimescaleDB optimization for time-series data
- **🐳 Production Ready**: Docker deployment with PostgreSQL + Redis

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0
- **Database**: PostgreSQL 14 + TimescaleDB
- **Cache**: Redis
- **Data Source**: vnstock (default, free, no API key needed) or SSI iBoard API
- **Data Processing**: pandas, numpy, pandas-ta
- **Deployment**: Docker, Docker Compose

## 📈 Investment Factors

### Fundamental (20+)
- Valuation: P/E, P/B, P/S, EV/EBITDA, Dividend Yield
- Profitability: ROE, ROA, ROI, Margins (Gross, Operating, Net)
- Leverage: Debt/Equity, Debt/Assets, Interest Coverage
- Liquidity: Current Ratio, Quick Ratio, Cash Ratio
- Efficiency: Asset Turnover, Inventory Turnover
- Growth: Revenue Growth, EPS Growth (YoY, QoQ)

### Technical (15+)
- Trend: SMA, EMA, MACD, ADX
- Momentum: RSI, Stochastic, Williams %R
- Volatility: Bollinger Bands, ATR
- Volume: OBV, MFI, VWAP, Volume MA Ratio
- Price Action: 52-week high/low distance

### Momentum (10+)
- Returns: 1W, 1M, 3M, 6M, 12M
- Relative Strength vs VN-Index
- Risk-Adjusted Momentum
- Price Acceleration

## 🌐 API Examples

### Screen Stocks
```bash
curl -X POST "http://localhost:8000/api/v1/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "pe_ratio": {"min": 5, "max": 15},
      "roe": {"min": 15},
      "momentum_6m": {"min": 10}
    },
    "exchanges": ["HOSE"],
    "sort_by": "roe",
    "limit": 20
  }'
```

### Get Stock Factors
```bash
curl "http://localhost:8000/api/v1/factors/VNM"
```

### List Tickers
```bash
curl "http://localhost:8000/api/v1/tickers?exchange=HOSE"
```

## 📁 Project Structure

```
vnquant/
├── src/
│   ├── api/              # FastAPI application
│   ├── core/             # Business logic
│   │   ├── factors/      # Factor calculations
│   │   ├── data_ingestion/ # Data clients
│   │   └── corporate_actions/
│   ├── database/         # SQLAlchemy models
│   ├── utils/            # Utilities
│   └── tests/            # Test suite
├── docker/               # Docker configuration
├── scripts/              # Operational scripts
├── config/               # Configuration
└── docs/                 # Documentation
```

## 🔧 Development

```bash
# Install dependencies
make install-dev

# Run tests
make run-tests

# Format code
make format

# Lint code
make lint
```

## 🇻🇳 Vietnam Market Specifics

- **±7% Daily Limits**: Handles price limit scenarios
- **T+2 Settlement**: Settlement period tracking
- **Foreign Ownership**: Limit monitoring
- **Market Holidays**: Vietnamese calendar integration
- **Three Exchanges**: HOSE, HNX, UPCoM support

## 📊 Database Models

1. **stock_info** - Stock metadata
2. **daily_price** - OHLCV data (TimescaleDB hypertable)
3. **financial_statement** - Quarterly/annual financials
4. **financial_ratio** - Calculated ratios
5. **corporate_action** - Splits, dividends
6. **factor** - Investment factors (TimescaleDB hypertable)
7. **market_index** - VN-Index, HNX-Index data
8. **data_quality_log** - Validation logs

## 🎯 Roadmap

### ✅ Phase 1 (MVP) - Complete
- Core data infrastructure
- Factor calculation engines
- Stock screening API
- Corporate actions detection
- Docker deployment

### 🔄 Phase 2 (Q1 2025)
- Backtesting framework
- Portfolio optimization  
- VNDirect API integration
- Real-time data feeds

### 📅 Phase 3 (Q2 2025)
- Machine learning models
- Sentiment analysis
- News integration
- Advanced strategies

### 🚀 Phase 4 (Q3 2025)
- Trading integration
- Risk management
- Performance attribution
- Mobile application

## 📚 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 10 minutes
- [docs/SETUP.md](docs/SETUP.md) - Detailed setup guide
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete project overview
- [TREE.txt](TREE.txt) - Project structure tree
- API Docs: http://localhost:8000/docs (after starting)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make format && make lint && make run-tests`
5. Submit a pull request

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- SSI for market data API access
- TimescaleDB for time-series optimization
- FastAPI for the excellent web framework
- Vietnamese investment community

## 📧 Support

- Documentation: See [docs/](docs/) folder
- Issues: GitHub Issues
- Email: your.email@example.com

---

**Built with ❤️ for Vietnamese quantitative investors**

**Version 0.1.0 | Production Ready**
