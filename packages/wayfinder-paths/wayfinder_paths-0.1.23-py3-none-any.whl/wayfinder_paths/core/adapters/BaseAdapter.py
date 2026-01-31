from __future__ import annotations

from abc import ABC
from typing import Any

from loguru import logger


class BaseAdapter(ABC):
    adapter_type: str | None = None

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(adapter=self.__class__.__name__)

    async def connect(self) -> bool:
        return True

    async def get_balance(self, asset: str) -> dict[str, Any]:
        if not asset or not isinstance(asset, str) or not asset.strip():
            raise ValueError("asset must be a non-empty string")
        raise NotImplementedError(
            f"get_balance not supported by {self.__class__.__name__}"
        )

    async def health_check(self) -> dict[str, Any]:
        try:
            connected = await self.connect()
            return {
                "status": "healthy" if connected else "unhealthy",
                "connected": connected,
                "adapter": self.adapter_type or self.__class__.__name__,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "adapter": self.adapter_type or self.__class__.__name__,
            }

    async def close(self) -> None:
        pass
