"""Unit tests for VNStock client."""
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.core.data_ingestion.vnstock_client import VNStockClient, VNStockAPIError


@pytest.fixture
def vnstock_client() -> VNStockClient:
    """Create VNStock client fixture."""
    return VNStockClient()


@pytest.fixture
def mock_price_data() -> pd.DataFrame:
    """Create mock price data."""
    return pd.DataFrame(
        {
            "time": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [98.0, 99.0, 100.0],
            "close": [103.0, 104.0, 105.0],
            "volume": [1000000, 1100000, 1200000],
        }
    )


@pytest.mark.asyncio
async def test_get_daily_prices_success(
    vnstock_client: VNStockClient, mock_price_data: pd.DataFrame
) -> None:
    """Test successful daily price fetch."""
    with patch.object(
        vnstock_client, "_run_in_executor", return_value=mock_price_data
    ):
        result = await vnstock_client.get_daily_prices(
            ticker="VNM",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
        )

        assert len(result) == 3
        assert result[0]["ticker"] == "VNM"
        assert "open" in result[0]
        assert "close" in result[0]
        assert "adjusted_close" in result[0]
        assert result[0]["volume"] == 1000000


@pytest.mark.asyncio
async def test_get_daily_prices_empty_response(vnstock_client: VNStockClient) -> None:
    """Test daily price fetch with empty response."""
    with patch.object(vnstock_client, "_run_in_executor", return_value=pd.DataFrame()):
        result = await vnstock_client.get_daily_prices(
            ticker="INVALID",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
        )

        assert result == []


@pytest.mark.asyncio
async def test_get_daily_prices_api_error(vnstock_client: VNStockClient) -> None:
    """Test daily price fetch with API error."""
    with patch.object(
        vnstock_client, "_run_in_executor", side_effect=Exception("API Error")
    ):
        with pytest.raises(VNStockAPIError):
            await vnstock_client.get_daily_prices(
                ticker="VNM",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 3),
            )


@pytest.mark.asyncio
async def test_get_stock_list_success(vnstock_client: VNStockClient) -> None:
    """Test successful stock list fetch."""
    mock_df = pd.DataFrame(
        {
            "ticker": ["VNM", "HPG", "VIC"],
            "organName": ["VinaMilk", "Hoa Phat", "VinGroup"],
            "comGroupCode": ["HOSE", "HOSE", "HOSE"],
            "industryName": ["Food", "Steel", "Real Estate"],
        }
    )

    with patch.object(vnstock_client, "_run_in_executor", return_value=mock_df):
        result = await vnstock_client.get_stock_list(exchange="HOSE")

        assert len(result) == 3
        assert result[0]["ticker"] == "VNM"
        assert result[0]["name"] == "VinaMilk"
        assert result[0]["exchange"] == "HOSE"


@pytest.mark.asyncio
async def test_get_stock_list_all_exchanges(vnstock_client: VNStockClient) -> None:
    """Test stock list fetch for all exchanges."""
    mock_df = pd.DataFrame(
        {
            "ticker": ["VNM", "HPG"],
            "organName": ["VinaMilk", "Hoa Phat"],
            "comGroupCode": ["HOSE", "HNX"],
            "industryName": ["Food", "Steel"],
        }
    )

    with patch.object(vnstock_client, "_run_in_executor", return_value=mock_df):
        result = await vnstock_client.get_stock_list()

        assert len(result) > 0


@pytest.mark.asyncio
async def test_get_financial_statements_success(vnstock_client: VNStockClient) -> None:
    """Test successful financial statement fetch."""
    mock_df = pd.DataFrame(
        {
            "totalAssets": [1000000],
            "totalLiabilities": [500000],
            "totalEquity": [500000],
        },
        index=[pd.Timestamp("2024-01-01")],
    )
    mock_df["year"] = 2024
    mock_df["quarter"] = 1

    with patch.object(vnstock_client, "_run_in_executor", return_value=mock_df):
        result = await vnstock_client.get_financial_statements(
            ticker="VNM", year=2024, quarter=1, report_type="Q"
        )

        assert result is not None
        assert "totalAssets" in result


@pytest.mark.asyncio
async def test_get_corporate_actions_returns_empty(vnstock_client: VNStockClient) -> None:
    """Test corporate actions returns empty list (pre-adjusted prices)."""
    result = await vnstock_client.get_corporate_actions(
        ticker="VNM",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert result == []


@pytest.mark.asyncio
async def test_cache_functionality(vnstock_client: VNStockClient) -> None:
    """Test cache hit functionality."""
    if not vnstock_client.cache:
        pytest.skip("Redis cache not available")

    # Mock cache hit
    cache_key = vnstock_client._get_cache_key(
        "daily_prices", {"symbol": "VNM", "start_date": "2024-01-01", "end_date": "2024-01-03"}
    )

    mock_df = pd.DataFrame(
        {
            "date": [date(2024, 1, 1)],
            "open": [100.0],
            "high": [105.0],
            "low": [98.0],
            "close": [103.0],
            "volume": [1000000],
            "adjusted_close": [103.0],
            "adjustment_factor": [1.0],
        }
    )

    vnstock_client._set_cache(cache_key, mock_df, ttl=60)

    cached_df = vnstock_client._get_from_cache(cache_key)

    assert cached_df is not None
    assert len(cached_df) == 1


@pytest.mark.asyncio
async def test_run_in_executor(vnstock_client: VNStockClient) -> None:
    """Test executor runs sync functions properly."""

    def sync_function() -> int:
        return 42

    result = await vnstock_client._run_in_executor(sync_function)

    assert result == 42


@pytest.mark.asyncio
async def test_close_client(vnstock_client: VNStockClient) -> None:
    """Test client cleanup."""
    await vnstock_client.close()
    # Should not raise any exceptions
