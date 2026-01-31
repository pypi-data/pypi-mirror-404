from __future__ import annotations

from typing import Any

from eth_utils import to_checksum_address

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.HyperlendClient import (
    AssetsView,
    HyperlendClient,
    LendRateHistory,
    MarketEntry,
    StableMarketsHeadroomResponse,
)
from wayfinder_paths.core.constants.contracts import (
    HYPEREVM_WHYPE,
    HYPERLEND_POOL,
    HYPERLEND_WRAPPED_TOKEN_GATEWAY,
)
from wayfinder_paths.core.constants.hyperlend_abi import (
    POOL_ABI,
    WRAPPED_TOKEN_GATEWAY_ABI,
)
from wayfinder_paths.core.utils.tokens import ensure_allowance
from wayfinder_paths.core.utils.transaction import send_transaction
from wayfinder_paths.core.utils.web3 import web3_from_chain_id


class HyperlendAdapter(BaseAdapter):
    adapter_type = "HYPERLEND"

    def __init__(
        self,
        config: dict[str, Any],
        strategy_wallet_signing_callback=None,
    ) -> None:
        super().__init__("hyperlend_adapter", config)
        config = config or {}
        adapter_cfg = config.get("hyperlend_adapter") or {}

        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback
        self.hyperlend_client = HyperlendClient()

        strategy_wallet = config.get("strategy_wallet") or {}
        strategy_addr = strategy_wallet.get("address")
        if not strategy_addr:
            raise ValueError("strategy_wallet.address is required")
        self.strategy_wallet_address = to_checksum_address(strategy_addr)
        self.pool_address = to_checksum_address(
            adapter_cfg.get("pool_address") or HYPERLEND_POOL
        )
        self.gateway_address = to_checksum_address(
            adapter_cfg.get("wrapped_token_gateway") or HYPERLEND_WRAPPED_TOKEN_GATEWAY
        )
        self.wrapped_native = to_checksum_address(
            adapter_cfg.get("wrapped_native_underlying") or HYPEREVM_WHYPE
        )
        self.gateway_deposit_takes_pool = adapter_cfg.get(
            "gateway_deposit_takes_pool", True
        )

    async def get_stable_markets(
        self,
        *,
        required_underlying_tokens: float | None = None,
        buffer_bps: int | None = None,
        min_buffer_tokens: float | None = None,
    ) -> tuple[bool, StableMarketsHeadroomResponse | str]:
        try:
            data = await self.hyperlend_client.get_stable_markets(
                required_underlying_tokens=required_underlying_tokens,
                buffer_bps=buffer_bps,
                min_buffer_tokens=min_buffer_tokens,
            )
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def get_assets_view(
        self,
        *,
        user_address: str,
    ) -> tuple[bool, AssetsView | str]:
        try:
            data = await self.hyperlend_client.get_assets_view(
                user_address=user_address
            )
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def get_market_entry(
        self,
        *,
        token: str,
    ) -> tuple[bool, MarketEntry | str]:
        try:
            data = await self.hyperlend_client.get_market_entry(token=token)
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def get_lend_rate_history(
        self,
        *,
        token: str,
        lookback_hours: int,
        force_refresh: bool | None = None,
    ) -> tuple[bool, LendRateHistory | str]:
        try:
            data = await self.hyperlend_client.get_lend_rate_history(
                token=token,
                lookback_hours=lookback_hours,
                force_refresh=force_refresh,
            )
            return True, data
        except Exception as exc:
            return False, str(exc)

    async def lend(
        self,
        *,
        underlying_token: str,
        qty: int,
        chain_id: int,
        native: bool = False,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        qty = int(qty)
        if qty <= 0:
            return False, "qty must be positive"
        chain_id = int(chain_id)

        if native:
            transcation = await self._encode_call(
                target=self.gateway_address,
                abi=WRAPPED_TOKEN_GATEWAY_ABI,
                fn_name="depositETH",
                args=[self._gateway_first_arg(underlying_token), strategy, 0],
                from_address=strategy,
                chain_id=chain_id,
                value=qty,
            )
        else:
            token_addr = to_checksum_address(underlying_token)
            approved = await ensure_allowance(
                token_address=token_addr,
                owner=strategy,
                spender=self.pool_address,
                amount=qty,
                chain_id=chain_id,
                signing_callback=self.strategy_wallet_signing_callback,
            )
            if not approved[0]:
                return approved
            transcation = await self._encode_call(
                target=self.pool_address,
                abi=POOL_ABI,
                fn_name="supply",
                args=[token_addr, qty, strategy, 0],
                from_address=strategy,
                chain_id=chain_id,
            )
        txn_hash = await send_transaction(
            transcation, self.strategy_wallet_signing_callback
        )
        return True, txn_hash

    async def unlend(
        self,
        *,
        underlying_token: str,
        qty: int,
        chain_id: int,
        native: bool = False,
    ) -> tuple[bool, Any]:
        strategy = self.strategy_wallet_address
        qty = int(qty)
        if qty <= 0:
            return False, "qty must be positive"
        chain_id = int(chain_id)

        if native:
            transaction = await self._encode_call(
                target=self.gateway_address,
                abi=WRAPPED_TOKEN_GATEWAY_ABI,
                fn_name="withdrawETH",
                args=[self._gateway_first_arg(underlying_token), qty, strategy],
                from_address=strategy,
                chain_id=chain_id,
            )
        else:
            token_addr = to_checksum_address(underlying_token)
            transaction = await self._encode_call(
                target=self.pool_address,
                abi=POOL_ABI,
                fn_name="withdraw",
                args=[token_addr, qty, strategy],
                from_address=strategy,
                chain_id=chain_id,
            )
        txn_hash = await send_transaction(
            transaction, self.strategy_wallet_signing_callback
        )
        return True, txn_hash

    async def _encode_call(
        self,
        *,
        target: str,
        abi: list[dict[str, Any]],
        fn_name: str,
        args: list[Any],
        from_address: str,
        chain_id: int,
        value: int = 0,
    ) -> dict[str, Any]:
        async with web3_from_chain_id(chain_id) as web3:
            contract = web3.eth.contract(address=target, abi=abi)
            try:
                data = (
                    await getattr(contract.functions, fn_name)(*args).build_transaction(
                        {"from": from_address}
                    )
                )["data"]
            except ValueError as exc:
                raise ValueError(f"Failed to encode {fn_name}: {exc}") from exc

            transaction: dict[str, Any] = {
                "chainId": int(chain_id),
                "from": to_checksum_address(from_address),
                "to": to_checksum_address(target),
                "data": data,
                "value": int(value),
            }
            return transaction

    def _gateway_first_arg(self, underlying_token: str) -> str:
        if self.gateway_deposit_takes_pool:
            return self.pool_address
        return to_checksum_address(underlying_token)
