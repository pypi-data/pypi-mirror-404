import json
import time
from typing import Union, List, Optional
from eth_account.signers.local import LocalAccount
from eth_abi import encode
from decimal import Decimal as PyDecimal

from ddx._rust.decimal import Decimal
from ddx._rust.common.requests.intents import (
    OrderIntent,
    CancelOrderIntent,
    CancelAllIntent,
    ProfileUpdateIntent,
    WithdrawIntent,
)
from ddx.rest_client.clients.base_client import BaseClient
from ddx.rest_client.constants.endpoints import Signed
from ddx.rest_client.models.signed import TradeReceipt
from ddx.rest_client.utils.encryption_utils import encrypt_with_nonce
from ddx.rest_client.http.http_client import HTTPClient


class TradingJSONEncoder(json.JSONEncoder):
    """JSON encoder for trading request data"""

    def default(self, o):
        if hasattr(o, "repr_json"):
            return o.repr_json()
        elif type(o) == Decimal:
            return PyDecimal(str(o))
        return super().default(o)


class SignedClient(BaseClient):
    """
    Trading operations for executing orders and other trading actions.

    Parameters
    ----------
    http : HTTPClient
        The HTTP client instance to use for requests
    base_url : str
        The base URL for trading endpoints
    web3_account : Any
        The web3 account for signing requests
    chain_id : int
        The blockchain chain ID
    verifying_contract : str
        The contract address for EIP-712 signing
    """

    def __init__(
        self,
        http: HTTPClient,
        base_url: str,
        web3_account: LocalAccount,
        chain_id: int,
        verifying_contract: str,
    ):
        super().__init__(http, base_url)
        self._web3_account = web3_account
        self._chain_id = chain_id
        self._verifying_contract = verifying_contract
        self._encryption_key = None

    async def _get_or_fetch_encryption_key(self) -> str:
        """Get cached encryption key or fetch if not available"""

        if self._encryption_key is None:
            response = await self._http.get(self._build_url(Signed.ENCRYPTION_KEY))
            self._encryption_key = response

        return self._encryption_key

    async def _encrypt_and_submit_request(
        self,
        intent: Union[
            OrderIntent,
            CancelOrderIntent,
            CancelAllIntent,
            ProfileUpdateIntent,
            WithdrawIntent,
        ],
        local_account: Optional[LocalAccount] = None,
    ) -> TradeReceipt:
        """
        Helper method to encrypt and submit trading requests.

        Parameters
        ----------
        intent : Union[OrderIntent, CancelOrderIntent, CancelAllIntent, ProfileUpdateIntent, WithdrawIntent]
            The trading intent to encrypt and submit
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TradeReceipt
            The parsed receipt response
        """

        account = local_account or self._web3_account

        intent.signature = account.signHash(
            intent.hash_eip712((self._chain_id, self._verifying_contract))
        ).signature.hex()

        encryption_key = await self._get_or_fetch_encryption_key()
        encrypted_contents = encrypt_with_nonce(
            encryption_key, TradingJSONEncoder().encode(intent.json)
        )

        # Submit the encrypted request
        response = await self._http.post(
            self._build_url(Signed.SUBMIT_REQUEST), data=encrypted_contents
        )

        return TradeReceipt.model_validate(response)

    def get_nonce(self) -> str:
        """
        Get nonce to be used as the unique nonce in various commands.

        Returns
        -------
        str
            32-byte hex-encoded nonce string, encoded using eth_abi
        """

        # Retrieve current UNIX time in nanoseconds to derive a unique, monotonically-increasing nonce
        nonce = str(time.time_ns())

        # abi.encode(['bytes32'], [nonce])
        return f'0x{encode(["bytes32"], [nonce.encode("utf8")]).hex()}'

    async def place_order(
        self,
        order: OrderIntent,
        local_account: Optional[LocalAccount] = None,
    ) -> TradeReceipt:
        """
        Place a single order on the exchange.

        Parameters
        ----------
        order : OrderIntent
            The order intent to submit, containing symbol, strategy, side,
            order type, quantity, and price information
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TradeReceipt
            The response containing order submission details including
            nonce, request hash, and request index
        """

        return await self._encrypt_and_submit_request(
            order, local_account=local_account
        )

    async def place_orders(
        self,
        orders: List[OrderIntent],
        local_account: Optional[LocalAccount] = None,
    ) -> List[TradeReceipt]:
        """
        Place multiple orders efficiently.

        Parameters
        ----------
        orders : List[OrderIntent]
            List of order intents to submit
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        List[TradeReceipt]
            List of responses for each order containing submission details
        """

        results = []
        for order in orders:
            result = await self.place_order(order, local_account=local_account)
            results.append(result)

        return results

    async def cancel_order(
        self,
        cancel_intent: CancelOrderIntent,
        local_account: Optional[LocalAccount] = None,
    ) -> TradeReceipt:
        """
        Cancel a specific order.

        Parameters
        ----------
        cancel_intent : CancelOrderIntent
            The cancel intent containing order details to cancel
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TradeReceipt
            Response containing cancellation details
        """

        return await self._encrypt_and_submit_request(
            cancel_intent, local_account=local_account
        )

    async def cancel_all(
        self,
        cancel_all_intent: CancelAllIntent,
        local_account: Optional[LocalAccount] = None,
    ) -> TradeReceipt:
        """
        Cancel all orders for a strategy.

        Parameters
        ----------
        cancel_all_intent : CancelAllIntent
            The cancel all intent containing strategy details
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TradeReceipt
            Response containing cancellation details for all orders
        """

        return await self._encrypt_and_submit_request(
            cancel_all_intent, local_account=local_account
        )

    async def withdraw(
        self,
        withdraw_intent: WithdrawIntent,
        local_account: Optional[LocalAccount] = None,
    ) -> TradeReceipt:
        """
        Submit a withdrawal request.

        Parameters
        ----------
        withdraw_intent : WithdrawIntent
            The withdrawal intent containing amount and strategy details
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TradeReceipt
            Response containing withdrawal submission details
        """

        return await self._encrypt_and_submit_request(
            withdraw_intent, local_account=local_account
        )

    # TODO: Add and fuzz withdraw_ddx
    # TODO: Add and fuzz modify_order

    async def update_profile(
        self,
        profile_update_intent: ProfileUpdateIntent,
        local_account: Optional[LocalAccount] = None,
    ) -> TradeReceipt:
        """
        Submit a profile update request.

        Parameters
        ----------
        profile_update_intent : ProfileUpdateIntent
            The profile update intent containing ddx fee election details
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TradeReceipt
            Response containing profile update submission details
        """

        return await self._encrypt_and_submit_request(
            profile_update_intent, local_account=local_account
        )
