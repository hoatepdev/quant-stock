"""Factor data endpoints."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.connection import get_sync_session
from src.database.models import Factor, FinancialRatio
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class FactorValue(BaseModel):
    """Factor value model."""

    date: date
    factor_name: str
    value: Optional[float]
    zscore: Optional[float]
    percentile: Optional[float]


class TickerFactors(BaseModel):
    """All factors for a ticker."""

    ticker: str
    date: date
    factors: dict[str, Optional[float]]


@router.get("/factors/{ticker}", response_model=TickerFactors)
async def get_ticker_factors(
    ticker: str = Path(..., description="Stock ticker symbol"),
    as_of_date: Optional[date] = Query(None, description="Date for factor values"),
    db: Session = Depends(get_sync_session),
) -> TickerFactors:
    """Get all factor values for a specific ticker.

    Args:
        ticker: Stock ticker symbol
        as_of_date: Date for factor values (default: latest)
        db: Database session

    Returns:
        All factor values for the ticker
    """
    ticker = ticker.upper()

    # Determine date to use
    if as_of_date is None:
        latest_factor = (
            db.query(Factor.date)
            .filter(Factor.ticker == ticker)
            .order_by(Factor.date.desc())
            .first()
        )

        if not latest_factor:
            raise HTTPException(
                status_code=404,
                detail=f"No factor data found for ticker {ticker}",
            )

        as_of_date = latest_factor[0]

    # Get financial ratios
    ratios = (
        db.query(FinancialRatio)
        .filter(
            FinancialRatio.ticker == ticker,
            FinancialRatio.date <= as_of_date,
        )
        .order_by(FinancialRatio.date.desc())
        .first()
    )

    # Get other factors
    factors = (
        db.query(Factor)
        .filter(
            Factor.ticker == ticker,
            Factor.date == as_of_date,
        )
        .all()
    )

    # Combine all factors
    all_factors = {}

    if ratios:
        all_factors.update({
            "pe_ratio": ratios.pe_ratio,
            "pb_ratio": ratios.pb_ratio,
            "ps_ratio": ratios.ps_ratio,
            "roe": ratios.roe,
            "roa": ratios.roa,
            "roi": ratios.roi,
            "gross_margin": ratios.gross_margin,
            "operating_margin": ratios.operating_margin,
            "net_margin": ratios.net_margin,
            "debt_to_equity": ratios.debt_to_equity,
            "debt_to_assets": ratios.debt_to_assets,
            "current_ratio": ratios.current_ratio,
            "quick_ratio": ratios.quick_ratio,
            "asset_turnover": ratios.asset_turnover,
            "revenue_growth_yoy": ratios.revenue_growth_yoy,
            "revenue_growth_qoq": ratios.revenue_growth_qoq,
            "eps_growth_yoy": ratios.eps_growth_yoy,
            "eps_growth_qoq": ratios.eps_growth_qoq,
            "dividend_yield": ratios.dividend_yield,
            "earnings_yield": ratios.earnings_yield,
        })

    for factor in factors:
        all_factors[factor.factor_name] = factor.value

    if not all_factors:
        raise HTTPException(
            status_code=404,
            detail=f"No factor data found for ticker {ticker} on {as_of_date}",
        )

    return TickerFactors(
        ticker=ticker,
        date=as_of_date,
        factors=all_factors,
    )


@router.get("/factors/{ticker}/history", response_model=List[FactorValue])
async def get_factor_history(
    ticker: str = Path(..., description="Stock ticker symbol"),
    factor_name: str = Query(..., description="Name of the factor"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_sync_session),
) -> List[FactorValue]:
    """Get historical values for a specific factor.

    Args:
        ticker: Stock ticker symbol
        factor_name: Name of the factor
        start_date: Start date (optional)
        end_date: End date (optional)
        db: Database session

    Returns:
        Historical factor values
    """
    ticker = ticker.upper()

    query = db.query(Factor).filter(
        Factor.ticker == ticker,
        Factor.factor_name == factor_name,
    )

    if start_date:
        query = query.filter(Factor.date >= start_date)

    if end_date:
        query = query.filter(Factor.date <= end_date)

    factors = query.order_by(Factor.date).all()

    if not factors:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for factor {factor_name} on ticker {ticker}",
        )

    return [
        FactorValue(
            date=f.date,
            factor_name=f.factor_name,
            value=f.value,
            zscore=f.zscore,
            percentile=f.percentile,
        )
        for f in factors
    ]


@router.get("/factors/available", response_model=List[str])
async def get_available_factors(
    db: Session = Depends(get_sync_session),
) -> List[str]:
    """Get list of all available factor names.

    Args:
        db: Database session

    Returns:
        List of factor names
    """
    # Get unique factor names from Factor table
    factor_names = (
        db.query(Factor.factor_name)
        .distinct()
        .all()
    )

    # Add financial ratio fields
    ratio_fields = [
        "pe_ratio", "pb_ratio", "ps_ratio", "roe", "roa", "roi",
        "gross_margin", "operating_margin", "net_margin",
        "debt_to_equity", "debt_to_assets", "current_ratio", "quick_ratio",
        "asset_turnover", "revenue_growth_yoy", "revenue_growth_qoq",
        "eps_growth_yoy", "eps_growth_qoq", "dividend_yield", "earnings_yield",
    ]

    all_factors = [name[0] for name in factor_names] + ratio_fields

    return sorted(set(all_factors))
