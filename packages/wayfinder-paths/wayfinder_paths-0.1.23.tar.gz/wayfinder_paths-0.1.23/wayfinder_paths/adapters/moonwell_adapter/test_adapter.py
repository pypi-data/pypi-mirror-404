from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wayfinder_paths.adapters.moonwell_adapter.adapter import (
    BASE_CHAIN_ID,
    MANTISSA,
    MOONWELL_DEFAULTS,
    MoonwellAdapter,
)


class TestMoonwellAdapter:
    @pytest.fixture
    def adapter(self):
        config = {
            "strategy_wallet": {"address": "0x1234567890123456789012345678901234567890"}
        }
        return MoonwellAdapter(config=config)

    def test_adapter_type(self, adapter):
        assert adapter.adapter_type == "MOONWELL"

    def test_default_addresses(self, adapter):
        assert (
            adapter.comptroller_address.lower()
            == MOONWELL_DEFAULTS["comptroller"].lower()
        )
        assert (
            adapter.reward_distributor_address.lower()
            == MOONWELL_DEFAULTS["reward_distributor"].lower()
        )
        assert adapter.m_usdc.lower() == MOONWELL_DEFAULTS["m_usdc"].lower()
        assert adapter.m_weth.lower() == MOONWELL_DEFAULTS["m_weth"].lower()
        assert adapter.m_wsteth.lower() == MOONWELL_DEFAULTS["m_wsteth"].lower()
        assert adapter.well_token.lower() == MOONWELL_DEFAULTS["well_token"].lower()

    def test_chain_id(self, adapter):
        assert adapter.chain_id == BASE_CHAIN_ID

    def test_chain_name(self, adapter):
        assert adapter.chain_name == "base"

    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        health = await adapter.health_check()
        assert isinstance(health, dict)
        assert health.get("status") in {"healthy", "unhealthy", "error"}
        assert health.get("adapter") == "MOONWELL"

    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        ok = await adapter.connect()
        assert isinstance(ok, bool)
        assert ok is True

    @pytest.mark.asyncio
    async def test_lend(self, adapter):
        mock_tx_hash = {"tx_hash": "0xabc123", "status": "success"}
        with (
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.ensure_allowance",
                new_callable=AsyncMock,
            ) as mock_allowance,
            patch.object(
                adapter, "_encode_call", new_callable=AsyncMock
            ) as mock_encode,
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.send_transaction",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            mock_allowance.return_value = (True, {})
            mock_encode.return_value = {
                "data": "0x1234",
                "to": MOONWELL_DEFAULTS["m_usdc"],
            }
            mock_send.return_value = mock_tx_hash

            success, result = await adapter.lend(
                mtoken=MOONWELL_DEFAULTS["m_usdc"],
                underlying_token=MOONWELL_DEFAULTS["usdc"],
                amount=10**6,
            )

            assert success
            assert result == mock_tx_hash

    @pytest.mark.asyncio
    async def test_lend_invalid_amount(self, adapter):
        success, result = await adapter.lend(
            mtoken=MOONWELL_DEFAULTS["m_usdc"],
            underlying_token=MOONWELL_DEFAULTS["usdc"],
            amount=0,
        )

        assert success is False
        assert "positive" in result.lower()

    @pytest.mark.asyncio
    async def test_unlend(self, adapter):
        # Mock contract encoding
        mock_contract = MagicMock()
        mock_contract.functions.redeem = MagicMock(
            return_value=MagicMock(
                build_transaction=AsyncMock(return_value={"data": "0x1234"})
            )
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        mock_tx_hash = {"tx_hash": "0xabc123", "status": "success"}

        with (
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
                mock_web3_ctx,
            ),
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.send_transaction",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            mock_send.return_value = mock_tx_hash
            success, result = await adapter.unlend(
                mtoken=MOONWELL_DEFAULTS["m_usdc"],
                amount=10**8,
            )

        assert success
        assert result == mock_tx_hash

    @pytest.mark.asyncio
    async def test_unlend_invalid_amount(self, adapter):
        success, result = await adapter.unlend(
            mtoken=MOONWELL_DEFAULTS["m_usdc"],
            amount=-1,
        )

        assert success is False
        assert "positive" in result.lower()

    @pytest.mark.asyncio
    async def test_borrow(self, adapter):
        # Track calls to return different values (0 before, 10**6 after)
        borrow_balance_calls = [0]

        async def mock_borrow_balance_call(**kwargs):
            result = borrow_balance_calls[0]
            # Next call returns increased balance
            borrow_balance_calls[0] = 10**6
            return result

        # Mock mtoken contract for pre-check and verification
        mock_mtoken = MagicMock()
        mock_mtoken.functions.borrowBalanceStored = MagicMock(
            return_value=MagicMock(call=mock_borrow_balance_call)
        )
        mock_mtoken.functions.borrow = MagicMock(
            return_value=MagicMock(
                call=AsyncMock(return_value=0),
                _encode_transaction_data=MagicMock(return_value="0x1234"),
                build_transaction=AsyncMock(return_value={"data": "0x1234"}),
            )
        )

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_mtoken)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        mock_tx_hash = {"tx_hash": "0xabc123", "status": "success"}

        with (
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
                mock_web3_ctx,
            ),
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.send_transaction",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            mock_send.return_value = mock_tx_hash
            success, result = await adapter.borrow(
                mtoken=MOONWELL_DEFAULTS["m_usdc"],
                amount=10**6,
            )

        assert success
        assert result == mock_tx_hash

    @pytest.mark.asyncio
    async def test_repay(self, adapter):
        mock_tx_hash = {"tx_hash": "0xabc123", "status": "success"}
        with (
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.ensure_allowance",
                new_callable=AsyncMock,
            ) as mock_allowance,
            patch.object(
                adapter, "_encode_call", new_callable=AsyncMock
            ) as mock_encode,
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.send_transaction",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            mock_allowance.return_value = (True, {})
            mock_encode.return_value = {
                "data": "0x1234",
                "to": MOONWELL_DEFAULTS["m_usdc"],
            }
            mock_send.return_value = mock_tx_hash

            success, result = await adapter.repay(
                mtoken=MOONWELL_DEFAULTS["m_usdc"],
                underlying_token=MOONWELL_DEFAULTS["usdc"],
                amount=10**6,
            )

            assert success
            assert result == mock_tx_hash

    @pytest.mark.asyncio
    async def test_set_collateral(self, adapter):
        # Mock comptroller contract for verification
        mock_comptroller = MagicMock()
        mock_comptroller.functions.checkMembership = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=True))
        )
        mock_comptroller.functions.enterMarkets = MagicMock(
            return_value=MagicMock(
                _encode_transaction_data=MagicMock(return_value="0x1234"),
                build_transaction=AsyncMock(return_value={"data": "0x1234"}),
            )
        )

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_comptroller)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        mock_tx_hash = {"tx_hash": "0xabc123", "status": "success"}

        with (
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
                mock_web3_ctx,
            ),
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.send_transaction",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            mock_send.return_value = mock_tx_hash
            success, result = await adapter.set_collateral(
                mtoken=MOONWELL_DEFAULTS["m_wsteth"],
            )

            assert success is True
            assert result == mock_tx_hash

    @pytest.mark.asyncio
    async def test_claim_rewards(self, adapter):
        # Mock contract for getting outstanding rewards
        mock_reward_contract = MagicMock()
        mock_reward_contract.functions.getOutstandingRewardsForUser = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=[]))
        )

        # Mock contract for claiming (on comptroller)
        mock_comptroller = MagicMock()
        mock_comptroller.functions.claimReward = MagicMock(
            return_value=MagicMock(
                build_transaction=AsyncMock(return_value={"data": "0x1234"})
            )
        )

        def mock_contract(address, abi):
            if address.lower() == adapter.reward_distributor_address.lower():
                return mock_reward_contract
            return mock_comptroller

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(side_effect=mock_contract)

        success, result = await adapter.claim_rewards()

        assert success
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_pos_success(self, adapter):
        underlying_addr = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

        # Mock mtoken contract calls
        mock_mtoken = MagicMock()
        mock_mtoken.functions.balanceOf = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=10**8))
        )
        mock_mtoken.functions.exchangeRateStored = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=2 * MANTISSA))
        )
        mock_mtoken.functions.borrowBalanceStored = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=10**6))
        )
        mock_mtoken.functions.underlying = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=underlying_addr))
        )

        # Mock reward distributor contract
        mock_reward = MagicMock()
        mock_reward.functions.getOutstandingRewardsForUser = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=[]))
        )

        def mock_contract(address, abi):
            if address.lower() == adapter.reward_distributor_address.lower():
                return mock_reward
            return mock_mtoken

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(side_effect=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_pos(mtoken=MOONWELL_DEFAULTS["m_usdc"])

        assert success
        assert "mtoken_balance" in result
        assert "underlying_balance" in result
        assert "borrow_balance" in result
        assert "balances" in result
        assert result["mtoken_balance"] == 10**8
        assert result["borrow_balance"] == 10**6

    @pytest.mark.asyncio
    async def test_get_collateral_factor_success(self, adapter):
        # Clear cache to ensure fresh test
        adapter._cf_cache.clear()

        # Mock contract calls - returns (isListed, collateralFactorMantissa)
        mock_contract = MagicMock()
        mock_contract.functions.markets = MagicMock(
            return_value=MagicMock(
                call=AsyncMock(return_value=(True, int(0.75 * MANTISSA)))
            )
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_collateral_factor(
                mtoken=MOONWELL_DEFAULTS["m_wsteth"]
            )

        assert success
        assert result == 0.75

    @pytest.mark.asyncio
    async def test_get_collateral_factor_not_listed(self, adapter):
        mock_contract = MagicMock()
        mock_contract.functions.markets = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=(False, 0)))
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_collateral_factor(
                mtoken="0x0000000000000000000000000000000000000001"
            )

        assert success is False
        assert "not listed" in result.lower()

    @pytest.mark.asyncio
    async def test_get_collateral_factor_caching(self, adapter):
        # Clear cache to ensure fresh test
        adapter._cf_cache.clear()

        call_count = 0

        async def mock_markets_call(**kwargs):
            nonlocal call_count
            call_count += 1
            return (True, int(0.80 * MANTISSA))

        mock_contract = MagicMock()
        mock_contract.functions.markets = MagicMock(
            return_value=MagicMock(call=mock_markets_call)
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        mtoken = MOONWELL_DEFAULTS["m_wsteth"]

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            # First call should hit RPC
            success1, result1 = await adapter.get_collateral_factor(mtoken=mtoken)
            assert success1 is True
            assert result1 == 0.80
            assert call_count == 1

            # Second call should use cache (no additional RPC call)
            success2, result2 = await adapter.get_collateral_factor(mtoken=mtoken)
            assert success2 is True
            assert result2 == 0.80
            assert call_count == 1

            # Third call for same mtoken should still use cache
            success3, result3 = await adapter.get_collateral_factor(mtoken=mtoken)
            assert success3 is True
            assert result3 == 0.80
            assert call_count == 1

            success4, result4 = await adapter.get_collateral_factor(
                mtoken=MOONWELL_DEFAULTS["m_usdc"]
            )
            assert success4 is True
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_collateral_factor_cache_expiry(self, adapter):
        import time

        from wayfinder_paths.adapters.moonwell_adapter import adapter as adapter_module

        # Clear cache to ensure fresh test
        adapter._cf_cache.clear()

        original_ttl = adapter_module.CF_CACHE_TTL

        try:
            adapter_module.CF_CACHE_TTL = 0.1

            call_count = 0

            async def mock_markets_call(**kwargs):
                nonlocal call_count
                call_count += 1
                return (True, int(0.75 * MANTISSA))

            mock_contract = MagicMock()
            mock_contract.functions.markets = MagicMock(
                return_value=MagicMock(call=mock_markets_call)
            )
            mock_web3 = MagicMock()
            mock_web3.eth.contract = MagicMock(return_value=mock_contract)

            @asynccontextmanager
            async def mock_web3_ctx(_chain_id):
                yield mock_web3

            mtoken = MOONWELL_DEFAULTS["m_wsteth"]

            with patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
                mock_web3_ctx,
            ):
                # First call
                await adapter.get_collateral_factor(mtoken=mtoken)
                assert call_count == 1

                # Immediate second call should use cache
                await adapter.get_collateral_factor(mtoken=mtoken)
                assert call_count == 1

                # Wait for cache to expire
                time.sleep(0.15)

                await adapter.get_collateral_factor(mtoken=mtoken)
                assert call_count == 2

        finally:
            # Restore original TTL
            adapter_module.CF_CACHE_TTL = original_ttl

    @pytest.mark.asyncio
    async def test_get_apy_supply(self, adapter):
        rate_per_second = int(1.5e9)

        # Mock mtoken contract
        mock_mtoken = MagicMock()
        mock_mtoken.functions.supplyRatePerTimestamp = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=rate_per_second))
        )
        mock_mtoken.functions.totalSupply = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=10**18))
        )

        # Mock reward distributor
        mock_reward = MagicMock()
        mock_reward.functions.getAllMarketConfigs = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=[]))
        )

        def mock_contract(address, abi):
            if address.lower() == adapter.reward_distributor_address.lower():
                return mock_reward
            return mock_mtoken

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(side_effect=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_apy(
                mtoken=MOONWELL_DEFAULTS["m_usdc"],
                apy_type="supply",
                include_rewards=False,
            )

        assert success
        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_get_apy_borrow(self, adapter):
        rate_per_second = int(2e9)

        # Mock mtoken contract
        mock_mtoken = MagicMock()
        mock_mtoken.functions.borrowRatePerTimestamp = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=rate_per_second))
        )
        mock_mtoken.functions.totalBorrows = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=10**18))
        )

        # Mock reward distributor
        mock_reward = MagicMock()
        mock_reward.functions.getAllMarketConfigs = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=[]))
        )

        def mock_contract(address, abi):
            if address.lower() == adapter.reward_distributor_address.lower():
                return mock_reward
            return mock_mtoken

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(side_effect=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_apy(
                mtoken=MOONWELL_DEFAULTS["m_usdc"],
                apy_type="borrow",
                include_rewards=False,
            )

        assert success
        assert isinstance(result, float)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_get_borrowable_amount_success(self, adapter):
        mock_contract = MagicMock()
        mock_contract.functions.getAccountLiquidity = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=(0, 10**18, 0)))
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_borrowable_amount()

        assert success
        assert result == 10**18

    @pytest.mark.asyncio
    async def test_get_borrowable_amount_shortfall(self, adapter):
        mock_contract = MagicMock()
        mock_contract.functions.getAccountLiquidity = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=(0, 0, 10**16)))
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.get_borrowable_amount()

        assert success is False
        assert "shortfall" in result.lower()

    @pytest.mark.asyncio
    async def test_wrap_eth(self, adapter):
        mock_contract = MagicMock()
        mock_contract.functions.deposit = MagicMock(
            return_value=MagicMock(
                build_transaction=AsyncMock(return_value={"data": "0x1234"})
            )
        )
        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_contract)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        mock_tx_hash = {"tx_hash": "0xabc123", "status": "success"}

        with (
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
                mock_web3_ctx,
            ),
            patch(
                "wayfinder_paths.adapters.moonwell_adapter.adapter.send_transaction",
                new_callable=AsyncMock,
            ) as mock_send,
        ):
            mock_send.return_value = mock_tx_hash
            success, result = await adapter.wrap_eth(amount=10**18)

        assert success
        assert result == mock_tx_hash

    def test_strategy_address_missing(self):
        with pytest.raises(ValueError, match="strategy_wallet"):
            MoonwellAdapter(config={})

    def test_config_override(self):
        custom_comptroller = "0x1111111111111111111111111111111111111111"
        custom_well = "0x2222222222222222222222222222222222222222"
        config = {
            "strategy_wallet": {
                "address": "0x1234567890123456789012345678901234567890"
            },
            "moonwell_adapter": {
                "comptroller": custom_comptroller,
                "well_token": custom_well,
                "chain_id": 1,
            },
        }

        adapter = MoonwellAdapter(config=config)

        assert adapter.comptroller_address.lower() == custom_comptroller.lower()
        assert adapter.well_token.lower() == custom_well.lower()
        assert adapter.chain_id == 1

    @pytest.mark.asyncio
    async def test_max_withdrawable_mtoken_zero_balance(self, adapter):
        # Mock contracts
        mock_mtoken = MagicMock()
        mock_mtoken.functions.balanceOf = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=0))
        )
        mock_mtoken.functions.exchangeRateStored = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=MANTISSA))
        )
        mock_mtoken.functions.getCash = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=10**18))
        )
        mock_mtoken.functions.decimals = MagicMock(
            return_value=MagicMock(call=AsyncMock(return_value=8))
        )
        mock_mtoken.functions.underlying = MagicMock(
            return_value=MagicMock(
                call=AsyncMock(return_value=MOONWELL_DEFAULTS["usdc"])
            )
        )

        mock_web3 = MagicMock()
        mock_web3.eth.contract = MagicMock(return_value=mock_mtoken)

        @asynccontextmanager
        async def mock_web3_ctx(_chain_id):
            yield mock_web3

        with patch(
            "wayfinder_paths.adapters.moonwell_adapter.adapter.web3_from_chain_id",
            mock_web3_ctx,
        ):
            success, result = await adapter.max_withdrawable_mtoken(
                mtoken=MOONWELL_DEFAULTS["m_usdc"]
            )

        assert success
        assert result["cTokens_raw"] == 0
        assert result["underlying_raw"] == 0
