"""Advanced screening strategies optimized for the Vietnamese stock market."""
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy import text, func
from sqlalchemy.orm import Session

from src.database.models import DailyPrice, FinancialRatio, StockInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdvancedScreener:
    """Advanced multi-factor screening strategies — optimized for Vietnam."""

    def __init__(self, db: Session):
        self.db = db

    def _get_recent_financial_dates_subquery(self, days_back: int = 90):
        """Get subquery of latest financial ratio date per ticker within last N days."""
        cutoff = date.today() - timedelta(days=days_back)
        return (
            self.db.query(
                FinancialRatio.ticker,
                func.max(FinancialRatio.date).label("max_date")
            )
            .filter(FinancialRatio.date >= cutoff)
            .group_by(FinancialRatio.ticker)
            .subquery()
        )

    def screen_value_stocks(
        self,
        exchange: Optional[str] = None,
        min_market_cap: float = 500_000_000_000,  # 500 tỷ VND
        min_avg_volume: int = 100_000,  # Tăng từ 50K lên 100K cho liquidity tốt hơn
        limit: int = 20,
    ) -> List[Dict]:
        logger.info("Screening for VALUE stocks (VN-optimized)")

        # Point-in-time financial data (90 ngày gần nhất)
        latest_subq = self._get_recent_financial_dates_subquery(days_back=90)
        thirty_days_ago = date.today() - timedelta(days=30)
        avg_volume_subq = (
            self.db.query(
                DailyPrice.ticker,
                func.avg(DailyPrice.volume).label("avg_volume")
            )
            .filter(DailyPrice.date >= thirty_days_ago)
            .group_by(DailyPrice.ticker)
            .subquery()
        )

        query_orm = (
            self.db.query(
                StockInfo.ticker,
                StockInfo.name,
                StockInfo.exchange,
                StockInfo.market_cap,
                FinancialRatio.pe_ratio,
                FinancialRatio.pb_ratio,
                FinancialRatio.dividend_yield,
                FinancialRatio.roe,
                FinancialRatio.current_ratio,
                FinancialRatio.debt_to_equity,
                FinancialRatio.revenue_growth_yoy,
                FinancialRatio.eps_growth_yoy,
                func.coalesce(avg_volume_subq.c.avg_volume, 0).label("avg_volume")
            )
            .join(FinancialRatio, StockInfo.ticker == FinancialRatio.ticker)
            .join(latest_subq, 
                  (FinancialRatio.ticker == latest_subq.c.ticker) & 
                  (FinancialRatio.date == latest_subq.c.max_date))
            .outerjoin(avg_volume_subq, StockInfo.ticker == avg_volume_subq.c.ticker)
            .filter(StockInfo.is_active == True)
            .filter(FinancialRatio.pe_ratio.between(5, 15))  # Giữ value range thật sự
            .filter(FinancialRatio.pb_ratio.between(0.5, 2.0))  # Tránh overvalued
            .filter(
                (FinancialRatio.dividend_yield >= 2.5) | 
                (FinancialRatio.dividend_yield.is_(None))
            )
            .filter(FinancialRatio.roe >= 10)
            .filter(FinancialRatio.current_ratio >= 1.2)
            .filter(
                (FinancialRatio.debt_to_equity <= 1.5) | 
                (FinancialRatio.debt_to_equity.is_(None))
            )
            .filter(
                (StockInfo.market_cap >= min_market_cap) | 
                (StockInfo.market_cap.is_(None))
            )
            .filter(func.coalesce(avg_volume_subq.c.avg_volume, 0) >= min_avg_volume)
            .filter(
                (FinancialRatio.revenue_growth_yoy.is_(None)) |
                (func.abs(FinancialRatio.revenue_growth_yoy) <= 100)
            )
            .filter(
                (FinancialRatio.eps_growth_yoy.is_(None)) |
                (func.abs(FinancialRatio.eps_growth_yoy) <= 100)
            )
        )

        if exchange:
            query_orm = query_orm.filter(StockInfo.exchange == exchange)

        results = query_orm.order_by(FinancialRatio.pe_ratio.asc()).limit(limit).all()

        return [
            {
                "ticker": r.ticker,
                "name": r.name,
                "exchange": r.exchange,
                "market_cap": float(r.market_cap) if r.market_cap else None,
                "pe_ratio": float(r.pe_ratio) if r.pe_ratio else None,
                "pb_ratio": float(r.pb_ratio) if r.pb_ratio else None,
                "dividend_yield": float(r.dividend_yield) if r.dividend_yield else None,
                "roe": float(r.roe) if r.roe else None,
                "current_ratio": float(r.current_ratio) if r.current_ratio else None,
                "debt_to_equity": float(r.debt_to_equity) if r.debt_to_equity else None,
                "revenue_growth_yoy": float(r.revenue_growth_yoy) if r.revenue_growth_yoy else None,
                "eps_growth_yoy": float(r.eps_growth_yoy) if r.eps_growth_yoy else None,
                "avg_volume": int(r.avg_volume) if r.avg_volume else 0,
                "strategy": "value",
            }
            for r in results
        ]

    def _get_tickers_with_recent_financials(self, days_back: int = 90) -> List[str]:
        cutoff = date.today() - timedelta(days=days_back)
        return [
            r[0] for r in self.db.query(FinancialRatio.ticker)
            .filter(FinancialRatio.date >= cutoff)
            .distinct()
            .all()
        ]

    def screen_growth_stocks(
        self,
        exchange: Optional[str] = None,
        min_market_cap: float = 500_000_000_000,
        min_avg_volume: int = 100_000,  # Tăng liquidity requirement
        limit: int = 20,
    ) -> List[Dict]:
        logger.info("Screening for GROWTH stocks (VN-optimized)")

        thirty_days_ago = date.today() - timedelta(days=30)
        latest_subq = self._get_recent_financial_dates_subquery(days_back=90)

        avg_volume_subq = (
            self.db.query(
                DailyPrice.ticker,
                func.avg(DailyPrice.volume).label("avg_volume")
            )
            .filter(DailyPrice.date >= thirty_days_ago)
            .group_by(DailyPrice.ticker)
            .subquery()
        )

        query = (
            self.db.query(
                StockInfo.ticker,
                StockInfo.name,
                StockInfo.exchange,
                StockInfo.market_cap,
                FinancialRatio.revenue_growth_yoy,
                FinancialRatio.eps_growth_yoy,
                FinancialRatio.roe,
                FinancialRatio.net_margin,
                func.coalesce(avg_volume_subq.c.avg_volume, 0).label("avg_volume")
            )
            .join(FinancialRatio, StockInfo.ticker == FinancialRatio.ticker)
            .join(latest_subq,
                  (FinancialRatio.ticker == latest_subq.c.ticker) &
                  (FinancialRatio.date == latest_subq.c.max_date))
            .outerjoin(avg_volume_subq, StockInfo.ticker == avg_volume_subq.c.ticker)
            .filter(StockInfo.is_active == True)
            .filter(FinancialRatio.revenue_growth_yoy.between(20, 80))  # Mở rộng range hơn
            .filter(FinancialRatio.eps_growth_yoy.between(20, 80))  # 20-80% là sustainable
            .filter(FinancialRatio.roe >= 12)
            .filter(FinancialRatio.net_margin >= 8)
            .filter(
                (StockInfo.market_cap >= min_market_cap) |
                (StockInfo.market_cap.is_(None))
            )
            .filter(func.coalesce(avg_volume_subq.c.avg_volume, 0) >= min_avg_volume)
        )

        if exchange:
            query = query.filter(StockInfo.exchange == exchange)

        results = query.order_by(FinancialRatio.revenue_growth_yoy.desc()).limit(limit).all()

        return [
            {
                "ticker": r.ticker,
                "name": r.name,
                "exchange": r.exchange,
                "market_cap": float(r.market_cap) if r.market_cap else None,
                "revenue_growth_yoy": float(r.revenue_growth_yoy) if r.revenue_growth_yoy else None,
                "eps_growth_yoy": float(r.eps_growth_yoy) if r.eps_growth_yoy else None,
                "roe": float(r.roe) if r.roe else None,
                "net_margin": float(r.net_margin) if r.net_margin else None,
                "avg_volume": int(r.avg_volume) if r.avg_volume else 0,
                "strategy": "growth",
            }
            for r in results
        ]

    def screen_momentum_stocks(
        self,
        exchange: Optional[str] = None,
        lookback_days: int = 63,  # ~3 months
        limit: int = 20,
    ) -> List[Dict]:
        logger.info("Screening for MOMENTUM stocks (VN-optimized)")

        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        # Lấy giá hiện tại và MA20 để lọc tín hiệu
        ma_days = 20
        ma_start = end_date - timedelta(days=ma_days + 10)  # buffer

        active_stocks = self.db.query(StockInfo).filter(StockInfo.is_active == True)
        if exchange:
            active_stocks = active_stocks.filter(StockInfo.exchange == exchange)
        stocks = active_stocks.all()

        momentum_list = []

        for stock in stocks:
            # Lấy dữ liệu giá đủ để tính MA20 và return
            prices = (
                self.db.query(DailyPrice)
                .filter(
                    DailyPrice.ticker == stock.ticker,
                    DailyPrice.date >= ma_start,
                    DailyPrice.date <= end_date,
                )
                .order_by(DailyPrice.date)
                .all()
            )

            if len(prices) < max(2, ma_days):
                continue

            # Tính return trong lookback_days
            price_dict = {p.date: p for p in prices}
            date_list = sorted(price_dict.keys())

            # Tìm ngày gần nhất <= end_date
            actual_end = max(d for d in date_list if d <= end_date)
            actual_start = min(d for d in date_list if d >= start_date)

            if actual_start >= actual_end:
                continue

            start_price = float(price_dict[actual_start].close)
            end_price = float(price_dict[actual_end].close)
            returns = (end_price - start_price) / start_price

            # Kiểm tra giá > MA20
            recent_prices = [float(p.close) for p in prices if p.date <= actual_end][-ma_days:]
            if len(recent_prices) < ma_days:
                continue
            ma20 = sum(recent_prices) / len(recent_prices)
            if end_price < ma20:
                continue  # chỉ giữ cổ phiếu đang trên MA20

            # Volume trend (tùy chọn)
            half = len([p for p in prices if p.date >= start_date]) // 2
            recent_vol = sum(p.volume for p in prices[-half:]) / half if half > 0 else 0
            older_vol = sum(p.volume for p in prices[-2*half:-half]) / half if half > 0 else 1
            vol_trend = (recent_vol - older_vol) / older_vol if older_vol > 0 else 0

            momentum_list.append({
                "ticker": stock.ticker,
                "name": stock.name,
                "exchange": stock.exchange,
                "returns": returns,
                "volume_trend": vol_trend,
                "price": end_price,
                "ma20": ma20,
                "avg_volume": int(sum(p.volume for p in prices[-30:]) / min(30, len(prices))),
                "strategy": "momentum",
            })

        momentum_list.sort(key=lambda x: x["returns"], reverse=True)
        return momentum_list[:limit]

    def screen_quality_stocks(
        self,
        exchange: Optional[str] = None,
        min_market_cap: float = 500_000_000_000,
        min_avg_volume: int = 100_000,  # Tăng liquidity requirement
        limit: int = 20,
    ) -> List[Dict]:
        logger.info("Screening for QUALITY stocks (VN-optimized)")

        thirty_days_ago = date.today() - timedelta(days=30)
        latest_subq = self._get_recent_financial_dates_subquery(days_back=90)

        avg_volume_subq = (
            self.db.query(
                DailyPrice.ticker,
                func.avg(DailyPrice.volume).label("avg_volume")
            )
            .filter(DailyPrice.date >= thirty_days_ago)
            .group_by(DailyPrice.ticker)
            .subquery()
        )

        query = (
            self.db.query(
                StockInfo.ticker,
                StockInfo.name,
                StockInfo.exchange,
                StockInfo.market_cap,
                FinancialRatio.roe,
                FinancialRatio.roa,
                FinancialRatio.net_margin,
                FinancialRatio.debt_to_equity,
                FinancialRatio.current_ratio,
                FinancialRatio.asset_turnover,
                func.coalesce(avg_volume_subq.c.avg_volume, 0).label("avg_volume")
            )
            .join(FinancialRatio, StockInfo.ticker == FinancialRatio.ticker)
            .join(latest_subq,
                  (FinancialRatio.ticker == latest_subq.c.ticker) &
                  (FinancialRatio.date == latest_subq.c.max_date))
            .outerjoin(avg_volume_subq, StockInfo.ticker == avg_volume_subq.c.ticker)
            .filter(StockInfo.is_active == True)
            .filter(FinancialRatio.roe >= 12)
            .filter(FinancialRatio.roa >= 8)
            .filter(FinancialRatio.net_margin >= 10)
            .filter(FinancialRatio.debt_to_equity < 1.2)  # nới lỏng cho VN
            .filter(FinancialRatio.current_ratio > 1.3)
            .filter(
                (StockInfo.market_cap >= min_market_cap) |
                (StockInfo.market_cap.is_(None))
            )
            .filter(func.coalesce(avg_volume_subq.c.avg_volume, 0) >= min_avg_volume)
        )

        if exchange:
            query = query.filter(StockInfo.exchange == exchange)

        results = query.order_by(FinancialRatio.roe.desc()).limit(limit).all()

        return [
            {
                "ticker": r.ticker,
                "name": r.name,
                "exchange": r.exchange,
                "market_cap": float(r.market_cap) if r.market_cap else None,
                "roe": float(r.roe) if r.roe else None,
                "roa": float(r.roa) if r.roa else None,
                "net_margin": float(r.net_margin) if r.net_margin else None,
                "debt_to_equity": float(r.debt_to_equity) if r.debt_to_equity else None,
                "current_ratio": float(r.current_ratio) if r.current_ratio else None,
                "asset_turnover": float(r.asset_turnover) if r.asset_turnover else None,
                "avg_volume": int(r.avg_volume) if r.avg_volume else 0,
                "strategy": "quality",
            }
            for r in results
        ]

    def screen_dividend_stocks(
        self,
        exchange: Optional[str] = None,
        min_yield: float = 2.5,
        max_yield: float = 12.0,
        min_market_cap: float = 500_000_000_000,
        min_avg_volume: int = 100_000,  # Tăng liquidity requirement
        limit: int = 20,
    ) -> List[Dict]:
        logger.info("Screening for DIVIDEND stocks (VN-optimized)")

        thirty_days_ago = date.today() - timedelta(days=30)
        latest_subq = self._get_recent_financial_dates_subquery(days_back=90)

        # Tránh dividend trap: giá không giảm quá 25% trong 6 tháng
        six_months_ago = date.today() - timedelta(days=180)
        price_change_subq = (
            self.db.query(
                DailyPrice.ticker,
                (func.max(DailyPrice.close) - func.min(DailyPrice.close)) / func.min(DailyPrice.close)
            )
            .filter(DailyPrice.date >= six_months_ago)
            .group_by(DailyPrice.ticker)
            .subquery()
        )

        avg_volume_subq = (
            self.db.query(
                DailyPrice.ticker,
                func.avg(DailyPrice.volume).label("avg_volume")
            )
            .filter(DailyPrice.date >= thirty_days_ago)
            .group_by(DailyPrice.ticker)
            .subquery()
        )

        query = (
            self.db.query(
                StockInfo.ticker,
                StockInfo.name,
                StockInfo.exchange,
                StockInfo.market_cap,
                FinancialRatio.dividend_yield,
                FinancialRatio.pe_ratio,
                FinancialRatio.roe,
                FinancialRatio.current_ratio,
                func.coalesce(avg_volume_subq.c.avg_volume, 0).label("avg_volume")
            )
            .join(FinancialRatio, StockInfo.ticker == FinancialRatio.ticker)
            .join(latest_subq,
                  (FinancialRatio.ticker == latest_subq.c.ticker) &
                  (FinancialRatio.date == latest_subq.c.max_date))
            .outerjoin(avg_volume_subq, StockInfo.ticker == avg_volume_subq.c.ticker)
            .filter(StockInfo.is_active == True)
            .filter(FinancialRatio.dividend_yield.between(min_yield, max_yield))
            .filter(FinancialRatio.pe_ratio > 0)
            .filter(FinancialRatio.roe >= 8)
            .filter(FinancialRatio.current_ratio >= 1.2)
            .filter(
                (StockInfo.market_cap >= min_market_cap) |
                (StockInfo.market_cap.is_(None))
            )
            .filter(func.coalesce(avg_volume_subq.c.avg_volume, 0) >= min_avg_volume)
        )

        if exchange:
            query = query.filter(StockInfo.exchange == exchange)

        results = query.order_by(FinancialRatio.dividend_yield.desc()).limit(limit).all()

        return [
            {
                "ticker": r.ticker,
                "name": r.name,
                "exchange": r.exchange,
                "market_cap": float(r.market_cap) if r.market_cap else None,
                "dividend_yield": float(r.dividend_yield) if r.dividend_yield else None,
                "pe_ratio": float(r.pe_ratio) if r.pe_ratio else None,
                "roe": float(r.roe) if r.roe else None,
                "current_ratio": float(r.current_ratio) if r.current_ratio else None,
                "avg_volume": int(r.avg_volume) if r.avg_volume else 0,
                "strategy": "dividend",
            }
            for r in results
        ]

    def screen_all_strategies(
        self,
        exchange: Optional[str] = None,
        min_market_cap: float = 500_000_000_000,
        min_avg_volume: int = 100_000,  # Tăng liquidity requirement
        limit_per_strategy: int = 10,
    ) -> Dict[str, List[Dict]]:
        return {
            "value": self.screen_value_stocks(
                exchange=exchange,
                min_market_cap=min_market_cap,
                min_avg_volume=min_avg_volume,
                limit=limit_per_strategy,
            ),
            "growth": self.screen_growth_stocks(
                exchange=exchange,
                min_market_cap=min_market_cap,
                min_avg_volume=min_avg_volume,
                limit=limit_per_strategy,
            ),
            "momentum": self.screen_momentum_stocks(
                exchange=exchange,
                limit=limit_per_strategy,
            ),
            "quality": self.screen_quality_stocks(
                exchange=exchange,
                min_market_cap=min_market_cap,
                min_avg_volume=min_avg_volume,
                limit=limit_per_strategy,
            ),
            "dividend": self.screen_dividend_stocks(
                exchange=exchange,
                min_market_cap=min_market_cap,
                min_avg_volume=min_avg_volume,
                limit=limit_per_strategy,
            ),
        }