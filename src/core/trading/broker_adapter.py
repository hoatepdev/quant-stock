"""Broker adapter for trading integration."""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class OrderType(Enum):
    """Order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(Enum):
    """Order sides."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class Order:
    """Trading order."""

    def __init__(
        self,
        ticker: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        order_id: Optional[str] = None,
    ):
        """Initialize order.

        Args:
            ticker: Stock ticker
            side: BUY or SELL
            order_type: Order type
            quantity: Number of shares
            price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            order_id: Unique order identifier
        """
        self.ticker = ticker
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.order_id = order_id or f"{ticker}_{datetime.now().timestamp()}"
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0
        self.average_fill_price: Optional[Decimal] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.broker_order_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert order to dictionary."""
        return {
            "order_id": self.order_id,
            "broker_order_id": self.broker_order_id,
            "ticker": self.ticker,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "filled_quantity": self.filled_quantity,
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "average_fill_price": float(self.average_fill_price) if self.average_fill_price else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class BrokerAdapter(ABC):
    """Abstract broker adapter interface."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker.

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from broker."""
        pass

    @abstractmethod
    async def submit_order(self, order: Order) -> str:
        """Submit order to broker.

        Args:
            order: Order to submit

        Returns:
            Broker order ID
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get order status.

        Args:
            order_id: Order ID

        Returns:
            Order status
        """
        pass

    @abstractmethod
    async def get_account_balance(self) -> Dict:
        """Get account balance.

        Returns:
            Dictionary with balance information
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict]:
        """Get current positions.

        Returns:
            List of position dictionaries
        """
        pass


class SSIBrokerAdapter(BrokerAdapter):
    """SSI broker adapter (placeholder implementation)."""

    def __init__(self, api_key: str, secret_key: str):
        """Initialize SSI broker adapter.

        Args:
            api_key: SSI API key
            secret_key: SSI secret key
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.connected = False

    async def connect(self) -> bool:
        """Connect to SSI broker."""
        logger.info("Connecting to SSI broker...")

        # Placeholder: In production, implement actual SSI trading API connection
        # This would involve:
        # 1. Authentication
        # 2. WebSocket connection for order updates
        # 3. Session management

        self.connected = True
        logger.info("Connected to SSI broker (simulated)")
        return True

    async def disconnect(self) -> None:
        """Disconnect from SSI broker."""
        logger.info("Disconnecting from SSI broker...")
        self.connected = False

    async def submit_order(self, order: Order) -> str:
        """Submit order to SSI.

        Args:
            order: Order to submit

        Returns:
            Broker order ID
        """
        if not self.connected:
            raise Exception("Not connected to broker")

        logger.info(f"Submitting order: {order.ticker} {order.side.value} {order.quantity}")

        # Placeholder: Implement actual SSI order submission
        # This would use SSI's trading API

        # Simulate order submission
        broker_order_id = f"SSI_{order.order_id}"
        order.broker_order_id = broker_order_id
        order.status = OrderStatus.SUBMITTED
        order.updated_at = datetime.now()

        logger.info(f"Order submitted: {broker_order_id}")

        return broker_order_id

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on SSI.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled
        """
        logger.info(f"Cancelling order: {order_id}")

        # Placeholder: Implement SSI order cancellation

        return True

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get order status from SSI.

        Args:
            order_id: Order ID

        Returns:
            Order status
        """
        # Placeholder: Query SSI for order status

        return OrderStatus.FILLED

    async def get_account_balance(self) -> Dict:
        """Get account balance from SSI.

        Returns:
            Balance information
        """
        # Placeholder: Get actual balance from SSI

        return {
            "cash": 100000000.0,  # 100M VND
            "buying_power": 200000000.0,  # With margin
            "total_value": 150000000.0,
            "currency": "VND",
        }

    async def get_positions(self) -> List[Dict]:
        """Get positions from SSI.

        Returns:
            List of positions
        """
        # Placeholder: Get actual positions from SSI

        return [
            {
                "ticker": "VCB",
                "quantity": 1000,
                "average_price": 95.5,
                "current_price": 98.0,
                "unrealized_pnl": 2500.0,
            }
        ]


class DNSEBrokerAdapter(BrokerAdapter):
    """DNSE broker adapter (placeholder implementation)."""

    def __init__(self, api_key: str, secret_key: str):
        """Initialize DNSE broker adapter.

        Args:
            api_key: DNSE API key
            secret_key: DNSE secret key
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.connected = False

    async def connect(self) -> bool:
        """Connect to DNSE broker."""
        logger.info("Connecting to DNSE broker...")
        self.connected = True
        logger.info("Connected to DNSE broker (simulated)")
        return True

    async def disconnect(self) -> None:
        """Disconnect from DNSE broker."""
        logger.info("Disconnecting from DNSE broker...")
        self.connected = False

    async def submit_order(self, order: Order) -> str:
        """Submit order to DNSE."""
        if not self.connected:
            raise Exception("Not connected to broker")

        logger.info(f"Submitting order to DNSE: {order.ticker} {order.side.value} {order.quantity}")

        broker_order_id = f"DNSE_{order.order_id}"
        order.broker_order_id = broker_order_id
        order.status = OrderStatus.SUBMITTED
        order.updated_at = datetime.now()

        return broker_order_id

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on DNSE."""
        logger.info(f"Cancelling DNSE order: {order_id}")
        return True

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get order status from DNSE."""
        return OrderStatus.FILLED

    async def get_account_balance(self) -> Dict:
        """Get account balance from DNSE."""
        return {
            "cash": 100000000.0,
            "buying_power": 200000000.0,
            "total_value": 150000000.0,
            "currency": "VND",
        }

    async def get_positions(self) -> List[Dict]:
        """Get positions from DNSE."""
        return []


class PaperTradingAdapter(BrokerAdapter):
    """Paper trading adapter for simulation."""

    def __init__(self, initial_cash: Decimal = Decimal("100000000")):
        """Initialize paper trading adapter.

        Args:
            initial_cash: Initial cash balance
        """
        self.cash = initial_cash
        self.positions: Dict[str, Dict] = {}
        self.orders: Dict[str, Order] = {}
        self.filled_orders: List[Order] = []
        self.connected = False

    async def connect(self) -> bool:
        """Connect to paper trading."""
        logger.info("Starting paper trading session...")
        self.connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from paper trading."""
        logger.info("Ending paper trading session...")
        self.connected = False

    async def submit_order(self, order: Order) -> str:
        """Submit order for paper trading.

        Args:
            order: Order to submit

        Returns:
            Order ID
        """
        if not self.connected:
            raise Exception("Paper trading not started")

        logger.info(
            f"Paper trade: {order.side.value} {order.quantity} {order.ticker} "
            f"@ {order.price if order.price else 'MARKET'}"
        )

        # Store order
        self.orders[order.order_id] = order
        order.status = OrderStatus.SUBMITTED

        # Simulate immediate fill for paper trading
        await self._simulate_fill(order)

        return order.order_id

    async def _simulate_fill(self, order: Order) -> None:
        """Simulate order fill.

        Args:
            order: Order to fill
        """
        # Use limit price or simulate market price
        fill_price = order.price if order.price else Decimal("100")

        # Update order
        order.filled_quantity = order.quantity
        order.average_fill_price = fill_price
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now()

        # Update positions
        if order.side == OrderSide.BUY:
            cost = fill_price * order.quantity
            if cost > self.cash:
                order.status = OrderStatus.REJECTED
                logger.warning(f"Insufficient cash for order {order.order_id}")
                return

            self.cash -= cost

            if order.ticker in self.positions:
                pos = self.positions[order.ticker]
                total_qty = pos["quantity"] + order.quantity
                pos["average_price"] = (
                    (pos["average_price"] * pos["quantity"] + fill_price * order.quantity)
                    / total_qty
                )
                pos["quantity"] = total_qty
            else:
                self.positions[order.ticker] = {
                    "quantity": order.quantity,
                    "average_price": fill_price,
                }

        elif order.side == OrderSide.SELL:
            if order.ticker not in self.positions:
                order.status = OrderStatus.REJECTED
                logger.warning(f"No position to sell for {order.ticker}")
                return

            pos = self.positions[order.ticker]
            if pos["quantity"] < order.quantity:
                order.status = OrderStatus.REJECTED
                logger.warning(f"Insufficient shares to sell for {order.ticker}")
                return

            proceeds = fill_price * order.quantity
            self.cash += proceeds

            pos["quantity"] -= order.quantity
            if pos["quantity"] == 0:
                del self.positions[order.ticker]

        self.filled_orders.append(order)
        logger.info(f"Order filled: {order.order_id} @ {fill_price}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order.

        Args:
            order_id: Order ID

        Returns:
            True if cancelled
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING or order.status == OrderStatus.SUBMITTED:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                logger.info(f"Order cancelled: {order_id}")
                return True

        return False

    async def get_order_status(self, order_id: str) -> OrderStatus:
        """Get order status.

        Args:
            order_id: Order ID

        Returns:
            Order status
        """
        if order_id in self.orders:
            return self.orders[order_id].status

        return OrderStatus.REJECTED

    async def get_account_balance(self) -> Dict:
        """Get account balance.

        Returns:
            Balance information
        """
        # Calculate total value
        total_value = float(self.cash)

        for ticker, pos in self.positions.items():
            # In real implementation, get current market price
            # For now, use average price
            total_value += float(pos["average_price"]) * pos["quantity"]

        return {
            "cash": float(self.cash),
            "buying_power": float(self.cash),
            "total_value": total_value,
            "currency": "VND",
        }

    async def get_positions(self) -> List[Dict]:
        """Get current positions.

        Returns:
            List of positions
        """
        positions = []

        for ticker, pos in self.positions.items():
            positions.append({
                "ticker": ticker,
                "quantity": pos["quantity"],
                "average_price": float(pos["average_price"]),
                "current_price": float(pos["average_price"]),  # Placeholder
                "unrealized_pnl": 0.0,  # Placeholder
            })

        return positions
