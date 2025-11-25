"""Risk management system for trading."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.analytics.performance import PerformanceAnalytics
from src.core.trading.broker_adapter import Order, OrderSide
from src.database.models import DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RiskLimits:
    """Risk limit configuration."""

    def __init__(
        self,
        max_position_size_pct: float = 0.10,  # 10% of portfolio
        max_sector_exposure_pct: float = 0.30,  # 30% per sector
        max_portfolio_leverage: float = 1.0,  # No leverage
        max_daily_loss_pct: float = 0.02,  # 2% daily loss limit
        max_drawdown_pct: float = 0.10,  # 10% max drawdown
        min_cash_balance_pct: float = 0.05,  # 5% minimum cash
        max_correlation: float = 0.7,  # Max correlation between positions
    ):
        """Initialize risk limits.

        Args:
            max_position_size_pct: Maximum position size as % of portfolio
            max_sector_exposure_pct: Maximum sector exposure
            max_portfolio_leverage: Maximum leverage allowed
            max_daily_loss_pct: Maximum daily loss
            max_drawdown_pct: Maximum drawdown allowed
            min_cash_balance_pct: Minimum cash to maintain
            max_correlation: Maximum correlation between holdings
        """
        self.max_position_size_pct = max_position_size_pct
        self.max_sector_exposure_pct = max_sector_exposure_pct
        self.max_portfolio_leverage = max_portfolio_leverage
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.min_cash_balance_pct = min_cash_balance_pct
        self.max_correlation = max_correlation


class RiskManager:
    """Risk management system."""

    def __init__(
        self,
        db: Session,
        risk_limits: Optional[RiskLimits] = None,
    ):
        """Initialize risk manager.

        Args:
            db: Database session
            risk_limits: Risk limit configuration
        """
        self.db = db
        self.risk_limits = risk_limits or RiskLimits()
        self.analytics = PerformanceAnalytics(db)
        self.daily_pnl: Decimal = Decimal("0")
        self.daily_start_value: Optional[Decimal] = None

    def validate_order(
        self,
        order: Order,
        portfolio_value: Decimal,
        cash_available: Decimal,
        current_positions: Dict[str, Dict],
    ) -> tuple[bool, str]:
        """Validate order against risk limits.

        Args:
            order: Order to validate
            portfolio_value: Total portfolio value
            cash_available: Available cash
            current_positions: Current positions

        Returns:
            Tuple of (is_valid, reason)
        """
        logger.info(f"Validating order: {order.ticker} {order.side.value} {order.quantity}")

        # 1. Check cash availability for buy orders
        if order.side == OrderSide.BUY:
            cost = order.price * order.quantity if order.price else Decimal("0")

            if cost > cash_available:
                return False, f"Insufficient cash: need {cost}, have {cash_available}"

            # Check minimum cash requirement
            remaining_cash = cash_available - cost
            min_cash = portfolio_value * Decimal(str(self.risk_limits.min_cash_balance_pct))

            if remaining_cash < min_cash:
                return False, f"Would violate minimum cash requirement: {min_cash}"

        # 2. Check position size limit
        if order.side == OrderSide.BUY:
            position_value = order.price * order.quantity if order.price else Decimal("0")
            max_position_value = portfolio_value * Decimal(str(self.risk_limits.max_position_size_pct))

            # Add existing position if any
            if order.ticker in current_positions:
                existing_value = (
                    Decimal(str(current_positions[order.ticker]["current_price"]))
                    * current_positions[order.ticker]["quantity"]
                )
                position_value += existing_value

            if position_value > max_position_value:
                return False, f"Exceeds max position size: {position_value} > {max_position_value}"

        # 3. Check sell quantity
        if order.side == OrderSide.SELL:
            if order.ticker not in current_positions:
                return False, f"No position in {order.ticker}"

            available_qty = current_positions[order.ticker]["quantity"]
            if order.quantity > available_qty:
                return False, f"Insufficient shares: need {order.quantity}, have {available_qty}"

        # 4. Check leverage
        # This would require calculating total exposure vs equity

        # 5. All checks passed
        logger.info(f"Order validation passed for {order.ticker}")
        return True, "OK"

    def check_daily_loss_limit(
        self,
        current_portfolio_value: Decimal,
    ) -> tuple[bool, str]:
        """Check if daily loss limit is exceeded.

        Args:
            current_portfolio_value: Current portfolio value

        Returns:
            Tuple of (is_ok, message)
        """
        if self.daily_start_value is None:
            self.daily_start_value = current_portfolio_value
            return True, "OK"

        daily_pnl = current_portfolio_value - self.daily_start_value
        daily_return = daily_pnl / self.daily_start_value

        max_daily_loss = Decimal(str(-self.risk_limits.max_daily_loss_pct))

        if daily_return < max_daily_loss:
            return False, f"Daily loss limit exceeded: {daily_return:.2%}"

        return True, "OK"

    def calculate_position_size(
        self,
        ticker: str,
        portfolio_value: Decimal,
        volatility: Optional[float] = None,
        risk_per_trade_pct: float = 0.01,
    ) -> int:
        """Calculate optimal position size using risk-based sizing.

        Args:
            ticker: Stock ticker
            portfolio_value: Total portfolio value
            volatility: Stock volatility (optional)
            risk_per_trade_pct: Risk per trade as % of portfolio

        Returns:
            Recommended quantity
        """
        # Get current price
        latest_price = (
            self.db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker)
            .order_by(DailyPrice.date.desc())
            .first()
        )

        if not latest_price:
            logger.warning(f"No price data for {ticker}")
            return 0

        price = float(latest_price.close)

        # Calculate volatility if not provided
        if volatility is None:
            end_date = date.today()
            start_date = end_date - timedelta(days=252)
            volatility = self.analytics.calculate_volatility(
                ticker,
                start_date,
                end_date,
                annualized=False,
            )

        if not volatility or volatility == 0:
            # Fallback to simple % of portfolio
            max_position_value = float(portfolio_value) * self.risk_limits.max_position_size_pct
            quantity = int(max_position_value / price)
        else:
            # Risk-based position sizing
            # Position size = (Portfolio * Risk %) / (Price * Volatility)
            risk_amount = float(portfolio_value) * risk_per_trade_pct
            position_risk = price * volatility * 2  # 2x vol as stop distance

            if position_risk > 0:
                quantity = int(risk_amount / position_risk)
            else:
                quantity = 0

        # Apply max position size limit
        max_position_value = float(portfolio_value) * self.risk_limits.max_position_size_pct
        max_quantity = int(max_position_value / price)

        quantity = min(quantity, max_quantity)

        logger.info(
            f"Position size for {ticker}: {quantity} shares "
            f"(Price: {price:.2f}, Volatility: {volatility:.2%})"
        )

        return quantity

    def calculate_stop_loss(
        self,
        ticker: str,
        entry_price: Decimal,
        method: str = "atr",
        atr_multiplier: float = 2.0,
        fixed_pct: float = 0.05,
    ) -> Decimal:
        """Calculate stop loss price.

        Args:
            ticker: Stock ticker
            entry_price: Entry price
            method: Method (atr, fixed_pct, support)
            atr_multiplier: ATR multiplier for atr method
            fixed_pct: Fixed percentage for fixed_pct method

        Returns:
            Stop loss price
        """
        if method == "fixed_pct":
            stop_loss = entry_price * Decimal(str(1 - fixed_pct))

        elif method == "atr":
            # Calculate ATR (simplified)
            end_date = date.today()
            start_date = end_date - timedelta(days=20)

            prices = (
                self.db.query(DailyPrice)
                .filter(
                    DailyPrice.ticker == ticker,
                    DailyPrice.date >= start_date,
                    DailyPrice.date <= end_date,
                )
                .order_by(DailyPrice.date)
                .all()
            )

            if len(prices) > 1:
                true_ranges = [
                    max(
                        float(prices[i].high) - float(prices[i].low),
                        abs(float(prices[i].high) - float(prices[i-1].close)),
                        abs(float(prices[i].low) - float(prices[i-1].close)),
                    )
                    for i in range(1, len(prices))
                ]

                atr = sum(true_ranges) / len(true_ranges)
                stop_loss = entry_price - Decimal(str(atr * atr_multiplier))
            else:
                # Fallback to fixed percentage
                stop_loss = entry_price * Decimal(str(1 - fixed_pct))

        else:
            # Default to fixed percentage
            stop_loss = entry_price * Decimal(str(1 - fixed_pct))

        logger.info(f"Stop loss for {ticker}: {stop_loss:.2f} (entry: {entry_price:.2f})")

        return stop_loss

    def calculate_take_profit(
        self,
        entry_price: Decimal,
        stop_loss: Decimal,
        risk_reward_ratio: float = 2.0,
    ) -> Decimal:
        """Calculate take profit price.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Risk/reward ratio

        Returns:
            Take profit price
        """
        risk = entry_price - stop_loss
        reward = risk * Decimal(str(risk_reward_ratio))
        take_profit = entry_price + reward

        logger.info(
            f"Take profit: {take_profit:.2f} "
            f"(R:R {risk_reward_ratio}:1, Risk: {risk:.2f})"
        )

        return take_profit

    def calculate_var(
        self,
        positions: Dict[str, Dict],
        confidence_level: float = 0.95,
        time_horizon_days: int = 1,
    ) -> float:
        """Calculate Value at Risk (VaR).

        Args:
            positions: Current positions
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            time_horizon_days: Time horizon in days

        Returns:
            VaR amount
        """
        # Simplified VaR calculation using historical simulation
        import numpy as np

        total_var = 0.0

        for ticker, pos in positions.items():
            # Get historical returns
            end_date = date.today()
            start_date = end_date - timedelta(days=252)

            returns_data = self.analytics.calculate_returns(ticker, start_date, end_date)

            if not returns_data or not returns_data["daily_returns"]:
                continue

            daily_returns = np.array(returns_data["daily_returns"])

            # Calculate VaR for this position
            position_value = pos["quantity"] * pos["current_price"]

            # Scale returns for time horizon
            if time_horizon_days > 1:
                scaled_std = np.std(daily_returns) * np.sqrt(time_horizon_days)
            else:
                scaled_std = np.std(daily_returns)

            # VaR at confidence level
            from scipy import stats
            z_score = stats.norm.ppf(1 - confidence_level)
            position_var = position_value * abs(z_score * scaled_std)

            total_var += position_var

        logger.info(f"Portfolio VaR ({confidence_level:.0%}, {time_horizon_days}d): {total_var:.2f}")

        return total_var

    def generate_risk_report(
        self,
        portfolio_value: Decimal,
        cash_available: Decimal,
        positions: Dict[str, Dict],
    ) -> Dict:
        """Generate comprehensive risk report.

        Args:
            portfolio_value: Total portfolio value
            cash_available: Available cash
            positions: Current positions

        Returns:
            Risk report dictionary
        """
        # Calculate metrics
        cash_pct = float(cash_available / portfolio_value) if portfolio_value > 0 else 0

        position_concentration = {}
        for ticker, pos in positions.items():
            pos_value = pos["quantity"] * pos["current_price"]
            pos_pct = pos_value / float(portfolio_value) if portfolio_value > 0 else 0
            position_concentration[ticker] = pos_pct

        # Find largest positions
        sorted_positions = sorted(
            position_concentration.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Calculate VaR
        try:
            var_95 = self.calculate_var(positions, confidence_level=0.95)
        except:
            var_95 = 0.0

        report = {
            "portfolio_value": float(portfolio_value),
            "cash_available": float(cash_available),
            "cash_percentage": cash_pct,
            "number_of_positions": len(positions),
            "largest_position": {
                "ticker": sorted_positions[0][0] if sorted_positions else None,
                "percentage": sorted_positions[0][1] if sorted_positions else 0,
            },
            "position_concentration": dict(sorted_positions[:5]),  # Top 5
            "var_95_1day": var_95,
            "risk_limits": {
                "max_position_size": self.risk_limits.max_position_size_pct,
                "max_daily_loss": self.risk_limits.max_daily_loss_pct,
                "max_drawdown": self.risk_limits.max_drawdown_pct,
                "min_cash": self.risk_limits.min_cash_balance_pct,
            },
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def reset_daily_tracking(self) -> None:
        """Reset daily tracking (call at start of day)."""
        self.daily_start_value = None
        self.daily_pnl = Decimal("0")
        logger.info("Daily risk tracking reset")
