#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import inspect
import json
import sys
from typing import Any

from loguru import logger

from wayfinder_paths.core.config import CONFIG
from wayfinder_paths.core.strategies.Strategy import Strategy
from wayfinder_paths.core.utils.evm_helpers import resolve_private_key_for_from_address
from wayfinder_paths.core.utils.web3 import get_transaction_chain_id, web3_from_chain_id


def get_strategy_config(strategy_name: str) -> dict[str, Any]:
    config = dict(CONFIG.get("strategy", {}))
    wallets = {w["label"]: w for w in CONFIG.get("wallets", [])}

    if "main_wallet" not in config and "main" in wallets:
        config["main_wallet"] = {"address": wallets["main"]["address"]}
    if "strategy_wallet" not in config and strategy_name in wallets:
        config["strategy_wallet"] = {"address": wallets[strategy_name]["address"]}

    by_addr = {w["address"].lower(): w for w in CONFIG.get("wallets", [])}
    for key in ("main_wallet", "strategy_wallet"):
        if wallet := config.get(key):
            if entry := by_addr.get(wallet.get("address", "").lower()):
                if pk := entry.get("private_key") or entry.get("private_key_hex"):
                    wallet["private_key_hex"] = pk
    return config


def create_signing_callback(address: str, config: dict[str, Any]):
    async def sign(transaction: dict) -> str:
        pk = resolve_private_key_for_from_address(address, config)
        async with web3_from_chain_id(get_transaction_chain_id(transaction)) as web3:
            return web3.eth.account.sign_transaction(
                transaction, pk
            ).raw_transaction.hex()

    return sign


def find_strategy_class(module) -> type[Strategy]:
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Strategy) and obj is not Strategy:
            return obj
    raise ValueError(f"No Strategy subclass found in {module.__name__}")


async def run_strategy(strategy_name: str, action: str = "status", **kw):
    config = get_strategy_config(strategy_name)

    def signing_cb(key: str):
        if addr := config.get(key, {}).get("address"):
            return create_signing_callback(addr, config)
        return None

    module = importlib.import_module(
        f"wayfinder_paths.strategies.{strategy_name}.strategy"
    )
    strategy_cls = find_strategy_class(module)
    strategy = strategy_cls(
        config,
        main_wallet_signing_callback=signing_cb("main_wallet"),
        strategy_wallet_signing_callback=signing_cb("strategy_wallet"),
    )
    await strategy.setup()

    if action == "policy":
        policies = strategy.policies() if hasattr(strategy, "policies") else []
        if wallet_id := kw.get("wallet_id"):
            policies = [p.replace("FORMAT_WALLET_ID", wallet_id) for p in policies]
        result = {"policies": policies}
    elif action == "status":
        result = await strategy.status()
    elif action == "deposit":
        result = await strategy.deposit(
            main_token_amount=kw.get("main_token_amount", 0.0),
            gas_token_amount=kw.get("gas_token_amount", 0.0),
        )
    elif action == "withdraw":
        result = await strategy.withdraw(amount=kw.get("amount"))
    elif action == "update":
        result = await strategy.update()
    elif action == "exit":
        result = await strategy.exit()
    elif action == "run":
        while True:
            try:
                result = await strategy.update()
                logger.info(f"Update: {result}")
                await asyncio.sleep(kw.get("interval", 60))
            except asyncio.CancelledError:
                result = (True, "stopped")
                break
    else:
        raise ValueError(f"Unknown action: {action}")

    print(
        json.dumps(result, indent=2)
        if isinstance(result, dict)
        else f"{action}: {result}"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("strategy")
    p.add_argument(
        "--action",
        default="status",
        choices=["run", "deposit", "withdraw", "status", "update", "exit", "policy"],
    )
    p.add_argument("--amount", type=float)
    p.add_argument("--main-token-amount", type=float, dest="main_token_amount")
    p.add_argument(
        "--gas-token-amount", type=float, dest="gas_token_amount", default=0.0
    )
    p.add_argument("--interval", type=int, default=60)
    p.add_argument("--wallet-id", dest="wallet_id")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if args.debug else "INFO")

    asyncio.run(
        run_strategy(
            args.strategy,
            args.action,
            amount=args.amount,
            main_token_amount=args.main_token_amount,
            gas_token_amount=args.gas_token_amount,
            interval=args.interval,
            wallet_id=args.wallet_id,
        )
    )


if __name__ == "__main__":
    main()
