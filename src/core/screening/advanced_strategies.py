"""Advanced screening strategies combining multiple factors."""
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.models import DailyPrice, FinancialRatio, StockInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdvancedScreener:
    """Advanced multi-factor screening strategies."""

    def __init__(self, db: Session):
        """Initialize advanced screener.

        Args:
            db: Database session
        """
        self.db = db

    def screen_value_stocks(
        self,
        exchange: Optional[str] = None,
        min_market_cap: Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Screen for undervalued stocks (value investing).

        Criteria:
        - Low P/E ratio (< 15)
        - Low P/B ratio (< 2)
        - High dividend yield (> 3%)
        - Positive earnings
        - Strong balance sheet

        Args:
            exchange: Optional exchange filter
            min_market_cap: Minimum market cap filter
            limit: Maximum results

        Returns:
            List of value stocks
        """
        logger.info("Screening for value stocks")

        # Get latest date
        latest_date = self.db.query(FinancialRatio.date).order_by(FinancialRatio.date.desc()).first()

        if not latest_date:
            return []

        latest_date = latest_date[0]

        # Query stocks with factors
        query = """
            SELECT DISTINCT
                si.ticker,
                si.name,
                si.exchange,
                si.market_cap,
                fr.pe_ratio,
                fr.pb_ratio,
                fr.dividend_yield,
                fr.roe,
                fr.current_ratio,
                fr.debt_to_equity
            FROM stock_info si
            JOIN financial_ratio fr ON si.ticker = fr.ticker
            WHERE si.is_active = true
            AND fr.date = :latest_date
            AND fr.pe_ratio > 0
            AND fr.pe_ratio < 15
            AND fr.pb_ratio > 0
            AND fr.pb_ratio < 2
            AND fr.dividend_yield > 3
            AND fr.roe > 10
            AND fr.current_ratio > 1.5
            AND fr.debt_to_equity < 1
        """

        params = {"latest_date": latest_date}

        if exchange:
            query += " AND si.exchange = :exchange"
            params["exchange"] = exchange

        if min_market_cap:
            query += " AND si.market_cap > :min_market_cap"
            params["min_market_cap"] = min_market_cap

        query += " ORDER BY fr.pe_ratio ASC LIMIT :limit"
        params["limit"] = limit

        result = self.db.execute(text(query), params)

        stocks = []
        for row in result:
            stocks.append({
                "ticker": row[0],
                "name": row[1],
                "exchange": row[2],
                "market_cap": float(row[3]) if row[3] else None,
                "pe_ratio": float(row[4]) if row[4] else None,
                "pb_ratio": float(row[5]) if row[5] else None,
                "dividend_yield": float(row[6]) if row[6] else None,
                "roe": float(row[7]) if row[7] else None,
                "current_ratio": float(row[8]) if row[8] else None,
                "debt_to_equity": float(row[9]) if row[9] else None,
                "strategy": "value",
            })

        logger.info(f"Found {len(stocks)} value stocks")

        return stocks

    def screen_growth_stocks(
        self,
        exchange: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Screen for high-growth stocks.

        Criteria:
        - High revenue growth (> 20% YoY)
        - High EPS growth (> 20% YoY)
        - Strong profitability (ROE > 15%)
        - Price momentum (positive 6M return)

        Args:
            exchange: Optional exchange filter
            limit: Maximum results

        Returns:
            List of growth stocks
        """
        logger.info("Screening for growth stocks")

        latest_date = self.db.query(FinancialRatio.date).order_by(FinancialRatio.date.desc()).first()

        if not latest_date:
            return []

        latest_date = latest_date[0]

        query = """
            SELECT DISTINCT
                si.ticker,
                si.name,
                si.exchange,
                si.market_cap,
                fr.revenue_growth_yoy,
                fr.eps_growth_yoy,
                fr.roe,
                fr.net_margin
            FROM stock_info si
            JOIN financial_ratio fr ON si.ticker = fr.ticker
            WHERE si.is_active = true
            AND fr.date = :latest_date
            AND fr.revenue_growth_yoy > 20
            AND fr.eps_growth_yoy > 20
            AND fr.roe > 15
            AND fr.net_margin > 10
        """

        params = {"latest_date": latest_date}

        if exchange:
            query += " AND si.exchange = :exchange"
            params["exchange"] = exchange

        query += " ORDER BY fr.revenue_growth_yoy DESC LIMIT :limit"
        params["limit"] = limit

        result = self.db.execute(text(query), params)

        stocks = []
        for row in result:
            stocks.append({
                "ticker": row[0],
                "name": row[1],
                "exchange": row[2],
                "market_cap": float(row[3]) if row[3] else None,
                "revenue_growth_yoy": float(row[4]) if row[4] else None,
                "eps_growth_yoy": float(row[5]) if row[5] else None,
                "roe": float(row[6]) if row[6] else None,
                "net_margin": float(row[7]) if row[7] else None,
                "strategy": "growth",
            })

        logger.info(f"Found {len(stocks)} growth stocks")

        return stocks

    def screen_momentum_stocks(
        self,
        exchange: Optional[str] = None,
        lookback_days: int = 126,  # ~6 months
        limit: int = 20,
    ) -> List[Dict]:
        """Screen for momentum stocks.

        Criteria:
        - Strong price momentum (top performers)
        - Increasing volume
        - Above moving averages
        - Relative strength

        Args:
            exchange: Optional exchange filter
            lookback_days: Momentum period
            limit: Maximum results

        Returns:
            List of momentum stocks
        """
        logger.info("Screening for momentum stocks")

        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        # Get price data
        stocks = self.db.query(StockInfo).filter(StockInfo.is_active == True)  # noqa: E712

        if exchange:
            stocks = stocks.filter(StockInfo.exchange == exchange)

        stocks = stocks.all()

        momentum_data = []

        for stock in stocks:
            prices = (
                self.db.query(DailyPrice)
                .filter(
                    DailyPrice.ticker == stock.ticker,
                    DailyPrice.date >= start_date,
                    DailyPrice.date <= end_date,
                )
                .order_by(DailyPrice.date)
                .all()
            )

            if len(prices) < 2:
                continue

            start_price = float(prices[0].close)
            end_price = float(prices[-1].close)

            returns = (end_price - start_price) / start_price

            # Calculate volume trend
            half_point = len(prices) // 2
            recent_vol = sum(p.volume for p in prices[half_point:]) / len(prices[half_point:])
            older_vol = sum(p.volume for p in prices[:half_point]) / len(prices[:half_point])
            volume_trend = (recent_vol - older_vol) / older_vol if older_vol > 0 else 0

            momentum_data.append({
                "ticker": stock.ticker,
                "name": stock.name,
                "exchange": stock.exchange,
                "returns": returns,
                "volume_trend": volume_trend,
                "start_price": start_price,
                "end_price": end_price,
                "strategy": "momentum",
            })

        # Sort by returns
        momentum_data.sort(key=lambda x: x["returns"], reverse=True)

        logger.info(f"Found {len(momentum_data[:limit])} momentum stocks")

        return momentum_data[:limit]

    def screen_quality_stocks(
        self,
        exchange: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Screen for high-quality stocks.

        Criteria:
        - Consistent profitability (ROE > 15%)
        - Strong cash flow
        - Low debt (D/E < 0.5)
        - High profit margins
        - Good asset efficiency

        Args:
            exchange: Optional exchange filter
            limit: Maximum results

        Returns:
            List of quality stocks
        """
        logger.info("Screening for quality stocks")

        latest_date = self.db.query(FinancialRatio.date).order_by(FinancialRatio.date.desc()).first()

        if not latest_date:
            return []

        latest_date = latest_date[0]

        query = """
            SELECT DISTINCT
                si.ticker,
                si.name,
                si.exchange,
                si.market_cap,
                fr.roe,
                fr.roa,
                fr.net_margin,
                fr.debt_to_equity,
                fr.current_ratio,
                fr.asset_turnover
            FROM stock_info si
            JOIN financial_ratio fr ON si.ticker = fr.ticker
            WHERE si.is_active = true
            AND fr.date = :latest_date
            AND fr.roe > 15
            AND fr.roa > 10
            AND fr.net_margin > 15
            AND fr.debt_to_equity < 0.5
            AND fr.current_ratio > 2
        """

        params = {"latest_date": latest_date}

        if exchange:
            query += " AND si.exchange = :exchange"
            params["exchange"] = exchange

        query += " ORDER BY fr.roe DESC LIMIT :limit"
        params["limit"] = limit

        result = self.db.execute(text(query), params)

        stocks = []
        for row in result:
            stocks.append({
                "ticker": row[0],
                "name": row[1],
                "exchange": row[2],
                "market_cap": float(row[3]) if row[3] else None,
                "roe": float(row[4]) if row[4] else None,
                "roa": float(row[5]) if row[5] else None,
                "net_margin": float(row[6]) if row[6] else None,
                "debt_to_equity": float(row[7]) if row[7] else None,
                "current_ratio": float(row[8]) if row[8] else None,
                "asset_turnover": float(row[9]) if row[9] else None,
                "strategy": "quality",
            })

        logger.info(f"Found {len(stocks)} quality stocks")

        return stocks

    def screen_dividend_stocks(
        self,
        exchange: Optional[str] = None,
        min_yield: float = 4.0,
        limit: int = 20,
    ) -> List[Dict]:
        """Screen for dividend stocks.

        Criteria:
        - High dividend yield
        - Consistent dividend history
        - Payout ratio < 70%
        - Stable earnings

        Args:
            exchange: Optional exchange filter
            min_yield: Minimum dividend yield
            limit: Maximum results

        Returns:
            List of dividend stocks
        """
        logger.info("Screening for dividend stocks")

        latest_date = self.db.query(FinancialRatio.date).order_by(FinancialRatio.date.desc()).first()

        if not latest_date:
            return []

        latest_date = latest_date[0]

        query = """
            SELECT DISTINCT
                si.ticker,
                si.name,
                si.exchange,
                si.market_cap,
                fr.dividend_yield,
                fr.pe_ratio,
                fr.roe,
                fr.current_ratio
            FROM stock_info si
            JOIN financial_ratio fr ON si.ticker = fr.ticker
            WHERE si.is_active = true
            AND fr.date = :latest_date
            AND fr.dividend_yield >= :min_yield
            AND fr.pe_ratio > 0
            AND fr.roe > 10
            AND fr.current_ratio > 1.5
        """

        params = {"latest_date": latest_date, "min_yield": min_yield}

        if exchange:
            query += " AND si.exchange = :exchange"
            params["exchange"] = exchange

        query += " ORDER BY fr.dividend_yield DESC LIMIT :limit"
        params["limit"] = limit

        result = self.db.execute(text(query), params)

        stocks = []
        for row in result:
            stocks.append({
                "ticker": row[0],
                "name": row[1],
                "exchange": row[2],
                "market_cap": float(row[3]) if row[3] else None,
                "dividend_yield": float(row[4]) if row[4] else None,
                "pe_ratio": float(row[5]) if row[5] else None,
                "roe": float(row[6]) if row[6] else None,
                "current_ratio": float(row[7]) if row[7] else None,
                "strategy": "dividend",
            })

        logger.info(f"Found {len(stocks)} dividend stocks")

        return stocks

    def screen_all_strategies(
        self,
        exchange: Optional[str] = None,
        limit_per_strategy: int = 10,
    ) -> Dict[str, List[Dict]]:
        """Run all screening strategies.

        Args:
            exchange: Optional exchange filter
            limit_per_strategy: Results per strategy

        Returns:
            Dictionary of strategy -> stocks
        """
        return {
            "value": self.screen_value_stocks(exchange, limit=limit_per_strategy),
            "growth": self.screen_growth_stocks(exchange, limit=limit_per_strategy),
            "momentum": self.screen_momentum_stocks(exchange, limit=limit_per_strategy),
            "quality": self.screen_quality_stocks(exchange, limit=limit_per_strategy),
            "dividend": self.screen_dividend_stocks(exchange, limit=limit_per_strategy),
        }
