from typing import Any

from wayfinder_paths.adapters.ledger_adapter.adapter import LedgerAdapter
from wayfinder_paths.adapters.token_adapter.adapter import TokenAdapter
from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.utils.evm_helpers import resolve_chain_id
from wayfinder_paths.core.utils.tokens import build_send_transaction, get_token_balance
from wayfinder_paths.core.utils.transaction import send_transaction


class BalanceAdapter(BaseAdapter):
    adapter_type = "BALANCE"

    def __init__(
        self,
        config: dict[str, Any],
        main_wallet_signing_callback=None,
        strategy_wallet_signing_callback=None,
    ):
        super().__init__("balance", config)
        self.main_wallet_signing_callback = main_wallet_signing_callback
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback
        self.token_client = TokenClient()
        self.token_adapter = TokenAdapter()
        self.ledger_adapter = LedgerAdapter()

    async def get_balance(
        self,
        *,
        wallet_address: str,
        token_id: str | None = None,
        token_address: str | None = None,
        chain_id: int | None = None,
    ) -> tuple[bool, int | str]:
        try:
            if token_id and not token_address:
                token_info = await self.token_client.get_token_details(token_id)
                token_address = token_info["address"]
                chain_id = chain_id or resolve_chain_id(token_info)
            balance = await get_token_balance(token_address, chain_id, wallet_address)
            return True, balance
        except Exception as e:
            return False, str(e)

    async def move_from_main_wallet_to_strategy_wallet(
        self,
        token_id: str,
        amount: float,
        strategy_name: str = "unknown",
        skip_ledger: bool = False,
    ) -> tuple[bool, str]:
        return await self._move_between_wallets(
            token_id=token_id,
            amount=amount,
            from_wallet=self.config["main_wallet"],
            to_wallet=self.config["strategy_wallet"],
            ledger_method=self.ledger_adapter.record_deposit
            if not skip_ledger
            else None,
            ledger_wallet="to",
            strategy_name=strategy_name,
        )

    async def move_from_strategy_wallet_to_main_wallet(
        self,
        token_id: str,
        amount: float,
        strategy_name: str = "unknown",
        skip_ledger: bool = False,
    ) -> tuple[bool, str]:
        return await self._move_between_wallets(
            token_id=token_id,
            amount=amount,
            from_wallet=self.config["strategy_wallet"],
            to_wallet=self.config["main_wallet"],
            ledger_method=self.ledger_adapter.record_withdrawal
            if not skip_ledger
            else None,
            ledger_wallet="from",
            strategy_name=strategy_name,
        )

    async def send_to_address(
        self,
        token_id: str,
        amount: int,
        from_wallet: dict[str, Any],
        to_address: str,
        signing_callback,
    ) -> tuple[bool, str]:
        token_info = await self.token_client.get_token_details(token_id)
        chain_id = resolve_chain_id(token_info)
        tx = await build_send_transaction(
            from_address=from_wallet["address"],
            to_address=to_address,
            token_address=token_info["address"],
            chain_id=chain_id,
            amount=amount,
        )
        tx_hash = await send_transaction(tx, signing_callback)
        return True, tx_hash

    async def _move_between_wallets(
        self,
        *,
        token_id: str,
        amount: float,
        from_wallet: dict[str, Any],
        to_wallet: dict[str, Any],
        ledger_method,
        ledger_wallet: str,
        strategy_name: str,
    ) -> tuple[bool, str]:
        token_info = await self.token_client.get_token_details(token_id)
        chain_id = resolve_chain_id(token_info)
        decimals = token_info.get("decimals", 18)
        raw_amount = int(amount * (10**decimals))

        transaction = await build_send_transaction(
            from_address=from_wallet["address"],
            to_address=to_wallet["address"],
            token_address=token_info["address"],
            chain_id=chain_id,
            amount=raw_amount,
        )

        main_address = self.config.get("main_wallet", {}).get("address", "").lower()
        callback = (
            self.main_wallet_signing_callback
            if from_wallet["address"].lower() == main_address
            else self.strategy_wallet_signing_callback
        )
        tx_hash = await send_transaction(transaction, callback)

        if ledger_method:
            wallet_for_ledger = (
                from_wallet["address"]
                if ledger_wallet == "from"
                else to_wallet["address"]
            )
            await self._record_ledger_entry(
                ledger_method, wallet_for_ledger, token_info, amount, strategy_name
            )

        return True, tx_hash

    async def _record_ledger_entry(
        self,
        ledger_method,
        wallet_address: str,
        token_info: dict[str, Any],
        amount: float,
        strategy_name: str,
    ) -> None:
        try:
            chain_id = resolve_chain_id(token_info)
            token_id = token_info.get("token_id")
            usd_value = (
                await self.token_adapter.get_amount_usd(
                    token_info.get("token_id"), amount, decimals=0
                )
                or 0.0
            )
            await ledger_method(
                wallet_address=wallet_address,
                chain_id=chain_id,
                token_address=token_info.get("address"),
                token_amount=str(amount),
                usd_value=usd_value,
                data={
                    "token_id": token_id,
                    "amount": str(amount),
                    "usd_value": usd_value,
                },
                strategy_name=strategy_name,
            )
        except Exception as exc:
            self.logger.warning(f"Ledger entry failed: {exc}", wallet=wallet_address)
