import json
import time
from typing import Any

import httpx
from loguru import logger

from wayfinder_paths.core.config import get_api_base_url
from wayfinder_paths.core.constants.base import DEFAULT_HTTP_TIMEOUT


class WayfinderClient:
    def __init__(self):
        self.api_base_url = f"{get_api_base_url()}/"
        timeout = httpx.Timeout(DEFAULT_HTTP_TIMEOUT)
        self.client = httpx.AsyncClient(timeout=timeout)

        self.headers = {
            "Content-Type": "application/json",
        }

    def clear_auth(self) -> None:
        self.headers.pop("X-API-KEY", None)

    def _load_config_credentials(self) -> dict[str, str | None]:
        try:
            with open("config.json") as f:
                cfg = json.load(f)
            system = cfg.get("system", {}) if isinstance(cfg, dict) else {}
            api_key = system.get("api_key")
            return {"api_key": api_key}
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.debug(f"Could not load config file at config.json: {e}")
            return {"api_key": None}
        except Exception as e:
            logger.warning(f"Unexpected error loading config file at config.json: {e}")
            return {"api_key": None}

    def _ensure_api_key(self) -> bool:
        if self.headers.get("X-API-KEY"):
            return True

        creds = self._load_config_credentials()
        api_key = creds.get("api_key")

        if api_key:
            api_key = api_key.strip() if isinstance(api_key, str) else api_key
            if not api_key:
                raise ValueError("API key cannot be empty")
            self.headers["X-API-KEY"] = api_key
            return True

        raise PermissionError(
            "Not authenticated: provide api_key in system.api_key in config.json"
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        logger.debug(f"Making {method} request to {url}")
        start_time = time.time()

        # Ensure API key is set in headers if available and not already set
        # This ensures API keys are passed to all endpoints (including public ones) for rate limiting
        if not self.headers.get("X-API-KEY"):
            creds = self._load_config_credentials()
            api_key = creds.get("api_key")

            if api_key:
                api_key = api_key.strip() if isinstance(api_key, str) else api_key
                if api_key:
                    self.headers["X-API-KEY"] = api_key

        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)
        resp = await self.client.request(method, url, headers=merged_headers, **kwargs)

        elapsed = time.time() - start_time
        if resp.status_code >= 400:
            logger.warning(
                f"HTTP {resp.status_code} response for {method} {url} after {elapsed:.2f}s"
            )
        else:
            logger.debug(
                f"HTTP {resp.status_code} response for {method} {url} after {elapsed:.2f}s"
            )

        resp.raise_for_status()
        return resp

    async def _authed_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        self._ensure_api_key()
        return await self._request(method, url, headers=headers, **kwargs)
