import asyncio
from collections.abc import Callable

from loguru import logger
from web3 import AsyncWeb3

from wayfinder_paths.core.constants.base import (
    SUGGESTED_GAS_PRICE_MULTIPLIER,
    SUGGESTED_PRIORITY_FEE_MULTIPLIER,
)
from wayfinder_paths.core.constants.chains import (
    CHAIN_ID_HYPEREVM,
    PRE_EIP_1559_CHAIN_IDS,
)
from wayfinder_paths.core.utils.web3 import (
    get_transaction_chain_id,
    web3_from_chain_id,
    web3s_from_chain_id,
)


def _get_transaction_from_address(transaction: dict) -> str:
    if "from" not in transaction:
        raise ValueError("Transaction does not contain from address")
    return AsyncWeb3.to_checksum_address(transaction["from"])


async def nonce_transaction(transaction: dict):
    transaction = transaction.copy()

    from_address = _get_transaction_from_address(transaction)

    async def _get_nonce(web3: AsyncWeb3, from_address: str) -> int:
        return await web3.eth.get_transaction_count(from_address)

    async with web3s_from_chain_id(get_transaction_chain_id(transaction)) as web3s:
        nonces = await asyncio.gather(
            *[_get_nonce(web3, from_address) for web3 in web3s]
        )

        nonce = max(nonces)
        transaction["nonce"] = nonce

    return transaction


async def gas_price_transaction(
    transaction: dict,
    gas_price_multiplier: float = SUGGESTED_GAS_PRICE_MULTIPLIER,
    priority_fee_multiplier: float = SUGGESTED_PRIORITY_FEE_MULTIPLIER,
):
    transaction = transaction.copy()

    async def _get_gas_price(web3: AsyncWeb3) -> int:
        return await web3.eth.gas_price

    async def _get_base_fee(web3: AsyncWeb3) -> int:
        latest_block = await web3.eth.get_block("latest")
        return latest_block.baseFeePerGas

    async def _get_priority_fee(web3: AsyncWeb3) -> int:
        lookback_blocks = 10
        percentile = 80
        fee_history = await web3.eth.fee_history(
            lookback_blocks, "latest", [percentile]
        )
        historical_priority_fees = [i[0] for i in fee_history.reward]
        return sum(historical_priority_fees) // len(historical_priority_fees)

    chain_id = get_transaction_chain_id(transaction)
    async with web3s_from_chain_id(chain_id) as web3s:
        if chain_id in PRE_EIP_1559_CHAIN_IDS:
            gas_prices = await asyncio.gather(*[_get_gas_price(web3) for web3 in web3s])
            gas_price = max(gas_prices)

            transaction["gasPrice"] = int(gas_price * gas_price_multiplier)
        elif chain_id == CHAIN_ID_HYPEREVM:
            # HyperEVM big blocks fetch base gas price from a different RPC method. Priority fee = 0 is # grandfathered in from Django, not sure what's right here.
            big_block_gas_prices = await asyncio.gather(
                *[web3.hype.big_block_gas_price() for web3 in web3s]
            )
            big_block_gas_price = max(big_block_gas_prices)

            transaction["maxFeePerGas"] = int(
                big_block_gas_price * priority_fee_multiplier
            )
            transaction["maxPriorityFeePerGas"] = 0
        else:
            base_fees = await asyncio.gather(*[_get_base_fee(web3) for web3 in web3s])
            priority_fees = await asyncio.gather(
                *[_get_priority_fee(web3) for web3 in web3s]
            )

            base_fee = max(base_fees)
            priority_fee = max(priority_fees)

            max_base_fee_growth_multiplier = 2
            transaction["maxFeePerGas"] = int(
                base_fee * max_base_fee_growth_multiplier
                + priority_fee * priority_fee_multiplier
            )
            transaction["maxPriorityFeePerGas"] = int(
                priority_fee * priority_fee_multiplier
            )

    return transaction


async def gas_limit_transaction(transaction: dict):
    transaction = transaction.copy()

    # prevents RPCs from taking this as a serious limit
    transaction.pop("gas", None)

    async def _estimate_gas(web3: AsyncWeb3, transaction: dict) -> int:
        try:
            return await web3.eth.estimate_gas(transaction, block_identifier="latest")
        except Exception as e:
            logger.info(
                f"Failed to estimate gas using {web3.provider.endpoint_uri}. Error: {e}"
            )
            return 0

    async with web3s_from_chain_id(get_transaction_chain_id(transaction)) as web3s:
        gas_limits = await asyncio.gather(
            *[_estimate_gas(web3, transaction) for web3 in web3s]
        )

        gas_limit = max(gas_limits)
        if gas_limit == 0:
            logger.error("Gas estimation failed on all RPCs")
            raise Exception("Gas estimation failed on all RPCs")
        transaction["gas"] = gas_limit

    return transaction


async def broadcast_transaction(chain_id, signed_transaction: bytes) -> str:
    async with web3_from_chain_id(chain_id) as web3:
        tx_hash = await web3.eth.send_raw_transaction(signed_transaction)
        return tx_hash.hex()


async def wait_for_transaction_receipt(
    chain_id: int,
    txn_hash: str,
    poll_interval: float = 0.1,
    timeout: int = 300,
    confirmations: int = 3,
) -> dict:
    async def _wait_for_receipt(web3: AsyncWeb3, tx_hash: str) -> dict:
        return await web3.eth.wait_for_transaction_receipt(
            tx_hash, poll_latency=poll_interval, timeout=timeout
        )

    async def _get_block_number(web3: AsyncWeb3) -> int:
        return await web3.eth.block_number

    async with web3s_from_chain_id(chain_id) as web3s:
        tasks = [
            asyncio.create_task(_wait_for_receipt(web3, txn_hash)) for web3 in web3s
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        receipt = done.pop().result()

        target_block = receipt["blockNumber"] + confirmations - 1
        while (
            max(await asyncio.gather(*[_get_block_number(w) for w in web3s]))
            < target_block
        ):
            await asyncio.sleep(poll_interval)
        return receipt


async def send_transaction(
    transaction: dict, sign_callback: Callable, wait_for_receipt=True
) -> str:
    if sign_callback is None:
        raise ValueError("sign_callback must be provided to send transaction")

    logger.info(f"Broadcasting transaction {transaction.get('to', 'unknown')[:10]}...")
    chain_id = get_transaction_chain_id(transaction)
    transaction = await gas_limit_transaction(transaction)
    transaction = await nonce_transaction(transaction)
    transaction = await gas_price_transaction(transaction)
    signed_transaction = await sign_callback(transaction)
    txn_hash = await broadcast_transaction(chain_id, signed_transaction)
    logger.info(f"Transaction broadcasted: {txn_hash}")
    if wait_for_receipt:
        await wait_for_transaction_receipt(chain_id, txn_hash)
    return txn_hash


# TODO: HypeEVM Big Blocks: Setting and detecting
