"""Position tracking and portfolio management."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.analytics.performance import PerformanceAnalytics
from src.core.trading.broker_adapter import BrokerAdapter
from src.database.models import DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Position:
    """Trading position."""

    def __init__(
        self,
        ticker: str,
        quantity: int,
        average_price: Decimal,
        current_price: Optional[Decimal] = None,
    ):
        """Initialize position.

        Args:
            ticker: Stock ticker
            quantity: Number of shares
            average_price: Average entry price
            current_price: Current market price
        """
        self.ticker = ticker
        self.quantity = quantity
        self.average_price = average_price
        self.current_price = current_price or average_price
        self.opened_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def market_value(self) -> Decimal:
        """Get current market value."""
        return self.current_price * self.quantity

    @property
    def cost_basis(self) -> Decimal:
        """Get cost basis."""
        return self.average_price * self.quantity

    @property
    def unrealized_pnl(self) -> Decimal:
        """Get unrealized P&L."""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Get unrealized P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return float(self.unrealized_pnl / self.cost_basis)

    def update_price(self, price: Decimal) -> None:
        """Update current price.

        Args:
            price: New price
        """
        self.current_price = price
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "average_price": float(self.average_price),
            "current_price": float(self.current_price),
            "market_value": float(self.market_value),
            "cost_basis": float(self.cost_basis),
            "unrealized_pnl": float(self.unrealized_pnl),
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "opened_at": self.opened_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PositionTracker:
    """Track and manage portfolio positions."""

    def __init__(
        self,
        db: Session,
        broker: BrokerAdapter,
    ):
        """Initialize position tracker.

        Args:
            db: Database session
            broker: Broker adapter
        """
        self.db = db
        self.broker = broker
        self.positions: Dict[str, Position] = {}
        self.analytics = PerformanceAnalytics(db)
        self.cash: Decimal = Decimal("0")

    async def sync_with_broker(self) -> None:
        """Sync positions with broker."""
        logger.info("Syncing positions with broker...")

        # Get broker positions
        broker_positions = await self.broker.get_positions()

        # Clear current positions
        self.positions = {}

        # Load broker positions
        for pos_data in broker_positions:
            position = Position(
                ticker=pos_data["ticker"],
                quantity=pos_data["quantity"],
                average_price=Decimal(str(pos_data["average_price"])),
                current_price=Decimal(str(pos_data.get("current_price", pos_data["average_price"]))),
            )
            self.positions[pos_data["ticker"]] = position

        # Get cash balance
        balance = await self.broker.get_account_balance()
        self.cash = Decimal(str(balance["cash"]))

        logger.info(f"Synced {len(self.positions)} positions, cash: {self.cash:,.2f}")

    async def update_prices(self) -> None:
        """Update current prices for all positions."""
        for ticker, position in self.positions.items():
            # Get latest price from database
            latest_price = (
                self.db.query(DailyPrice)
                .filter(DailyPrice.ticker == ticker)
                .order_by(DailyPrice.date.desc())
                .first()
            )

            if latest_price:
                position.update_price(latest_price.close)

    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Position or None
        """
        return self.positions.get(ticker)

    def get_all_positions(self) -> List[Position]:
        """Get all positions.

        Returns:
            List of positions
        """
        return list(self.positions.values())

    def get_portfolio_value(self) -> Decimal:
        """Get total portfolio value.

        Returns:
            Total value (cash + positions)
        """
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary.

        Returns:
            Portfolio summary dictionary
        """
        total_value = self.get_portfolio_value()
        positions_value = sum(pos.market_value for pos in self.positions.values())
        total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

        return {
            "total_value": float(total_value),
            "cash": float(self.cash),
            "positions_value": float(positions_value),
            "cash_pct": float(self.cash / total_value) if total_value > 0 else 0,
            "number_of_positions": len(self.positions),
            "total_unrealized_pnl": float(total_pnl),
            "total_unrealized_pnl_pct": float(total_pnl / positions_value) if positions_value > 0 else 0,
        }

    def get_position_breakdown(self) -> List[Dict]:
        """Get detailed position breakdown.

        Returns:
            List of position details
        """
        total_value = self.get_portfolio_value()

        breakdown = []
        for position in self.positions.values():
            pos_dict = position.to_dict()
            pos_dict["weight"] = float(position.market_value / total_value) if total_value > 0 else 0
            breakdown.append(pos_dict)

        # Sort by weight
        breakdown.sort(key=lambda x: x["weight"], reverse=True)

        return breakdown

    def calculate_portfolio_metrics(
        self,
        start_date: Optional[date] = None,
    ) -> Dict:
        """Calculate portfolio-level performance metrics.

        Args:
            start_date: Optional start date for calculation

        Returns:
            Portfolio metrics
        """
        if not start_date:
            start_date = date.today() - timedelta(days=365)

        end_date = date.today()

        # Calculate metrics for each position
        position_metrics = []

        for position in self.positions.values():
            metrics = self.analytics.calculate_all_metrics(
                position.ticker,
                start_date,
                end_date,
            )

            if metrics["returns"]["total"] is not None:
                position_metrics.append({
                    "ticker": position.ticker,
                    "weight": float(position.market_value / self.get_portfolio_value()),
                    "return": metrics["returns"]["total"],
                    "volatility": metrics["risk"]["volatility"],
                    "sharpe": metrics["risk"]["sharpe_ratio"],
                })

        # Calculate weighted portfolio return
        portfolio_return = sum(
            pm["weight"] * pm["return"]
            for pm in position_metrics
            if pm["return"] is not None
        )

        # Calculate portfolio volatility (simplified)
        portfolio_vol = sum(
            pm["weight"] * pm["volatility"]
            for pm in position_metrics
            if pm["volatility"] is not None
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "portfolio_return": portfolio_return,
            "portfolio_volatility": portfolio_vol,
            "portfolio_sharpe": portfolio_return / portfolio_vol if portfolio_vol > 0 else 0,
            "positions": position_metrics,
        }

    def get_top_performers(self, limit: int = 5) -> List[Dict]:
        """Get top performing positions.

        Args:
            limit: Number of top performers

        Returns:
            List of top performers
        """
        positions = [pos.to_dict() for pos in self.positions.values()]
        positions.sort(key=lambda x: x["unrealized_pnl_pct"], reverse=True)

        return positions[:limit]

    def get_worst_performers(self, limit: int = 5) -> List[Dict]:
        """Get worst performing positions.

        Args:
            limit: Number of worst performers

        Returns:
            List of worst performers
        """
        positions = [pos.to_dict() for pos in self.positions.values()]
        positions.sort(key=lambda x: x["unrealized_pnl_pct"])

        return positions[:limit]

    def export_positions(self) -> List[Dict]:
        """Export all positions.

        Returns:
            List of position dictionaries
        """
        return [pos.to_dict() for pos in self.positions.values()]
