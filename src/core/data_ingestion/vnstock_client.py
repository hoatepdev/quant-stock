"""VNStock data client for fetching Vietnam stock market data."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
import redis
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from vnstock import Vnstock

from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.utils.validators import validate_date_range, validate_ticker

logger = get_logger(__name__)
settings = get_settings()


class VNStockAPIError(Exception):
    """Custom exception for VNStock API errors."""

    pass


class VNStockClient:
    """Client for VNStock API with rate limiting and caching."""

    def __init__(self) -> None:
        """Initialize VNStock API client."""
        self.vnstock = Vnstock()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Redis cache
        try:
            self.cache = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            logger.info("Redis cache initialized successfully for VNStock client")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self.cache = None

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request.

        Args:
            endpoint: API endpoint
            params: Request parameters

        Returns:
            Cache key string
        """
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"vnstock:{endpoint}:{param_str}"

    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Get data from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached DataFrame or None
        """
        if not self.cache:
            return None

        try:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for key: {cache_key}")
                import json

                data = json.loads(cached)
                return pd.DataFrame(data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    def _set_cache(self, cache_key: str, df: pd.DataFrame, ttl: int = 86400) -> None:
        """Set data in cache.

        Args:
            cache_key: Cache key
            df: DataFrame to cache
            ttl: Time to live in seconds (default 1 day)
        """
        if not self.cache:
            return

        try:
            import json

            data = df.to_dict(orient="records")
            self.cache.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"Cached data for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    async def _run_in_executor(self, func, *args, **kwargs) -> Any:  # type: ignore
        """Run synchronous function in thread pool.

        Args:
            func: Function to run
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
    )
    async def get_daily_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch daily OHLCV price data with adjusted close.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of daily price records

        Raises:
            ValidationError: If parameters are invalid
            VNStockAPIError: If API request fails
        """
        validate_ticker(ticker)
        validate_date_range(start_date, end_date)

        params = {
            "symbol": ticker,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        # Check cache
        cache_key = self._get_cache_key("daily_prices", params)
        cached_df = self._get_from_cache(cache_key)

        if cached_df is not None:
            return cached_df.to_dict(orient="records")

        try:
            # Fetch data using vnstock (sync call in executor)
            stock = self.vnstock.stock(symbol=ticker, source="VCI")

            def fetch_data() -> pd.DataFrame:
                return stock.quote.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                )

            df = await self._run_in_executor(fetch_data)

            if df is None or df.empty:
                logger.warning(f"No data returned for {ticker}")
                return []

            # Standardize column names to match SSI client
            df = df.reset_index()
            column_mapping = {
                "time": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }

            df = df.rename(columns=column_mapping)

            # VNStock returns adjusted prices by default
            df["adjusted_close"] = df["close"]
            df["adjustment_factor"] = 1.0

            # Ensure date is datetime.date type
            df["date"] = pd.to_datetime(df["date"]).dt.date

            # Select and order columns
            required_columns = [
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "adjusted_close",
                "adjustment_factor",
            ]

            df = df[required_columns]

            # Transform to records
            records = []
            for _, row in df.iterrows():
                records.append(
                    {
                        "ticker": ticker,
                        "date": row["date"],
                        "open": Decimal(str(row["open"])),
                        "high": Decimal(str(row["high"])),
                        "low": Decimal(str(row["low"])),
                        "close": Decimal(str(row["close"])),
                        "volume": int(row["volume"]),
                        "value": Decimal("0"),
                        "adjusted_close": Decimal(str(row["adjusted_close"])),
                        "adjustment_factor": Decimal(str(row["adjustment_factor"])),
                    }
                )

            # Cache the DataFrame
            self._set_cache(cache_key, df, ttl=settings.PRICE_DATA_CACHE_TTL)

            logger.info(
                f"Fetched {len(records)} daily price records for {ticker} "
                f"from {start_date} to {end_date}"
            )

            return records

        except Exception as e:
            logger.error(f"Error fetching daily prices for {ticker}: {e}")
            raise VNStockAPIError(f"Failed to fetch daily prices: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
    )
    async def get_financial_statements(
        self,
        ticker: str,
        year: int,
        quarter: int,
        report_type: str = "Q",
    ) -> Optional[Dict[str, Any]]:
        """Fetch financial statements.

        Args:
            ticker: Stock ticker symbol
            year: Year
            quarter: Quarter (1-4)
            report_type: Report type ('Q' for quarterly, 'Y' for yearly)

        Returns:
            Financial statement data or None
        """
        validate_ticker(ticker)

        params = {
            "symbol": ticker,
            "year": year,
            "quarter": quarter,
            "type": report_type,
        }

        # Check cache
        cache_key = self._get_cache_key("financial_statements", params)
        cached_df = self._get_from_cache(cache_key)

        if cached_df is not None and not cached_df.empty:
            return cached_df.iloc[0].to_dict()

        try:
            stock = self.vnstock.stock(symbol=ticker, source="VCI")

            def fetch_data() -> pd.DataFrame:
                if report_type == "Y":
                    return stock.finance.balance_sheet(period="year", lang="en")
                else:
                    return stock.finance.balance_sheet(period="quarter", lang="en")

            df = await self._run_in_executor(fetch_data)

            if df is None or df.empty:
                logger.warning(f"No financial data for {ticker}")
                return None

            # Filter by year and quarter
            df["year"] = pd.to_datetime(df.index).year
            df["quarter"] = pd.to_datetime(df.index).quarter

            filtered = df[(df["year"] == year) & (df["quarter"] == quarter)]

            if filtered.empty:
                return None

            # Cache the result
            self._set_cache(cache_key, filtered, ttl=604800)  # 7 days

            logger.info(f"Fetched financial data for {ticker} {year}Q{quarter}")

            return filtered.iloc[0].to_dict()

        except Exception as e:
            logger.error(f"Error fetching financial statements for {ticker}: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
    )
    async def get_stock_list(self, exchange: Optional[str] = None) -> List[Dict[str, str]]:
        """Fetch list of all stocks or stocks on specific exchange.

        Args:
            exchange: Exchange name (HOSE, HNX, UPCOM) or None for all

        Returns:
            List of stock information
        """
        # Check cache
        cache_key = self._get_cache_key("stock_list", {"exchange": exchange or "all"})
        cached_df = self._get_from_cache(cache_key)

        if cached_df is not None:
            return cached_df.to_dict(orient="records")

        try:

            def fetch_data() -> pd.DataFrame:
                # Create a stock object (symbol doesn't matter for listing)
                stock = self.vnstock.stock("ACB")
                listing = stock.listing

                # Get all symbols with exchange info
                df = listing.symbols_by_exchange()

                # Filter by exchange if specified
                # Map HOSE -> HSX for vnstock
                if exchange:
                    exchange_map = {
                        "HOSE": "HSX",
                        "HNX": "HNX",
                        "UPCOM": "UPCOM",
                    }
                    vnstock_exchange = exchange_map.get(exchange.upper())
                    if vnstock_exchange and 'exchange' in df.columns:
                        df = df[df['exchange'] == vnstock_exchange]

                return df

            df = await self._run_in_executor(fetch_data)

            if df is None or df.empty:
                logger.warning("No stock list data returned")
                return []

            # Standardize columns
            # Map HSX back to HOSE for our system
            exchange_reverse_map = {
                "HSX": "HOSE",
                "HNX": "HNX",
                "UPCOM": "UPCOM",
            }

            # Valid exchanges for our system
            valid_exchanges = {"HOSE", "HNX", "UPCOM"}

            stocks = []
            for _, row in df.iterrows():
                # Map exchange back to HOSE from HSX
                stock_exchange = row.get("exchange", "")
                stock_exchange = exchange_reverse_map.get(stock_exchange, stock_exchange)

                # Only include stocks with valid exchanges and type=STOCK
                if stock_exchange in valid_exchanges and row.get("type") == "STOCK":
                    stocks.append(
                        {
                            "ticker": row.get("symbol", ""),
                            "name": row.get("organ_name", ""),
                            "exchange": stock_exchange,
                            "industry": row.get("type", ""),
                            "listing_date": None,
                        }
                    )

            # Cache for 1 day
            result_df = pd.DataFrame(stocks)
            self._set_cache(cache_key, result_df, ttl=86400)

            logger.info(f"Fetched {len(stocks)} stocks from {exchange or 'all exchanges'}")

            return stocks

        except Exception as e:
            logger.error(f"Error fetching stock list: {e}")
            raise VNStockAPIError(f"Failed to fetch stock list: {e}")

    async def get_corporate_actions(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch corporate actions (dividends, splits, etc.).

        Note: VNStock provides adjusted prices, so corporate actions are implicit.
        This method returns an empty list as explicit corporate actions are not
        needed since prices are pre-adjusted.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            Empty list (corporate actions already applied in price data)
        """
        validate_ticker(ticker)
        validate_date_range(start_date, end_date)

        logger.info(
            f"VNStock provides pre-adjusted prices for {ticker}. "
            "Corporate action detection not needed."
        )

        return []

    async def close(self) -> None:
        """Close HTTP client and connections."""
        self.executor.shutdown(wait=False)
        if self.cache:
            self.cache.close()
