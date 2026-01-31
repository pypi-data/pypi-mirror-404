"""
DerivaDEX Client
"""

from typing import Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware

from ddx.realtime_client import RealtimeClient
from ddx.rest_client.clients.market_client import MarketClient
from ddx.rest_client.clients.on_chain_client import OnChainClient
from ddx.rest_client.clients.signed_client import SignedClient
from ddx.rest_client.clients.system_client import SystemClient
from ddx.rest_client.clients.trade_client import TradeClient
from ddx.rest_client.http.http_client import HTTPClient


class DerivaDEXClient:
    """
    Main client for interacting with the DerivaDEX API.

    This client provides access to all DerivaDEX API endpoints through
    various client objects and supports both REST and WebSocket APIs.
    It can be used as an async context manager to ensure proper client cleanup.

    Attributes
    ----------
    market : MarketClient
        Access to market operations
    on_chain : OnChainClient
        Access to on-chain operations
    signed : SignedClient
        Access to signed operations
    system : SystemClient
        Access to system operations
    trade : TradeClient
        Access to trade operations
    web3_account : Account
        The Web3 account used for signing transactions
    """

    def __init__(
        self,
        base_url: str,
        ws_url: str,
        rpc_url: str,
        contract_deployment: str,
        private_key: Optional[str] = None,
        mnemonic: Optional[str] = None,
        timeout: int = 30,
        http_max_connections: int = 100,
        http_max_keepalive: int = 20,
        keepalive_expiry: int = 5,
    ) -> None:
        """
        Initialize the client.

        Parameters
        ----------
        base_url : str
            Base URL for webserver
        ws_url : str
            WebSocket URL for real-time updates
        rpc_url : str
            RPC URL for webserver
        contract_deployment : str
            Type of contract deployment (e.g. "mainnet")
        private_key : Optional[str]
            Ethereum private key for user
        mnemonic : Optional[str]
            Ethereum mnemonic for user
        timeout : int, default=30
            Timeout in seconds for HTTP requests
        http_max_connections : int, default=100
            Max concurrent connections allowed for the HTTP client
        http_max_keepalive : int, default=20
            Max allowable keep-alive connections, None means always allow
        keepalive_expiry: int, default=5
            Time in seconds to keep HTTP connection alive. None means connection never expires

        Raises
        ------
        ValueError
            If neither private_key nor mnemonic is provided
        """

        if not private_key and not mnemonic:
            raise ValueError("Either private_key or mnemonic must be provided")

        self._base_url = base_url
        self._ws_url = ws_url

        # Initialize HTTP client
        self._http = HTTPClient(timeout, max_connections=http_max_connections, max_keepalive=http_max_keepalive, keepalive_expiry=keepalive_expiry)

        self._contract_deployment = contract_deployment

        # These will be initialized when needed
        self._chain_id: Optional[int] = None
        self._verifying_contract: Optional[str] = None

        # Initialize web3 service
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))

        if contract_deployment == "geth":
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Initialize web3 account from private key or mnemonic
        if private_key is not None:
            self.web3_account = self.w3.eth.account.from_key(private_key)
        else:
            self.w3.eth.account.enable_unaudited_hdwallet_features()
            self.web3_account = self.w3.eth.account.from_mnemonic(mnemonic)

        # Set default account for send transactions
        self.w3.eth.defaultAccount = self.web3_account.address

        # Initialize clients (lazy loading)
        self._market: Optional[MarketClient] = None
        self._on_chain: Optional[OnChainClient] = None
        self._signed: Optional[SignedClient] = None
        self._system: Optional[SystemClient] = None
        self._trade: Optional[TradeClient] = None

    async def __aenter__(self) -> "DerivaDEXClient":
        await self._http.__aenter__()

        # Get deployment configuration
        deployment_info = await self.system.get_deployment_info(
            self._contract_deployment
        )
        self._chain_id = deployment_info.chain_id
        self._verifying_contract = deployment_info.addresses.derivadex_address

        # Propagate chain and verifying contract to already-initialized sub-clients (if any)
        if self._on_chain is not None:
            self._on_chain._verifying_contract = self._verifying_contract  # type: ignore[attr-defined]
        if self._signed is not None:
            self._signed._chain_id = self._chain_id  # type: ignore[attr-defined]
            self._signed._verifying_contract = self._verifying_contract  # type: ignore[attr-defined]

        # Initialize and start WebSocket client
        # We do this here rather than lazy loading because we want
        # to ensure the connection is established when using the context manager
        self._ws = RealtimeClient(self._ws_url)
        await self._ws.connect()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # Stop WebSocket client if it was started
        if self._ws is not None:
            await self._ws.disconnect()
        await self._http.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def ws(self) -> RealtimeClient:
        """
        Access WebSocket functionality.

        Returns
        -------
        RealtimeClient
            The WebSocket Realtime API client instance

        Raises
        ------
        RuntimeError
            If accessed outside of context manager
        """

        if not hasattr(self, "_ws"):
            raise RuntimeError("WebSocket client must be used within context manager")

        return self._ws

    @property
    def market(self) -> MarketClient:
        """
        Access to market operations.

        Returns
        -------
        MarketClient
            The market client instance, initialized on first access
        """

        if self._market is None:
            self._market = MarketClient(self._http, self._base_url)

        return self._market

    @property
    def on_chain(self) -> OnChainClient:
        """
        Access on-chain operations.

        Returns
        -------
        OnChainClient
            The on-chain client instance, initialized on first access
        """

        if self._on_chain is None:
            self._on_chain = OnChainClient(
                self._http,
                self._base_url,
                self.web3_account,
                self.w3,
                self._verifying_contract,
            )

        return self._on_chain

    @property
    def signed(self) -> SignedClient:
        """
        Access to signed operations

        Returns
        -------
        SignedClient
            The signed client instance, initialized on first access
        """

        if self._signed is None:
            self._signed = SignedClient(
                self._http,
                self._base_url,
                self.web3_account,
                self._chain_id,
                self._verifying_contract,
            )

        return self._signed

    @property
    def system(self) -> SystemClient:
        """
        Access to system operations.

        Returns
        -------
        SystemClient
            The system client instance, initialized on first access
        """

        if self._system is None:
            self._system = SystemClient(self._http, self._base_url)

        return self._system

    @property
    def trade(self) -> TradeClient:
        """
        Access to trade operations

        Returns
        -------
        TradeClient
            The trade client instance, initialized on first access
        """

        if self._trade is None:
            self._trade = TradeClient(
                self._http,
                self._base_url,
            )

        return self._trade
