import asyncio
import logging
from typing import Optional
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import TxReceipt
from zero_ex.contract_wrappers import TxParams
from eth_abi.utils.padding import zpad32_right

from ddx._rust.decimal import Decimal
from ddx._rust.common.state.keys import StrategyKey
from ddx.common.utils import to_base_unit_amount_list, to_base_unit_amount
from ddx.rest_client.clients.base_client import BaseClient
from ddx.rest_client.contracts.i_collateral import ICollateral
from ddx.rest_client.contracts.ddx import DDX
from ddx.rest_client.contracts.dummy_token import DummyToken
from ddx.rest_client.contracts.checkpoint import Checkpoint
from ddx.rest_client.contracts.i_stake import IStake
from ddx.rest_client.constants.endpoints import OnChain
from ddx.rest_client.http.http_client import HTTPClient

COLLATERAL_DECIMALS = 6
DDX_DECIMALS = 18
DEFAULT_GAS_LIMIT = 500_000


class OnChainClient(BaseClient):
    """
    On-chain operations for depositing, withdrawing, and other activities.

    Parameters
    ----------
    http : HTTPClient
        The HTTP client instance to use for requests
    base_url : str
        The base URL for trading endpoints
    web3_account : Any
        The web3 account for signing requests
    verifying_contract : str
        The contract address
    """

    def __init__(
        self,
        http: HTTPClient,
        base_url: str,
        web3_account: LocalAccount,
        web3: Web3,
        verifying_contract: str,
    ):
        super().__init__(http, base_url)
        self._web3_account = web3_account
        self._web3 = web3
        self._verifying_contract = verifying_contract
        self._logger = logging.getLogger(__name__)

    def _send_transaction(
        self,
        contract_method,
        method_params: list,
        nonce: Optional[int] = None,
        gas: int = 500_000,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Helper to build, sign and send a transaction.

        Parameters
        ----------
        contract_method : ContractMethod
            The contract method object
        method_params : list
            Parameters to pass to the contract method
        nonce : Optional[int]
            Custom nonce or None for auto
        gas : int
            Gas limit for transaction
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt
        """

        account = local_account or self._web3_account

        if nonce is None:
            nonce = self._web3.eth.get_transaction_count(account.address)

        tx = contract_method.build_transaction(
            *method_params,
            tx_params=TxParams(from_=account.address, nonce=nonce, gas=gas),
        )
        signed_tx = self._web3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash, poll_latency=0.5)

        return receipt

    def approve(
        self,
        collateral_address: str,
        amount: Decimal,
        nonce: Optional[int] = None,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Approve ERC-20 collateral for transfer to the DerivaDEX contract.

        Parameters
        ----------
        collateral_address : str
            The token contract address to approve
        amount : Decimal
            Amount to approve for transfer
        nonce : Optional[int]
            Custom nonce for the transaction, if None uses next available
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt
        """

        if not self._verifying_contract:
            raise TypeError("Verifying contract address is not set")
        dummy_token = DummyToken(self._web3, collateral_address)
        approve_amount = to_base_unit_amount(amount, COLLATERAL_DECIMALS)

        return self._send_transaction(
            dummy_token.approve,
            method_params=[self._verifying_contract, approve_amount],
            nonce=nonce,
            local_account=local_account,
        )

    async def deposit(
        self,
        collateral_address: str,
        strategy_id: str,
        amount: Decimal,
        nonce: Optional[int] = None,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Deposit ERC-20 collateral into a strategy.

        Parameters
        ----------
        collateral_address : str
            The token contract address to deposit
        strategy_id : str
            Strategy identifier to deposit into
        amount : Decimal
            Amount to deposit
        nonce : Optional[int]
            Custom nonce for the transaction, if None uses next available
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt
        """

        account = local_account or self._web3_account
        kyc_auth = await self._http.get(
            self._build_url(OnChain.KYC_AUTH), params={"trader": account.address}
        )

        encoded_strategy = zpad32_right(
            len(strategy_id).to_bytes(1, byteorder="little")
            + strategy_id.encode("utf8")
        )
        deposit_amount = to_base_unit_amount(amount, COLLATERAL_DECIMALS)
        i_collateral_contract = ICollateral(self._web3, self._verifying_contract)

        return self._send_transaction(
            i_collateral_contract.deposit,
            method_params=[
                collateral_address,
                encoded_strategy,
                deposit_amount,
                kyc_auth["kycAuth"]["expiryBlock"],
                kyc_auth["signature"],
            ],
            nonce=nonce,
            gas=DEFAULT_GAS_LIMIT,
            local_account=local_account,
        )

    def approve_ddx(
        self,
        ddx_address: str,
        amount: Decimal,
        nonce: Optional[int] = None,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Approve DDX for transfer to the DerivaDEX contract.

        Parameters
        ----------
        ddx_address : str
            The DDX token contract address
        amount : Decimal
            Amount to approve for transfer
        nonce : Optional[int]
            Custom nonce for the transaction, if None uses next available
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt
        """

        if not self._verifying_contract:
            raise TypeError("Verifying contract address is not set")
        ddx_contract = DDX(self._web3, ddx_address)
        approve_amount = to_base_unit_amount(amount, DDX_DECIMALS)

        return self._send_transaction(
            ddx_contract.approve,
            method_params=[self._verifying_contract, approve_amount],
            nonce=nonce,
            local_account=local_account,
        )

    async def deposit_ddx(
        self,
        amount: Decimal,
        nonce: Optional[int] = None,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Deposit DDX to exchange.

        Parameters
        ----------
        amount : Decimal
            Amount of DDX to deposit
        nonce : Optional[int]
            Custom nonce for the transaction, if None uses next available
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt
        """

        account = local_account or self._web3_account
        kyc_auth = await self._http.get(
            self._build_url(OnChain.KYC_AUTH), params={"trader": account.address}
        )

        deposit_amount = to_base_unit_amount(amount, DDX_DECIMALS)
        i_stake_contract = IStake(self._web3, self._verifying_contract)

        return self._send_transaction(
            i_stake_contract.deposit_ddx,
            method_params=[
                deposit_amount,
                kyc_auth["kycAuth"]["expiryBlock"],
                kyc_auth["signature"],
            ],
            nonce=nonce,
            gas=DEFAULT_GAS_LIMIT,
            local_account=local_account,
        )

    async def withdraw(
        self,
        collateral_address: str,
        strategy_id: str,
        amount: Decimal,
        nonce: Optional[int] = None,
        local_account: Optional[LocalAccount] = None,
    ) -> TxReceipt:
        """
        Withdraw collateral from a strategy.

        Parameters
        ----------
        collateral_address : str
            The token contract address to withdraw
        strategy_id : str
            Strategy identifier to withdraw from
        amount : Decimal
            Amount to deposit
        nonce : Optional[int]
            Custom nonce for the transaction, if None uses next available
        local_account : Optional[LocalAccount]
            Local account to sign with, defaults to client's account

        Returns
        -------
        TxReceipt
            Transaction receipt
        """

        account = local_account or self._web3_account

        # Get checkpointed epoch id
        checkpoint_contract = Checkpoint(self._web3, self._verifying_contract)
        checkpointed_epoch_id = checkpoint_contract.get_latest_checkpoint.call()[3]

        # Get withdrawal proof
        strategy_key = StrategyKey(
            f"0x00{account.address[2:]}",
            StrategyKey.generate_strategy_id_hash(strategy_id),
        )

        proof_response = await self._http.get(
            self._build_url(OnChain.PROOF),
            params={
                "key": str(strategy_key.encode_key()),
                "epochId": checkpointed_epoch_id,
            },
        )

        collateral_address = self._web3.to_checksum_address(collateral_address)

        # Prepare strategy data
        checkpointed_strategy = {
            "maxLeverage": 3,
            "frozen": False,
            "availCollateral": {
                "tokens": [
                    self._web3.to_checksum_address(key)
                    for key in list(
                        proof_response["item"]["Strategy"]["availCollateral"].keys()
                    )
                ],
                "amounts": to_base_unit_amount_list(
                    [
                        Decimal(val)
                        for val in list(
                            proof_response["item"]["Strategy"][
                                "availCollateral"
                            ].values()
                        )
                    ],
                    6,
                ),
            },
            "lockedCollateral": {
                "tokens": [
                    self._web3.to_checksum_address(key)
                    for key in list(
                        proof_response["item"]["Strategy"]["lockedCollateral"].keys()
                    )
                ],
                "amounts": to_base_unit_amount_list(
                    [
                        Decimal(val)
                        for val in list(
                            proof_response["item"]["Strategy"][
                                "lockedCollateral"
                            ].values()
                        )
                    ],
                    6,
                ),
            },
        }

        withdraw_data = {
            "tokens": [collateral_address],
            "amounts": [int(amount * Decimal("1e6"))],
        }

        # Execute withdrawal
        i_collateral_contract = ICollateral(self._web3, self._verifying_contract)
        return self._send_transaction(
            i_collateral_contract.withdraw,
            method_params=[
                StrategyKey.generate_strategy_id_hash(strategy_id),
                withdraw_data,
                checkpointed_strategy,
                f'0x{bytes(proof_response["proof"]).hex()}',
            ],
            nonce=nonce,
            local_account=local_account,
        )

    # TODO: Add and fuzz withdraw_ddx method
    # TODO: Add and fuzz checkpoint method

    async def wait_for_confirmations(
        self,
        tx_receipt: TxReceipt,
        confirmations: int = 6,
        check_interval: float = 1.0,
    ) -> None:
        """
        Wait for required number of block confirmations.

        Parameters
        ----------
        tx_receipt : TxReceipt
            Transaction receipt containing block number
        confirmations : int, default=6
            Number of block confirmations to wait for
        check_interval : float, default=1.0
            How often to check for new blocks in seconds

        Raises
        ------
        TimeoutError
            If confirmations don't arrive within reasonable time
        """

        tx_block_number = tx_receipt.blockNumber
        timeout = (confirmations * 2) * 12
        start_time = asyncio.get_event_loop().time()

        while True:
            current_block = self._web3.eth.block_number
            confirmed_blocks = current_block - tx_block_number

            if confirmed_blocks >= confirmations:
                return

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(
                    f"Timeout waiting for {confirmations} confirmations. "
                    f"Got {confirmed_blocks} after {timeout} seconds"
                )

            await asyncio.sleep(check_interval)
