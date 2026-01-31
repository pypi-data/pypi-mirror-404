from __future__ import annotations

import traceback
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from loguru import logger

from wayfinder_paths.core.clients.TokenClient import TokenDetails
from wayfinder_paths.core.strategies.descriptors import StratDescriptor


class StatusDict(TypedDict):
    portfolio_value: float
    net_deposit: float
    strategy_status: Any
    gas_available: float
    gassed_up: bool


StatusTuple = tuple[bool, str]


class WalletConfig(TypedDict, total=False):
    address: str
    private_key: str | None
    private_key_hex: str | None
    wallet_type: str | None


class StrategyConfig(TypedDict, total=False):
    main_wallet: WalletConfig | None
    strategy_wallet: WalletConfig | None
    wallet_type: str | None


class LiquidationResult(TypedDict):
    usd_value: float
    token: TokenDetails
    amt: int


class Strategy(ABC):
    name: str | None = None
    INFO: StratDescriptor | None = None

    def __init__(
        self,
        config: StrategyConfig | dict[str, Any] | None = None,
        *,
        main_wallet: WalletConfig | dict[str, Any] | None = None,
        strategy_wallet: WalletConfig | dict[str, Any] | None = None,
        api_key: str | None = None,
        main_wallet_signing_callback: Callable[[dict], Awaitable[str]] | None = None,
        strategy_wallet_signing_callback: Callable[[dict], Awaitable[str]]
        | None = None,
    ):
        self.adapters = {}
        self.ledger_adapter = None
        self.logger = logger.bind(strategy=self.__class__.__name__)
        self.config = config
        self.main_wallet_signing_callback = main_wallet_signing_callback
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback

    async def setup(self) -> None:
        pass

    async def log(self, msg: str) -> None:
        self.logger.info(msg)

    async def quote(self) -> None:
        pass

    def _get_strategy_wallet_address(self) -> str:
        strategy_wallet = self.config.get("strategy_wallet")
        if not strategy_wallet or not isinstance(strategy_wallet, dict):
            raise ValueError("strategy_wallet not configured in strategy config")
        address = strategy_wallet.get("address")
        if not address:
            raise ValueError("strategy_wallet address not found in config")
        return str(address)

    def _get_main_wallet_address(self) -> str:
        main_wallet = self.config.get("main_wallet")
        if not main_wallet or not isinstance(main_wallet, dict):
            raise ValueError("main_wallet not configured in strategy config")
        address = main_wallet.get("address")
        if not address:
            raise ValueError("main_wallet address not found in config")
        return str(address)

    @abstractmethod
    async def deposit(self, **kwargs) -> StatusTuple:
        pass

    async def withdraw(self, **kwargs) -> StatusTuple:
        return (True, "Withdrawal complete")

    @abstractmethod
    async def update(self) -> StatusTuple:
        pass

    @abstractmethod
    async def exit(self, **kwargs) -> StatusTuple:
        pass

    @staticmethod
    async def policies() -> list[str]:
        raise NotImplementedError

    @abstractmethod
    async def _status(self) -> StatusDict:
        pass

    async def status(self) -> StatusDict:
        status = await self._status()
        await self.ledger_adapter.record_strategy_snapshot(
            wallet_address=self._get_strategy_wallet_address(),
            strategy_status=status,
        )

        return status

    def register_adapters(self, adapters: list[Any]) -> None:
        self.adapters = {}
        for adapter in adapters:
            if hasattr(adapter, "adapter_type"):
                self.adapters[adapter.adapter_type] = adapter
            elif hasattr(adapter, "__class__"):
                self.adapters[adapter.__class__.__name__] = adapter

    def unwind_on_error(
        self, func: Callable[..., Awaitable[StatusTuple]]
    ) -> Callable[..., Awaitable[StatusTuple]]:
        async def wrapper(*args: Any, **kwargs: Any) -> StatusTuple:
            try:
                return await func(*args, **kwargs)
            except Exception:
                trace = traceback.format_exc()
                try:
                    await self.withdraw()
                    return (
                        False,
                        f"Strategy failed during operation and was unwound. Failure: {trace}",
                    )
                except Exception:
                    trace2 = traceback.format_exc()
                    return (
                        False,
                        f"Strategy failed and unwinding also failed. Operation error: {trace}. Unwind error: {trace2}",
                    )
            finally:
                if hasattr(self, "ledger_adapter") and self.ledger_adapter:
                    await self.ledger_adapter.save()

        return wrapper

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "name": getattr(cls, "name", None),
            "description": getattr(cls, "description", None),
            "summary": getattr(cls, "summary", None),
        }

    async def health_check(self) -> dict[str, Any]:
        health = {"status": "healthy", "strategy": self.name, "adapters": {}}

        for name, adapter in self.adapters.items():
            if hasattr(adapter, "health_check"):
                health["adapters"][name] = await adapter.health_check()
            else:
                health["adapters"][name] = {"status": "unknown"}

        return health

    async def partial_liquidate(
        self, usd_value: float
    ) -> tuple[bool, LiquidationResult]:
        if usd_value <= 0:
            raise ValueError(f"usd_value must be positive, got {usd_value}")
        return (False, "Partial liquidation not implemented for this strategy")
