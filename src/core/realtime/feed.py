"""Real-time data feed support using WebSocket."""
import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Callable, Dict, List, Optional, Set

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RealtimeDataFeed:
    """Real-time stock data feed via WebSocket."""

    def __init__(self):
        """Initialize real-time data feed."""
        self.connections: Set = set()
        self.subscriptions: Dict[str, Set] = {}  # ticker -> set of connections
        self.latest_prices: Dict[str, Dict] = {}
        self.callbacks: List[Callable] = []

    def subscribe(self, ticker: str, connection_id: str) -> None:
        """Subscribe to real-time data for a ticker.

        Args:
            ticker: Stock ticker
            connection_id: Connection identifier
        """
        if ticker not in self.subscriptions:
            self.subscriptions[ticker] = set()

        self.subscriptions[ticker].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to {ticker}")

    def unsubscribe(self, ticker: str, connection_id: str) -> None:
        """Unsubscribe from ticker updates.

        Args:
            ticker: Stock ticker
            connection_id: Connection identifier
        """
        if ticker in self.subscriptions:
            self.subscriptions[ticker].discard(connection_id)
            logger.info(f"Connection {connection_id} unsubscribed from {ticker}")

    def unsubscribe_all(self, connection_id: str) -> None:
        """Unsubscribe connection from all tickers.

        Args:
            connection_id: Connection identifier
        """
        for ticker in list(self.subscriptions.keys()):
            self.subscriptions[ticker].discard(connection_id)

        logger.info(f"Connection {connection_id} unsubscribed from all tickers")

    async def broadcast_price_update(
        self,
        ticker: str,
        price_data: Dict,
    ) -> None:
        """Broadcast price update to subscribed connections.

        Args:
            ticker: Stock ticker
            price_data: Price update data
        """
        if ticker not in self.subscriptions:
            return

        # Update latest price
        self.latest_prices[ticker] = price_data

        # Notify callbacks
        for callback in self.callbacks:
            try:
                await callback(ticker, price_data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")

        # Broadcast to subscribers
        message = {
            "type": "price_update",
            "ticker": ticker,
            "data": price_data,
            "timestamp": datetime.now().isoformat(),
        }

        # In a real implementation, you would send to WebSocket connections
        logger.debug(f"Broadcasting {ticker} update to {len(self.subscriptions[ticker])} subscribers")

    def register_callback(self, callback: Callable) -> None:
        """Register callback for price updates.

        Args:
            callback: Async function to call on updates
        """
        self.callbacks.append(callback)

    def get_latest_price(self, ticker: str) -> Optional[Dict]:
        """Get latest price for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Latest price data or None
        """
        return self.latest_prices.get(ticker)

    async def start_feed(
        self,
        tickers: List[str],
        update_interval: int = 5,
    ) -> None:
        """Start real-time data feed (simulation).

        Args:
            tickers: List of tickers to track
            update_interval: Seconds between updates
        """
        logger.info(f"Starting real-time feed for {len(tickers)} tickers")

        while True:
            for ticker in tickers:
                # Simulate price update
                # In production, this would fetch from actual real-time source
                price_update = await self._fetch_realtime_price(ticker)

                if price_update:
                    await self.broadcast_price_update(ticker, price_update)

            await asyncio.sleep(update_interval)

    async def _fetch_realtime_price(self, ticker: str) -> Optional[Dict]:
        """Fetch real-time price (placeholder).

        Args:
            ticker: Stock ticker

        Returns:
            Price data dictionary
        """
        # Placeholder for real-time price fetching
        # In production, integrate with actual data provider (SSI, DNSE, etc.)

        import random

        # Simulate price with random walk
        if ticker in self.latest_prices:
            last_price = self.latest_prices[ticker]["price"]
            change = random.uniform(-0.02, 0.02)
            new_price = last_price * (1 + change)
        else:
            new_price = random.uniform(10, 100)

        return {
            "ticker": ticker,
            "price": round(new_price, 2),
            "change": round(new_price - self.latest_prices.get(ticker, {}).get("price", new_price), 2),
            "change_pct": round(
                (new_price - self.latest_prices.get(ticker, {}).get("price", new_price)) /
                self.latest_prices.get(ticker, {}).get("price", new_price) * 100, 2
            ) if ticker in self.latest_prices else 0,
            "volume": random.randint(100000, 1000000),
            "timestamp": datetime.now().isoformat(),
        }


class PriceAlert:
    """Price alert system for monitoring price movements."""

    def __init__(self, feed: RealtimeDataFeed):
        """Initialize price alert system.

        Args:
            feed: Real-time data feed
        """
        self.feed = feed
        self.alerts: Dict[str, List[Dict]] = {}  # ticker -> list of alerts
        feed.register_callback(self._check_alerts)

    def add_alert(
        self,
        ticker: str,
        alert_type: str,
        threshold: float,
        callback: Optional[Callable] = None,
    ) -> str:
        """Add price alert.

        Args:
            ticker: Stock ticker
            alert_type: Type (price_above, price_below, change_pct)
            threshold: Alert threshold
            callback: Optional callback function

        Returns:
            Alert ID
        """
        alert_id = f"{ticker}_{alert_type}_{threshold}_{datetime.now().timestamp()}"

        alert = {
            "id": alert_id,
            "ticker": ticker,
            "type": alert_type,
            "threshold": threshold,
            "callback": callback,
            "created_at": datetime.now(),
            "triggered": False,
        }

        if ticker not in self.alerts:
            self.alerts[ticker] = []

        self.alerts[ticker].append(alert)

        logger.info(f"Added alert {alert_id} for {ticker}")

        return alert_id

    async def _check_alerts(self, ticker: str, price_data: Dict) -> None:
        """Check if any alerts should be triggered.

        Args:
            ticker: Stock ticker
            price_data: Current price data
        """
        if ticker not in self.alerts:
            return

        current_price = price_data.get("price", 0)
        change_pct = price_data.get("change_pct", 0)

        for alert in self.alerts[ticker]:
            if alert["triggered"]:
                continue

            should_trigger = False

            if alert["type"] == "price_above" and current_price > alert["threshold"]:
                should_trigger = True
            elif alert["type"] == "price_below" and current_price < alert["threshold"]:
                should_trigger = True
            elif alert["type"] == "change_pct" and abs(change_pct) > alert["threshold"]:
                should_trigger = True

            if should_trigger:
                alert["triggered"] = True
                logger.info(
                    f"Alert triggered: {ticker} {alert['type']} {alert['threshold']}"
                )

                if alert["callback"]:
                    try:
                        await alert["callback"](ticker, price_data, alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")

    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert.

        Args:
            alert_id: Alert identifier

        Returns:
            True if removed, False if not found
        """
        for ticker, alerts in self.alerts.items():
            for i, alert in enumerate(alerts):
                if alert["id"] == alert_id:
                    del alerts[i]
                    logger.info(f"Removed alert {alert_id}")
                    return True

        return False

    def get_active_alerts(self, ticker: Optional[str] = None) -> List[Dict]:
        """Get active alerts.

        Args:
            ticker: Optional ticker filter

        Returns:
            List of active alerts
        """
        if ticker:
            return [
                alert for alert in self.alerts.get(ticker, [])
                if not alert["triggered"]
            ]

        all_alerts = []
        for ticker_alerts in self.alerts.values():
            all_alerts.extend([a for a in ticker_alerts if not a["triggered"]])

        return all_alerts


class MarketDataStream:
    """Stream market data with aggregation."""

    def __init__(self, feed: RealtimeDataFeed):
        """Initialize market data stream.

        Args:
            feed: Real-time data feed
        """
        self.feed = feed
        self.bars: Dict[str, Dict] = {}  # ticker -> current bar
        feed.register_callback(self._update_bars)

    async def _update_bars(self, ticker: str, price_data: Dict) -> None:
        """Update OHLC bars with new tick.

        Args:
            ticker: Stock ticker
            price_data: Price tick data
        """
        price = price_data.get("price", 0)

        if ticker not in self.bars:
            self.bars[ticker] = {
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 0,
                "start_time": datetime.now(),
            }
        else:
            bar = self.bars[ticker]
            bar["high"] = max(bar["high"], price)
            bar["low"] = min(bar["low"], price)
            bar["close"] = price
            bar["volume"] += price_data.get("volume", 0)

    def get_current_bar(self, ticker: str) -> Optional[Dict]:
        """Get current OHLC bar.

        Args:
            ticker: Stock ticker

        Returns:
            Current bar data
        """
        return self.bars.get(ticker)

    def reset_bar(self, ticker: str) -> None:
        """Reset bar (for new time period).

        Args:
            ticker: Stock ticker
        """
        if ticker in self.bars:
            del self.bars[ticker]


class OrderBookTracker:
    """Track order book depth (placeholder for future)."""

    def __init__(self):
        """Initialize order book tracker."""
        self.order_books: Dict[str, Dict] = {}

    def update_order_book(
        self,
        ticker: str,
        bids: List[Dict],
        asks: List[Dict],
    ) -> None:
        """Update order book for ticker.

        Args:
            ticker: Stock ticker
            bids: List of bid orders
            asks: List of ask orders
        """
        self.order_books[ticker] = {
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.now(),
        }

    def get_best_bid_ask(self, ticker: str) -> Optional[Dict]:
        """Get best bid and ask prices.

        Args:
            ticker: Stock ticker

        Returns:
            Best bid/ask data
        """
        if ticker not in self.order_books:
            return None

        book = self.order_books[ticker]

        best_bid = book["bids"][0] if book["bids"] else None
        best_ask = book["asks"][0] if book["asks"] else None

        if not best_bid or not best_ask:
            return None

        return {
            "ticker": ticker,
            "best_bid": best_bid["price"],
            "best_ask": best_ask["price"],
            "spread": best_ask["price"] - best_bid["price"],
            "spread_pct": (best_ask["price"] - best_bid["price"]) / best_bid["price"] * 100,
        }
