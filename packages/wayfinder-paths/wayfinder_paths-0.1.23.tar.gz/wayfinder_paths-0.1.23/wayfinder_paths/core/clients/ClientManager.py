from typing import Any

from wayfinder_paths.core.clients.BRAPClient import BRAPClient
from wayfinder_paths.core.clients.HyperlendClient import HyperlendClient
from wayfinder_paths.core.clients.LedgerClient import LedgerClient
from wayfinder_paths.core.clients.PoolClient import PoolClient
from wayfinder_paths.core.clients.protocols import (
    BRAPClientProtocol,
    HyperlendClientProtocol,
    LedgerClientProtocol,
    PoolClientProtocol,
    TokenClientProtocol,
)
from wayfinder_paths.core.clients.TokenClient import TokenClient


class ClientManager:
    def __init__(
        self,
        clients: dict[str, Any] | None = None,
        skip_auth: bool = False,
    ):
        self._injected_clients = clients or {}
        self._skip_auth = skip_auth

        self._token_client: TokenClientProtocol | None = None
        self._ledger_client: LedgerClientProtocol | None = None
        self._pool_client: PoolClientProtocol | None = None
        self._hyperlend_client: HyperlendClientProtocol | None = None
        self._brap_client: BRAPClientProtocol | None = None

    def _get_or_create_client(
        self,
        client_attr: str,
        injected_key: str,
        client_class: type[Any],
    ) -> Any:
        client = getattr(self, client_attr)
        if not client:
            client = self._injected_clients.get(injected_key) or client_class()
            setattr(self, client_attr, client)
        return client

    @property
    def token(self) -> TokenClientProtocol:
        return self._get_or_create_client("_token_client", "token", TokenClient)

    @property
    def ledger(self) -> LedgerClientProtocol:
        return self._get_or_create_client("_ledger_client", "ledger", LedgerClient)

    @property
    def pool(self) -> PoolClientProtocol:
        return self._get_or_create_client("_pool_client", "pool", PoolClient)

    @property
    def hyperlend(self) -> HyperlendClientProtocol:
        return self._get_or_create_client(
            "_hyperlend_client", "hyperlend", HyperlendClient
        )

    @property
    def brap(self) -> BRAPClientProtocol:
        return self._get_or_create_client("_brap_client", "brap", BRAPClient)
