"""DNSE API client for fetching Vietnam stock market data."""
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
import redis
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.utils.config import get_settings
from src.utils.helpers import retry_on_failure
from src.utils.logger import get_logger
from src.utils.validators import validate_date_range, validate_ticker

logger = get_logger(__name__)
settings = get_settings()


class DNSEAPIError(Exception):
    """Custom exception for DNSE API errors."""

    pass


class DNSEClient:
    """Client for DNSE API with rate limiting and caching."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        rate_limit_requests: int = 200,
        rate_limit_period: int = 60,
    ):
        """Initialize DNSE API client.

        Args:
            api_key: DNSE API key
            secret_key: DNSE secret key
            rate_limit_requests: Maximum requests per period
            rate_limit_period: Period in seconds for rate limiting
        """
        self.api_key = api_key or settings.DNSE_API_KEY
        self.secret_key = secret_key or settings.DNSE_SECRET_KEY
        self.base_url = "https://services.entrade.com.vn"

        # Rate limiting
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period = rate_limit_period
        self.request_timestamps: List[float] = []

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        # Redis cache
        try:
            self.cache = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self.cache = None

    async def __aenter__(self) -> "DNSEClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client and connections."""
        await self.client.aclose()
        if self.cache:
            self.cache.close()

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()

        # Remove timestamps outside the rate limit window
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if current_time - ts < self.rate_limit_period
        ]

        # Check if limit exceeded
        if len(self.request_timestamps) >= self.rate_limit_requests:
            oldest_request = self.request_timestamps[0]
            sleep_time = self.rate_limit_period - (current_time - oldest_request)
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds"
                )
                time.sleep(sleep_time)
                self.request_timestamps = []

        # Add current request timestamp
        self.request_timestamps.append(current_time)

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request.

        Args:
            endpoint: API endpoint
            params: Request parameters

        Returns:
            Cache key string
        """
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"dnse:{endpoint}:{param_str}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None
        """
        if not self.cache:
            return None

        try:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for key: {cache_key}")
                import json
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")

        return None

    def _set_cache(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl: int = 3600,
    ) -> None:
        """Set data in cache.

        Args:
            cache_key: Cache key
            data: Data to cache
            ttl: Time to live in seconds
        """
        if not self.cache:
            return

        try:
            import json
            self.cache.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"Cached data for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Make HTTP request to DNSE API with retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters
            use_cache: Whether to use cache

        Returns:
            API response data

        Raises:
            DNSEAPIError: If API request fails
        """
        params = params or {}

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data

        # Rate limiting
        self._check_rate_limit()

        # Make request
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making request to {url} with params {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Cache successful response
            if use_cache and data:
                cache_key = self._get_cache_key(endpoint, params)
                self._set_cache(cache_key, data, ttl=settings.PRICE_DATA_CACHE_TTL)

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise DNSEAPIError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise DNSEAPIError(f"Failed to fetch data: {e}")

    async def get_daily_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch daily OHLCV price data.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of daily price records

        Raises:
            ValidationError: If parameters are invalid
            DNSEAPIError: If API request fails
        """
        validate_ticker(ticker)
        validate_date_range(start_date, end_date)

        params = {
            "symbol": ticker,
            "fromDate": start_date.strftime("%Y-%m-%d"),
            "toDate": end_date.strftime("%Y-%m-%d"),
            "type": "D",
        }

        data = await self._make_request("chart/bars", params)

        # Transform API response to standard format
        records = []
        if data and "data" in data:
            for item in data["data"]:
                records.append({
                    "ticker": ticker,
                    "date": datetime.strptime(item["tradingDate"], "%Y-%m-%d").date(),
                    "open": Decimal(str(item["open"])),
                    "high": Decimal(str(item["high"])),
                    "low": Decimal(str(item["low"])),
                    "close": Decimal(str(item["close"])),
                    "volume": int(item["volume"]),
                    "value": Decimal(str(item.get("value", 0))),
                })

        logger.info(
            f"Fetched {len(records)} daily price records for {ticker} "
            f"from {start_date} to {end_date}"
        )

        return records

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

        data = await self._make_request("finance/financial-statement", params)

        if data and "data" in data:
            return data["data"]

        return None

    async def get_stock_list(self, exchange: Optional[str] = None) -> List[Dict[str, str]]:
        """Fetch list of all stocks or stocks on specific exchange.

        Args:
            exchange: Exchange name (HOSE, HNX, UPCOM) or None for all

        Returns:
            List of stock information
        """
        params = {}
        if exchange:
            params["exchange"] = exchange

        data = await self._make_request("stock/symbols", params, use_cache=True)

        stocks = []
        if data and "data" in data:
            for item in data["data"]:
                stocks.append({
                    "ticker": item["stockCode"],
                    "name": item["stockName"],
                    "exchange": item["exchange"],
                    "industry": item.get("industryName"),
                    "listing_date": item.get("firstTradingDate"),
                })

        logger.info(f"Fetched {len(stocks)} stocks from {exchange or 'all exchanges'}")
        return stocks

    async def get_corporate_actions(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch corporate actions (dividends, splits, etc.).

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of corporate actions
        """
        validate_ticker(ticker)
        validate_date_range(start_date, end_date)

        params = {
            "symbol": ticker,
            "fromDate": start_date.strftime("%Y-%m-%d"),
            "toDate": end_date.strftime("%Y-%m-%d"),
        }

        data = await self._make_request("stock/events", params)

        actions = []
        if data and "data" in data:
            for item in data["data"]:
                actions.append({
                    "ticker": ticker,
                    "ex_date": datetime.strptime(item["exDate"], "%Y-%m-%d").date(),
                    "action_type": item["eventType"],
                    "ratio": Decimal(str(item.get("ratio", 0))),
                    "dividend_amount": Decimal(str(item.get("dividendValue", 0))),
                    "description": item.get("eventName"),
                })

        logger.info(
            f"Fetched {len(actions)} corporate actions for {ticker} "
            f"from {start_date} to {end_date}"
        )

        return actions
