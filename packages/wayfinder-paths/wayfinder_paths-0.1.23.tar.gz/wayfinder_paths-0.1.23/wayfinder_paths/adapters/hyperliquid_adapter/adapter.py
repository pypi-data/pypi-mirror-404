from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.constants.contracts import (
    ARBITRUM_USDC,
    HYPERLIQUID_BRIDGE,
)

if TYPE_CHECKING:
    from wayfinder_paths.core.clients.protocols import (
        HyperliquidExecutorProtocol as HyperliquidExecutor,
    )

HYPERLIQUID_BRIDGE_ADDRESS = HYPERLIQUID_BRIDGE
ARBITRUM_USDC_ADDRESS = ARBITRUM_USDC

try:
    from hyperliquid.info import Info
    from hyperliquid.utils import constants

    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    Info = None
    constants = None


class SimpleCache:
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            if time.time() < self._expiry.get(key, 0):
                return self._cache[key]
            del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
        return None

    def set(self, key: str, value: Any, timeout: int = 300) -> None:
        self._cache[key] = value
        self._expiry[key] = time.time() + timeout

    def clear(self) -> None:
        self._cache.clear()
        self._expiry.clear()


class HyperliquidAdapter(BaseAdapter):
    adapter_type = "HYPERLIQUID"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        executor: HyperliquidExecutor | None = None,
    ) -> None:
        super().__init__("hyperliquid_adapter", config)

        if not HYPERLIQUID_AVAILABLE:
            raise ImportError(
                "hyperliquid package not installed. "
                "Install with: poetry add hyperliquid"
            )

        self._cache = SimpleCache()
        self._executor = executor

        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)

        # Cache asset mappings after first fetch
        self._asset_to_sz_decimals: dict[int, int] | None = None
        self._coin_to_asset: dict[str, int] | None = None

    async def connect(self) -> bool:
        try:
            meta = self.info.meta_and_asset_ctxs()
            if meta:
                self.logger.debug("HyperliquidAdapter connected successfully")
                return True
            return False
        except Exception as exc:
            self.logger.error(f"HyperliquidAdapter connection failed: {exc}")
            return False

    # ------------------------------------------------------------------ #
    # Market Data - Read Operations                                       #
    # ------------------------------------------------------------------ #

    async def get_meta_and_asset_ctxs(self) -> tuple[bool, Any]:
        cache_key = "hl_meta_and_asset_ctxs"
        cached = self._cache.get(cache_key)
        if cached:
            return True, cached

        try:
            data = self.info.meta_and_asset_ctxs()
            self._cache.set(cache_key, data, timeout=60)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch meta_and_asset_ctxs: {exc}")
            return False, str(exc)

    async def get_spot_meta(self) -> tuple[bool, Any]:
        cache_key = "hl_spot_meta"
        cached = self._cache.get(cache_key)
        if cached:
            return True, cached

        try:
            spot_meta = self.info.spot_meta
            if callable(spot_meta):
                data = spot_meta()
            else:
                data = spot_meta
            self._cache.set(cache_key, data, timeout=60)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch spot_meta: {exc}")
            return False, str(exc)

    async def get_spot_assets(self) -> tuple[bool, dict[str, int]]:
        cache_key = "hl_spot_assets"
        cached = self._cache.get(cache_key)
        if cached:
            return True, cached

        try:
            success, spot_meta = await self.get_spot_meta()
            if not success:
                return False, {}

            response = {}
            tokens = spot_meta.get("tokens", [])
            universe = spot_meta.get("universe", [])

            for pair in universe:
                pair_tokens = pair.get("tokens", [])
                if len(pair_tokens) < 2:
                    continue

                base_idx, quote_idx = pair_tokens[0], pair_tokens[1]

                base_info = tokens[base_idx] if base_idx < len(tokens) else {}
                quote_info = tokens[quote_idx] if quote_idx < len(tokens) else {}

                base_name = base_info.get("name", f"TOKEN{base_idx}")
                quote_name = quote_info.get("name", f"TOKEN{quote_idx}")

                name = f"{base_name}/{quote_name}"
                spot_asset_id = pair.get("index", 0) + 10000
                response[name] = spot_asset_id

            self._cache.set(cache_key, response, timeout=300)
            return True, response

        except Exception as exc:
            self.logger.error(f"Failed to get spot assets: {exc}")
            return False, {}

    def get_spot_asset_id(self, base_coin: str, quote_coin: str = "USDC") -> int | None:
        cache_key = "hl_spot_assets"
        cached = self._cache.get(cache_key)
        if cached:
            pair_name = f"{base_coin}/{quote_coin}"
            return cached.get(pair_name)
        return None

    async def get_funding_history(
        self,
        coin: str,
        start_time_ms: int,
        end_time_ms: int | None = None,
    ) -> tuple[bool, list[dict[str, Any]]]:
        try:
            data = self.info.funding_history(coin, start_time_ms, end_time_ms)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch funding_history for {coin}: {exc}")
            return False, str(exc)

    async def get_candles(
        self,
        coin: str,
        interval: str,
        start_time_ms: int,
        end_time_ms: int | None = None,
    ) -> tuple[bool, list[dict[str, Any]]]:
        try:
            data = self.info.candles_snapshot(
                coin, interval, start_time_ms, end_time_ms
            )
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch candles for {coin}: {exc}")
            return False, str(exc)

    async def get_l2_book(
        self,
        coin: str,
        n_levels: int = 20,
    ) -> tuple[bool, dict[str, Any]]:
        try:
            data = self.info.l2_snapshot(coin)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch L2 book for {coin}: {exc}")
            return False, str(exc)

    async def get_user_state(self, address: str) -> tuple[bool, dict[str, Any]]:
        try:
            data = self.info.user_state(address)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch user_state for {address}: {exc}")
            return False, str(exc)

    async def get_spot_user_state(self, address: str) -> tuple[bool, dict[str, Any]]:
        try:
            data = self.info.spot_user_state(address)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch spot_user_state for {address}: {exc}")
            return False, str(exc)

    async def get_margin_table(self, margin_table_id: int) -> tuple[bool, list[dict]]:
        cache_key = f"hl_margin_table_{margin_table_id}"
        cached = self._cache.get(cache_key)
        if cached:
            return True, cached

        try:
            # Hyperliquid expects `id` for margin tables in the /info API.
            # Keep a fallback to `marginTableId` for compatibility with older SDKs.
            body = {"type": "marginTable", "id": int(margin_table_id)}
            try:
                data = self.info.post("/info", body)
            except Exception:  # noqa: BLE001 - try alternate payload key
                body = {"type": "marginTable", "marginTableId": int(margin_table_id)}
                data = self.info.post("/info", body)
            self._cache.set(cache_key, data, timeout=86400)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch margin_table {margin_table_id}: {exc}")
            return False, str(exc)

    async def get_spot_l2_book(self, spot_asset_id: int) -> tuple[bool, dict[str, Any]]:
        try:
            # Spot L2 uses different coin names based on spot index:
            # - Index 0 (PURR): use "PURR/USDC"
            # - All other indices: use "@{index}"
            spot_index = (
                spot_asset_id - 10000 if spot_asset_id >= 10000 else spot_asset_id
            )

            if spot_index == 0:
                coin = "PURR/USDC"
            else:
                coin = f"@{spot_index}"

            body = {"type": "l2Book", "coin": coin}
            data = self.info.post("/info", body)
            return True, data
        except Exception as exc:
            self.logger.error(
                f"Failed to fetch spot L2 book for {spot_asset_id}: {exc}"
            )
            return False, str(exc)

    # ------------------------------------------------------------------ #
    # Asset Mappings                                                      #
    # ------------------------------------------------------------------ #

    @property
    def asset_to_sz_decimals(self) -> dict[int, int]:
        if self._asset_to_sz_decimals is None:
            self._asset_to_sz_decimals = dict(self.info.asset_to_sz_decimals)
        return self._asset_to_sz_decimals

    @property
    def coin_to_asset(self) -> dict[str, int]:
        if self._coin_to_asset is None:
            self._coin_to_asset = dict(self.info.coin_to_asset)
        return self._coin_to_asset

    def get_sz_decimals(self, asset_id: int) -> int:
        try:
            return self.asset_to_sz_decimals[asset_id]
        except KeyError:
            raise ValueError(
                f"Unknown asset_id {asset_id}: missing szDecimals"
            ) from None

    def refresh_mappings(self) -> None:
        self._asset_to_sz_decimals = None
        self._coin_to_asset = None
        self._cache.clear()

    # ------------------------------------------------------------------ #
    # Utility Methods                                                      #
    # ------------------------------------------------------------------ #

    async def get_all_mid_prices(self) -> tuple[bool, dict[str, float]]:
        try:
            data = self.info.all_mids()
            return True, {k: float(v) for k, v in data.items()}
        except Exception as exc:
            self.logger.error(f"Failed to fetch mid prices: {exc}")
            return False, str(exc)

    def get_valid_order_size(self, asset_id: int, size: float) -> float:
        decimals = self.get_sz_decimals(asset_id)
        from decimal import ROUND_DOWN, Decimal

        step = Decimal(10) ** (-decimals)
        if size <= 0:
            return 0.0
        quantized = (Decimal(str(size)) / step).to_integral_value(
            rounding=ROUND_DOWN
        ) * step
        return float(quantized)

    # ------------------------------------------------------------------ #
    # Execution Methods (require signing callback)                         #
    # ------------------------------------------------------------------ #

    async def place_market_order(
        self,
        asset_id: int,
        is_buy: bool,
        slippage: float,
        size: float,
        address: str,
        *,
        reduce_only: bool = False,
        cloid: str | None = None,
        builder: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError(
                "No Hyperliquid executor configured. "
                "Inject a HyperliquidExecutor implementation (e.g., LocalHyperliquidExecutor)."
            )

        result = await self._executor.place_market_order(
            asset_id=asset_id,
            is_buy=is_buy,
            slippage=slippage,
            size=size,
            address=address,
            reduce_only=reduce_only,
            cloid=cloid,
            builder=builder,
        )

        success = result.get("status") == "ok"
        return success, result

    async def cancel_order(
        self,
        asset_id: int,
        order_id: int | str,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError(
                "No Hyperliquid executor configured. "
                "Inject a HyperliquidExecutor implementation (e.g., LocalHyperliquidExecutor)."
            )

        result = await self._executor.cancel_order(
            asset_id=asset_id,
            order_id=int(order_id) if isinstance(order_id, str) else order_id,
            address=address,
        )

        success = result.get("status") == "ok"
        return success, result

    async def update_leverage(
        self,
        asset_id: int,
        leverage: int,
        is_cross: bool,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.update_leverage(
            asset_id=asset_id,
            leverage=leverage,
            is_cross=is_cross,
            address=address,
        )

        success = result.get("status") == "ok"
        return success, result

    async def transfer_spot_to_perp(
        self,
        amount: float,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.transfer_spot_to_perp(
            amount=amount,
            address=address,
        )

        success = result.get("status") == "ok"
        return success, result

    async def transfer_perp_to_spot(
        self,
        amount: float,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.transfer_perp_to_spot(
            amount=amount,
            address=address,
        )

        success = result.get("status") == "ok"
        return success, result

    async def place_stop_loss(
        self,
        asset_id: int,
        is_buy: bool,
        trigger_price: float,
        size: float,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.place_stop_loss(
            asset_id=asset_id,
            is_buy=is_buy,
            trigger_price=trigger_price,
            size=size,
            address=address,
        )

        success = result.get("status") == "ok"
        return success, result

    async def get_user_fills(self, address: str) -> tuple[bool, list[dict[str, Any]]]:
        try:
            data = self.info.user_fills(address)
            return True, data if isinstance(data, list) else []
        except Exception as exc:
            self.logger.error(f"Failed to fetch user_fills for {address}: {exc}")
            return False, str(exc)

    async def get_order_status(
        self, address: str, order_id: int | str
    ) -> tuple[bool, dict[str, Any]]:
        try:
            body = {"type": "orderStatus", "user": address, "oid": order_id}
            data = self.info.post("/info", body)
            return True, data
        except Exception as exc:
            self.logger.error(f"Failed to fetch order_status for {order_id}: {exc}")
            return False, str(exc)

    async def get_open_orders(self, address: str) -> tuple[bool, list[dict[str, Any]]]:
        try:
            data = self.info.open_orders(address)
            return True, data if isinstance(data, list) else []
        except Exception as exc:
            self.logger.error(f"Failed to fetch open_orders for {address}: {exc}")
            return False, str(exc)

    async def get_frontend_open_orders(
        self, address: str
    ) -> tuple[bool, list[dict[str, Any]]]:
        try:
            data = self.info.frontend_open_orders(address)
            return True, data if isinstance(data, list) else []
        except Exception as exc:
            self.logger.error(
                f"Failed to fetch frontend_open_orders for {address}: {exc}"
            )
            return False, str(exc)

    async def withdraw(
        self,
        *,
        amount: float,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.withdraw(
            amount=amount,
            address=address,
        )
        success = result.get("status") == "ok"
        return success, result

    # ------------------------------------------------------------------ #
    # Health Check                                                        #
    # ------------------------------------------------------------------ #

    async def health_check(self) -> dict[str, Any]:
        try:
            success, meta = await self.get_meta_and_asset_ctxs()
            if success and meta:
                return {
                    "status": "healthy",
                    "perp_markets": len(meta[0].get("universe", [])) if meta else 0,
                }
            return {"status": "unhealthy", "error": "Failed to fetch metadata"}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Deposit/Withdrawal Helpers                                          #
    # ------------------------------------------------------------------ #

    def get_perp_margin_amount(self, user_state: dict[str, Any]) -> float:
        try:
            margin_summary = user_state.get("marginSummary", {})
            account_value = margin_summary.get("accountValue")
            if account_value is not None:
                return float(account_value)
            # Fallback to crossMarginSummary
            cross_summary = user_state.get("crossMarginSummary", {})
            return float(cross_summary.get("accountValue", 0.0))
        except (TypeError, ValueError):
            return 0.0

    async def get_max_builder_fee(
        self,
        user: str,
        builder: str,
    ) -> tuple[bool, int]:
        try:
            body = {"type": "maxBuilderFee", "user": user, "builder": builder}
            data = self.info.post("/info", body)
            # Response is just an integer (tenths of basis points)
            return True, int(data) if data is not None else 0
        except Exception as exc:
            self.logger.error(f"Failed to fetch max_builder_fee for {user}: {exc}")
            return False, 0

    async def approve_builder_fee(
        self,
        builder: str,
        max_fee_rate: str,
        address: str,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.approve_builder_fee(
            builder=builder,
            max_fee_rate=max_fee_rate,
            address=address,
        )

        success = result.get("status") == "ok"
        return success, result

    async def place_limit_order(
        self,
        asset_id: int,
        is_buy: bool,
        price: float,
        size: float,
        address: str,
        *,
        reduce_only: bool = False,
        builder: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        if not self._executor:
            raise NotImplementedError("No Hyperliquid executor configured.")

        result = await self._executor.place_limit_order(
            asset_id=asset_id,
            is_buy=is_buy,
            price=price,
            size=size,
            address=address,
            reduce_only=reduce_only,
            builder=builder,
        )

        success = result.get("status") == "ok"
        return success, result

    async def wait_for_deposit(
        self,
        address: str,
        expected_increase: float,
        *,
        timeout_s: int = 120,
        poll_interval_s: int = 5,
    ) -> tuple[bool, float]:
        iterations = timeout_s // poll_interval_s

        success, initial_state = await self.get_user_state(address)
        if not success:
            self.logger.warning(f"Could not fetch initial state: {initial_state}")
            initial_balance = 0.0
        else:
            initial_balance = self.get_perp_margin_amount(initial_state)

        self.logger.info(
            f"Waiting for Hyperliquid deposit. Initial balance: ${initial_balance:.2f}, "
            f"expecting +${expected_increase:.2f}"
        )

        for i in range(iterations):
            await asyncio.sleep(poll_interval_s)

            success, state = await self.get_user_state(address)
            if not success:
                continue

            current_balance = self.get_perp_margin_amount(state)

            # Allow 5% tolerance for fees/slippage
            if current_balance >= initial_balance + expected_increase * 0.95:
                self.logger.info(
                    f"Hyperliquid deposit confirmed: ${current_balance - initial_balance:.2f} "
                    f"(expected ${expected_increase:.2f})"
                )
                return True, current_balance

            remaining_s = (iterations - i - 1) * poll_interval_s
            self.logger.debug(
                f"Waiting for deposit... current=${current_balance:.2f}, "
                f"need=${initial_balance + expected_increase:.2f}, {remaining_s}s remaining"
            )

        self.logger.warning(
            f"Hyperliquid deposit not confirmed after {timeout_s}s. "
            f"Deposits typically take 1-2 minutes."
        )
        success, state = await self.get_user_state(address)
        final_balance = (
            self.get_perp_margin_amount(state) if success else initial_balance
        )
        return False, final_balance

    async def get_user_withdrawals(
        self,
        address: str,
        from_timestamp_ms: int,
    ) -> tuple[bool, dict[str, float]]:
        try:
            from eth_utils import to_checksum_address

            data = self.info.post(
                "/info",
                {
                    "type": "userNonFundingLedgerUpdates",
                    "user": to_checksum_address(address),
                    "startTime": int(from_timestamp_ms),
                },
            )

            result = {}
            # Sort earliest to latest
            for update in sorted(data or [], key=lambda x: x.get("time", 0)):
                delta = update.get("delta") or {}
                if delta.get("type") == "withdraw":
                    tx_hash = update.get("hash")
                    usdc_amount = float(delta.get("usdc", 0))
                    if tx_hash:
                        result[tx_hash] = usdc_amount

            return True, result

        except Exception as exc:
            self.logger.error(f"Failed to get user withdrawals: {exc}")
            return False, {}

    async def wait_for_withdrawal(
        self,
        address: str,
        *,
        lookback_s: int = 5,
        max_poll_time_s: int = 30 * 60,
        poll_interval_s: int = 5,
    ) -> tuple[bool, dict[str, float]]:
        import time

        start_time_ms = time.time() * 1000
        iterations = int(max_poll_time_s / poll_interval_s) + 1

        for i in range(iterations, 0, -1):
            # Check for withdrawals since just before we started
            check_from_ms = start_time_ms - (lookback_s * 1000)
            success, withdrawals = await self.get_user_withdrawals(
                address, int(check_from_ms)
            )

            if success and withdrawals:
                self.logger.info(
                    f"Found {len(withdrawals)} withdrawal(s): {withdrawals}"
                )
                return True, withdrawals

            remaining_s = i * poll_interval_s
            self.logger.info(
                f"Waiting for withdrawal to appear on-chain... "
                f"{remaining_s}s remaining (withdrawals often take 10+ minutes)"
            )
            await asyncio.sleep(poll_interval_s)

        self.logger.warning(
            f"No withdrawal detected after {max_poll_time_s}s. "
            "The withdrawal may still be processing."
        )
        return False, {}
