"""Stock screening endpoints."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.database.connection import get_sync_session
from src.database.models import Factor, FinancialRatio, StockInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class FilterCriteria(BaseModel):
    """Filter criteria for stock screening."""

    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")


class ScreeningRequest(BaseModel):
    """Stock screening request model."""

    filters: dict[str, FilterCriteria] = Field(
        default_factory=dict,
        description="Dictionary of factor filters",
    )
    exchanges: Optional[List[str]] = Field(
        default=None,
        description="List of exchanges (HOSE, HNX, UPCOM)",
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Factor to sort by",
    )
    sort_order: str = Field(
        default="desc",
        description="Sort order (asc or desc)",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of results",
    )


class StockScreeningResult(BaseModel):
    """Stock screening result model."""

    ticker: str
    name: str
    exchange: str
    factors: dict[str, Optional[float]]


@router.post("/screen", response_model=List[StockScreeningResult])
async def screen_stocks(
    request: ScreeningRequest,
    db: Session = Depends(get_sync_session),
) -> List[StockScreeningResult]:
    """Screen stocks based on multiple factor criteria.

    Args:
        request: Screening request with filters
        db: Database session

    Returns:
        List of stocks matching criteria with their factor values
    """
    logger.info(f"Screening stocks with filters: {request.filters}")

    # Get latest date for factor data
    latest_factor_date = (
        db.query(Factor.date)
        .order_by(Factor.date.desc())
        .first()
    )

    if not latest_factor_date:
        raise HTTPException(status_code=404, detail="No factor data available")

    latest_date = latest_factor_date[0]

    # Start with active stocks
    query = db.query(StockInfo).filter(StockInfo.is_active == True)  # noqa: E712

    # Apply exchange filter
    if request.exchanges:
        query = query.filter(StockInfo.exchange.in_(request.exchanges))

    stocks = query.all()

    # Get factors for all stocks
    results = []
    for stock in stocks:
        # Get financial ratios
        ratios = (
            db.query(FinancialRatio)
            .filter(
                FinancialRatio.ticker == stock.ticker,
                FinancialRatio.date <= latest_date,
            )
            .order_by(FinancialRatio.date.desc())
            .first()
        )

        # Get other factors
        factors_data = (
            db.query(Factor)
            .filter(
                Factor.ticker == stock.ticker,
                Factor.date == latest_date,
            )
            .all()
        )

        # Combine all factor values
        factor_values = {}

        if ratios:
            factor_values.update({
                "pe_ratio": ratios.pe_ratio,
                "pb_ratio": ratios.pb_ratio,
                "roe": ratios.roe,
                "roa": ratios.roa,
                "debt_to_equity": ratios.debt_to_equity,
                "current_ratio": ratios.current_ratio,
                "revenue_growth_yoy": ratios.revenue_growth_yoy,
                "eps_growth_yoy": ratios.eps_growth_yoy,
            })

        for factor in factors_data:
            factor_values[factor.factor_name] = factor.value

        # Apply filters
        passes_filters = True
        for factor_name, criteria in request.filters.items():
            value = factor_values.get(factor_name)

            if value is None:
                passes_filters = False
                break

            if criteria.min_value is not None and value < criteria.min_value:
                passes_filters = False
                break

            if criteria.max_value is not None and value > criteria.max_value:
                passes_filters = False
                break

        if passes_filters:
            results.append(
                StockScreeningResult(
                    ticker=stock.ticker,
                    name=stock.name,
                    exchange=stock.exchange,
                    factors=factor_values,
                )
            )

    # Sort results
    if request.sort_by and request.sort_by in (results[0].factors.keys() if results else []):
        results.sort(
            key=lambda x: x.factors.get(request.sort_by, float("-inf")),
            reverse=(request.sort_order == "desc"),
        )

    # Limit results
    results = results[:request.limit]

    logger.info(f"Screening returned {len(results)} stocks")

    return results


@router.get("/tickers", response_model=List[dict])
async def get_tickers(
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    active_only: bool = Query(True, description="Return only active stocks"),
    db: Session = Depends(get_sync_session),
) -> List[dict]:
    """Get list of all available tickers.

    Args:
        exchange: Filter by exchange (optional)
        active_only: Return only active stocks
        db: Database session

    Returns:
        List of ticker information
    """
    query = db.query(StockInfo)

    if active_only:
        query = query.filter(StockInfo.is_active == True)  # noqa: E712

    if exchange:
        query = query.filter(StockInfo.exchange == exchange.upper())

    stocks = query.all()

    return [
        {
            "ticker": stock.ticker,
            "name": stock.name,
            "exchange": stock.exchange,
            "industry": stock.industry,
            "market_cap": float(stock.market_cap) if stock.market_cap else None,
        }
        for stock in stocks
    ]
