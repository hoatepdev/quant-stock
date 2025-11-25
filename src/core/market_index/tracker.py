"""Market index tracking and data management."""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.models import MarketIndex
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarketIndexTracker:
    """Track and manage Vietnam market indices."""

    # Vietnam market indices
    INDICES = {
        "VN-INDEX": "VNINDEX",  # Ho Chi Minh Stock Exchange
        "HNX-INDEX": "HNX",     # Hanoi Stock Exchange
        "UPCOM-INDEX": "UPCOM", # Unlisted Public Company Market
        "VN30": "VN30",         # Top 30 stocks by market cap
        "HNX30": "HNX30",       # Top 30 HNX stocks
    }

    def __init__(self, db: Session):
        """Initialize market index tracker.

        Args:
            db: Database session
        """
        self.db = db

    async def fetch_and_save_index_data(
        self,
        index_name: str,
        start_date: date,
        end_date: date,
        client,  # type: ignore
    ) -> int:
        """Fetch and save market index data.

        Args:
            index_name: Index name (VN-INDEX, HNX-INDEX, etc.)
            start_date: Start date
            end_date: End date
            client: Data client instance

        Returns:
            Number of records saved
        """
        logger.info(f"Fetching index data for {index_name} from {start_date} to {end_date}")

        try:
            # Different clients may have different methods for fetching index data
            if hasattr(client, 'get_index_data'):
                records = await client.get_index_data(index_name, start_date, end_date)
            elif hasattr(client, 'get_daily_prices'):
                # Use ticker-like approach if index data method not available
                symbol = self.INDICES.get(index_name, index_name)
                records = await client.get_daily_prices(symbol, start_date, end_date)
            else:
                logger.warning(f"Client does not support index data fetching")
                return 0

            if not records:
                logger.warning(f"No data returned for {index_name}")
                return 0

            saved_count = 0

            for record in records:
                # Check if record already exists
                existing = (
                    self.db.query(MarketIndex)
                    .filter(
                        MarketIndex.index_name == index_name,
                        MarketIndex.date == record.get("date"),
                    )
                    .first()
                )

                if not existing:
                    index_record = MarketIndex(
                        index_name=index_name,
                        date=record.get("date"),
                        open=Decimal(str(record.get("open", 0))),
                        high=Decimal(str(record.get("high", 0))),
                        low=Decimal(str(record.get("low", 0))),
                        close=Decimal(str(record.get("close", 0))),
                        volume=int(record.get("volume", 0)),
                        value=Decimal(str(record.get("value", 0))) if record.get("value") else None,
                    )
                    self.db.add(index_record)
                    saved_count += 1
                else:
                    # Update existing record
                    existing.open = Decimal(str(record.get("open", 0)))
                    existing.high = Decimal(str(record.get("high", 0)))
                    existing.low = Decimal(str(record.get("low", 0)))
                    existing.close = Decimal(str(record.get("close", 0)))
                    existing.volume = int(record.get("volume", 0))
                    existing.value = Decimal(str(record.get("value", 0))) if record.get("value") else None

            self.db.commit()
            logger.info(f"Saved {saved_count} index records for {index_name}")

            return saved_count

        except Exception as e:
            logger.error(f"Error fetching index data for {index_name}: {e}")
            self.db.rollback()
            return 0

    def get_index_data(
        self,
        index_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[MarketIndex]:
        """Get historical index data from database.

        Args:
            index_name: Index name
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional limit on number of records

        Returns:
            List of index records
        """
        query = self.db.query(MarketIndex).filter(
            MarketIndex.index_name == index_name
        )

        if start_date:
            query = query.filter(MarketIndex.date >= start_date)

        if end_date:
            query = query.filter(MarketIndex.date <= end_date)

        query = query.order_by(MarketIndex.date.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_latest_index_value(self, index_name: str) -> Optional[MarketIndex]:
        """Get the most recent index value.

        Args:
            index_name: Index name

        Returns:
            Latest index record or None
        """
        return (
            self.db.query(MarketIndex)
            .filter(MarketIndex.index_name == index_name)
            .order_by(MarketIndex.date.desc())
            .first()
        )

    def calculate_index_returns(
        self,
        index_name: str,
        start_date: date,
        end_date: date,
    ) -> Optional[float]:
        """Calculate total return for an index over a period.

        Args:
            index_name: Index name
            start_date: Start date
            end_date: End date

        Returns:
            Total return as decimal (e.g., 0.15 for 15%) or None
        """
        # Get start and end values
        start_value = (
            self.db.query(MarketIndex)
            .filter(
                MarketIndex.index_name == index_name,
                MarketIndex.date >= start_date,
            )
            .order_by(MarketIndex.date)
            .first()
        )

        end_value = (
            self.db.query(MarketIndex)
            .filter(
                MarketIndex.index_name == index_name,
                MarketIndex.date <= end_date,
            )
            .order_by(MarketIndex.date.desc())
            .first()
        )

        if not start_value or not end_value:
            logger.warning(
                f"Could not find index values for {index_name} "
                f"between {start_date} and {end_date}"
            )
            return None

        start_close = float(start_value.close)
        end_close = float(end_value.close)

        if start_close == 0:
            return None

        return (end_close - start_close) / start_close

    def calculate_index_volatility(
        self,
        index_name: str,
        start_date: date,
        end_date: date,
        annualized: bool = True,
    ) -> Optional[float]:
        """Calculate volatility of an index over a period.

        Args:
            index_name: Index name
            start_date: Start date
            end_date: End date
            annualized: Whether to annualize volatility

        Returns:
            Volatility (standard deviation of returns) or None
        """
        records = self.get_index_data(index_name, start_date, end_date)

        if len(records) < 2:
            return None

        # Calculate daily returns
        returns = []
        for i in range(len(records) - 1):
            curr_close = float(records[i].close)
            prev_close = float(records[i + 1].close)  # Records are in desc order

            if prev_close != 0:
                daily_return = (curr_close - prev_close) / prev_close
                returns.append(daily_return)

        if not returns:
            return None

        # Calculate standard deviation
        import statistics
        volatility = statistics.stdev(returns)

        # Annualize if requested (assuming 252 trading days)
        if annualized:
            volatility = volatility * (252 ** 0.5)

        return volatility

    def get_index_summary(self, index_name: str) -> Optional[Dict]:
        """Get summary statistics for an index.

        Args:
            index_name: Index name

        Returns:
            Dictionary with summary statistics or None
        """
        latest = self.get_latest_index_value(index_name)

        if not latest:
            return None

        # Get 1 year of data for statistics
        from datetime import timedelta
        one_year_ago = latest.date - timedelta(days=365)

        year_data = self.get_index_data(index_name, one_year_ago, latest.date)

        if not year_data:
            return {
                "index_name": index_name,
                "latest_date": latest.date,
                "latest_close": float(latest.close),
            }

        # Calculate statistics
        closes = [float(record.close) for record in year_data]
        volumes = [record.volume for record in year_data]

        year_return = self.calculate_index_returns(index_name, one_year_ago, latest.date)
        volatility = self.calculate_index_volatility(index_name, one_year_ago, latest.date)

        return {
            "index_name": index_name,
            "latest_date": latest.date,
            "latest_close": float(latest.close),
            "year_high": max(closes) if closes else None,
            "year_low": min(closes) if closes else None,
            "year_return": year_return,
            "year_volatility": volatility,
            "avg_daily_volume": sum(volumes) / len(volumes) if volumes else None,
            "total_trading_days": len(year_data),
        }

    def get_all_indices_summary(self) -> List[Dict]:
        """Get summary for all tracked indices.

        Returns:
            List of index summaries
        """
        summaries = []

        for index_name in self.INDICES.keys():
            summary = self.get_index_summary(index_name)
            if summary:
                summaries.append(summary)

        return summaries

    def compare_stock_to_index(
        self,
        ticker: str,
        index_name: str,
        start_date: date,
        end_date: date,
    ) -> Optional[Dict]:
        """Compare stock performance to market index.

        Args:
            ticker: Stock ticker
            index_name: Index name
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with comparison metrics or None
        """
        from src.database.models import DailyPrice

        # Get stock returns
        stock_start = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.ticker == ticker,
                DailyPrice.date >= start_date,
            )
            .order_by(DailyPrice.date)
            .first()
        )

        stock_end = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.ticker == ticker,
                DailyPrice.date <= end_date,
            )
            .order_by(DailyPrice.date.desc())
            .first()
        )

        if not stock_start or not stock_end:
            logger.warning(f"Could not find stock data for {ticker}")
            return None

        stock_return = (
            (float(stock_end.close) - float(stock_start.close)) / float(stock_start.close)
        )

        # Get index returns
        index_return = self.calculate_index_returns(index_name, start_date, end_date)

        if index_return is None:
            logger.warning(f"Could not calculate index return for {index_name}")
            return None

        # Calculate alpha (excess return over index)
        alpha = stock_return - index_return

        return {
            "ticker": ticker,
            "index_name": index_name,
            "start_date": start_date,
            "end_date": end_date,
            "stock_return": stock_return,
            "index_return": index_return,
            "alpha": alpha,
            "outperformed": stock_return > index_return,
        }
