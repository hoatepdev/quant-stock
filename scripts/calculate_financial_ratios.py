"""Calculate and store financial ratios for all stocks."""
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import click
import pandas as pd
from tqdm import tqdm
from vnstock import Vnstock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_sync_session
from src.database.models import DailyPrice, FinancialRatio, StockInfo
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def parse_ratio_value(value) -> Optional[float]:
    """Parse ratio value to float, handling NaN and None.

    Args:
        value: Value to parse

    Returns:
        Float value or None
    """
    if pd.isna(value) or value is None:
        return None
    try:
        result = float(value)
        # Check for infinity or NaN
        if pd.isna(result) or result == float("inf") or result == float("-inf"):
            return None
        return result
    except (ValueError, TypeError):
        return None


def get_financial_ratios(ticker: str, period: str = "quarter") -> Optional[pd.DataFrame]:
    """Fetch financial ratios from VNStock API with retry logic.

    Args:
        ticker: Stock ticker
        period: 'quarter' or 'year'

    Returns:
        DataFrame with financial ratios or None
    """
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            stock = Vnstock().stock(ticker, source="VCI")
            ratios = stock.finance.ratio(period=period, lang="en")

            if ratios is None or ratios.empty:
                logger.warning(f"No ratio data for {ticker}")
                return None

            return ratios

        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "quá nhiều request" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(f"Rate limit hit for {ticker}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded for {ticker} after {max_retries} retries")
                    return None
            else:
                logger.error(f"Error fetching ratios for {ticker}: {e}")
                return None

    return None


def process_ratios(ticker: str, ratios_df: pd.DataFrame) -> list[dict]:
    """Process ratios DataFrame and convert to database records.

    Args:
        ticker: Stock ticker
        ratios_df: DataFrame from VNStock API

    Returns:
        List of financial ratio records
    """
    records = []

    for idx, row in ratios_df.iterrows():
        try:
            # Extract metadata
            year = row.get(("Meta", "yearReport"))
            quarter = row.get(("Meta", "lengthReport"))

            if pd.isna(year) or pd.isna(quarter):
                continue

            # Calculate date (end of quarter)
            year = int(year)
            quarter = int(quarter)
            if quarter == 1:
                ratio_date = date(year, 3, 31)
            elif quarter == 2:
                ratio_date = date(year, 6, 30)
            elif quarter == 3:
                ratio_date = date(year, 9, 30)
            else:  # quarter == 4
                ratio_date = date(year, 12, 31)

            # Extract ratios with Vietnamese column names
            # Note: VNStock API returns percentage values as decimals (0.26 = 26%)
            # We need to multiply by 100 for percentage fields

            # Helper to convert decimal to percentage
            def to_percent(value):
                parsed = parse_ratio_value(value)
                return parsed * 100 if parsed is not None else None

            record = {
                "ticker": ticker,
                "date": ratio_date,
                # Valuation ratios (not percentages)
                "pe_ratio": parse_ratio_value(row.get(("Chỉ tiêu định giá", "P/E"))),
                "pb_ratio": parse_ratio_value(row.get(("Chỉ tiêu định giá", "P/B"))),
                "ps_ratio": parse_ratio_value(row.get(("Chỉ tiêu định giá", "P/S"))),
                "ev_ebitda": parse_ratio_value(
                    row.get(("Chỉ tiêu định giá", "EV/EBITDA"))
                ),
                # Profitability ratios (convert decimals to percentages)
                "dividend_yield": to_percent(
                    row.get(("Chỉ tiêu khả năng sinh lợi", "Dividend yield (%)"))
                ),
                "roe": to_percent(row.get(("Chỉ tiêu khả năng sinh lợi", "ROE (%)"))),
                "roa": to_percent(row.get(("Chỉ tiêu khả năng sinh lợi", "ROA (%)"))),
                "roi": to_percent(row.get(("Chỉ tiêu khả năng sinh lợi", "ROIC (%)"))),
                "gross_margin": to_percent(
                    row.get(("Chỉ tiêu khả năng sinh lợi", "Gross Profit Margin (%)"))
                ),
                "operating_margin": to_percent(
                    row.get(("Chỉ tiêu khả năng sinh lợi", "EBIT Margin (%)"))
                ),
                "net_margin": to_percent(
                    row.get(("Chỉ tiêu khả năng sinh lợi", "Net Profit Margin (%)"))
                ),
                # Leverage ratios
                "debt_to_equity": parse_ratio_value(
                    row.get(("Chỉ tiêu cơ cấu nguồn vốn", "Debt/Equity"))
                ),
                "debt_to_assets": None,  # Not provided by VNStock
                "interest_coverage": parse_ratio_value(
                    row.get(("Chỉ tiêu thanh khoản", "Interest Coverage"))
                ),
                # Liquidity ratios
                "current_ratio": parse_ratio_value(
                    row.get(("Chỉ tiêu thanh khoản", "Current Ratio"))
                ),
                "quick_ratio": parse_ratio_value(
                    row.get(("Chỉ tiêu thanh khoản", "Quick Ratio"))
                ),
                "cash_ratio": parse_ratio_value(
                    row.get(("Chỉ tiêu thanh khoản", "Cash Ratio"))
                ),
                # Efficiency ratios
                "asset_turnover": parse_ratio_value(
                    row.get(("Chỉ tiêu hiệu quả hoạt động", "Asset Turnover"))
                ),
                "inventory_turnover": parse_ratio_value(
                    row.get(("Chỉ tiêu hiệu quả hoạt động", "Inventory Turnover"))
                ),
                "receivables_turnover": None,  # Not directly provided
            }

            # Calculate growth rates if we have previous quarter data
            # This will be done in a separate step after all data is collected

            records.append(record)

        except Exception as e:
            logger.error(f"Error processing ratio record for {ticker}: {e}")
            continue

    return records


def calculate_growth_rates(db, ticker: str) -> None:
    """Calculate YoY and QoQ growth rates for revenue and EPS.

    Args:
        db: Database session
        ticker: Stock ticker
    """
    try:
        # Get stock price and financial data to calculate growth
        # This is simplified - in production you'd fetch from income statements
        stock = Vnstock().stock(ticker, source="VCI")
        income = stock.finance.income_statement(period="quarter", lang="en")

        if income is None or income.empty:
            return

        # Get latest ratios from database
        ratios = (
            db.query(FinancialRatio)
            .filter(FinancialRatio.ticker == ticker)
            .order_by(FinancialRatio.date.desc())
            .limit(8)  # Last 2 years of quarterly data
            .all()
        )

        if len(ratios) < 5:  # Need at least 5 quarters for YoY
            return

        # Extract revenue and profit data
        revenue_col = "Revenue (Bn. VND)"
        profit_col = "Attribute to parent company (Bn. VND)"

        for idx, row in income.iterrows():
            try:
                year = int(row.get("yearReport", 0))
                quarter = int(row.get("lengthReport", 0))

                if year == 0 or quarter == 0:
                    continue

                # Calculate date
                if quarter == 1:
                    ratio_date = date(year, 3, 31)
                elif quarter == 2:
                    ratio_date = date(year, 6, 30)
                elif quarter == 3:
                    ratio_date = date(year, 9, 30)
                else:
                    ratio_date = date(year, 12, 31)

                # Find matching ratio record
                ratio_record = db.query(FinancialRatio).filter(
                    FinancialRatio.ticker == ticker, FinancialRatio.date == ratio_date
                ).first()

                if not ratio_record:
                    continue

                # Get current revenue and profit
                current_revenue = parse_ratio_value(row.get(revenue_col))
                current_profit = parse_ratio_value(row.get(profit_col))

                # Get YoY data (same quarter, previous year)
                prev_year_data = income[
                    (income["yearReport"] == year - 1) & (income["lengthReport"] == quarter)
                ]

                if not prev_year_data.empty:
                    prev_revenue = parse_ratio_value(prev_year_data.iloc[0].get(revenue_col))
                    prev_profit = parse_ratio_value(prev_year_data.iloc[0].get(profit_col))

                    # Calculate YoY growth
                    if (
                        current_revenue
                        and prev_revenue
                        and prev_revenue != 0
                    ):
                        revenue_growth_yoy = (
                            (current_revenue - prev_revenue) / abs(prev_revenue)
                        ) * 100
                        ratio_record.revenue_growth_yoy = revenue_growth_yoy

                    # For EPS growth, we need shares outstanding
                    # Simplified: use profit growth as proxy
                    if current_profit and prev_profit and prev_profit != 0:
                        eps_growth_yoy = (
                            (current_profit - prev_profit) / abs(prev_profit)
                        ) * 100
                        ratio_record.eps_growth_yoy = eps_growth_yoy

                # Get QoQ data
                if quarter == 1:
                    prev_quarter = 4
                    prev_year_qoq = year - 1
                else:
                    prev_quarter = quarter - 1
                    prev_year_qoq = year

                prev_qtr_data = income[
                    (income["yearReport"] == prev_year_qoq)
                    & (income["lengthReport"] == prev_quarter)
                ]

                if not prev_qtr_data.empty:
                    prev_revenue_qoq = parse_ratio_value(
                        prev_qtr_data.iloc[0].get(revenue_col)
                    )
                    prev_profit_qoq = parse_ratio_value(
                        prev_qtr_data.iloc[0].get(profit_col)
                    )

                    if (
                        current_revenue
                        and prev_revenue_qoq
                        and prev_revenue_qoq != 0
                    ):
                        revenue_growth_qoq = (
                            (current_revenue - prev_revenue_qoq) / abs(prev_revenue_qoq)
                        ) * 100
                        ratio_record.revenue_growth_qoq = revenue_growth_qoq

                    if (
                        current_profit
                        and prev_profit_qoq
                        and prev_profit_qoq != 0
                    ):
                        eps_growth_qoq = (
                            (current_profit - prev_profit_qoq) / abs(prev_profit_qoq)
                        ) * 100
                        ratio_record.eps_growth_qoq = eps_growth_qoq

            except Exception as e:
                logger.debug(f"Error calculating growth for {ticker} at {ratio_date}: {e}")
                continue

        db.commit()

    except Exception as e:
        logger.error(f"Error calculating growth rates for {ticker}: {e}")


def update_stock_ratios(ticker: str, period: str = "quarter") -> int:
    """Update financial ratios for a single stock.

    Args:
        ticker: Stock ticker
        period: 'quarter' or 'year'

    Returns:
        Number of records inserted/updated
    """
    try:
        logger.info(f"Fetching financial ratios for {ticker}")

        # Fetch ratios from API
        ratios_df = get_financial_ratios(ticker, period)

        if ratios_df is None or ratios_df.empty:
            return 0

        # Process ratios
        records = process_ratios(ticker, ratios_df)

        if not records:
            logger.warning(f"No valid ratios processed for {ticker}")
            return 0

        # Insert into database
        db = next(get_sync_session())
        inserted_count = 0
        updated_count = 0

        for record in records:
            # Check if record already exists
            existing = (
                db.query(FinancialRatio)
                .filter(
                    FinancialRatio.ticker == record["ticker"],
                    FinancialRatio.date == record["date"],
                )
                .first()
            )

            if existing:
                # Update existing record
                for key, value in record.items():
                    if key not in ["ticker", "date"]:
                        setattr(existing, key, value)
                updated_count += 1
            else:
                # Insert new record
                ratio_obj = FinancialRatio(**record)
                db.add(ratio_obj)
                inserted_count += 1

        db.commit()

        # Calculate growth rates
        calculate_growth_rates(db, ticker)

        logger.info(f"Processed {ticker}: {inserted_count} inserted, {updated_count} updated")

        db.close()

        return inserted_count + updated_count

    except Exception as e:
        logger.error(f"Error updating ratios for {ticker}: {e}")
        return 0


@click.command()
@click.option(
    "--tickers",
    default="all",
    help="Comma-separated tickers or 'all' for all stocks",
)
@click.option(
    "--exchange",
    default=None,
    help="Filter by exchange (HOSE, HNX, UPCOM)",
)
@click.option(
    "--period",
    type=click.Choice(["quarter", "year"]),
    default="quarter",
    help="Report period (quarter or year)",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit number of stocks to process (for testing)",
)
@click.option(
    "--delay",
    type=float,
    default=1.0,
    help="Delay between API requests in seconds (default: 1.0)",
)
def main(
    tickers: str,
    exchange: Optional[str],
    period: str,
    limit: Optional[int],
    delay: float,
) -> None:
    """Calculate and store financial ratios for stocks.

    This script fetches financial ratios from VNStock API and stores them
    in the database for use in screening strategies.

    Examples:
        # Update all stocks (with 2s delay to avoid rate limits)
        python scripts/calculate_financial_ratios.py --delay=2.0

        # Update HOSE stocks only
        python scripts/calculate_financial_ratios.py --exchange=HOSE --delay=2.0

        # Update specific stocks
        python scripts/calculate_financial_ratios.py --tickers=VNM,HPG,VIC

        # Test with limited stocks (faster delay for testing)
        python scripts/calculate_financial_ratios.py --limit=10 --delay=1.0
    """
    # Get tickers
    if tickers.lower() == "all":
        db = next(get_sync_session())
        query = db.query(StockInfo).filter(StockInfo.is_active == True)  # noqa: E712

        if exchange:
            query = query.filter(StockInfo.exchange == exchange.upper())

        stocks = query.all()
        ticker_list = [stock.ticker for stock in stocks]

        if not ticker_list:
            logger.error("No stocks found in database. Please load stock list first.")
            sys.exit(1)

        db.close()
    else:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

    # Apply limit if specified
    if limit:
        ticker_list = ticker_list[:limit]

    logger.info(f"Updating financial ratios for {len(ticker_list)} stocks")

    # Process each ticker
    total_records = 0
    successful = 0
    failed = 0

    for ticker in tqdm(ticker_list, desc="Processing stocks"):
        try:
            count = update_stock_ratios(ticker, period)
            total_records += count
            if count > 0:
                successful += 1
            else:
                failed += 1

            # Rate limiting - use configurable delay
            asyncio.run(asyncio.sleep(delay))

        except Exception as e:
            logger.error(f"Failed to process {ticker}: {e}")
            failed += 1
            continue

    # Summary
    print("\n" + "=" * 60)
    print("FINANCIAL RATIO CALCULATION SUMMARY")
    print("=" * 60)
    print(f"Total stocks processed: {len(ticker_list)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total ratio records: {total_records}")
    print("=" * 60 + "\n")

    logger.info("Financial ratio calculation complete")


if __name__ == "__main__":
    main()
