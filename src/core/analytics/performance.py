"""Performance analytics and metrics calculation."""
from datetime import date, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceAnalytics:
    """Calculate portfolio and stock performance metrics."""

    def __init__(self, db: Session):
        """Initialize performance analytics.

        Args:
            db: Database session
        """
        self.db = db

    def calculate_returns(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> Optional[Dict]:
        """Calculate returns for a stock.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date

        Returns:
            Returns metrics dictionary
        """
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

        if len(prices) < 2:
            return None

        closes = [float(p.close) for p in prices]

        # Total return
        total_return = (closes[-1] - closes[0]) / closes[0]

        # Calculate daily returns
        daily_returns = [
            (closes[i] - closes[i-1]) / closes[i-1]
            for i in range(1, len(closes))
        ]

        # Annualized return
        years = (end_date - start_date).days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "daily_returns": daily_returns,
        }

    def calculate_volatility(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        annualized: bool = True,
    ) -> Optional[float]:
        """Calculate volatility (standard deviation of returns).

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
            annualized: Whether to annualize

        Returns:
            Volatility value
        """
        returns_data = self.calculate_returns(ticker, start_date, end_date)

        if not returns_data or not returns_data["daily_returns"]:
            return None

        volatility = np.std(returns_data["daily_returns"])

        if annualized:
            # Annualize assuming 252 trading days
            volatility = volatility * np.sqrt(252)

        return float(volatility)

    def calculate_sharpe_ratio(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        risk_free_rate: float = 0.03,
    ) -> Optional[float]:
        """Calculate Sharpe ratio.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        returns_data = self.calculate_returns(ticker, start_date, end_date)

        if not returns_data:
            return None

        volatility = self.calculate_volatility(ticker, start_date, end_date, annualized=True)

        if not volatility or volatility == 0:
            return None

        excess_return = returns_data["annualized_return"] - risk_free_rate
        sharpe = excess_return / volatility

        return float(sharpe)

    def calculate_max_drawdown(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> Optional[Dict]:
        """Calculate maximum drawdown.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date

        Returns:
            Max drawdown metrics
        """
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

        if len(prices) < 2:
            return None

        closes = [float(p.close) for p in prices]
        dates = [p.date for p in prices]

        # Calculate cumulative maximum
        cum_max = np.maximum.accumulate(closes)

        # Calculate drawdown
        drawdown = (closes - cum_max) / cum_max

        # Find maximum drawdown
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)

        # Find peak before max drawdown
        peak_idx = np.argmax(closes[:max_dd_idx+1])

        return {
            "ticker": ticker,
            "max_drawdown": float(max_dd),
            "max_drawdown_pct": float(max_dd * 100),
            "peak_date": dates[peak_idx],
            "trough_date": dates[max_dd_idx],
            "recovery_date": None,  # Could calculate recovery time
        }

    def calculate_beta(
        self,
        ticker: str,
        market_ticker: str,
        start_date: date,
        end_date: date,
    ) -> Optional[float]:
        """Calculate beta (systematic risk).

        Args:
            ticker: Stock ticker
            market_ticker: Market index ticker
            start_date: Start date
            end_date: End date

        Returns:
            Beta value
        """
        # Get stock returns
        stock_returns = self.calculate_returns(ticker, start_date, end_date)

        # Get market returns
        market_returns = self.calculate_returns(market_ticker, start_date, end_date)

        if not stock_returns or not market_returns:
            return None

        stock_ret = stock_returns["daily_returns"]
        market_ret = market_returns["daily_returns"]

        # Align lengths
        min_len = min(len(stock_ret), len(market_ret))
        stock_ret = stock_ret[:min_len]
        market_ret = market_ret[:min_len]

        # Calculate beta using covariance
        covariance = np.cov(stock_ret, market_ret)[0][1]
        market_variance = np.var(market_ret)

        if market_variance == 0:
            return None

        beta = covariance / market_variance

        return float(beta)

    def calculate_alpha(
        self,
        ticker: str,
        market_ticker: str,
        start_date: date,
        end_date: date,
        risk_free_rate: float = 0.03,
    ) -> Optional[float]:
        """Calculate Jensen's alpha.

        Args:
            ticker: Stock ticker
            market_ticker: Market index ticker
            start_date: Start date
            end_date: End date
            risk_free_rate: Annual risk-free rate

        Returns:
            Alpha value
        """
        stock_returns = self.calculate_returns(ticker, start_date, end_date)
        market_returns = self.calculate_returns(market_ticker, start_date, end_date)
        beta = self.calculate_beta(ticker, market_ticker, start_date, end_date)

        if not stock_returns or not market_returns or beta is None:
            return None

        # Jensen's alpha
        stock_return = stock_returns["annualized_return"]
        market_return = market_returns["annualized_return"]

        expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
        alpha = stock_return - expected_return

        return float(alpha)

    def calculate_all_metrics(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        market_ticker: str = "VNINDEX",
        risk_free_rate: float = 0.03,
    ) -> Dict:
        """Calculate all performance metrics.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
            market_ticker: Market index ticker
            risk_free_rate: Annual risk-free rate

        Returns:
            Dictionary of all metrics
        """
        logger.info(f"Calculating metrics for {ticker}")

        returns = self.calculate_returns(ticker, start_date, end_date)
        volatility = self.calculate_volatility(ticker, start_date, end_date)
        sharpe = self.calculate_sharpe_ratio(ticker, start_date, end_date, risk_free_rate)
        max_dd = self.calculate_max_drawdown(ticker, start_date, end_date)
        beta = self.calculate_beta(ticker, market_ticker, start_date, end_date)
        alpha = self.calculate_alpha(ticker, market_ticker, start_date, end_date, risk_free_rate)

        return {
            "ticker": ticker,
            "period": {
                "start": start_date,
                "end": end_date,
                "days": (end_date - start_date).days,
            },
            "returns": {
                "total": returns["total_return"] if returns else None,
                "annualized": returns["annualized_return"] if returns else None,
            },
            "risk": {
                "volatility": volatility,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd["max_drawdown_pct"] if max_dd else None,
                "beta": beta,
            },
            "alpha": alpha,
        }

    def compare_stocks(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Compare performance of multiple stocks.

        Args:
            tickers: List of stock tickers
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with comparative metrics
        """
        results = []

        for ticker in tickers:
            metrics = self.calculate_all_metrics(ticker, start_date, end_date)

            results.append({
                "ticker": ticker,
                "total_return": metrics["returns"]["total"],
                "annualized_return": metrics["returns"]["annualized"],
                "volatility": metrics["risk"]["volatility"],
                "sharpe_ratio": metrics["risk"]["sharpe_ratio"],
                "max_drawdown": metrics["risk"]["max_drawdown"],
                "beta": metrics["risk"]["beta"],
                "alpha": metrics["alpha"],
            })

        df = pd.DataFrame(results)

        # Sort by Sharpe ratio
        df = df.sort_values("sharpe_ratio", ascending=False)

        return df

    def calculate_rolling_metrics(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        window_days: int = 252,
    ) -> pd.DataFrame:
        """Calculate rolling performance metrics.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
            window_days: Rolling window size

        Returns:
            DataFrame with rolling metrics
        """
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

        if len(prices) < window_days:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "date": p.date,
                "close": float(p.close),
            }
            for p in prices
        ])

        df = df.set_index("date")

        # Calculate rolling returns
        df["rolling_return"] = df["close"].pct_change(window_days)

        # Calculate rolling volatility
        df["rolling_volatility"] = (
            df["close"]
            .pct_change()
            .rolling(window=window_days)
            .std() * np.sqrt(252)
        )

        # Calculate rolling Sharpe (simplified)
        df["rolling_sharpe"] = (
            df["rolling_return"] / df["rolling_volatility"]
        )

        return df.dropna()

    def generate_performance_report(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """Generate comprehensive performance report.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date

        Returns:
            Performance report dictionary
        """
        metrics = self.calculate_all_metrics(ticker, start_date, end_date)

        # Additional calculations
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

        if not prices:
            return metrics

        closes = [float(p.close) for p in prices]

        # Best/worst days
        daily_returns = [
            (closes[i] - closes[i-1]) / closes[i-1]
            for i in range(1, len(closes))
        ]

        best_day = max(daily_returns) if daily_returns else 0
        worst_day = min(daily_returns) if daily_returns else 0

        # Win rate
        positive_days = sum(1 for r in daily_returns if r > 0)
        win_rate = positive_days / len(daily_returns) if daily_returns else 0

        metrics["statistics"] = {
            "trading_days": len(prices),
            "best_day": best_day,
            "worst_day": worst_day,
            "win_rate": win_rate,
            "start_price": closes[0],
            "end_price": closes[-1],
            "high": max(closes),
            "low": min(closes),
        }

        return metrics
