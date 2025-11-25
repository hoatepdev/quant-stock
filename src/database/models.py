"""SQLAlchemy models for Vietnam Quant Platform."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class StockInfo(Base):
    """Stock information and metadata."""

    __tablename__ = "stock_info"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(
        Enum("HOSE", "HNX", "UPCOM", name="exchange_enum"),
        nullable=False,
    )
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    foreign_ownership_limit: Mapped[Optional[float]] = mapped_column(Float)
    foreign_ownership_current: Mapped[Optional[float]] = mapped_column(Float)
    outstanding_shares: Mapped[Optional[int]] = mapped_column(BigInteger)
    listing_date: Mapped[Optional[date]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    delisting_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_stock_exchange", "exchange"),
        Index("idx_stock_industry", "industry"),
        Index("idx_stock_active", "is_active"),
    )


class DailyPrice(Base):
    """Daily OHLCV price data with corporate action adjustments."""

    __tablename__ = "daily_price"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    adjusted_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    adjustment_factor: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=1.0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_daily_price_ticker_date"),
        Index("idx_daily_price_ticker", "ticker"),
        Index("idx_daily_price_date", "date"),
        Index("idx_daily_price_ticker_date", "ticker", "date"),
        CheckConstraint("high >= low", name="check_high_low"),
        CheckConstraint("high >= open", name="check_high_open"),
        CheckConstraint("high >= close", name="check_high_close"),
        CheckConstraint("low <= open", name="check_low_open"),
        CheckConstraint("low <= close", name="check_low_close"),
        CheckConstraint("volume >= 0", name="check_volume_positive"),
    )


class FinancialStatement(Base):
    """Quarterly and annual financial statements."""

    __tablename__ = "financial_statement"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    report_type: Mapped[str] = mapped_column(
        Enum("Q", "Y", name="report_type_enum"), nullable=False
    )

    # Income Statement
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    gross_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    operating_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    profit_before_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    net_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    diluted_eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))

    # Balance Sheet
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    non_current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    cash_and_equivalents: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    inventory: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    receivables: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    current_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    non_current_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    short_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    long_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    total_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    share_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    retained_earnings: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # Cash Flow Statement
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    investing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    financing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "ticker", "year", "quarter", "report_type",
            name="uq_financial_statement_ticker_period"
        ),
        Index("idx_financial_statement_ticker", "ticker"),
        Index("idx_financial_statement_year_quarter", "year", "quarter"),
        CheckConstraint("quarter BETWEEN 1 AND 4", name="check_quarter_range"),
        CheckConstraint("year >= 2000", name="check_year_min"),
    )


class FinancialRatio(Base):
    """Calculated financial ratios and metrics."""

    __tablename__ = "financial_ratio"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Valuation Ratios
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ps_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ev_ebitda: Mapped[Optional[float]] = mapped_column(Float)
    dividend_yield: Mapped[Optional[float]] = mapped_column(Float)
    earnings_yield: Mapped[Optional[float]] = mapped_column(Float)

    # Profitability Ratios
    roe: Mapped[Optional[float]] = mapped_column(Float)
    roa: Mapped[Optional[float]] = mapped_column(Float)
    roi: Mapped[Optional[float]] = mapped_column(Float)
    gross_margin: Mapped[Optional[float]] = mapped_column(Float)
    operating_margin: Mapped[Optional[float]] = mapped_column(Float)
    net_margin: Mapped[Optional[float]] = mapped_column(Float)

    # Leverage Ratios
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Float)
    debt_to_assets: Mapped[Optional[float]] = mapped_column(Float)
    interest_coverage: Mapped[Optional[float]] = mapped_column(Float)

    # Liquidity Ratios
    current_ratio: Mapped[Optional[float]] = mapped_column(Float)
    quick_ratio: Mapped[Optional[float]] = mapped_column(Float)
    cash_ratio: Mapped[Optional[float]] = mapped_column(Float)

    # Efficiency Ratios
    asset_turnover: Mapped[Optional[float]] = mapped_column(Float)
    inventory_turnover: Mapped[Optional[float]] = mapped_column(Float)
    receivables_turnover: Mapped[Optional[float]] = mapped_column(Float)

    # Growth Rates
    revenue_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)
    revenue_growth_qoq: Mapped[Optional[float]] = mapped_column(Float)
    eps_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)
    eps_growth_qoq: Mapped[Optional[float]] = mapped_column(Float)
    book_value_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_financial_ratio_ticker_date"),
        Index("idx_financial_ratio_ticker", "ticker"),
        Index("idx_financial_ratio_date", "date"),
        Index("idx_financial_ratio_ticker_date", "ticker", "date"),
    )


class CorporateAction(Base):
    """Corporate actions (splits, dividends, bonus shares, etc.)."""

    __tablename__ = "corporate_action"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    ex_date: Mapped[date] = mapped_column(Date, nullable=False)
    action_type: Mapped[str] = mapped_column(
        Enum(
            "SPLIT",
            "REVERSE_SPLIT",
            "DIVIDEND",
            "BONUS_SHARE",
            "RIGHTS_ISSUE",
            name="action_type_enum"
        ),
        nullable=False,
    )
    ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    dividend_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    adjustment_factor: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detection_method: Mapped[Optional[str]] = mapped_column(
        Enum("AUTOMATIC", "MANUAL", "API", name="detection_method_enum")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        Index("idx_corporate_action_ticker", "ticker"),
        Index("idx_corporate_action_ex_date", "ex_date"),
        Index("idx_corporate_action_type", "action_type"),
        Index("idx_corporate_action_applied", "is_applied"),
    )


class Factor(Base):
    """Calculated investment factors."""

    __tablename__ = "factor"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    factor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Optional[float]] = mapped_column(Float)
    zscore: Mapped[Optional[float]] = mapped_column(Float)
    percentile: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "ticker", "date", "factor_name",
            name="uq_factor_ticker_date_name"
        ),
        Index("idx_factor_ticker", "ticker"),
        Index("idx_factor_date", "date"),
        Index("idx_factor_name", "factor_name"),
        Index("idx_factor_ticker_date", "ticker", "date"),
    )


class MarketIndex(Base):
    """Market index data (VN-Index, HNX-Index, UPCoM-Index)."""

    __tablename__ = "market_index"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    index_name: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("index_name", "date", name="uq_market_index_name_date"),
        Index("idx_market_index_name", "index_name"),
        Index("idx_market_index_date", "date"),
    )


class DataQualityLog(Base):
    """Data quality checks and validation logs."""

    __tablename__ = "data_quality_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    check_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("PASS", "FAIL", "WARNING", name="status_enum"),
        nullable=False,
    )
    message: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[Optional[str]] = mapped_column(Text)
    affected_records: Mapped[Optional[int]] = mapped_column(Integer)

    __table_args__ = (
        Index("idx_data_quality_date", "check_date"),
        Index("idx_data_quality_table", "table_name"),
        Index("idx_data_quality_status", "status"),
    )
