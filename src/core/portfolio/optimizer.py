"""Portfolio optimization using Modern Portfolio Theory."""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioOptimizer:
    """Portfolio optimization using various methods."""

    def __init__(self, db: Session):
        """Initialize portfolio optimizer.

        Args:
            db: Database session
        """
        self.db = db

    def get_returns_data(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Get historical returns data for tickers.

        Args:
            tickers: List of stock tickers
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame of daily returns
        """
        # Fetch price data
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

        if not prices:
            logger.warning("No price data found for optimization")
            return pd.DataFrame()

        # Convert to DataFrame
        price_data = pd.DataFrame([
            {
                "ticker": p.ticker,
                "date": p.date,
                "close": float(p.close),
            }
            for p in prices
        ])

        # Pivot to get prices by ticker
        price_df = price_data.pivot(
            index="date",
            columns="ticker",
            values="close"
        )

        # Calculate daily returns
        returns_df = price_df.pct_change().dropna()

        return returns_df

    def calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        returns: pd.DataFrame,
        risk_free_rate: float = 0.03,
    ) -> Tuple[float, float, float]:
        """Calculate portfolio return, volatility, and Sharpe ratio.

        Args:
            weights: Portfolio weights
            returns: Historical returns DataFrame
            risk_free_rate: Annual risk-free rate

        Returns:
            Tuple of (expected_return, volatility, sharpe_ratio)
        """
        # Annual expected return
        expected_return = np.sum(returns.mean() * weights) * 252

        # Annual volatility
        cov_matrix = returns.cov() * 252
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        volatility = np.sqrt(portfolio_variance)

        # Sharpe ratio
        sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0

        return expected_return, volatility, sharpe_ratio

    def optimize_max_sharpe(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        risk_free_rate: float = 0.03,
    ) -> Optional[Dict]:
        """Optimize portfolio for maximum Sharpe ratio.

        Args:
            tickers: List of stock tickers
            start_date: Start date for historical data
            end_date: End date for historical data
            risk_free_rate: Annual risk-free rate

        Returns:
            Dictionary with optimal weights and metrics
        """
        logger.info(f"Optimizing portfolio for max Sharpe ratio: {tickers}")

        returns = self.get_returns_data(tickers, start_date, end_date)

        if returns.empty:
            logger.error("No returns data available")
            return None

        num_assets = len(tickers)

        # Try multiple random starting points
        best_sharpe = -np.inf
        best_weights = None
        best_metrics = None

        for _ in range(100):
            # Generate random initial weights
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)

            try:
                # Use scipy optimize if available
                from scipy.optimize import minimize

                # Objective: minimize negative Sharpe ratio
                def objective(w):
                    ret, vol, sharpe = self.calculate_portfolio_metrics(
                        w, returns, risk_free_rate
                    )
                    return -sharpe

                # Constraints: weights sum to 1
                constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

                # Bounds: each weight between 0 and 1
                bounds = tuple((0, 1) for _ in range(num_assets))

                result = minimize(
                    objective,
                    weights,
                    method="SLSQP",
                    bounds=bounds,
                    constraints=constraints,
                )

                if result.success:
                    optimized_weights = result.x
                    ret, vol, sharpe = self.calculate_portfolio_metrics(
                        optimized_weights, returns, risk_free_rate
                    )

                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_weights = optimized_weights
                        best_metrics = (ret, vol, sharpe)

            except ImportError:
                # Fallback: use simple equal weighting
                logger.warning("scipy not available, using equal weighting")
                equal_weights = np.ones(num_assets) / num_assets
                ret, vol, sharpe = self.calculate_portfolio_metrics(
                    equal_weights, returns, risk_free_rate
                )
                best_weights = equal_weights
                best_metrics = (ret, vol, sharpe)
                break

        if best_weights is None:
            logger.error("Optimization failed")
            return None

        # Create result dictionary
        weights_dict = {
            ticker: float(weight)
            for ticker, weight in zip(tickers, best_weights)
        }

        return {
            "weights": weights_dict,
            "expected_return": best_metrics[0],
            "volatility": best_metrics[1],
            "sharpe_ratio": best_metrics[2],
            "optimization_method": "max_sharpe",
        }

    def optimize_min_volatility(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
    ) -> Optional[Dict]:
        """Optimize portfolio for minimum volatility.

        Args:
            tickers: List of stock tickers
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            Dictionary with optimal weights and metrics
        """
        logger.info(f"Optimizing portfolio for min volatility: {tickers}")

        returns = self.get_returns_data(tickers, start_date, end_date)

        if returns.empty:
            logger.error("No returns data available")
            return None

        num_assets = len(tickers)

        try:
            from scipy.optimize import minimize

            # Initial weights
            weights = np.ones(num_assets) / num_assets

            # Objective: minimize volatility
            def objective(w):
                _, vol, _ = self.calculate_portfolio_metrics(w, returns)
                return vol

            # Constraints
            constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
            bounds = tuple((0, 1) for _ in range(num_assets))

            result = minimize(
                objective,
                weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            if not result.success:
                logger.error("Optimization failed")
                return None

            optimized_weights = result.x
            ret, vol, sharpe = self.calculate_portfolio_metrics(optimized_weights, returns)

        except ImportError:
            logger.warning("scipy not available, using equal weighting")
            optimized_weights = np.ones(num_assets) / num_assets
            ret, vol, sharpe = self.calculate_portfolio_metrics(optimized_weights, returns)

        weights_dict = {
            ticker: float(weight)
            for ticker, weight in zip(tickers, optimized_weights)
        }

        return {
            "weights": weights_dict,
            "expected_return": ret,
            "volatility": vol,
            "sharpe_ratio": sharpe,
            "optimization_method": "min_volatility",
        }

    def optimize_target_return(
        self,
        tickers: List[str],
        target_return: float,
        start_date: date,
        end_date: date,
    ) -> Optional[Dict]:
        """Optimize portfolio to achieve target return with minimum risk.

        Args:
            tickers: List of stock tickers
            target_return: Target annual return
            start_date: Start date for historical data
            end_date: End date for historical data

        Returns:
            Dictionary with optimal weights and metrics
        """
        logger.info(
            f"Optimizing portfolio for target return {target_return:.2%}: {tickers}"
        )

        returns = self.get_returns_data(tickers, start_date, end_date)

        if returns.empty:
            logger.error("No returns data available")
            return None

        num_assets = len(tickers)

        try:
            from scipy.optimize import minimize

            weights = np.ones(num_assets) / num_assets

            # Objective: minimize volatility
            def objective(w):
                _, vol, _ = self.calculate_portfolio_metrics(w, returns)
                return vol

            # Constraints: weights sum to 1 and return = target
            def return_constraint(w):
                ret, _, _ = self.calculate_portfolio_metrics(w, returns)
                return ret - target_return

            constraints = [
                {"type": "eq", "fun": lambda w: np.sum(w) - 1},
                {"type": "eq", "fun": return_constraint},
            ]

            bounds = tuple((0, 1) for _ in range(num_assets))

            result = minimize(
                objective,
                weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
            )

            if not result.success:
                logger.warning(
                    f"Could not achieve target return {target_return:.2%}, "
                    "using min volatility instead"
                )
                return self.optimize_min_volatility(tickers, start_date, end_date)

            optimized_weights = result.x
            ret, vol, sharpe = self.calculate_portfolio_metrics(optimized_weights, returns)

        except ImportError:
            logger.error("scipy required for target return optimization")
            return None

        weights_dict = {
            ticker: float(weight)
            for ticker, weight in zip(tickers, optimized_weights)
        }

        return {
            "weights": weights_dict,
            "expected_return": ret,
            "volatility": vol,
            "sharpe_ratio": sharpe,
            "target_return": target_return,
            "optimization_method": "target_return",
        }

    def efficient_frontier(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        num_points: int = 50,
    ) -> List[Dict]:
        """Calculate the efficient frontier.

        Args:
            tickers: List of stock tickers
            start_date: Start date for historical data
            end_date: End date for historical data
            num_points: Number of points on the frontier

        Returns:
            List of portfolio points on efficient frontier
        """
        logger.info(f"Calculating efficient frontier with {num_points} points")

        returns = self.get_returns_data(tickers, start_date, end_date)

        if returns.empty:
            logger.error("No returns data available")
            return []

        # Calculate range of possible returns
        num_assets = len(tickers)
        mean_returns = returns.mean() * 252

        min_return = float(mean_returns.min())
        max_return = float(mean_returns.max())

        # Generate target returns
        target_returns = np.linspace(min_return, max_return, num_points)

        frontier = []

        for target_ret in target_returns:
            result = self.optimize_target_return(
                tickers,
                target_ret,
                start_date,
                end_date
            )

            if result:
                frontier.append(result)

        return frontier

    def equal_weight_portfolio(self, tickers: List[str]) -> Dict[str, float]:
        """Create equal weight portfolio.

        Args:
            tickers: List of stock tickers

        Returns:
            Dictionary of ticker -> weight
        """
        weight = 1.0 / len(tickers)
        return {ticker: weight for ticker in tickers}

    def market_cap_weighted_portfolio(
        self,
        tickers: List[str],
    ) -> Dict[str, float]:
        """Create market cap weighted portfolio.

        Args:
            tickers: List of stock tickers

        Returns:
            Dictionary of ticker -> weight
        """
        from src.database.models import StockInfo

        # Get market caps
        stocks = (
            self.db.query(StockInfo)
            .filter(StockInfo.ticker.in_(tickers))
            .all()
        )

        market_caps = {
            stock.ticker: float(stock.market_cap) if stock.market_cap else 0
            for stock in stocks
        }

        # Calculate weights
        total_cap = sum(market_caps.values())

        if total_cap == 0:
            logger.warning("No market cap data, using equal weighting")
            return self.equal_weight_portfolio(tickers)

        weights = {
            ticker: cap / total_cap
            for ticker, cap in market_caps.items()
        }

        return weights
