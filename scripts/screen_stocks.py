"""Stock screening script with multiple strategies and custom filters."""
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import click
import pandas as pd
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.screening.advanced_strategies import AdvancedScreener
from src.database.connection import get_sync_session
from src.database.models import DailyPrice, Factor, FinancialRatio, StockInfo
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def display_results(stocks: List[dict], title: str) -> None:
    """Display screening results in a formatted table.

    Args:
        stocks: List of stock dictionaries
        title: Title for the results
    """
    if not stocks:
        print(f"\n{title}")
        print("No stocks found matching the criteria.\n")
        return

    print(f"\n{title}")
    print(f"Found {len(stocks)} stocks:\n")

    # Prepare data for tabulate
    headers = ["Ticker", "Name", "Exchange"]
    rows = []

    # Get all unique keys from stocks (excluding standard fields)
    standard_fields = {"ticker", "name", "exchange", "strategy"}
    all_metrics = set()
    for stock in stocks:
        all_metrics.update(stock.keys() - standard_fields)

    # Sort metrics for consistent display
    metric_columns = sorted(all_metrics)
    headers.extend([m.replace("_", " ").title() for m in metric_columns])

    # Build rows
    for stock in stocks:
        row = [
            stock.get("ticker", ""),
            stock.get("name", "")[:30],  # Truncate long names
            stock.get("exchange", ""),
        ]

        for metric in metric_columns:
            value = stock.get(metric)
            if value is not None:
                if isinstance(value, float):
                    if abs(value) >= 1000:
                        row.append(f"{value:,.0f}")
                    elif abs(value) >= 100:
                        row.append(f"{value:.1f}")
                    else:
                        row.append(f"{value:.2f}")
                else:
                    row.append(value)
            else:
                row.append("-")

        rows.append(row)

    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def export_to_csv(stocks: List[dict], filename: str) -> None:
    """Export screening results to CSV file.

    Args:
        stocks: List of stock dictionaries
        filename: Output filename
    """
    if not stocks:
        logger.warning("No stocks to export")
        return

    df = pd.DataFrame(stocks)
    df.to_csv(filename, index=False)
    logger.info(f"Exported {len(stocks)} stocks to {filename}")
    print(f"\nResults exported to: {filename}")


@click.group()
def cli():
    """Vietnam Quant Platform - Stock Screening Tool.

    Screen stocks based on various strategies and custom criteria.
    """
    pass


@cli.command()
@click.option(
    "--strategy",
    type=click.Choice(["value", "growth", "momentum", "quality", "dividend", "all"]),
    default="all",
    help="Screening strategy to apply",
)
@click.option(
    "--exchange",
    type=click.Choice(["HOSE", "HNX", "UPCOM"]),
    default=None,
    help="Filter by exchange",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of results per strategy",
)
@click.option(
    "--export",
    type=str,
    default=None,
    help="Export results to CSV file",
)
def strategy(
    strategy: str,
    exchange: Optional[str],
    limit: int,
    export: Optional[str],
) -> None:
    """Screen stocks using predefined strategies.

    Strategies available:
    - value: Undervalued stocks with strong fundamentals
    - growth: High-growth stocks with strong revenue/earnings growth
    - momentum: Stocks with strong price momentum
    - quality: High-quality stocks with strong balance sheets
    - dividend: High dividend-yielding stocks
    - all: Run all strategies

    Examples:
        python scripts/screen_stocks.py strategy --strategy=value
        python scripts/screen_stocks.py strategy --strategy=growth --exchange=HOSE
        python scripts/screen_stocks.py strategy --strategy=all --limit=10
    """
    db = next(get_sync_session())
    screener = AdvancedScreener(db)

    try:
        if strategy == "all":
            results = screener.screen_all_strategies(
                exchange=exchange,
                limit_per_strategy=limit,
            )

            for strat_name, stocks in results.items():
                display_results(stocks, f"=== {strat_name.upper()} STRATEGY ===")

            if export:
                # Flatten results for export
                all_stocks = []
                for strat_name, stocks in results.items():
                    for stock in stocks:
                        stock["strategy"] = strat_name
                        all_stocks.append(stock)
                export_to_csv(all_stocks, export)

        else:
            # Run single strategy
            if strategy == "value":
                stocks = screener.screen_value_stocks(exchange=exchange, limit=limit)
            elif strategy == "growth":
                stocks = screener.screen_growth_stocks(exchange=exchange, limit=limit)
            elif strategy == "momentum":
                stocks = screener.screen_momentum_stocks(exchange=exchange, limit=limit)
            elif strategy == "quality":
                stocks = screener.screen_quality_stocks(exchange=exchange, limit=limit)
            elif strategy == "dividend":
                stocks = screener.screen_dividend_stocks(exchange=exchange, limit=limit)

            display_results(stocks, f"=== {strategy.upper()} STRATEGY ===")

            if export:
                export_to_csv(stocks, export)

    except Exception as e:
        logger.error(f"Error during screening: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cli.command()
@click.option(
    "--min-pe",
    type=float,
    default=None,
    help="Minimum P/E ratio",
)
@click.option(
    "--max-pe",
    type=float,
    default=None,
    help="Maximum P/E ratio",
)
@click.option(
    "--min-pb",
    type=float,
    default=None,
    help="Minimum P/B ratio",
)
@click.option(
    "--max-pb",
    type=float,
    default=None,
    help="Maximum P/B ratio",
)
@click.option(
    "--min-roe",
    type=float,
    default=None,
    help="Minimum ROE (%)",
)
@click.option(
    "--min-roa",
    type=float,
    default=None,
    help="Minimum ROA (%)",
)
@click.option(
    "--max-debt-to-equity",
    type=float,
    default=None,
    help="Maximum debt-to-equity ratio",
)
@click.option(
    "--min-current-ratio",
    type=float,
    default=None,
    help="Minimum current ratio",
)
@click.option(
    "--min-revenue-growth",
    type=float,
    default=None,
    help="Minimum revenue growth YoY (%)",
)
@click.option(
    "--min-eps-growth",
    type=float,
    default=None,
    help="Minimum EPS growth YoY (%)",
)
@click.option(
    "--min-dividend-yield",
    type=float,
    default=None,
    help="Minimum dividend yield (%)",
)
@click.option(
    "--exchange",
    type=click.Choice(["HOSE", "HNX", "UPCOM"]),
    default=None,
    help="Filter by exchange",
)
@click.option(
    "--min-market-cap",
    type=float,
    default=None,
    help="Minimum market cap (billion VND)",
)
@click.option(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of results",
)
@click.option(
    "--sort-by",
    type=click.Choice([
        "pe_ratio",
        "pb_ratio",
        "roe",
        "roa",
        "revenue_growth_yoy",
        "eps_growth_yoy",
        "dividend_yield",
        "market_cap",
    ]),
    default=None,
    help="Sort results by metric",
)
@click.option(
    "--ascending/--descending",
    default=False,
    help="Sort order",
)
@click.option(
    "--export",
    type=str,
    default=None,
    help="Export results to CSV file",
)
def custom(
    min_pe: Optional[float],
    max_pe: Optional[float],
    min_pb: Optional[float],
    max_pb: Optional[float],
    min_roe: Optional[float],
    min_roa: Optional[float],
    max_debt_to_equity: Optional[float],
    min_current_ratio: Optional[float],
    min_revenue_growth: Optional[float],
    min_eps_growth: Optional[float],
    min_dividend_yield: Optional[float],
    exchange: Optional[str],
    min_market_cap: Optional[float],
    limit: int,
    sort_by: Optional[str],
    ascending: bool,
    export: Optional[str],
) -> None:
    """Screen stocks with custom criteria.

    Examples:
        # Find undervalued stocks
        python scripts/screen_stocks.py custom --max-pe=10 --min-roe=15

        # Find growth stocks with good financials
        python scripts/screen_stocks.py custom --min-revenue-growth=20 --min-eps-growth=20 --max-debt-to-equity=0.5

        # Find high dividend stocks
        python scripts/screen_stocks.py custom --min-dividend-yield=5 --min-current-ratio=2

        # Complex screening
        python scripts/screen_stocks.py custom --max-pe=15 --min-pb=0.5 --max-pb=2 --min-roe=15 --max-debt-to-equity=1 --exchange=HOSE --sort-by=roe
    """
    db = next(get_sync_session())

    try:
        # Get latest financial ratio date
        latest_date = (
            db.query(FinancialRatio.date)
            .order_by(FinancialRatio.date.desc())
            .first()
        )

        if not latest_date:
            click.echo("No financial data available. Please run backfill first.")
            sys.exit(1)

        latest_date = latest_date[0]

        # Build query
        query = (
            db.query(StockInfo, FinancialRatio)
            .join(FinancialRatio, StockInfo.ticker == FinancialRatio.ticker)
            .filter(
                StockInfo.is_active == True,  # noqa: E712
                FinancialRatio.date == latest_date,
            )
        )

        # Apply filters
        if exchange:
            query = query.filter(StockInfo.exchange == exchange)

        if min_market_cap:
            min_market_cap_value = min_market_cap * 1_000_000_000  # Convert to VND
            query = query.filter(StockInfo.market_cap >= min_market_cap_value)

        if min_pe is not None:
            query = query.filter(FinancialRatio.pe_ratio >= min_pe)

        if max_pe is not None:
            query = query.filter(
                FinancialRatio.pe_ratio <= max_pe,
                FinancialRatio.pe_ratio > 0,
            )

        if min_pb is not None:
            query = query.filter(FinancialRatio.pb_ratio >= min_pb)

        if max_pb is not None:
            query = query.filter(
                FinancialRatio.pb_ratio <= max_pb,
                FinancialRatio.pb_ratio > 0,
            )

        if min_roe is not None:
            query = query.filter(FinancialRatio.roe >= min_roe)

        if min_roa is not None:
            query = query.filter(FinancialRatio.roa >= min_roa)

        if max_debt_to_equity is not None:
            query = query.filter(
                FinancialRatio.debt_to_equity <= max_debt_to_equity,
            )

        if min_current_ratio is not None:
            query = query.filter(FinancialRatio.current_ratio >= min_current_ratio)

        if min_revenue_growth is not None:
            query = query.filter(FinancialRatio.revenue_growth_yoy >= min_revenue_growth)

        if min_eps_growth is not None:
            query = query.filter(FinancialRatio.eps_growth_yoy >= min_eps_growth)

        if min_dividend_yield is not None:
            query = query.filter(FinancialRatio.dividend_yield >= min_dividend_yield)

        # Apply sorting
        if sort_by:
            order_column = getattr(FinancialRatio, sort_by, None)
            if order_column is None and sort_by == "market_cap":
                order_column = StockInfo.market_cap

            if order_column is not None:
                if ascending:
                    query = query.order_by(order_column.asc())
                else:
                    query = query.order_by(order_column.desc())

        # Execute query
        results = query.limit(limit).all()

        # Format results
        stocks = []
        for stock_info, ratio in results:
            stocks.append({
                "ticker": stock_info.ticker,
                "name": stock_info.name,
                "exchange": stock_info.exchange,
                "market_cap": float(stock_info.market_cap / 1_000_000_000)
                if stock_info.market_cap
                else None,
                "pe_ratio": float(ratio.pe_ratio) if ratio.pe_ratio else None,
                "pb_ratio": float(ratio.pb_ratio) if ratio.pb_ratio else None,
                "roe": float(ratio.roe) if ratio.roe else None,
                "roa": float(ratio.roa) if ratio.roa else None,
                "debt_to_equity": float(ratio.debt_to_equity)
                if ratio.debt_to_equity
                else None,
                "current_ratio": float(ratio.current_ratio)
                if ratio.current_ratio
                else None,
                "revenue_growth_yoy": float(ratio.revenue_growth_yoy)
                if ratio.revenue_growth_yoy
                else None,
                "eps_growth_yoy": float(ratio.eps_growth_yoy)
                if ratio.eps_growth_yoy
                else None,
                "dividend_yield": float(ratio.dividend_yield)
                if ratio.dividend_yield
                else None,
            })

        display_results(stocks, "=== CUSTOM SCREENING RESULTS ===")

        if export:
            export_to_csv(stocks, export)

    except Exception as e:
        logger.error(f"Error during custom screening: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cli.command()
@click.option(
    "--ticker",
    required=True,
    type=str,
    help="Stock ticker to analyze",
)
def analyze(ticker: str) -> None:
    """Analyze a specific stock with detailed metrics.

    Example:
        python scripts/screen_stocks.py analyze --ticker=VNM
    """
    db = next(get_sync_session())

    try:
        ticker = ticker.upper()

        # Get stock info
        stock = db.query(StockInfo).filter(StockInfo.ticker == ticker).first()

        if not stock:
            click.echo(f"Stock {ticker} not found.")
            sys.exit(1)

        # Get latest financial ratios
        ratio = (
            db.query(FinancialRatio)
            .filter(FinancialRatio.ticker == ticker)
            .order_by(FinancialRatio.date.desc())
            .first()
        )

        # Get latest price
        price = (
            db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker)
            .order_by(DailyPrice.date.desc())
            .first()
        )

        # Display information
        print(f"\n{'='*60}")
        print(f"Stock Analysis: {ticker}")
        print(f"{'='*60}\n")

        print("BASIC INFORMATION")
        print(f"  Name: {stock.name}")
        print(f"  Exchange: {stock.exchange}")
        print(f"  Industry: {stock.industry or 'N/A'}")
        print(f"  Sector: {stock.sector or 'N/A'}")
        if stock.market_cap:
            print(f"  Market Cap: {float(stock.market_cap / 1_000_000_000):.2f} B VND")

        if price:
            print(f"\nLATEST PRICE ({price.date})")
            print(f"  Close: {float(price.close):,.0f} VND")
            print(f"  Open: {float(price.open):,.0f} VND")
            print(f"  High: {float(price.high):,.0f} VND")
            print(f"  Low: {float(price.low):,.0f} VND")
            print(f"  Volume: {price.volume:,}")

        if ratio:
            print(f"\nFINANCIAL RATIOS (as of {ratio.date})")
            print("\n  Valuation:")
            if ratio.pe_ratio:
                print(f"    P/E Ratio: {ratio.pe_ratio:.2f}")
            if ratio.pb_ratio:
                print(f"    P/B Ratio: {ratio.pb_ratio:.2f}")
            if ratio.dividend_yield:
                print(f"    Dividend Yield: {ratio.dividend_yield:.2f}%")

            print("\n  Profitability:")
            if ratio.roe:
                print(f"    ROE: {ratio.roe:.2f}%")
            if ratio.roa:
                print(f"    ROA: {ratio.roa:.2f}%")
            if ratio.net_margin:
                print(f"    Net Margin: {ratio.net_margin:.2f}%")

            print("\n  Financial Health:")
            if ratio.debt_to_equity is not None:
                print(f"    Debt/Equity: {ratio.debt_to_equity:.2f}")
            if ratio.current_ratio:
                print(f"    Current Ratio: {ratio.current_ratio:.2f}")

            print("\n  Growth:")
            if ratio.revenue_growth_yoy:
                print(f"    Revenue Growth YoY: {ratio.revenue_growth_yoy:.2f}%")
            if ratio.eps_growth_yoy:
                print(f"    EPS Growth YoY: {ratio.eps_growth_yoy:.2f}%")

        print(f"\n{'='*60}\n")

    except Exception as e:
        logger.error(f"Error analyzing stock: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cli.command()
@click.option(
    "--exchange",
    type=click.Choice(["HOSE", "HNX", "UPCOM"]),
    default=None,
    help="Filter by exchange",
)
def stats(exchange: Optional[str]) -> None:
    """Display database statistics and data coverage.

    Example:
        python scripts/screen_stocks.py stats
        python scripts/screen_stocks.py stats --exchange=HOSE
    """
    db = next(get_sync_session())

    try:
        # Count stocks
        stock_query = db.query(StockInfo).filter(StockInfo.is_active == True)  # noqa: E712
        if exchange:
            stock_query = stock_query.filter(StockInfo.exchange == exchange)

        total_stocks = stock_query.count()

        # Count stocks with price data
        stocks_with_prices = (
            db.query(DailyPrice.ticker)
            .distinct()
            .join(StockInfo, DailyPrice.ticker == StockInfo.ticker)
            .filter(StockInfo.is_active == True)  # noqa: E712
        )
        if exchange:
            stocks_with_prices = stocks_with_prices.filter(StockInfo.exchange == exchange)
        stocks_with_prices_count = stocks_with_prices.count()

        # Count stocks with financial data
        stocks_with_ratios = (
            db.query(FinancialRatio.ticker)
            .distinct()
            .join(StockInfo, FinancialRatio.ticker == StockInfo.ticker)
            .filter(StockInfo.is_active == True)  # noqa: E712
        )
        if exchange:
            stocks_with_ratios = stocks_with_ratios.filter(StockInfo.exchange == exchange)
        stocks_with_ratios_count = stocks_with_ratios.count()

        # Get date ranges
        latest_price = db.query(DailyPrice.date).order_by(DailyPrice.date.desc()).first()
        earliest_price = db.query(DailyPrice.date).order_by(DailyPrice.date.asc()).first()

        latest_ratio = (
            db.query(FinancialRatio.date).order_by(FinancialRatio.date.desc()).first()
        )

        print(f"\n{'='*60}")
        print(f"Database Statistics{' - ' + exchange if exchange else ''}")
        print(f"{'='*60}\n")

        print(f"Active Stocks: {total_stocks}")
        print(f"Stocks with Price Data: {stocks_with_prices_count}")
        print(f"Stocks with Financial Data: {stocks_with_ratios_count}")

        if earliest_price and latest_price:
            print(f"\nPrice Data Range:")
            print(f"  From: {earliest_price[0]}")
            print(f"  To: {latest_price[0]}")

        if latest_ratio:
            print(f"\nLatest Financial Data: {latest_ratio[0]}")

        # Exchange breakdown
        if not exchange:
            print("\nStocks by Exchange:")
            for exch in ["HOSE", "HNX", "UPCOM"]:
                count = (
                    db.query(StockInfo)
                    .filter(
                        StockInfo.is_active == True,  # noqa: E712
                        StockInfo.exchange == exch,
                    )
                    .count()
                )
                print(f"  {exch}: {count}")

        print(f"\n{'='*60}\n")

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    cli()
