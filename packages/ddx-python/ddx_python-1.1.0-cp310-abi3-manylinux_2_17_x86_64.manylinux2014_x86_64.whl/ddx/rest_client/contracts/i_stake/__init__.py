"""Generated wrapper for IStake Solidity contract."""

# pylint: disable=too-many-arguments

import json
from typing import (  # pylint: disable=unused-import
    Any,
    List,
    Optional,
    Tuple,
    Union,
)

from eth_utils import to_checksum_address
from mypy_extensions import TypedDict  # pylint: disable=unused-import
from hexbytes import HexBytes
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.providers.base import BaseProvider

from zero_ex.contract_wrappers.bases import ContractMethod, Validator
from zero_ex.contract_wrappers.tx_params import TxParams


# Try to import a custom validator class definition; if there isn't one,
# declare one that we can instantiate for the default argument to the
# constructor for IStake below.
try:
    # both mypy and pylint complain about what we're doing here, but this
    # works just fine, so their messages have been disabled here.
    from . import (  # type: ignore # pylint: disable=import-self
        IStakeValidator,
    )
except ImportError:

    class IStakeValidator(  # type: ignore
        Validator
    ):
        """No-op input validator."""


try:
    from .middleware import MIDDLEWARE  # type: ignore
except ImportError:
    pass


class DepositDefsTraderData(TypedDict):
    """Python representation of a tuple or struct.

    Solidity compiler output does not include the names of structs that appear
    in method definitions.  A tuple found in an ABI may have been written in
    Solidity as a literal, anonymous tuple, or it may have been written as a
    named `struct`:code:, but there is no way to tell from the compiler
    output.  This class represents a tuple that appeared in a method
    definition.  Its name is derived from a hash of that tuple's field names,
    and every method whose ABI refers to a tuple with that same list of field
    names will have a generated wrapper method that refers to this class.

    Any members of type `bytes`:code: should be encoded as UTF-8, which can be
    accomplished via `str.encode("utf_8")`:code:
    """

    availDDXBalance: int

    lockedDDXBalance: int

    referralAddress: str

    payFeesInDDX: bool

    accessDenied: bool


class DepositDdxMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the depositDDX method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, amount: int, expiry_block: int, signature: Union[bytes, str]):
        """Validate the inputs to the depositDDX method."""
        self.validator.assert_valid(
            method_name='depositDDX',
            parameter_name='_amount',
            argument_value=amount,
        )
        self.validator.assert_valid(
            method_name='depositDDX',
            parameter_name='_expiryBlock',
            argument_value=expiry_block,
        )
        # safeguard against fractional inputs
        expiry_block = int(expiry_block)
        self.validator.assert_valid(
            method_name='depositDDX',
            parameter_name='_signature',
            argument_value=signature,
        )
        return (amount, expiry_block, signature)

    def call(self, amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _amount: The amount to deposit.
        :param _expiryBlock: Expiry block number for KYC authorization.
        :param _signature: Signature of KYC authorization address.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (amount, expiry_block, signature) = self.validate_and_normalize_inputs(amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(amount, expiry_block, signature).call(tx_params.as_dict())

    def send_transaction(self, amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _amount: The amount to deposit.
        :param _expiryBlock: Expiry block number for KYC authorization.
        :param _signature: Signature of KYC authorization address.
        :param tx_params: transaction parameters
        """
        (amount, expiry_block, signature) = self.validate_and_normalize_inputs(amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount, expiry_block, signature).transact(tx_params.as_dict())

    def build_transaction(self, amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (amount, expiry_block, signature) = self.validate_and_normalize_inputs(amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount, expiry_block, signature).build_transaction(tx_params.as_dict())

    def estimate_gas(self, amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (amount, expiry_block, signature) = self.validate_and_normalize_inputs(amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount, expiry_block, signature).estimate_gas(tx_params.as_dict())

class GetMaxDdxCapMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getMaxDDXCap method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().transact(tx_params.as_dict())

    def build_transaction(self, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().build_transaction(tx_params.as_dict())

    def estimate_gas(self, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method().estimate_gas(tx_params.as_dict())

class GetProcessedDdxWithdrawalsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getProcessedDDXWithdrawals method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, withdraw_address: str, block_number: int):
        """Validate the inputs to the getProcessedDDXWithdrawals method."""
        self.validator.assert_valid(
            method_name='getProcessedDDXWithdrawals',
            parameter_name='_withdrawAddress',
            argument_value=withdraw_address,
        )
        withdraw_address = self.validate_and_checksum_address(withdraw_address)
        self.validator.assert_valid(
            method_name='getProcessedDDXWithdrawals',
            parameter_name='_blockNumber',
            argument_value=block_number,
        )
        return (withdraw_address, block_number)

    def call(self, withdraw_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _blockNumber: The confirmed block number to use for the query.
        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (withdraw_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(withdraw_address, block_number).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, withdraw_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _blockNumber: The confirmed block number to use for the query.
        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        """
        (withdraw_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, block_number).transact(tx_params.as_dict())

    def build_transaction(self, withdraw_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (withdraw_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, block_number).build_transaction(tx_params.as_dict())

    def estimate_gas(self, withdraw_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (withdraw_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, block_number).estimate_gas(tx_params.as_dict())

class GetUnprocessedDdxWithdrawalsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getUnprocessedDDXWithdrawals method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, withdraw_address: str):
        """Validate the inputs to the getUnprocessedDDXWithdrawals method."""
        self.validator.assert_valid(
            method_name='getUnprocessedDDXWithdrawals',
            parameter_name='_withdrawAddress',
            argument_value=withdraw_address,
        )
        withdraw_address = self.validate_and_checksum_address(withdraw_address)
        return (withdraw_address)

    def call(self, withdraw_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (withdraw_address) = self.validate_and_normalize_inputs(withdraw_address)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(withdraw_address).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, withdraw_address: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        """
        (withdraw_address) = self.validate_and_normalize_inputs(withdraw_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address).transact(tx_params.as_dict())

    def build_transaction(self, withdraw_address: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (withdraw_address) = self.validate_and_normalize_inputs(withdraw_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address).build_transaction(tx_params.as_dict())

    def estimate_gas(self, withdraw_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (withdraw_address) = self.validate_and_normalize_inputs(withdraw_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address).estimate_gas(tx_params.as_dict())

class InitializeMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the initialize method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, ddx_minimum_rate_limit: int, max_ddx_cap: int):
        """Validate the inputs to the initialize method."""
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_ddxMinimumRateLimit',
            argument_value=ddx_minimum_rate_limit,
        )
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_maxDDXCap',
            argument_value=max_ddx_cap,
        )
        # safeguard against fractional inputs
        max_ddx_cap = int(max_ddx_cap)
        return (ddx_minimum_rate_limit, max_ddx_cap)

    def call(self, ddx_minimum_rate_limit: int, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        This function is intended to be the initialization target of the
        diamond cut function. This function is not included in the selectors
        being added to the diamond, meaning it cannot be called again.

        :param _ddxMinimumRateLimit: The minimum rate limit for DDX withdrawn
                 from the DDX trader leaves.
        :param _maxDDXCap: The maximum DDX capitalization allowed within the
            SMT.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (ddx_minimum_rate_limit, max_ddx_cap) = self.validate_and_normalize_inputs(ddx_minimum_rate_limit, max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(ddx_minimum_rate_limit, max_ddx_cap).call(tx_params.as_dict())

    def send_transaction(self, ddx_minimum_rate_limit: int, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        This function is intended to be the initialization target of the
        diamond cut function. This function is not included in the selectors
        being added to the diamond, meaning it cannot be called again.

        :param _ddxMinimumRateLimit: The minimum rate limit for DDX withdrawn
                 from the DDX trader leaves.
        :param _maxDDXCap: The maximum DDX capitalization allowed within the
            SMT.
        :param tx_params: transaction parameters
        """
        (ddx_minimum_rate_limit, max_ddx_cap) = self.validate_and_normalize_inputs(ddx_minimum_rate_limit, max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(ddx_minimum_rate_limit, max_ddx_cap).transact(tx_params.as_dict())

    def build_transaction(self, ddx_minimum_rate_limit: int, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (ddx_minimum_rate_limit, max_ddx_cap) = self.validate_and_normalize_inputs(ddx_minimum_rate_limit, max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(ddx_minimum_rate_limit, max_ddx_cap).build_transaction(tx_params.as_dict())

    def estimate_gas(self, ddx_minimum_rate_limit: int, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (ddx_minimum_rate_limit, max_ddx_cap) = self.validate_and_normalize_inputs(ddx_minimum_rate_limit, max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(ddx_minimum_rate_limit, max_ddx_cap).estimate_gas(tx_params.as_dict())

class SetDdxRateLimitsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setDDXRateLimits method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, minimum_rate_limit: int):
        """Validate the inputs to the setDDXRateLimits method."""
        self.validator.assert_valid(
            method_name='setDDXRateLimits',
            parameter_name='_minimumRateLimit',
            argument_value=minimum_rate_limit,
        )
        return (minimum_rate_limit)

    def call(self, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _minimumRateLimit: The minimum amount that the rate limit will
            be        set to.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (minimum_rate_limit) = self.validate_and_normalize_inputs(minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(minimum_rate_limit).call(tx_params.as_dict())

    def send_transaction(self, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _minimumRateLimit: The minimum amount that the rate limit will
            be        set to.
        :param tx_params: transaction parameters
        """
        (minimum_rate_limit) = self.validate_and_normalize_inputs(minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(minimum_rate_limit).transact(tx_params.as_dict())

    def build_transaction(self, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (minimum_rate_limit) = self.validate_and_normalize_inputs(minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(minimum_rate_limit).build_transaction(tx_params.as_dict())

    def estimate_gas(self, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (minimum_rate_limit) = self.validate_and_normalize_inputs(minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(minimum_rate_limit).estimate_gas(tx_params.as_dict())

class SetMaxDdxCapMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setMaxDDXCap method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, max_ddx_cap: int):
        """Validate the inputs to the setMaxDDXCap method."""
        self.validator.assert_valid(
            method_name='setMaxDDXCap',
            parameter_name='_maxDDXCap',
            argument_value=max_ddx_cap,
        )
        # safeguard against fractional inputs
        max_ddx_cap = int(max_ddx_cap)
        return (max_ddx_cap)

    def call(self, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        We intentionally avoid checking to see that the max DDX cap is greater
        than the current DDX balance as this check could be front-run in order
        to keep the cap at the elevated level. Instead, we simply set the cap
        to the chosen value which prevents further deposits from taking place.
        The operation is still susceptible to front-running, but the ability to
        keep the cap arbitrarily elevated is removed.

        :param _maxDDXCap: The maximum amount of DDX that can be held within
            the        DerivaDEX SMT.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (max_ddx_cap) = self.validate_and_normalize_inputs(max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(max_ddx_cap).call(tx_params.as_dict())

    def send_transaction(self, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        We intentionally avoid checking to see that the max DDX cap is greater
        than the current DDX balance as this check could be front-run in order
        to keep the cap at the elevated level. Instead, we simply set the cap
        to the chosen value which prevents further deposits from taking place.
        The operation is still susceptible to front-running, but the ability to
        keep the cap arbitrarily elevated is removed.

        :param _maxDDXCap: The maximum amount of DDX that can be held within
            the        DerivaDEX SMT.
        :param tx_params: transaction parameters
        """
        (max_ddx_cap) = self.validate_and_normalize_inputs(max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(max_ddx_cap).transact(tx_params.as_dict())

    def build_transaction(self, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (max_ddx_cap) = self.validate_and_normalize_inputs(max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(max_ddx_cap).build_transaction(tx_params.as_dict())

    def estimate_gas(self, max_ddx_cap: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (max_ddx_cap) = self.validate_and_normalize_inputs(max_ddx_cap)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(max_ddx_cap).estimate_gas(tx_params.as_dict())

class WithdrawDdxMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the withdrawDDX method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, amount: int, trader: DepositDefsTraderData, proof: Union[bytes, str]):
        """Validate the inputs to the withdrawDDX method."""
        self.validator.assert_valid(
            method_name='withdrawDDX',
            parameter_name='_amount',
            argument_value=amount,
        )
        self.validator.assert_valid(
            method_name='withdrawDDX',
            parameter_name='_trader',
            argument_value=trader,
        )
        self.validator.assert_valid(
            method_name='withdrawDDX',
            parameter_name='_proof',
            argument_value=proof,
        )
        return (amount, trader, proof)

    def call(self, amount: int, trader: DepositDefsTraderData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _amount: The amount of DDX to withdraw.
        :param _proof: The merkle proof that will be used to verify whether or
            not        the trader can withdraw the requested amount.
        :param _trader: The Trader leaf that should represent the sender's
            trader        account within the DDX state root.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (amount, trader, proof) = self.validate_and_normalize_inputs(amount, trader, proof)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(amount, trader, proof).call(tx_params.as_dict())

    def send_transaction(self, amount: int, trader: DepositDefsTraderData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _amount: The amount of DDX to withdraw.
        :param _proof: The merkle proof that will be used to verify whether or
            not        the trader can withdraw the requested amount.
        :param _trader: The Trader leaf that should represent the sender's
            trader        account within the DDX state root.
        :param tx_params: transaction parameters
        """
        (amount, trader, proof) = self.validate_and_normalize_inputs(amount, trader, proof)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount, trader, proof).transact(tx_params.as_dict())

    def build_transaction(self, amount: int, trader: DepositDefsTraderData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (amount, trader, proof) = self.validate_and_normalize_inputs(amount, trader, proof)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount, trader, proof).build_transaction(tx_params.as_dict())

    def estimate_gas(self, amount: int, trader: DepositDefsTraderData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (amount, trader, proof) = self.validate_and_normalize_inputs(amount, trader, proof)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(amount, trader, proof).estimate_gas(tx_params.as_dict())

# pylint: disable=too-many-public-methods,too-many-instance-attributes
class IStake:
    """Wrapper class for IStake Solidity contract.

    All method parameters of type `bytes`:code: should be encoded as UTF-8,
    which can be accomplished via `str.encode("utf_8")`:code:.
    """
    deposit_ddx: DepositDdxMethod
    """Constructor-initialized instance of
    :class:`DepositDdxMethod`.
    """

    get_max_ddx_cap: GetMaxDdxCapMethod
    """Constructor-initialized instance of
    :class:`GetMaxDdxCapMethod`.
    """

    get_processed_ddx_withdrawals: GetProcessedDdxWithdrawalsMethod
    """Constructor-initialized instance of
    :class:`GetProcessedDdxWithdrawalsMethod`.
    """

    get_unprocessed_ddx_withdrawals: GetUnprocessedDdxWithdrawalsMethod
    """Constructor-initialized instance of
    :class:`GetUnprocessedDdxWithdrawalsMethod`.
    """

    initialize: InitializeMethod
    """Constructor-initialized instance of
    :class:`InitializeMethod`.
    """

    set_ddx_rate_limits: SetDdxRateLimitsMethod
    """Constructor-initialized instance of
    :class:`SetDdxRateLimitsMethod`.
    """

    set_max_ddx_cap: SetMaxDdxCapMethod
    """Constructor-initialized instance of
    :class:`SetMaxDdxCapMethod`.
    """

    withdraw_ddx: WithdrawDdxMethod
    """Constructor-initialized instance of
    :class:`WithdrawDdxMethod`.
    """


    def __init__(
        self,
        web3_or_provider: Union[Web3, BaseProvider],
        contract_address: str,
        validator: IStakeValidator = None,
    ):
        """Get an instance of wrapper for smart contract.

        :param web3_or_provider: Either an instance of `web3.Web3`:code: or
            `web3.providers.base.BaseProvider`:code:
        :param contract_address: where the contract has been deployed
        :param validator: for validation of method inputs.
        """
        # pylint: disable=too-many-statements

        self.contract_address = contract_address

        if not validator:
            validator = IStakeValidator(web3_or_provider, contract_address)

        web3 = None
        if isinstance(web3_or_provider, BaseProvider):
            web3 = Web3(web3_or_provider)
        elif isinstance(web3_or_provider, Web3):
            web3 = web3_or_provider
        else:
            raise TypeError(
                "Expected parameter 'web3_or_provider' to be an instance of either"
                + " Web3 or BaseProvider"
            )

        # if any middleware was imported, inject it
        try:
            MIDDLEWARE
        except NameError:
            pass
        else:
            try:
                for middleware in MIDDLEWARE:
                    web3.middleware_onion.inject(
                         middleware['function'], layer=middleware['layer'],
                    )
            except ValueError as value_error:
                if value_error.args == ("You can't add the same un-named instance twice",):
                    pass

        self._web3_eth = web3.eth

        functions = self._web3_eth.contract(address=to_checksum_address(contract_address), abi=IStake.abi()).functions

        self.deposit_ddx = DepositDdxMethod(web3_or_provider, contract_address, functions.depositDDX, validator)

        self.get_max_ddx_cap = GetMaxDdxCapMethod(web3_or_provider, contract_address, functions.getMaxDDXCap)

        self.get_processed_ddx_withdrawals = GetProcessedDdxWithdrawalsMethod(web3_or_provider, contract_address, functions.getProcessedDDXWithdrawals, validator)

        self.get_unprocessed_ddx_withdrawals = GetUnprocessedDdxWithdrawalsMethod(web3_or_provider, contract_address, functions.getUnprocessedDDXWithdrawals, validator)

        self.initialize = InitializeMethod(web3_or_provider, contract_address, functions.initialize, validator)

        self.set_ddx_rate_limits = SetDdxRateLimitsMethod(web3_or_provider, contract_address, functions.setDDXRateLimits, validator)

        self.set_max_ddx_cap = SetMaxDdxCapMethod(web3_or_provider, contract_address, functions.setMaxDDXCap, validator)

        self.withdraw_ddx = WithdrawDdxMethod(web3_or_provider, contract_address, functions.withdrawDDX, validator)

    def get_ddx_rate_limit_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for DDXRateLimitSet event.

        :param tx_hash: hash of transaction emitting DDXRateLimitSet event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=IStake.abi()).events.DDXRateLimitSet().process_receipt(tx_receipt)
    def get_max_ddx_cap_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for MaxDDXCapSet event.

        :param tx_hash: hash of transaction emitting MaxDDXCapSet event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=IStake.abi()).events.MaxDDXCapSet().process_receipt(tx_receipt)
    def get_trader_updated_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for TraderUpdated event.

        :param tx_hash: hash of transaction emitting TraderUpdated event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=IStake.abi()).events.TraderUpdated().process_receipt(tx_receipt)

    @staticmethod
    def abi():
        """Return the ABI to the underlying contract."""
        return json.loads(
            '[{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint128","name":"minimumRateLimit","type":"uint128"}],"name":"DDXRateLimitSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"oldMaxCap","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"newMaxCap","type":"uint256"}],"name":"MaxDDXCapSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"trader","type":"address"},{"indexed":false,"internalType":"uint128","name":"amount","type":"uint128"},{"indexed":false,"internalType":"enum DepositDefs.TraderUpdateKind","name":"updateKind","type":"uint8"}],"name":"TraderUpdated","type":"event"},{"inputs":[{"internalType":"uint128","name":"_amount","type":"uint128"},{"internalType":"uint256","name":"_expiryBlock","type":"uint256"},{"internalType":"bytes","name":"_signature","type":"bytes"}],"name":"depositDDX","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"getMaxDDXCap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_withdrawAddress","type":"address"},{"internalType":"uint128","name":"_blockNumber","type":"uint128"}],"name":"getProcessedDDXWithdrawals","outputs":[{"internalType":"uint128","name":"amount","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_withdrawAddress","type":"address"}],"name":"getUnprocessedDDXWithdrawals","outputs":[{"internalType":"uint128","name":"amount","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint128","name":"_ddxMinimumRateLimit","type":"uint128"},{"internalType":"uint256","name":"_maxDDXCap","type":"uint256"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_minimumRateLimit","type":"uint128"}],"name":"setDDXRateLimits","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_maxDDXCap","type":"uint256"}],"name":"setMaxDDXCap","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_amount","type":"uint128"},{"components":[{"internalType":"uint128","name":"availDDXBalance","type":"uint128"},{"internalType":"uint128","name":"lockedDDXBalance","type":"uint128"},{"internalType":"bytes21","name":"referralAddress","type":"bytes21"},{"internalType":"bool","name":"payFeesInDDX","type":"bool"},{"internalType":"bool","name":"accessDenied","type":"bool"}],"internalType":"struct DepositDefs.TraderData","name":"_trader","type":"tuple"},{"internalType":"bytes","name":"_proof","type":"bytes"}],"name":"withdrawDDX","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa: E501 (line-too-long)
        )

# pylint: disable=too-many-lines
