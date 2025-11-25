"""Data client factory for selecting appropriate data source."""
from typing import Union

from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_data_client() -> Union["VNStockClient", "SSIClient", "DNSEClient"]:  # type: ignore
    """Get data client based on configuration.

    Returns:
        Data client instance (VNStockClient, SSIClient, or DNSEClient)
    """
    data_source = settings.DATA_SOURCE.lower()

    if data_source == "vnstock":
        from src.core.data_ingestion.vnstock_client import VNStockClient

        logger.info("Using VNStock as data source")
        return VNStockClient()
    elif data_source == "ssi":
        from src.core.data_ingestion.ssi_client import SSIClient

        logger.info("Using SSI as data source")
        return SSIClient()
    elif data_source == "dnse":
        from src.core.data_ingestion.dnse_client import DNSEClient

        logger.info("Using DNSE as data source")
        return DNSEClient()
    else:
        logger.warning(
            f"Unknown data source '{data_source}', falling back to VNStock (default)"
        )
        from src.core.data_ingestion.vnstock_client import VNStockClient

        return VNStockClient()
