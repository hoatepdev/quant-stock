"""Load stock list from data source into database."""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import click

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.data_ingestion.data_client_factory import get_data_client
from src.database.connection import get_sync_session
from src.database.models import StockInfo
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


async def load_stocks(exchange: str | None = None) -> int:
    """Load stocks from data source into database.

    Args:
        exchange: Exchange filter (HOSE, HNX, UPCOM) or None for all

    Returns:
        Number of stocks loaded
    """
    client = get_data_client()

    try:
        logger.info(
            f"Fetching stock list from {settings.DATA_SOURCE} "
            f"for {exchange or 'all exchanges'}"
        )

        # Fetch stock list
        stocks = await client.get_stock_list(exchange=exchange)

        if not stocks:
            logger.warning("No stocks returned from data source")
            return 0

        logger.info(f"Fetched {len(stocks)} stocks from data source")

        # Load into database
        db = next(get_sync_session())
        loaded_count = 0
        updated_count = 0

        for stock_data in stocks:
            ticker = stock_data["ticker"]

            # Check if stock already exists
            existing = db.query(StockInfo).filter(StockInfo.ticker == ticker).first()

            if existing:
                # Update existing stock
                existing.name = stock_data.get("name", existing.name)
                existing.exchange = stock_data.get("exchange", existing.exchange)
                existing.industry = stock_data.get("industry", existing.industry)
                existing.is_active = True
                existing.updated_at = datetime.now()
                updated_count += 1
            else:
                # Insert new stock
                listing_date = stock_data.get("listing_date")
                if listing_date and isinstance(listing_date, str):
                    try:
                        listing_date = datetime.strptime(listing_date, "%Y-%m-%d").date()
                    except ValueError:
                        listing_date = None

                stock_info = StockInfo(
                    ticker=ticker,
                    name=stock_data.get("name"),
                    exchange=stock_data.get("exchange"),
                    industry=stock_data.get("industry"),
                    sector=stock_data.get("sector"),
                    listing_date=listing_date,
                    is_active=True,
                )
                db.add(stock_info)
                loaded_count += 1

        db.commit()

        logger.info(
            f"Stock list loaded successfully: {loaded_count} new, "
            f"{updated_count} updated"
        )

        return loaded_count + updated_count

    except Exception as e:
        logger.error(f"Error loading stock list: {e}")
        raise
    finally:
        await client.close()


@click.command()
@click.option(
    "--exchange",
    default=None,
    help="Filter by exchange (HOSE, HNX, UPCOM)",
)
def main(exchange: str | None) -> None:
    """Load stock list from data source into database.

    Args:
        exchange: Exchange filter
    """
    logger.info(f"Starting stock list load using {settings.DATA_SOURCE}")

    count = asyncio.run(load_stocks(exchange=exchange))

    logger.info(f"Completed. Total stocks processed: {count}")


if __name__ == "__main__":
    main()
