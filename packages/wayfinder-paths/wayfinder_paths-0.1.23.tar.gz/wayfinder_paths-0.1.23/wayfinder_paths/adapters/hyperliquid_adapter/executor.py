from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from loguru import logger

from wayfinder_paths.core.clients.protocols import HyperliquidExecutorProtocol

# Re-export for backwards compatibility with existing imports.
HyperliquidExecutor = HyperliquidExecutorProtocol

try:
    from eth_account import Account
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
    from hyperliquid.utils.types import BuilderInfo, Cloid

    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    Account = None
    Exchange = None
    Info = None
    constants = None
    Cloid = None
    BuilderInfo = None


def _new_client_id() -> Cloid:
    cloid_str = "0x" + uuid.uuid4().hex
    return Cloid(cloid_str)


class LocalHyperliquidExecutor:
    def __init__(
        self,
        *,
        config: dict[str, Any],
        network: str = "mainnet",
    ) -> None:
        if not HYPERLIQUID_AVAILABLE:
            raise ImportError(
                "hyperliquid package not installed. Install with: poetry add hyperliquid"
            )

        self.config = config
        self.network = network

        # Resolve private key from config
        self._private_key = self._resolve_private_key(config)
        if not self._private_key:
            raise ValueError(
                "No private key found in config. "
                "Provide strategy_wallet.private_key_hex or strategy_wallet.private_key"
            )

        pk = self._private_key
        if not pk.startswith("0x"):
            pk = "0x" + pk
        self._wallet = Account.from_key(pk)

        base_url = (
            constants.MAINNET_API_URL
            if network == "mainnet"
            else constants.TESTNET_API_URL
        )
        self.info = Info(base_url, skip_ws=True)
        self.exchange = Exchange(self._wallet, base_url)
        self._asset_id_to_coin: dict[int, str] | None = None

        logger.info(
            f"LocalHyperliquidExecutor initialized for address: {self._wallet.address}"
        )

    def _get_perp_coin(self, asset_id: int) -> str | None:
        if self._asset_id_to_coin is None:
            mapping: dict[int, str] = {}

            asset_to_coin = getattr(self.info, "asset_to_coin", None)
            if isinstance(asset_to_coin, Mapping):
                for k, v in asset_to_coin.items():
                    try:
                        asset_int = int(k)
                    except (TypeError, ValueError):
                        continue
                    if v:
                        mapping[asset_int] = str(v)

            coin_to_asset = getattr(self.info, "coin_to_asset", None)
            try:
                coin_to_asset_dict = dict(coin_to_asset) if coin_to_asset else {}
            except Exception:  # noqa: BLE001
                coin_to_asset_dict = {}
            for coin, aid in coin_to_asset_dict.items():
                try:
                    asset_int = int(aid)
                except (TypeError, ValueError):
                    continue
                if coin and asset_int not in mapping:
                    mapping[asset_int] = str(coin)

            self._asset_id_to_coin = mapping

        return self._asset_id_to_coin.get(asset_id) if self._asset_id_to_coin else None

    def _resolve_private_key(self, config: dict[str, Any]) -> str | None:
        # Try strategy_wallet first
        strategy_wallet = config.get("strategy_wallet", {})
        if isinstance(strategy_wallet, dict):
            pk = strategy_wallet.get("private_key_hex") or strategy_wallet.get(
                "private_key"
            )
            if pk:
                return pk

        # Try main_wallet as fallback (for single-wallet setups)
        main_wallet = config.get("main_wallet", {})
        if isinstance(main_wallet, dict):
            pk = main_wallet.get("private_key_hex") or main_wallet.get("private_key")
            if pk:
                return pk

        return None

    @property
    def address(self) -> str:
        return self._wallet.address

    async def place_market_order(
        self,
        *,
        asset_id: int,
        is_buy: bool,
        slippage: float,
        size: float,
        address: str,
        reduce_only: bool = False,
        cloid: Any = None,
        builder: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if cloid is None:
            cloid = _new_client_id()
        elif isinstance(cloid, str):
            cloid = Cloid(cloid)

        builder_info = None
        if builder:
            builder_info = BuilderInfo(b=builder.get("b", ""), f=builder.get("f", 0))

        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {
                    "type": "error",
                    "data": f"Address mismatch: expected {self._wallet.address}, got {address}",
                },
            }

        try:
            # For spot (asset_id >= 10000), use different method
            is_spot = asset_id >= 10000

            if is_spot:
                # Spot market order. Hyperliquid spot uses `@{spot_index}` where
                # spot_index == spot_asset_id - 10000.
                spot_index = asset_id - 10000
                result = self.exchange.market_open(
                    name=f"@{spot_index}",
                    is_buy=is_buy,
                    sz=size,
                    slippage=slippage,
                    cloid=cloid,
                    builder=builder_info,
                )
            else:
                # Perp market order
                coin = self._get_perp_coin(asset_id)
                if not coin:
                    return {
                        "status": "err",
                        "response": {
                            "type": "error",
                            "data": f"Unknown asset_id: {asset_id}",
                        },
                    }

                if reduce_only:
                    result = self.exchange.market_close(
                        coin=coin,
                        sz=size,
                        slippage=slippage,
                        cloid=cloid,
                        builder=builder_info,
                    )
                else:
                    result = self.exchange.market_open(
                        name=coin,
                        is_buy=is_buy,
                        sz=size,
                        slippage=slippage,
                        cloid=cloid,
                        builder=builder_info,
                    )

            logger.debug(f"Market order result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Market order failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def cancel_order(
        self,
        *,
        asset_id: int,
        order_id: int,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            # Resolve coin name
            is_spot = asset_id >= 10000
            if is_spot:
                spot_index = asset_id - 10000
                coin = f"@{spot_index}"
            else:
                coin = self._get_perp_coin(asset_id)
                if not coin:
                    return {
                        "status": "err",
                        "response": {
                            "type": "error",
                            "data": f"Unknown asset_id: {asset_id}",
                        },
                    }

            result = self.exchange.cancel(name=coin, oid=order_id)
            logger.debug(f"Cancel order result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Cancel order failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def update_leverage(
        self,
        *,
        asset_id: int,
        leverage: int,
        is_cross: bool,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            coin = self._get_perp_coin(asset_id)
            if not coin:
                return {
                    "status": "err",
                    "response": {
                        "type": "error",
                        "data": f"Unknown asset_id: {asset_id}",
                    },
                }

            result = self.exchange.update_leverage(
                leverage=leverage,
                name=coin,
                is_cross=is_cross,
            )
            logger.debug(f"Update leverage result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Update leverage failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def transfer_spot_to_perp(
        self,
        *,
        amount: float,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            result = self.exchange.usd_class_transfer(
                amount=amount,
                to_perp=True,
            )
            logger.debug(f"Spot to perp transfer result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Spot to perp transfer failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def transfer_perp_to_spot(
        self,
        *,
        amount: float,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            result = self.exchange.usd_class_transfer(
                amount=amount,
                to_perp=False,
            )
            logger.debug(f"Perp to spot transfer result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Perp to spot transfer failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def place_stop_loss(
        self,
        *,
        asset_id: int,
        is_buy: bool,
        trigger_price: float,
        size: float,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            coin = self._get_perp_coin(asset_id)
            if not coin:
                return {
                    "status": "err",
                    "response": {
                        "type": "error",
                        "data": f"Unknown asset_id: {asset_id}",
                    },
                }

            # Use the SDK's order method with trigger order type
            result = self.exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=trigger_price,
                order_type={
                    "trigger": {
                        "triggerPx": trigger_price,
                        "isMarket": True,
                        "tpsl": "sl",
                    }
                },
                reduce_only=True,
            )
            logger.debug(f"Stop loss result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Place stop loss failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def place_limit_order(
        self,
        *,
        asset_id: int,
        is_buy: bool,
        price: float,
        size: float,
        address: str,
        reduce_only: bool = False,
        builder: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            # Resolve coin name
            is_spot = asset_id >= 10000
            if is_spot:
                spot_index = asset_id - 10000
                coin = f"@{spot_index}"
            else:
                coin = self._get_perp_coin(asset_id)
                if not coin:
                    return {
                        "status": "err",
                        "response": {
                            "type": "error",
                            "data": f"Unknown asset_id: {asset_id}",
                        },
                    }

            builder_info = None
            if builder:
                builder_info = BuilderInfo(
                    b=builder.get("b", ""), f=builder.get("f", 0)
                )

            # Place limit order using SDK
            result = self.exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type={"limit": {"tif": "Gtc"}},
                reduce_only=reduce_only,
                builder=builder_info,
            )
            logger.debug(f"Limit order result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Place limit order failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def withdraw(
        self,
        *,
        amount: float,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            # Use withdraw_from_bridge to withdraw to the wallet's own address on Arbitrum
            result = self.exchange.withdraw_from_bridge(
                amount=amount,
                destination=address,
            )
            logger.debug(f"Withdraw result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Withdraw failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }

    async def approve_builder_fee(
        self,
        *,
        builder: str,
        max_fee_rate: str,
        address: str,
    ) -> dict[str, Any]:
        if address.lower() != self._wallet.address.lower():
            return {
                "status": "err",
                "response": {"type": "error", "data": "Address mismatch"},
            }

        try:
            result = self.exchange.approve_builder_fee(
                builder=builder,
                max_fee_rate=max_fee_rate,
            )
            logger.debug(f"Approve builder fee result: {result}")
            return result

        except Exception as exc:
            logger.error(f"Approve builder fee failed: {exc}")
            return {
                "status": "err",
                "response": {"type": "error", "data": str(exc)},
            }
