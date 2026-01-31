from unittest.mock import AsyncMock

import pytest

from wayfinder_paths.adapters.pool_adapter.adapter import PoolAdapter


class TestPoolAdapter:
    @pytest.fixture
    def mock_pool_client(self):
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def adapter(self, mock_pool_client):
        adapter = PoolAdapter()
        adapter.pool_client = mock_pool_client
        return adapter

    @pytest.mark.asyncio
    async def test_get_pools_by_ids_success(self, adapter, mock_pool_client):
        mock_response = {
            "pools": [
                {
                    "id": "pool-123",
                    "name": "USDC/USDT Pool",
                    "symbol": "USDC-USDT",
                    "apy": 0.05,
                    "tvl": 1000000,
                }
            ]
        }
        mock_pool_client.get_pools_by_ids = AsyncMock(return_value=mock_response)

        success, data = await adapter.get_pools_by_ids(
            pool_ids=["pool-123", "pool-456"]
        )

        assert success
        assert data == mock_response
        mock_pool_client.get_pools_by_ids.assert_called_once_with(
            pool_ids=["pool-123", "pool-456"]
        )

    @pytest.mark.asyncio
    async def test_get_pools_success(self, adapter, mock_pool_client):
        # Mock response
        mock_response = {
            "matches": [
                {
                    "id": "pool-123",
                    "apy": 5.2,
                    "tvlUsd": 1000000,
                    "stablecoin": True,
                    "network": "base",
                }
            ]
        }
        mock_pool_client.get_pools = AsyncMock(return_value=mock_response)

        success, data = await adapter.get_pools()

        assert success
        assert data == mock_response

    @pytest.mark.asyncio
    async def test_get_pools_by_ids_failure(self, adapter, mock_pool_client):
        mock_pool_client.get_pools_by_ids = AsyncMock(
            side_effect=Exception("API Error")
        )

        success, data = await adapter.get_pools_by_ids(["pool-123"])

        assert success is False
        assert "API Error" in data

    def test_adapter_type(self, adapter):
        assert adapter.adapter_type == "POOL"
