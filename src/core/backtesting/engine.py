"""Backtesting engine for trading strategies."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Callable

import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Position:
    """Represents a trading position."""

    def __init__(
        self,
        ticker: str,
        entry_date: date,
        entry_price: Decimal,
        shares: int,
        position_type: str = "LONG",
    ):
        """Initialize position.

        Args:
            ticker: Stock ticker
            entry_date: Date position was opened
            entry_price: Entry price per share
            shares: Number of shares
            position_type: LONG or SHORT
        """
        self.ticker = ticker
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.shares = shares
        self.position_type = position_type
        self.exit_date: Optional[date] = None
        self.exit_price: Optional[Decimal] = None
        self.pnl: Optional[Decimal] = None
        self.pnl_pct: Optional[float] = None

    def close(self, exit_date: date, exit_price: Decimal) -> None:
        """Close the position.

        Args:
            exit_date: Date position was closed
            exit_price: Exit price per share
        """
        self.exit_date = exit_date
        self.exit_price = exit_price

        if self.position_type == "LONG":
            self.pnl = (exit_price - self.entry_price) * self.shares
            self.pnl_pct = float((exit_price - self.entry_price) / self.entry_price)
        else:  # SHORT
            self.pnl = (self.entry_price - exit_price) * self.shares
            self.pnl_pct = float((self.entry_price - exit_price) / self.entry_price)

    def get_value(self, current_price: Decimal) -> Decimal:
        """Get current value of position.

        Args:
            current_price: Current market price

        Returns:
            Current position value
        """
        if self.position_type == "LONG":
            return current_price * self.shares
        else:  # SHORT
            return (self.entry_price * 2 - current_price) * self.shares

    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            "ticker": self.ticker,
            "entry_date": self.entry_date,
            "entry_price": float(self.entry_price),
            "exit_date": self.exit_date,
            "exit_price": float(self.exit_price) if self.exit_price else None,
            "shares": self.shares,
            "position_type": self.position_type,
            "pnl": float(self.pnl) if self.pnl else None,
            "pnl_pct": self.pnl_pct,
        }


class Portfolio:
    """Represents a trading portfolio."""

    def __init__(self, initial_capital: Decimal, commission_rate: float = 0.0015):
        """Initialize portfolio.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate (default 0.15%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: List[Position] = []
        self.closed_positions: List[Position] = []
        self.equity_curve: List[Dict] = []

    def buy(
        self,
        ticker: str,
        date: date,
        price: Decimal,
        shares: int,
    ) -> Optional[Position]:
        """Buy shares (open long position).

        Args:
            ticker: Stock ticker
            date: Trade date
            price: Entry price
            shares: Number of shares

        Returns:
            Position object or None if insufficient funds
        """
        cost = price * shares
        commission = cost * Decimal(str(self.commission_rate))
        total_cost = cost + commission

        if total_cost > self.cash:
            logger.warning(
                f"Insufficient funds to buy {shares} shares of {ticker} "
                f"at {price}. Need {total_cost}, have {self.cash}"
            )
            return None

        position = Position(ticker, date, price, shares, "LONG")
        self.positions.append(position)
        self.cash -= total_cost

        logger.info(
            f"Bought {shares} shares of {ticker} at {price} on {date}. "
            f"Commission: {commission:.2f}, Remaining cash: {self.cash:.2f}"
        )

        return position

    def sell(
        self,
        ticker: str,
        date: date,
        price: Decimal,
        shares: Optional[int] = None,
    ) -> Optional[Position]:
        """Sell shares (close long position).

        Args:
            ticker: Stock ticker
            date: Trade date
            price: Exit price
            shares: Number of shares (None = sell all)

        Returns:
            Closed position or None
        """
        # Find position for ticker
        position = next((p for p in self.positions if p.ticker == ticker), None)

        if not position:
            logger.warning(f"No position found for {ticker}")
            return None

        shares_to_sell = shares if shares else position.shares

        if shares_to_sell > position.shares:
            logger.warning(
                f"Cannot sell {shares_to_sell} shares, only have {position.shares}"
            )
            return None

        # Calculate proceeds
        proceeds = price * shares_to_sell
        commission = proceeds * Decimal(str(self.commission_rate))
        net_proceeds = proceeds - commission

        # Close position
        position.close(date, price)
        self.cash += net_proceeds

        # Remove from active positions
        self.positions.remove(position)
        self.closed_positions.append(position)

        logger.info(
            f"Sold {shares_to_sell} shares of {ticker} at {price} on {date}. "
            f"P&L: {position.pnl:.2f} ({position.pnl_pct:.2%}), "
            f"Commission: {commission:.2f}, Cash: {self.cash:.2f}"
        )

        return position

    def get_total_value(self, current_prices: Dict[str, Decimal]) -> Decimal:
        """Get total portfolio value.

        Args:
            current_prices: Dictionary of current prices by ticker

        Returns:
            Total portfolio value
        """
        total = self.cash

        for position in self.positions:
            if position.ticker in current_prices:
                total += position.get_value(current_prices[position.ticker])

        return total

    def get_statistics(self) -> Dict:
        """Get portfolio performance statistics.

        Returns:
            Dictionary of statistics
        """
        if not self.closed_positions:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
            }

        winning = [p for p in self.closed_positions if p.pnl and p.pnl > 0]
        losing = [p for p in self.closed_positions if p.pnl and p.pnl <= 0]

        total_pnl = sum(p.pnl for p in self.closed_positions if p.pnl)
        avg_pnl = total_pnl / len(self.closed_positions)

        avg_win = sum(p.pnl for p in winning) / len(winning) if winning else Decimal(0)
        avg_loss = sum(p.pnl for p in losing) / len(losing) if losing else Decimal(0)

        return {
            "total_trades": len(self.closed_positions),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": len(winning) / len(self.closed_positions),
            "total_pnl": float(total_pnl),
            "total_pnl_pct": float(total_pnl / self.initial_capital),
            "avg_pnl": float(avg_pnl),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "profit_factor": float(abs(avg_win / avg_loss)) if avg_loss != 0 else 0,
        }


class BacktestEngine:
    """Backtesting engine for trading strategies."""

    def __init__(
        self,
        db: Session,
        initial_capital: Decimal = Decimal("100000000"),  # 100M VND
        commission_rate: float = 0.0015,
    ):
        """Initialize backtest engine.

        Args:
            db: Database session
            initial_capital: Starting capital
            commission_rate: Commission rate
        """
        self.db = db
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.portfolio: Optional[Portfolio] = None

    def run(
        self,
        strategy: Callable,
        tickers: List[str],
        start_date: date,
        end_date: date,
        rebalance_frequency: str = "DAILY",  # DAILY, WEEKLY, MONTHLY
    ) -> Dict:
        """Run backtest with given strategy.

        Args:
            strategy: Strategy function that returns signals
            tickers: List of tickers to trade
            start_date: Backtest start date
            end_date: Backtest end date
            rebalance_frequency: How often to rebalance

        Returns:
            Backtest results dictionary
        """
        logger.info(
            f"Starting backtest from {start_date} to {end_date} "
            f"for {len(tickers)} tickers"
        )

        # Initialize portfolio
        self.portfolio = Portfolio(self.initial_capital, self.commission_rate)

        # Get all price data
        price_data = self._load_price_data(tickers, start_date, end_date)

        if not price_data:
            logger.error("No price data available for backtest")
            return {}

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(price_data)
        df = df.pivot_table(
            index="date",
            columns="ticker",
            values=["open", "high", "low", "close", "volume"]
        )

        # Run backtest day by day
        trading_days = sorted(df.index.unique())

        for trading_day in trading_days:
            # Get current prices
            current_prices = {}
            for ticker in tickers:
                try:
                    current_prices[ticker] = Decimal(
                        str(df.loc[trading_day, ("close", ticker)])
                    )
                except:
                    continue

            # Get signals from strategy
            signals = strategy(df.loc[:trading_day], self.portfolio, current_prices)

            # Execute trades based on signals
            if signals:
                self._execute_signals(signals, trading_day, current_prices)

            # Record portfolio value
            portfolio_value = self.portfolio.get_total_value(current_prices)
            self.portfolio.equity_curve.append({
                "date": trading_day,
                "value": float(portfolio_value),
                "cash": float(self.portfolio.cash),
                "positions": len(self.portfolio.positions),
            })

        # Close all remaining positions
        final_prices = {
            ticker: Decimal(str(df.iloc[-1][("close", ticker)]))
            for ticker in tickers
            if ("close", ticker) in df.columns
        }

        for position in list(self.portfolio.positions):
            if position.ticker in final_prices:
                self.portfolio.sell(
                    position.ticker,
                    end_date,
                    final_prices[position.ticker]
                )

        # Calculate final statistics
        stats = self.portfolio.get_statistics()
        final_value = self.portfolio.get_total_value({})

        results = {
            "initial_capital": float(self.initial_capital),
            "final_value": float(final_value),
            "total_return": float((final_value - self.initial_capital) / self.initial_capital),
            "statistics": stats,
            "equity_curve": self.portfolio.equity_curve,
            "trades": [p.to_dict() for p in self.portfolio.closed_positions],
        }

        logger.info(
            f"Backtest complete. "
            f"Initial: {self.initial_capital:,.0f}, "
            f"Final: {final_value:,.0f}, "
            f"Return: {results['total_return']:.2%}"
        )

        return results

    def _load_price_data(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
    ) -> List[Dict]:
        """Load price data for tickers.

        Args:
            tickers: List of tickers
            start_date: Start date
            end_date: End date

        Returns:
            List of price records
        """
        prices = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.ticker.in_(tickers),
                DailyPrice.date >= start_date,
                DailyPrice.date <= end_date,
            )
            .order_by(DailyPrice.date)
            .all()
        )

        return [
            {
                "ticker": p.ticker,
                "date": p.date,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": p.volume,
            }
            for p in prices
        ]

    def _execute_signals(
        self,
        signals: Dict[str, str],
        trade_date: date,
        current_prices: Dict[str, Decimal],
    ) -> None:
        """Execute trading signals.

        Args:
            signals: Dictionary of ticker -> signal (BUY, SELL, HOLD)
            trade_date: Trade date
            current_prices: Current prices dictionary
        """
        for ticker, signal in signals.items():
            if ticker not in current_prices:
                continue

            price = current_prices[ticker]

            if signal == "BUY":
                # Use 10% of available cash per position
                position_size = self.portfolio.cash * Decimal("0.1")
                shares = int(position_size / price)

                if shares > 0:
                    self.portfolio.buy(ticker, trade_date, price, shares)

            elif signal == "SELL":
                self.portfolio.sell(ticker, trade_date, price)
