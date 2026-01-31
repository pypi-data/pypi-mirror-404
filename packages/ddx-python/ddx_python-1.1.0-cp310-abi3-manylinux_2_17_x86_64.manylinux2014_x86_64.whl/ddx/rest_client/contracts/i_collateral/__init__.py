"""Generated wrapper for ICollateral Solidity contract."""

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
# constructor for ICollateral below.
try:
    # both mypy and pylint complain about what we're doing here, but this
    # works just fine, so their messages have been disabled here.
    from . import (  # type: ignore # pylint: disable=import-self
        ICollateralValidator,
    )
except ImportError:

    class ICollateralValidator(  # type: ignore
        Validator
    ):
        """No-op input validator."""


try:
    from .middleware import MIDDLEWARE  # type: ignore
except ImportError:
    pass


class SharedDefsBalance256(TypedDict):
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

    tokens: List[str]

    amounts: List[int]


class SharedDefsBalance128(TypedDict):
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

    tokens: List[str]

    amounts: List[int]


class DepositDefsStrategyData(TypedDict):
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

    availCollateral: SharedDefsBalance256

    lockedCollateral: SharedDefsBalance128

    maxLeverage: int

    frozen: bool


class DepositDefsExchangeCollateral(TypedDict):
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

    underlyingToken: str

    flavor: int

    isListed: bool


class AddExchangeCollateralMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the addExchangeCollateral method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, collateral_token: str, minimum_rate_limit: int):
        """Validate the inputs to the addExchangeCollateral method."""
        self.validator.assert_valid(
            method_name='addExchangeCollateral',
            parameter_name='_collateralToken',
            argument_value=collateral_token,
        )
        collateral_token = self.validate_and_checksum_address(collateral_token)
        self.validator.assert_valid(
            method_name='addExchangeCollateral',
            parameter_name='_minimumRateLimit',
            argument_value=minimum_rate_limit,
        )
        return (collateral_token, minimum_rate_limit)

    def call(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        This function purposefully prevents governance from adding collateral
        flavors that are not Vanilla. Claiming Compound or Aave rewards has not
        been implemented yet, so adding these tokens as collateral will
        encourage users to waste their rewards.

        :param _collateralToken: The collateral token to add.
        :param _minimumRateLimit: The minimum amount that the rate limit will
            be        set to.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(collateral_token, minimum_rate_limit).call(tx_params.as_dict())

    def send_transaction(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        This function purposefully prevents governance from adding collateral
        flavors that are not Vanilla. Claiming Compound or Aave rewards has not
        been implemented yet, so adding these tokens as collateral will
        encourage users to waste their rewards.

        :param _collateralToken: The collateral token to add.
        :param _minimumRateLimit: The minimum amount that the rate limit will
            be        set to.
        :param tx_params: transaction parameters
        """
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token, minimum_rate_limit).transact(tx_params.as_dict())

    def build_transaction(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token, minimum_rate_limit).build_transaction(tx_params.as_dict())

    def estimate_gas(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token, minimum_rate_limit).estimate_gas(tx_params.as_dict())

class DepositMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the deposit method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, collateral_address: str, strategy_id: Union[bytes, str], amount: int, expiry_block: int, signature: Union[bytes, str]):
        """Validate the inputs to the deposit method."""
        self.validator.assert_valid(
            method_name='deposit',
            parameter_name='_collateralAddress',
            argument_value=collateral_address,
        )
        collateral_address = self.validate_and_checksum_address(collateral_address)
        self.validator.assert_valid(
            method_name='deposit',
            parameter_name='_strategyId',
            argument_value=strategy_id,
        )
        self.validator.assert_valid(
            method_name='deposit',
            parameter_name='_amount',
            argument_value=amount,
        )
        self.validator.assert_valid(
            method_name='deposit',
            parameter_name='_expiryBlock',
            argument_value=expiry_block,
        )
        # safeguard against fractional inputs
        expiry_block = int(expiry_block)
        self.validator.assert_valid(
            method_name='deposit',
            parameter_name='_signature',
            argument_value=signature,
        )
        return (collateral_address, strategy_id, amount, expiry_block, signature)

    def call(self, collateral_address: str, strategy_id: Union[bytes, str], amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _amount: The amount to deposit.
        :param _collateralAddress: The address of the collateral that should be
            deposited.
        :param _expiryBlock: Expiry block number for KYC authorization.
        :param _signature: Signature of KYC authorization address.
        :param _strategyId: The ID of the strategy to deposit into.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (collateral_address, strategy_id, amount, expiry_block, signature) = self.validate_and_normalize_inputs(collateral_address, strategy_id, amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(collateral_address, strategy_id, amount, expiry_block, signature).call(tx_params.as_dict())

    def send_transaction(self, collateral_address: str, strategy_id: Union[bytes, str], amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _amount: The amount to deposit.
        :param _collateralAddress: The address of the collateral that should be
            deposited.
        :param _expiryBlock: Expiry block number for KYC authorization.
        :param _signature: Signature of KYC authorization address.
        :param _strategyId: The ID of the strategy to deposit into.
        :param tx_params: transaction parameters
        """
        (collateral_address, strategy_id, amount, expiry_block, signature) = self.validate_and_normalize_inputs(collateral_address, strategy_id, amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_address, strategy_id, amount, expiry_block, signature).transact(tx_params.as_dict())

    def build_transaction(self, collateral_address: str, strategy_id: Union[bytes, str], amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (collateral_address, strategy_id, amount, expiry_block, signature) = self.validate_and_normalize_inputs(collateral_address, strategy_id, amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_address, strategy_id, amount, expiry_block, signature).build_transaction(tx_params.as_dict())

    def estimate_gas(self, collateral_address: str, strategy_id: Union[bytes, str], amount: int, expiry_block: int, signature: Union[bytes, str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (collateral_address, strategy_id, amount, expiry_block, signature) = self.validate_and_normalize_inputs(collateral_address, strategy_id, amount, expiry_block, signature)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_address, strategy_id, amount, expiry_block, signature).estimate_gas(tx_params.as_dict())

class GetAddressesHaveDepositedMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getAddressesHaveDeposited method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, traders: List[str]):
        """Validate the inputs to the getAddressesHaveDeposited method."""
        self.validator.assert_valid(
            method_name='getAddressesHaveDeposited',
            parameter_name='_traders',
            argument_value=traders,
        )
        return (traders)

    def call(self, traders: List[str], tx_params: Optional[TxParams] = None) -> List[bool]:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (traders) = self.validate_and_normalize_inputs(traders)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(traders).call(tx_params.as_dict())
        return [bool(element) for element in returned]

    def send_transaction(self, traders: List[str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param tx_params: transaction parameters
        """
        (traders) = self.validate_and_normalize_inputs(traders)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(traders).transact(tx_params.as_dict())

    def build_transaction(self, traders: List[str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (traders) = self.validate_and_normalize_inputs(traders)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(traders).build_transaction(tx_params.as_dict())

    def estimate_gas(self, traders: List[str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (traders) = self.validate_and_normalize_inputs(traders)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(traders).estimate_gas(tx_params.as_dict())

class GetExchangeCollateralInfoMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getExchangeCollateralInfo method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, collateral_token: str):
        """Validate the inputs to the getExchangeCollateralInfo method."""
        self.validator.assert_valid(
            method_name='getExchangeCollateralInfo',
            parameter_name='_collateralToken',
            argument_value=collateral_token,
        )
        collateral_token = self.validate_and_checksum_address(collateral_token)
        return (collateral_token)

    def call(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> DepositDefsExchangeCollateral:
        """Execute underlying contract method via eth_call.

        :param _collateralToken: The collateral token of the collateral to
            query.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(collateral_token).call(tx_params.as_dict())
        return DepositDefsExchangeCollateral(underlyingToken=returned[0],flavor=returned[1],isListed=returned[2],)

    def send_transaction(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _collateralToken: The collateral token of the collateral to
            query.
        :param tx_params: transaction parameters
        """
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token).transact(tx_params.as_dict())

    def build_transaction(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token).build_transaction(tx_params.as_dict())

    def estimate_gas(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token).estimate_gas(tx_params.as_dict())

class GetGuardedDepositInfoMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getGuardedDepositInfo method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> Tuple[int, int, int]:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return (returned[0],returned[1],returned[2],)

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

class GetMaximumWithdrawalMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getMaximumWithdrawal method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, token_address: str):
        """Validate the inputs to the getMaximumWithdrawal method."""
        self.validator.assert_valid(
            method_name='getMaximumWithdrawal',
            parameter_name='_tokenAddress',
            argument_value=token_address,
        )
        token_address = self.validate_and_checksum_address(token_address)
        return (token_address)

    def call(self, token_address: str, tx_params: Optional[TxParams] = None) -> Tuple[int, int]:
        """Execute underlying contract method via eth_call.

        :param _tokenAddress: The address of the token to withdraw.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(token_address).call(tx_params.as_dict())
        return (returned[0],returned[1],)

    def send_transaction(self, token_address: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _tokenAddress: The address of the token to withdraw.
        :param tx_params: transaction parameters
        """
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(token_address).transact(tx_params.as_dict())

    def build_transaction(self, token_address: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(token_address).build_transaction(tx_params.as_dict())

    def estimate_gas(self, token_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(token_address).estimate_gas(tx_params.as_dict())

class GetProcessedWithdrawalsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getProcessedWithdrawals method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, block_number: int):
        """Validate the inputs to the getProcessedWithdrawals method."""
        self.validator.assert_valid(
            method_name='getProcessedWithdrawals',
            parameter_name='_withdrawAddress',
            argument_value=withdraw_address,
        )
        withdraw_address = self.validate_and_checksum_address(withdraw_address)
        self.validator.assert_valid(
            method_name='getProcessedWithdrawals',
            parameter_name='_strategyIdHash',
            argument_value=strategy_id_hash,
        )
        self.validator.assert_valid(
            method_name='getProcessedWithdrawals',
            parameter_name='_tokenAddress',
            argument_value=token_address,
        )
        token_address = self.validate_and_checksum_address(token_address)
        self.validator.assert_valid(
            method_name='getProcessedWithdrawals',
            parameter_name='_blockNumber',
            argument_value=block_number,
        )
        return (withdraw_address, strategy_id_hash, token_address, block_number)

    def call(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _blockNumber: The confirmed block number to use for the query.
        :param _strategyIdHash: The ID hash of the strategy that is being
            withdrawn from.
        :param _tokenAddress: The address of the collateral that was withdrawn.
        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (withdraw_address, strategy_id_hash, token_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(withdraw_address, strategy_id_hash, token_address, block_number).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _blockNumber: The confirmed block number to use for the query.
        :param _strategyIdHash: The ID hash of the strategy that is being
            withdrawn from.
        :param _tokenAddress: The address of the collateral that was withdrawn.
        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        """
        (withdraw_address, strategy_id_hash, token_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, strategy_id_hash, token_address, block_number).transact(tx_params.as_dict())

    def build_transaction(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (withdraw_address, strategy_id_hash, token_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, strategy_id_hash, token_address, block_number).build_transaction(tx_params.as_dict())

    def estimate_gas(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, block_number: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (withdraw_address, strategy_id_hash, token_address, block_number) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address, block_number)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, strategy_id_hash, token_address, block_number).estimate_gas(tx_params.as_dict())

class GetRateLimitParametersMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getRateLimitParameters method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address)
        self._underlying_method = contract_function

    def call(self, tx_params: Optional[TxParams] = None) -> Tuple[int, int]:
        """Execute underlying contract method via eth_call.

        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method().call(tx_params.as_dict())
        return (returned[0],returned[1],)

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

class GetUnprocessedWithdrawalsMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getUnprocessedWithdrawals method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str):
        """Validate the inputs to the getUnprocessedWithdrawals method."""
        self.validator.assert_valid(
            method_name='getUnprocessedWithdrawals',
            parameter_name='_withdrawAddress',
            argument_value=withdraw_address,
        )
        withdraw_address = self.validate_and_checksum_address(withdraw_address)
        self.validator.assert_valid(
            method_name='getUnprocessedWithdrawals',
            parameter_name='_strategyIdHash',
            argument_value=strategy_id_hash,
        )
        self.validator.assert_valid(
            method_name='getUnprocessedWithdrawals',
            parameter_name='_tokenAddress',
            argument_value=token_address,
        )
        token_address = self.validate_and_checksum_address(token_address)
        return (withdraw_address, strategy_id_hash, token_address)

    def call(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _strategyIdHash: The ID hash of the strategy that is being
            withdrawn from.
        :param _tokenAddress: The address of the collateral that was withdrawn.
        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (withdraw_address, strategy_id_hash, token_address) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(withdraw_address, strategy_id_hash, token_address).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _strategyIdHash: The ID hash of the strategy that is being
            withdrawn from.
        :param _tokenAddress: The address of the collateral that was withdrawn.
        :param _withdrawAddress: The address that is attempting to withdraw.
        :param tx_params: transaction parameters
        """
        (withdraw_address, strategy_id_hash, token_address) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, strategy_id_hash, token_address).transact(tx_params.as_dict())

    def build_transaction(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (withdraw_address, strategy_id_hash, token_address) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, strategy_id_hash, token_address).build_transaction(tx_params.as_dict())

    def estimate_gas(self, withdraw_address: str, strategy_id_hash: Union[bytes, str], token_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (withdraw_address, strategy_id_hash, token_address) = self.validate_and_normalize_inputs(withdraw_address, strategy_id_hash, token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(withdraw_address, strategy_id_hash, token_address).estimate_gas(tx_params.as_dict())

class GetWithdrawalAllowanceMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the getWithdrawalAllowance method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, token_address: str):
        """Validate the inputs to the getWithdrawalAllowance method."""
        self.validator.assert_valid(
            method_name='getWithdrawalAllowance',
            parameter_name='_tokenAddress',
            argument_value=token_address,
        )
        token_address = self.validate_and_checksum_address(token_address)
        return (token_address)

    def call(self, token_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Execute underlying contract method via eth_call.

        :param _tokenAddress: The specified token.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        returned = self._underlying_method(token_address).call(tx_params.as_dict())
        return int(returned)

    def send_transaction(self, token_address: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _tokenAddress: The specified token.
        :param tx_params: transaction parameters
        """
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(token_address).transact(tx_params.as_dict())

    def build_transaction(self, token_address: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(token_address).build_transaction(tx_params.as_dict())

    def estimate_gas(self, token_address: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (token_address) = self.validate_and_normalize_inputs(token_address)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(token_address).estimate_gas(tx_params.as_dict())

class InitializeMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the initialize method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, rate_limit_period: int, rate_limit_percentage: int, max_deposited_addresses: int, min_deposit: int):
        """Validate the inputs to the initialize method."""
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_rateLimitPeriod',
            argument_value=rate_limit_period,
        )
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_rateLimitPercentage',
            argument_value=rate_limit_percentage,
        )
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_maxDepositedAddresses',
            argument_value=max_deposited_addresses,
        )
        self.validator.assert_valid(
            method_name='initialize',
            parameter_name='_minDeposit',
            argument_value=min_deposit,
        )
        return (rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit)

    def call(self, rate_limit_period: int, rate_limit_percentage: int, max_deposited_addresses: int, min_deposit: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        This function is intended to be the initialization target of the
        diamond cut function. This function is not included in the selectors
        being added to the diamond, meaning it cannot be called again.

        :param _maxDepositedAddresses: The maximum number of deposited
            addresses.
        :param _minDeposit: The minimum amount of USDC that must be deposited.
        :param _rateLimitPercentage: The dynamic component of the withdrawal
                rate limits.
        :param _rateLimitPeriod: The number of blocks before token-specific
               rate limits are reassessed.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit).call(tx_params.as_dict())

    def send_transaction(self, rate_limit_period: int, rate_limit_percentage: int, max_deposited_addresses: int, min_deposit: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        This function is intended to be the initialization target of the
        diamond cut function. This function is not included in the selectors
        being added to the diamond, meaning it cannot be called again.

        :param _maxDepositedAddresses: The maximum number of deposited
            addresses.
        :param _minDeposit: The minimum amount of USDC that must be deposited.
        :param _rateLimitPercentage: The dynamic component of the withdrawal
                rate limits.
        :param _rateLimitPeriod: The number of blocks before token-specific
               rate limits are reassessed.
        :param tx_params: transaction parameters
        """
        (rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit).transact(tx_params.as_dict())

    def build_transaction(self, rate_limit_period: int, rate_limit_percentage: int, max_deposited_addresses: int, min_deposit: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit).build_transaction(tx_params.as_dict())

    def estimate_gas(self, rate_limit_period: int, rate_limit_percentage: int, max_deposited_addresses: int, min_deposit: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(rate_limit_period, rate_limit_percentage, max_deposited_addresses, min_deposit).estimate_gas(tx_params.as_dict())

class RemoveExchangeCollateralMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the removeExchangeCollateral method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, collateral_token: str):
        """Validate the inputs to the removeExchangeCollateral method."""
        self.validator.assert_valid(
            method_name='removeExchangeCollateral',
            parameter_name='_collateralToken',
            argument_value=collateral_token,
        )
        collateral_token = self.validate_and_checksum_address(collateral_token)
        return (collateral_token)

    def call(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _collateralToken: The collateral token to remove.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(collateral_token).call(tx_params.as_dict())

    def send_transaction(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _collateralToken: The collateral token to remove.
        :param tx_params: transaction parameters
        """
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token).transact(tx_params.as_dict())

    def build_transaction(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token).build_transaction(tx_params.as_dict())

    def estimate_gas(self, collateral_token: str, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (collateral_token) = self.validate_and_normalize_inputs(collateral_token)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token).estimate_gas(tx_params.as_dict())

class SetMaxDepositedAddressesMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setMaxDepositedAddresses method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, max_deposited_addresses: int):
        """Validate the inputs to the setMaxDepositedAddresses method."""
        self.validator.assert_valid(
            method_name='setMaxDepositedAddresses',
            parameter_name='_maxDepositedAddresses',
            argument_value=max_deposited_addresses,
        )
        return (max_deposited_addresses)

    def call(self, max_deposited_addresses: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _maxDepositedAddresses: The maximum number of deposited
            addresses.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (max_deposited_addresses) = self.validate_and_normalize_inputs(max_deposited_addresses)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(max_deposited_addresses).call(tx_params.as_dict())

    def send_transaction(self, max_deposited_addresses: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _maxDepositedAddresses: The maximum number of deposited
            addresses.
        :param tx_params: transaction parameters
        """
        (max_deposited_addresses) = self.validate_and_normalize_inputs(max_deposited_addresses)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(max_deposited_addresses).transact(tx_params.as_dict())

    def build_transaction(self, max_deposited_addresses: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (max_deposited_addresses) = self.validate_and_normalize_inputs(max_deposited_addresses)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(max_deposited_addresses).build_transaction(tx_params.as_dict())

    def estimate_gas(self, max_deposited_addresses: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (max_deposited_addresses) = self.validate_and_normalize_inputs(max_deposited_addresses)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(max_deposited_addresses).estimate_gas(tx_params.as_dict())

class SetMinDepositMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setMinDeposit method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, min_deposit: int):
        """Validate the inputs to the setMinDeposit method."""
        self.validator.assert_valid(
            method_name='setMinDeposit',
            parameter_name='_minDeposit',
            argument_value=min_deposit,
        )
        return (min_deposit)

    def call(self, min_deposit: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _minDeposit: The minimum amount of USDC that must be deposited.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (min_deposit) = self.validate_and_normalize_inputs(min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(min_deposit).call(tx_params.as_dict())

    def send_transaction(self, min_deposit: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _minDeposit: The minimum amount of USDC that must be deposited.
        :param tx_params: transaction parameters
        """
        (min_deposit) = self.validate_and_normalize_inputs(min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(min_deposit).transact(tx_params.as_dict())

    def build_transaction(self, min_deposit: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (min_deposit) = self.validate_and_normalize_inputs(min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(min_deposit).build_transaction(tx_params.as_dict())

    def estimate_gas(self, min_deposit: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (min_deposit) = self.validate_and_normalize_inputs(min_deposit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(min_deposit).estimate_gas(tx_params.as_dict())

class SetRateLimitParametersMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the setRateLimitParameters method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, rate_limit_period: int, rate_limit_percentage: int):
        """Validate the inputs to the setRateLimitParameters method."""
        self.validator.assert_valid(
            method_name='setRateLimitParameters',
            parameter_name='_rateLimitPeriod',
            argument_value=rate_limit_period,
        )
        self.validator.assert_valid(
            method_name='setRateLimitParameters',
            parameter_name='_rateLimitPercentage',
            argument_value=rate_limit_percentage,
        )
        return (rate_limit_period, rate_limit_percentage)

    def call(self, rate_limit_period: int, rate_limit_percentage: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _rateLimitPercentage: The new rate limit percentage.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (rate_limit_period, rate_limit_percentage) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(rate_limit_period, rate_limit_percentage).call(tx_params.as_dict())

    def send_transaction(self, rate_limit_period: int, rate_limit_percentage: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _rateLimitPercentage: The new rate limit percentage.
        :param tx_params: transaction parameters
        """
        (rate_limit_period, rate_limit_percentage) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(rate_limit_period, rate_limit_percentage).transact(tx_params.as_dict())

    def build_transaction(self, rate_limit_period: int, rate_limit_percentage: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (rate_limit_period, rate_limit_percentage) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(rate_limit_period, rate_limit_percentage).build_transaction(tx_params.as_dict())

    def estimate_gas(self, rate_limit_period: int, rate_limit_percentage: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (rate_limit_period, rate_limit_percentage) = self.validate_and_normalize_inputs(rate_limit_period, rate_limit_percentage)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(rate_limit_period, rate_limit_percentage).estimate_gas(tx_params.as_dict())

class UpdateExchangeCollateralMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the updateExchangeCollateral method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, collateral_token: str, minimum_rate_limit: int):
        """Validate the inputs to the updateExchangeCollateral method."""
        self.validator.assert_valid(
            method_name='updateExchangeCollateral',
            parameter_name='_collateralToken',
            argument_value=collateral_token,
        )
        collateral_token = self.validate_and_checksum_address(collateral_token)
        self.validator.assert_valid(
            method_name='updateExchangeCollateral',
            parameter_name='_minimumRateLimit',
            argument_value=minimum_rate_limit,
        )
        return (collateral_token, minimum_rate_limit)

    def call(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        :param _collateralToken: The collateral token to update.
        :param _minimumRateLimit: The minimum amount that the rate limit will
            be        set to.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(collateral_token, minimum_rate_limit).call(tx_params.as_dict())

    def send_transaction(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        :param _collateralToken: The collateral token to update.
        :param _minimumRateLimit: The minimum amount that the rate limit will
            be        set to.
        :param tx_params: transaction parameters
        """
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token, minimum_rate_limit).transact(tx_params.as_dict())

    def build_transaction(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token, minimum_rate_limit).build_transaction(tx_params.as_dict())

    def estimate_gas(self, collateral_token: str, minimum_rate_limit: int, tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (collateral_token, minimum_rate_limit) = self.validate_and_normalize_inputs(collateral_token, minimum_rate_limit)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(collateral_token, minimum_rate_limit).estimate_gas(tx_params.as_dict())

class WithdrawMethod(ContractMethod): # pylint: disable=invalid-name
    """Various interfaces to the withdraw method."""

    def __init__(self, web3_or_provider: Union[Web3, BaseProvider], contract_address: str, contract_function, validator: Validator=None):
        """Persist instance data."""
        super().__init__(web3_or_provider, contract_address, validator)
        self._underlying_method = contract_function

    def validate_and_normalize_inputs(self, strategy_id_hash: Union[bytes, str], withdrawal_data: SharedDefsBalance128, strategy: DepositDefsStrategyData, proof: Union[bytes, str]):
        """Validate the inputs to the withdraw method."""
        self.validator.assert_valid(
            method_name='withdraw',
            parameter_name='_strategyIdHash',
            argument_value=strategy_id_hash,
        )
        self.validator.assert_valid(
            method_name='withdraw',
            parameter_name='_withdrawalData',
            argument_value=withdrawal_data,
        )
        self.validator.assert_valid(
            method_name='withdraw',
            parameter_name='_strategy',
            argument_value=strategy,
        )
        self.validator.assert_valid(
            method_name='withdraw',
            parameter_name='_proof',
            argument_value=proof,
        )
        return (strategy_id_hash, withdrawal_data, strategy, proof)

    def call(self, strategy_id_hash: Union[bytes, str], withdrawal_data: SharedDefsBalance128, strategy: DepositDefsStrategyData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> None:
        """Execute underlying contract method via eth_call.

        This withdrawal strategy does not incorporate rebalancing to ensure
        that users can always withdraw the tokens that they specify. This
        consideration doesn't have an effect on UX when there is only one type
        of collateral that is accepted by the exchange, but it will become more
        pressing once multi-collateral support has been implemented.

        :param _proof: A merkle proof that proves that the included strategy is
            in        the most recent state root.
        :param _strategy: The data that is contained within the strategy.
        :param _strategyIdHash: The hash of the strategy id to withdraw from.
        :param _withdrawalData: Data that specifies the tokens and amounts to
                 withdraw. The withdraw data that is provided to this function
            must        be given in the same order as the
            `_strategy.lockedCollateral`        field. Misordering this
            parameter will cause the function to revert.
        :param tx_params: transaction parameters
        :returns: the return value of the underlying method.
        """
        (strategy_id_hash, withdrawal_data, strategy, proof) = self.validate_and_normalize_inputs(strategy_id_hash, withdrawal_data, strategy, proof)
        tx_params = super().normalize_tx_params(tx_params)
        self._underlying_method(strategy_id_hash, withdrawal_data, strategy, proof).call(tx_params.as_dict())

    def send_transaction(self, strategy_id_hash: Union[bytes, str], withdrawal_data: SharedDefsBalance128, strategy: DepositDefsStrategyData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> Union[HexBytes, bytes]:
        """Execute underlying contract method via eth_sendTransaction.

        This withdrawal strategy does not incorporate rebalancing to ensure
        that users can always withdraw the tokens that they specify. This
        consideration doesn't have an effect on UX when there is only one type
        of collateral that is accepted by the exchange, but it will become more
        pressing once multi-collateral support has been implemented.

        :param _proof: A merkle proof that proves that the included strategy is
            in        the most recent state root.
        :param _strategy: The data that is contained within the strategy.
        :param _strategyIdHash: The hash of the strategy id to withdraw from.
        :param _withdrawalData: Data that specifies the tokens and amounts to
                 withdraw. The withdraw data that is provided to this function
            must        be given in the same order as the
            `_strategy.lockedCollateral`        field. Misordering this
            parameter will cause the function to revert.
        :param tx_params: transaction parameters
        """
        (strategy_id_hash, withdrawal_data, strategy, proof) = self.validate_and_normalize_inputs(strategy_id_hash, withdrawal_data, strategy, proof)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(strategy_id_hash, withdrawal_data, strategy, proof).transact(tx_params.as_dict())

    def build_transaction(self, strategy_id_hash: Union[bytes, str], withdrawal_data: SharedDefsBalance128, strategy: DepositDefsStrategyData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> dict:
        """Construct calldata to be used as input to the method."""
        (strategy_id_hash, withdrawal_data, strategy, proof) = self.validate_and_normalize_inputs(strategy_id_hash, withdrawal_data, strategy, proof)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(strategy_id_hash, withdrawal_data, strategy, proof).build_transaction(tx_params.as_dict())

    def estimate_gas(self, strategy_id_hash: Union[bytes, str], withdrawal_data: SharedDefsBalance128, strategy: DepositDefsStrategyData, proof: Union[bytes, str], tx_params: Optional[TxParams] = None) -> int:
        """Estimate gas consumption of method call."""
        (strategy_id_hash, withdrawal_data, strategy, proof) = self.validate_and_normalize_inputs(strategy_id_hash, withdrawal_data, strategy, proof)
        tx_params = super().normalize_tx_params(tx_params)
        return self._underlying_method(strategy_id_hash, withdrawal_data, strategy, proof).estimate_gas(tx_params.as_dict())

# pylint: disable=too-many-public-methods,too-many-instance-attributes
class ICollateral:
    """Wrapper class for ICollateral Solidity contract.

    All method parameters of type `bytes`:code: should be encoded as UTF-8,
    which can be accomplished via `str.encode("utf_8")`:code:.
    """
    add_exchange_collateral: AddExchangeCollateralMethod
    """Constructor-initialized instance of
    :class:`AddExchangeCollateralMethod`.
    """

    deposit: DepositMethod
    """Constructor-initialized instance of
    :class:`DepositMethod`.
    """

    get_addresses_have_deposited: GetAddressesHaveDepositedMethod
    """Constructor-initialized instance of
    :class:`GetAddressesHaveDepositedMethod`.
    """

    get_exchange_collateral_info: GetExchangeCollateralInfoMethod
    """Constructor-initialized instance of
    :class:`GetExchangeCollateralInfoMethod`.
    """

    get_guarded_deposit_info: GetGuardedDepositInfoMethod
    """Constructor-initialized instance of
    :class:`GetGuardedDepositInfoMethod`.
    """

    get_maximum_withdrawal: GetMaximumWithdrawalMethod
    """Constructor-initialized instance of
    :class:`GetMaximumWithdrawalMethod`.
    """

    get_processed_withdrawals: GetProcessedWithdrawalsMethod
    """Constructor-initialized instance of
    :class:`GetProcessedWithdrawalsMethod`.
    """

    get_rate_limit_parameters: GetRateLimitParametersMethod
    """Constructor-initialized instance of
    :class:`GetRateLimitParametersMethod`.
    """

    get_unprocessed_withdrawals: GetUnprocessedWithdrawalsMethod
    """Constructor-initialized instance of
    :class:`GetUnprocessedWithdrawalsMethod`.
    """

    get_withdrawal_allowance: GetWithdrawalAllowanceMethod
    """Constructor-initialized instance of
    :class:`GetWithdrawalAllowanceMethod`.
    """

    initialize: InitializeMethod
    """Constructor-initialized instance of
    :class:`InitializeMethod`.
    """

    remove_exchange_collateral: RemoveExchangeCollateralMethod
    """Constructor-initialized instance of
    :class:`RemoveExchangeCollateralMethod`.
    """

    set_max_deposited_addresses: SetMaxDepositedAddressesMethod
    """Constructor-initialized instance of
    :class:`SetMaxDepositedAddressesMethod`.
    """

    set_min_deposit: SetMinDepositMethod
    """Constructor-initialized instance of
    :class:`SetMinDepositMethod`.
    """

    set_rate_limit_parameters: SetRateLimitParametersMethod
    """Constructor-initialized instance of
    :class:`SetRateLimitParametersMethod`.
    """

    update_exchange_collateral: UpdateExchangeCollateralMethod
    """Constructor-initialized instance of
    :class:`UpdateExchangeCollateralMethod`.
    """

    withdraw: WithdrawMethod
    """Constructor-initialized instance of
    :class:`WithdrawMethod`.
    """


    def __init__(
        self,
        web3_or_provider: Union[Web3, BaseProvider],
        contract_address: str,
        validator: ICollateralValidator = None,
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
            validator = ICollateralValidator(web3_or_provider, contract_address)

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

        functions = self._web3_eth.contract(address=to_checksum_address(contract_address), abi=ICollateral.abi()).functions

        self.add_exchange_collateral = AddExchangeCollateralMethod(web3_or_provider, contract_address, functions.addExchangeCollateral, validator)

        self.deposit = DepositMethod(web3_or_provider, contract_address, functions.deposit, validator)

        self.get_addresses_have_deposited = GetAddressesHaveDepositedMethod(web3_or_provider, contract_address, functions.getAddressesHaveDeposited, validator)

        self.get_exchange_collateral_info = GetExchangeCollateralInfoMethod(web3_or_provider, contract_address, functions.getExchangeCollateralInfo, validator)

        self.get_guarded_deposit_info = GetGuardedDepositInfoMethod(web3_or_provider, contract_address, functions.getGuardedDepositInfo)

        self.get_maximum_withdrawal = GetMaximumWithdrawalMethod(web3_or_provider, contract_address, functions.getMaximumWithdrawal, validator)

        self.get_processed_withdrawals = GetProcessedWithdrawalsMethod(web3_or_provider, contract_address, functions.getProcessedWithdrawals, validator)

        self.get_rate_limit_parameters = GetRateLimitParametersMethod(web3_or_provider, contract_address, functions.getRateLimitParameters)

        self.get_unprocessed_withdrawals = GetUnprocessedWithdrawalsMethod(web3_or_provider, contract_address, functions.getUnprocessedWithdrawals, validator)

        self.get_withdrawal_allowance = GetWithdrawalAllowanceMethod(web3_or_provider, contract_address, functions.getWithdrawalAllowance, validator)

        self.initialize = InitializeMethod(web3_or_provider, contract_address, functions.initialize, validator)

        self.remove_exchange_collateral = RemoveExchangeCollateralMethod(web3_or_provider, contract_address, functions.removeExchangeCollateral, validator)

        self.set_max_deposited_addresses = SetMaxDepositedAddressesMethod(web3_or_provider, contract_address, functions.setMaxDepositedAddresses, validator)

        self.set_min_deposit = SetMinDepositMethod(web3_or_provider, contract_address, functions.setMinDeposit, validator)

        self.set_rate_limit_parameters = SetRateLimitParametersMethod(web3_or_provider, contract_address, functions.setRateLimitParameters, validator)

        self.update_exchange_collateral = UpdateExchangeCollateralMethod(web3_or_provider, contract_address, functions.updateExchangeCollateral, validator)

        self.withdraw = WithdrawMethod(web3_or_provider, contract_address, functions.withdraw, validator)

    def get_exchange_collateral_added_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for ExchangeCollateralAdded event.

        :param tx_hash: hash of transaction emitting ExchangeCollateralAdded
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.ExchangeCollateralAdded().process_receipt(tx_receipt)
    def get_exchange_collateral_removed_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for ExchangeCollateralRemoved event.

        :param tx_hash: hash of transaction emitting ExchangeCollateralRemoved
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.ExchangeCollateralRemoved().process_receipt(tx_receipt)
    def get_exchange_collateral_updated_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for ExchangeCollateralUpdated event.

        :param tx_hash: hash of transaction emitting ExchangeCollateralUpdated
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.ExchangeCollateralUpdated().process_receipt(tx_receipt)
    def get_max_deposited_addresses_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for MaxDepositedAddressesSet event.

        :param tx_hash: hash of transaction emitting MaxDepositedAddressesSet
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.MaxDepositedAddressesSet().process_receipt(tx_receipt)
    def get_min_deposit_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for MinDepositSet event.

        :param tx_hash: hash of transaction emitting MinDepositSet event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.MinDepositSet().process_receipt(tx_receipt)
    def get_rate_limit_parameters_set_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for RateLimitParametersSet event.

        :param tx_hash: hash of transaction emitting RateLimitParametersSet
            event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.RateLimitParametersSet().process_receipt(tx_receipt)
    def get_strategy_updated_event(
        self, tx_hash: Union[HexBytes, bytes]
    ) -> Tuple[AttributeDict]:
        """Get log entry for StrategyUpdated event.

        :param tx_hash: hash of transaction emitting StrategyUpdated event
        """
        tx_receipt = self._web3_eth.get_transaction_receipt(tx_hash)
        return self._web3_eth.contract(address=to_checksum_address(self.contract_address), abi=ICollateral.abi()).events.StrategyUpdated().process_receipt(tx_receipt)

    @staticmethod
    def abi():
        """Return the ABI to the underlying contract."""
        return json.loads(
            '[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"collateralToken","type":"address"},{"indexed":true,"internalType":"address","name":"underlyingToken","type":"address"},{"indexed":false,"internalType":"enum SharedDefs.Flavor","name":"flavor","type":"uint8"},{"indexed":false,"internalType":"uint128","name":"minimumRateLimit","type":"uint128"}],"name":"ExchangeCollateralAdded","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"collateralToken","type":"address"}],"name":"ExchangeCollateralRemoved","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"collateralToken","type":"address"},{"indexed":false,"internalType":"uint128","name":"minimumRateLimit","type":"uint128"}],"name":"ExchangeCollateralUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint128","name":"maxDepositedAddresses","type":"uint128"}],"name":"MaxDepositedAddressesSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint128","name":"minDeposit","type":"uint128"}],"name":"MinDepositSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint128","name":"rateLimitPeriod","type":"uint128"},{"indexed":false,"internalType":"uint128","name":"rateLimitPercentage","type":"uint128"}],"name":"RateLimitParametersSet","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"trader","type":"address"},{"indexed":true,"internalType":"address","name":"collateralAddress","type":"address"},{"indexed":true,"internalType":"bytes4","name":"strategyIdHash","type":"bytes4"},{"indexed":false,"internalType":"bytes32","name":"strategyId","type":"bytes32"},{"indexed":false,"internalType":"uint128","name":"amount","type":"uint128"},{"indexed":false,"internalType":"enum DepositDefs.StrategyUpdateKind","name":"updateKind","type":"uint8"}],"name":"StrategyUpdated","type":"event"},{"inputs":[{"internalType":"address","name":"_collateralToken","type":"address"},{"internalType":"uint128","name":"_minimumRateLimit","type":"uint128"}],"name":"addExchangeCollateral","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_collateralAddress","type":"address"},{"internalType":"bytes32","name":"_strategyId","type":"bytes32"},{"internalType":"uint128","name":"_amount","type":"uint128"},{"internalType":"uint256","name":"_expiryBlock","type":"uint256"},{"internalType":"bytes","name":"_signature","type":"bytes"}],"name":"deposit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"_traders","type":"address[]"}],"name":"getAddressesHaveDeposited","outputs":[{"internalType":"bool[]","name":"","type":"bool[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_collateralToken","type":"address"}],"name":"getExchangeCollateralInfo","outputs":[{"components":[{"internalType":"address","name":"underlyingToken","type":"address"},{"internalType":"enum SharedDefs.Flavor","name":"flavor","type":"uint8"},{"internalType":"bool","name":"isListed","type":"bool"}],"internalType":"struct DepositDefs.ExchangeCollateral","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getGuardedDepositInfo","outputs":[{"internalType":"uint128","name":"","type":"uint128"},{"internalType":"uint128","name":"","type":"uint128"},{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_tokenAddress","type":"address"}],"name":"getMaximumWithdrawal","outputs":[{"internalType":"uint128","name":"maximumWithdrawalAmount","type":"uint128"},{"internalType":"uint128","name":"blocksRemaining","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_withdrawAddress","type":"address"},{"internalType":"bytes4","name":"_strategyIdHash","type":"bytes4"},{"internalType":"address","name":"_tokenAddress","type":"address"},{"internalType":"uint128","name":"_blockNumber","type":"uint128"}],"name":"getProcessedWithdrawals","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getRateLimitParameters","outputs":[{"internalType":"uint128","name":"","type":"uint128"},{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_withdrawAddress","type":"address"},{"internalType":"bytes4","name":"_strategyIdHash","type":"bytes4"},{"internalType":"address","name":"_tokenAddress","type":"address"}],"name":"getUnprocessedWithdrawals","outputs":[{"internalType":"uint128","name":"amount","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_tokenAddress","type":"address"}],"name":"getWithdrawalAllowance","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint128","name":"_rateLimitPeriod","type":"uint128"},{"internalType":"uint128","name":"_rateLimitPercentage","type":"uint128"},{"internalType":"uint128","name":"_maxDepositedAddresses","type":"uint128"},{"internalType":"uint128","name":"_minDeposit","type":"uint128"}],"name":"initialize","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_collateralToken","type":"address"}],"name":"removeExchangeCollateral","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_maxDepositedAddresses","type":"uint128"}],"name":"setMaxDepositedAddresses","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_minDeposit","type":"uint128"}],"name":"setMinDeposit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint128","name":"_rateLimitPeriod","type":"uint128"},{"internalType":"uint128","name":"_rateLimitPercentage","type":"uint128"}],"name":"setRateLimitParameters","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_collateralToken","type":"address"},{"internalType":"uint128","name":"_minimumRateLimit","type":"uint128"}],"name":"updateExchangeCollateral","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"_strategyIdHash","type":"bytes4"},{"components":[{"internalType":"address[]","name":"tokens","type":"address[]"},{"internalType":"uint128[]","name":"amounts","type":"uint128[]"}],"internalType":"struct SharedDefs.Balance128","name":"_withdrawalData","type":"tuple"},{"components":[{"components":[{"internalType":"address[]","name":"tokens","type":"address[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"internalType":"struct SharedDefs.Balance256","name":"availCollateral","type":"tuple"},{"components":[{"internalType":"address[]","name":"tokens","type":"address[]"},{"internalType":"uint128[]","name":"amounts","type":"uint128[]"}],"internalType":"struct SharedDefs.Balance128","name":"lockedCollateral","type":"tuple"},{"internalType":"uint64","name":"maxLeverage","type":"uint64"},{"internalType":"bool","name":"frozen","type":"bool"}],"internalType":"struct DepositDefs.StrategyData","name":"_strategy","type":"tuple"},{"internalType":"bytes","name":"_proof","type":"bytes"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}]'  # noqa: E501 (line-too-long)
        )

# pylint: disable=too-many-lines
