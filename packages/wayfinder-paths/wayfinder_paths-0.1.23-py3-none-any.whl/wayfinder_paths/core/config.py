import json
from pathlib import Path
from typing import Any

from loguru import logger


def _load_config_file() -> dict[str, Any]:
    path = Path("config.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.warning(f"Failed to read config file at config.json: {e}")
        return {}


CONFIG = _load_config_file()


def set_rpc_urls(rpc_urls):
    if "strategy" not in CONFIG:
        CONFIG["strategy"] = {}
    if "rpc_urls" not in CONFIG["strategy"]:
        CONFIG["strategy"]["rpc_urls"] = {}
    CONFIG["strategy"]["rpc_urls"] = rpc_urls


def get_rpc_urls() -> dict[str, Any]:
    return CONFIG.get("strategy", {}).get("rpc_urls", {})


def get_api_base_url() -> str:
    system = CONFIG.get("system", {}) if isinstance(CONFIG, dict) else {}
    api_url = system.get("api_base_url")
    if api_url and isinstance(api_url, str):
        return api_url.strip()
    return "https://wayfinder.ai/api/v1"
