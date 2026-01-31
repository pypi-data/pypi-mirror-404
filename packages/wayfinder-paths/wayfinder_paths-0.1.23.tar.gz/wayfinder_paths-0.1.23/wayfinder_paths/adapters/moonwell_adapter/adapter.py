from __future__ import annotations

import asyncio
import time
from typing import Any, Literal

from eth_utils import to_checksum_address

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.constants.base import MANTISSA, MAX_UINT256, SECONDS_PER_YEAR
from wayfinder_paths.core.constants.chains import CHAIN_ID_BASE
from wayfinder_paths.core.constants.contracts import (
    BASE_USDC,
    BASE_WETH,
    BASE_WSTETH,
    MOONWELL_COMPTROLLER,
    MOONWELL_M_USDC,
    MOONWELL_M_WETH,
    MOONWELL_M_WSTETH,
    MOONWELL_REWARD_DISTRIBUTOR,
    MOONWELL_WELL_TOKEN,
)
from wayfinder_paths.core.constants.moonwell_abi import (
    COMPTROLLER_ABI,
    MTOKEN_ABI,
    REWARD_DISTRIBUTOR_ABI,
    WETH_ABI,
)
from wayfinder_paths.core.utils.tokens import ensure_allowance
from wayfinder_paths.core.utils.transaction import send_transaction
from wayfinder_paths.core.utils.web3 import web3_from_chain_id

MOONWELL_DEFAULTS = {
    "m_usdc": MOONWELL_M_USDC,
    "m_weth": MOONWELL_M_WETH,
    "m_wsteth": MOONWELL_M_WSTETH,
    "usdc": BASE_USDC,
    "weth": BASE_WETH,
    "wsteth": BASE_WSTETH,
    "reward_distributor": MOONWELL_REWARD_DISTRIBUTOR,
    "comptroller": MOONWELL_COMPTROLLER,
    "well_token": MOONWELL_WELL_TOKEN,
}

BASE_CHAIN_ID = CHAIN_ID_BASE
CF_CACHE_TTL = 3600
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 3.0


def _is_rate_limit_error(error: Exception | str) -> bool:
    error_str = str(error)
    return "429" in error_str or "Too Many Requests" in error_str


def _timestamp_rate_to_apy(rate: float) -> float:
    return (1 + rate) ** SECONDS_PER_YEAR - 1


class MoonwellAdapter(BaseAdapter):
    adapter_type = "MOONWELL"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        token_client: TokenClient | None = None,
        strategy_wallet_signing_callback=None,
    ) -> None:
        super().__init__("moonwell_adapter", config)
        cfg = config or {}
        adapter_cfg = cfg.get("moonwell_adapter") or {}

        self.token_client = token_client
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback

        strategy_wallet = cfg.get("strategy_wallet") or {}
        strategy_addr = strategy_wallet.get("address")
        if not strategy_addr:
            raise ValueError("strategy_wallet.address is required")
        self.strategy_wallet_address = to_checksum_address(strategy_addr)
        self.chain_id = adapter_cfg.get("chain_id", BASE_CHAIN_ID)
        self.chain_name = "base"

        # Protocol addresses (with config overrides)
        self.comptroller_address = to_checksum_address(
            adapter_cfg.get("comptroller") or MOONWELL_DEFAULTS["comptroller"]
        )
        self.reward_distributor_address = to_checksum_address(
            adapter_cfg.get("reward_distributor")
            or MOONWELL_DEFAULTS["reward_distributor"]
        )
        self.well_token = to_checksum_address(
            adapter_cfg.get("well_token") or MOONWELL_DEFAULTS["well_token"]
        )

        # Token addresses
        self.m_usdc = to_checksum_address(
            adapter_cfg.get("m_usdc") or MOONWELL_DEFAULTS["m_usdc"]
        )
        self.m_weth = to_checksum_address(
            adapter_cfg.get("m_weth") or MOONWELL_DEFAULTS["m_weth"]
        )
        self.m_wsteth = to_checksum_address(
            adapter_cfg.get("m_wsteth") or MOONWELL_DEFAULTS["m_wsteth"]
        )
        self.usdc = to_checksum_address(
            adapter_cfg.get("usdc") or MOONWELL_DEFAULTS["usdc"]
        )
        self.weth = to_checksum_address(
            adapter_cfg.get("weth") or MOONWELL_DEFAULTS["weth"]
        )
        self.wsteth = to_checksum_address(
            adapter_cfg.get("wsteth") or MOONWELL_DEFAULTS["wsteth"]
        )

        # Collateral factor cache: mtoken -> (value, timestamp)
        self._cf_cache: dict[str, tuple[float, float]] = {}

    async def lend(
        self,
        *,
        mtoken: str,
        underlying_token: str,
        amount: int,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = to_checksum_address(mtoken)
        underlying_token = to_checksum_address(underlying_token)

        # Approve mToken to spend underlying tokens
        approved = await ensure_allowance(
            token_address=underlying_token,
            owner=strategy,
            spender=mtoken,
            amount=amount,
            chain_id=self.chain_id,
            signing_callback=self.strategy_wallet_signing_callback,
            approval_amount=MAX_UINT256,
        )
        if not approved[0]:
            return approved

        # Mint mTokens (supply underlying)
        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="mint",
            args=[amount],
            from_address=strategy,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return (True, txn_hash)

    async def unlend(
        self,
        *,
        mtoken: str,
        amount: int,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = to_checksum_address(mtoken)

        # Redeem mTokens for underlying
        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="redeem",
            args=[amount],
            from_address=strategy,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return (True, txn_hash)

    async def borrow(
        self,
        *,
        mtoken: str,
        amount: int,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = to_checksum_address(mtoken)

        borrow_before = 0
        try:
            async with web3_from_chain_id(self.chain_id) as web3:
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)

                borrow_before = await mtoken_contract.functions.borrowBalanceStored(
                    strategy
                ).call(block_identifier="pending")

                # Simulate borrow to check for errors before submitting
                try:
                    borrow_return = await mtoken_contract.functions.borrow(amount).call(
                        {"from": strategy}, block_identifier="pending"
                    )
                    if borrow_return != 0:
                        self.logger.warning(
                            f"Borrow simulation returned error code {borrow_return}. "
                            "Codes: 3=COMPTROLLER_REJECTION, 9=INVALID_ACCOUNT_PAIR, "
                            "14=INSUFFICIENT_LIQUIDITY"
                        )
                except Exception as call_err:
                    self.logger.debug(f"Borrow simulation failed: {call_err}")
        except Exception as e:
            self.logger.warning(f"Failed to get pre-borrow balance: {e}")

        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="borrow",
            args=[amount],
            from_address=strategy,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)

        # Verify the borrow actually succeeded by checking balance increased
        try:
            async with web3_from_chain_id(self.chain_id) as web3:
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                borrow_after = await mtoken_contract.functions.borrowBalanceStored(
                    strategy
                ).call(block_identifier="pending")

                # Borrow balance should have increased by approximately the amount
                # Allow for some interest accrual
                expected_increase = amount * 0.99
                actual_increase = borrow_after - borrow_before

                if actual_increase < expected_increase:
                    self.logger.error(
                        f"Borrow verification failed: balance only increased by "
                        f"{actual_increase} (expected ~{amount}). "
                        f"Moonwell likely returned an error code. "
                        f"Before: {borrow_before}, After: {borrow_after}"
                    )
                    return (
                        False,
                        f"Borrow failed: balance did not increase as expected. "
                        f"Before: {borrow_before}, After: {borrow_after}, Expected: +{amount}",
                    )
        except Exception as e:
            self.logger.warning(f"Could not verify borrow balance: {e}")

        return (True, txn_hash)

    async def repay(
        self,
        *,
        mtoken: str,
        underlying_token: str,
        amount: int,
        repay_full: bool = False,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = to_checksum_address(mtoken)
        underlying_token = to_checksum_address(underlying_token)

        # Approve mToken to spend underlying tokens for repayment
        # When repay_full=True, approve the amount we have, Moonwell will use only what's needed
        approved = await ensure_allowance(
            token_address=underlying_token,
            owner=strategy,
            spender=mtoken,
            amount=amount,
            chain_id=self.chain_id,
            signing_callback=self.strategy_wallet_signing_callback,
            approval_amount=MAX_UINT256,
        )
        if not approved[0]:
            return approved

        # Use max uint256 for full repayment to avoid balance calculation issues
        repay_amount = MAX_UINT256 if repay_full else amount

        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="repayBorrow",
            args=[repay_amount],
            from_address=strategy,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return (True, txn_hash)

    async def set_collateral(
        self,
        *,
        mtoken: str,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        mtoken = to_checksum_address(mtoken)

        tx = await self._encode_call(
            target=self.comptroller_address,
            abi=COMPTROLLER_ABI,
            fn_name="enterMarkets",
            args=[[mtoken]],
            from_address=strategy,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)

        # Verify the market was actually entered
        try:
            async with web3_from_chain_id(self.chain_id) as web3:
                comptroller = web3.eth.contract(
                    address=self.comptroller_address, abi=COMPTROLLER_ABI
                )
                is_member = await comptroller.functions.checkMembership(
                    strategy, mtoken
                ).call(block_identifier="pending")

                if not is_member:
                    self.logger.error(
                        f"set_collateral verification failed: account {strategy} "
                        f"is not a member of market {mtoken} after enterMarkets call"
                    )
                    return (
                        False,
                        f"enterMarkets succeeded but account is not a member of market {mtoken}",
                    )
        except Exception as e:
            self.logger.warning(f"Could not verify market membership: {e}")

        return (True, txn_hash)

    async def is_market_entered(
        self,
        *,
        mtoken: str,
        account: str | None = None,
    ) -> tuple[bool, bool | str]:
        try:
            acct = (
                to_checksum_address(account)
                if account
                else self.strategy_wallet_address
            )
            mtoken = to_checksum_address(mtoken)

            async with web3_from_chain_id(self.chain_id) as web3:
                comptroller = web3.eth.contract(
                    address=self.comptroller_address, abi=COMPTROLLER_ABI
                )
                is_member = await comptroller.functions.checkMembership(
                    acct, mtoken
                ).call(block_identifier="pending")
                return True, bool(is_member)
        except Exception as exc:
            return False, str(exc)

    async def remove_collateral(
        self,
        *,
        mtoken: str,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        mtoken = to_checksum_address(mtoken)

        tx = await self._encode_call(
            target=self.comptroller_address,
            abi=COMPTROLLER_ABI,
            fn_name="exitMarket",
            args=[mtoken],
            from_address=strategy,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return (True, txn_hash)

    async def claim_rewards(
        self,
        *,
        min_rewards_usd: float = 0.0,
    ) -> tuple[bool, dict[str, int] | str]:
        strategy = self.strategy_wallet_address

        rewards = await self._get_outstanding_rewards(strategy)

        # Skip if no rewards to claim
        if not rewards:
            return True, {}

        if min_rewards_usd > 0 and self.token_client:
            total_usd = await self._calculate_rewards_usd(rewards)
            if total_usd < min_rewards_usd:
                return True, {}

        # Claim via comptroller (like reference implementation)
        tx = await self._encode_call(
            target=self.comptroller_address,
            abi=COMPTROLLER_ABI,
            fn_name="claimReward",
            args=[strategy],
            from_address=strategy,
        )
        await send_transaction(tx, self.strategy_wallet_signing_callback)
        return True, rewards

    async def _get_outstanding_rewards(self, account: str) -> dict[str, int]:
        try:
            async with web3_from_chain_id(self.chain_id) as web3:
                contract = web3.eth.contract(
                    address=self.reward_distributor_address, abi=REWARD_DISTRIBUTOR_ABI
                )

                all_rewards = await contract.functions.getOutstandingRewardsForUser(
                    account
                ).call(block_identifier="pending")

                rewards: dict[str, int] = {}
                for mtoken_data in all_rewards:
                    # mtoken_data is (mToken, [(rewardToken, totalReward, supplySide, borrowSide)])
                    if len(mtoken_data) >= 2:
                        token_rewards = mtoken_data[1] if len(mtoken_data) > 1 else []
                        for reward_info in token_rewards:
                            if len(reward_info) >= 2:
                                token_addr = reward_info[0]
                                total_reward = reward_info[1]
                                if total_reward > 0:
                                    key = f"{self.chain_name}_{token_addr}"
                                    rewards[key] = rewards.get(key, 0) + total_reward
                return rewards
        except Exception:
            return {}

    async def _calculate_rewards_usd(self, rewards: dict[str, int]) -> float:
        if not self.token_client:
            return 0.0

        total_usd = 0.0
        for token_key, amount in rewards.items():
            try:
                token_data = await self.token_client.get_token_details(token_key)
                if token_data:
                    price = token_data.get("price_usd") or token_data.get("price", 0)
                    decimals = token_data.get("decimals", 18)
                    total_usd += (amount / (10**decimals)) * price
            except Exception:
                pass
        return total_usd

    async def get_pos(
        self,
        *,
        mtoken: str,
        account: str | None = None,
        include_usd: bool = False,
        max_retries: int = 3,
        block_identifier: int | str | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        mtoken = to_checksum_address(mtoken)
        account = (
            to_checksum_address(account) if account else self.strategy_wallet_address
        )
        block_id = block_identifier if block_identifier is not None else "pending"

        bal = exch = borrow = underlying = rewards = None
        last_error = ""

        for attempt in range(max_retries):
            try:
                async with web3_from_chain_id(self.chain_id) as web3:
                    mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                    rewards_contract = web3.eth.contract(
                        address=self.reward_distributor_address,
                        abi=REWARD_DISTRIBUTOR_ABI,
                    )

                    # (parallel fetch would make 5 simultaneous calls per position)
                    bal = await mtoken_contract.functions.balanceOf(account).call(
                        block_identifier=block_id
                    )
                    exch = await mtoken_contract.functions.exchangeRateStored().call(
                        block_identifier=block_id
                    )
                    borrow = await mtoken_contract.functions.borrowBalanceStored(
                        account
                    ).call(block_identifier=block_id)
                    underlying = await mtoken_contract.functions.underlying().call(
                        block_identifier=block_id
                    )
                    rewards = (
                        await rewards_contract.functions.getOutstandingRewardsForUser(
                            mtoken, account
                        ).call(block_identifier=block_id)
                    )
                break
            except Exception as exc:
                last_error = str(exc)
                if "429" in last_error or "Too Many Requests" in last_error:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        await asyncio.sleep(wait_time)
                        continue
                return False, last_error
        else:
            # All retries exhausted
            return False, last_error

        try:
            reward_balances = self._process_rewards(rewards)

            mtoken_key = f"{self.chain_name}_{mtoken}"
            underlying_key = f"{self.chain_name}_{underlying}"

            balances: dict[str, int] = {mtoken_key: bal}
            balances.update(reward_balances)

            if borrow > 0:
                balances[underlying_key] = -borrow

            result: dict[str, Any] = {
                "balances": balances,
                "mtoken_balance": bal,
                "underlying_balance": (bal * exch) // MANTISSA,
                "borrow_balance": borrow,
                "exchange_rate": exch,
                "underlying_token": underlying,
            }

            if include_usd and self.token_client:
                usd_balances = await self._calculate_usd_balances(
                    balances, underlying_key, exch
                )
                result["usd_balances"] = usd_balances

            return True, result
        except Exception as exc:
            return False, str(exc)

    def _process_rewards(self, rewards: list) -> dict[str, int]:
        result: dict[str, int] = {}
        for reward_info in rewards:
            if len(reward_info) >= 2:
                token_addr = reward_info[0]
                total_reward = reward_info[1]
                if total_reward > 0:
                    key = f"{self.chain_name}_{token_addr}"
                    result[key] = total_reward
        return result

    async def _calculate_usd_balances(
        self, balances: dict[str, int], underlying_key: str, _exchange_rate: int
    ) -> dict[str, float | None]:
        if not self.token_client:
            return {}

        tokens = set(balances.keys()) | {underlying_key}
        token_data: dict[str, dict | None] = {}
        for token_key in tokens:
            try:
                token_data[token_key] = await self.token_client.get_token_details(
                    token_key
                )
            except Exception:
                token_data[token_key] = None

        usd_balances: dict[str, float | None] = {}
        for token_key, bal in balances.items():
            data = token_data.get(token_key)
            if data:
                price = data.get("price_usd") or data.get("price")
                if price is not None:
                    decimals = data.get("decimals", 18)
                    usd_balances[token_key] = (bal / (10**decimals)) * price
                else:
                    usd_balances[token_key] = None
            else:
                usd_balances[token_key] = None

        return usd_balances

    async def get_collateral_factor(
        self,
        *,
        mtoken: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> tuple[bool, float | str]:
        mtoken = to_checksum_address(mtoken)

        now = time.time()
        if mtoken in self._cf_cache:
            cached_value, cached_time = self._cf_cache[mtoken]
            if now - cached_time < CF_CACHE_TTL:
                return True, cached_value

        last_error = ""
        for attempt in range(max_retries):
            try:
                async with web3_from_chain_id(self.chain_id) as web3:
                    contract = web3.eth.contract(
                        address=self.comptroller_address, abi=COMPTROLLER_ABI
                    )

                    # markets() returns (isListed, collateralFactorMantissa)
                    result = await contract.functions.markets(mtoken).call(
                        block_identifier="pending"
                    )
                    is_listed, collateral_factor_mantissa = result

                    if not is_listed:
                        return False, f"Market {mtoken} is not listed"

                    collateral_factor = collateral_factor_mantissa / MANTISSA

                    # Cache the result
                    self._cf_cache[mtoken] = (collateral_factor, now)

                    return True, collateral_factor
            except Exception as exc:
                last_error = str(exc)
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, last_error

        return False, last_error

    async def get_apy(
        self,
        *,
        mtoken: str,
        apy_type: Literal["supply", "borrow"] = "supply",
        include_rewards: bool = True,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> tuple[bool, float | str]:
        mtoken = to_checksum_address(mtoken)

        last_error = ""
        for attempt in range(max_retries):
            try:
                async with web3_from_chain_id(self.chain_id) as web3:
                    mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                    reward_distributor = web3.eth.contract(
                        address=self.reward_distributor_address,
                        abi=REWARD_DISTRIBUTOR_ABI,
                    )

                    if apy_type == "supply":
                        rate_per_timestamp = await mtoken_contract.functions.supplyRatePerTimestamp().call(
                            block_identifier="pending"
                        )
                        mkt_config = (
                            await reward_distributor.functions.getAllMarketConfigs(
                                mtoken
                            ).call(block_identifier="pending")
                        )
                        total_value = (
                            await mtoken_contract.functions.totalSupply().call(
                                block_identifier="pending"
                            )
                        )
                    else:
                        rate_per_timestamp = await mtoken_contract.functions.borrowRatePerTimestamp().call(
                            block_identifier="pending"
                        )
                        mkt_config = (
                            await reward_distributor.functions.getAllMarketConfigs(
                                mtoken
                            ).call(block_identifier="pending")
                        )
                        total_value = (
                            await mtoken_contract.functions.totalBorrows().call(
                                block_identifier="pending"
                            )
                        )

                    rate = rate_per_timestamp / MANTISSA
                    apy = _timestamp_rate_to_apy(rate)

                    if include_rewards and self.token_client and total_value > 0:
                        rewards_apr = await self._calculate_rewards_apr(
                            mtoken, mkt_config, total_value, apy_type
                        )
                        apy += rewards_apr

                    return True, apy
            except Exception as exc:
                last_error = str(exc)
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, last_error

        return False, last_error

    async def _calculate_rewards_apr(
        self,
        mtoken: str,
        mkt_config: list,
        total_value: int,
        apy_type: str,
    ) -> float:
        if not self.token_client:
            return 0.0

        try:
            # Find WELL token config
            well_config = None
            for config in mkt_config:
                if len(config) >= 6 and config[1].lower() == self.well_token.lower():
                    well_config = config
                    break

            if not well_config:
                return 0.0

            # Config format: (mToken, rewardToken, owner, emissionCap, supplyEmissionsPerSec, borrowEmissionsPerSec, ...)
            if apy_type == "supply":
                well_rate = well_config[4]
            else:
                well_rate = well_config[5]
                # Borrow rewards are shown as negative in some implementations
                if well_rate < 0:
                    well_rate = -well_rate

            if well_rate == 0:
                return 0.0

            async with web3_from_chain_id(self.chain_id) as web3:
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                underlying_addr = await mtoken_contract.functions.underlying().call(
                    block_identifier="pending"
                )

            well_key = f"{self.chain_name}_{self.well_token}"
            underlying_key = f"{self.chain_name}_{underlying_addr}"

            well_data, underlying_data = await asyncio.gather(
                self.token_client.get_token_details(well_key),
                self.token_client.get_token_details(underlying_key),
            )

            well_price = (
                well_data.get("price_usd") or well_data.get("price", 0)
                if well_data
                else 0
            )
            underlying_price = (
                underlying_data.get("price_usd") or underlying_data.get("price", 0)
                if underlying_data
                else 0
            )
            underlying_decimals = (
                underlying_data.get("decimals", 18) if underlying_data else 18
            )

            if not well_price or not underlying_price:
                return 0.0

            total_value_usd = (
                total_value / (10**underlying_decimals)
            ) * underlying_price

            if total_value_usd == 0:
                return 0.0

            # rewards_apr = well_price * emissions_per_second * seconds_per_year / total_value_usd
            rewards_apr = (
                well_price * (well_rate / MANTISSA) * SECONDS_PER_YEAR / total_value_usd
            )

            return rewards_apr
        except Exception:
            return 0.0

    async def get_borrowable_amount(
        self,
        *,
        account: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> tuple[bool, int | str]:
        account = (
            to_checksum_address(account) if account else self.strategy_wallet_address
        )

        last_error = ""
        for attempt in range(max_retries):
            try:
                async with web3_from_chain_id(self.chain_id) as web3:
                    contract = web3.eth.contract(
                        address=self.comptroller_address, abi=COMPTROLLER_ABI
                    )

                    (
                        error,
                        liquidity,
                        shortfall,
                    ) = await contract.functions.getAccountLiquidity(account).call(
                        block_identifier="pending"
                    )

                    if error != 0:
                        return False, f"Comptroller error: {error}"

                    if shortfall > 0:
                        return False, f"Account has shortfall: {shortfall}"

                    return True, liquidity
            except Exception as exc:
                last_error = str(exc)
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, last_error

        return False, last_error

    async def max_withdrawable_mtoken(
        self,
        *,
        mtoken: str,
        account: str | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        mtoken = to_checksum_address(mtoken)
        account = (
            to_checksum_address(account) if account else self.strategy_wallet_address
        )

        try:
            async with web3_from_chain_id(self.chain_id) as web3:
                comptroller = web3.eth.contract(
                    address=self.comptroller_address, abi=COMPTROLLER_ABI
                )
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)

                bal_raw, exch_raw, cash_raw, m_dec, u_addr = await asyncio.gather(
                    mtoken_contract.functions.balanceOf(account).call(
                        block_identifier="pending"
                    ),
                    mtoken_contract.functions.exchangeRateStored().call(
                        block_identifier="pending"
                    ),
                    mtoken_contract.functions.getCash().call(
                        block_identifier="pending"
                    ),
                    mtoken_contract.functions.decimals().call(
                        block_identifier="pending"
                    ),
                    mtoken_contract.functions.underlying().call(
                        block_identifier="pending"
                    ),
                )

                if bal_raw == 0 or exch_raw == 0:
                    return True, {
                        "cTokens_raw": 0,
                        "cTokens": 0.0,
                        "underlying_raw": 0,
                        "underlying": 0.0,
                        "bounds_raw": {"collateral_cTokens": 0, "cash_cTokens": 0},
                        "exchangeRate_raw": int(exch_raw),
                        "mToken_decimals": int(m_dec),
                        "underlying_decimals": None,
                    }

                u_dec = 18
                if self.token_client:
                    try:
                        u_key = f"{self.chain_name}_{u_addr}"
                        u_data = await self.token_client.get_token_details(u_key)
                        if u_data:
                            u_dec = u_data.get("decimals", 18)
                    except Exception:
                        pass

                # Binary search: largest cTokens you can redeem without shortfall
                lo, hi = 0, int(bal_raw)
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    (
                        err,
                        _liq,
                        short,
                    ) = await comptroller.functions.getHypotheticalAccountLiquidity(
                        account, mtoken, mid, 0
                    ).call(block_identifier="pending")
                    if err != 0:
                        return False, f"Comptroller error {err}"
                    if short == 0:
                        lo = mid
                    else:
                        hi = mid - 1

                c_by_collateral = lo

                # Pool cash bound (convert underlying cash -> cToken capacity)
                c_by_cash = (int(cash_raw) * MANTISSA) // int(exch_raw)

                redeem_c_raw = min(c_by_collateral, int(c_by_cash))

                # Final underlying you actually receive (mirror Solidity floor)
                under_raw = (redeem_c_raw * int(exch_raw)) // MANTISSA

                return True, {
                    "cTokens_raw": int(redeem_c_raw),
                    "cTokens": redeem_c_raw / (10 ** int(m_dec)),
                    "underlying_raw": int(under_raw),
                    "underlying": under_raw / (10 ** int(u_dec)),
                    "bounds_raw": {
                        "collateral_cTokens": int(c_by_collateral),
                        "cash_cTokens": int(c_by_cash),
                    },
                    "exchangeRate_raw": int(exch_raw),
                    "mToken_decimals": int(m_dec),
                    "underlying_decimals": int(u_dec),
                    "conversion_factor": redeem_c_raw / under_raw
                    if under_raw > 0
                    else 0,
                }
        except Exception as exc:
            return False, str(exc)

    async def wrap_eth(
        self,
        *,
        amount: int,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        tx = await self._encode_call(
            target=self.weth,
            abi=WETH_ABI,
            fn_name="deposit",
            args=[],
            from_address=strategy,
            value=amount,
        )
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return (True, txn_hash)

    async def _encode_call(
        self,
        *,
        target: str,
        abi: list[dict[str, Any]],
        fn_name: str,
        args: list[Any],
        from_address: str,
        value: int = 0,
    ) -> dict[str, Any]:
        async with web3_from_chain_id(self.chain_id) as web3:
            contract = web3.eth.contract(address=target, abi=abi)

            try:
                tx_data = await getattr(contract.functions, fn_name)(
                    *args
                ).build_transaction({"from": from_address})
                data = tx_data["data"]
            except ValueError as exc:
                raise ValueError(f"Failed to encode {fn_name}: {exc}") from exc

            tx: dict[str, Any] = {
                "chainId": int(self.chain_id),
                "from": to_checksum_address(from_address),
                "to": to_checksum_address(target),
                "data": data,
                "value": int(value),
            }
            return tx
