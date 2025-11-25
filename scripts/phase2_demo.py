"""Phase 2 features demonstration script."""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.backtesting.engine import BacktestEngine
from src.core.backtesting.strategies import (
    buy_and_hold_strategy,
    momentum_strategy,
    simple_moving_average_strategy,
)
from src.core.corporate_actions.adjuster import CorporateActionAdjuster
from src.core.corporate_actions.detector import CorporateActionDetector
from src.core.data_ingestion.data_client_factory import get_data_client
from src.core.market_index.tracker import MarketIndexTracker
from src.core.portfolio.optimizer import PortfolioOptimizer
from src.database.connection import get_sync_session
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def demo_corporate_actions():
    """Demonstrate corporate action detection and adjustment."""
    logger.info("=== Corporate Action Detection & Adjustment Demo ===")

    db = next(get_sync_session())

    # Initialize detector and adjuster
    detector = CorporateActionDetector(db)
    adjuster = CorporateActionAdjuster(db)

    # Example: Detect splits for a ticker
    ticker = "VCB"  # Example ticker
    logger.info(f"Detecting corporate actions for {ticker}")

    splits = detector.detect_stock_splits(ticker)
    logger.info(f"Found {len(splits)} potential stock splits")

    if splits:
        # Save detected actions
        saved = detector.save_detected_actions(splits)
        logger.info(f"Saved {saved} corporate actions")

        # Get unverified actions
        unverified = adjuster.get_unverified_actions(ticker)
        logger.info(f"Unverified actions: {len(unverified)}")

        # Note: In production, you would manually verify these before applying
        # For demo purposes, we'll just show what actions were detected

    db.close()
    logger.info("Corporate actions demo complete\n")


async def demo_market_index_tracking():
    """Demonstrate market index tracking."""
    logger.info("=== Market Index Tracking Demo ===")

    db = next(get_sync_session())
    tracker = MarketIndexTracker(db)

    # Get summary for all indices
    logger.info("Getting market index summaries...")
    summaries = tracker.get_all_indices_summary()

    for summary in summaries:
        logger.info(f"\n{summary['index_name']}:")
        logger.info(f"  Latest Close: {summary.get('latest_close', 'N/A')}")
        logger.info(f"  Year Return: {summary.get('year_return', 'N/A')}")
        logger.info(f"  Year Volatility: {summary.get('year_volatility', 'N/A')}")

    # Example: Compare stock to index
    ticker = "VCB"
    index_name = "VN-INDEX"
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    logger.info(f"\nComparing {ticker} to {index_name}...")
    comparison = tracker.compare_stock_to_index(
        ticker, index_name, start_date, end_date
    )

    if comparison:
        logger.info(f"Stock Return: {comparison['stock_return']:.2%}")
        logger.info(f"Index Return: {comparison['index_return']:.2%}")
        logger.info(f"Alpha: {comparison['alpha']:.2%}")
        logger.info(f"Outperformed: {comparison['outperformed']}")

    db.close()
    logger.info("\nMarket index tracking demo complete\n")


def demo_backtesting():
    """Demonstrate backtesting framework."""
    logger.info("=== Backtesting Framework Demo ===")

    db = next(get_sync_session())
    engine = BacktestEngine(db, initial_capital=100_000_000)  # 100M VND

    # Define test parameters
    tickers = ["VCB", "VHM", "VIC"]  # Top Vietnamese stocks
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    logger.info(f"Running backtest for {tickers}")
    logger.info(f"Period: {start_date} to {end_date}")

    # Test with simple moving average strategy
    logger.info("\nTesting Moving Average Strategy...")

    def ma_strategy_wrapper(data, portfolio, prices):
        return simple_moving_average_strategy(
            data, portfolio, prices, short_window=20, long_window=50
        )

    results = engine.run(
        strategy=ma_strategy_wrapper,
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
    )

    if results:
        logger.info(f"\nBacktest Results:")
        logger.info(f"Initial Capital: {results['initial_capital']:,.0f} VND")
        logger.info(f"Final Value: {results['final_value']:,.0f} VND")
        logger.info(f"Total Return: {results['total_return']:.2%}")

        stats = results['statistics']
        logger.info(f"\nTrade Statistics:")
        logger.info(f"  Total Trades: {stats['total_trades']}")
        logger.info(f"  Win Rate: {stats['win_rate']:.2%}")
        logger.info(f"  Average P&L: {stats['avg_pnl']:,.0f} VND")
        logger.info(f"  Profit Factor: {stats['profit_factor']:.2f}")

    db.close()
    logger.info("\nBacktesting demo complete\n")


def demo_portfolio_optimization():
    """Demonstrate portfolio optimization."""
    logger.info("=== Portfolio Optimization Demo ===")

    db = next(get_sync_session())
    optimizer = PortfolioOptimizer(db)

    # Define portfolio
    tickers = ["VCB", "VHM", "VIC", "GAS", "MSN"]
    end_date = date.today()
    start_date = end_date - timedelta(days=365 * 2)  # 2 years of data

    logger.info(f"Optimizing portfolio for {tickers}")
    logger.info(f"Historical data period: {start_date} to {end_date}")

    # Equal weight baseline
    logger.info("\n1. Equal Weight Portfolio:")
    equal_weights = optimizer.equal_weight_portfolio(tickers)
    for ticker, weight in equal_weights.items():
        logger.info(f"  {ticker}: {weight:.2%}")

    # Max Sharpe ratio
    logger.info("\n2. Maximum Sharpe Ratio Portfolio:")
    max_sharpe = optimizer.optimize_max_sharpe(tickers, start_date, end_date)

    if max_sharpe:
        logger.info(f"Expected Return: {max_sharpe['expected_return']:.2%}")
        logger.info(f"Volatility: {max_sharpe['volatility']:.2%}")
        logger.info(f"Sharpe Ratio: {max_sharpe['sharpe_ratio']:.2f}")
        logger.info("Weights:")
        for ticker, weight in max_sharpe['weights'].items():
            logger.info(f"  {ticker}: {weight:.2%}")

    # Minimum volatility
    logger.info("\n3. Minimum Volatility Portfolio:")
    min_vol = optimizer.optimize_min_volatility(tickers, start_date, end_date)

    if min_vol:
        logger.info(f"Expected Return: {min_vol['expected_return']:.2%}")
        logger.info(f"Volatility: {min_vol['volatility']:.2%}")
        logger.info(f"Sharpe Ratio: {min_vol['sharpe_ratio']:.2f}")
        logger.info("Weights:")
        for ticker, weight in min_vol['weights'].items():
            logger.info(f"  {ticker}: {weight:.2%}")

    db.close()
    logger.info("\nPortfolio optimization demo complete\n")


def main():
    """Run all Phase 2 demos."""
    logger.info("Starting Phase 2 Features Demonstration\n")

    try:
        # Demo 1: Corporate Actions
        demo_corporate_actions()

        # Demo 2: Market Index Tracking
        asyncio.run(demo_market_index_tracking())

        # Demo 3: Backtesting
        demo_backtesting()

        # Demo 4: Portfolio Optimization
        demo_portfolio_optimization()

        logger.info("All Phase 2 demos completed successfully!")

    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
