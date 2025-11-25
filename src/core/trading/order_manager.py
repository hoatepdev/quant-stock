"""Order management system."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.trading.broker_adapter import (
    BrokerAdapter,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
)
from src.core.trading.risk_manager import RiskManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OrderManager:
    """Centralized order management system."""

    def __init__(
        self,
        db: Session,
        broker: BrokerAdapter,
        risk_manager: RiskManager,
    ):
        """Initialize order manager.

        Args:
            db: Database session
            broker: Broker adapter
            risk_manager: Risk manager
        """
        self.db = db
        self.broker = broker
        self.risk_manager = risk_manager
        self.orders: Dict[str, Order] = {}
        self.pending_orders: List[Order] = []

    async def create_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Order:
        """Create a new order.

        Args:
            ticker: Stock ticker
            side: BUY or SELL
            quantity: Number of shares
            order_type: Order type
            price: Limit price
            stop_price: Stop price

        Returns:
            Created order
        """
        order = Order(
            ticker=ticker,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        self.orders[order.order_id] = order
        logger.info(f"Order created: {order.order_id}")

        return order

    async def submit_order(
        self,
        order: Order,
        validate_risk: bool = True,
    ) -> bool:
        """Submit order to broker.

        Args:
            order: Order to submit
            validate_risk: Whether to validate against risk limits

        Returns:
            True if submitted successfully
        """
        logger.info(f"Submitting order {order.order_id}: {order.ticker} {order.side.value}")

        # Get current portfolio state
        balance = await self.broker.get_account_balance()
        positions = await self.broker.get_positions()

        portfolio_value = Decimal(str(balance["total_value"]))
        cash_available = Decimal(str(balance["cash"]))

        # Convert positions to dict
        positions_dict = {
            pos["ticker"]: pos for pos in positions
        }

        # Validate risk if requested
        if validate_risk:
            is_valid, reason = self.risk_manager.validate_order(
                order,
                portfolio_value,
                cash_available,
                positions_dict,
            )

            if not is_valid:
                logger.warning(f"Order {order.order_id} rejected: {reason}")
                order.status = OrderStatus.REJECTED
                return False

        # Submit to broker
        try:
            broker_order_id = await self.broker.submit_order(order)
            order.broker_order_id = broker_order_id
            order.status = OrderStatus.SUBMITTED
            order.updated_at = datetime.now()

            self.pending_orders.append(order)

            logger.info(f"Order {order.order_id} submitted successfully: {broker_order_id}")
            return True

        except Exception as e:
            logger.error(f"Error submitting order {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return False

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        if order_id not in self.orders:
            logger.warning(f"Order {order_id} not found")
            return False

        order = self.orders[order_id]

        if order.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            logger.warning(f"Cannot cancel order {order_id} with status {order.status.value}")
            return False

        try:
            success = await self.broker.cancel_order(order.broker_order_id or order_id)

            if success:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()

                if order in self.pending_orders:
                    self.pending_orders.remove(order)

                logger.info(f"Order {order_id} cancelled successfully")
                return True

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")

        return False

    async def update_order_status(self, order_id: str) -> OrderStatus:
        """Update order status from broker.

        Args:
            order_id: Order ID

        Returns:
            Updated status
        """
        if order_id not in self.orders:
            return OrderStatus.REJECTED

        order = self.orders[order_id]

        try:
            status = await self.broker.get_order_status(order.broker_order_id or order_id)
            order.status = status
            order.updated_at = datetime.now()

            # Remove from pending if filled or cancelled
            if status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                if order in self.pending_orders:
                    self.pending_orders.remove(order)

            logger.debug(f"Order {order_id} status: {status.value}")
            return status

        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {e}")
            return OrderStatus.REJECTED

    async def update_all_pending_orders(self) -> None:
        """Update status of all pending orders."""
        for order in list(self.pending_orders):
            await self.update_order_status(order.order_id)

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order or None
        """
        return self.orders.get(order_id)

    def get_orders_by_ticker(self, ticker: str) -> List[Order]:
        """Get all orders for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            List of orders
        """
        return [
            order for order in self.orders.values()
            if order.ticker == ticker
        ]

    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status.

        Args:
            status: Order status

        Returns:
            List of orders
        """
        return [
            order for order in self.orders.values()
            if order.status == status
        ]

    def get_filled_orders(
        self,
        since: Optional[datetime] = None,
    ) -> List[Order]:
        """Get filled orders.

        Args:
            since: Optional datetime filter

        Returns:
            List of filled orders
        """
        filled = self.get_orders_by_status(OrderStatus.FILLED)

        if since:
            filled = [
                order for order in filled
                if order.updated_at >= since
            ]

        return filled

    async def create_market_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        submit: bool = True,
    ) -> Order:
        """Create and optionally submit market order.

        Args:
            ticker: Stock ticker
            side: BUY or SELL
            quantity: Number of shares
            submit: Whether to submit immediately

        Returns:
            Created order
        """
        order = await self.create_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
        )

        if submit:
            await self.submit_order(order)

        return order

    async def create_limit_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        price: Decimal,
        submit: bool = True,
    ) -> Order:
        """Create and optionally submit limit order.

        Args:
            ticker: Stock ticker
            side: BUY or SELL
            quantity: Number of shares
            price: Limit price
            submit: Whether to submit immediately

        Returns:
            Created order
        """
        order = await self.create_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            price=price,
        )

        if submit:
            await self.submit_order(order)

        return order

    async def create_stop_order(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        stop_price: Decimal,
        limit_price: Optional[Decimal] = None,
        submit: bool = True,
    ) -> Order:
        """Create and optionally submit stop order.

        Args:
            ticker: Stock ticker
            side: BUY or SELL
            quantity: Number of shares
            stop_price: Stop price
            limit_price: Optional limit price (for stop-limit)
            submit: Whether to submit immediately

        Returns:
            Created order
        """
        order_type = OrderType.STOP_LIMIT if limit_price else OrderType.STOP

        order = await self.create_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=limit_price,
            stop_price=stop_price,
        )

        if submit:
            await self.submit_order(order)

        return order

    def get_order_summary(self) -> Dict:
        """Get summary of all orders.

        Returns:
            Order summary dictionary
        """
        summary = {
            "total_orders": len(self.orders),
            "pending": len(self.get_orders_by_status(OrderStatus.PENDING)),
            "submitted": len(self.get_orders_by_status(OrderStatus.SUBMITTED)),
            "filled": len(self.get_orders_by_status(OrderStatus.FILLED)),
            "cancelled": len(self.get_orders_by_status(OrderStatus.CANCELLED)),
            "rejected": len(self.get_orders_by_status(OrderStatus.REJECTED)),
        }

        return summary

    def export_orders(
        self,
        status_filter: Optional[OrderStatus] = None,
    ) -> List[Dict]:
        """Export orders to list of dictionaries.

        Args:
            status_filter: Optional status filter

        Returns:
            List of order dictionaries
        """
        if status_filter:
            orders = self.get_orders_by_status(status_filter)
        else:
            orders = list(self.orders.values())

        return [order.to_dict() for order in orders]
