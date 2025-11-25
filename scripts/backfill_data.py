"""Backfill historical stock data using configured data source."""
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

import click
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.data_ingestion.data_client_factory import get_data_client
from src.database.connection import get_sync_session
from src.database.models import DailyPrice, StockInfo
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


async def backfill_stock_prices(
    ticker: str,
    start_date: date,
    end_date: date,
    client,  # type: ignore
) -> int:
    """Backfill price data for a single stock.

    Args:
        ticker: Stock ticker
        start_date: Start date
        end_date: End date
        client: Data client instance

    Returns:
        Number of records inserted
    """
    try:
        logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")

        records = await client.get_daily_prices(ticker, start_date, end_date)

        if not records:
            logger.warning(f"No data returned for {ticker}")
            return 0

        # Insert into database
        db = next(get_sync_session())
        inserted_count = 0

        for record in records:
            # Check if record already exists
            existing = (
                db.query(DailyPrice)
                .filter(
                    DailyPrice.ticker == record["ticker"],
                    DailyPrice.date == record["date"],
                )
                .first()
            )

            if not existing:
                price_record = DailyPrice(
                    ticker=record["ticker"],
                    date=record["date"],
                    open=record["open"],
                    high=record["high"],
                    low=record["low"],
                    close=record["close"],
                    volume=record["volume"],
                    value=record.get("value"),
                    adjusted_close=record.get("adjusted_close"),
                    adjustment_factor=record.get("adjustment_factor", 1.0),
                )
                db.add(price_record)
                inserted_count += 1

        db.commit()
        logger.info(f"Inserted {inserted_count} records for {ticker}")

        return inserted_count

    except Exception as e:
        logger.error(f"Error backfilling {ticker}: {e}")
        return 0


async def backfill_all_tickers(
    tickers: list[str],
    start_date: date,
    end_date: date,
) -> None:
    """Backfill data for multiple tickers.

    Args:
        tickers: List of ticker symbols
        start_date: Start date
        end_date: End date
    """
    client = get_data_client()

    logger.info(
        f"Starting backfill for {len(tickers)} tickers using {settings.DATA_SOURCE}"
    )

    total_records = 0

    for ticker in tqdm(tickers, desc="Backfilling stocks"):
        count = await backfill_stock_prices(ticker, start_date, end_date, client)
        total_records += count
        await asyncio.sleep(1)  # Rate limiting

    await client.close()

    logger.info(f"Backfill complete. Total records inserted: {total_records}")


@click.command()
@click.option(
    "--tickers",
    default="all",
    help="Comma-separated tickers or 'all' for all stocks",
)
@click.option(
    "--start-date",
    default=None,
    help="Start date (YYYY-MM-DD), defaults to BACKFILL_START_DATE",
)
@click.option(
    "--end-date",
    default=None,
    help="End date (YYYY-MM-DD), defaults to today",
)
@click.option(
    "--exchange",
    default=None,
    help="Filter by exchange (HOSE, HNX, UPCOM)",
)
def main(
    tickers: str,
    start_date: str | None,
    end_date: str | None,
    exchange: str | None,
) -> None:
    """Backfill historical stock data.

    Args:
        tickers: Ticker symbols or 'all'
        start_date: Start date string
        end_date: End date string
        exchange: Exchange filter
    """
    # Parse dates
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start = datetime.strptime(settings.BACKFILL_START_DATE, "%Y-%m-%d").date()

    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end = date.today()

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
    else:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]

    logger.info(f"Backfilling {len(ticker_list)} tickers from {start} to {end}")

    # Run backfill
    asyncio.run(backfill_all_tickers(ticker_list, start, end))


if __name__ == "__main__":
    main()
