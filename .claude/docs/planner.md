Vietnam Stock Market Investment Research & Quant Platform – Full Project Planner
A. PROJECT OVERVIEW
Project Purpose
Develop a comprehensive investment research framework and quantitative trading platform specifically tailored for the Vietnam stock market, enabling systematic analysis across multiple investment methodologies to identify alpha-generating opportunities in HOSE, HNX, and UPCoM exchanges.
Scope of Research

Coverage: All listed securities on Vietnamese exchanges (~1,800 tickers)
Methodologies: Seven core investment approaches (FA, TA, Quant, Macro, Behavioral, Event, Flow)
Time Horizons: Intraday to multi-year investment strategies
Asset Classes: Equities, ETFs, covered warrants, bonds (secondary focus)
Data Sources: SSI iBoard, VNDIRECT, DNSE, FiinPro, Cafef, VietStock
Research Output: Actionable investment signals, systematic strategies, risk models

Out-of-Scope (Optional)

Derivatives trading (futures/options not available in Vietnam)
Cryptocurrency integration
Real-time HFT systems (sub-second execution)
Regulatory compliance automation
Client portfolio management features

Key Assumptions

SSI free API maintains 99% uptime with consistent data quality
Historical data available from 2000 onwards for major tickers
Team has basic Vietnamese language capability for local news analysis
Foreign ownership limits data accessible via public sources
Market microstructure remains stable (T+2 settlement, ±7% daily limits)

Risks & Mitigations
RiskImpactProbabilityMitigationSSI API changes/deprecationHighMediumImplement abstraction layer, maintain backup data sourcesData quality issuesHighHighBuild validation pipeline, cross-reference multiple sourcesRegulatory changesMediumLowMonitor VSD/SSC announcements, flexible architectureTeam knowledge gapsMediumMediumWeekly learning sessions, external consultation budgetInfrastructure limitationsLowMediumOptimize data storage, implement caching strategies
B. HIGH-LEVEL ROADMAP (6 MONTHS)
Phase 1: Research Foundation (Weeks 1-4)

Set up data infrastructure and ingestion pipelines
Establish research documentation framework
Complete MVP quant platform with screening capabilities
Define investment universe and classification system

Phase 2: Data & Tools Setup (Weeks 5-8)

Build comprehensive data warehouse with 10+ years history
Implement corporate actions adjustment system
Create research toolkit libraries
Establish backtesting framework foundation

Phase 3: Methodology Development (Weeks 9-12)

Develop factor models for each investment approach
Create signal generation systems
Build portfolio construction frameworks
Implement risk management models

Phase 4: Backtesting & Validation (Weeks 13-16)

Conduct historical backtests across all strategies
Perform walk-forward analysis
Validate against out-of-sample data
Optimize strategy parameters

Phase 5: Reporting & Dashboard (Weeks 17-20)

Build automated reporting systems
Create interactive dashboards
Develop alert mechanisms
Implement performance attribution

Phase 6: Final Optimization (Weeks 21-24)

Refine strategies based on results
Implement ensemble methods
Optimize execution algorithms
Complete documentation and training materials

C. DETAILED WORK BREAKDOWN STRUCTURE (WBS)

1. Fundamental Analysis (FA)
   Objectives

Build comprehensive financial statement database
Develop valuation models for Vietnamese market context
Create peer comparison frameworks
Identify value opportunities with margin of safety

Detailed Tasks

Scrape and parse financial statements from SSI/VNDIRECT
Calculate 50+ fundamental ratios (P/E, P/B, ROE, ROA, debt ratios)
Build DCF models with Vietnam-specific assumptions
Create industry classification mapping (ICB to local standards)
Develop earnings quality scoring system
Build peer group selection algorithm
Create FA factor library (value, quality, profitability)

Required Tools

Financial data APIs (SSI iBoard, FiinPro)
Python libraries: pandas, numpy, scipy
Database: PostgreSQL with time-series extensions
Visualization: Plotly, Seaborn

Expected Outputs

Automated fundamental screening system
Company valuation reports
Sector comparison matrices
Value score rankings
Financial health indicators

Dependencies

Clean financial data pipeline
Industry classification system
Macro economic indicators

2. Technical Analysis (TA)
   Objectives

Implement comprehensive technical indicator library
Develop pattern recognition systems
Create multi-timeframe analysis framework
Build price action signal generators

Detailed Tasks

Calculate 100+ technical indicators (MA, RSI, MACD, Bollinger)
Implement chart pattern detection (head-shoulders, triangles, flags)
Build candlestick pattern recognition
Develop support/resistance identification algorithms
Create volume profile analysis
Implement market breadth indicators
Build TA signal aggregation system

Required Tools

TA libraries: ta-lib, pandas-ta
Charting: TradingView widgets, Plotly
Pattern recognition: ML libraries (scikit-learn)
Real-time data feeds

Expected Outputs

Daily technical signals report
Pattern alert system
Technical scoring dashboard
Trend strength indicators
Entry/exit signal generator

Dependencies

High-quality OHLCV data
Real-time price feeds
Historical data for pattern training

3. Quantitative Research (Quant)
   Objectives

Develop systematic factor models
Build statistical arbitrage strategies
Create risk models and portfolio optimization
Implement machine learning predictive models

Detailed Tasks

Build 100+ alpha factors (momentum, mean-reversion, quality)
Develop factor combination frameworks
Create factor decay analysis
Implement Fama-French models for Vietnam
Build pairs trading algorithms
Develop volatility forecasting models
Create portfolio optimization engines
Implement risk parity strategies

Required Tools

Quantitative libraries: zipline, backtrader, vectorbt
ML frameworks: scikit-learn, XGBoost, LightGBM
Statistical packages: statsmodels, arch
Optimization: cvxpy, scipy.optimize

Expected Outputs

Factor performance reports
Strategy backtest results
Risk decomposition analysis
Portfolio allocation recommendations
Signal strength indicators

Dependencies

Clean, adjusted price data
Fundamental data for factor creation
Market microstructure data

4. Macro Analysis (Top-down)
   Objectives

Track Vietnam economic indicators
Analyze sector rotation patterns
Monitor global macro impacts
Develop regime detection models

Detailed Tasks

Build economic indicator dashboard (GDP, inflation, FDI)
Create sector performance tracking
Develop currency impact analysis (USD/VND effects)
Monitor government bond yields
Track foreign flow patterns
Build business cycle indicators
Create regime-switching models

Required Tools

Economic data: GSO, SBV, Bloomberg
Sector ETFs tracking
Correlation analysis tools
Time-series forecasting libraries

Expected Outputs

Monthly macro reports
Sector allocation recommendations
Economic regime indicators
Currency hedging signals
Risk-on/risk-off indicators

Dependencies

Reliable economic data feeds
Sector classification system
Global market data

5. Behavioral Finance
   Objectives

Identify market sentiment patterns
Detect behavioral anomalies
Build crowd psychology indicators
Develop contrarian signals

Detailed Tasks

Scrape and analyze VN stock forums/social media
Build news sentiment analysis (Vietnamese NLP)
Track retail vs institutional behavior
Monitor foreign room utilization patterns
Develop put/call ratio equivalents
Create fear/greed indicators
Build herding behavior detection

Required Tools

NLP libraries: underthesea, pyvi
Sentiment analysis: VADER adapted for Vietnamese
Web scraping: BeautifulSoup, Selenium
Social media APIs

Expected Outputs

Daily sentiment scores
Behavioral bias alerts
Crowd positioning indicators
Contrarian opportunity signals
Sentiment divergence reports

Dependencies

Vietnamese text processing capability
Social media data access
News feed aggregation

6. Event-based Trading
   Objectives

Systematically track corporate events
Quantify event impacts
Build event arbitrage strategies
Create event calendars

Detailed Tasks

Monitor dividend announcements
Track stock splits/bonuses
Detect M&A activity
Follow earnings surprises
Track foreign room changes
Monitor index rebalancing
Build event impact models

Required Tools

Corporate action feeds
News monitoring systems
Event databases
Statistical event studies

Expected Outputs

Event calendar dashboard
Pre/post event analysis
Event arbitrage signals
Corporate action alerts
Historical event impact database

Dependencies

Real-time news feeds
Corporate disclosure monitoring
Historical event database

7. Market Flow Analysis
   Objectives

Track money flows across markets
Monitor liquidity patterns
Analyze order flow dynamics
Detect accumulation/distribution

Detailed Tasks

Build foreign flow tracking system
Analyze proprietary trading patterns
Create volume-price analysis
Monitor block trades
Track ETF flows
Develop liquidity indicators
Build market microstructure models

Required Tools

Level 2 data (if available)
Volume analysis tools
Flow calculation libraries
Market depth analytics

Expected Outputs

Daily flow reports
Liquidity heat maps
Smart money indicators
Accumulation signals
Market breadth dashboard

Dependencies

Detailed transaction data
Foreign/local investor classification
Real-time volume data

D. DELIVERABLES LIST
Core Systems

Integrated Stock Screening Platform

Multi-factor screening interface
Saved screen templates
Real-time and historical screening
Export capabilities

Fundamental Analysis Suite

Automated valuation models
Peer comparison tools
Financial health scorecards
Earnings forecast tracker

Technical Analysis Toolkit

Pattern recognition scanner
Multi-timeframe analyzer
Signal strength dashboard
Backtested strategy library

Quantitative Strategy Framework

Factor model library (50+ factors)
Portfolio optimization engine
Risk management system
Performance attribution tools

Macro Dashboard

Economic indicator tracker
Sector rotation monitor
Regime detection system
Global correlation matrix

Research Documentation

Strategy white papers
Factor definitions catalog
Backtesting methodology guide
Risk management framework

Reporting Infrastructure

Daily market summary
Weekly strategy performance
Monthly factor review
Quarterly strategy rebalancing

Supporting Tools

Data Quality Monitor
Corporate Actions Adjuster
Alert & Notification System
Performance Analytics Suite
Strategy Backtesting Engine

E. WEEKLY PLANNER (24 WEEKS)
Month 1: Foundation
Week 1

Goals: Data infrastructure setup, team alignment
Tasks: SSI API integration, PostgreSQL setup, Docker configuration
Outputs: Working data pipeline, project wiki
Time: 40 hours
Priority: Critical

Week 2

Goals: Historical data collection, research framework
Tasks: Bulk data download, database schema design, documentation setup
Outputs: 5-year historical database, research templates
Time: 40 hours
Priority: Critical

Week 3

Goals: MVP platform core development
Tasks: Factor calculation engine, screening logic, API development
Outputs: 10 basic factors, screening endpoint
Time: 40 hours
Priority: Critical

Week 4

Goals: MVP completion and testing
Tasks: Integration testing, performance optimization, documentation
Outputs: Working MVP with screening capabilities
Time: 40 hours
Priority: Critical

Month 2: Data Excellence
Week 5

Goals: Comprehensive data collection
Tasks: Multi-source integration, validation rules, quality checks
Outputs: Unified data model, quality reports
Time: 35 hours
Priority: High

Week 6

Goals: Corporate actions handling
Tasks: Split detection, dividend adjustment, rights issue processing
Outputs: Adjusted price series, corporate action log
Time: 35 hours
Priority: High

Week 7

Goals: Fundamental data processing
Tasks: Financial statement parsing, ratio calculations, peer mapping
Outputs: Fundamental database, ratio library
Time: 40 hours
Priority: High

Week 8

Goals: Technical indicator implementation
Tasks: TA library integration, custom indicators, pattern detection
Outputs: 50+ technical indicators, pattern scanner
Time: 35 hours
Priority: Medium

Month 3: Strategy Development
Week 9

Goals: Factor model development
Tasks: Alpha factor creation, factor testing, correlation analysis
Outputs: 30+ alpha factors, factor performance metrics
Time: 40 hours
Priority: High

Week 10

Goals: Value strategy implementation
Tasks: Value factor combinations, screening rules, backtesting
Outputs: Value strategy v1, backtest results
Time: 35 hours
Priority: High

Week 11

Goals: Momentum strategy development
Tasks: Momentum factors, timing rules, risk controls
Outputs: Momentum strategy v1, performance analysis
Time: 35 hours
Priority: High

Week 12

Goals: Mean reversion strategies
Tasks: Pairs identification, cointegration tests, entry/exit rules
Outputs: Pairs trading system, statistical arbitrage signals
Time: 40 hours
Priority: Medium

Month 4: Backtesting & Validation
Week 13

Goals: Backtesting framework completion
Tasks: Engine optimization, slippage modeling, transaction costs
Outputs: Robust backtesting system, cost models
Time: 40 hours
Priority: Critical

Week 14

Goals: Strategy validation
Tasks: Walk-forward analysis, out-of-sample testing, parameter stability
Outputs: Validation reports, confidence intervals
Time: 35 hours
Priority: High

Week 15

Goals: Risk model development
Tasks: VaR calculations, stress testing, correlation analysis
Outputs: Risk management framework, risk reports
Time: 35 hours
Priority: High

Week 16

Goals: Portfolio optimization
Tasks: Markowitz optimization, risk parity, position sizing
Outputs: Portfolio construction tools, allocation models
Time: 40 hours
Priority: High

Month 5: Visualization & Reporting
Week 17

Goals: Dashboard development
Tasks: KPI dashboards, performance charts, factor monitors
Outputs: Interactive dashboard v1
Time: 40 hours
Priority: Medium

Week 18

Goals: Automated reporting
Tasks: Report templates, scheduling, distribution system
Outputs: Daily/weekly/monthly reports
Time: 35 hours
Priority: Medium

Week 19

Goals: Alert system implementation
Tasks: Signal alerts, threshold monitoring, notification channels
Outputs: Multi-channel alert system
Time: 30 hours
Priority: Medium

Week 20

Goals: Performance attribution
Tasks: Return decomposition, factor attribution, benchmarking
Outputs: Attribution analysis tools
Time: 35 hours
Priority: Low

Month 6: Optimization & Deployment
Week 21

Goals: Strategy refinement
Tasks: Parameter optimization, ensemble methods, regime filters
Outputs: Optimized strategy suite
Time: 40 hours
Priority: High

Week 22

Goals: Execution optimization
Tasks: Order routing, execution algorithms, slippage reduction
Outputs: Execution framework v2
Time: 35 hours
Priority: Medium

Week 23

Goals: Documentation completion
Tasks: User guides, API documentation, strategy papers
Outputs: Complete documentation package
Time: 30 hours
Priority: Low

Week 24

Goals: Final testing and handover
Tasks: System stress testing, knowledge transfer, training
Outputs: Production-ready system, trained team
Time: 35 hours
Priority: High

F. KPIs FOR SUCCESS
Research Quality Metrics

Data Coverage: >95% of listed tickers with complete data
Data Accuracy: <0.1% error rate in price/volume data
Factor Coverage: 100+ unique alpha factors developed
Strategy Count: 10+ production-ready strategies
Documentation Score: >90% coverage of all components

Strategy Performance Metrics

Sharpe Ratio: >1.5 for flagship strategies
Win Rate: >55% for momentum strategies, >60% for mean reversion
Profit Factor: >1.8 across all strategies
Maximum Drawdown: <15% for conservative strategies, <25% for aggressive
Recovery Time: <3 months from drawdown trough
Alpha Generation: >10% annualized vs VN-Index
Information Ratio: >0.8 for factor portfolios

Process Metrics

Task Completion Rate: >90% on-time delivery
Code Coverage: >80% unit test coverage
System Uptime: >99.5% availability
Data Freshness: <1 hour delay for EOD data
Bug Resolution: <24 hours for critical issues
Documentation Quality: Updated within 48 hours of changes

G. TOOLS & TECH STACK RECOMMENDATION
Data Sources & APIs

Primary: SSI iBoard API (free tier)
Secondary: VNDIRECT API, DNSE DataFeed
Alternative: VietStock, CafeF, VnEconomy
Fundamental: FiinPro (if budget allows)
News: VnExpress API, CafeF RSS feeds

Development & Research

Languages: Python 3.10+, SQL, JavaScript (dashboards)
IDEs: VS Code, Jupyter Lab
Version Control: Git with GitLab/GitHub
Documentation: Notion for research, Sphinx for code
Collaboration: Slack, Jira for task management

Data Infrastructure

Database: PostgreSQL 14+ with TimescaleDB extension
Cache: Redis for real-time data
Message Queue: RabbitMQ for event processing
Container: Docker + docker-compose
Data Processing: Apache Airflow for orchestration

Analytics & Computation

Data Manipulation: pandas, numpy, polars
Statistical: statsmodels, scipy, arch
Machine Learning: scikit-learn, XGBoost, LightGBM
Backtesting: vectorbt, backtrader, custom framework
Optimization: cvxpy, scipy.optimize

Visualization & Reporting

Dashboards: Streamlit, Dash, or Grafana
Charts: Plotly, Matplotlib, Seaborn
Business Intelligence: Apache Superset (open-source)
Reports: Python + Jinja2 templates → PDF

Vietnamese-Specific Tools

NLP: underthesea, pyvi for sentiment analysis
Calendar: Vietnamese market calendar library
Broker Integration: SSI/VNDIRECT SDK if available

H. WORKFLOW DIAGRAM (TEXT-BASED)
Research Workflow
Market Data Sources → Data Ingestion Pipeline → Data Warehouse
↓
Quality Checks & Validation
↓
┌────────────────┴────────────────┐
↓ ↓
Historical DB Real-time Cache
↓ ↓
Research Tools ← ─ ─ ─ ─ ─ ─ ─ ─ → Screening Tools
↓ ↓
Factor Models Signal Generation
↓ ↓
Backtesting Live Monitoring
↓ ↓
Optimization Alerts
↓ ↓
Strategy Selection ← ─ ─ ─ ─ → Risk Management
↓
Portfolio Construction
↓
Execution Orders
Data Processing Pipeline
Raw Data → Validation → Cleaning → Adjustment → Storage
↑ ↓ ↓ ↓ ↓
| Errors Outliers Splits PostgreSQL
| ↓ ↓ ↓ ↓
└──────── Logs ──── Quality Report ────→ Monitoring
Strategy Development Cycle
Hypothesis → Research → Factor Design → Testing → Validation
↑ ↓ ↓ ↓ ↓
| Literature Engineering Backtest Forward Test
| ↓ ↓ ↓ ↓
└───── Analysis ← Optimization ← Results ← Performance
↓
Production Deploy

MVP QUANT PLATFORM – 4 WEEK DAILY PLANNER
Week 1

Day 1: Setup Docker environment, PostgreSQL container config [DE]
Day 2: Design database schema for prices, fundamentals, corporate actions [DE]
Day 3: Implement SSI iBoard API client wrapper [DEV]
Day 4: Build EOD data fetcher for all tickers [DEV]
Day 5: Create data validation and error handling [DE]

Week 2

Day 6: Implement corporate action detection logic [QA]
Day 7: Build stock-split identification algorithm [DEV]
Day 8: Create split adjustment calculation engine [DEV]
Day 9: Design factor calculation framework [QA]
Day 10: Implement PE ratio calculation [DEV]

Week 3

Day 11: Implement ROE calculation [DEV]
Day 12: Build 6-month momentum calculator [DEV]
Day 13: Add 7 more basic factors (P/B, debt/equity, etc.) [DEV]
Day 14: Create factor storage and retrieval system [DE]
Day 15: Build FastAPI application structure [DEV]

Week 4

Day 16: Implement /screen endpoint with filtering logic [DEV]
Day 17: Add query optimization for screening [DE]
Day 18: Create docker-compose orchestration file [DE]
Day 19: Internal testing - data ingestion and factors [QA]
Day 20: Internal testing - API endpoint and integration [QA]
