"""Initialize database schema and tables."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.database.connection import sync_engine
from src.database.models import Base
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def init_database() -> None:
    """Initialize database with tables and TimescaleDB hypertables."""
    logger.info("Starting database initialization...")

    try:
        # Create all tables
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Tables created successfully")

        # Connect and enable TimescaleDB
        with sync_engine.connect() as conn:
            # Enable TimescaleDB extension
            logger.info("Enabling TimescaleDB extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.commit()

            # Create hypertables for time-series data
            logger.info("Creating TimescaleDB hypertables...")

            # DailyPrice hypertable
            try:
                conn.execute(text(
                    "SELECT create_hypertable('daily_price', 'date', "
                    "if_not_exists => TRUE, migrate_data => TRUE);"
                ))
                logger.info("Created hypertable for daily_price")
            except Exception as e:
                logger.warning(f"Hypertable for daily_price may already exist: {e}")

            # MarketIndex hypertable
            try:
                conn.execute(text(
                    "SELECT create_hypertable('market_index', 'date', "
                    "if_not_exists => TRUE, migrate_data => TRUE);"
                ))
                logger.info("Created hypertable for market_index")
            except Exception as e:
                logger.warning(f"Hypertable for market_index may already exist: {e}")

            # Factor hypertable
            try:
                conn.execute(text(
                    "SELECT create_hypertable('factor', 'date', "
                    "if_not_exists => TRUE, migrate_data => TRUE);"
                ))
                logger.info("Created hypertable for factor")
            except Exception as e:
                logger.warning(f"Hypertable for factor may already exist: {e}")

            conn.commit()

            # Create additional indexes for performance
            logger.info("Creating additional indexes...")

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_daily_price_ticker_date_desc "
                "ON daily_price (ticker, date DESC);",

                "CREATE INDEX IF NOT EXISTS idx_factor_ticker_date_desc "
                "ON factor (ticker, date DESC);",

                "CREATE INDEX IF NOT EXISTS idx_financial_ratio_ticker_date_desc "
                "ON financial_ratio (ticker, date DESC);",
            ]

            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql.split('idx_')[1].split()[0]}")
                except Exception as e:
                    logger.warning(f"Index may already exist: {e}")

            conn.commit()

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    init_database()
