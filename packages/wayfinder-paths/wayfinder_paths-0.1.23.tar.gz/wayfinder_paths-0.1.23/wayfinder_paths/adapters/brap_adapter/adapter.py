from __future__ import annotations

from typing import Any

from web3 import Web3

from wayfinder_paths.adapters.ledger_adapter.adapter import LedgerAdapter
from wayfinder_paths.adapters.token_adapter.adapter import TokenAdapter
from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.adapters.models import SWAP
from wayfinder_paths.core.clients.BRAPClient import BRAPClient
from wayfinder_paths.core.clients.LedgerClient import TransactionRecord
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.constants.contracts import TOKENS_REQUIRING_APPROVAL_RESET
from wayfinder_paths.core.utils.tokens import (
    build_approve_transaction,
    get_token_allowance,
    is_native_token,
)
from wayfinder_paths.core.utils.transaction import send_transaction


class BRAPAdapter(BaseAdapter):
    adapter_type: str = "BRAP"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        strategy_wallet_signing_callback=None,
    ):
        super().__init__("brap_adapter", config)
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback
        self.brap_client = BRAPClient()
        self.token_client = TokenClient()
        self.token_adapter = TokenAdapter()
        self.ledger_adapter = LedgerAdapter()

    def _select_quote_by_provider(
        self,
        quotes: list[dict[str, Any]],
        preferred_providers: list[str],
    ) -> dict[str, Any] | None:
        preferred_lower = {p.lower() for p in preferred_providers}
        matching = [
            q for q in quotes if q.get("provider", "").lower() in preferred_lower
        ]
        if matching:
            return max(matching, key=lambda q: int(q.get("output_amount", 0) or 0))
        return None

    async def _handle_token_approval(
        self,
        *,
        chain_id: int,
        token_address: str,
        owner_address: str,
        spender_address: str,
        amount: int,
    ) -> None:
        token_checksum = Web3.to_checksum_address(token_address)
        owner_checksum = Web3.to_checksum_address(owner_address)
        spender_checksum = Web3.to_checksum_address(spender_address)

        if (chain_id, token_checksum.lower()) in TOKENS_REQUIRING_APPROVAL_RESET:
            allowance = await get_token_allowance(
                token_checksum,
                chain_id,
                owner_checksum,
                spender_checksum,
            )
            if allowance > 0:
                clear_tx = await build_approve_transaction(
                    from_address=owner_checksum,
                    chain_id=chain_id,
                    token_address=token_checksum,
                    spender_address=spender_checksum,
                    amount=0,
                )
                await send_transaction(clear_tx, self.strategy_wallet_signing_callback)

        approve_tx = await build_approve_transaction(
            from_address=owner_checksum,
            chain_id=chain_id,
            token_address=token_checksum,
            spender_address=spender_checksum,
            amount=int(amount),
        )
        await send_transaction(approve_tx, self.strategy_wallet_signing_callback)

    async def _record_swap_operation(
        self,
        from_token: dict[str, Any],
        to_token: dict[str, Any],
        wallet_address: str,
        quote: dict[str, Any],
        tx_hash: str,
        strategy_name: str | None = None,
    ) -> TransactionRecord | dict[str, Any]:
        from_amount_usd = quote.get("from_amount_usd", 0)
        to_amount_usd = quote.get("to_amount_usd", 0)
        if from_amount_usd is None:
            from_amount_usd = await self.token_adapter.get_amount_usd(
                from_token.get("token_id"),
                quote.get("input_amount"),
                from_token.get("decimals") or 18,
            )
        if to_amount_usd is None:
            to_amount_usd = await self.token_adapter.get_amount_usd(
                to_token.get("token_id"),
                quote.get("output_amount"),
                to_token.get("decimals") or 18,
            )

        operation_data = SWAP(
            adapter=self.adapter_type,
            from_token_id=str(from_token.get("id")),
            to_token_id=str(to_token.get("id")),
            from_amount=str(quote.get("input_amount")),
            to_amount=str(quote.get("output_amount")),
            from_amount_usd=from_amount_usd,
            to_amount_usd=to_amount_usd,
            transaction_hash=tx_hash,
            transaction_chain_id=from_token.get("chain_id")
            or (from_token.get("chain") or {}).get("id"),
            transaction_status=None,
            transaction_receipt=None,
        )

        try:
            success, ledger_response = await self.ledger_adapter.record_operation(
                wallet_address=wallet_address,
                operation_data=operation_data,
                usd_value=from_amount_usd or 0,
                strategy_name=strategy_name,
            )
            if success:
                return ledger_response
            self.logger.warning(
                "Ledger swap record failed", error=ledger_response, quote=quote
            )
        except Exception as exc:
            self.logger.warning(f"Ledger swap record raised: {exc}", quote=quote)

        return operation_data.model_dump(mode="json")

    async def best_quote(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        from_address: str,
        amount: str,
        preferred_providers: list[str] | None = None,
        retries: int = 1,
        slippage: float | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        last_error = "No quotes available"
        for attempt in range(retries):
            try:
                data = await self.brap_client.get_quote(
                    from_token=from_token_address,
                    to_token=to_token_address,
                    from_chain=from_chain_id,
                    to_chain=to_chain_id,
                    from_wallet=from_address,
                    from_amount=amount,
                    slippage=slippage,
                )

                all_quotes, quote = data.get("quotes", []), data.get("best_quote")

                if preferred_providers and all_quotes:
                    selected = self._select_quote_by_provider(
                        all_quotes, preferred_providers
                    )
                    if selected:
                        return (True, selected)

                if quote:
                    return (True, quote)

                last_error = "No quotes available"
            except Exception as e:
                last_error = str(e)
                if attempt < retries - 1:
                    self.logger.warning(
                        f"Quote attempt {attempt + 1}/{retries} failed: {e}"
                    )

        self.logger.error(f"All {retries} quote attempts failed: {last_error}")
        return (False, last_error)

    async def swap_from_quote(
        self,
        from_token: dict[str, Any],
        to_token: dict[str, Any],
        from_address: str,
        quote: dict[str, Any],
        strategy_name: str | None = None,
    ) -> tuple[bool, Any]:
        chain_id = from_token["chain"]["id"]

        calldata = quote.get("calldata")
        if not calldata or not calldata.get("data"):
            return (False, "Quote missing calldata")

        transaction = {
            **calldata,
            "chainId": chain_id,
            "from": Web3.to_checksum_address(from_address),
        }
        if "value" in calldata:
            transaction["value"] = int(calldata["value"])

        approve_amount = (
            quote.get("input_amount")
            or quote.get("inputAmount")
            or transaction.get("value")
        )
        token_address = from_token.get("address")

        spender = transaction.get("to")
        if (
            token_address
            and spender
            and approve_amount
            and not is_native_token(token_address)
        ):
            await self._handle_token_approval(
                chain_id=chain_id,
                token_address=from_token.get("address"),
                owner_address=from_address,
                spender_address=spender,
                amount=int(approve_amount),
            )

        txn_hash = await send_transaction(
            transaction, self.strategy_wallet_signing_callback
        )
        self.logger.info(f"Swap broadcast: tx={txn_hash}")

        try:
            ledger_record = await self._record_swap_operation(
                from_token=from_token,
                to_token=to_token,
                wallet_address=from_address,
                quote=quote,
                tx_hash=txn_hash,
                strategy_name=strategy_name,
            )
        except Exception as e:
            self.logger.warning(
                f"Ledger recording failed (swap succeeded on-chain): {e}"
            )
            ledger_record = {}

        result_payload: dict[str, Any] = {
            "from_amount": quote.get("input_amount"),
            "to_amount": quote.get("output_amount"),
            "tx_hash": txn_hash,
            "ledger_record": ledger_record,
        }

        return (True, result_payload)

    async def swap_from_token_ids(
        self,
        from_token_id: str,
        to_token_id: str,
        from_address: str,
        amount: str,
        strategy_name: str | None = None,
        preferred_providers: list[str] | None = None,
        retries: int = 1,
        slippage: float | None = None,
    ) -> tuple[bool, Any]:
        from_token = await self.token_client.get_token_details(from_token_id)
        to_token = await self.token_client.get_token_details(to_token_id)
        if not from_token:
            return (False, f"From token not found: {from_token_id}")
        if not to_token:
            return (False, f"To token not found: {to_token_id}")

        success, quote = await self.best_quote(
            from_token_address=from_token.get("address"),
            to_token_address=to_token.get("address"),
            from_chain_id=(from_token.get("chain") or {}).get("id"),
            to_chain_id=(to_token.get("chain") or {}).get("id"),
            from_address=from_address,
            amount=amount,
            preferred_providers=preferred_providers,
            retries=retries,
            slippage=slippage,
        )
        if not success:
            return (False, quote)

        return await self.swap_from_quote(
            from_token=from_token,
            to_token=to_token,
            from_address=from_address,
            quote=quote,
            strategy_name=strategy_name,
        )
